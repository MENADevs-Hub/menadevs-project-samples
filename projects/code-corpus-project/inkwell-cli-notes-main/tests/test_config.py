from pathlib import Path

import pytest

from inkwell_cli_notes.config import load_settings


def test_load_settings_uses_environment_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("INKWELL_HOME", "~/tmp/inkwell-home")
    monkeypatch.setenv("INKWELL_EDITOR", "vim")
    monkeypatch.setenv("INKWELL_INDEX_NAME", "notes-index.json")

    settings = load_settings()

    assert settings.home_dir == Path("~/tmp/inkwell-home").expanduser()
    assert settings.editor == "vim"
    assert settings.index_name == "notes-index.json"
