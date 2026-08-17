# Contributing

## Setup

```bash
git clone https://github.com/code-corpus/node-todo-cli.git
cd node-todo-cli
npm install
```

## Running tests

```bash
npm test
```

## Linting

```bash
npm run lint
```

## Conventions

- Branch names: `feat/<short-description>`, `fix/<short-description>`, `chore/<short-description>`
- Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/)
- All new behavior must have tests in `tests/`
- Do not commit `node_modules/` or `~/.todo-cli/todos.json`
