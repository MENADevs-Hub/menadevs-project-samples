#!/bin/bash
set -e

# Start PostgreSQL if not already running
su - postgres -c "/usr/lib/postgresql/*/bin/pg_ctl -D /var/lib/postgresql/data -l /tmp/pg.log start" 2>/dev/null || true
sleep 2

mkdir -p /app/output

cd /app

python3 << 'ORACLE'
import sys, json, os

for skill_dir in os.listdir("/app/skills"):
    scripts_path = os.path.join("/app/skills", skill_dir, "scripts")
    if os.path.isdir(scripts_path):
        sys.path.insert(0, scripts_path)

from query_mission_db import MissionDB
from compute_hohmann_transfer import HohmannTransfer
from compute_fuel_budget import FuelBudget
from build_mission_timeline import MissionTimeline
from estimate_mission_cost import MissionCostEstimator

db = MissionDB()

# Step 1: Get mission constraints (exact name match)
constraints = db.run("get_mission_constraints", constraint_name="Mars Cargo 2026")[0]
print(f"Mission: {constraints['constraint_name']}")

# Step 2: Planetary data
earth = db.run("get_planet", name="Earth")[0]
mars = db.run("get_planet", name="Mars")[0]
sun = db.run("get_planet", name="Sun")[0]

# Step 3: Best 2026 launch window (filters deprecated)
windows = db.run("get_launch_windows", target_year=2026)
best_window = windows[0]
print(f"Window: {best_window['window_name']} (alignment={best_window['alignment_quality']})")

# Step 4: Hohmann transfer
ht = HohmannTransfer()
transfer = ht.run(
    r1_km=earth['orbital_radius_km'],
    r2_km=mars['orbital_radius_km'],
    mu_sun=sun['mu_km3_s2'],
    delta_v_penalty_pct=best_window['delta_v_penalty_pct']
)
print(f"Total delta-v: {transfer['total_delta_v_km_s']} km/s")
print(f"Transfer time: {transfer['transfer_time_days']} days")

# Step 5: Find suitable spacecraft
spacecraft_list = db.run("get_suitable_spacecraft",
    min_reliability=constraints['min_spacecraft_reliability'],
    min_payload=constraints['min_payload_kg']
)

# Step 6: Compute fuel budget for each, find viable ones
fb = FuelBudget()
viable = []
for sc in spacecraft_list:
    # Get compatible fuel types (filters expired certs)
    fuel_types = db.run("get_compatible_fuel_types", spacecraft_name=sc['name'])
    if not fuel_types:
        continue
    # Use first compatible fuel type for budget calculation
    ft = fuel_types[0]['fuel_type']
    fuel_result = fb.run(
        total_delta_v_km_s=transfer['total_delta_v_km_s'],
        dry_mass_kg=sc['dry_mass_kg'],
        payload_kg=constraints['min_payload_kg'],
        engine_isp_s=sc['engine_isp_s'],
        max_fuel_capacity_kg=sc['max_fuel_capacity_kg'],
        fuel_type=ft,
        transfer_time_days=transfer['transfer_time_days']
    )
    if fuel_result['fuel_fits_capacity']:
        viable.append((sc, fuel_result, ft))
        print(f"  {sc['name']}: fuel={fuel_result['fuel_mass_kg']:.0f}kg, margin={fuel_result['fuel_margin_pct']:.1f}%")

assert viable, "No viable spacecraft found!"

# Pick spacecraft with best fuel margin
viable.sort(key=lambda x: x[1]['fuel_margin_pct'], reverse=True)
chosen_sc, chosen_fuel, chosen_ft = viable[0]
print(f"Chosen: {chosen_sc['name']} ({chosen_ft})")

# Step 7: Find cheapest compatible active provider
providers = db.run("get_compatible_providers",
    spacecraft_name=chosen_sc['name'],
    min_reliability=constraints['min_fuel_provider_reliability']
)
suitable_providers = [p for p in providers if p['max_supply_kg'] >= chosen_fuel['fuel_mass_kg']]
assert suitable_providers, "No suitable fuel provider!"
chosen_provider = suitable_providers[0]
print(f"Provider: {chosen_provider['provider_name']} @ ${chosen_provider['cost_per_kg_usd']}/kg")

