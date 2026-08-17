"""Pipeline orchestrator: chains the cleaning stages end to end.

Order: load -> normalize -> validate -> deduplicate. Normalization runs before
validation and deduplication so those stages operate on cleaned values (lowercased
emails, normalized phones, collapsed whitespace).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from pipeline.config import load_schema
from pipeline.deduplicator import DuplicateRow, deduplicate, load_deduplication_options
from pipeline.loader import load_csv
from pipeline.normalizers import load_normalization_options, normalize_row
from pipeline.validators import RejectedRow, load_rules, validate_rows


@dataclass
class PipelineResult:
    """The outcome of a full pipeline run."""

    cleaned_rows: list[dict[str, str]] = field(default_factory=list)
    rejected: list[RejectedRow] = field(default_factory=list)
    duplicates: list[DuplicateRow] = field(default_factory=list)
    total_input: int = 0


def run_pipeline(
    input_path: str | Path,
    config_dir: str | Path = "config",
    logger: logging.Logger | None = None,
) -> PipelineResult:
    """Run the full cleaning pipeline and return the result."""
    log = logger or logging.getLogger("pipeline")
    config_dir = Path(config_dir)

    schema = load_schema(config_dir / "schema.yaml")
    rules = load_rules(config_dir / "validation_rules.yaml")
    norm_options = load_normalization_options(config_dir / "pipeline.yaml")
    dedup_options = load_deduplication_options(config_dir / "pipeline.yaml")

    load_result = load_csv(input_path, schema)
    log.info("loaded %d rows from %s", len(load_result.rows), input_path)
    if load_result.extra_columns:
        log.warning("unexpected extra columns: %s", ", ".join(load_result.extra_columns))

    normalized = [normalize_row(row, norm_options) for row in load_result.rows]
    log.info("normalized %d rows", len(normalized))

    validation = validate_rows(normalized, rules)
    log.info(
        "validated rows: %d valid, %d rejected",
        len(validation.valid_rows),
        len(validation.rejected),
    )

    dedup = deduplicate(validation.valid_rows, dedup_options)
    log.info(
        "deduplicated: %d unique, %d duplicates",
        len(dedup.unique_rows),
        len(dedup.duplicates),
    )

    return PipelineResult(
        cleaned_rows=dedup.unique_rows,
        rejected=validation.rejected,
        duplicates=dedup.duplicates,
        total_input=len(load_result.rows),
    )
