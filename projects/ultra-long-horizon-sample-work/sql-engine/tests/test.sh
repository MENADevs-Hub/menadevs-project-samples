#!/usr/bin/env bash
set -o pipefail

cd /app

mkdir -p /logs/verifier

# -- Step 1: Decrypt /private from the encrypted archive ----------------------
gpg --batch --yes --passphrase uci --pinentry-mode loopback \
    -d /private.enc | tar xzf - -C /

# -- Step 2: Restore tamper-proof test files from /private backup --------------
echo "=== Restoring tamper-proof test files ==="

rm -rf src/sql/testscripts
cp -r /private/sql_testscripts src/sql/testscripts
cp /private/sql_mod.rs src/sql/mod.rs
rm -rf src/raft/testscripts
cp -r /private/raft_testscripts src/raft/testscripts
rm -rf tests
cp -r /private/integration_tests tests

echo "=== Test files restored ==="

# -- Step 3: Build the project -------------------------------------------------
echo "=== Building toydb ==="
cargo build --release 2>&1 | tee /logs/verifier/build_output.log
build_status=${PIPESTATUS[0]}

if [ $build_status -ne 0 ]; then
    echo "=== BUILD FAILED ==="
    echo 0 > /logs/verifier/reward.txt
    exit 0
fi

echo "=== Build succeeded ==="

# -- Step 4: Run pytest (individual test functions with partial scoring) --------
echo "=== Running tests ==="
pytest /tests/test_sql.py \
    --ctrf /logs/verifier/ctrf.json \
    -rA -v \
    2>&1 | tee /logs/verifier/test_output.log

# -- Step 5: Compute partial reward from ctrf.json ----------------------------
python3 /tests/compute_reward.py
