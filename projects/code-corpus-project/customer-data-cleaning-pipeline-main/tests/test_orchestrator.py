"""End-to-end integration tests for the pipeline orchestrator and CLI."""

from pipeline.cli import main
from pipeline.orchestrator import run_pipeline


def test_run_pipeline_on_sample(project_root, sample_raw_csv):
    result = run_pipeline(sample_raw_csv, project_root / "config")

    assert result.total_input == 10
    # every input row ends up either cleaned, rejected, or removed as a duplicate
    valid_count = len(result.cleaned_rows) + len(result.duplicates)
    assert valid_count + len(result.rejected) == result.total_input
    # the sample has known-bad rows and at least one duplicate pair
    assert len(result.rejected) > 0
    assert len(result.duplicates) >= 1


def test_cleaned_rows_are_normalized(project_root, sample_raw_csv):
    result = run_pipeline(sample_raw_csv, project_root / "config")
    for row in result.cleaned_rows:
        assert row["email"] == row["email"].lower()
        if row.get("phone"):
            assert row["phone"].startswith("+")


def test_cli_main_runs_on_sample(project_root, sample_raw_csv):
    exit_code = main(["--input", str(sample_raw_csv), "--config", str(project_root / "config")])
    assert exit_code == 0
