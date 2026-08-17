---
name: search-housing
description: Search campus housing options by university and housing type from the bundled dataset. Use this skill when you need to check housing availability, costs, or guaranteed years for a university.
---

# Search Housing

Filter the housing CSV by university and/or housing type.

## Installation

```bash
pip install pandas
```

## Quick Start

```python
from search_housing import Housing

housing = Housing()
result = housing.run(university="University of Michigan")
print(result)
```

## Parameters

- `university` – Filter by university name (e.g. `"Purdue University"`)
- `housing_type` – Filter by type (e.g. `"On-Campus Dorm"`, `"On-Campus Apartment"`)

Both filters are optional and case-insensitive.
