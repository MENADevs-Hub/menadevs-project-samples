"""Markdown TOC rendering for py-md-toc."""

from __future__ import annotations

from collections.abc import Sequence

from .errors import InvalidHeadingDepthError
from .parser import Heading

__all__ = ["build_toc"]


def build_toc(
    headings: Sequence[Heading],
    *,
    bullet: str = "-",
    indent: int = 2,
) -> str:
    """Render a nested Markdown table of contents."""

    if not bullet or "\n" in bullet or "\r" in bullet:
        raise ValueError("bullet must be a non-empty single-line string")
    if indent < 0:
        raise InvalidHeadingDepthError("indent must be greater than or equal to zero")
    if not headings:
        return ""

    base_level = min(heading.level for heading in headings)
    lines: list[str] = []

    for heading in headings:
        depth = max(heading.level - base_level, 0)
        prefix = " " * (depth * indent)
        lines.append(f"{prefix}{bullet} [{heading.text}](#{heading.slug})")

    return "\n".join(lines)
