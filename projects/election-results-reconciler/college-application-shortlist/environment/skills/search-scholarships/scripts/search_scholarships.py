"""Utility for searching scholarships by university."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from pandas import DataFrame


def _find_data_path() -> Path:
    """Find data file, checking container path first, then relative to script."""
    relative = "scholarships/scholarships.csv"
    container_path = Path("/app/data") / relative
    if container_path.exists():
        return container_path
    return Path(__file__).resolve().parent.parent.parent / "data" / relative


DEFAULT_DATA_PATH = _find_data_path()


class Scholarships:
    """Search helper for the scholarships dataset."""

    def __init__(self, path: str | Path = DEFAULT_DATA_PATH) -> None:
        self.path = Path(path)
        self.data: DataFrame = DataFrame()
        self.load_db()
        print("Scholarships loaded.")

    def load_db(self) -> None:
        """Load and clean the scholarships CSV."""
        if not self.path.exists():
            raise FileNotFoundError(f"Scholarships CSV not found at {self.path}")
        df = pd.read_csv(self.path)
        df["University"] = df["University"].astype(str).str.strip()
        self.data = df

    def run(self, university: str = "", min_amount: int = 0, scholarship_type: str = "") -> DataFrame | str:
        """Return scholarships matching the given filters.

        Args:
            university: Filter by university name (e.g. 'Purdue University')
            min_amount: Minimum scholarship amount (e.g. 10000)
            scholarship_type: Filter by type ('Merit', 'Need', 'Need + Merit')
        """
        if self.data.empty:
            return "No scholarship data is available."

        results = self.data.copy()
        if university:
            results = results[results["University"].str.lower() == university.strip().lower()]
        if min_amount > 0:
            results = results[results["Amount"] >= min_amount]
        if scholarship_type:
            results = results[results["Type"].str.lower() == scholarship_type.strip().lower()]

        results = results.reset_index(drop=True)
        if results.empty:
            return "No scholarships match the given criteria."
        return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Search scholarships.")
    parser.add_argument("--university", "-u", default="", help="University to filter by.")
    parser.add_argument("--min-amount", type=int, default=0, help="Minimum scholarship amount.")
    parser.add_argument("--type", default="", dest="scholarship_type", help="Scholarship type.")
    args = parser.parse_args()
    result = Scholarships().run(
        university=args.university,
        min_amount=args.min_amount,
        scholarship_type=args.scholarship_type,
    )
    print(result)


if __name__ == "__main__":
    main()
