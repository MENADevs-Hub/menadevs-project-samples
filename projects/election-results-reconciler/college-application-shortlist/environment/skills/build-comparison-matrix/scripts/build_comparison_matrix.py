"""Build a weighted comparison matrix for university selection.

Takes a list of university candidate dicts and criteria weights,
produces a scored pivot-style DataFrame with normalized scores,
weighted scores, and composite totals — exported as CSV.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd


# Default criteria weights (must sum to 1.0)
DEFAULT_WEIGHTS = {
    "program_ranking": 0.30,    # lower is better (inverted)
    "net_annual_cost": 0.25,    # lower is better (inverted)
    "roi_ratio": 0.20,          # higher is better
    "avg_starting_salary": 0.15, # higher is better
    "housing_guaranteed_years": 0.10, # higher is better
}


def _normalize_column(series: pd.Series, invert: bool = False) -> pd.Series:
    """Min-max normalize a series to [0, 1]. If invert=True, lower raw = higher score."""
    min_val = series.min()
    max_val = series.max()
    if max_val == min_val:
        return pd.Series([0.5] * len(series), index=series.index)
    normalized = (series - min_val) / (max_val - min_val)
    if invert:
        normalized = 1.0 - normalized
    return normalized


class ComparisonMatrix:
    """Build a weighted scoring matrix for comparing universities."""

    def __init__(self) -> None:
        print("ComparisonMatrix loaded.")

    def run(
        self,
        candidates: list[dict[str, Any]],
        weights: dict[str, float] | None = None,
        output_path: str | None = None,
    ) -> pd.DataFrame:
        """Score and rank candidates using weighted criteria.

        Args:
            candidates: List of dicts, each with keys matching the weight criteria
                        plus a 'university' key for identification.
            weights: Dict mapping criteria names to weights (should sum to ~1.0).
                     Uses DEFAULT_WEIGHTS if not provided.
            output_path: If provided, writes the matrix as CSV to this path.

        Returns:
            DataFrame with raw values, normalized scores, weighted scores,
            and composite_score column, sorted by composite_score descending.
        """
        if weights is None:
            weights = DEFAULT_WEIGHTS.copy()

        df = pd.DataFrame(candidates)
        if "university" not in df.columns:
            raise ValueError("Each candidate must have a 'university' key.")

        result = df[["university"]].copy()

        # Criteria that are "lower is better" (need inversion)
        invert_criteria = {"program_ranking", "net_annual_cost", "payback_years"}

        composite = pd.Series([0.0] * len(df), index=df.index)

        for criterion, weight in weights.items():
            if criterion not in df.columns:
                continue

            raw_col = f"{criterion}_raw"
            norm_col = f"{criterion}_norm"
            weighted_col = f"{criterion}_weighted"

            result[raw_col] = df[criterion]
            invert = criterion in invert_criteria
            result[norm_col] = _normalize_column(df[criterion].astype(float), invert=invert)
            result[weighted_col] = (result[norm_col] * weight).round(4)
            composite += result[weighted_col]

        result["composite_score"] = composite.round(4)
        result = result.sort_values("composite_score", ascending=False).reset_index(drop=True)
        result.insert(1, "rank", range(1, len(result) + 1))

        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            result.to_csv(output_path, index=False)
            print(f"Comparison matrix written to {output_path}")

        return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Build comparison matrix.")
    parser.add_argument("--input", required=True, help="JSON file with candidates array")
    parser.add_argument("--output", required=True, help="Output CSV path")
    parser.add_argument("--weights", default=None, help="JSON string of weights")
    args = parser.parse_args()

    with open(args.input) as f:
        candidates = json.load(f)

    w = json.loads(args.weights) if args.weights else None
    ComparisonMatrix().run(candidates=candidates, weights=w, output_path=args.output)


if __name__ == "__main__":
    main()
