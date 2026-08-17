import sys
sys.path.append('/logs/agent/sessions/skills/build-mission-timeline/scripts')
from build_mission_timeline import MissionTimeline

mt = MissionTimeline()

# Values from previous calculations
result = mt.run(
    launch_date="2026-10-20",                    # 2026-Beta launch window
    transfer_time_days=258.87,                   # From Hohmann transfer
    delta_v1_km_s=2.997692,                     # TMI burn from Hohmann
    delta_v2_km_s=2.696574,                     # MOI burn from Hohmann
    total_fuel_kg=43544.88,                     # Total fuel from fuel budget
    spacecraft_name="Valkyrie Express",
    boil_off_kg=4694.08,                        # Boil-off loss from fuel budget
    settling_loss_kg=292.39,                    # Settling loss from fuel budget
    output_path="/app/output/mission_timeline.csv"
)

print("Mission Timeline Generated!")
print(f"Phases: {len(result)}")
print("\nPhase Summary:")
for phase in result:
    print(f"  {phase['phase']}: {phase['start_date']} to {phase['end_date']} "
          f"({phase['duration_days']} days, ΔV={phase['delta_v_km_s']} km/s, "
          f"fuel consumed={phase['fuel_consumed_kg']} kg)")

print(f"\nTimeline saved to: /app/output/mission_timeline.csv")