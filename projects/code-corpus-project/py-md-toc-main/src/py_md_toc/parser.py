"""Markdown heading parsing for py-md-toc."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from .errors import InvalidHeadingDepthError

__all__ = ["Heading", "parse_headings"]

_ATX_HEADING_RE = re.compile(r"^[ \t]{0,3}(#{1,6})[ \t]+(.+?)\s*#*\s*$")
_SETEXT_UNDERLINE_RE = re.compile(r"^[ \t]{0,3}(=+|-+)[ \t]*$")
_FENCE_OPEN_RE = re.compile(r"^[ \t]{0,3}(?P<fence>`{3,}|~{3,})(?P<info>.*)$")
_INDENTED_CODE_RE = re.compile(r"^(?: {4,}|\t)")
_LINK_RE = re.compile(r"!\[([^\]]*)\]\([^)]+\)|\[([^\]]+)\]\([^)]+\)")
_CODE_SPAN_RE = re.compile(r"`([^`]+)`")
_TAG_RE = re.compile(r"<[^>]+>")
_INLINE_MARKERS_RE = re.compile(r"[*_~]")


@dataclass(frozen=True, slots=True)
class Heading:
    """A parsed Markdown heading."""

    level: int
    text: str
    slug: str
    line: int


def parse_headings(
    markdown: str,
    *,
    min_level: int = 1,
    max_level: int = 6,
) -> list[Heading]:
    """Parse Markdown headings from a document."""

    _validate_heading_levels(min_level, max_level)

    headings: list[Heading] = []
    seen_slugs: dict[str, int] = {}
    pending_heading: tuple[int, str] | None = None
    fenced_marker: tuple[str, int] | None = None

    for line_number, raw_line in enumerate(markdown.splitlines(), start=1):
        line = raw_line.rstrip("\r")

        # Once a fenced block opens, the parser stays inside it until a matching closer.
        if fenced_marker is not None:
            if _is_fence_closer(line, fenced_marker[0], fenced_marker[1]):
                fenced_marker = None
            continue

        fence_open = _FENCE_OPEN_RE.match(line)
        if fence_open is not None:
            fenced_marker = (fence_open.group("fence")[0], len(fence_open.group("fence")))
            pending_heading = None
            continue

        # Indented code blocks are ignored as raw Markdown content, not headings.
        if _INDENTED_CODE_RE.match(line):
            pending_heading = None
            continue

        stripped = line.strip()
        if not stripped:
            pending_heading = None
            continue

        setext_match = _SETEXT_UNDERLINE_RE.match(line)
        if setext_match is not None:
            # A Setext underline turns the immediately previous text line into a heading.
            if pending_heading is not None:
                level = 1 if setext_match.group(1)[0] == "=" else 2
                if min_level <= level <= max_level:
                    heading_line, heading_text = pending_heading
                    normalized = _normalize_heading_text(heading_text)
                    slug = _unique_slug(_slugify(normalized), seen_slugs)
                    headings.append(
                        Heading(level=level, text=normalized, slug=slug, line=heading_line)
                    )
            pending_heading = None
            continue

        atx_match = _ATX_HEADING_RE.match(line)
        if atx_match is not None:
            # ATX headings are simpler: the level is encoded directly in the prefix.
            level = len(atx_match.group(1))
            if min_level <= level <= max_level:
                normalized = _normalize_heading_text(atx_match.group(2))
                slug = _unique_slug(_slugify(normalized), seen_slugs)
                headings.append(Heading(level=level, text=normalized, slug=slug, line=line_number))
            pending_heading = None
            continue

        pending_heading = (line_number, stripped)

    return headings


def _validate_heading_levels(min_level: int, max_level: int) -> None:
    """Reject ranges that cannot produce a valid heading selection."""

    if not 1 <= min_level <= 6:
        raise InvalidHeadingDepthError("min_level must be between 1 and 6")
    if not 1 <= max_level <= 6:
        raise InvalidHeadingDepthError("max_level must be between 1 and 6")
    if min_level > max_level:
        raise InvalidHeadingDepthError("min_level cannot be greater than max_level")


def _is_fence_closer(line: str, marker: str, length: int) -> bool:
    """Detect a fence closer that matches the opener's marker and length."""

    candidate = line.lstrip(" ")
    return candidate.startswith(marker * length) and set(candidate.rstrip()) <= {marker}


def _normalize_heading_text(text: str) -> str:
    """Strip inline Markdown syntax that should not appear in TOC labels."""

    normalized = text.strip()
    normalized = _LINK_RE.sub(lambda match: match.group(1) or match.group(2) or "", normalized)
    normalized = _CODE_SPAN_RE.sub(lambda match: match.group(1), normalized)
    normalized = _TAG_RE.sub("", normalized)
    normalized = _INLINE_MARKERS_RE.sub("", normalized)
    normalized = unicodedata.normalize("NFKC", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


def _slugify(text: str) -> str:
    """Convert heading text into a GitHub-style slug."""

    slug_parts: list[str] = []
    needs_dash = False
    for character in text.casefold():
        if character.isalnum():
            slug_parts.append(character)
            needs_dash = False
        elif slug_parts:
            needs_dash = True
        if needs_dash and (not slug_parts or slug_parts[-1] != "-"):
            slug_parts.append("-")
            needs_dash = False
    slug = "".join(slug_parts).strip("-")
    return slug or "section"


def _unique_slug(base_slug: str, seen_slugs: dict[str, int]) -> str:
    """Append a numeric suffix when the same slug appears more than once."""

    count = seen_slugs.get(base_slug, 0)
    seen_slugs[base_slug] = count + 1
    if count == 0:
        return base_slug
    return f"{base_slug}-{count}"
