# Email suppression planner

This small Node.js service reads email lifecycle events and writes a deterministic suppression report for downstream send planning. The CLI is intentionally dependency-free so it can run in restricted batch environments.

The behavioral contract lives in `docs/suppression-contract.md`.
