---
name: build-comparison-matrix
description: Build a weighted scoring matrix to rank university candidates. Takes a list of candidate dicts with numeric criteria, applies configurable weights, normalizes scores, and produces a ranked CSV pivot table. Use this skill when you need to systematically compare and rank options across multiple dimensions.
---

# Build Comparison Matrix

Produce a weighted, normalized comparison matrix as a CSV pivot table.

## Installation

```bash
pip install pandas
```

## Quick Start

```python
from build_comparison_matrix import ComparisonMatrix

candidates = [
    {"university": "School A", "program_ranking": 5, "net_annual_cost": 24000, "roi_ratio": 0.85, "avg_starting_salary": 110000, "housing_guaranteed_years": 2},
    {"university": "School B", "program_ranking": 12, "net_annual_cost": 30000, "roi_ratio": 0.72, "avg_starting_salary": 95000, "housing_guaranteed_years": 1},
]

matrix = ComparisonMatrix()
result = matrix.run(candidates=candidates, output_path="/app/output/comparison_matrix.csv")
print(result)
```

## Parameters

- `candidates` – List of dicts. Each must have `"university"` key plus numeric fields matching the weight keys.
- `weights` – Optional dict mapping criteria → weight (should sum to ~1.0). Defaults:
  - `program_ranking`: 0.30 (lower is better)
  - `net_annual_cost`: 0.25 (lower is better)
  - `roi_ratio`: 0.20 (higher is better)
  - `avg_starting_salary`: 0.15 (higher is better)
  - `housing_guaranteed_years`: 0.10 (higher is better)
- `output_path` – Path to write the CSV. If omitted, returns DataFrame only.

## Output Columns

For each criterion `X`:
- `X_raw` – Original value
- `X_norm` – Min-max normalized to [0, 1] (inverted for "lower is better" criteria)
- `X_weighted` – Normalized × weight

Plus:
- `university` – Name
- `rank` – Final rank (1 = best)
- `composite_score` – Sum of all weighted scores

## Scoring Notes

- **Lower-is-better** criteria (`program_ranking`, `net_annual_cost`) are inverted during normalization so a lower raw value → higher score.
- Weights can be customized per use case.
