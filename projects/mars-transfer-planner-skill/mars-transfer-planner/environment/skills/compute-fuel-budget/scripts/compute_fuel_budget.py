"""Compute fuel requirements using Tsiolkovsky with boil-off, settling, and reserve."""

import math

G0 = 9.80665


class FuelBudget:
    FUEL_RESERVE_PCT = 0.055
    SETTLING_LOSS_PCT = 0.008
    BOILOFF_RATES = {
        "LOX/LH2": 0.0005,
        "LOX/RP-1": 0.00005,
        "LOX/LCH4": 0.0002,
    }

    def run(self, total_delta_v_km_s, dry_mass_kg, payload_kg, engine_isp_s,
            max_fuel_capacity_kg, fuel_type="LOX/LH2", transfer_time_days=259.0):
        delta_v_m_s = total_delta_v_km_s * 1000.0
        exhaust_velocity = engine_isp_s * G0
        inert_mass = dry_mass_kg + payload_kg
        mass_ratio = math.exp(delta_v_m_s / exhaust_velocity)
        base_fuel_mass = inert_mass * (mass_ratio - 1)

        settling_loss = base_fuel_mass * self.SETTLING_LOSS_PCT
        coast_days = max(0, transfer_time_days - 2)
        boiloff_rate = self.BOILOFF_RATES.get(fuel_type, 0.0)
        boil_off_loss = base_fuel_mass * boiloff_rate * coast_days
        fuel_reserve = base_fuel_mass * self.FUEL_RESERVE_PCT

        fuel_mass = base_fuel_mass + settling_loss + boil_off_loss + fuel_reserve

        fuel_fits = fuel_mass <= max_fuel_capacity_kg
        fuel_margin = max_fuel_capacity_kg - fuel_mass
        fuel_margin_pct = (fuel_margin / max_fuel_capacity_kg) * 100.0 if max_fuel_capacity_kg > 0 else 0.0

        return {
            "total_delta_v_km_s": total_delta_v_km_s,
            "total_delta_v_m_s": round(delta_v_m_s, 2),
            "dry_mass_kg": dry_mass_kg,
            "payload_kg": payload_kg,
            "inert_mass_kg": inert_mass,
            "engine_isp_s": engine_isp_s,
            "exhaust_velocity_m_s": round(exhaust_velocity, 2),
            "mass_ratio": round(mass_ratio, 6),
            "base_fuel_mass_kg": round(base_fuel_mass, 2),
            "settling_loss_kg": round(settling_loss, 2),
            "boil_off_loss_kg": round(boil_off_loss, 2),
            "boil_off_rate_pct_per_day": boiloff_rate * 100,
            "fuel_reserve_kg": round(fuel_reserve, 2),
            "fuel_reserve_pct": self.FUEL_RESERVE_PCT * 100,
            "fuel_mass_kg": round(fuel_mass, 2),
            "total_wet_mass_kg": round(inert_mass + fuel_mass, 2),
            "max_fuel_capacity_kg": max_fuel_capacity_kg,
            "fuel_fits_capacity": fuel_fits,
            "fuel_margin_kg": round(fuel_margin, 2),
            "fuel_margin_pct": round(fuel_margin_pct, 2),
        }
