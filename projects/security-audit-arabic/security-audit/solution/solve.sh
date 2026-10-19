#!/bin/bash
set -euo pipefail

SOLUTION_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cp "$SOLUTION_DIR/app/app.py" /app/app.py
cp "$SOLUTION_DIR/app_tests/"*.py /app/tests/
cp "$SOLUTION_DIR/SECURITY_REPORT.md" /app/SECURITY_REPORT.md

echo "Security fixes applied under /app"
