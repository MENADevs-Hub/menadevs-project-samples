"""Compute partial reward from pytest-json-ctrf output."""
import json
import os
import sys

CTRF_PATH = "/logs/verifier/ctrf.json"
REWARD_PATH = "/logs/verifier/reward.txt"


def main():
    try:
        with open(CTRF_PATH) as f:
            ctrf = json.load(f)

        summary = ctrf.get("results", {}).get("summary", {})
        passed = summary.get("passed", 0)
        failed = summary.get("failed", 0)
        total = passed + failed

        reward = round(passed / total, 4) if total > 0 else 0.0

    except Exception as e:
        print(f"Error reading ctrf.json: {e}", file=sys.stderr)
        reward = 0.0
        passed = 0
        total = 0

    with open(REWARD_PATH, "w") as f:
        f.write(str(reward))

    print(f"Reward: {reward} ({passed}/{total} test categories passed)")


if __name__ == "__main__":
    main()
