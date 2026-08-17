"""Unit tests for the schema-aware CSV loader."""

import pytest

from pipeline.config import load_schema
from pipeline.loader import LoaderError, load_csv


@pytest.fixture
def schema(project_root):
    return load_schema(project_root / "config" / "schema.yaml")


def test_load_real_sample(sample_raw_csv, schema):
    result = load_csv(sample_raw_csv, schema)
    assert len(result.rows) == 10
    assert result.missing_columns == []
    assert result.extra_columns == []


def test_whitespace_is_stripped(tmp_path, schema):
    path = tmp_path / "data.csv"
    path.write_text(
        "customer_id,full_name,email\n1,  John  ,  john@example.com  \n",
        encoding="utf-8",
    )
    result = load_csv(path, schema)
    assert result.rows[0]["full_name"] == "John"
    assert result.rows[0]["email"] == "john@example.com"


def test_missing_required_column_raises(tmp_path, schema):
    path = tmp_path / "data.csv"
    path.write_text("customer_id,full_name\n1,John\n", encoding="utf-8")
    with pytest.raises(LoaderError):
        load_csv(path, schema)


def test_extra_column_is_recorded(tmp_path, schema):
    path = tmp_path / "data.csv"
    path.write_text(
        "customer_id,full_name,email,nickname\n1,John,john@example.com,JJ\n",
        encoding="utf-8",
    )
    result = load_csv(path, schema)
    assert "nickname" in result.extra_columns


def test_empty_file_raises(tmp_path, schema):
    path = tmp_path / "empty.csv"
    path.write_text("", encoding="utf-8")
    with pytest.raises(LoaderError):
        load_csv(path, schema)


def test_missing_file_raises(tmp_path, schema):
    with pytest.raises(LoaderError):
        load_csv(tmp_path / "nope.csv", schema)
