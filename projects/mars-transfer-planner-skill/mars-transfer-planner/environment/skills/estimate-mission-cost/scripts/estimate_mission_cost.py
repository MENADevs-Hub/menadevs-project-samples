"""Estimate total mission cost with industry-specific surcharges and actuarial insurance."""

from datetime import datetime


class MissionCostEstimator:
    LAUNCH_OPS = {"cargo": 45_000_000, "crewed": 120_000_000, "flyby": 30_000_000}
    LAUNCH_PAD_RENTAL = 3_800_000
    RANGE_SAFETY_FEE = 1_200_000
    MC_RATE_BASE = 750_000
    MC_RATE_EXTENDED = 1_100_000
    MC_TIER_DAYS = 180
    CONTINGENCY_RATE = 0.085
    HANDLING_SURCHARGE = {"LOX/LH2": 0.11, "LOX/RP-1": 0.045, "LOX/LCH4": 0.07}
    FALL_MONTHS = {9, 10, 11}
    SEASON_PREMIUM_RATE = 0.05
    INSURANCE_TIER1 = 200_000_000
    INSURANCE_TIER2 = 500_000_000

    def _insurance_base_rate(self, combined_reliability):
        if combined_reliability >= 0.90:
            return 0.035
        elif combined_reliability >= 0.85:
            return 0.052
        else:
            return 0.078

    def run(self, fuel_mass_kg, fuel_cost_per_kg, transfer_time_days,
            mission_type, spacecraft_name, fuel_provider_name,
            fuel_type=None, launch_date=None,
            spacecraft_reliability=0.95, fuel_provider_reliability=0.95,
            max_budget_usd=None):
        fuel_cost = fuel_mass_kg * fuel_cost_per_kg
        handling_rate = self.HANDLING_SURCHARGE.get(fuel_type, 0.0) if fuel_type else 0.0
        fuel_handling_surcharge = fuel_cost * handling_rate
        launch_ops = self.LAUNCH_OPS.get(mission_type, self.LAUNCH_OPS["cargo"])

        launch_season_premium = 0.0
        if launch_date:
            month = datetime.strptime(str(launch_date), "%Y-%m-%d").month
            if month in self.FALL_MONTHS:
                launch_season_premium = launch_ops * self.SEASON_PREMIUM_RATE

        if transfer_time_days <= self.MC_TIER_DAYS:
            mission_control = self.MC_RATE_BASE * transfer_time_days
        else:
            mission_control = (self.MC_RATE_BASE * self.MC_TIER_DAYS
                               + self.MC_RATE_EXTENDED * (transfer_time_days - self.MC_TIER_DAYS))

        subtotal_pre_ins = (fuel_cost + fuel_handling_surcharge
                            + launch_ops + launch_season_premium
                            + self.LAUNCH_PAD_RENTAL + self.RANGE_SAFETY_FEE
                            + mission_control)

        combined_rel = spacecraft_reliability * fuel_provider_reliability
        base_rate = self._insurance_base_rate(combined_rel)
        if subtotal_pre_ins <= self.INSURANCE_TIER1:
            insurance = subtotal_pre_ins * base_rate
        elif subtotal_pre_ins <= self.INSURANCE_TIER2:
            insurance = (self.INSURANCE_TIER1 * base_rate
                         + (subtotal_pre_ins - self.INSURANCE_TIER1) * (base_rate + 0.02))
        else:
            insurance = (self.INSURANCE_TIER1 * base_rate
                         + (self.INSURANCE_TIER2 - self.INSURANCE_TIER1) * (base_rate + 0.02)
                         + (subtotal_pre_ins - self.INSURANCE_TIER2) * (base_rate + 0.04))

        subtotal = subtotal_pre_ins + insurance
        contingency = subtotal * self.CONTINGENCY_RATE
        total = subtotal + contingency

        result = {
            "spacecraft_name": spacecraft_name,
            "fuel_provider_name": fuel_provider_name,
            "mission_type": mission_type,
            "fuel_mass_kg": fuel_mass_kg,
            "fuel_cost_per_kg_usd": fuel_cost_per_kg,
            "fuel_cost_usd": round(fuel_cost, 2),
            "fuel_handling_surcharge_usd": round(fuel_handling_surcharge, 2),
            "launch_ops_cost_usd": launch_ops,
            "launch_season_premium_usd": round(launch_season_premium, 2),
            "launch_pad_rental_usd": self.LAUNCH_PAD_RENTAL,
            "range_safety_fee_usd": round(self.RANGE_SAFETY_FEE, 2),
            "mission_control_days": transfer_time_days,
            "mission_control_cost_usd": round(mission_control, 2),
            "insurance_cost_usd": round(insurance, 2),
            "contingency_usd": round(contingency, 2),
            "total_cost_usd": round(total, 2),
        }

        if max_budget_usd is not None:
            result["max_budget_usd"] = max_budget_usd
            result["within_budget"] = total <= max_budget_usd
            result["budget_margin_usd"] = round(max_budget_usd - total, 2)

        return result
