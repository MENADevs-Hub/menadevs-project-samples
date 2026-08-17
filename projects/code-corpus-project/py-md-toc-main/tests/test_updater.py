"""Updater tests for managed TOC marker replacement."""

from py_md_toc.errors import TocMarkerConflictError, TocMarkerNotFoundError
from py_md_toc.updater import END_MARKER, START_MARKER, insert_toc


def test_insert_toc_replaces_existing_marker_block() -> None:
    """The updater should rewrite only the body between the managed markers."""

    markdown = (
        "# Intro\n\n"
        f"{START_MARKER}\n"
        "outdated\n"
        f"{END_MARKER}\n"
    )

    updated = insert_toc(markdown, "- [Intro](#intro)")

    assert updated == (
        "# Intro\n\n"
        f"{START_MARKER}\n"
        "- [Intro](#intro)\n"
        f"{END_MARKER}\n"
    )


def test_insert_toc_preserves_crlf_newlines() -> None:
    """Line-ending style should survive a TOC rewrite unchanged."""

    markdown = (
        "# Intro\r\n\r\n"
        f"{START_MARKER}\r\n"
        "old\r\n"
        f"{END_MARKER}\r\n"
    )

    updated = insert_toc(markdown, "- [Intro](#intro)")

    assert "\r\n" in updated
    assert updated == (
        "# Intro\r\n\r\n"
        f"{START_MARKER}\r\n"
        "- [Intro](#intro)\r\n"
        f"{END_MARKER}\r\n"
    )


def test_insert_toc_requires_marker_block() -> None:
    """Missing markers should fail fast so the caller can surface a clear error."""

    markdown = "# Intro\n"

    try:
        insert_toc(markdown, "- [Intro](#intro)")
    except TocMarkerNotFoundError as exc:
        assert str(exc) == "Markdown must contain a managed TOC marker block"
    else:  # pragma: no cover - defensive branch
        raise AssertionError("Expected TocMarkerNotFoundError")


def test_insert_toc_rejects_duplicate_marker_blocks() -> None:
    """Duplicate marker pairs should be treated as a conflict, not a guess."""

    markdown = (
        f"{START_MARKER}\n"
        "old\n"
        f"{END_MARKER}\n"
        f"{START_MARKER}\n"
        "duplicate\n"
        f"{END_MARKER}\n"
    )

    try:
        insert_toc(markdown, "- [Intro](#intro)")
    except TocMarkerConflictError as exc:
        assert str(exc) == "Markdown must contain exactly one TOC marker block"
    else:  # pragma: no cover - defensive branch
        raise AssertionError("Expected TocMarkerConflictError")
