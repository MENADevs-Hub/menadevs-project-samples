# Contributing

Every change should leave the CLI buildable, testable, and easier to evolve.

## Workflow

1. Branch from `main` using `<type>/<short-description>`.
2. Keep each branch aligned to one planned phase or one tightly scoped fix.
3. Run the same checks CI runs before opening a pull request.
4. Use conventional commit messages in command form.

## Pull Request Template

```markdown
## Summary

- <change>
- <change>

## Validation

- `ruff check .`
- `pytest -q --maxfail=1`
- `python -m mypy src tests`
- `python -m build`
```

## Rules

- Do not modify `.github/workflows/ci.yml` unless the task explicitly requires it.
- Never commit secrets or local `.env` files.
- Keep source changes typed, tested, and documented when behavior changes.
- Prefer plain Markdown files as the source of truth for notes and metadata.
- Keep branch names and commit messages short, conventional, and phase-scoped.
