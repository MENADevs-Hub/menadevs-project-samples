"""Helpers for opening notes in a text editor."""

from __future__ import annotations

import os
import shlex
import subprocess
import tempfile
from pathlib import Path

from inkwell_cli_notes.errors import EditorError


def resolve_editor(preferred: str | None) -> str:
    """Return the editor command to use for an interactive edit."""

    # Respecting both application-specific and conventional editor variables
    # makes the CLI feel native in developer shells.
    return preferred or os.getenv("EDITOR") or os.getenv("VISUAL") or "vi"


def edit_text_in_editor(text: str, editor_command: str) -> str:
    """Write text to a temp file, open it in an editor, and return the result."""

    editor_args = shlex.split(editor_command)
    if not editor_args:
        raise EditorError("no editor command is available")

    with tempfile.NamedTemporaryFile(
        mode="w+",
        encoding="utf-8",
        delete=False,
        suffix=".md",
    ) as handle:
        handle.write(text)
        handle.flush()
        temp_path = Path(handle.name)

    try:
        # The editor receives a real filesystem path so terminal editors and
        # GUI wrappers can both participate in the same workflow.
        subprocess.run([*editor_args, str(temp_path)], check=True)
        return temp_path.read_text(encoding="utf-8")
    except subprocess.CalledProcessError as exc:
        raise EditorError(f"editor command failed: {editor_command}") from exc
    finally:
        # Temp cleanup happens even on editor failure so aborted sessions do not
        # leave stale note fragments behind on disk.
        temp_path.unlink(missing_ok=True)
