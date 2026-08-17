#!/bin/bash

set -e
echo "=== solve.sh starting ==="
echo "PWD: $(pwd)"
echo "Contents of /app:"
ls -la /app/ || echo "Cannot list /app"
echo "Contents of /app/skills:"
ls -la /app/skills/ || echo "Cannot list /app/skills"

python3 <<'PYEOF'
import json
import os
import sys
from pathlib import Path

import pandas as pd

print("=== Python script starting ===")
print(f"CWD: {os.getcwd()}")

base_dir = Path(os.getcwd())

# Resolve skills directory and add script paths
skills_roots = [
    Path("/app/skills"),
    base_dir / "environment" / "skills",
    base_dir / "skills",
]

for root in skills_roots:
    print(f"Checking root: {root}, exists: {root.exists()}")
    if not root.exists():
        continue
    for skill in [
        "search-universities",
        "search-programs",
        "search-scholarships",
        "search-housing",
        "compute-affordability",
        "build-comparison-matrix",
    ]:
        skill_path = root / skill / "scripts"
        print(f"  Adding to path: {skill_path}, exists: {skill_path.exists()}")
        sys.path.append(str(skill_path))

print("Attempting imports...")
from search_universities import Universities
from search_programs import Programs
from search_scholarships import Scholarships
from search_housing import Housing
from compute_affordability import AffordabilityCalculator
from build_comparison_matrix import ComparisonMatrix
print("All imports successful.")

# ── constraints from the instruction ──
MAX_TUITION = 40000
TARGET_PROGRAM = "Computer Science"
MIN_SCHOLARSHIP = 10000
REQUIRED_HOUSING_YEARS = 1
EXCLUDED_SETTINGS = {"rural"}
SHORTLIST_SIZE = 5

# ── criteria weights for comparison matrix ──
WEIGHTS = {
    "program_ranking": 0.30,
    "net_annual_cost": 0.25,
    "roi_ratio": 0.20,
    "avg_starting_salary": 0.15,
    "housing_guaranteed_years": 0.10,
}

# ────────────────────────────────────────────
# Stage 1: Search & Filter (4 search skills)
# ────────────────────────────────────────────

# 1. Get all non-rural universities
unis = Universities()
all_unis = unis.run()
setting_mask = ~all_unis["Setting"].str.lower().isin(EXCLUDED_SETTINGS)
candidate_unis = all_unis[setting_mask]
candidate_names = set(candidate_unis["Name"].str.lower())
print(f"Non-rural universities: {len(candidate_names)}")

# 2. CS programs under budget
programs = Programs()
cs_programs = programs.run(program=TARGET_PROGRAM)
if isinstance(cs_programs, str):
    raise SystemExit("No CS programs found.")
cs = cs_programs[cs_programs["Annual Tuition Out-of-State"] <= MAX_TUITION]
cs = cs[cs["University"].str.lower().isin(candidate_names)].reset_index(drop=True)
print(f"CS programs under ${MAX_TUITION}: {len(cs)}")

# 3. Filter for guaranteed housing
housing = Housing()
all_housing = housing.run()
if isinstance(all_housing, str):
    raise SystemExit("No housing data found.")
guaranteed = all_housing[all_housing["Guaranteed Years"] >= REQUIRED_HOUSING_YEARS]
housing_names = set(guaranteed["University"].str.lower())
cs = cs[cs["University"].str.lower().isin(housing_names)].reset_index(drop=True)
print(f"After housing filter: {len(cs)}")

# 4. Filter for merit scholarships >= $10K
scholarships = Scholarships()
big_schol = scholarships.run(min_amount=MIN_SCHOLARSHIP, scholarship_type="Merit")
if isinstance(big_schol, str):
    schol_names = set()
else:
    schol_names = set(big_schol["University"].str.lower())
cs = cs[cs["University"].str.lower().isin(schol_names)].reset_index(drop=True)
print(f"After scholarship filter: {len(cs)}")

# Sort by program ranking then tuition, take top N
cs = cs.sort_values(
    by=["Program Ranking", "Annual Tuition Out-of-State"],
    ascending=[True, True],
).reset_index(drop=True)
shortlist_df = cs.head(SHORTLIST_SIZE)
print(f"Selected {len(shortlist_df)} candidates")

# ────────────────────────────────────────────
# Stage 2: Compute Affordability (analytical)
# ────────────────────────────────────────────

calc = AffordabilityCalculator()
shortlist = []
matrix_candidates = []

