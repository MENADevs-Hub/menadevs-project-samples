import sys
sys.path.append('/logs/agent/sessions/skills/estimate-mission-cost/scripts')
from estimate_mission_cost import MissionCostEstimator

mc = MissionCostEstimator()

result = mc.run(
    fuel_mass_kg=43544.88,
    fuel_cost_per_kg=10.5,
    transfer_time_days=258.87,
    mission_type="cargo",
    spacecraft_name="Valkyrie Express",
    fuel_provider_name="NovaFuel",
    fuel_type="LOX/LH2",
    launch_date="2026-10-20",  # 2026-Beta window opens
    spacecraft_reliability=0.98,
    fuel_provider_reliability=0.94,
    max_budget_usd=850_000_000
)

print("Mission Cost Breakdown:")
for key, value in result.items():
    if key.endswith('_usd') or key == 'total_cost_usd':
        print(f"  {key}: ${value:,.2f}")
    else:
        print(f"  {key}: {value}")

print(f"\nBudget Status: {'WITHIN BUDGET' if result['within_budget'] else 'OVER BUDGET'}")
print(f"Budget margin: ${result['budget_margin_usd']:,.2f}")