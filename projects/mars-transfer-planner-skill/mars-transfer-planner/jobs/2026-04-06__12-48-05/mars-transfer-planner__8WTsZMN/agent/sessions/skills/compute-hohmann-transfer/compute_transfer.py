import sys
sys.path.append('/logs/agent/sessions/skills/compute-hohmann-transfer/scripts')
from compute_hohmann_transfer import HohmannTransfer

# Planet data from database
earth_orbital_radius = 149598023.0  # km
mars_orbital_radius = 227939366.0   # km
mu_sun = 132712440018.0             # km³/s² - standard solar gravitational parameter
launch_window_penalty = 1.8        # % from 2026-Beta launch window

ht = HohmannTransfer()
result = ht.run(
    r1_km=earth_orbital_radius,
    r2_km=mars_orbital_radius,
    mu_sun=mu_sun,
    delta_v_penalty_pct=launch_window_penalty
)

print("Hohmann Transfer Results:")
for key, value in result.items():
    print(f"  {key}: {value}")