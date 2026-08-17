"""Tests for the college application shortlist task."""

import csv
import json
import os
from pathlib import Path

import pytest

PLAN_PATH = "/app/output/shortlist.json"
MATRIX_PATH = "/app/output/comparison_matrix.csv"

# Known valid universities from the dataset that pass all filters:
# CS program, out-of-state tuition ≤ $40K, guaranteed housing ≥1yr,
# merit scholarship ≥$10K, non-rural setting.
EXPECTED_VALID_UNIVERSITIES = {
    "university of illinois urbana-champaign",
    "georgia institute of technology",
    "university of washington",
    "university of wisconsin-madison",
    "university of maryland",
    "purdue university",
    "ohio state university",
    "university of texas at austin",
    "university of minnesota",
    "penn state university",
    "university of florida",
    "north carolina state university",
    "texas a&m university",
    "university of colorado boulder",
    "arizona state university",
    "iowa state university",
    "michigan state university",
    "indiana university bloomington",
}


# ──────────────── shortlist.json tests ────────────────


def test_output_file_exists():
    """Shortlist JSON should be produced at the expected path."""
    assert os.path.exists(PLAN_PATH), f"Shortlist JSON not found at {PLAN_PATH}"


def test_matrix_file_exists():
    """Comparison matrix CSV should be produced at the expected path."""
    assert os.path.exists(MATRIX_PATH), f"Comparison matrix CSV not found at {MATRIX_PATH}"


def test_top_level_structure():
    """Output should have shortlist array, criteria object, and tools_called array."""
    with open(PLAN_PATH) as f:
        payload = json.load(f)

    assert isinstance(payload, dict), "Top-level JSON should be an object"
    assert "shortlist" in payload, "Top-level 'shortlist' key missing"
    assert isinstance(payload["shortlist"], list), "'shortlist' should be a list"
    assert len(payload["shortlist"]) == 5, f"Expected 5 universities, got {len(payload['shortlist'])}"


def test_shortlist_required_fields():
    """Each shortlist entry should have required fields including financial projections."""
    with open(PLAN_PATH) as f:
        shortlist = json.load(f)["shortlist"]

    required = {
        "rank", "university", "state", "city", "program",
        "program_ranking", "annual_tuition_out_of_state",
        "total_4yr_net_cost", "roi_ratio",
    }
    for idx, entry in enumerate(shortlist, start=1):
        assert isinstance(entry, dict), f"Entry {idx} must be an object"
        missing = required - set(entry.keys())
        assert not missing, f"Entry {idx} missing fields: {missing}"
        assert entry["rank"] == idx, f"Rank should be sequential; got {entry['rank']} at position {idx}"


def test_all_entries_are_cs_programs():
    """Every shortlisted entry should be for Computer Science."""
    with open(PLAN_PATH) as f:
        shortlist = json.load(f)["shortlist"]

    for entry in shortlist:
        program = entry.get("program", "").lower()
        assert "computer science" in program, (
            f"{entry['university']} has program '{entry.get('program')}', expected Computer Science"
        )


def test_tuition_within_budget():
    """Every shortlisted university should have out-of-state tuition ≤ $40,000."""
    with open(PLAN_PATH) as f:
        shortlist = json.load(f)["shortlist"]

    for entry in shortlist:
        tuition = entry.get("annual_tuition_out_of_state", 999999)
        assert tuition <= 40000, (
            f"{entry['university']} tuition ${tuition} exceeds $40,000 budget"
        )


def test_universities_are_valid_candidates():
    """Every shortlisted university should be in the set of valid candidates from the data."""
    with open(PLAN_PATH) as f:
        shortlist = json.load(f)["shortlist"]

    for entry in shortlist:
        uni_lower = entry["university"].lower()
        assert uni_lower in EXPECTED_VALID_UNIVERSITIES, (
            f"{entry['university']} is not a valid candidate (fails one or more constraints)"
        )


