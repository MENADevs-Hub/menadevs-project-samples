"""Compute 4-year affordability projections for universities.

Takes tuition, scholarship, housing cost, and cost-of-living data and
produces a detailed financial projection including net cost, total 4-year
cost, and ROI (return on investment) based on expected starting salary.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd


def _find_col_path() -> Path:
    relative = "cost-of-living/cost_of_living.csv"
    container_path = Path("/app/data") / relative
    if container_path.exists():
        return container_path
    return Path(__file__).resolve().parent.parent.parent / "data" / relative


DEFAULT_COL_PATH = _find_col_path()

# Annual cost assumptions beyond tuition
BOOKS_AND_SUPPLIES = 1200        # $/year
PERSONAL_EXPENSES = 2400         # $/year
TUITION_INFLATION_RATE = 0.03    # 3% annual tuition increase
HOUSING_INFLATION_RATE = 0.02    # 2% annual housing cost increase


class AffordabilityCalculator:
    """Computes 4-year net cost and ROI for a university."""

    def __init__(self, col_path: str | Path = DEFAULT_COL_PATH) -> None:
        self.col_data: pd.DataFrame = pd.DataFrame()
        col_p = Path(col_path)
        if col_p.exists():
            self.col_data = pd.read_csv(col_p)
            self.col_data["City"] = self.col_data["City"].astype(str).str.strip()
        print("AffordabilityCalculator loaded.")

    def run(
        self,
        annual_tuition: float,
        scholarship_amount: float,
        monthly_housing_cost: float,
        city: str,
        avg_starting_salary: float,
        years: int = 4,
    ) -> dict[str, Any]:
        """Compute a multi-year cost projection.

        Args:
            annual_tuition: Annual out-of-state tuition ($).
            scholarship_amount: Annual renewable scholarship ($).
            monthly_housing_cost: Monthly on-campus housing ($).
            city: City name for cost-of-living lookup.
            avg_starting_salary: Expected starting salary after graduation ($).
            years: Number of years to project (default 4).

        Returns:
            Dictionary with year-by-year breakdown, totals, and ROI.
        """
        # Lookup cost-of-living multiplier
        col_factor = 1.0
        median_rent = 0
        if not self.col_data.empty and city:
            match = self.col_data[self.col_data["City"].str.lower() == city.lower()]
            if not match.empty:
                col_factor = match.iloc[0]["Overall Index"] / 100.0
                median_rent = int(match.iloc[0]["Median Rent 1BR"])

        yearly_breakdown = []
        total_cost = 0.0
        total_scholarship = 0.0

        for year in range(1, years + 1):
            tuition = annual_tuition * ((1 + TUITION_INFLATION_RATE) ** (year - 1))
            housing = monthly_housing_cost * 12 * ((1 + HOUSING_INFLATION_RATE) ** (year - 1))
            living = (BOOKS_AND_SUPPLIES + PERSONAL_EXPENSES) * col_factor
            gross = tuition + housing + living
            net = gross - scholarship_amount
            total_cost += net
            total_scholarship += scholarship_amount

            yearly_breakdown.append({
                "year": year,
                "tuition": round(tuition, 2),
                "housing": round(housing, 2),
                "living_expenses": round(living, 2),
                "gross_cost": round(gross, 2),
                "scholarship": round(scholarship_amount, 2),
                "net_cost": round(net, 2),
            })

        roi = round(avg_starting_salary / total_cost, 4) if total_cost > 0 else 0.0
        payback_years = round(total_cost / avg_starting_salary, 2) if avg_starting_salary > 0 else 99.0

        return {
            "yearly_breakdown": yearly_breakdown,
            "total_4yr_net_cost": round(total_cost, 2),
            "total_scholarship_value": round(total_scholarship, 2),
            "avg_starting_salary": avg_starting_salary,
            "roi_ratio": roi,
            "payback_years": payback_years,
            "col_factor": round(col_factor, 4),
            "median_city_rent": median_rent,
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute 4-year affordability.")
    parser.add_argument("--tuition", type=float, required=True)
    parser.add_argument("--scholarship", type=float, default=0)
    parser.add_argument("--housing", type=float, required=True)
    parser.add_argument("--city", required=True)
    parser.add_argument("--salary", type=float, required=True)
    args = parser.parse_args()
    import json
    result = AffordabilityCalculator().run(
        annual_tuition=args.tuition,
        scholarship_amount=args.scholarship,
        monthly_housing_cost=args.housing,
        city=args.city,
        avg_starting_salary=args.salary,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
