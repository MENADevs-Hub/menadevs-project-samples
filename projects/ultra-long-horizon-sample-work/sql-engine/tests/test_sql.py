"""
Partial-scoring test suite for the toydb SQL engine.

Each test function maps to a component from instruction.md.
Score = (passing tests) / (total tests), written to reward.txt.

Test categories:
  1.  test_compiles            – cargo check (lexer.rs + parser.rs compile)
  2.  test_expressions         – lexer.rs + parser.rs: tokenisation & expression parsing
  3.  test_schema              – planner.rs + local.rs: CREATE/DROP TABLE
  4.  test_writes              – executor.rs: INSERT, UPDATE, DELETE
  5.  test_queries_core        – plan.rs + executor.rs: SELECT, WHERE, ORDER, LIMIT
  6.  test_joins               – join.rs: INNER, OUTER, CROSS joins
  7.  test_aggregates          – aggregator.rs: COUNT, SUM, AVG, MIN, MAX + GROUP BY/HAVING
  8.  test_optimizers          – optimizer.rs: filter-pushdown, index-lookup, hash-join
  9.  test_transactions        – session.rs: BEGIN, COMMIT, ROLLBACK, isolation
  10. test_median              – aggregator.rs: custom MEDIAN aggregate
  11. test_string_agg          – aggregator.rs: custom STRING_AGG aggregate
  12. test_integration         – local.rs: full end-to-end integration tests
"""

import subprocess
import os

APP_DIR = "/app"
LOGS_DIR = "/logs/verifier"


def _cargo_test(args, timeout=300):
    """Run cargo test and return (success: bool, output: str)."""
    cmd = ["cargo", "test", "--no-fail-fast"] + args
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=APP_DIR,
        timeout=timeout,
    )
    output = result.stdout + result.stderr
    return result.returncode == 0, output


# ---------------------------------------------------------------------------
# 1. Compilation
# ---------------------------------------------------------------------------

def test_compiles():
    """The SQL engine skeleton must compile after implementation (cargo check)."""
    result = subprocess.run(
        ["cargo", "check"],
        capture_output=True,
        text=True,
        cwd=APP_DIR,
        timeout=120,
    )
    assert result.returncode == 0, (
        f"cargo check failed — compilation errors in the implementation:\n"
        f"{result.stderr[-3000:]}"
    )


# ---------------------------------------------------------------------------
# 2. Lexer + Parser (expressions)
# ---------------------------------------------------------------------------

def test_expressions():
    """lexer.rs + parser.rs: SQL tokenisation and expression evaluation must be correct.

    Covers: literals, operators (arithmetic, comparison, logic, string LIKE),
    operator precedence, and expression functions (sqrt etc.).
    Maps to goldenscripts: src/sql/testscripts/expressions/
    """
    ok, output = _cargo_test(["--lib", "sql::tests::expressions", "--", "--test-threads=1"])
    assert ok, (
        f"Expression tests failed (lexer.rs / parser.rs):\n{output[-3000:]}"
    )


# ---------------------------------------------------------------------------
# 3. Schema (DDL)
# ---------------------------------------------------------------------------

def test_schema():
    """planner.rs + local.rs: CREATE TABLE and DROP TABLE must work correctly.

    Covers: basic DDL, data-type validation, primary keys, unique constraints,
    foreign-key references, indexes, default values, nullable columns, transactions.
    Maps to goldenscripts: src/sql/testscripts/schema/
    """
    ok, output = _cargo_test(["--lib", "sql::tests::schema", "--", "--test-threads=1"])
    assert ok, (
        f"Schema tests failed (planner.rs / local.rs):\n{output[-3000:]}"
    )


# ---------------------------------------------------------------------------
# 4. Write operations (DML)
# ---------------------------------------------------------------------------

def test_writes():
    """executor.rs: INSERT, UPDATE, and DELETE must work correctly.

    Covers: basic inserts, multi-row inserts, data-type handling, default values,
    primary-key enforcement, unique constraints, foreign-key checks, index updates,
    conditional deletes/updates, expression-based updates.
    Maps to goldenscripts: src/sql/testscripts/writes/
    """
    ok, output = _cargo_test(["--lib", "sql::tests::writes", "--", "--test-threads=1"])
    assert ok, (
        f"Write tests failed (executor.rs):\n{output[-3000:]}"
    )


# ---------------------------------------------------------------------------
# 5. Core SELECT queries (plan.rs + executor.rs)
# ---------------------------------------------------------------------------

def test_queries_core():
    """plan.rs + executor.rs: SELECT, WHERE, ORDER BY, LIMIT, OFFSET must work.

    Runs all query goldenscripts except join and aggregate tests, giving
    independent credit for the core query pipeline.
    Maps to goldenscripts: src/sql/testscripts/queries/ (core subset)
    """
    ok, output = _cargo_test([
        "--lib", "sql::tests::queries",
        "--",
        "--skip", "join",
        "--skip", "aggregate",
        "--skip", "group_by",
        "--skip", "having",
        "--test-threads=1",
    ])
    assert ok, (
        f"Core query tests failed (plan.rs / executor.rs):\n{output[-3000:]}"
    )


# ---------------------------------------------------------------------------
# 6. Join implementations (join.rs)
# ---------------------------------------------------------------------------

