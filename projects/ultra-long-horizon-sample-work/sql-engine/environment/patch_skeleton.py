#!/usr/bin/env python3
"""
patch_skeleton.py - Patches the toydb source at SKELETON_COMMIT to add MEDIAN
and STRING_AGG enum variants (without implementations, which are todo!() stubs).

This gives the agent the type scaffolding it must implement.
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
    # 1. Patch plan.rs — add Median and StringAgg to the Aggregate enum only.
    #    The skeleton already has todo!() in the method bodies, so we only
    #    need to add the new variants so the code compiles and the agent sees
    #    them as required tasks to handle.
    # =========================================================================
    plan_path = os.path.join(WORKDIR, "src/sql/planner/plan.rs")
    print(f"\n[plan.rs] Reading {plan_path}")
    plan = read_file(plan_path)

    # Add variants to the Aggregate enum.
    plan, ok = patch(
        "Aggregate enum - add Median/StringAgg variants",
        plan,
        "    Sum(Expression),\n}",
        "    Sum(Expression),\n    Median(Expression),\n    StringAgg(Expression, Expression),\n}",
    )
    if not ok:
        errors.append("plan.rs: Aggregate enum variants")

    write_file(plan_path, plan)
    print(f"[plan.rs] Written.")

    # =========================================================================
    # 2. Patch aggregator.rs — add Median and StringAgg to the Accumulator
    #    enum only. The skeleton's method bodies are already todo!() stubs.
    # =========================================================================
    agg_path = os.path.join(WORKDIR, "src/sql/execution/aggregator.rs")
    print(f"\n[aggregator.rs] Reading {agg_path}")
    agg = read_file(agg_path)

    # Add variants to the Accumulator enum.
    agg, ok = patch(
        "Accumulator enum - add Median/StringAgg variants",
        agg,
        "    Sum(Option<Value>),\n}",
        "    Sum(Option<Value>),\n    Median(Vec<Value>),\n    StringAgg { values: Vec<String>, delimiter: String },\n}",
    )
    if not ok:
        errors.append("aggregator.rs: Accumulator enum variants")

    write_file(agg_path, agg)
    print(f"[aggregator.rs] Written.")

    # Note: planner.rs is_aggregate_function is already todo!() in the skeleton,
    # so no patch needed — the agent implements it from scratch.

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
        print("All skeleton patches applied successfully.")
    print("=" * 60)

if __name__ == "__main__":
    main()