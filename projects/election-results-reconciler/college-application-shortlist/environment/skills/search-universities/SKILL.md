---
name: search-universities
description: Lookup universities from the bundled dataset with filters for state, campus setting, and institution type. Use this skill when you need to find or compare universities before checking their programs, costs, or housing.
---

# Search Universities

Filter the universities CSV by state, setting, or type.

## Installation

```bash
pip install pandas
```

## Quick Start

```python
from search_universities import Universities

unis = Universities()
result = unis.run(state="Ohio")
print(result)
```

## Parameters

- `state` – Filter by state (e.g. `"Michigan"`)
- `setting` – Filter by setting (`"Urban"`, `"Suburban"`, `"Rural"`)
- `uni_type` – Filter by type (`"Public"`, `"Private"`)

All filters are optional and case-insensitive.