# Step 8: Estimate cost
mc = MissionCostEstimator()
cost = mc.run(
    fuel_mass_kg=chosen_fuel['fuel_mass_kg'],
    fuel_cost_per_kg=chosen_provider['cost_per_kg_usd'],
    transfer_time_days=transfer['transfer_time_days'],
    mission_type=constraints['mission_type'],
    spacecraft_name=chosen_sc['name'],
    fuel_provider_name=chosen_provider['provider_name'],
    fuel_type=chosen_provider['fuel_type'],
    launch_date=str(best_window['open_date']),
    spacecraft_reliability=chosen_sc['reliability_rating'],
    fuel_provider_reliability=chosen_provider['reliability_rating'],
    max_budget_usd=constraints['max_budget_usd']
)
print(f"Total cost: ${cost['total_cost_usd']:,.0f}")

# Step 9: Build timeline
mt = MissionTimeline()
timeline = mt.run(
    launch_date=str(best_window['open_date']),
    transfer_time_days=transfer['transfer_time_days'],
    delta_v1_km_s=transfer['delta_v1_km_s'],
    delta_v2_km_s=transfer['delta_v2_km_s'],
    total_fuel_kg=chosen_fuel['fuel_mass_kg'],
    spacecraft_name=chosen_sc['name'],
    boil_off_kg=chosen_fuel['boil_off_loss_kg'],
    settling_loss_kg=chosen_fuel['settling_loss_kg'],
    output_path="/app/output/mission_timeline.csv"
)
print(f"Timeline: {len(timeline)} phases")

# Step 10: Write mission plan
mission_plan = {
    "mission": constraints['constraint_name'],
    "target_planet": constraints['target_planet'],
    "mission_type": constraints['mission_type'],
    "launch_window": {
        "name": best_window['window_name'],
        "open_date": str(best_window['open_date']),
        "close_date": str(best_window['close_date']),
        "alignment_quality": best_window['alignment_quality'],
        "delta_v_penalty_pct": best_window['delta_v_penalty_pct'],
    },
    "spacecraft": {
        "name": chosen_sc['name'],
        "manufacturer": chosen_sc['manufacturer'],
        "dry_mass_kg": chosen_sc['dry_mass_kg'],
        "engine_isp_s": chosen_sc['engine_isp_s'],
        "thrust_kn": chosen_sc['thrust_kn'],
        "max_fuel_capacity_kg": chosen_sc['max_fuel_capacity_kg'],
        "max_payload_kg": chosen_sc['max_payload_kg'],
        "reliability_rating": chosen_sc['reliability_rating'],
    },
    "orbital_mechanics": {
        "departure_orbit_km": earth['orbital_radius_km'],
        "arrival_orbit_km": mars['orbital_radius_km'],
        "semi_major_axis_km": transfer['semi_major_axis_km'],
        "delta_v1_km_s": transfer['delta_v1_km_s'],
        "delta_v2_km_s": transfer['delta_v2_km_s'],
        "gravity_loss_km_s": transfer['gravity_loss_km_s'],
        "midcourse_correction_km_s": transfer['midcourse_correction_km_s'],
        "solar_radiation_pressure_km_s": transfer['solar_radiation_pressure_km_s'],
        "total_delta_v_km_s": transfer['total_delta_v_km_s'],
        "ideal_total_delta_v_km_s": transfer['ideal_total_delta_v_km_s'],
        "transfer_time_days": transfer['transfer_time_days'],
    },
    "fuel_budget": {
        "base_fuel_mass_kg": chosen_fuel['base_fuel_mass_kg'],
        "settling_loss_kg": chosen_fuel['settling_loss_kg'],
        "boil_off_loss_kg": chosen_fuel['boil_off_loss_kg'],
        "boil_off_rate_pct_per_day": chosen_fuel['boil_off_rate_pct_per_day'],
        "fuel_reserve_kg": chosen_fuel['fuel_reserve_kg'],
        "fuel_reserve_pct": chosen_fuel['fuel_reserve_pct'],
        "fuel_mass_kg": chosen_fuel['fuel_mass_kg'],
        "total_wet_mass_kg": chosen_fuel['total_wet_mass_kg'],
        "mass_ratio": chosen_fuel['mass_ratio'],
        "fuel_margin_pct": chosen_fuel['fuel_margin_pct'],
        "payload_kg": constraints['min_payload_kg'],
    },
    "fuel_provider": {
        "name": chosen_provider['provider_name'],
        "fuel_type": chosen_provider['fuel_type'],
        "cost_per_kg_usd": chosen_provider['cost_per_kg_usd'],
        "reliability_rating": chosen_provider['reliability_rating'],
    },
    "cost_breakdown": cost,
}

with open("/app/output/mission_plan.json", "w") as f:
    json.dump(mission_plan, f, indent=2)

print("\nMission plan written to /app/output/mission_plan.json")
print("Timeline written to /app/output/mission_timeline.csv")

db.close()
ORACLE