def test_joins():
    """join.rs: INNER JOIN, LEFT/RIGHT OUTER JOIN, and CROSS JOIN must be correct.

    Covers hash-join, nested-loop join, and cross-product execution.
    Maps to goldenscripts: sql::tests::queries::join_*
    """
    tests = [
        "sql::tests::queries::join_inner",
        "sql::tests::queries::join_outer",
        "sql::tests::queries::join_cross",
    ]
    failures = []
    for t in tests:
        ok, output = _cargo_test(["--lib", t, "--", "--test-threads=1"])
        if not ok:
            failures.append((t, output[-1500:]))

    assert not failures, (
        "Join tests failed (join.rs):\n"
        + "\n---\n".join(f"[{t}]\n{out}" for t, out in failures)
    )


# ---------------------------------------------------------------------------
# 7. Aggregate functions (aggregator.rs — standard)
# ---------------------------------------------------------------------------

def test_aggregates():
    """aggregator.rs: COUNT, SUM, AVG, MIN, MAX, GROUP BY, and HAVING must work.

    Covers standard SQL aggregates, null handling, empty-table behaviour,
    and grouped aggregation with HAVING filters.
    Maps to goldenscripts: sql::tests::queries::aggregate, group_by, having
    """
    tests = [
        "sql::tests::queries::aggregate",
        "sql::tests::queries::group_by",
        "sql::tests::queries::having",
    ]
    failures = []
    for t in tests:
        ok, output = _cargo_test([
            "--lib", t, "--", "--exact", "--test-threads=1",
        ])
        if not ok:
            failures.append((t, output[-1500:]))

    assert not failures, (
        "Aggregate tests failed (aggregator.rs):\n"
        + "\n---\n".join(f"[{t}]\n{out}" for t, out in failures)
    )


# ---------------------------------------------------------------------------
# 8. Query optimizer (optimizer.rs)
# ---------------------------------------------------------------------------

def test_optimizers():
    """optimizer.rs: filter-pushdown, index-lookup, constant folding, hash-join optimizations.

    The optimizer must transform query plans correctly while preserving
    exact output parity with the unoptimized baseline.
    Maps to goldenscripts: src/sql/testscripts/optimizers/
    """
    ok, output = _cargo_test(["--lib", "sql::tests::optimizers", "--", "--test-threads=1"])
    assert ok, (
        f"Optimizer tests failed (optimizer.rs):\n{output[-3000:]}"
    )


# ---------------------------------------------------------------------------
# 9. Transaction management (session.rs)
# ---------------------------------------------------------------------------

def test_transactions():
    """session.rs: BEGIN, COMMIT, ROLLBACK and MVCC isolation must be correct.

    Covers snapshot isolation, anomaly prevention (dirty read, fuzzy read,
    phantom read, write skew, lost update), and schema-change transactions.
    Maps to goldenscripts: src/sql/testscripts/transactions/
    """
    ok, output = _cargo_test(["--lib", "sql::tests::transactions", "--", "--test-threads=1"])
    assert ok, (
        f"Transaction tests failed (session.rs):\n{output[-3000:]}"
    )


# ---------------------------------------------------------------------------
# 10. Custom aggregate: MEDIAN (aggregator.rs)
# ---------------------------------------------------------------------------

def test_median():
    """aggregator.rs: MEDIAN(expr) must compute the statistical median correctly.

    MEDIAN is a custom aggregate not in the original toydb. It must:
    - Return the middle value for odd-count datasets.
    - Return the average of the two middle values for even-count datasets.
    - Exclude NULL values from the computation.
    - Return NULL for empty input.
    Maps to goldenscript: sql::tests::queries::aggregate_median
    """
    ok, output = _cargo_test([
        "--lib", "sql::tests::queries::aggregate_median",
        "--", "--exact", "--test-threads=1",
    ])
    assert ok, (
        f"MEDIAN aggregate test failed (aggregator.rs):\n{output[-3000:]}"
    )


# ---------------------------------------------------------------------------
# 11. Custom aggregate: STRING_AGG (aggregator.rs)
# ---------------------------------------------------------------------------

def test_string_agg():
    """aggregator.rs: STRING_AGG(expr, delimiter) must concatenate strings correctly.

    STRING_AGG is a custom aggregate not in the original toydb. It must:
    - Join non-NULL string values with the given delimiter.
    - Exclude NULL values from the output.
    - Return NULL for empty input.
    Maps to goldenscript: sql::tests::queries::aggregate_string_agg
    """
    ok, output = _cargo_test([
        "--lib", "sql::tests::queries::aggregate_string_agg",
        "--", "--exact", "--test-threads=1",
    ])
    assert ok, (
        f"STRING_AGG aggregate test failed (aggregator.rs):\n{output[-3000:]}"
    )


# ---------------------------------------------------------------------------
# 12. End-to-end integration (local.rs)
# ---------------------------------------------------------------------------

def test_integration():
    """local.rs: full end-to-end integration tests using a real storage engine.

    Runs the integration test suite (tests/tests.rs) which exercises the
    complete SQL-to-storage stack including Raft consensus simulation.
    Maps to: cargo test --test tests
    """
    ok, output = _cargo_test([
        "--test", "tests",
        "--", "--test-threads=1",
    ], timeout=360)
    assert ok, (
        f"Integration tests failed (local.rs):\n{output[-3000:]}"
    )
