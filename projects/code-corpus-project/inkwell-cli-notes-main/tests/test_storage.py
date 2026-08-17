from datetime import UTC, datetime
from pathlib import Path

import pytest

from inkwell_cli_notes.errors import AmbiguousNoteError, InvalidNoteError, NoteNotFoundError
from inkwell_cli_notes.storage import NoteStore


def test_create_read_update_archive_restore_and_delete_note(tmp_path: Path) -> None:
    store = NoteStore(tmp_path / "inkwell")

    created = store.create_note(
        "Project Launch",
        body="First draft",
        tags=["work", "launch"],
        notebook="team",
        pinned=True,
    )

    assert created.path.exists()
    assert store.get_note(created.note_id) == created
    assert store.get_note(created.slug) == created

    updated = store.update_note(
        created.note_id,
        title="Project Launch Notes",
        body="Updated draft",
        tags=["work", "launch", "launch"],
    )

    assert updated.note_id == created.note_id
    assert updated.slug == "project-launch-notes"
    assert updated.body == "Updated draft"
    assert updated.path.exists()
    assert not created.path.exists()

    archived = store.archive_note(updated.note_id)
    assert archived.metadata.archived is True
    assert archived.path.parent == store.archive_dir
    assert not updated.path.exists()

    restored = store.restore_note(archived.note_id)
    assert restored.metadata.archived is False
    assert restored.path.parent == store.notes_dir
    assert restored.path.exists()
    assert not archived.path.exists()

    store.delete_note(restored.note_id)
    with pytest.raises(NoteNotFoundError):
        store.get_note(restored.note_id)


def test_slug_lookup_becomes_ambiguous_when_two_notes_share_a_slug(
    tmp_path: Path,
) -> None:
    store = NoteStore(tmp_path / "inkwell")

    first = store.create_note("Shared Title", body="first")
    second = store.create_note("Shared Title", body="second")
    store.archive_note(second.note_id)

    with pytest.raises(AmbiguousNoteError):
        store.get_note(first.slug)


def test_list_notes_raises_for_invalid_front_matter(tmp_path: Path) -> None:
    store = NoteStore(tmp_path / "inkwell")
    store.ensure()
    bad_note = store.notes_dir / "broken--note.md"
    bad_note.write_text(
        "\n".join(
            [
                "---",
                'id: "20260625-broken"',
                'title: "Broken Note"',
                'slug: "wrong-slug"',
                "tags: []",
                'notebook: "default"',
                f'created_at: "{datetime.now(tz=UTC).isoformat()}"',
                f'updated_at: "{datetime.now(tz=UTC).isoformat()}"',
                "archived: false",
                "pinned: false",
                "---",
                "",
                "body",
                "",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(InvalidNoteError):
        store.list_notes()
