"""Tests for the reporter output stage."""

from __future__ import annotations

import csv
import json

from pipeline.cli import main
from pipeline.orchestrator import run_pipeline
from pipeline.reporter import ReportSummary, write_report


def test_write_report_returns_summary(project_root, sample_raw_csv, tmp_path):
    result = run_pipeline(sample_raw_csv, project_root / "config")
    summary = write_report(result, tmp_path)
    assert isinstance(summary, ReportSummary)


def test_all_output_files_are_created(project_root, sample_raw_csv, tmp_path):
    result = run_pipeline(sample_raw_csv, project_root / "config")
    summary = write_report(result, tmp_path)
    assert summary.cleaned_csv.exists()
    assert summary.rejected_csv.exists()
    assert summary.duplicates_csv.exists()
    assert summary.quality_report.exists()


def test_cleaned_csv_row_count_matches(project_root, sample_raw_csv, tmp_path):
    result = run_pipeline(sample_raw_csv, project_root / "config")
    summary = write_report(result, tmp_path)
    with summary.cleaned_csv.open() as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == len(result.cleaned_rows)


def test_rejected_csv_has_one_row_per_violation(project_root, sample_raw_csv, tmp_path):
    result = run_pipeline(sample_raw_csv, project_root / "config")
    summary = write_report(result, tmp_path)
    with summary.rejected_csv.open() as f:
        rows = list(csv.DictReader(f))
    expected_violations = sum(len(r.violations) for r in result.rejected)
    assert len(rows) == expected_violations
    assert {"violation_field", "violation_rule", "violation_code"}.issubset(rows[0].keys())


def test_duplicates_csv_has_similarity_score(project_root, sample_raw_csv, tmp_path):
    result = run_pipeline(sample_raw_csv, project_root / "config")
    summary = write_report(result, tmp_path)
    with summary.duplicates_csv.open() as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == len(result.duplicates)
    assert "similarity_score" in rows[0]
    assert float(rows[0]["similarity_score"]) > 0.0


def test_quality_report_counts_sum_to_total(project_root, sample_raw_csv, tmp_path):
    result = run_pipeline(sample_raw_csv, project_root / "config")
    summary = write_report(result, tmp_path)
    with summary.quality_report.open() as f:
        report = json.load(f)
    assert report["total_input"] == result.total_input
    assert report["cleaned"] + report["rejected"] + report["duplicates"] == result.total_input
    assert 0.0 <= report["quality_score"] <= 1.0


def test_write_report_creates_nested_output_dir(project_root, sample_raw_csv, tmp_path):
    result = run_pipeline(sample_raw_csv, project_root / "config")
    nested = tmp_path / "a" / "b" / "c"
    write_report(result, nested)
    assert nested.exists()
    assert (nested / "cleaned.csv").exists()


def test_cli_writes_output_files_when_flag_given(project_root, sample_raw_csv, tmp_path):
    exit_code = main(
        [
            "--input", str(sample_raw_csv),
            "--output", str(tmp_path),
            "--config", str(project_root / "config"),
        ]
    )
    assert exit_code == 0
    assert (tmp_path / "cleaned.csv").exists()
    assert (tmp_path / "rejected.csv").exists()
    assert (tmp_path / "duplicates.csv").exists()
    assert (tmp_path / "report.json").exists()
