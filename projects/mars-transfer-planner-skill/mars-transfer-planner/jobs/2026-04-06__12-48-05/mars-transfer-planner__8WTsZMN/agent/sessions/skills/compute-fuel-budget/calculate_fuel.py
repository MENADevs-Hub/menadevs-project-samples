import sys
sys.path.append('/logs/agent/sessions/skills/compute-fuel-budget/scripts')
from compute_fuel_budget import FuelBudget

fb = FuelBudget()

# Test Valkyrie Express with NovaFuel LOX/LH2
print("=== Valkyrie Express + NovaFuel (LOX/LH2) ===")
result_valkyrie = fb.run(
    total_delta_v_km_s=6.167,
    dry_mass_kg=9500,        # Valkyrie Express dry mass
    payload_kg=3500,         # Full payload capacity
    engine_isp_s=470,        # Valkyrie Express ISP
    max_fuel_capacity_kg=65000,  # Valkyrie Express fuel capacity
    fuel_type="LOX/LH2",
    transfer_time_days=258.87
)

for key, value in result_valkyrie.items():
    print(f"  {key}: {value}")

print(f"\nFuel fits: {'YES' if result_valkyrie['fuel_fits_capacity'] else 'NO'}")
print(f"Required fuel: {result_valkyrie['fuel_mass_kg']:,.0f} kg")
print(f"Tank capacity: {result_valkyrie['max_fuel_capacity_kg']:,.0f} kg")
print(f"Fuel margin: {result_valkyrie['fuel_margin_kg']:,.0f} kg ({result_valkyrie['fuel_margin_pct']:.1f}%)")

# If Valkyrie Express doesn't work, test Ares Clipper
if not result_valkyrie['fuel_fits_capacity']:
    print("\n=== Ares Clipper + NovaFuel (LOX/LH2) ===")
    result_ares = fb.run(
        total_delta_v_km_s=6.167,
        dry_mass_kg=12000,       # Ares Clipper dry mass
        payload_kg=5000,         # Full payload capacity
        engine_isp_s=450,        # Ares Clipper ISP
        max_fuel_capacity_kg=85000,  # Ares Clipper fuel capacity
        fuel_type="LOX/LH2",
        transfer_time_days=258.87
    )

    print(f"Required fuel: {result_ares['fuel_mass_kg']:,.0f} kg")
    print(f"Fuel fits: {'YES' if result_ares['fuel_fits_capacity'] else 'NO'}")
    print(f"Fuel margin: {result_ares['fuel_margin_kg']:,.0f} kg ({result_ares['fuel_margin_pct']:.1f}%)")