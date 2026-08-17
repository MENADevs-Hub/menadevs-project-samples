"""Typer app entrypoint for the Inkwell CLI."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Literal, cast

import frontmatter
import typer
from pydantic import ValidationError
from rich.console import Console
from rich.markdown import Markdown

from inkwell_cli_notes import __version__
from inkwell_cli_notes.config import Settings, load_settings
from inkwell_cli_notes.doctor import run_doctor
from inkwell_cli_notes.editor import edit_text_in_editor, resolve_editor
from inkwell_cli_notes.errors import EditorError, InkwellError
from inkwell_cli_notes.export import export_notes
from inkwell_cli_notes.models import Note
from inkwell_cli_notes.render import note_document, notes_table, search_results_table
from inkwell_cli_notes.storage import NoteStore

app = typer.Typer(
    add_completion=False,
    help="Local-first CLI for building a durable Markdown notes practice.",
    no_args_is_help=True,
)
console = Console()


@dataclass(frozen=True, slots=True)
class AppContext:
    """Shared application state for a single CLI invocation."""

    settings: Settings
    store: NoteStore


def build_context(home_override: Path | None = None) -> AppContext:
    """Create app settings and storage for the current invocation."""

    # The CLI builds context once per invocation so commands can share resolved
    # settings without reaching back into environment variables repeatedly.
    settings = load_settings(home_override=home_override)
    return AppContext(
        settings=settings,
        store=NoteStore(settings.home_dir, index_name=settings.index_name),
    )


def get_context(ctx: typer.Context) -> AppContext:
    """Return the active application context."""

    if isinstance(ctx.obj, AppContext):
        return ctx.obj
    # Tests and programmatic calls can bypass the top-level callback, so we
    # lazily create context here instead of assuming it already exists.
    context = build_context()
    ctx.obj = context
    return context


def version_callback(value: bool) -> None:
    """Print the installed version and exit early."""

    if value:
        console.print(f"inkwell-cli-notes {__version__}")
        raise typer.Exit()


def _print_error(exc: InkwellError) -> None:
    # Keeping error presentation in one helper makes command handlers read like
    # workflows instead of mixing control flow with Rich formatting details.
    console.print(f"[red]{exc}[/red]")


def _filtered_notes(
    notes: list[Note],
    *,
    tag: str | None = None,
    notebook: str | None = None,
    pinned: bool = False,
    archived: bool = False,
    all_notes: bool = False,
    limit: int | None = None,
) -> list[Note]:
    """Apply command-line filters to a note list."""

    filtered = notes
    # The archived/all interaction mirrors the public command semantics:
    # `--all` broadens scope, while `--archived` narrows it to archived only.
    if not all_notes:
        filtered = [note for note in filtered if note.metadata.archived is archived]
    elif archived:
        filtered = [note for note in filtered if note.metadata.archived]
    if tag is not None:
        filtered = [note for note in filtered if tag in note.metadata.tags]
    if notebook is not None:
        filtered = [note for note in filtered if note.metadata.notebook == notebook]
    if pinned:
        filtered = [note for note in filtered if note.metadata.pinned]
    if limit is not None:
        filtered = filtered[:limit]
    return filtered


def _note_scope(
    store: NoteStore,
    *,
    archived: bool = False,
    all_notes: bool = False,
) -> list[Note]:
    """Return the note scope for list/search/export commands."""

    # Commands that operate on collections share one scope helper so the
    # archive semantics stay consistent across the CLI surface.
    return store.list_notes(include_archived=all_notes or archived)


@app.callback()
def main(
    ctx: typer.Context,
    home: Annotated[
        Path | None,
        typer.Option(
            "--home",
            help="Override the notes home directory for this invocation.",
            exists=False,
            file_okay=False,
            dir_okay=True,
            resolve_path=False,
        ),
    ] = None,
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            help="Show the installed CLI version and exit.",
            callback=version_callback,
            is_eager=True,
        ),
    ] = False,
) -> None:
    """Initialize shared CLI behavior."""

    ctx.obj = build_context(home)


@app.command("status")
def status(ctx: typer.Context) -> None:
    """Show the current foundation status and resolved home directory."""

    context = get_context(ctx)
    settings = context.settings
    console.print("Inkwell foundation is ready.")
    console.print(f"Home directory: {settings.home_dir}")
    console.print(f"Index file: {settings.index_name}")


@app.command("init")
def init(ctx: typer.Context) -> None:
    """Create the storage directories used by the CLI."""

    context = get_context(ctx)
    context.store.ensure()
    console.print(f"Initialized notes home at {context.settings.home_dir}")


@app.command("new")
def new(
    ctx: typer.Context,
    title: Annotated[str, typer.Argument(help="Title for the new note.")],
    body: Annotated[str | None, typer.Option("--body", help="Initial note body.")] = None,
    tag: Annotated[list[str] | None, typer.Option("--tag", help="Attach a tag.")] = None,
    notebook: Annotated[
        str,
        typer.Option("--notebook", help="Notebook name for the note."),
    ] = "default",
    pin: Annotated[bool, typer.Option("--pin", help="Pin the note on creation.")] = False,
) -> None:
    """Create a note in the active notes directory."""

    context = get_context(ctx)
    try:
        note = context.store.create_note(
            title,
            body=body or "",
            tags=tag or [],
            notebook=notebook,
            pinned=pin,
        )
    except InkwellError as exc:
        _print_error(exc)
        raise typer.Exit(code=1) from exc

    console.print(f"Created note {note.metadata.title!r}")
    console.print(f"ID: {note.note_id}")
    console.print(f"Path: {note.path}")


@app.command("list")
def list_notes(
    ctx: typer.Context,
    tag: Annotated[str | None, typer.Option("--tag", help="Filter by a tag.")] = None,
    notebook: Annotated[
        str | None,
        typer.Option("--notebook", help="Filter by notebook."),
    ] = None,
    archived: Annotated[
        bool,
        typer.Option("--archived", help="Show archived notes only."),
    ] = False,
    all_notes: Annotated[
        bool,
        typer.Option("--all", help="Include archived notes in the listing."),
    ] = False,
    pinned: Annotated[bool, typer.Option("--pinned", help="Show pinned notes only.")] = False,
    limit: Annotated[
        int | None,
        typer.Option("--limit", min=1, help="Limit the number shown."),
    ] = None,
) -> None:
    """List notes with optional filters."""

    context = get_context(ctx)
    try:
        notes = _note_scope(context.store, archived=archived, all_notes=all_notes)
    except InkwellError as exc:
        _print_error(exc)
        raise typer.Exit(code=1) from exc

    filtered = _filtered_notes(
        notes,
        tag=tag,
        notebook=notebook,
        pinned=pinned,
        archived=archived,
        all_notes=all_notes,
        limit=limit,
    )
    if not filtered:
        console.print("No notes found.")
        return
    console.print(notes_table(filtered))


@app.command("search")
def search(
    ctx: typer.Context,
    query: Annotated[str, typer.Argument(help="Search query.")],
    tag: Annotated[str | None, typer.Option("--tag", help="Filter by a tag.")] = None,
    notebook: Annotated[
        str | None,
        typer.Option("--notebook", help="Filter by notebook."),
    ] = None,
    archived: Annotated[
        bool,
        typer.Option("--archived", help="Show archived notes only."),
    ] = False,
    all_notes: Annotated[
        bool,
        typer.Option("--all", help="Include archived notes in the search scope."),
    ] = False,
    pinned: Annotated[bool, typer.Option("--pinned", help="Show pinned notes only.")] = False,
    limit: Annotated[
        int | None,
        typer.Option("--limit", min=1, help="Limit the number shown."),
    ] = 10,
) -> None:
    """Search notes by title, tags, notebook, and body content."""

    context = get_context(ctx)
    try:
        # Search refreshes the index first so the derived cache remains warm for
        # users who search frequently and then run doctor or export operations.
        context.store.rebuild_index()
        notes = context.store.search_notes(
            query,
            tag=tag,
            notebook=notebook,
            pinned=pinned,
            archived=archived,
            all_notes=all_notes,
            limit=limit,
        )
    except InkwellError as exc:
        _print_error(exc)
        raise typer.Exit(code=1) from exc

    if not notes:
        console.print("No matches found.")
        return
    console.print(search_results_table(notes))


@app.command("show")
def show(
    ctx: typer.Context,
    reference: Annotated[str, typer.Argument(help="Note id or slug.")],
    raw: Annotated[bool, typer.Option("--raw", help="Print the raw Markdown document.")] = False,
) -> None:
    """Show one note."""

    context = get_context(ctx)
    try:
        note = context.store.get_note(reference)
    except InkwellError as exc:
        _print_error(exc)
        raise typer.Exit(code=1) from exc

    if raw:
        console.print(note_document(note))
        return

    console.rule(note.metadata.title)
    console.print(f"ID: {note.note_id}")
    console.print(f"Notebook: {note.metadata.notebook}")
    console.print(f"Tags: {', '.join(note.metadata.tags) if note.metadata.tags else '-'}")
    console.print(f"State: {'archived' if note.metadata.archived else 'active'}")
    console.print(Markdown(note.body or "_Empty note_"))


@app.command("edit")
def edit(
    ctx: typer.Context,
    reference: Annotated[str, typer.Argument(help="Note id or slug.")],
    title: Annotated[str | None, typer.Option("--title", help="Replace the note title.")] = None,
    body: Annotated[str | None, typer.Option("--body", help="Replace the note body.")] = None,
    tag: Annotated[list[str] | None, typer.Option("--tag", help="Replace tags.")] = None,
    notebook: Annotated[
        str | None,
        typer.Option("--notebook", help="Replace the notebook."),
    ] = None,
    pin: Annotated[bool, typer.Option("--pin", help="Pin the note after editing.")] = False,
) -> None:
    """Edit a note directly or through the configured editor."""

    context = get_context(ctx)
    try:
        existing = context.store.get_note(reference)
        if any(value is not None for value in (title, body, tag, notebook)) or pin:
            # Explicit CLI flags win over editor-based editing because the user
            # has already declared the intended field updates in the command.
            updated = context.store.update_note(
                reference,
                title=title,
                body=body,
                tags=tag,
                notebook=notebook,
                pinned=True if pin else None,
            )
        else:
            editor_command = resolve_editor(context.settings.editor)
            edited_text = edit_text_in_editor(note_document(existing), editor_command)
            edited_post = frontmatter.loads(edited_text)
            edited_metadata = dict(edited_post.metadata)
            # Front matter is user-editable text, so every extracted value is
            # treated as untrusted until the model layer validates it again.
            title_value = edited_metadata.get("title")
            notebook_value = edited_metadata.get("notebook")
            tags_value = edited_metadata.get("tags", existing.metadata.tags)
            pinned_value = edited_metadata.get("pinned")
            archived_value = edited_metadata.get("archived")
            tags_override = cast(Iterable[str] | None, tags_value)
            updated = context.store.update_note(
                reference,
                title=existing.metadata.title if title_value is None else str(title_value),
                body=edited_post.content,
                tags=tags_override,
                notebook=(
                    existing.metadata.notebook
                    if notebook_value is None
                    else str(notebook_value)
                ),
                pinned=existing.metadata.pinned if pinned_value is None else bool(pinned_value),
                archived=(
                    existing.metadata.archived if archived_value is None else bool(archived_value)
                ),
            )
    except (InkwellError, ValidationError) as exc:
        message = str(exc)
        if isinstance(exc, ValidationError):
            # Pydantic surfaces field-level detail, but the CLI keeps the user
            # message compact and points to the edited document as the problem.
            message = "edited note document is invalid"
        _print_error(EditorError(message) if isinstance(exc, ValidationError) else exc)
        raise typer.Exit(code=1) from exc

    console.print(f"Updated note {updated.metadata.title!r}")


@app.command("archive")
def archive(
    ctx: typer.Context,
    reference: Annotated[str, typer.Argument(help="Note id or slug.")],
) -> None:
    """Archive a note."""

    context = get_context(ctx)
    try:
        archived = context.store.archive_note(reference)
    except InkwellError as exc:
        _print_error(exc)
        raise typer.Exit(code=1) from exc

    console.print(f"Archived note {archived.metadata.title!r}")


@app.command("restore")
def restore(
    ctx: typer.Context,
    reference: Annotated[str, typer.Argument(help="Note id or slug.")],
) -> None:
    """Restore a note from the archive."""

    context = get_context(ctx)
    try:
        restored = context.store.restore_note(reference)
    except InkwellError as exc:
        _print_error(exc)
        raise typer.Exit(code=1) from exc

    console.print(f"Restored note {restored.metadata.title!r}")


@app.command("delete")
def delete(
    ctx: typer.Context,
    reference: Annotated[str, typer.Argument(help="Note id or slug.")],
    yes: Annotated[bool, typer.Option("--yes", help="Skip the confirmation prompt.")] = False,
) -> None:
    """Delete a note from disk."""

    context = get_context(ctx)
    try:
        note = context.store.get_note(reference)
        if not yes:
            # Deletes are permanent, so the prompt defaults to "no" to make
            # accidental confirmations less likely in interactive shells.
            confirmed = typer.confirm(
                f"Delete note {note.metadata.title!r}?",
                default=False,
            )
            if not confirmed:
                raise typer.Abort()
        context.store.delete_note(reference)
    except typer.Abort:
        raise
    except InkwellError as exc:
        _print_error(exc)
        raise typer.Exit(code=1) from exc

    console.print(f"Deleted note {note.metadata.title!r}")


@app.command("export")
def export(
    ctx: typer.Context,
    output: Annotated[Path, typer.Option("--output", help="Destination path.")],
    fmt: Annotated[
        Literal["markdown", "json"],
        typer.Option("--format", help="Export format."),
    ] = "markdown",
    tag: Annotated[str | None, typer.Option("--tag", help="Filter by a tag.")] = None,
    notebook: Annotated[
        str | None,
        typer.Option("--notebook", help="Filter by notebook."),
    ] = None,
    archived: Annotated[
        bool,
        typer.Option("--archived", help="Export archived notes only."),
    ] = False,
    all_notes: Annotated[
        bool,
        typer.Option("--all", help="Include archived notes in the export scope."),
    ] = False,
    pinned: Annotated[bool, typer.Option("--pinned", help="Export pinned notes only.")] = False,
    limit: Annotated[
        int | None,
        typer.Option("--limit", min=1, help="Limit the number exported."),
    ] = None,
) -> None:
    """Export the current note set to Markdown or JSON."""

    context = get_context(ctx)
    try:
        notes = _filtered_notes(
            _note_scope(context.store, archived=archived, all_notes=all_notes),
            tag=tag,
            notebook=notebook,
            pinned=pinned,
            archived=archived,
            all_notes=all_notes,
            limit=limit,
        )
        # Export only sees the filtered note set, which makes it safe to use
        # as a backup tool for one notebook or tag subset at a time.
        export_notes(notes, output, fmt=fmt)
    except InkwellError as exc:
        _print_error(exc)
        raise typer.Exit(code=1) from exc

    console.print(f"Exported {len(notes)} notes to {output}")


@app.command("doctor")
def doctor(
    ctx: typer.Context,
    rebuild_index: Annotated[
        bool,
        typer.Option("--rebuild-index", help="Rebuild the derived note index."),
    ] = False,
) -> None:
    """Validate note storage and the derived index."""

    context = get_context(ctx)
    # Doctor deliberately stays non-interactive so it can be dropped into CI,
    # cron jobs, or shell aliases without special-case parsing.
    report = run_doctor(context.store, rebuild_index=rebuild_index)
    if report.ok:
        console.print(f"Doctor report: {report.note_count} notes OK")
        if report.index_rebuilt:
            console.print(f"Rebuilt index at {context.store.index_path}")
        raise typer.Exit(code=0)

    console.print("Doctor report found problems:")
    for issue in report.issues:
        console.print(f"- {issue}")
    raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
