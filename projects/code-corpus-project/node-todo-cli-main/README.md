# node-todo-cli

A command-line todo manager that stores tasks in a local JSON file. Supports
projects, tags, priority levels, due dates, multi-axis filtering, and JSON/CSV
export.

## Installation

```bash
npm install
npm link        # makes `todo` available globally
```

Or run directly:

```bash
node src/cli.js --help
```

## Commands

### add

```bash
todo add "Buy groceries" --project personal --priority high --due 2026-07-01 --tag errands
```

Options:

| Flag | Description |
|------|-------------|
| `--project <name>` | Assign to a project |
| `--priority low\|normal\|high` | Priority level (default: normal) |
| `--due <YYYY-MM-DD>` | Due date |
| `--tag <tag>` | Tag, repeatable |

### list

```bash
todo list
todo list --status done
todo list --project work --priority high
todo list --overdue
todo list --format json
```

Options:

| Flag | Description |
|------|-------------|
| `--status open\|done\|all` | Filter by status (default: open) |
| `--project <name>` | Filter by project |
| `--priority <level>` | Filter by priority |
| `--tag <tag>` | Filter by tag |
| `--overdue` | Show only overdue items |
| `--format text\|json` | Output format (default: text) |

### done

```bash
todo done a1b2c3d4
todo done a1b2        # prefix match
```

### delete

```bash
todo delete a1b2c3d4
```

### export

```bash
todo export
todo export --format csv
todo export --format json --output backup.json
todo export --status open --format csv
```

### stats

```bash
todo stats
todo stats --project work
todo stats --format json
```

## Global Options

| Flag | Description |
|------|-------------|
| `--storage <path>` | Override default storage file (`~/.todo-cli/todos.json`) |
| `--version` | Print version |
| `--help` | Print help |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Item not found, path error, or storage failure |
| 2 | Invalid arguments (bad date, bad priority, bad format) |

## Storage

Todos are stored in `~/.todo-cli/todos.json`. The file is created automatically
on first use. If the file is corrupted, a backup is saved and the store resets.

## Development

```bash
npm install
npm run lint
npm test
```

## License

MIT
