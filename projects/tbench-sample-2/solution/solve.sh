#!/bin/bash
set -euo pipefail
cd /app

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FIXED_DIR=""
for candidate in "$SCRIPT_DIR/fixed" /solution/fixed /oracle/fixed; do
    if [ -d "$candidate" ]; then
        FIXED_DIR="$candidate"
        break
    fi
done

if [ -z "$FIXED_DIR" ]; then
    echo "Unable to locate fixed source files" >&2
    exit 1
fi

cp "$FIXED_DIR/src/normalize.js" /app/src/normalize.js
cp "$FIXED_DIR/src/time.js" /app/src/time.js
cp "$FIXED_DIR/src/state.js" /app/src/state.js
cp "$FIXED_DIR/src/evaluate.js" /app/src/evaluate.js
cp "$FIXED_DIR/src/files.js" /app/src/files.js

node /app/scripts/smoke-check.js
