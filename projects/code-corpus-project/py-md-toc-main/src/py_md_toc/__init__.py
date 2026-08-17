"""py-md-toc package."""

from __future__ import annotations

from .parser import Heading, parse_headings
from .renderer import build_toc
from .updater import END_MARKER, START_MARKER, insert_toc

__all__ = [
    "END_MARKER",
    "Heading",
    "START_MARKER",
    "build_toc",
    "insert_toc",
    "parse_headings",
    "__version__",
]

__version__ = "0.1.0"
