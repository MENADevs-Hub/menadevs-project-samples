"""Rich rendering helpers for notes commands."""

from __future__ import annotations

from collections.abc import Sequence

import frontmatter
from rich.table import Table

from inkwell_cli_notes.models import Note


def note_document(note: Note) -> str:
    """Render a note to the on-disk Markdown document format."""

    # Rendering goes through the same frontmatter library used for parsing so
    # round-trips stay faithful to the supported document structure.
    post = frontmatter.Post(
        note.body,
        **note.metadata.model_dump(by_alias=True, mode="json"),
    )
    return frontmatter.dumps(post)


def notes_table(notes: Sequence[Note]) -> Table:
    """Create a readable summary table for note listings."""

    table = Table(title="Notes", show_lines=False)
    table.add_column("State", style="cyan", no_wrap=True)
    table.add_column("Title", style="bold")
    table.add_column("Notebook", no_wrap=True)
    table.add_column("Tags")
    table.add_column("Updated", no_wrap=True)
    table.add_column("ID", no_wrap=True)

    for note in notes:
        # State is condensed into one column so wide note titles still fit well
        # in ordinary terminal widths.
        state = "archived" if note.metadata.archived else "active"
        if note.metadata.pinned:
            state = f"{state}, pinned"
        table.add_row(
            state,
            note.metadata.title,
            note.metadata.notebook,
            ", ".join(note.metadata.tags) if note.metadata.tags else "-",
            note.metadata.updated_at.isoformat(timespec="minutes"),
            note.note_id,
        )
    return table


def search_results_table(results: Sequence[tuple[Note, float]]) -> Table:
    """Create a readable table for ranked search results."""

    table = Table(title="Search Results", show_lines=False)
    table.add_column("Score", justify="right", no_wrap=True)
    table.add_column("Title", style="bold")
    table.add_column("Notebook", no_wrap=True)
    table.add_column("Tags")
    table.add_column("State", no_wrap=True)
    table.add_column("ID", no_wrap=True)

    for note, score in results:
        # Scores stay visible to make the ranking behavior inspectable during
        # testing and while tuning the search weights over time.
        table.add_row(
            f"{score:.1f}",
            note.metadata.title,
            note.metadata.notebook,
            ", ".join(note.metadata.tags) if note.metadata.tags else "-",
            "archived" if note.metadata.archived else "active",
            note.note_id,
        )
    return table
