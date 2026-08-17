---
name: compute-reentry-heating
description: "Compute thermal loads and heat shield requirements for atmospheric reentry. Calculates peak heating rate, total heat load, and recommended thermal protection system. Use when planning reentry from orbit to a planetary surface."
---

# Compute Reentry Heating

Calculates reentry thermal loads for atmospheric entry.

## Usage

```python
from compute_reentry_heating import ReentryHeating
rh = ReentryHeating()
result = rh.run(entry_velocity_km_s=7.5, entry_angle_deg=12, vehicle_mass_kg=5000)
```
