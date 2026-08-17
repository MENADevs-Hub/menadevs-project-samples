"""Tests for the Mars Transfer Mission Planner task."""

import csv
import json
import math
import os

import pytest

PLAN_PATH = "/app/output/mission_plan.json"
TIMELINE_PATH = "/app/output/mission_timeline.csv"

MU_SUN = 132712440018.0
EARTH_ORBIT_KM = 149598023.0
MARS_ORBIT_KM = 227939366.0
G0 = 9.80665

# Skill-specific constants (non-standard — cannot be derived from first principles)
GRAVITY_LOSS = 0.386
MIDCOURSE_CORRECTION = 0.072
SOLAR_RADIATION_PRESSURE = 0.015
FUEL_RESERVE_PCT = 0.055
SETTLING_LOSS_PCT = 0.008
BOILOFF_RATES = {"LOX/LH2": 0.0005, "LOX/RP-1": 0.00005, "LOX/LCH4": 0.0002}

# Providers known to be suspended in the DB
SUSPENDED_PROVIDERS = {"GreenProp"}

# Spacecraft with expired LOX/LH2 certifications (before 2026)
EXPIRED_LH2_CERTS = {"Helios Mk2", "Olympus Carrier"}


@pytest.fixture(scope="module")
def plan():
    assert os.path.exists(PLAN_PATH), f"Mission plan not found at {PLAN_PATH}"
    with open(PLAN_PATH) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def timeline_rows():
    assert os.path.exists(TIMELINE_PATH), f"Timeline not found at {TIMELINE_PATH}"
    with open(TIMELINE_PATH) as f:
        return list(csv.DictReader(f))


def test_plan_structure(plan):
    """Plan has required sections, targets Mars, mission type cargo."""
    required = {
        "mission", "target_planet", "mission_type",
        "launch_window", "spacecraft", "orbital_mechanics",
        "fuel_budget", "fuel_provider", "cost_breakdown",
    }
    missing = required - set(plan.keys())
    assert not missing, f"Missing top-level keys: {missing}"
    assert plan["target_planet"].lower() == "mars", f"Target is {plan['target_planet']}, expected Mars"
    assert plan["mission_type"] == "cargo", f"Mission type is {plan['mission_type']}, expected cargo"


def test_orbital_mechanics(plan):
    """Correction values match heritage data, components sum, Hohmann math verified."""
    om = plan["orbital_mechanics"]

    # Gravity loss must match the heritage value (0.386), not a generic estimate
    assert abs(om["gravity_loss_km_s"] - GRAVITY_LOSS) < 0.02, \
        f"Gravity loss {om['gravity_loss_km_s']} != expected {GRAVITY_LOSS} from heritage data"

    # Midcourse correction must be 0.072
    assert abs(om["midcourse_correction_km_s"] - MIDCOURSE_CORRECTION) < 0.01, \
        f"Midcourse {om['midcourse_correction_km_s']} != expected {MIDCOURSE_CORRECTION}"

    # Solar radiation pressure must be 0.015
    srp = om.get("solar_radiation_pressure_km_s", 0)
    assert abs(srp - SOLAR_RADIATION_PRESSURE) < 0.005, \
        f"SRP {srp} != expected {SOLAR_RADIATION_PRESSURE}"

    # Components must sum to total
    dv_sum = (om["delta_v1_km_s"] + om["delta_v2_km_s"]
              + om["gravity_loss_km_s"] + om["midcourse_correction_km_s"] + srp)
    assert abs(dv_sum - om["total_delta_v_km_s"]) < 0.01, \
        f"Components sum {dv_sum:.4f} != total {om['total_delta_v_km_s']}"

    # Verify ideal Hohmann delta-v
    r1, r2 = EARTH_ORBIT_KM, MARS_ORBIT_KM
    a_t = (r1 + r2) / 2.0
    v_c1 = math.sqrt(MU_SUN / r1)
    v_p = math.sqrt(MU_SUN * (2.0 / r1 - 1.0 / a_t))
    v_c2 = math.sqrt(MU_SUN / r2)
    v_a = math.sqrt(MU_SUN * (2.0 / r2 - 1.0 / a_t))
    expected_ideal = abs(v_p - v_c1) + abs(v_c2 - v_a)
    ideal = om.get("ideal_total_delta_v_km_s", om["total_delta_v_km_s"])
    assert abs(ideal - expected_ideal) < 0.05, \
        f"Ideal delta-v {ideal} != computed {expected_ideal:.4f}"


def test_transfer_time(plan):
    """Transfer time within 240-300 days and ≤280-day constraint."""
    days = plan["orbital_mechanics"]["transfer_time_days"]
    assert 240 < days < 300, f"Transfer time {days} days outside plausible range"
    assert days <= 280, f"Transfer time {days} exceeds 280-day constraint"


