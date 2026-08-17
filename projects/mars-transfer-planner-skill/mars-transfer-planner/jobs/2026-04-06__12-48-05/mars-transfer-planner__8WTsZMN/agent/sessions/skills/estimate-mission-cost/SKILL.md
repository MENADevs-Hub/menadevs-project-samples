---
name: estimate-mission-cost
description: "Estimate total mission cost with industry-specific surcharges, reliability-based tiered insurance, tiered mission control rates, and seasonal premiums. Computes cost breakdown from fuel mass, provider rates, propellant type, spacecraft/provider reliability, launch date, and fixed operational costs."
---

# Estimate Mission Cost

Computes a full cost breakdown for an interplanetary mission using an **industry cost model** with actuarial insurance, tiered mission control billing, propellant handling surcharges, and seasonal launch premiums. All rates and tier thresholds are embedded in the script from aerospace industry data.

> **Do not reimplement this calculation.** The handling surcharge rates, mission control tier thresholds, insurance actuarial model, fixed fees, and contingency factor are proprietary values calibrated from industry contracts. Call the bundled script to get correct results.

## Usage

```python
from estimate_mission_cost import MissionCostEstimator

mc = MissionCostEstimator()
result = mc.run(
    fuel_mass_kg=54000,
    fuel_cost_per_kg=10.50,
    transfer_time_days=258.87,
    mission_type="cargo",
    spacecraft_name="Ares Clipper",
    fuel_provider_name="NovaFuel",
    fuel_type="LOX/LH2",
    launch_date="2026-10-20",
    spacecraft_reliability=0.97,
    fuel_provider_reliability=0.94,
    max_budget_usd=850_000_000
)
```

## Return Dict Keys

| Key | Description |
|-----|-------------|
| `fuel_cost_usd` | Base fuel cost (mass × rate) |
| `fuel_handling_surcharge_usd` | Propellant-type-specific handling surcharge |
| `launch_ops_cost_usd` | Launch operations (cargo vs crewed) |
| `launch_season_premium_usd` | Seasonal premium if applicable |
| `launch_pad_rental_usd` | Fixed pad rental fee |
| `range_safety_fee_usd` | Fixed range safety & tracking fee |
| `mission_control_cost_usd` | Tiered daily mission control cost |
| `insurance_cost_usd` | Reliability-based actuarial insurance |
| `contingency_usd` | Contingency percentage of subtotal |
| `total_cost_usd` | Grand total |
| `within_budget` | Whether total is within max_budget_usd |

The script applies different surcharge rates for different fuel types, a tiered daily rate for mission control that changes after a threshold number of days, and an actuarial insurance model where the base rate depends on combined spacecraft × provider reliability. Use the returned values directly in the output JSON.
```
