"""Smoke tests for the base project structure."""

import pipeline
from pipeline.cli import build_parser


def test_version_is_exposed():
    assert pipeline.__version__ == "0.1.0"


def test_parser_has_expected_arguments():
    parser = build_parser()
    args = parser.parse_args(["--input", "in.csv", "--output", "out"])
    assert args.input == "in.csv"
    assert args.output == "out"
    assert args.config == "config"
