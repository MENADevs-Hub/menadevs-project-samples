"""Filesystem-backed storage for Markdown notes."""

from __future__ import annotations

import os
import tempfile
from collections.abc import Iterable
from dataclasses import replace
from pathlib import Path

import frontmatter

from inkwell_cli_notes.errors import AmbiguousNoteError, InvalidNoteError, NoteNotFoundError
from inkwell_cli_notes.models import Note, NoteMetadata

from .index import NoteIndex, build_index, load_index, save_index
from .search import search_notes as rank_notes


class NoteStore:
    """Persist and retrieve notes from a local directory tree."""

    def __init__(self, root_dir: Path, *, index_name: str = "index.json") -> None:
        self.root_dir = root_dir.expanduser()
        self.index_name = index_name

    @property
    def notes_dir(self) -> Path:
        return self.root_dir / "notes"

    @property
    def archive_dir(self) -> Path:
        return self.root_dir / "archive"

    @property
    def index_dir(self) -> Path:
        return self.root_dir / ".inkwell"

    @property
    def index_path(self) -> Path:
        return self.index_dir / self.index_name

    def ensure(self) -> None:
        """Create the storage directories if they do not exist."""

        # Creating all managed directories up front keeps later write paths
        # simple and makes one-time initialization idempotent.
        self.notes_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        self.index_dir.mkdir(parents=True, exist_ok=True)

    def create_note(
        self,
        title: str,
        *,
        body: str = "",
        tags: Iterable[str] = (),
        notebook: str = "default",
        pinned: bool = False,
    ) -> Note:
        """Create and persist a new note."""

        self.ensure()
        metadata = NoteMetadata.create(title, tags=tags, notebook=notebook, pinned=pinned)
        note = Note(metadata=metadata, body=body, path=self._note_path(metadata, archived=False))
        self._write_note(note)
        return note

    def list_notes(self, *, include_archived: bool = False) -> list[Note]:
        """Return notes sorted by recency."""

        notes = [*self._iter_notes(self.notes_dir)]
        if include_archived:
            notes.extend(self._iter_notes(self.archive_dir))
        return sorted(notes, key=lambda note: note.metadata.updated_at, reverse=True)

    def get_note(self, reference: str) -> Note:
        """Resolve a note by id or slug."""

        # We intentionally search across active and archived notes so commands
        # like restore and delete can target any stored note with one lookup.
        matches = [
            note
            for note in self.list_notes(include_archived=True)
            if self._matches(note, reference)
        ]
        # Exact id matches take precedence over slug matches because ids are
        # globally unique while slugs can collide after title normalization.
        id_matches = [note for note in matches if note.note_id == reference]
        if len(id_matches) == 1:
            return id_matches[0]
        if len(id_matches) > 1:
            raise AmbiguousNoteError(f"note id {reference!r} matches more than one note")
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise AmbiguousNoteError(f"note slug {reference!r} matches more than one note")
        raise NoteNotFoundError(f"note {reference!r} not found")

    def update_note(
        self,
        reference: str,
        *,
        title: str | None = None,
        body: str | None = None,
        tags: Iterable[str] | None = None,
        notebook: str | None = None,
        pinned: bool | None = None,
        archived: bool | None = None,
    ) -> Note:
        """Update an existing note and persist the result."""

        existing = self.get_note(reference)
        # Metadata owns derived fields like slug and updated_at so the model
        # remains the single place that enforces those invariants.
        metadata = existing.metadata.with_changes(
            title=title,
            tags=tags,
            notebook=notebook,
            pinned=pinned,
            archived=archived,
        )
        updated = Note(
            metadata=metadata,
            body=existing.body if body is None else body,
            path=self._note_path(metadata, archived=metadata.archived),
        )
        # A title or archive-state change can move the file, so writes go
        # through one path that can both replace content and relocate safely.
        self._write_note(updated, previous_path=existing.path)
        return updated

    def archive_note(self, reference: str) -> Note:
        """Move a note into the archive directory."""

        existing = self.get_note(reference)
        if existing.metadata.archived:
            return existing
        metadata = existing.metadata.with_changes(archived=True)
        archived_path = self._note_path(metadata, archived=True)
        archived = replace(existing, metadata=metadata, path=archived_path)
        self._write_note(archived, previous_path=existing.path)
        return archived

    def restore_note(self, reference: str) -> Note:
        """Move an archived note back into the active notes directory."""

        existing = self.get_note(reference)
        if not existing.metadata.archived:
            return existing
        metadata = existing.metadata.with_changes(archived=False)
        restored_path = self._note_path(metadata, archived=False)
        restored = replace(existing, metadata=metadata, path=restored_path)
        self._write_note(restored, previous_path=existing.path)
        return restored

    def delete_note(self, reference: str) -> None:
        """Delete a note from disk."""

        note = self.get_note(reference)
        note.path.unlink(missing_ok=False)

    def rebuild_index(self) -> NoteIndex:
        """Rebuild the derived JSON index from the current notes."""

        # The index is derived state, so rebuilding always starts from the
        # filesystem rather than trying to patch an existing cache in place.
        notes = self.list_notes(include_archived=True)
        index = build_index(notes)
        save_index(index, self.index_path)
        return index

    def load_index(self) -> NoteIndex | None:
        """Load the cached note index if it exists."""

        if not self.index_path.exists():
            return None
        return load_index(self.index_path)

    def search_notes(
        self,
        query: str,
        *,
        tag: str | None = None,
        notebook: str | None = None,
        pinned: bool = False,
        archived: bool = False,
        all_notes: bool = False,
        limit: int | None = None,
    ) -> list[tuple[Note, float]]:
        """Search the note corpus with ranking and optional filters."""

        # Search reuses the same filter vocabulary as list/export so users do
        # not have to learn slightly different meanings per command.
        notes = self.list_notes(include_archived=all_notes or archived)
        filtered = [
            note
            for note in notes
            if self._note_matches_filters(
                note,
                tag=tag,
                notebook=notebook,
                pinned=pinned,
                archived=archived,
                all_notes=all_notes,
            )
        ]
        return rank_notes(filtered, query, limit=limit)

    def _iter_notes(self, directory: Path) -> list[Note]:
        if not directory.exists():
            return []
        notes: list[Note] = []
        # Sorted iteration keeps list/search/index output stable across runs,
        # which makes tests and exports easier to reason about.
        for path in sorted(directory.glob("*.md")):
            notes.append(self._read_note_file(path))
        return notes

    def _matches(self, note: Note, reference: str) -> bool:
        return note.note_id == reference or note.slug == reference

    def _read_note_file(self, path: Path) -> Note:
        try:
            post = frontmatter.load(path)
            metadata = NoteMetadata.model_validate(post.metadata)
        except Exception as exc:  # pragma: no cover - frontmatter can raise many types
            # Parsing funnels disparate parser and validation failures into one
            # domain-level error so CLI callers can handle them consistently.
            raise InvalidNoteError(f"could not parse note file {path}") from exc
        return Note(metadata=metadata, body=post.content, path=path)

    def read_note_file(self, path: Path) -> Note:
        """Read a note file from disk."""

        return self._read_note_file(path)

    def _note_path(self, metadata: NoteMetadata, *, archived: bool) -> Path:
        base_dir = self.archive_dir if archived else self.notes_dir
        # Filenames keep both slug and id: the slug stays readable, while the
        # id protects uniqueness when titles normalize to the same slug.
        return base_dir / f"{metadata.slug}--{metadata.note_id}.md"

    def _write_note(self, note: Note, *, previous_path: Path | None = None) -> None:
        self.ensure()
        path = note.path
        payload = frontmatter.Post(
            note.body,
            **note.metadata.model_dump(by_alias=True, mode="json"),
        )
        rendered = frontmatter.dumps(payload)
        path.parent.mkdir(parents=True, exist_ok=True)
        # Writes go through a temp file in the target directory so replace is
        # atomic on the same filesystem and partial saves are avoided.
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            delete=False,
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
        ) as handle:
            handle.write(rendered)
            temp_path = Path(handle.name)
        os.replace(temp_path, path)
        if previous_path is not None and previous_path != path:
            # When the note moved because of a rename or archive transition,
            # we remove the old file only after the new file is safely in place.
            previous_path.unlink(missing_ok=True)

    def _note_matches_filters(
        self,
        note: Note,
        *,
        tag: str | None,
        notebook: str | None,
        pinned: bool,
        archived: bool,
        all_notes: bool,
    ) -> bool:
        # Centralizing these checks keeps list, search, and export behavior
        # aligned even as the option set grows over time.
        if not all_notes and note.metadata.archived is not archived:
            return False
        if archived and not note.metadata.archived:
            return False
        if tag is not None and tag not in note.metadata.tags:
            return False
        if notebook is not None and note.metadata.notebook != notebook:
            return False
        if pinned and not note.metadata.pinned:
            return False
        return True
