"""Export helpers for notes collections."""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Literal

from inkwell_cli_notes.index import build_index
from inkwell_cli_notes.models import Note
from inkwell_cli_notes.render import note_document


def export_notes(notes: Sequence[Note], output: Path, *, fmt: Literal["markdown", "json"]) -> Path:
    """Export notes to a Markdown directory or JSON file."""

    if fmt == "markdown":
        output.mkdir(parents=True, exist_ok=True)
        for note in notes:
            relative = note.path.name
            export_path = output / relative
            # Markdown export preserves the stored document format so exported
            # notes can be reviewed or restored without a custom importer.
            export_path.write_text(note_document(note), encoding="utf-8")
        return output

    payload = {
        # JSON export shares the index timestamp format so backup artifacts stay
        # consistent with the rest of the repository's derived data.
        "generated_at": build_index(notes).generated_at,
        "notes": [
            {
                "metadata": note.metadata.model_dump(by_alias=True, mode="json"),
                "body": note.body,
                "path": str(note.path),
            }
            for note in notes
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return output
