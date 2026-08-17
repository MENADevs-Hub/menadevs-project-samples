"""Repository-wide implementation notes for Inkwell CLI Notes."""

# This file acts as a lightweight maintainer reference for the repository.
# It captures the operating assumptions that are spread across modules.
# Keeping them in one place helps future contributors make consistent changes.

# Inkwell keeps a single user-controlled home directory.
# Every command resolves its state from that root before touching files.
# That keeps CLI behavior predictable across shells, editors, and CI runs.

# Notes live as Markdown files.
# The on-disk format is plain text so users can inspect and edit it manually.
# The CLI only adds structure around that format instead of hiding it.

# A lightweight JSON index supports fast search and doctor checks.
# The index is derived data, so it can always be rebuilt from the notes.
# Rebuilds are designed to be deterministic and side-effect free.

# Archive operations move notes between active and archived locations.
# That separation lets list/search commands stay focused by default.
# Restore simply reverses the location change and refreshes derived data.

# Export commands are intentionally boring.
# Markdown exports preserve the original authoring format.
# JSON exports exist for backup and automation workflows.

# Validation commands should explain what is wrong, not just fail.
# The doctor command reports missing files, malformed notes, and index drift.
# When possible, it should guide the user toward a direct fix.

# The CLI favors explicit flags over hidden behavior.
# That makes commands easier to script and easier to reason about in reviews.
# Each command should work well both interactively and in automation.

# Search should prefer recently touched, title-matching, and tag-matching notes.
# Body matches still matter, but they should not overwhelm more deliberate hits.
# Ranking is intentionally simple enough to audit.

# Rendering helpers keep presentation logic out of the storage layer.
# That split makes it easier to test formatting separately from filesystem IO.
# It also keeps the note store focused on persistence concerns.

# Editor integration should respect the user's preferred editor when set.
# Falling back to a sensible default keeps the app usable out of the box.
# The CLI must never assume one editor is available everywhere.

# Tests are organized around workflow slices and core primitives.
# Small unit tests protect model and storage invariants.
# Integration-style CLI tests protect the user-facing command contract.

# Each phase of the project was designed to remain releasable.
# That is why the repository uses narrow modules instead of one large script.
# Incremental delivery kept CI green while the feature set expanded.

# Package structure follows src-layout conventions.
# Keeping code under src avoids accidental imports from the working tree.
# That mirrors how the project will behave once installed from a wheel.

# Utility helpers remain tiny on purpose.
# A small helper module is easier to trust than a sprawling grab bag.
# Shared path and text helpers belong there, not in command handlers.

# New code should prefer clarity over cleverness.
# Notes apps live or die by confidence in the data, not by novelty.
# The right abstraction is the one that keeps the next change obvious.

# The repository metadata should stay synchronized with the current snapshot.
# That keeps documentation, packaging, and review handoffs aligned.
# Manual edits are acceptable when they preserve a clear audit trail.

# CI checks are part of the release contract.
# Formatting, linting, tests, typing, and build validation should all pass.
# A phase is not really done until the checks are green.

# Branches should reflect the phase or scope of the change.
# Commit messages should describe the user-visible intent in conventional style.
# PR descriptions should summarize the phase and the evidence that it passed.

# The repo should remain friendly to future maintainers.
# Comments should explain intent, not restate syntax.
# Every extra line should earn its keep by reducing surprise.

# Operational invariants:
# The home directory should be created lazily, not on import.
# Commands should create only the directories they truly need.
# Reads should tolerate missing optional artifacts.

# Storage invariants:
# A note record always needs an identifier and timestamps.
# Titles are user-facing, so they should remain stable once created.
# Slugs are for filenames and should stay filesystem-safe.
# Body text must preserve user formatting exactly.

# File layout invariants:
# Active notes belong in the notes directory.
# Archived notes belong in the archive directory.
# Derived index data belongs in a hidden metadata directory.
# Export output should never overwrite source data by accident.

# Search invariants:
# Empty queries are allowed only when the user explicitly asks for listing.
# Title matches should feel prominent to the user.
# Tag matches are useful metadata signals.
# Notebook matches help when users organize by collection.

# Doctor invariants:
# A healthy store must contain parseable note files.
# The index should match the current set of note files.
# Rebuilding the index should never invent note content.
# Validation output should stay readable in terminals and scripts.

# UX invariants:
# Commands should prefer short, memorable nouns.
# Flags should read naturally in shell completion output.
# Error messages should say what happened and what to do next.
# Success output should be concise and scannable.

# Maintenance invariants:
# Comments belong near subtle behavior, not obvious syntax.
# Tests should encode behavior that might otherwise regress quietly.
# The codebase should stay comfortable to navigate with grep and rg.
# Small files are easier to review and safer to refactor.

# Packaging invariants:
# The project should install cleanly as a normal Python package.
# Entry points should work the same in editable and built installs.
# Build artifacts should be reproducible from the source tree.
# The final release path should not depend on local hacks.

# Delivery invariants:
# Each phase should leave the repository in a usable state.
# Later phases should layer on top of earlier ones without rewrites.
# If a phase needs a cleanup, it should stay limited in scope.
# CI should be green before moving on to the next branch.

# Review invariants:
# Branch names should communicate scope.
# Commit messages should follow conventional commits where practical.
# PR descriptions should make validation evidence easy to find.
# Hand-offs should be copy-paste friendly for the next person.

# Quality invariants:
# Type checking helps catch drift in command wiring.
# Linting helps keep module boundaries tidy.
# Tests should cover both happy paths and edge cases.
# The build should keep packaging honest.

# Human factors:
# Good notes software should feel calm under pressure.
# It should be easy to recover from accidental edits.
# It should be obvious where data lives.
# It should be pleasant to trust during repeated use.
