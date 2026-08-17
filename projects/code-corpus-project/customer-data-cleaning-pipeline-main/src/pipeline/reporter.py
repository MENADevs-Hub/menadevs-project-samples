"""Output stage: write cleaned data, rejected rows, duplicates, and a quality report.

Writes four files to the output directory:
- cleaned.csv:    rows that passed validation and deduplication
- rejected.csv:   one row per rule violation (a row with two violations appears twice)
- duplicates.csv: rows removed as near-duplicates, with the similarity score appended
- report.json:    summary counts and a data-quality score (cleaned / total_input)
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

from pipeline.deduplicator import DuplicateRow
from pipeline.orchestrator import PipelineResult
from pipeline.validators import RejectedRow


@dataclass
class ReportSummary:
    """Paths of the four files written by write_report."""

    cleaned_csv: Path
    rejected_csv: Path
    duplicates_csv: Path
    quality_report: Path


def write_report(result: PipelineResult, output_dir: str | Path) -> ReportSummary:
    """Write all pipeline outputs to output_dir and return the file paths."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    paths = ReportSummary(
        cleaned_csv=out / "cleaned.csv",
        rejected_csv=out / "rejected.csv",
        duplicates_csv=out / "duplicates.csv",
        quality_report=out / "report.json",
    )
    _write_cleaned(result.cleaned_rows, paths.cleaned_csv)
    _write_rejected(result.rejected, paths.rejected_csv)
    _write_duplicates(result.duplicates, paths.duplicates_csv)
    _write_quality_report(result, paths.quality_report)
    return paths


def _write_cleaned(rows: list[dict[str, str]], path: Path) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _write_rejected(rejected: list[RejectedRow], path: Path) -> None:
    """Write one row per violation so every failure is individually auditable."""
    if not rejected:
        path.write_text("", encoding="utf-8")
        return
    row_fields = list(rejected[0].row.keys())
    fieldnames = row_fields + ["violation_field", "violation_rule", "violation_code"]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for item in rejected:
            for v in item.violations:
                writer.writerow(
                    {
                        **item.row,
                        "violation_field": v.field,
                        "violation_rule": v.rule,
                        "violation_code": v.code,
                    }
                )


def _write_duplicates(duplicates: list[DuplicateRow], path: Path) -> None:
    if not duplicates:
        path.write_text("", encoding="utf-8")
        return
    row_fields = list(duplicates[0].row.keys())
    fieldnames = row_fields + ["similarity_score"]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for dup in duplicates:
            writer.writerow({**dup.row, "similarity_score": f"{dup.score:.4f}"})


def _write_quality_report(result: PipelineResult, path: Path) -> None:
    total = result.total_input
    cleaned = len(result.cleaned_rows)
    rejected = len(result.rejected)
    duplicates = len(result.duplicates)
    quality_score = round(cleaned / total, 4) if total > 0 else 0.0
    report = {
        "total_input": total,
        "cleaned": cleaned,
        "rejected": rejected,
        "duplicates": duplicates,
        "quality_score": quality_score,
    }
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
