# Contributing

Thanks for contributing to `customer-data-cleaning-pipeline`. This project follows a
simple, disciplined GitHub Flow.

## Getting started

```bash
git clone https://github.com/code-corpus/customer-data-cleaning-pipeline.git
cd customer-data-cleaning-pipeline
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pre-commit install               # optional but recommended
```

## Workflow

- `main` is protected and always runnable.
- One issue = one branch = one pull request.
- Never push directly to `main`.
- Merge only after CI passes and the PR is approved.

## Branch naming

```text
feature/<short-description>    new feature
fix/<short-description>        bug fix
chore/<short-description>      maintenance, config, CI
docs/<short-description>       documentation
test/<short-description>       tests only
refactor/<short-description>   restructuring without behavior change
```

## Commit messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

```text
feat: add fuzzy deduplication engine
fix: handle empty phone values
test: cover invalid email cases
chore: add ci workflow
docs: add usage examples
refactor: simplify normalization pipeline
```

Keep the subject line under 72 characters and use the imperative mood.

## Code style

- **Linter / formatter**: [ruff](https://docs.astral.sh/ruff/) with `line-length = 100`
  and `target-version = py311`.
- **Import order**: managed by ruff (`I` rule set) — do not reorder manually.
- **No unused imports, no bare `except`**: enforced by ruff (`F`, `E`, `B` rule sets).

Run the linter before opening a PR:

```bash
ruff check .
```

## Local checks before opening a PR

All four must pass. CI runs the same checks on every PR.

```bash
pip install -e ".[dev]"
ruff check .
pytest -v
python -m compileall src
```

## Running specific tests

```bash
pytest tests/test_reporter.py -v      # one test module
pytest -k "test_cleaned" -v           # tests whose name contains the keyword
pytest -q --maxfail=1                 # stop after the first failure
```

Fixtures shared across modules live in `tests/conftest.py` (`project_root`,
`sample_raw_csv`). Use them for any test that needs the config directory or sample data.

## Pre-commit hooks

After running `pre-commit install`, the following checks run automatically on every
`git commit`:

- **ruff** — lint and auto-fix imports/style issues
- **end-of-file-fixer**, **trailing-whitespace**, **check-yaml** — file hygiene
- **TruffleHog** — secret scan on staged commits

## Pull requests

Every PR must answer:

- What does this change do?
- Which issue does it serve?
- How was it tested?

Use this template when opening the PR on GitHub:

```markdown
## Summary

## Related Issue
Closes #<n>

## Changes
-

## Testing

## Reviewer Notes

## Checklist
- [ ] Branch name follows the team convention
- [ ] Commit messages follow Conventional Commits
- [ ] Tests were added or updated
- [ ] CI passes
- [ ] No secrets or credentials were committed
- [ ] Documentation updated if needed
```

## What not to commit

```text
.env
*.pem / *.key / *.p12
secrets.yaml / credentials.json
data/output/          (runtime artifacts — gitignored)
__pycache__ / *.pyc   (gitignored)
.venv/                (gitignored)
```

If you accidentally stage a secret, remove it from history before pushing. Do not
use `--no-verify` to bypass the pre-commit hooks.
