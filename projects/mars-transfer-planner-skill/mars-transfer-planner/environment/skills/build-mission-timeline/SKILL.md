---
name: build-mission-timeline
description: "Build a phase-by-phase mission timeline CSV for an interplanetary transfer mission. Handles fuel distribution across phases including propellant settling loss at ignition and boil-off during coast. Produces phases: pre-launch, launch, TMI, coast, MOI, arrival."
---

# Build Mission Timeline

Generates a CSV timeline breaking the mission into 6 phases with dates, velocities, fuel consumption, and status. The script handles the non-trivial fuel distribution logic: which losses occur in which phase and how burn fuel is split proportionally across TMI and MOI.

> **Do not reimplement this calculation.** The fuel distribution across phases — where settling loss is consumed, where boil-off is consumed, and how burn fuel is allocated between TMI and MOI — is handled by the script's internal logic. Pass in the values from the fuel budget script and let this script distribute them correctly.

## Usage

```python
from build_mission_timeline import MissionTimeline

mt = MissionTimeline()
result = mt.run(
    launch_date="2026-10-20",
    transfer_time_days=258.87,
    delta_v1_km_s=2.95,          # from compute-hohmann-transfer
    delta_v2_km_s=2.65,          # from compute-hohmann-transfer
    total_fuel_kg=54000,         # from compute-fuel-budget (fuel_mass_kg)
    spacecraft_name="Ares Clipper",
    boil_off_kg=5800,            # from compute-fuel-budget (boil_off_loss_kg)
    settling_loss_kg=360,        # from compute-fuel-budget (settling_loss_kg)
    output_path="/app/output/mission_timeline.csv"
)
# Writes CSV to output_path and returns list of phase dicts
```

## Output CSV Columns

The CSV includes: phase, start_date, end_date, duration_days, delta_v_km_s, fuel_consumed_kg, cumulative_fuel_kg, remaining_fuel_kg, status

## Important

- Pass `boil_off_kg` and `settling_loss_kg` from the fuel budget result — the timeline script distributes these to the correct phases
- The total fuel consumed across all phases should equal `total_fuel_kg` minus the reserve
- Verify that remaining fuel at arrival matches the reserve from the fuel budget