def test_fuel_budget(plan):
    """Fuel includes boil-off, settling, and 5.5% reserve; base matches Tsiolkovsky."""
    fb = plan["fuel_budget"]
    om = plan["orbital_mechanics"]
    dv_m_s = om["total_delta_v_km_s"] * 1000.0
    isp = plan["spacecraft"]["engine_isp_s"]
    dry = plan["spacecraft"]["dry_mass_kg"]
    payload = fb["payload_kg"]
    ve = isp * G0
    expected_base = (dry + payload) * (math.exp(dv_m_s / ve) - 1)

    # Base fuel must match Tsiolkovsky
    base = fb.get("base_fuel_mass_kg", fb["fuel_mass_kg"])
    assert abs(base - expected_base) < expected_base * 0.02, \
        f"Base fuel {base:.0f} != Tsiolkovsky {expected_base:.0f} (±2%)"

    # Total fuel must include boil-off + settling + reserve (not just Tsiolkovsky + flat %)
    fuel_type = plan["fuel_provider"]["fuel_type"]
    boiloff_rate = BOILOFF_RATES.get(fuel_type, 0)
    coast_days = om["transfer_time_days"] - 2
    expected_boiloff = expected_base * boiloff_rate * coast_days
    expected_settling = expected_base * SETTLING_LOSS_PCT
    expected_reserve = expected_base * FUEL_RESERVE_PCT
    expected_total = expected_base + expected_boiloff + expected_settling + expected_reserve

    actual_total = fb["fuel_mass_kg"]
    assert abs(actual_total - expected_total) < expected_total * 0.03, \
        f"Total fuel {actual_total:.0f} != expected {expected_total:.0f} (must include boil-off, settling, 5.5% reserve)"

    # Capacity check
    assert actual_total <= plan["spacecraft"]["max_fuel_capacity_kg"], \
        f"Fuel {actual_total:.0f} exceeds capacity {plan['spacecraft']['max_fuel_capacity_kg']}"


def test_constraints_and_cost(plan):
    """Budget ≤$850M, payload ≥3000kg, reliability ≥0.93, handling surcharge at correct rate."""
    cb = plan["cost_breakdown"]
    assert cb["total_cost_usd"] <= 850_000_000, \
        f"Cost ${cb['total_cost_usd']:,.0f} exceeds $850M"
    assert plan["fuel_budget"]["payload_kg"] >= 3000, \
        f"Payload {plan['fuel_budget']['payload_kg']} kg below 3000 kg"
    assert plan["spacecraft"]["reliability_rating"] >= 0.93, \
        f"Reliability {plan['spacecraft']['reliability_rating']} below 0.93"

    # Handling surcharge must match the skill's non-standard rates
    SURCHARGE_RATES = {"LOX/LH2": 0.11, "LOX/RP-1": 0.045, "LOX/LCH4": 0.07}
    ft = plan["fuel_provider"]["fuel_type"]
    fuel_cost = cb["fuel_cost_usd"]
    expected_surcharge = fuel_cost * SURCHARGE_RATES.get(ft, 0)
    actual_surcharge = cb.get("fuel_handling_surcharge_usd", 0)
    assert abs(actual_surcharge - expected_surcharge) < expected_surcharge * 0.05, \
        f"Handling surcharge ${actual_surcharge:,.0f} != expected ${expected_surcharge:,.0f} ({SURCHARGE_RATES[ft]*100}% of fuel cost)"


def test_provider_and_compatibility(plan):
    """Provider is active (not suspended), fuel compatible with spacecraft, cert not expired."""
    provider_name = plan["fuel_provider"]["name"]
    assert provider_name not in SUSPENDED_PROVIDERS, \
        f"Provider '{provider_name}' is suspended — must use an active provider"

    sc_name = plan["spacecraft"]["name"]
    ft = plan["fuel_provider"]["fuel_type"]

    # If spacecraft has an expired cert for this fuel type, it's invalid
    if ft == "LOX/LH2" and sc_name in EXPIRED_LH2_CERTS:
        pytest.fail(
            f"{sc_name}'s LOX/LH2 certification expired before 2026 — "
            f"cannot use this spacecraft/fuel combination"
        )

    # Standard compatibility check
    compatibility = {
        "Ares Clipper": ["LOX/LH2"],
        "Red Horizon": ["LOX/RP-1", "LOX/LCH4"],
        "Valkyrie Express": ["LOX/LH2"],
        "Titan Hauler": ["LOX/LH2", "LOX/RP-1", "LOX/LCH4"],
        "Pioneer Scout": ["LOX/RP-1"],
        "Mars Dart": ["LOX/LCH4"],
        "Olympus Carrier": ["LOX/RP-1"],
        "Zephyr Light": ["LOX/LH2"],
        "Helios Mk2": ["LOX/LCH4"],
        "Nebula Hauler": ["LOX/RP-1"],
        "StormRider": ["LOX/LCH4"],
        "Aether Prime": ["LOX/LH2"],
        "Cargo King": ["LOX/RP-1"],
        "Mercury Express": ["LOX/LH2"],
        "DeepStar III": ["LOX/LH2", "LOX/LCH4"],
    }
    allowed = compatibility.get(sc_name, [])
    assert ft in allowed, f"Fuel '{ft}' incompatible with {sc_name}. Valid: {allowed}"


def test_timeline(plan, timeline_rows):
    """Timeline has 6 phases, fuel only decreases, total consumed matches budget."""
    phases = {row["phase"] for row in timeline_rows}
    expected = {"Pre-launch", "Launch", "Trans-Mars Injection", "Coast",
                "Mars Orbit Insertion", "Arrival"}
    missing = expected - phases
    assert not missing, f"Timeline missing phases: {missing}"

    fuels = [float(row["fuel_remaining_kg"]) for row in timeline_rows]
    for i in range(1, len(fuels)):
        assert fuels[i] <= fuels[i - 1], \
            f"Fuel increased at phase {i}: {fuels[i-1]} -> {fuels[i]}"

    total_consumed = sum(float(r["fuel_consumed_kg"]) for r in timeline_rows)
    expected_fuel = plan["fuel_budget"]["fuel_mass_kg"]
    assert abs(total_consumed - expected_fuel) < expected_fuel * 0.03, \
        f"Timeline fuel consumed {total_consumed:.0f} != budget {expected_fuel:.0f}"
