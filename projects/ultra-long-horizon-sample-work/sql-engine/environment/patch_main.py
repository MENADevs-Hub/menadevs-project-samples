#!/usr/bin/env python3
"""
patch_main.py - Patches the toydb source at MAIN_COMMIT to add MEDIAN and STRING_AGG
aggregate functions. Run after the full implementation builds and tests pass.
"""

import sys
import os

WORKDIR = "/app"

def read_file(path):
    with open(path, "r") as f:
        return f.read()

def write_file(path, content):
    with open(path, "w") as f:
        f.write(content)

def patch(label, content, old, new):
    if old not in content:
        print(f"  ERROR: pattern not found for '{label}'")
        print(f"  Expected to find:\n---\n{old}\n---")
        return content, False
    result = content.replace(old, new, 1)
    print(f"  OK: patched '{label}'")
    return result, True

def main():
    errors = []

    # =========================================================================
    # 1. Patch plan.rs — add Median and StringAgg to the Aggregate enum and
    #    to the format() and expr() methods.
    # =========================================================================
    plan_path = os.path.join(WORKDIR, "src/sql/planner/plan.rs")
    print(f"\n[plan.rs] Reading {plan_path}")
    plan = read_file(plan_path)

    # 1a. Add variants to the Aggregate enum.
    plan, ok = patch(
        "Aggregate enum - add Median/StringAgg variants",
        plan,
        "    Sum(Expression),\n}",
        "    Sum(Expression),\n    Median(Expression),\n    StringAgg(Expression, Expression),\n}",
    )
    if not ok:
        errors.append("plan.rs: Aggregate enum variants")

    # 1b. Add arms to Aggregate::format().
    old_fmt_12 = '            Self::Sum(expr) => format!("sum({})", expr.display(node)),'
    new_fmt_12 = (
        '            Self::Sum(expr) => format!("sum({})", expr.display(node)),\n'
        '            Self::Median(expr) => format!("median({})", expr.display(node)),\n'
        '            Self::StringAgg(expr, delim) => format!("string_agg({}, {})", expr.display(node), delim.display(node)),'
    )
    old_fmt_8 = '        Self::Sum(expr) => format!("sum({})", expr.display(node)),'
    new_fmt_8 = (
        '        Self::Sum(expr) => format!("sum({})", expr.display(node)),\n'
        '        Self::Median(expr) => format!("median({})", expr.display(node)),\n'
        '        Self::StringAgg(expr, delim) => format!("string_agg({}, {})", expr.display(node), delim.display(node)),'
    )

    if old_fmt_12 in plan:
        plan, ok = patch("Aggregate::format() - 12-space indent variant", plan, old_fmt_12, new_fmt_12)
    elif old_fmt_8 in plan:
        plan, ok = patch("Aggregate::format() - 8-space indent variant", plan, old_fmt_8, new_fmt_8)
    else:
        print("  ERROR: pattern not found for 'Aggregate::format() arms' (tried 12-space and 8-space variants)")
        ok = False
    if not ok:
        errors.append("plan.rs: format() arms")

    # 1c. Add arms to Aggregate::expr() — returns the first/primary expression.
    #     StringAgg needs special handling in Aggregator::add(), so expr() returns
    #     the value expression (first arg); the delimiter is handled via Accumulator::new().
    #     Try multiple indentation levels.
    old_expr_12 = "            | Self::Sum(expr) => expr,"
    new_expr_12 = "            | Self::Sum(expr)\n            | Self::Median(expr)\n            | Self::StringAgg(expr, _) => expr,"
    old_expr_8  = "        | Self::Sum(expr) => expr,"
    new_expr_8  = "        | Self::Sum(expr)\n        | Self::Median(expr)\n        | Self::StringAgg(expr, _) => expr,"

    if old_expr_12 in plan:
        plan, ok = patch("Aggregate::expr() - 12-space indent variant", plan, old_expr_12, new_expr_12)
    elif old_expr_8 in plan:
        plan, ok = patch("Aggregate::expr() - 8-space indent variant", plan, old_expr_8, new_expr_8)
    else:
        print("  ERROR: pattern not found for 'Aggregate::expr() arms' (tried 12-space and 8-space variants)")
        ok = False
    if not ok:
        errors.append("plan.rs: expr() arms")

    write_file(plan_path, plan)
    print(f"[plan.rs] Written.")

    # =========================================================================
    # 2. Patch aggregator.rs — add Median and StringAgg to the Accumulator enum
    #    and to new(), add(), and value() methods.
    # =========================================================================
    agg_path = os.path.join(WORKDIR, "src/sql/execution/aggregator.rs")
    print(f"\n[aggregator.rs] Reading {agg_path}")
    agg = read_file(agg_path)

    # 2a. Add variants to the Accumulator enum.
    agg, ok = patch(
        "Accumulator enum - add Median/StringAgg variants",
        agg,
        "    Sum(Option<Value>),\n}",
        "    Sum(Option<Value>),\n    Median(Vec<Value>),\n    StringAgg { values: Vec<String>, delimiter: String },\n}",
    )
    if not ok:
        errors.append("aggregator.rs: Accumulator enum variants")

    # 2b. Add arms to Accumulator::new().
    #     Arms at 12 spaces, closing `        }\n    }` at 8+4 spaces.
    old_new_12 = (
        "            Aggregate::Sum(_) => Self::Sum(None),\n"
        "        }\n"
        "    }"
    )
    new_new_12 = (
        "            Aggregate::Sum(_) => Self::Sum(None),\n"
        "            Aggregate::Median(_) => Self::Median(Vec::new()),\n"
        "            Aggregate::StringAgg(_, delimiter_expr) => {\n"
        "                let delimiter = delimiter_expr\n"
        "                    .evaluate(None)\n"
        "                    .ok()\n"
        "                    .and_then(|v| if let Value::String(s) = v { Some(s) } else { None })\n"
        "                    .unwrap_or_default();\n"
        "                Self::StringAgg { values: Vec::new(), delimiter }\n"
        "            }\n"
        "        }\n"
        "    }"
    )
    # 8-space fallback: arms at 8 spaces, match close at 4 spaces, fn close at 4 spaces.
    # Note: "    }\n    }" is two closing braces which is somewhat ambiguous but
    # anchored by the specific Aggregate::Sum arm above it.
    old_new_8 = (
        "        Aggregate::Sum(_) => Self::Sum(None),\n"
        "    }\n"
        "    }"
    )
    new_new_8 = (
        "        Aggregate::Sum(_) => Self::Sum(None),\n"
        "        Aggregate::Median(_) => Self::Median(Vec::new()),\n"
        "        Aggregate::StringAgg(_, delimiter_expr) => {\n"
        "            let delimiter = delimiter_expr\n"
        "                .evaluate(None)\n"
        "                .ok()\n"
        "                .and_then(|v| if let Value::String(s) = v { Some(s) } else { None })\n"
        "                .unwrap_or_default();\n"
        "            Self::StringAgg { values: Vec::new(), delimiter }\n"
        "        }\n"
        "    }\n"
        "    }"
    )

    if old_new_12 in agg:
        agg, ok = patch("Accumulator::new() - 12-space indent variant", agg, old_new_12, new_new_12)
    elif old_new_8 in agg:
        agg, ok = patch("Accumulator::new() - 8-space indent variant", agg, old_new_8, new_new_8)
    else:
        print("  ERROR: pattern not found for 'Accumulator::new() arms' (tried 12-space and 8-space variants)")
        ok = False
    if not ok:
        errors.append("aggregator.rs: new() arms")

    # 2c. Add arms to Accumulator::add().
    #     The existing add() has an early return for Null at the top, then a match.
    #     The last existing arm is Self::Sum(Some(sum)) => *sum = sum.checked_add(&value)?,
    #     followed by `        }` (closing match) and `        Ok(())` and `    }` (closing fn).
    old_add_12 = (
        "            Self::Sum(Some(sum)) => *sum = sum.checked_add(&value)?,\n"
        "        }\n"
        "        Ok(())\n"
        "    }"
    )
    new_add_12 = (
        "            Self::Sum(Some(sum)) => *sum = sum.checked_add(&value)?,\n"
        "            Self::Median(values) => {\n"
        "                // Null already filtered at top of add().\n"
        "                values.push(value);\n"
        "            }\n"
        "            Self::StringAgg { values, .. } => {\n"
        "                if let Value::String(s) = value {\n"
        "                    values.push(s);\n"
        "                }\n"
        "            }\n"
        "        }\n"
        "        Ok(())\n"
        "    }"
    )
    old_add_8 = (
        "        Self::Sum(Some(sum)) => *sum = sum.checked_add(&value)?,\n"
        "    }\n"
        "    Ok(())\n"
        "}"
    )
    new_add_8 = (
        "        Self::Sum(Some(sum)) => *sum = sum.checked_add(&value)?,\n"
        "        Self::Median(values) => {\n"
        "            // Null already filtered at top of add().\n"
        "            values.push(value);\n"
        "        }\n"
        "        Self::StringAgg { values, .. } => {\n"
        "            if let Value::String(s) = value {\n"
        "                values.push(s);\n"
        "            }\n"
        "        }\n"
        "    }\n"
        "    Ok(())\n"
        "}"
    )

    if old_add_12 in agg:
        agg, ok = patch("Accumulator::add() - 12-space indent variant", agg, old_add_12, new_add_12)
    elif old_add_8 in agg:
        agg, ok = patch("Accumulator::add() - 8-space indent variant", agg, old_add_8, new_add_8)
    else:
        print("  ERROR: pattern not found for 'Accumulator::add() arms' (tried 12-space and 8-space variants)")
        ok = False
    if not ok:
        errors.append("aggregator.rs: add() arms")

    # 2d. Add arms to Accumulator::value().
    #     The method returns Result<Value> and has the form:
    #       fn value(self) -> Result<Value> {
    #           Ok(match self {
    #               ...
    #               Self::Max(None) | Self::Min(None) | Self::Sum(None) => Value::Null,
    #           })
    #       }
    #     Arms are indented 12 spaces, closing `    })` is 8 spaces.
    #     We try the 12-space arm + 8-space closing first, then fall back to
    #     searching with less rigid indentation.
    old_value_12 = (
        "            Self::Max(None) | Self::Min(None) | Self::Sum(None) => Value::Null,\n"
        "        })"
    )
    new_value_12 = (
        "            Self::Max(None) | Self::Min(None) | Self::Sum(None) => Value::Null,\n"
        "            Self::Median(mut values) => {\n"
        "                let mut nums: Vec<f64> = values\n"
        "                    .drain(..)\n"
        "                    .filter_map(|v| match v {\n"
        "                        Value::Integer(i) => Some(i as f64),\n"
        "                        Value::Float(f) => Some(f),\n"
        "                        _ => None,\n"
        "                    })\n"
        "                    .collect();\n"
        "                if nums.is_empty() {\n"
        "                    Value::Null\n"
        "                } else {\n"
        "                    nums.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));\n"
        "                    let n = nums.len();\n"
        "                    Value::Float(if n % 2 == 1 {\n"
        "                        nums[n / 2]\n"
        "                    } else {\n"
        "                        (nums[n / 2 - 1] + nums[n / 2]) / 2.0\n"
        "                    })\n"
        "                }\n"
        "            }\n"
        "            Self::StringAgg { values, delimiter } => {\n"
        "                if values.is_empty() {\n"
        "                    Value::Null\n"
        "                } else {\n"
        "                    Value::String(values.join(&delimiter))\n"
        "                }\n"
        "            }\n"
        "        })"
    )
    # Also try 8-space arm + 4-space closing (some codebases use different indent).
    old_value_8 = (
        "        Self::Max(None) | Self::Min(None) | Self::Sum(None) => Value::Null,\n"
        "    })"
    )
    new_value_8 = (
        "        Self::Max(None) | Self::Min(None) | Self::Sum(None) => Value::Null,\n"
        "        Self::Median(mut values) => {\n"
        "            let mut nums: Vec<f64> = values\n"
        "                .drain(..)\n"
        "                .filter_map(|v| match v {\n"
        "                    Value::Integer(i) => Some(i as f64),\n"
        "                    Value::Float(f) => Some(f),\n"
        "                    _ => None,\n"
        "                })\n"
        "                .collect();\n"
        "            if nums.is_empty() {\n"
        "                Value::Null\n"
        "            } else {\n"
        "                nums.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));\n"
        "                let n = nums.len();\n"
        "                Value::Float(if n % 2 == 1 {\n"
        "                    nums[n / 2]\n"
        "                } else {\n"
        "                    (nums[n / 2 - 1] + nums[n / 2]) / 2.0\n"
        "                })\n"
        "            }\n"
        "        }\n"
        "        Self::StringAgg { values, delimiter } => {\n"
        "            if values.is_empty() {\n"
        "                Value::Null\n"
        "            } else {\n"
        "                Value::String(values.join(&delimiter))\n"
        "            }\n"
        "        }\n"
        "    })"
    )

    if old_value_12 in agg:
        agg, ok = patch("Accumulator::value() - 12-space indent variant", agg, old_value_12, new_value_12)
    elif old_value_8 in agg:
        agg, ok = patch("Accumulator::value() - 8-space indent variant", agg, old_value_8, new_value_8)
    else:
        print("  ERROR: pattern not found for 'Accumulator::value() arms' (tried 12-space and 8-space variants)")
        ok = False
    if not ok:
        errors.append("aggregator.rs: value() arms")

    write_file(agg_path, agg)
    print(f"[aggregator.rs] Written.")

    # =========================================================================
    # 3. Patch planner.rs — add "median" and "string_agg" to the aggregate
    #    function name mapping in build_aggregate_function().
    #
    #    The current code enforces args.len() != 1 before the match, so we need
    #    to handle string_agg (2 args) before that check.
    # =========================================================================
    planner_path = os.path.join(WORKDIR, "src/sql/planner/planner.rs")
    print(f"\n[planner.rs] Reading {planner_path}")
    planner = read_file(planner_path)

    # The existing build_aggregate_function:
    #
    # fn build_aggregate_function(expr: ast::Expression, scope: &Scope) -> Result<Aggregate> {
    #     let ast::Expression::Function(name, mut args) = expr else {
    #         panic!("aggregate expression must be function");
    #     };
    #     if args.len() != 1 {
    #         return errinput!("{name} takes 1 argument");
    #     }
    #     if args[0].contains(&|expr| Self::is_aggregate_function(expr)) {
    #         return errinput!("aggregate functions can't be nested");
    #     }
    #     // Special-case COUNT(*) since expressions don't support tuples.
    #     let expr = match (name.as_str(), args.remove(0)) {
    #         ("count", ast::Expression::All) => Expression::Constant(Value::Boolean(true)),
    #         (_, arg) => Self::build_expression(arg, scope)?,
    #     };
    #     Ok(match name.as_str() {
    #         "avg" => Aggregate::Average(expr),
    #         "count" => Aggregate::Count(expr),
    #         "min" => Aggregate::Min(expr),
    #         "max" => Aggregate::Max(expr),
    #         "sum" => Aggregate::Sum(expr),
    #         name => return errinput!("unknown aggregate function {name}"),
    #     })
    # }
    #
    # Strategy: replace the entire function body so we can add the string_agg
    # early-exit before the args.len() != 1 check.

    old_fn = (
        '    fn build_aggregate_function(expr: ast::Expression, scope: &Scope) -> Result<Aggregate> {\n'
        '        let ast::Expression::Function(name, mut args) = expr else {\n'
        '            panic!("aggregate expression must be function");\n'
        '        };\n'
        '        if args.len() != 1 {\n'
        '            return errinput!("{name} takes 1 argument");\n'
        '        }\n'
        '        if args[0].contains(&|expr| Self::is_aggregate_function(expr)) {\n'
        '            return errinput!("aggregate functions can\'t be nested");\n'
        '        }\n'
        '        // Special-case COUNT(*) since expressions don\'t support tuples.\n'
        '        let expr = match (name.as_str(), args.remove(0)) {\n'
        '            ("count", ast::Expression::All) => Expression::Constant(Value::Boolean(true)),\n'
        '            (_, arg) => Self::build_expression(arg, scope)?,\n'
        '        };\n'
        '        Ok(match name.as_str() {\n'
        '            "avg" => Aggregate::Average(expr),\n'
        '            "count" => Aggregate::Count(expr),\n'
        '            "min" => Aggregate::Min(expr),\n'
        '            "max" => Aggregate::Max(expr),\n'
        '            "sum" => Aggregate::Sum(expr),\n'
        '            name => return errinput!("unknown aggregate function {name}"),\n'
        '        })\n'
        '    }'
    )

    new_fn = (
        '    fn build_aggregate_function(expr: ast::Expression, scope: &Scope) -> Result<Aggregate> {\n'
        '        let ast::Expression::Function(name, mut args) = expr else {\n'
        '            panic!("aggregate expression must be function");\n'
        '        };\n'
        '        // Handle string_agg early: it takes exactly 2 arguments.\n'
        '        if name.as_str() == "string_agg" {\n'
        '            if args.len() != 2 {\n'
        '                return errinput!("string_agg takes 2 arguments");\n'
        '            }\n'
        '            if args[0].contains(&|expr| Self::is_aggregate_function(expr)) {\n'
        '                return errinput!("aggregate functions can\'t be nested");\n'
        '            }\n'
        '            let val_expr = Self::build_expression(args.remove(0), scope)?;\n'
        '            let delim_expr = Self::build_expression(args.remove(0), scope)?;\n'
        '            return Ok(Aggregate::StringAgg(val_expr, delim_expr));\n'
        '        }\n'
        '        if args.len() != 1 {\n'
        '            return errinput!("{name} takes 1 argument");\n'
        '        }\n'
        '        if args[0].contains(&|expr| Self::is_aggregate_function(expr)) {\n'
        '            return errinput!("aggregate functions can\'t be nested");\n'
        '        }\n'
        '        // Special-case COUNT(*) since expressions don\'t support tuples.\n'
        '        let expr = match (name.as_str(), args.remove(0)) {\n'
        '            ("count", ast::Expression::All) => Expression::Constant(Value::Boolean(true)),\n'
        '            (_, arg) => Self::build_expression(arg, scope)?,\n'
        '        };\n'
        '        Ok(match name.as_str() {\n'
        '            "avg" => Aggregate::Average(expr),\n'
        '            "count" => Aggregate::Count(expr),\n'
        '            "min" => Aggregate::Min(expr),\n'
        '            "max" => Aggregate::Max(expr),\n'
        '            "sum" => Aggregate::Sum(expr),\n'
        '            "median" => Aggregate::Median(expr),\n'
        '            name => return errinput!("unknown aggregate function {name}"),\n'
        '        })\n'
        '    }'
    )

    planner, ok = patch("planner.rs: build_aggregate_function", planner, old_fn, new_fn)
    if not ok:
        errors.append("planner.rs: build_aggregate_function")

    # 3b. Patch is_aggregate_function() to recognise "median" and "string_agg".
    #     Without this the planner treats them as scalar functions and never calls
    #     build_aggregate_function(), so we get "unknown function median" at runtime.
    old_is_agg = '["avg", "count", "max", "min", "sum"].contains(&name.as_str())'
    new_is_agg = '["avg", "count", "max", "min", "sum", "median", "string_agg"].contains(&name.as_str())'
    planner, ok = patch("planner.rs: is_aggregate_function", planner, old_is_agg, new_is_agg)
    if not ok:
        errors.append("planner.rs: is_aggregate_function")

    write_file(planner_path, planner)
    print(f"[planner.rs] Written.")

    # =========================================================================
    # 4. Patch aggregator.rs Aggregator::add() to handle StringAgg's delimiter
    #    expression. The Aggregator::add() method uses a.expr() to get the
    #    expression to evaluate. For StringAgg we need the first (value) expr,
    #    which expr() already returns (we patched plan.rs to do this).
    #    No additional change needed here.
    # =========================================================================

    # =========================================================================
    # 5. Create goldenscript test files.
    # =========================================================================
    testscripts_dir = os.path.join(WORKDIR, "src/sql/testscripts/queries")
    os.makedirs(testscripts_dir, exist_ok=True)

    median_test = """\
# MEDIAN aggregate function.

# Setup.
> CREATE TABLE t (id INTEGER PRIMARY KEY, v FLOAT)
> INSERT INTO t VALUES (1, 1.0), (2, 2.0), (3, 3.0), (4, 4.0), (5, 5.0)
---
ok

# Odd count: median is the middle value.
> SELECT MEDIAN(v) FROM t
---
3.0

# Even count: median is average of two middle values.
> INSERT INTO t VALUES (6, 6.0)
---
ok

> SELECT MEDIAN(v) FROM t
---
3.5

# NULLs are excluded from the computation.
> CREATE TABLE tnull (id INTEGER PRIMARY KEY, v FLOAT)
> INSERT INTO tnull VALUES (1, 2.0), (2, NULL), (3, 4.0)
---
ok

> SELECT MEDIAN(v) FROM tnull
---
3.0

# Empty table returns NULL.
> CREATE TABLE tempty (id INTEGER PRIMARY KEY, v FLOAT)
---
ok

> SELECT MEDIAN(v) FROM tempty
---
NULL
"""

    string_agg_test = """\
# STRING_AGG aggregate function.

# Setup.
> CREATE TABLE t (id INTEGER PRIMARY KEY, s STRING)
> INSERT INTO t VALUES (1, 'hello'), (2, 'world'), (3, 'foo')
---
ok

> SELECT STRING_AGG(s, ', ') FROM t
---
'hello, world, foo'

# NULLs are excluded.
> CREATE TABLE t2 (id INTEGER PRIMARY KEY, s STRING)
> INSERT INTO t2 VALUES (1, 'a'), (2, NULL), (3, 'b')
---
ok

> SELECT STRING_AGG(s, '-') FROM t2
---
'a-b'

# Empty table returns NULL.
> CREATE TABLE tempty (id INTEGER PRIMARY KEY, s STRING)
---
ok

> SELECT STRING_AGG(s, ',') FROM tempty
---
NULL
"""

    median_path = os.path.join(testscripts_dir, "aggregate_median")
    string_agg_path = os.path.join(testscripts_dir, "aggregate_string_agg")

    write_file(median_path, median_test)
    print(f"\n[testscripts] Written {median_path}")

    write_file(string_agg_path, string_agg_test)
    print(f"[testscripts] Written {string_agg_path}")

    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "=" * 60)
    if errors:
        print(f"FAILED: {len(errors)} patch(es) did not apply:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("All patches applied successfully.")
    print("=" * 60)

if __name__ == "__main__":
    main()