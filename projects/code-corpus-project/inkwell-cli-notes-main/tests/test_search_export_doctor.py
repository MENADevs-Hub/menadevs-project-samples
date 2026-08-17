from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from inkwell_cli_notes.cli import app
from inkwell_cli_notes.doctor import run_doctor
from inkwell_cli_notes.export import export_notes
from inkwell_cli_notes.search import search_notes
from inkwell_cli_notes.storage import NoteStore

runner = CliRunner()


def test_search_ranks_title_matches_above_body_matches(tmp_path: Path) -> None:
    store = NoteStore(tmp_path / "inkwell")
    top = store.create_note("Alpha Project", body="noisy content")
    store.create_note("Beta Plan", body="alpha appears here", tags=["beta"])

    results = search_notes(store.list_notes(), "alpha")

    assert results[0][0].note_id == top.note_id
    assert results[0][1] > results[1][1]


def test_search_and_export_respect_filters(tmp_path: Path) -> None:
    store = NoteStore(tmp_path / "inkwell")
    active = store.create_note("Alpha Project", body="alpha", tags=["alpha"])
    archived = store.create_note("Beta Plan", body="beta", tags=["beta"])
    store.archive_note(archived.note_id)

    results = store.search_notes("alpha", tag="alpha", pinned=False, all_notes=False)
    assert results
    assert results[0][0].note_id == active.note_id

    export_path = tmp_path / "filtered.json"
    export_notes([active], export_path, fmt="json")
    payload = json.loads(export_path.read_text(encoding="utf-8"))
    assert len(payload["notes"]) == 1
    assert payload["notes"][0]["metadata"]["title"] == "Alpha Project"


def test_rebuild_index_and_doctor_validate_storage(tmp_path: Path) -> None:
    store = NoteStore(tmp_path / "inkwell")
    store.create_note("Alpha Project", body="notes")
    store.create_note("Beta Plan", body="notes")

    index = store.rebuild_index()
    cached = store.load_index()

    assert len(index.entries) == 2
    assert cached is not None
    assert len(cached.entries) == 2

    report = run_doctor(store)
    assert report.ok is True
    assert report.note_count == 2


def test_doctor_reports_invalid_note_file(tmp_path: Path) -> None:
    store = NoteStore(tmp_path / "inkwell")
    store.ensure()
    bad_note = store.notes_dir / "broken.md"
    bad_note.write_text("not front matter", encoding="utf-8")

    report = run_doctor(store)

    assert report.ok is False
    assert report.issues
    assert any("broken.md" in issue for issue in report.issues)


def test_doctor_rebuild_skips_invalid_notes(tmp_path: Path) -> None:
    store = NoteStore(tmp_path / "inkwell")
    store.ensure()
    (store.notes_dir / "broken.md").write_text("not front matter", encoding="utf-8")

    report = run_doctor(store, rebuild_index=True)

    assert report.ok is False
    assert report.index_rebuilt is False
    assert any("broken.md" in issue for issue in report.issues)


def test_export_writes_markdown_and_json_backups(tmp_path: Path) -> None:
    store = NoteStore(tmp_path / "inkwell")
    first = store.create_note("Alpha Project", body="first", tags=["alpha"])
    second = store.create_note("Beta Plan", body="second", tags=["beta"])

    markdown_dir = tmp_path / "markdown-export"
    json_file = tmp_path / "backup.json"

    exported_dir = export_notes([first], markdown_dir, fmt="markdown")
    exported_json = export_notes([first, second], json_file, fmt="json")

    assert exported_dir == markdown_dir
    assert (markdown_dir / first.path.name).exists()
    assert exported_json == json_file

    payload = json.loads(json_file.read_text(encoding="utf-8"))
    assert payload["generated_at"]
    assert len(payload["notes"]) == 2
    assert payload["notes"][0]["metadata"]["title"] == "Alpha Project"


def test_cli_search_export_and_doctor_commands(tmp_path: Path) -> None:
    home = tmp_path / "inkwell"
    runner.invoke(app, ["--home", str(home), "init"])
    runner.invoke(
        app,
        [
            "--home",
            str(home),
            "new",
            "Alpha Project",
            "--body",
            "alpha body",
            "--tag",
            "alpha",
        ],
    )
    runner.invoke(
        app,
        ["--home", str(home), "new", "Beta Plan", "--body", "beta body", "--tag", "beta"],
    )

    search_result = runner.invoke(app, ["--home", str(home), "search", "alpha"])
    assert search_result.exit_code == 0
    assert "Alpha Project" in search_result.stdout

    markdown_dir = tmp_path / "export-md"
    export_result = runner.invoke(
        app,
        ["--home", str(home), "export", "--format", "markdown", "--output", str(markdown_dir)],
    )
    assert export_result.exit_code == 0
    assert any(markdown_dir.glob("*.md"))

    filtered_dir = tmp_path / "export-alpha"
    filtered_result = runner.invoke(
        app,
        [
            "--home",
            str(home),
            "export",
            "--format",
            "json",
            "--output",
            str(filtered_dir / "alpha.json"),
            "--tag",
            "alpha",
        ],
    )
    assert filtered_result.exit_code == 0
    payload = json.loads((filtered_dir / "alpha.json").read_text(encoding="utf-8"))
    assert len(payload["notes"]) == 1

    doctor_result = runner.invoke(app, ["--home", str(home), "doctor", "--rebuild-index"])
    assert doctor_result.exit_code == 0
    assert "Rebuilt index" in doctor_result.stdout


def test_delete_confirmation_can_abort(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    home = tmp_path / "inkwell"
    runner.invoke(app, ["--home", str(home), "init"])
    runner.invoke(app, ["--home", str(home), "new", "Alpha Project", "--body", "alpha body"])

    monkeypatch.setattr("typer.confirm", lambda *args, **kwargs: False)

    delete_result = runner.invoke(app, ["--home", str(home), "delete", "alpha-project"])
    assert delete_result.exit_code != 0


def test_help_mentions_final_phase_commands() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "search" in result.stdout
    assert "export" in result.stdout
    assert "doctor" in result.stdout
