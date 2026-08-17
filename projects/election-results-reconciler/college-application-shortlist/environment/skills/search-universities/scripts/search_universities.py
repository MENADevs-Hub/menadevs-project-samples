"""Utility for searching universities from the bundled dataset."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from pandas import DataFrame


def _find_data_path() -> Path:
    """Find data file, checking container path first, then relative to script."""
    relative = "universities/universities.csv"
    container_path = Path("/app/data") / relative
    if container_path.exists():
        return container_path
    return Path(__file__).resolve().parent.parent.parent / "data" / relative


DEFAULT_DATA_PATH = _find_data_path()


class Universities:
    """Search helper for the universities dataset."""

    def __init__(self, path: str | Path = DEFAULT_DATA_PATH) -> None:
        self.path = Path(path)
        self.data: DataFrame = DataFrame()
        self.load_db()
        print("Universities loaded.")

    def load_db(self) -> None:
        """Load and clean the universities CSV."""
        if not self.path.exists():
            raise FileNotFoundError(f"Universities CSV not found at {self.path}")
        df = pd.read_csv(self.path)
        df["State"] = df["State"].astype(str).str.strip()
        df["Name"] = df["Name"].astype(str).str.strip()
        self.data = df

    def run(self, state: str = "", setting: str = "", uni_type: str = "") -> DataFrame | str:
        """Return universities matching the given filters (case-insensitive).

        Args:
            state: Filter by state name (e.g. 'Ohio')
            setting: Filter by setting ('Urban', 'Suburban', 'Rural')
            uni_type: Filter by type ('Public', 'Private')
        """
        if self.data.empty:
            return "No university data is available."

        results = self.data.copy()
        if state:
            results = results[results["State"].str.lower() == state.strip().lower()]
        if setting:
            results = results[results["Setting"].str.lower() == setting.strip().lower()]
        if uni_type:
            results = results[results["Type"].str.lower() == uni_type.strip().lower()]

        results = results.reset_index(drop=True)
        if results.empty:
            return "No universities match the given criteria."
        return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Search universities.")
    parser.add_argument("--state", "-s", default="", help="State to filter by.")
    parser.add_argument("--setting", default="", help="Setting to filter by.")
    parser.add_argument("--type", default="", dest="uni_type", help="Type to filter by.")
    args = parser.parse_args()
    result = Universities().run(state=args.state, setting=args.setting, uni_type=args.uni_type)
    print(result)


if __name__ == "__main__":
    main()
