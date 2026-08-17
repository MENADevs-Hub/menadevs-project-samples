# Setup Guide

This guide covers the phase-one foundation for `py-md-toc`.

## 1. Install dependencies

```bash
python -m pip install -r requirements.txt
```

## 2. Run the CLI

```bash
py-md-toc --help
py-md-toc --version
py-md-toc README.md
py-md-toc README.md --output /tmp/toc.md
py-md-toc README.md --in-place
```

## 3. Run quality checks

```bash
python -m pytest
ruff check .
python -m build
```

If you are validating an edited Markdown file with managed markers, `--check`
is the quickest way to see whether the generated TOC still matches the file.

## 4. Continue with phase branches

Use short Conventional Commit branch names for later phases:

- `feat/toc-core`
- `feat/toc-cli-workflows`
- `test/harden-toc-tooling`

Use commit messages in this format:

```text
<type>: <short description in command form>
```
