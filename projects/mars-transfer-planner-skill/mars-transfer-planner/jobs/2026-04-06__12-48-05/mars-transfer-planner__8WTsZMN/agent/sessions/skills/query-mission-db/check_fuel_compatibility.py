import sys
sys.path.append('/logs/agent/sessions/skills/query-mission-db/scripts')
from query_mission_db import MissionDB

db = MissionDB()

# Check fuel compatibility for promising spacecraft
candidates = ["Valkyrie Express", "Ares Clipper", "StormRider", "DeepStar III"]

for spacecraft_name in candidates:
    print(f"\n{spacecraft_name}:")

    # Get compatible fuel types (non-expired)
    fuel_types = db.run("get_compatible_fuel_types", spacecraft_name=spacecraft_name)
    print(f"  Compatible fuel types: {[ft['fuel_type'] for ft in fuel_types]}")

    # Get compatible providers (active, meets reliability)
    providers = db.run("get_compatible_providers",
                      spacecraft_name=spacecraft_name,
                      min_reliability=0.92)
    print(f"  Compatible providers:")
    for provider in providers:
        print(f"    {provider['provider_name']}: {provider['fuel_type']}, ${provider['cost_per_kg_usd']}/kg, reliability={provider['reliability_rating']}, max_supply={provider['max_supply_kg']}kg")