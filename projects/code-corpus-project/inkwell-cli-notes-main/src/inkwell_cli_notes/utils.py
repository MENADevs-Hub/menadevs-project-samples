"""Low-level helpers shared by note storage and future workflows."""

from __future__ import annotations

import re
import secrets
import unicodedata
from collections.abc import Iterable
from datetime import UTC, datetime


def slugify(value: str) -> str:
    """Convert arbitrary text into a stable filesystem-safe slug."""

    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_text.lower()).strip("-")
    return slug or "note"


def unique_items(values: Iterable[str]) -> list[str]:
    """Deduplicate strings while preserving order."""

    seen: set[str] = set()
    items: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        items.append(value)
    return items


def utc_now() -> datetime:
    """Return the current time in UTC."""

    return datetime.now(tz=UTC)


def generate_note_id() -> str:
    """Generate a readable, collision-resistant note identifier."""

    return f"{utc_now():%Y%m%d%H%M%S}-{secrets.token_hex(3)}"
