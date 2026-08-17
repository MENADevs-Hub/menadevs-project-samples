# TBench Sample 2

This benchmark asks an implementer to correct a Node.js email-suppression planner so it produces deterministic send/no-send decisions from JSONL event data, including out-of-order and corrected events.

## Technology and structure

- Node.js implementation and command-line entry point under `environment/`.
- Contract and operational documentation under `environment/docs/`.
- Python output-validation tests under `tests/`.
- A fixed reference solution under `solution/`.
- Docker configuration for a reproducible evaluation environment.

The original benchmark identifier and macOS metadata are retained within this normalized project folder.
