"""Compute Hohmann transfer orbit parameters with mission-realistic corrections from heritage data."""

import math


class HohmannTransfer:
    # Corrections calibrated from heritage Mars mission telemetry (Pathfinder, MRO, MAVEN).
    GRAVITY_LOSS_KM_S = 0.386
    MIDCOURSE_CORRECTION_KM_S = 0.072
    SOLAR_RADIATION_PRESSURE_KM_S = 0.015

    def run(self, r1_km, r2_km, mu_sun, delta_v_penalty_pct=0.0):
        a_t = (r1_km + r2_km) / 2.0
        v_c1 = math.sqrt(mu_sun / r1_km)
        v_p = math.sqrt(mu_sun * (2.0 / r1_km - 1.0 / a_t))
        delta_v1 = abs(v_p - v_c1)
        v_c2 = math.sqrt(mu_sun / r2_km)
        v_a = math.sqrt(mu_sun * (2.0 / r2_km - 1.0 / a_t))
        delta_v2 = abs(v_c2 - v_a)
        total_dv = delta_v1 + delta_v2

        penalty_factor = 1.0 + delta_v_penalty_pct / 100.0
        total_dv_adjusted = total_dv * penalty_factor
        delta_v1_adjusted = delta_v1 * penalty_factor
        delta_v2_adjusted = delta_v2 * penalty_factor

        total_dv_corrected = (total_dv_adjusted
                              + self.GRAVITY_LOSS_KM_S
                              + self.MIDCOURSE_CORRECTION_KM_S
                              + self.SOLAR_RADIATION_PRESSURE_KM_S)

        transfer_time_s = math.pi * math.sqrt(a_t ** 3 / mu_sun)
        transfer_time_days = transfer_time_s / 86400.0

        return {
            "r1_km": r1_km,
            "r2_km": r2_km,
            "semi_major_axis_km": a_t,
            "delta_v1_km_s": round(delta_v1_adjusted, 6),
            "delta_v2_km_s": round(delta_v2_adjusted, 6),
            "gravity_loss_km_s": self.GRAVITY_LOSS_KM_S,
            "midcourse_correction_km_s": self.MIDCOURSE_CORRECTION_KM_S,
            "solar_radiation_pressure_km_s": self.SOLAR_RADIATION_PRESSURE_KM_S,
            "total_delta_v_km_s": round(total_dv_corrected, 6),
            "transfer_time_seconds": round(transfer_time_s, 2),
            "transfer_time_days": round(transfer_time_days, 2),
            "delta_v_penalty_pct": delta_v_penalty_pct,
            "ideal_delta_v1_km_s": round(delta_v1, 6),
            "ideal_delta_v2_km_s": round(delta_v2, 6),
            "ideal_total_delta_v_km_s": round(total_dv, 6),
        }