for _, row in shortlist_df.iterrows():
    uni_name = row["University"]
    tuition = float(row["Annual Tuition Out-of-State"])
    salary = float(row["Avg Starting Salary"])

    # Get university metadata
    uni_row = all_unis[all_unis["Name"].str.lower() == uni_name.lower()].iloc[0]
    city = uni_row["City"]
    state = uni_row["State"]
    setting = uni_row["Setting"]

    # Get best scholarship
    uni_schol = scholarships.run(university=uni_name, min_amount=MIN_SCHOLARSHIP, scholarship_type="Merit")
    if isinstance(uni_schol, str):
        best_schol_amount = 0
        best_schol_name = "-"
    else:
        best = uni_schol.sort_values("Amount", ascending=False).iloc[0]
        best_schol_amount = int(best["Amount"])
        best_schol_name = best["Scholarship Name"]

    # Get housing cost (dorm)
    uni_housing = housing.run(university=uni_name)
    if isinstance(uni_housing, str):
        monthly_housing = 1000
        guaranteed_yrs = 0
    else:
        dorm = uni_housing[uni_housing["Housing Type"].str.contains("Dorm", case=False)]
        if dorm.empty:
            dorm = uni_housing.iloc[[0]]
        h = dorm.iloc[0]
        monthly_housing = float(h["Monthly Cost"])
        guaranteed_yrs = int(h["Guaranteed Years"])

    # Compute 4-year affordability projection
    projection = calc.run(
        annual_tuition=tuition,
        scholarship_amount=float(best_schol_amount),
        monthly_housing_cost=monthly_housing,
        city=city,
        avg_starting_salary=salary,
    )

    net_annual = projection["total_4yr_net_cost"] / 4.0

    entry = {
        "university": uni_name,
        "state": state,
        "city": city,
        "setting": setting,
        "program": TARGET_PROGRAM,
        "program_ranking": int(row["Program Ranking"]),
        "annual_tuition_out_of_state": int(tuition),
        "best_scholarship": best_schol_name,
        "best_scholarship_amount": best_schol_amount,
        "monthly_housing_cost": int(monthly_housing),
        "housing_guaranteed_years": guaranteed_yrs,
        "has_co_op": str(row.get("Has Co-op", "No")).lower() == "yes",
        "avg_starting_salary": int(salary),
        "total_4yr_net_cost": projection["total_4yr_net_cost"],
        "roi_ratio": projection["roi_ratio"],
        "payback_years": projection["payback_years"],
        "col_factor": projection["col_factor"],
        "yearly_breakdown": projection["yearly_breakdown"],
    }
    shortlist.append(entry)

    # Prepare flattened candidate for matrix scoring
    matrix_candidates.append({
        "university": uni_name,
        "program_ranking": int(row["Program Ranking"]),
        "net_annual_cost": round(net_annual, 2),
        "roi_ratio": projection["roi_ratio"],
        "avg_starting_salary": int(salary),
        "housing_guaranteed_years": guaranteed_yrs,
    })

# ────────────────────────────────────────────
# Stage 3: Build Comparison Matrix (analytical)
# ────────────────────────────────────────────

out_dir = os.environ.get("OUTPUT_DIR", "/app/output")
os.makedirs(out_dir, exist_ok=True)

matrix = ComparisonMatrix()
matrix_df = matrix.run(
    candidates=matrix_candidates,
    weights=WEIGHTS,
    output_path=os.path.join(out_dir, "comparison_matrix.csv"),
)

# Re-rank shortlist by composite score order
score_order = {row["university"]: row["rank"] for _, row in matrix_df.iterrows()}
for entry in shortlist:
    entry["composite_rank"] = score_order.get(entry["university"], 99)
shortlist.sort(key=lambda e: e["composite_rank"])
for i, entry in enumerate(shortlist, 1):
    entry["rank"] = i

# Write shortlist JSON
output = {
    "shortlist": shortlist,
    "criteria": {
        "program": TARGET_PROGRAM,
        "max_annual_tuition": MAX_TUITION,
        "min_scholarship_amount": MIN_SCHOLARSHIP,
        "required_housing_guaranteed_years": REQUIRED_HOUSING_YEARS,
        "excluded_settings": list(EXCLUDED_SETTINGS),
        "weights": WEIGHTS,
    },
    "tools_called": [
        "search_universities",
        "search_programs",
        "search_scholarships",
        "search_housing",
        "compute_affordability",
        "build_comparison_matrix",
    ],
}

out_path = os.path.join(out_dir, "shortlist.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)
print(f"=== SUCCESS: shortlist.json written to {out_path} ===")
print(f"=== SUCCESS: comparison_matrix.csv written ===")

PYEOF

echo "=== solve.sh completed ==="
