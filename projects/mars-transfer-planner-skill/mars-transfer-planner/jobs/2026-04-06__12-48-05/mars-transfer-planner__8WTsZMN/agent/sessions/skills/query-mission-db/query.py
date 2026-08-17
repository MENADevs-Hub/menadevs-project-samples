import sys
sys.path.append('/logs/agent/sessions/skills/query-mission-db/scripts')
from query_mission_db import MissionDB

db = MissionDB()

# Get Mars Cargo 2026 mission constraints
constraints = db.run("get_mission_constraints", constraint_name="Mars Cargo 2026")
print("Mission Constraints:")
print(constraints)
print()

# Get available launch windows for 2026
windows = db.run("get_launch_windows", target_year=2026)
print("Available 2026 Launch Windows:")
for window in windows:
    print(f"  {window}")
print()

# Get basic planet data for Earth and Mars
earth = db.run("get_planet", name="Earth")
mars = db.run("get_planet", name="Mars")
print("Earth data:", earth)
print("Mars data:", mars)