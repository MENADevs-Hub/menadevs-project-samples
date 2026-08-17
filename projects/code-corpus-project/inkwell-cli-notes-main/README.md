# Inkwell CLI Notes

`inkwell-cli-notes` is a production-oriented, local-first CLI for writing and
organizing Markdown notes. Notes live on disk as plain files, so the tool stays
scriptable, portable, and easy to recover.

The repo is now GitHub-ready: the package is typed, tested, buildable, and split into
clear CLI workflows with a rebuildable local index. No hidden services are required.

## Planned Feature Set

- Create Markdown notes with titles, tags, notebooks, and pinned status.
- List and search notes from the terminal.
- Open notes in `$EDITOR` for focused editing.
- Archive, restore, delete, and export notes.
- Rebuild local indexes from note files when needed.
- Validate storage health and cache integrity with `doctor`.

Out of scope: sync, encryption, web UI, TUI, remote storage, AI features, and plugins.

## Requirements

- Python 3.12
- `uv` for local development convenience

## Setup

```bash
uv sync --dev
cp .env.example .env
```

## Run

```bash
uv run inkwell --help
uv run inkwell --version
uv run inkwell status
uv run inkwell search "project launch"
uv run inkwell doctor --rebuild-index
```

## Test And Quality Checks

```bash
uv run pytest
uv run ruff check .
uv run python -m mypy src tests
uv run python -m build
```

## Project Structure

```text
.
├── README.md
├── .gitignore
├── .editorconfig
├── LICENSE
├── CONTRIBUTING.md
├── .github/
│   └── workflows/
│       └── ci.yml
├── src/
│   └── inkwell_cli_notes/
├── tests/
├── pyproject.toml
├── requirements.txt
├── .pre-commit-config.yaml
└── config/
```

## Phase Plan

- `main`: `chore: set up initial project foundation`
- `feat/core-note-storage`: `feat: add core note storage`
- `feat/notes-cli-workflows`: `feat: expose notes cli workflows`
- `feat/search-export-doctor`: `feat: add search export and doctor workflows`
- `test/harden-docs-and-quality`: `test: harden documentation and quality checks`

## Notes Home

By default the CLI stores notes in the platform-specific application data directory.
Use `--home PATH` for scripting, tests, or a custom workspace root.
