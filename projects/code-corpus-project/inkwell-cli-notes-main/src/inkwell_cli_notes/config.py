"""Configuration primitives for the CLI foundation."""

from __future__ import annotations

import os
from pathlib import Path

from platformdirs import user_data_path
from pydantic import BaseModel, ConfigDict


class Settings(BaseModel):
    """Runtime settings used by the phase-one CLI foundation."""

    model_config = ConfigDict(frozen=True)

    home_dir: Path
    editor: str | None
    index_name: str = "index.json"


def load_settings(
    *,
    home_override: Path | None = None,
    editor_override: str | None = None,
    index_name_override: str | None = None,
) -> Settings:
    """Load application settings from the environment."""

    env_home = os.getenv("INKWELL_HOME")
    # Precedence is explicit flag, then dedicated app env var, then the
    # platform-specific data directory so scripts can override predictably.
    home_dir = (
        home_override.expanduser()
        if home_override is not None
        else Path(env_home).expanduser()
        if env_home
        else user_data_path("inkwell-cli-notes")
    )

    editor = editor_override or os.getenv("INKWELL_EDITOR") or os.getenv("EDITOR") or os.getenv(
        "VISUAL"
    )
    env_index_name = os.getenv("INKWELL_INDEX_NAME")
    # The index name is configurable mostly for tests and isolated sandboxes
    # where multiple repositories may share the same temp home.
    index_name = index_name_override if index_name_override is not None else env_index_name
    if index_name is None:
        index_name = "index.json"
    return Settings(home_dir=home_dir, editor=editor, index_name=index_name)
