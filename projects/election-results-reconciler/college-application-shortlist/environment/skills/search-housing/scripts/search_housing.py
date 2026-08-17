"""Utility for searching campus housing options by university."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from pandas import DataFrame


def _find_data_path() -> Path:
    """Find data file, checking container path first, then relative to script."""
    relative = "housing/housing.csv"
    container_path = Path("/app/data") / relative
    if container_path.exists():
        return container_path
    return Path(__file__).resolve().parent.parent.parent / "data" / relative


DEFAULT_DATA_PATH = _find_data_path()


class Housing:
    """Search helper for the campus housing dataset."""

    def __init__(self, path: str | Path = DEFAULT_DATA_PATH) -> None:
        self.path = Path(path)
        self.data: DataFrame = DataFrame()
        self.load_db()
        print("Housing loaded.")

    def load_db(self) -> None:
        """Load and clean the housing CSV."""
        if not self.path.exists():
            raise FileNotFoundError(f"Housing CSV not found at {self.path}")
        df = pd.read_csv(self.path)
        df["University"] = df["University"].astype(str).str.strip()
        self.data = df

    def run(self, university: str = "", housing_type: str = "") -> DataFrame | str:
        """Return housing options matching the given filters.

        Args:
            university: Filter by university name (e.g. 'Purdue University')
            housing_type: Filter by housing type (e.g. 'On-Campus Dorm')
        """
        if self.data.empty:
            return "No housing data is available."

        results = self.data.copy()
        if university:
            results = results[results["University"].str.lower() == university.strip().lower()]
        if housing_type:
            results = results[results["Housing Type"].str.lower() == housing_type.strip().lower()]

        results = results.reset_index(drop=True)
        if results.empty:
            return "No housing options match the given criteria."
        return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Search campus housing.")
    parser.add_argument("--university", "-u", default="", help="University to filter by.")
    parser.add_argument("--type", default="", dest="housing_type", help="Housing type.")
    args = parser.parse_args()
    result = Housing().run(university=args.university, housing_type=args.housing_type)
    print(result)


if __name__ == "__main__":
    main()
