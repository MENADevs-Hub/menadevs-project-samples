---
name: fuzzy-record-linkage
description: Match and join records across two datasets when shared identifiers have minor variations — typos, abbreviations, OCR errors, inconsistent formatting. Use when two sources refer to the same real-world entities (locations, names, product titles, org names) but IDs don't align and exact string matching fails.
---

# Fuzzy Record Linkage

## When exact matching breaks

Two datasets covering the same domain often differ in label formatting:
- OCR errors: `"East Wrd"` instead of `"East Ward"`
- Abbreviations: `"Univ. District"` vs `"University District"`
- Extra whitespace, punctuation, or casing differences

## Python standard library approach (no extra dependencies)

`difflib` covers most cases without installing anything.

### One-to-many lookup — find the best match from a list

```python
import difflib

def match_name(query, candidates, cutoff=0.75):
    """Return the closest candidate or None if no match above cutoff."""
    matches = difflib.get_close_matches(query, candidates, n=1, cutoff=cutoff)
    return matches[0] if matches else None

# Example
official_names = ["North Ward", "South Ward", "East Ward", "University District"]
match_name("East Wrd", official_names)        # → "East Ward"
match_name("Univeristy Distric", official_names)  # → "University District"
match_name("Completely Wrong", official_names)    # → None
```

### Pair-wise similarity score

```python
def similarity(a, b):
    return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()

similarity("East Ward", "East Wrd")   # → ~0.89
similarity("East Ward", "West Ward")  # → ~0.73
```

## Choosing a cutoff threshold

| Cutoff | Use when |
|--------|----------|
| 0.6–0.7 | OCR output, heavy abbreviation, international names |
| 0.75–0.8 | Typos, missing characters, minor OCR noise ← good default |
| 0.85+ | Only allow very close matches, reject partial names |

## Normalise before matching

Strip noise before comparison to improve accuracy:

```python
import re

def normalise(s):
    s = s.lower().strip()
    s = re.sub(r"[^\w\s]", "", s)   # remove punctuation
    s = re.sub(r"\s+", " ", s)      # collapse whitespace
    return s
```

Run `normalise()` on both the query and the candidate list before calling `get_close_matches`.

## Build a mapping dict once, reuse everywhere

```python
name_map = {}
for raw_name in source_names:
    official = match_name(normalise(raw_name), [normalise(n) for n in official_names])
    if official:
        # map back to original casing using index
        idx = [normalise(n) for n in official_names].index(official)
        name_map[raw_name] = official_names[idx]
    else:
        name_map[raw_name] = None   # unresolvable
```
