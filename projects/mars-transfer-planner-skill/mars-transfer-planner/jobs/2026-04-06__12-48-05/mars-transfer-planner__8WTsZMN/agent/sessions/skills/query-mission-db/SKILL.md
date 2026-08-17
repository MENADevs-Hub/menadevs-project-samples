---
name: query-mission-db
description: "Query the PostgreSQL mission planning database. Contains tables: planets, spacecraft, spacecraft_fuel_compatibility (with certification expiry dates), launch_windows (with deprecated flag), fuel_providers (with active/suspended status), mission_constraints. Use for retrieving mission parameters — the bundled script handles data quality filtering automatically."
---

# Query Mission DB

Connect to the local PostgreSQL database `mission_db` and run queries. The bundled script provides pre-built query methods that handle all data-quality filtering automatically.

> **Use the bundled script for queries.** The database contains invalid entries (expired certifications, suspended providers, deprecated windows, draft constraints) that the script filters out automatically. Writing raw SQL without these filters will return bad data.

## Connection (if needed for raw queries)

```python
import psycopg2
conn = psycopg2.connect(dbname="mission_db", user="postgres", host="localhost")
```

## Schema

| Table | Key Columns |
|-------|------------|
| `planets` | name, orbital_radius_km, mu_km3_s2, radius_km, escape_velocity_km_s |
| `spacecraft` | name, dry_mass_kg, max_fuel_capacity_kg, engine_isp_s, thrust_kn, max_payload_kg, reliability_rating, available |
| `spacecraft_fuel_compatibility` | spacecraft_name, fuel_type, certified, **certification_expiry** |
| `launch_windows` | window_name, open_date, close_date, phase_angle_deg, alignment_quality, delta_v_penalty_pct, **deprecated** |
| `fuel_providers` | provider_name, fuel_type, cost_per_kg_usd, reliability_rating, max_supply_kg, lead_time_days, **status** |
| `mission_constraints` | constraint_name, max_budget_usd, max_transfer_days, min_payload_kg, min_spacecraft_reliability, min_fuel_provider_reliability, target_planet, mission_type |

## Data Quality Hazards

The database contains entries that look valid but are **not usable for current missions**:

- Some fuel certifications have **expired** — the `certification_expiry` column may be before 2026
- Some fuel providers are **suspended** — the `status` column may not be `'active'`
- Some launch windows are **deprecated** — the `deprecated` column may be `TRUE`
- Multiple constraint versions exist — there may be draft/preliminary rows alongside final ones

## Usage (recommended)

```python
from query_mission_db import MissionDB

db = MissionDB()
earth = db.run("get_planet", name="Earth")
spacecraft = db.run("get_available_spacecraft", min_reliability=0.93)
windows = db.run("get_launch_windows", target_year=2026)
providers = db.run("get_fuel_providers", min_reliability=0.92)
constraints = db.run("get_mission_constraints", constraint_name="Mars Cargo 2026")

# Fuel compatibility — filters for non-expired certs automatically
fuel_types = db.run("get_compatible_fuel_types", spacecraft_name="Ares Clipper")
# Compatible providers — filters certs + active status automatically
compatible = db.run("get_compatible_providers", spacecraft_name="Ares Clipper", min_reliability=0.92)
```

All query methods return dicts or lists of dicts with the relevant columns. The script handles certification expiry checks, provider status validation, deprecated window filtering, and exact constraint name matching internally.
