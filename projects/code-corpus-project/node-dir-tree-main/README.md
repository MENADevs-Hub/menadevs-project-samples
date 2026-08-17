# node-dir-tree

A CLI tool that prints a visual directory tree with depth limiting, ignore patterns, hidden-file control, size annotations, symlink detection, and permission-error handling.

## Installation

```bash
npm install
npm link
```

## Usage

```bash
dirtree tree <path> [options]
dirtree summary <path> [options]
```

### tree

Print a visual directory tree.

```bash
dirtree tree ./my-project
dirtree tree ./my-project --depth 2
dirtree tree ./my-project --ignore node_modules --ignore .git
dirtree tree ./my-project --hidden --size
dirtree tree ./my-project --format json
```

### summary

Print file and directory counts with total size.

```bash
dirtree summary ./my-project
dirtree summary ./my-project --depth 3 --format json
```

### Options

| Option | Description |
|--------|-------------|
| `--depth <n>` | Max recursion depth |
| `--ignore <pattern>` | Glob pattern to exclude (repeatable) |
| `--hidden` | Include hidden files and directories |
| `--size` | Show file size next to each entry (tree only) |
| `--format text\|json` | Output format (default: text) |

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | Path does not exist or is not a directory |
| `2` | Invalid arguments |

## Development

```bash
npm install
npm test
npm run lint
```

## License

MIT
