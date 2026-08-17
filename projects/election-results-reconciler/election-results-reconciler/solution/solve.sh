#!/bin/bash
set -e

python3 << 'EOF'
import csv
import difflib
import json

OFFICIAL_PATH = "/root/official_results.csv"
TALLY_PATH = "/root/tally_sheets.json"
REPORT_PATH = "/root/audit_report.json"


def parse_votes(v):
    """Parse vote count from int, float, or formatted string like '1,249'."""
    if isinstance(v, (int, float)):
        return int(v)
    return int(str(v).strip().replace(",", "").replace(" ", ""))


def match_precinct(name, official_names):
    """Fuzzy-match a tally precinct name to the closest official name."""
    matches = difflib.get_close_matches(name, official_names, n=1, cutoff=0.75)
    return matches[0] if matches else None


def classify_severity(d_type, diff):
    if d_type in ("impossible_value", "candidate_missing", "precinct_missing"):
        return "high"
    if diff <= 10:
        return "low"
    if diff <= 100:
        return "medium"
    return "high"


# --- Load official results ---
official = {}
with open(OFFICIAL_PATH, newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        p = row["precinct_name"]
        c = row["candidate"]
        if p not in official:
            official[p] = {}
        official[p][c] = {
            "votes": int(row["votes"]),
            "registered_voters": int(row["registered_voters"]),
            "party": row["party"],
        }

# --- Load tally sheets and fuzzy-match precinct names ---
with open(TALLY_PATH, encoding="utf-8") as f:
    tally_data = json.load(f)

official_names = list(official.keys())
tally = {}

for sheet in tally_data["sheets"]:
    raw_name = sheet["precinct"]
    matched = match_precinct(raw_name, official_names)
    if not matched:
        continue
    tally[matched] = {r["candidate"]: parse_votes(r["votes"]) for r in sheet["results"]}

# --- Compare and collect discrepancies ---
discrepancies = []
matched_precincts = set(tally.keys())

for precinct, candidates in official.items():
    registered = list(candidates.values())[0]["registered_voters"]

    if precinct not in matched_precincts:
        discrepancies.append({
            "precinct": precinct,
            "candidate": None,
            "discrepancy_type": "precinct_missing",
            "official_votes": None,
            "tally_votes": None,
            "difference": None,
            "registered_voters": registered,
            "severity": "high",
            "note": f"precinct '{precinct}' not found in tally sheets",
        })
        continue

    for candidate, data in candidates.items():
        official_votes = data["votes"]

        if candidate not in tally[precinct]:
            discrepancies.append({
                "precinct": precinct,
                "candidate": candidate,
                "discrepancy_type": "candidate_missing",
                "official_votes": official_votes,
                "tally_votes": None,
                "difference": None,
                "registered_voters": registered,
                "severity": "high",
                "note": f"candidate '{candidate}' missing from tally sheet for '{precinct}'",
            })
            continue

        tally_votes = tally[precinct][candidate]
        if tally_votes == official_votes:
            continue

        diff = abs(tally_votes - official_votes)
        if tally_votes > registered:
            d_type = "impossible_value"
            note = f"tally votes ({tally_votes}) exceed registered voters ({registered})"
        else:
            d_type = "vote_count_mismatch"
            note = None

        entry = {
            "precinct": precinct,
            "candidate": candidate,
            "discrepancy_type": d_type,
            "official_votes": official_votes,
            "tally_votes": tally_votes,
            "difference": diff,
            "registered_voters": registered,
            "severity": classify_severity(d_type, diff),
        }
        if note:
            entry["note"] = note
        discrepancies.append(entry)

# Sort: high → medium → low, then alphabetically by precinct
sev_order = {"high": 0, "medium": 1, "low": 2}
discrepancies.sort(key=lambda d: (sev_order[d["severity"]], d["precinct"] or ""))

# --- Build summary ---
sev_counts = {"low": 0, "medium": 0, "high": 0}
type_counts = {"vote_count_mismatch": 0, "impossible_value": 0, "candidate_missing": 0, "precinct_missing": 0}
for d in discrepancies:
    sev_counts[d["severity"]] += 1
    type_counts[d["discrepancy_type"]] += 1

precincts_with_issues = {d["precinct"] for d in discrepancies if d["precinct"]}

report = {
    "summary": {
        "total_precincts_official": len(official),
        "total_precincts_tally": len(tally_data["sheets"]),
        "precincts_matched": len(matched_precincts),
        "precincts_with_discrepancies": len(precincts_with_issues),
        "total_discrepancies": len(discrepancies),
        "discrepancies_by_severity": sev_counts,
        "discrepancies_by_type": type_counts,
    },
    "discrepancies": discrepancies,
}

with open(REPORT_PATH, "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2)

print(f"Done: {len(discrepancies)} discrepancies → {REPORT_PATH}")
EOF
