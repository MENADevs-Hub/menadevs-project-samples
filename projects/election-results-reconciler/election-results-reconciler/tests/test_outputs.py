"""
Tests for election-results-reconciler task.

Verifies /root/audit_report.json contains correct discrepancies between
official_results.csv and tally_sheets.json:

Known discrepancies (6 total):
  - North Ward / Maria Chen:     vote_count_mismatch, diff=2,   severity=low
  - South Ward / James Walker:   impossible_value,    diff=3744, severity=high
  - West Ward  / Sofia Rivera:   vote_count_mismatch, diff=14,  severity=medium
  - Central    / Maria Chen:     vote_count_mismatch, diff=150, severity=high
  - University District / Sofia Rivera: candidate_missing,       severity=high
  - Harbor Area:                 precinct_missing,               severity=high
"""

import json

import pytest

REPORT_PATH = "/root/audit_report.json"


@pytest.fixture(scope="module")
def report():
    with open(REPORT_PATH, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def discrepancies(report):
    return report["discrepancies"]


@pytest.fixture(scope="module")
def summary(report):
    return report["summary"]


def find(items, precinct, candidate=None, d_type=None):
    for d in items:
        if d.get("precinct") != precinct:
            continue
        if candidate is not None and d.get("candidate") != candidate:
            continue
        if d_type is not None and d.get("discrepancy_type") != d_type:
            continue
        return d
    return None


def test_report_structure(report):
    """Report exists, is valid JSON, and has required top-level keys with correct types."""
    assert "summary" in report, "Missing 'summary' key"
    assert "discrepancies" in report, "Missing 'discrepancies' key"
    assert isinstance(report["discrepancies"], list), "'discrepancies' must be a list"


def test_summary(summary):
    """Summary counts match the 6 known discrepancies: totals, severity breakdown, and type breakdown."""
    assert summary["total_discrepancies"] == 6, \
        f"Expected 6 total discrepancies, got {summary['total_discrepancies']}"

    sev = summary["discrepancies_by_severity"]
    assert sev["low"] == 1, f"Expected 1 low, got {sev['low']}"
    assert sev["medium"] == 1, f"Expected 1 medium, got {sev['medium']}"
    assert sev["high"] == 4, f"Expected 4 high, got {sev['high']}"

    types = summary["discrepancies_by_type"]
    assert types["vote_count_mismatch"] == 3, f"Expected 3 vote_count_mismatch, got {types['vote_count_mismatch']}"
    assert types["impossible_value"] == 1, f"Expected 1 impossible_value, got {types['impossible_value']}"
    assert types["candidate_missing"] == 1, f"Expected 1 candidate_missing, got {types['candidate_missing']}"
    assert types["precinct_missing"] == 1, f"Expected 1 precinct_missing, got {types['precinct_missing']}"


@pytest.mark.parametrize("precinct,candidate,d_type,severity,checks", [
    ("North Ward",        "Maria Chen",   "vote_count_mismatch", "low",    {"official_votes": 1247, "tally_votes": 1249, "difference": 2}),
    ("South Ward",        "James Walker", "impossible_value",    "high",   {"tally_votes": 4500}),
    ("West Ward",         "Sofia Rivera", "vote_count_mismatch", "medium", {"difference": 14}),
    ("Central",           "Maria Chen",   "vote_count_mismatch", "high",   {"difference": 150}),
    ("University District", "Sofia Rivera", "candidate_missing", "high",   {}),
    ("Harbor Area",       None,           "precinct_missing",    "high",   {}),
])
def test_discrepancy(discrepancies, precinct, candidate, d_type, severity, checks):
    """Each known discrepancy is present with the correct type, severity, and numeric fields."""
    d = find(discrepancies, precinct, candidate, d_type)
    assert d is not None, f"Missing discrepancy: {precinct} / {candidate} ({d_type})"
    assert d["discrepancy_type"] == d_type, \
        f"{precinct}: expected type {d_type!r}, got {d['discrepancy_type']!r}"
    assert d["severity"] == severity, \
        f"{precinct}: expected severity {severity!r}, got {d['severity']!r}"
    for field, expected in checks.items():
        assert d[field] == expected, \
            f"{precinct} {field}: expected {expected}, got {d[field]}"
