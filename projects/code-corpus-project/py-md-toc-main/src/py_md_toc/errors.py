"""Custom exceptions for py-md-toc."""

from __future__ import annotations


class PyMdTocError(Exception):
    """Base error raised by py-md-toc."""


class InvalidHeadingDepthError(PyMdTocError, ValueError):
    """Raised when a heading depth range is invalid."""


class TocMarkerError(PyMdTocError, ValueError):
    """Raised when a managed TOC marker block is invalid."""


class TocMarkerNotFoundError(TocMarkerError):
    """Raised when the TOC marker block is missing."""


class TocMarkerConflictError(TocMarkerError):
    """Raised when the TOC marker block is duplicated or out of order."""
