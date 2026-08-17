"""Unit tests for the fuzzy deduplication engine."""

from pipeline.config import load_schema
from pipeline.deduplicator import (
    DeduplicationOptions,
    deduplicate,
    load_deduplication_options,
)
from pipeline.loader import load_csv
from pipeline.normalizers import NormalizationOptions, normalize_row

OPTS = DeduplicationOptions()


def test_load_real_options(project_root):
    options = load_deduplication_options(project_root / "config" / "pipeline.yaml")
    assert options.similarity_threshold == 0.9
    assert options.key_fields == ("email", "full_name")


def test_no_duplicates():
    rows = [
        {"email": "ann@example.com", "full_name": "Ann Lee"},
        {"email": "bob@example.com", "full_name": "Bob Fox"},
    ]
    result = deduplicate(rows, OPTS)
    assert len(result.unique_rows) == 2
    assert result.duplicates == []


def test_exact_duplicate_removed():
    rows = [
        {"email": "john@example.com", "full_name": "John Smith"},
        {"email": "john@example.com", "full_name": "John Smith"},
    ]
    result = deduplicate(rows, OPTS)
    assert len(result.unique_rows) == 1
    assert len(result.duplicates) == 1
    assert result.duplicates[0].score == 1.0


def test_near_duplicate_removed():
    rows = [
        {"email": "john@example.com", "full_name": "John Smith"},
        {"email": "john@example.com", "full_name": "John  Smith"},  # extra space
    ]
    result = deduplicate(rows, OPTS)
    assert len(result.unique_rows) == 1
    assert len(result.duplicates) == 1


def test_different_domain_is_not_compared():
    # Same name but different email domains land in different blocks, so they are kept.
    rows = [
        {"email": "alice@gmail.com", "full_name": "Alice Brown"},
        {"email": "alice@yahoo.com", "full_name": "Alice Brown"},
    ]
    result = deduplicate(rows, OPTS)
    assert len(result.unique_rows) == 2
    assert result.duplicates == []


def test_first_occurrence_is_kept():
    rows = [
        {"email": "x@example.com", "full_name": "Sam Tan"},
        {"email": "x@example.com", "full_name": "Sam Tan"},
    ]
    result = deduplicate(rows, OPTS)
    assert result.unique_rows[0] is rows[0]
    assert result.duplicates[0].duplicate_of_index == 0


def test_threshold_is_configurable():
    rows = [
        {"email": "a@example.com", "full_name": "Jon Smith"},
        {"email": "a@example.com", "full_name": "Jonny Smithe"},
    ]
    strict = deduplicate(rows, DeduplicationOptions(similarity_threshold=0.99))
    loose = deduplicate(rows, DeduplicationOptions(similarity_threshold=0.5))
    assert len(strict.duplicates) == 0
    assert len(loose.duplicates) == 1


def test_dedup_on_normalized_sample(project_root, sample_raw_csv):
    schema = load_schema(project_root / "config" / "schema.yaml")
    norm_opts = NormalizationOptions()
    raw_rows = load_csv(sample_raw_csv, schema).rows
    rows = [normalize_row(r, norm_opts) for r in raw_rows]
    result = deduplicate(rows, OPTS)
    # rows 1/3 (John Smith) and 8/9 (Mary Jones) are duplicates
    assert len(result.duplicates) == 2
    assert len(result.unique_rows) == 8
