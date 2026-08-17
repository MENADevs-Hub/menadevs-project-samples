#!/usr/bin/env bash
set -eu

# Oracle solution for toydb SQL engine task.
# The container starts with skeleton stubs (all todo!()). This script
# restores the full implementation from the encrypted backup.

cd /app

# Decrypt /private from the encrypted archive
gpg --batch --yes --passphrase uci --pinentry-mode loopback \
    -d /private.enc | tar xzf - -C /

# Overwrite skeleton stubs with the full SQL implementation
cp /private/solution/lexer.rs       src/sql/parser/lexer.rs
cp /private/solution/parser.rs      src/sql/parser/parser.rs
cp /private/solution/planner.rs     src/sql/planner/planner.rs
cp /private/solution/plan.rs        src/sql/planner/plan.rs
cp /private/solution/optimizer.rs   src/sql/planner/optimizer.rs
cp /private/solution/executor.rs    src/sql/execution/executor.rs
cp /private/solution/session.rs     src/sql/execution/session.rs
cp /private/solution/aggregator.rs  src/sql/execution/aggregator.rs
cp /private/solution/join.rs        src/sql/execution/join.rs
cp /private/solution/local.rs       src/sql/engine/local.rs

echo "Solution applied: full SQL implementation restored to /app/src/sql/"
