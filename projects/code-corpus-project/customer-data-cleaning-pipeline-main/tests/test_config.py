"""Unit tests for the config loader."""

import pytest

from pipeline.config import ConfigError, load_schema, load_yaml


def test_load_real_schema(project_root):
    schema = load_schema(project_root / "config" / "schema.yaml")
    assert "email" in schema.column_names
    assert "email" in schema.required_columns()
    assert "phone" not in schema.required_columns()


def test_load_yaml_missing_file(tmp_path):
    with pytest.raises(ConfigError):
        load_yaml(tmp_path / "does-not-exist.yaml")


def test_load_yaml_empty_file(tmp_path):
    path = tmp_path / "empty.yaml"
    path.write_text("", encoding="utf-8")
    with pytest.raises(ConfigError):
        load_yaml(path)


def test_load_schema_requires_columns_key(tmp_path):
    path = tmp_path / "schema.yaml"
    path.write_text("foo: bar\n", encoding="utf-8")
    with pytest.raises(ConfigError):
        load_schema(path)


def test_load_schema_rejects_unknown_type(tmp_path):
    path = tmp_path / "schema.yaml"
    path.write_text("columns:\n  - name: x\n    type: bogus\n", encoding="utf-8")
    with pytest.raises(ConfigError):
        load_schema(path)
