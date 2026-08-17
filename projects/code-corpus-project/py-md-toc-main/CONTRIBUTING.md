# Contributing

Every change should be small, reviewable, and backed by tests.

## Workflow

1. Create or reference the work item.
2. Branch from `main` using a short Conventional Commit-style name, such as `feat/toc-core`.
3. Commit in imperative Conventional Commit form, such as `feat: add markdown toc parser`.
4. Open a pull request with the validation commands you ran.
5. Wait for CI to pass before merging.

## Rules

- Never commit secrets or `.env` files.
- Keep comments focused on intent, invariants, or non-obvious behavior.
- Ship tests with behavior changes.
