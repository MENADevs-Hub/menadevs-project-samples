"""Command-line interface for py-md-toc."""

from __future__ import annotations

from pathlib import Path
from typing import NoReturn

import typer

from . import __version__
from .errors import PyMdTocError
from .parser import parse_headings
from .renderer import build_toc
from .updater import insert_toc

app = typer.Typer(
    add_completion=False,
    help="Generate a table of contents from Markdown headings.",
)

FILE_ARGUMENT = typer.Argument(None, metavar="FILE", help="Markdown file to read.")
VERSION_OPTION = typer.Option(
    False,
    "--version",
    help="Show the installed version and exit.",
)
MIN_LEVEL_OPTION = typer.Option(
    1,
    "--min-level",
    min=1,
    max=6,
    help="Lowest heading level to include.",
)
MAX_LEVEL_OPTION = typer.Option(
    6,
    "--max-level",
    min=1,
    max=6,
    help="Highest heading level to include.",
)
OUTPUT_OPTION = typer.Option(
    None,
    "--output",
    help="Write the generated TOC to a file.",
)
IN_PLACE_OPTION = typer.Option(
    False,
    "--in-place",
    help="Update the managed TOC block inside the source file.",
)
CHECK_OPTION = typer.Option(
    False,
    "--check",
    help="Validate the managed TOC block without writing changes.",
)


@app.command(help="Generate a table of contents from Markdown headings.")
def main(
    ctx: typer.Context,
    version: bool = VERSION_OPTION,
    markdown_file: Path | None = FILE_ARGUMENT,
    min_level: int = MIN_LEVEL_OPTION,
    max_level: int = MAX_LEVEL_OPTION,
    output: Path | None = OUTPUT_OPTION,
    in_place: bool = IN_PLACE_OPTION,
    check: bool = CHECK_OPTION,
) -> None:
    """Run the root command."""

    if version:
        typer.echo(f"py-md-toc {__version__}")
        raise typer.Exit()

    if markdown_file is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()

    # The write modes are intentionally exclusive so the command stays predictable.
    if sum(bool(flag) for flag in (output, in_place, check)) > 1:
        _fail("Use only one of --output, --in-place, or --check.")

    markdown = _read_text(markdown_file)
    try:
        toc = build_toc(parse_headings(markdown, min_level=min_level, max_level=max_level))
    except (PyMdTocError, OSError, ValueError) as exc:
        _fail(str(exc))

    if check:
        _check_in_place_block(markdown, toc)
        raise typer.Exit(code=0)

    if in_place:
        # In-place writes are constrained to the managed marker block only.
        try:
            updated = insert_toc(markdown, toc)
            _write_text(markdown_file, updated)
        except (OSError, PyMdTocError, ValueError) as exc:
            _fail(str(exc))
        raise typer.Exit()

    if output is not None:
        # `--output` is a pure file write, so the source document remains untouched.
        try:
            _write_text(output, toc)
        except OSError as exc:
            _fail(str(exc))
        raise typer.Exit()

    # Silence empty documents so the command composes cleanly in shell pipelines.
    if toc:
        typer.echo(toc)


def _read_text(path: Path) -> str:
    """Read the input Markdown file as UTF-8 text."""

    try:
        with path.open("r", encoding="utf-8", newline="") as stream:
            return stream.read()
    except FileNotFoundError:
        _fail(f"Input file not found: {path}")


def _write_text(path: Path, text: str) -> None:
    """Write UTF-8 text with the platform newline style preserved by Python."""

    with path.open("w", encoding="utf-8", newline="") as stream:
        stream.write(text)


def _check_in_place_block(markdown: str, toc: str) -> None:
    """Recompute the managed block and compare it against the current file."""

    try:
        current = insert_toc(markdown, toc)
    except PyMdTocError as exc:
        _fail(str(exc))
    if _normalize_newlines(current) != _normalize_newlines(markdown):
        raise typer.Exit(code=1)


def _normalize_newlines(text: str) -> str:
    """Treat different newline styles as equivalent during comparisons."""

    return text.replace("\r\n", "\n").replace("\r", "\n")


def _fail(message: str) -> NoReturn:
    typer.echo(message, err=True)
    raise typer.Exit(code=1)
