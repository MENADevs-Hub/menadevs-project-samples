# Setup Guide

This guide covers the final setup for `inkwell-cli-notes`.

## 1. Install dependencies

```bash
uv sync --dev
cp .env.example .env
```

## 2. Run the CLI locally

```bash
uv run inkwell --help
uv run inkwell --version
uv run inkwell status
uv run inkwell init
```

## 3. Run quality checks

```bash
uv run pytest
uv run ruff check .
uv run python -m mypy src tests
uv run python -m build
```

## 4. Phase Branches

- `feat/core-note-storage`
- `feat/notes-cli-workflows`
- `feat/search-export-doctor`
- `test/harden-docs-and-quality`

Commit messages should use conventional command form, for example:

```text
feat: add core note storage
```

## 5. GitHub Readiness

- Keep `.github/workflows/ci.yml` unchanged.
- Open pull requests with the summary plus validation commands.
- Prefer one phase per branch so review stays focused.
