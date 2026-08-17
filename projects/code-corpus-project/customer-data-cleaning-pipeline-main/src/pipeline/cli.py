"""Command-line interface for the customer data cleaning pipeline.

Runs the full pipeline (load -> normalize -> validate -> deduplicate) and logs a summary.
Writing output files (cleaned data, rejected rows, reports) is added in the reporting
feature branch.
"""

from __future__ import annotations

import argparse
import sys

from pipeline.logging_setup import setup_logging
from pipeline.orchestrator import run_pipeline
from pipeline.reporter import write_report


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the pipeline CLI."""
    parser = argparse.ArgumentParser(
        prog="pipeline",
        description=(
            "Clean raw customer CSV exports: load, normalize, validate, "
            "deduplicate, and report."
        ),
    )
    parser.add_argument("--input", help="Path to the raw input CSV file.")
    parser.add_argument("--output", help="Directory for cleaned output and reports.")
    parser.add_argument(
        "--config",
        default="config",
        help="Path to the config directory (default: config).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point for the pipeline CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.input:
        parser.error("--input is required")

    logger = setup_logging()
    result = run_pipeline(args.input, args.config, logger=logger)
    logger.info(
        "summary: input=%d cleaned=%d rejected=%d duplicates=%d",
        result.total_input,
        len(result.cleaned_rows),
        len(result.rejected),
        len(result.duplicates),
    )
    if args.output:
        paths = write_report(result, args.output)
        logger.info("cleaned rows   → %s", paths.cleaned_csv)
        logger.info("rejected rows  → %s", paths.rejected_csv)
        logger.info("duplicates     → %s", paths.duplicates_csv)
        logger.info("quality report → %s", paths.quality_report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
