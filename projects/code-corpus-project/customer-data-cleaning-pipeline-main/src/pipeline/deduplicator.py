"""Fuzzy deduplication with a blocking key and a configurable similarity threshold.

Rows are grouped into blocks (by default, the email domain) so only plausibly-related
rows are compared, which avoids an O(n^2) scan across the whole dataset. Within a block,
each row is compared against the rows already kept; if the similarity of the key fields
meets the threshold, the row is treated as a duplicate of the earlier one.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from pipeline.config import load_yaml


@dataclass(frozen=True)
class DeduplicationOptions:
    """Deduplication behavior, loaded from pipeline.yaml."""

    blocking_key: str = "email_domain"
    similarity_threshold: float = 0.9
    key_fields: tuple[str, ...] = ("email", "full_name")

    @classmethod
    def from_config(cls, data: dict[str, Any]) -> DeduplicationOptions:
        return cls(
            blocking_key=str(data.get("blocking_key", "email_domain")),
            similarity_threshold=float(data.get("similarity_threshold", 0.9)),
            key_fields=tuple(data.get("key_fields", ["email", "full_name"])),
        )


@dataclass
class DuplicateRow:
    """A row identified as a duplicate of an earlier (kept) row."""

    row: dict[str, str]
    duplicate_of_index: int
    score: float


@dataclass
class DeduplicationResult:
    """Unique rows kept, and the duplicates that were removed."""

    unique_rows: list[dict[str, str]] = field(default_factory=list)
    duplicates: list[DuplicateRow] = field(default_factory=list)


def load_deduplication_options(path: str | Path) -> DeduplicationOptions:
    """Load the deduplication options from pipeline.yaml."""
    data = load_yaml(path)
    return DeduplicationOptions.from_config(data.get("deduplication", {}) or {})


def _key_string(row: dict[str, str], key_fields: tuple[str, ...]) -> str:
    return " ".join((row.get(f) or "").strip().lower() for f in key_fields)


def _blocking_key(row: dict[str, str], options: DeduplicationOptions) -> str:
    if options.blocking_key == "email_domain":
        email = row.get("email") or ""
        return email.split("@")[-1].strip().lower() if "@" in email else ""
    if options.blocking_key == "first_letter_name":
        return (row.get("full_name") or "").strip().lower()[:1]
    # Unknown blocking key: treat everything as one block.
    return ""


def _similarity(left: str, right: str) -> float:
    return SequenceMatcher(None, left, right).ratio()


def deduplicate(
    rows: list[dict[str, str]], options: DeduplicationOptions
) -> DeduplicationResult:
    """Remove fuzzy-duplicate rows, keeping the first occurrence of each."""
    result = DeduplicationResult()
    # block -> list of (original_index, key_string) for kept unique rows
    kept_by_block: dict[str, list[tuple[int, str]]] = {}

    for index, row in enumerate(rows):
        block = _blocking_key(row, options)
        key = _key_string(row, options.key_fields)
        candidates = kept_by_block.setdefault(block, [])

        match: tuple[int, float] | None = None
        for kept_index, kept_key in candidates:
            score = _similarity(key, kept_key)
            if score >= options.similarity_threshold:
                match = (kept_index, score)
                break

        if match is not None:
            result.duplicates.append(
                DuplicateRow(row=row, duplicate_of_index=match[0], score=match[1])
            )
        else:
            result.unique_rows.append(row)
            candidates.append((index, key))

    return result
