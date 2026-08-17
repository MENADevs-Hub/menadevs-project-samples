# Contributing

## Workflow

- One issue = one branch = one PR
- Branch off `main`, open a PR, get CI green, then merge
- Never push directly to `main`

## Branch Naming

```
feat/<short-description>
fix/<short-description>
chore/<short-description>
docs/<short-description>
test/<short-description>
```

## Commit Messages

Follow Conventional Commits:

```
feat: add tree command
fix: handle permission errors in recursive walk
chore: update eslint config
test: add depth-limit tests
docs: add usage examples
```

## Development Setup

```bash
npm install
npm link        # makes dirtree available globally
npm test        # run jest
npm run lint    # run eslint
```

## Pull Request Checklist

- [ ] All tests pass (`npm test`)
- [ ] Linting is clean (`npm run lint`)
- [ ] New features have tests
- [ ] No secrets or credentials committed
