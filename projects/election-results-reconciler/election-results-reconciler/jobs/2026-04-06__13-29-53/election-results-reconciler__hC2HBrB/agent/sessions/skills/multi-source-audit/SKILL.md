---
name: multi-source-audit
description: Pattern for comparing two structured datasets that should agree, finding every discrepancy, classifying it by type and severity, and producing a standard audit report. Use when auditing election tallies, financial statements, inventory counts, or any pair of records where mismatches need to be categorised and ranked.
---

# Multi-Source Audit Pattern

## Core workflow

```
Load official CSV  →  Load tally JSON  →  Align precincts (fuzzy-match names)  →  Compare candidates  →  Classify  →  Summarise  →  Write report
```

## Discrepancy types for election audits

| Type | When to use | Granularity |
|------|-------------|-------------|
| `vote_count_mismatch` | Precinct matched, candidate found in both, but vote counts differ | One entry **per precinct+candidate pair** |
| `impossible_value` | Tally votes exceed registered_voters for that precinct | One entry **per precinct+candidate pair** |
| `candidate_missing` | Precinct matched in tally, but a specific candidate row is absent | One entry **per missing candidate** |
| `precinct_missing` | Entire precinct is absent from tally sheets (no match found even after fuzzy matching) | One entry **per missing precinct** — NOT one per candidate |

> **Critical granularity rule**: A missing precinct is ONE discrepancy, regardless of how many candidates it has. Do NOT emit separate entries for each candidate of a missing precinct. Use `candidate: null` for `precinct_missing` entries.

## Severity tiers

```python
def classify_severity(d_type, diff=None):
    if d_type in ("impossible_value", "precinct_missing", "candidate_missing"):
        return "high"
    # vote_count_mismatch: grade by difference
    if diff <= 10:
        return "low"
    if diff <= 100:
        return "medium"
    return "high"
```

## Report structure

Output `/root/audit_report.json`:

```json
{
  "summary": {
    "total_precincts_official": 8,
    "total_precincts_tally": 7,
    "precincts_matched": 7,
    "precincts_with_discrepancies": 6,
    "total_discrepancies": 6,
    "discrepancies_by_severity": {"low": 1, "medium": 1, "high": 4},
    "discrepancies_by_type": {
      "vote_count_mismatch": 3,
      "impossible_value": 1,
      "candidate_missing": 1,
      "precinct_missing": 1
    }
  },
  "discrepancies": [
    {
      "precinct": "North Ward",
      "candidate": "Maria Chen",
      "discrepancy_type": "vote_count_mismatch",
      "official_votes": 1247,
      "tally_votes": 1249,
      "difference": 2,
      "severity": "low"
    },
    {
      "precinct": "Harbor Area",
      "candidate": null,
      "discrepancy_type": "precinct_missing",
      "official_votes": null,
      "tally_votes": null,
      "difference": null,
      "severity": "high"
    }
  ]
}
```

**Field names matter** — tests look for `precinct`, `candidate`, `discrepancy_type`, `official_votes`, `tally_votes`, `difference`, `severity` in each item.

## Key implementation notes

**Parse values defensively** — source B often has formatting noise (commas in numbers, leading zeros, string instead of int):

```python
def parse_int(v):
    if isinstance(v, (int, float)):
        return int(v)
    return int(str(v).strip().replace(",", ""))
```

**Check impossible values before mismatch** — test domain constraints first:

```python
if value_b > max_allowed:
    d_type = "impossible_value"
elif value_b != value_a:
    d_type = "vote_count_mismatch"
```

**Sort the output** — put high severity first, then alphabetical by precinct so reviewers see the worst issues immediately:

```python
sev_order = {"high": 0, "medium": 1, "low": 2}
discrepancies.sort(key=lambda d: (sev_order[d["severity"]], d["precinct"] or ""))
```

**Count precincts with discrepancies** using a set of unique precinct names, not the length of the discrepancy list (one precinct can have multiple issues):

```python
precincts_with_issues = {d["precinct"] for d in discrepancies if d["precinct"]}
summary["precincts_with_discrepancies"] = len(precincts_with_issues)
```

**Algorithm outline**:

```python
for official_precinct in official_precincts:
    tally_precinct = fuzzy_match(official_precinct, tally_names)

    if tally_precinct is None:
        # Entire precinct absent — ONE entry, no candidate
        discrepancies.append({
            "precinct": official_precinct, "candidate": None,
            "discrepancy_type": "precinct_missing", "severity": "high",
            "official_votes": None, "tally_votes": None, "difference": None,
        })
        continue  # do NOT loop over candidates for this precinct

    for candidate in official_candidates:
        if candidate not in tally_precinct:
            discrepancies.append({
                "precinct": official_precinct, "candidate": candidate,
                "discrepancy_type": "candidate_missing", "severity": "high",
                "official_votes": None, "tally_votes": None, "difference": None,
            })
        else:
            official_v = official_votes[official_precinct][candidate]
            tally_v    = parse_int(tally_precinct[candidate])
            registered = official_registered[official_precinct]
            if tally_v > registered:
                d_type = "impossible_value"
            elif tally_v != official_v:
                d_type = "vote_count_mismatch"
            else:
                continue  # no discrepancy
            diff = abs(tally_v - official_v)
            discrepancies.append({
                "precinct": official_precinct, "candidate": candidate,
                "discrepancy_type": d_type,
                "official_votes": official_v, "tally_votes": tally_v,
                "difference": diff,
                "severity": classify_severity(d_type, diff),
            })
```

