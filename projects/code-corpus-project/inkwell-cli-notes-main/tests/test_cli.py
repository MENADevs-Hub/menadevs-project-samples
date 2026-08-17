from typer.testing import CliRunner

from inkwell_cli_notes.cli import app

runner = CliRunner()


def test_help_renders_cli_name() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "local-first cli" in result.stdout.lower()
    assert "status" in result.stdout.lower()


def test_version_flag_reports_distribution_version() -> None:
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert "0.1.0" in result.stdout
