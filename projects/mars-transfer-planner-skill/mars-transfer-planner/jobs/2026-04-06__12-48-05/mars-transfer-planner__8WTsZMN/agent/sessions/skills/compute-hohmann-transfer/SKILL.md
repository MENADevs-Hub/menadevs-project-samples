---
name: compute-hohmann-transfer
description: "Compute Hohmann transfer orbit parameters between two planets with mission-realistic corrections from heritage flight data. Calculates delta-v for departure and arrival burns, transfer time, gravity losses, mid-course corrections, and solar radiation pressure budget."
---

# Compute Hohmann Transfer

Computes the classical Hohmann transfer orbit between two circular orbits around the Sun, then applies **mission-realistic corrections** calibrated from heritage deep-space mission telemetry (Mars Pathfinder, MRO, MAVEN). The correction constants are embedded in the script and are not published — they must be obtained by calling the script.

> **Do not reimplement this calculation.** The correction model applies penalties to individual burn components before summing, and uses flight-heritage constants that differ from textbook values. Call the bundled script to get correct results.

## Usage

```python
from compute_hohmann_transfer import HohmannTransfer

ht = HohmannTransfer()
result = ht.run(
    r1_km=149598023.0,      # Earth orbital radius
    r2_km=227939366.0,      # Mars orbital radius
    mu_sun=132712440018.0,  # Sun gravitational parameter km³/s²
    delta_v_penalty_pct=1.8 # launch window penalty from database
)
```

## Return Dict Keys

| Key | Description |
|-----|-------------|
| `delta_v1_km_s` | Departure burn delta-v (with penalty applied) |
| `delta_v2_km_s` | Arrival burn delta-v (with penalty applied) |
| `gravity_loss_km_s` | Gravity loss correction value |
| `midcourse_correction_km_s` | Mid-course correction budget |
| `solar_radiation_pressure_km_s` | SRP delta-v correction |
| `total_delta_v_km_s` | Fully corrected total delta-v |
| `ideal_total_delta_v_km_s` | Ideal Hohmann delta-v (no corrections) |
| `transfer_time_seconds` | Transfer time in seconds |
| `transfer_time_days` | Transfer time in days |
| `semi_major_axis_km` | Transfer orbit semi-major axis |

All correction values in the return dict come from the script's internal heritage constants. Use them directly in downstream calculations (fuel budget, output JSON).
