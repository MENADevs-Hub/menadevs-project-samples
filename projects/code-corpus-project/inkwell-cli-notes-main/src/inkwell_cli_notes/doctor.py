"""Validation helpers for note storage and derived caches."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from inkwell_cli_notes.errors import InvalidNoteError
from inkwell_cli_notes.storage import NoteStore


@dataclass(frozen=True, slots=True)
class DoctorReport:
    """Summary of storage validation results."""

    ok: bool
    issues: list[str]
    note_count: int
    index_rebuilt: bool


def run_doctor(store: NoteStore, *, rebuild_index: bool = False) -> DoctorReport:
    """Validate storage and optionally rebuild the derived index."""

    issues: list[str] = []
    notes = []
    for directory in (store.notes_dir, store.archive_dir):
        for path in sorted(directory.glob("*.md")) if directory.exists() else []:
            try:
                notes.append(store.read_note_file(path))
            except InvalidNoteError as exc:
                # Doctor aggregates file-level failures so one bad note does not
                # hide additional corruption elsewhere in the repository.
                issues.append(str(exc))

    # Duplicate ids are a higher-severity integrity problem than duplicate
    # slugs, because ids are the canonical reference target for the CLI.
    seen_ids = Counter(note.note_id for note in notes)
    for note_id, count in seen_ids.items():
        if count > 1:
            issues.append(f"duplicate note id: {note_id}")

    rebuilt = False
    if rebuild_index and not issues:
        # Rebuild only when the corpus parsed cleanly; otherwise we risk
        # replacing a previously valid index with one missing broken notes.
        store.rebuild_index()
        rebuilt = True

    index_missing = not store.index_path.exists()
    if index_missing and not rebuild_index:
        issues.append(f"missing index file: {store.index_path}")

    if not rebuild_index and store.index_path.exists():
        try:
            store.load_index()
        except Exception as exc:  # pragma: no cover - cache corruption is rare
            # The index is derived, so corruption is reportable but not fatal to
            # recovery; users can rerun doctor with --rebuild-index.
            issues.append(f"invalid index file: {exc}")

    ok = not issues
    return DoctorReport(ok=ok, issues=issues, note_count=len(notes), index_rebuilt=rebuilt)
