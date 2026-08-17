"""Derived JSON index for note discovery and validation."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

from inkwell_cli_notes.models import Note


@dataclass(frozen=True, slots=True)
class NoteIndexEntry:
    """Serializable summary of a note."""

    note_id: str
    title: str
    slug: str
    tags: list[str]
    notebook: str
    created_at: str
    updated_at: str
    archived: bool
    pinned: bool
    path: str
    body: str

    @classmethod
    def from_note(cls, note: Note) -> NoteIndexEntry:
        """Create an index entry from a note model."""

        return cls(
            note_id=note.note_id,
            title=note.metadata.title,
            slug=note.slug,
            tags=list(note.metadata.tags),
            notebook=note.metadata.notebook,
            created_at=note.metadata.created_at.isoformat(),
            updated_at=note.metadata.updated_at.isoformat(),
            archived=note.metadata.archived,
            pinned=note.metadata.pinned,
            path=str(note.path),
            body=note.body,
        )


@dataclass(frozen=True, slots=True)
class NoteIndex:
    """A rebuildable snapshot of the note corpus."""

    generated_at: str
    entries: list[NoteIndexEntry]

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable dictionary."""

        return {
            "generated_at": self.generated_at,
            "entries": [asdict(entry) for entry in self.entries],
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> NoteIndex:
        """Rehydrate an index from JSON data."""

        raw_entries = payload.get("entries", [])
        if not isinstance(raw_entries, list):
            raise ValueError("index entries must be a list")
        entries: list[NoteIndexEntry] = []
        for entry in raw_entries:
            if not isinstance(entry, dict):
                raise ValueError("index entries must be JSON objects")
            entry_dict = cast(dict[str, object], entry)
            # Rehydration performs explicit field coercion instead of relying on
            # incidental JSON shapes so cache corruption fails loudly.
            entries.append(
                NoteIndexEntry(
                    note_id=str(entry_dict["note_id"]),
                    title=str(entry_dict["title"]),
                    slug=str(entry_dict["slug"]),
                    tags=[str(tag) for tag in cast(list[object], entry_dict["tags"])],
                    notebook=str(entry_dict["notebook"]),
                    created_at=str(entry_dict["created_at"]),
                    updated_at=str(entry_dict["updated_at"]),
                    archived=bool(entry_dict["archived"]),
                    pinned=bool(entry_dict["pinned"]),
                    path=str(entry_dict["path"]),
                    body=str(entry_dict["body"]),
                )
            )
        generated_at = str(payload.get("generated_at", ""))
        return cls(generated_at=generated_at, entries=entries)


def build_index(notes: Sequence[Note]) -> NoteIndex:
    """Build an index from the current note corpus."""

    # The generated timestamp is part of the artifact, not the individual
    # notes, so it is assigned once for the whole snapshot.
    return NoteIndex(
        generated_at=datetime.now(tz=UTC).isoformat(timespec="seconds"),
        entries=[NoteIndexEntry.from_note(note) for note in notes],
    )


def save_index(index: NoteIndex, path: Path) -> None:
    """Persist an index to disk as JSON."""

    path.parent.mkdir(parents=True, exist_ok=True)
    # Stable formatting keeps diffs readable when the index is inspected by
    # users or copied into debugging artifacts.
    path.write_text(json.dumps(index.to_dict(), indent=2, sort_keys=True), encoding="utf-8")


def load_index(path: Path) -> NoteIndex:
    """Load an index from disk."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("index file must contain a JSON object")
    return NoteIndex.from_dict(payload)
