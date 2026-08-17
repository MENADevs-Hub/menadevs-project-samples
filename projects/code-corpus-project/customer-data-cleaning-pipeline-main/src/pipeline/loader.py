"""Schema-aware CSV loader.

Reads a raw customer CSV into a list of row dictionaries, checks the header against
the declared schema, and trims surrounding whitespace from every value.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path

from pipeline.config import Schema


class LoaderError(ValueError):
    """Raised when a CSV cannot be loaded."""


@dataclass
class LoadResult:
    """The outcome of loading a CSV against a schema."""

    rows: list[dict[str, str]]
    missing_columns: list[str] = field(default_factory=list)
    extra_columns: list[str] = field(default_factory=list)


def load_csv(path: str | Path, schema: Schema) -> LoadResult:
    """Load ``path`` as a CSV and validate its header against ``schema``.

    Raises LoaderError if the file is missing, has no header, or is missing a
    required column. Non-required missing columns and unexpected extra columns are
    recorded on the result rather than raised.
    """
    path = Path(path)
    if not path.exists():
        raise LoaderError(f"Input file not found: {path}")

    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise LoaderError(f"Input file has no header: {path}")
        header = list(reader.fieldnames)
        raw_rows = [dict(row) for row in reader]

    expected = schema.column_names
    missing = [c for c in expected if c not in header]
    extra = [c for c in header if c not in expected]

    missing_required = [c for c in schema.required_columns() if c not in header]
    if missing_required:
        raise LoaderError(
            f"Missing required column(s): {', '.join(missing_required)}"
        )

    rows = [
        {key: (value.strip() if isinstance(value, str) else value) for key, value in row.items()}
        for row in raw_rows
    ]
    return LoadResult(rows=rows, missing_columns=missing, extra_columns=extra)
