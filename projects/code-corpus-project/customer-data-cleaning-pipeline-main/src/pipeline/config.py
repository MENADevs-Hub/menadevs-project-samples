"""Configuration loading and validation for the pipeline.

Loads the YAML config files (schema, validation rules, pipeline options) and turns
the schema into typed objects the rest of the pipeline can rely on.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

_VALID_TYPES = {"string", "date", "int", "float"}


class ConfigError(ValueError):
    """Raised when configuration is missing or invalid."""


@dataclass(frozen=True)
class ColumnSpec:
    """A single column declaration from the schema."""

    name: str
    type: str = "string"
    required: bool = False


@dataclass(frozen=True)
class Schema:
    """The declared shape of the input CSV."""

    columns: list[ColumnSpec]

    @property
    def column_names(self) -> list[str]:
        return [c.name for c in self.columns]

    def required_columns(self) -> list[str]:
        return [c.name for c in self.columns if c.required]


def load_yaml(path: str | Path) -> dict[str, Any]:
    """Load a YAML file into a dictionary, raising ConfigError on problems."""
    path = Path(path)
    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if data is None:
        raise ConfigError(f"Config file is empty: {path}")
    if not isinstance(data, dict):
        raise ConfigError(f"Config file must be a mapping: {path}")
    return data


def load_schema(path: str | Path) -> Schema:
    """Load and validate the column schema."""
    data = load_yaml(path)
    if "columns" not in data:
        raise ConfigError("schema config must contain a 'columns' key")

    columns: list[ColumnSpec] = []
    for raw in data["columns"]:
        if not isinstance(raw, dict) or "name" not in raw:
            raise ConfigError("each column must be a mapping with a 'name'")
        col_type = raw.get("type", "string")
        if col_type not in _VALID_TYPES:
            raise ConfigError(
                f"unknown column type '{col_type}' for column '{raw['name']}'"
            )
        columns.append(
            ColumnSpec(
                name=raw["name"],
                type=col_type,
                required=bool(raw.get("required", False)),
            )
        )

    if not columns:
        raise ConfigError("schema must define at least one column")
    return Schema(columns=columns)
