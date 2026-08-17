# Configuration

`inkwell-cli-notes` reads runtime settings from environment variables and an optional
`.env` file during local development.

Copy the sample file before running locally:

```bash
cp .env.example .env
```

Current settings:

- `INKWELL_HOME`: override the default application data directory.
- `INKWELL_EDITOR`: editor override used before falling back to `$EDITOR`, then `$VISUAL`.
- `INKWELL_INDEX_NAME`: name of the derived JSON index file inside `.inkwell/`.

The CLI also accepts `--home PATH` on every command, which is useful for tests and
scripted runs.
