from __future__ import annotations

from pathlib import Path

import frontmatter
import pytest
from typer.testing import CliRunner

from inkwell_cli_notes.cli import app
from inkwell_cli_notes.render import note_document
from inkwell_cli_notes.storage import NoteStore

runner = CliRunner()


def test_init_new_list_and_show_workflow(tmp_path: Path) -> None:
    home = tmp_path / "inkwell"

    init_result = runner.invoke(app, ["--home", str(home), "init"])
    assert init_result.exit_code == 0
    assert (home / "notes").exists()
    assert (home / "archive").exists()

    new_result = runner.invoke(
        app,
        [
            "--home",
            str(home),
            "new",
            "Morning Notes",
            "--body",
            "First line\n\nSecond line",
            "--tag",
            "daily",
            "--notebook",
            "journal",
            "--pin",
        ],
    )
    assert new_result.exit_code == 0
    assert "Morning Notes" in new_result.stdout

    store = NoteStore(home)
    created = store.get_note("morning-notes")

    list_result = runner.invoke(app, ["--home", str(home), "list", "--pinned"])
    assert list_result.exit_code == 0
    assert "journal" in list_result.stdout
    assert created.note_id in list_result.stdout

    show_result = runner.invoke(app, ["--home", str(home), "show", created.note_id])
    assert show_result.exit_code == 0
    assert "Morning Notes" in show_result.stdout
    assert "First line" in show_result.stdout

    raw_result = runner.invoke(app, ["--home", str(home), "show", created.note_id, "--raw"])
    assert raw_result.exit_code == 0
    assert "title: Morning Notes" in raw_result.stdout


def test_edit_archive_restore_and_delete_workflow(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    home = tmp_path / "inkwell"
    runner.invoke(app, ["--home", str(home), "init"])
    runner.invoke(app, ["--home", str(home), "new", "Workspace", "--body", "Draft"])
    store = NoteStore(home)
    note = store.get_note("workspace")

    updated_post = frontmatter.loads(note_document(note))
    updated_post.metadata["title"] = "Workspace Revised"
    updated_post.metadata["tags"] = ["ops", "docs"]
    updated_post.metadata["notebook"] = "team"
    updated_post.metadata["pinned"] = True
    updated_post.content = "Updated body"

    monkeypatch.setattr(
        "inkwell_cli_notes.cli.edit_text_in_editor",
        lambda text, editor_command: frontmatter.dumps(updated_post),
    )

    edit_result = runner.invoke(app, ["--home", str(home), "edit", note.note_id])
    assert edit_result.exit_code == 0
    assert "Updated note" in edit_result.stdout

    revised = store.get_note(note.note_id)
    assert revised.metadata.title == "Workspace Revised"
    assert revised.metadata.tags == ["ops", "docs"]
    assert revised.metadata.notebook == "team"
    assert revised.metadata.pinned is True
    assert revised.body == "Updated body"

    archive_result = runner.invoke(app, ["--home", str(home), "archive", revised.note_id])
    assert archive_result.exit_code == 0
    assert "Archived note" in archive_result.stdout
    archived = store.get_note(revised.note_id)
    assert archived.metadata.archived is True

    restore_result = runner.invoke(app, ["--home", str(home), "restore", revised.note_id])
    assert restore_result.exit_code == 0
    assert "Restored note" in restore_result.stdout
    restored = store.get_note(revised.note_id)
    assert restored.metadata.archived is False

    delete_result = runner.invoke(
        app,
        ["--home", str(home), "delete", restored.note_id, "--yes"],
    )
    assert delete_result.exit_code == 0
    assert "Deleted note" in delete_result.stdout
    assert store.list_notes() == []
