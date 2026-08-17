"""Build a phase-by-phase mission timeline CSV with boil-off and settling."""

import csv
import os
from datetime import datetime, timedelta


class MissionTimeline:
    def run(self, launch_date, transfer_time_days, delta_v1_km_s, delta_v2_km_s,
            total_fuel_kg, spacecraft_name, boil_off_kg=0, settling_loss_kg=0,
            output_path="/app/output/mission_timeline.csv"):
        total_dv = delta_v1_km_s + delta_v2_km_s
        burn_fuel = total_fuel_kg - boil_off_kg - settling_loss_kg
        fuel_tmi = burn_fuel * (delta_v1_km_s / total_dv)
        fuel_moi = burn_fuel * (delta_v2_km_s / total_dv)

        launch = datetime.strptime(launch_date, "%Y-%m-%d")
        phases = []

        # Pre-launch (T-30 to T-0)
        phases.append({
            "phase": "Pre-launch",
            "start_date": (launch - timedelta(days=30)).strftime("%Y-%m-%d"),
            "end_date": (launch - timedelta(days=1)).strftime("%Y-%m-%d"),
            "duration_days": 30, "delta_v_km_s": 0.0,
            "fuel_consumed_kg": 0.0, "fuel_remaining_kg": round(total_fuel_kg, 2),
            "spacecraft": spacecraft_name, "status": "Ground operations and fueling",
        })

        # Launch — settling loss occurs during ullage
        remaining = total_fuel_kg - settling_loss_kg
        phases.append({
            "phase": "Launch",
            "start_date": launch.strftime("%Y-%m-%d"),
            "end_date": launch.strftime("%Y-%m-%d"),
            "duration_days": 1, "delta_v_km_s": 0.0,
            "fuel_consumed_kg": round(settling_loss_kg, 2),
            "fuel_remaining_kg": round(remaining, 2),
            "spacecraft": spacecraft_name, "status": "Ascent to parking orbit",
        })

        # Trans-Mars Injection (1 day)
        tmi_date = launch + timedelta(days=1)
        remaining -= fuel_tmi
        phases.append({
            "phase": "Trans-Mars Injection",
            "start_date": tmi_date.strftime("%Y-%m-%d"),
            "end_date": tmi_date.strftime("%Y-%m-%d"),
            "duration_days": 1, "delta_v_km_s": round(delta_v1_km_s, 4),
            "fuel_consumed_kg": round(fuel_tmi, 2),
            "fuel_remaining_kg": round(remaining, 2),
            "spacecraft": spacecraft_name, "status": "Departure burn complete",
        })

        # Coast — boil-off consumed
        coast_days = max(1, int(transfer_time_days) - 2)
        coast_start = tmi_date + timedelta(days=1)
        coast_end = coast_start + timedelta(days=coast_days - 1)
        remaining -= boil_off_kg
        phases.append({
            "phase": "Coast",
            "start_date": coast_start.strftime("%Y-%m-%d"),
            "end_date": coast_end.strftime("%Y-%m-%d"),
            "duration_days": coast_days, "delta_v_km_s": 0.0,
            "fuel_consumed_kg": round(boil_off_kg, 2),
            "fuel_remaining_kg": round(remaining, 2),
            "spacecraft": spacecraft_name, "status": "Cruise phase",
        })

        # Mars Orbit Insertion (1 day)
        moi_date = coast_end + timedelta(days=1)
        remaining -= fuel_moi
        phases.append({
            "phase": "Mars Orbit Insertion",
            "start_date": moi_date.strftime("%Y-%m-%d"),
            "end_date": moi_date.strftime("%Y-%m-%d"),
            "duration_days": 1, "delta_v_km_s": round(delta_v2_km_s, 4),
            "fuel_consumed_kg": round(fuel_moi, 2),
            "fuel_remaining_kg": round(remaining, 2),
            "spacecraft": spacecraft_name, "status": "Arrival burn complete",
        })

        # Arrival
        arrival_date = moi_date + timedelta(days=1)
        phases.append({
            "phase": "Arrival",
            "start_date": arrival_date.strftime("%Y-%m-%d"),
            "end_date": arrival_date.strftime("%Y-%m-%d"),
            "duration_days": 0, "delta_v_km_s": 0.0,
            "fuel_consumed_kg": 0.0, "fuel_remaining_kg": round(remaining, 2),
            "spacecraft": spacecraft_name, "status": "In Mars orbit",
        })

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        fieldnames = list(phases[0].keys())
        with open(output_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(phases)

        return phases