def test_not_rural_setting():
    """Cross-check that no shortlisted university is in a rural setting."""
    unis_path = Path("/app/data/universities/universities.csv")
    if not unis_path.exists():
        pytest.skip("Universities data not found")

    rural_unis = set()
    with open(unis_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("Setting", "").strip().lower() == "rural":
                rural_unis.add(row["Name"].strip().lower())

    with open(PLAN_PATH) as f:
        shortlist = json.load(f)["shortlist"]

    for entry in shortlist:
        uni_lower = entry["university"].lower()
        assert uni_lower not in rural_unis, (
            f"{entry['university']} is in a rural setting"
        )


# ──────────────── affordability computation tests ────────────────


def test_4yr_cost_is_positive_and_plausible():
    """Each entry's total_4yr_net_cost should be positive and between $20K–$200K."""
    with open(PLAN_PATH) as f:
        shortlist = json.load(f)["shortlist"]

    for entry in shortlist:
        cost = entry.get("total_4yr_net_cost", 0)
        assert 20000 < cost < 200000, (
            f"{entry['university']} total_4yr_net_cost={cost} is outside plausible range"
        )


def test_roi_ratio_is_positive():
    """Each entry's ROI ratio should be positive (salary / cost > 0)."""
    with open(PLAN_PATH) as f:
        shortlist = json.load(f)["shortlist"]

    for entry in shortlist:
        roi = entry.get("roi_ratio", 0)
        assert roi > 0, f"{entry['university']} roi_ratio={roi} should be positive"


def test_yearly_breakdown_present_and_4_years():
    """Each entry should have a yearly_breakdown with exactly 4 years."""
    with open(PLAN_PATH) as f:
        shortlist = json.load(f)["shortlist"]

    for entry in shortlist:
        breakdown = entry.get("yearly_breakdown", [])
        assert len(breakdown) == 4, (
            f"{entry['university']} yearly_breakdown has {len(breakdown)} years, expected 4"
        )
        for yr in breakdown:
            assert "year" in yr and "net_cost" in yr and "tuition" in yr, (
                f"{entry['university']} year {yr.get('year')} missing required breakdown fields"
            )


def test_tuition_increases_year_over_year():
    """Tuition in yearly_breakdown should increase each year (inflation)."""
    with open(PLAN_PATH) as f:
        shortlist = json.load(f)["shortlist"]

    for entry in shortlist:
        breakdown = entry.get("yearly_breakdown", [])
        if len(breakdown) < 2:
            continue
        for i in range(1, len(breakdown)):
            assert breakdown[i]["tuition"] >= breakdown[i - 1]["tuition"], (
                f"{entry['university']} tuition should not decrease year-over-year"
            )


# ──────────────── comparison matrix tests ────────────────


def test_matrix_has_all_shortlisted_universities():
    """Comparison matrix should contain all 5 shortlisted universities."""
    import pandas as pd

    matrix = pd.read_csv(MATRIX_PATH)
    with open(PLAN_PATH) as f:
        shortlist = json.load(f)["shortlist"]

    shortlist_names = {e["university"].lower() for e in shortlist}
    matrix_names = set(matrix["university"].str.lower())
    missing = shortlist_names - matrix_names
    assert not missing, f"Matrix is missing universities: {missing}"


def test_matrix_has_composite_score():
    """Matrix CSV should have a composite_score column."""
    import pandas as pd

    matrix = pd.read_csv(MATRIX_PATH)
    assert "composite_score" in matrix.columns, "Matrix missing composite_score column"
    assert matrix["composite_score"].notna().all(), "composite_score has NaN values"


def test_matrix_has_rank_column():
    """Matrix CSV should have rank column with valid sequential values."""
    import pandas as pd

    matrix = pd.read_csv(MATRIX_PATH)
    assert "rank" in matrix.columns, "Matrix missing rank column"
    ranks = sorted(matrix["rank"].tolist())
    assert ranks == list(range(1, len(matrix) + 1)), (
        f"Ranks should be sequential 1..N, got {ranks}"
    )


def test_matrix_has_weighted_columns():
    """Matrix should have at least some normalized and weighted score columns."""
    import pandas as pd

    matrix = pd.read_csv(MATRIX_PATH)
    norm_cols = [c for c in matrix.columns if c.endswith("_norm")]
    weighted_cols = [c for c in matrix.columns if c.endswith("_weighted")]
    assert len(norm_cols) >= 3, f"Expected ≥3 normalized columns, got {norm_cols}"
    assert len(weighted_cols) >= 3, f"Expected ≥3 weighted columns, got {weighted_cols}"


# ──────────────── tools_called test ────────────────


def test_tools_called():
    """Output should list both search and analytical tools as having been called."""
    with open(PLAN_PATH) as f:
        payload = json.load(f)

    tools = set(payload.get("tools_called", []))
    expected_search = {"search_universities", "search_programs", "search_scholarships", "search_housing"}
    expected_analytical = {"compute_affordability", "build_comparison_matrix"}
    matched_search = tools & expected_search
    matched_analytical = tools & expected_analytical
    assert len(matched_search) >= 3, f"Expected ≥3 search tools; got {matched_search}"
    assert len(matched_analytical) >= 1, f"Expected ≥1 analytical tool; got {matched_analytical}"
