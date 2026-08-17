# py-md-toc

`py-md-toc` is a Python CLI for generating a table of contents from Markdown headings.

This repository is being built in phases. Phase 1 establishes the packaging, CLI shell, documentation, and test scaffolding. The Markdown parsing and TOC generation engine land in later phases.

## Current Foundation

- Python 3.12 package layout under `src/py_md_toc`.
- Console entry point: `py-md-toc`.
- Minimal CLI help and version output.
- CI-friendly tooling for linting, testing, and builds.

## Setup

```bash
python -m pip install -r requirements.txt
```

## Run

```bash
py-md-toc --help
py-md-toc --version
py-md-toc docs/example.md
py-md-toc docs/example.md --output docs/toc.md
py-md-toc docs/example.md --in-place
py-md-toc docs/example.md --check
```

## Markdown Example

```markdown
# Project Title

<!-- py-md-toc:start -->
<!-- py-md-toc:end -->

## Usage
### Install
### Run
```

## Checks

```bash
python -m pytest
ruff check .
python -m build
```

## Behavior Notes

- The default command prints the generated TOC to stdout.
- `--output` writes the TOC text to a separate file.
- `--in-place` updates only the content between the managed markers.
- `--check` exits with a nonzero status when the managed block is stale.

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
│   └── py_md_toc/
├── tests/
├── pyproject.toml
├── .pre-commit-config.yaml
└── config/
```

## Phase Branches

- `main` - foundation
- `feat/toc-core` - heading parsing and TOC rendering
- `feat/toc-cli-workflows` - stdout, file output, and in-place updates
- `test/harden-toc-tooling` - documentation and edge-case hardening
