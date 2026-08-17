#!/usr/bin/env python3
"""Compute proportional score from ctrf.json and write to reward.txt."""
import json, sys

ctrf_path = sys.argv[1]
reward_path = sys.argv[2]

try:
    with open(ctrf_path) as f:
        d = json.load(f)
    tests = d["results"]["tests"]
    passed = sum(1 for t in tests if t["status"] == "passed")
    total = len(tests)
    score = round(passed / total, 4) if total > 0 else 0.0
except Exception:
    score = 0.0

with open(reward_path, "w") as f:
    f.write(str(score) + "\n")

print(f"Score: {score} ({passed if 'passed' in dir() else 0}/{total if 'total' in dir() else 0})")
