"""Managed TOC block updates for py-md-toc."""

from __future__ import annotations

from .errors import TocMarkerConflictError, TocMarkerNotFoundError

__all__ = ["END_MARKER", "START_MARKER", "insert_toc"]

START_MARKER = "<!-- py-md-toc:start -->"
END_MARKER = "<!-- py-md-toc:end -->"


def insert_toc(
    markdown: str,
    toc: str,
    *,
    start_marker: str = START_MARKER,
    end_marker: str = END_MARKER,
) -> str:
    """Replace the managed TOC block in a Markdown document."""

    start_index, end_index = _locate_markers(markdown, start_marker, end_marker)
    newline = _detect_newline(markdown)
    # Preserve the original prefix and suffix so only the managed block changes.
    before = markdown[: start_index + len(start_marker)]
    after = markdown[end_index:]
    body = toc.replace("\r\n", "\n").replace("\r", "\n")
    if body:
        body = body.replace("\n", newline)
    replacement = f"{newline}{body}{newline}"
    return before + replacement + after


def _locate_markers(markdown: str, start_marker: str, end_marker: str) -> tuple[int, int]:
    """Find the unique managed TOC block and validate its ordering."""

    start_count = markdown.count(start_marker)
    end_count = markdown.count(end_marker)
    if start_count == 0 or end_count == 0:
        raise TocMarkerNotFoundError("Markdown must contain a managed TOC marker block")
    if start_count > 1 or end_count > 1:
        raise TocMarkerConflictError("Markdown must contain exactly one TOC marker block")

    start_index = markdown.index(start_marker)
    end_index = markdown.index(end_marker)
    if start_index > end_index:
        raise TocMarkerConflictError("TOC start marker must appear before the end marker")
    return start_index, end_index


def _detect_newline(markdown: str) -> str:
    """Mirror the input file's newline style when rewriting content."""

    if "\r\n" in markdown:
        return "\r\n"
    if "\r" in markdown:
        return "\r"
    return "\n"
