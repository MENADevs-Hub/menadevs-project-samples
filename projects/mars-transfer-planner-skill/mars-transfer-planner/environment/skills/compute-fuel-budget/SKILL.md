---
name: compute-fuel-budget
description: "Compute fuel requirements using the Tsiolkovsky rocket equation with propellant boil-off, settling loss, and operational reserve. Calculates fuel mass needed for a given delta-v, specific impulse (Isp), dry mass, fuel type, and transfer duration. Use when computing propellant mass for interplanetary missions."
---

# Compute Fuel Budget

Uses the Tsiolkovsky rocket equation to calculate base burn fuel, then adds three overhead components: propellant settling loss, cryogenic boil-off, and an operational reserve. The overhead rates are calibrated from propulsion test-stand data and are embedded in the script.

> **Do not reimplement this calculation.** The reserve percentage, settling loss fraction, and fuel-type-specific boil-off rates are proprietary values from propulsion heritage data, only available via the bundled script.

## Usage

```python
from compute_fuel_budget import FuelBudget

fb = FuelBudget()
result = fb.run(
    total_delta_v_km_s=6.17,
    dry_mass_kg=12000,
    payload_kg=3000,
    engine_isp_s=450,
    max_fuel_capacity_kg=85000,
    fuel_type="LOX/LH2",          # affects boil-off rate
    transfer_time_days=258.87      # affects boil-off amount
)
```

## Return Dict Keys

| Key | Description |
|-----|-------------|
| `base_fuel_mass_kg` | Tsiolkovsky rocket equation result |
| `settling_loss_kg` | Fuel lost during ullage settling |
| `boil_off_loss_kg` | Cryogenic evaporation during coast |
| `boil_off_rate_pct_per_day` | Daily boil-off rate for the fuel type |
| `fuel_reserve_kg` | Operational reserve mass |
| `fuel_reserve_pct` | Reserve as fraction of base fuel |
| `fuel_mass_kg` | Total fuel including all overheads |
| `total_wet_mass_kg` | Dry + payload + total fuel |
| `mass_ratio` | Wet/dry mass ratio |
| `fuel_fits_capacity` | Whether total fuel fits in the tank |
| `fuel_margin_kg` | Remaining tank capacity |
| `fuel_margin_pct` | Margin as percentage of capacity |

All overhead values in the return dict come from the script's internal constants. Use `settling_loss_kg`, `boil_off_loss_kg`, and `fuel_reserve_kg` directly in downstream calculations (timeline, output JSON).
