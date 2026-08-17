"""Utility for searching academic programs by university."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from pandas import DataFrame


def _find_data_path() -> Path:
    """Find data file, checking container path first, then relative to script."""
    relative = "programs/programs.csv"
    container_path = Path("/app/data") / relative
    if container_path.exists():
        return container_path
    return Path(__file__).resolve().parent.parent.parent / "data" / relative


DEFAULT_DATA_PATH = _find_data_path()


class Programs:
    """Search helper for the academic programs dataset."""

    def __init__(self, path: str | Path = DEFAULT_DATA_PATH) -> None:
        self.path = Path(path)
        self.data: DataFrame = DataFrame()
        self.load_db()
        print("Programs loaded.")

    def load_db(self) -> None:
        """Load and clean the programs CSV."""
        if not self.path.exists():
            raise FileNotFoundError(f"Programs CSV not found at {self.path}")
        df = pd.read_csv(self.path)
        df["University"] = df["University"].astype(str).str.strip()
        df["Program"] = df["Program"].astype(str).str.strip()
        self.data = df

    def run(self, university: str = "", program: str = "") -> DataFrame | str:
        """Return programs matching the given filters (case-insensitive).

        Args:
            university: Filter by university name (e.g. 'Ohio State University')
            program: Filter by program name (e.g. 'Computer Science')
        """
        if self.data.empty:
            return "No program data is available."

        results = self.data.copy()
        if university:
            results = results[results["University"].str.lower() == university.strip().lower()]
        if program:
            results = results[results["Program"].str.lower() == program.strip().lower()]

        results = results.reset_index(drop=True)
        if results.empty:
            return "No programs match the given criteria."
        return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Search academic programs.")
    parser.add_argument("--university", "-u", default="", help="University to filter by.")
    parser.add_argument("--program", "-p", default="", help="Program name to filter by.")
    args = parser.parse_args()
    result = Programs().run(university=args.university, program=args.program)
    print(result)


if __name__ == "__main__":
    main()
