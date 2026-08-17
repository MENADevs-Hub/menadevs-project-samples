"""CLI workflow tests for py-md-toc."""

from typer.testing import CliRunner

from py_md_toc import __version__
from py_md_toc.cli import app

runner = CliRunner()


def test_package_exposes_version() -> None:
    assert __version__ == "0.1.0"


def test_cli_help() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "Generate a table of contents from Markdown headings." in result.stdout


def test_cli_version() -> None:
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert result.stdout.strip() == "py-md-toc 0.1.0"


def test_cli_prints_toc_to_stdout(tmp_path) -> None:
    """The default command should emit the TOC on stdout only."""

    markdown_file = tmp_path / "sample.md"
    markdown_file.write_text("# Intro\n\n## Details\n", encoding="utf-8")

    result = runner.invoke(app, [str(markdown_file)])

    assert result.exit_code == 0
    assert result.stdout == "- [Intro](#intro)\n  - [Details](#details)\n"


def test_cli_stays_quiet_for_documents_without_headings(tmp_path) -> None:
    """Documents with no headings should not produce noisy blank output."""

    markdown_file = tmp_path / "sample.md"
    markdown_file.write_text("Plain paragraph only.\n", encoding="utf-8")

    result = runner.invoke(app, [str(markdown_file)])

    assert result.exit_code == 0
    assert result.stdout == ""


def test_cli_writes_output_file(tmp_path) -> None:
    """`--output` should write the generated TOC without touching the input."""

    markdown_file = tmp_path / "sample.md"
    output_file = tmp_path / "toc.md"
    markdown_file.write_text("# Intro\n\n## Details\n", encoding="utf-8")

    result = runner.invoke(app, [str(markdown_file), "--output", str(output_file)])

    assert result.exit_code == 0
    assert result.stdout == ""
    assert output_file.read_text(encoding="utf-8") == (
        "- [Intro](#intro)\n  - [Details](#details)"
    )


def test_cli_rejects_combining_write_modes(tmp_path) -> None:
    """The write modes stay exclusive so scripts cannot accidentally double-write."""

    markdown_file = tmp_path / "sample.md"
    markdown_file.write_text("# Intro\n", encoding="utf-8")

    result = runner.invoke(
        app,
        [str(markdown_file), "--output", str(tmp_path / "toc.md"), "--in-place"],
    )

    assert result.exit_code == 1
    assert "Use only one of --output, --in-place, or --check." in result.stderr


def test_cli_updates_marker_block_in_place(tmp_path) -> None:
    """`--in-place` should replace only the managed marker block."""

    markdown_file = tmp_path / "sample.md"
    markdown_file.write_text(
        """# Intro

<!-- py-md-toc:start -->
placeholder
<!-- py-md-toc:end -->
""",
        encoding="utf-8",
    )

    result = runner.invoke(app, [str(markdown_file), "--in-place"])

    assert result.exit_code == 0
    assert markdown_file.read_text(encoding="utf-8") == (
        """# Intro

<!-- py-md-toc:start -->
- [Intro](#intro)
<!-- py-md-toc:end -->
"""
    )


def test_cli_check_validates_existing_marker_block(tmp_path) -> None:
    """`--check` should succeed when the managed block already matches."""

    markdown_file = tmp_path / "sample.md"
    markdown_file.write_text(
        """# Intro

<!-- py-md-toc:start -->
- [Intro](#intro)
<!-- py-md-toc:end -->
""",
        encoding="utf-8",
    )

    result = runner.invoke(app, [str(markdown_file), "--check"])

    assert result.exit_code == 0


def test_cli_check_fails_for_outdated_marker_block(tmp_path) -> None:
    """`--check` should fail when the managed block is stale."""

    markdown_file = tmp_path / "sample.md"
    markdown_file.write_text(
        """# Intro

<!-- py-md-toc:start -->
outdated
<!-- py-md-toc:end -->
""",
        encoding="utf-8",
    )

    result = runner.invoke(app, [str(markdown_file), "--check"])

    assert result.exit_code == 1


def test_cli_reports_missing_input_file(tmp_path) -> None:
    """A missing source file should fail with a clear error message."""

    missing = tmp_path / "missing.md"

    result = runner.invoke(app, [str(missing)])

    assert result.exit_code == 1
    assert f"Input file not found: {missing}" in result.stderr


def test_cli_rejects_invalid_depth_range(tmp_path) -> None:
    """The parser should reject depth ranges that cannot produce output."""

    markdown_file = tmp_path / "sample.md"
    markdown_file.write_text("# Intro\n", encoding="utf-8")

    result = runner.invoke(app, [str(markdown_file), "--min-level", "4", "--max-level", "3"])

    assert result.exit_code == 1
    assert "min_level cannot be greater than max_level" in result.stderr
