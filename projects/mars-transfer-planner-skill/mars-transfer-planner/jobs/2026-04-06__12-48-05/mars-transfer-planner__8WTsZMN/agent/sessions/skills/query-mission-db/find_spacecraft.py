import sys
sys.path.append('/logs/agent/sessions/skills/query-mission-db/scripts')
from query_mission_db import MissionDB

db = MissionDB()

# Mission constraints
min_reliability = 0.93
min_payload = 3000  # kg

# Get suitable spacecraft
spacecraft = db.run("get_suitable_spacecraft",
                   min_reliability=min_reliability,
                   min_payload=min_payload)

print("Suitable Spacecraft:")
for sc in spacecraft:
    print(f"  {sc['name']}: dry_mass={sc['dry_mass_kg']}kg, payload={sc['max_payload_kg']}kg, fuel_cap={sc['max_fuel_capacity_kg']}kg, isp={sc['engine_isp_s']}s, reliability={sc['reliability_rating']}")

# Also get all available spacecraft for comparison
all_spacecraft = db.run("get_available_spacecraft", min_reliability=0.0)
print(f"\nTotal available spacecraft: {len(all_spacecraft)}")
print(f"Meeting requirements: {len(spacecraft)}")