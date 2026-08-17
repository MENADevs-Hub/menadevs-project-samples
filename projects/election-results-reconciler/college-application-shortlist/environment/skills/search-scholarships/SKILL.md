---
name: search-scholarships
description: Search scholarships by university, minimum amount, or type from the bundled dataset. Use this skill when you need to find merit or need-based financial aid for a particular university.
---

# Search Scholarships

Filter the scholarships CSV by university, minimum award amount, or scholarship type.

## Installation

```bash
pip install pandas
```

## Quick Start

```python
from search_scholarships import Scholarships

scholarships = Scholarships()
result = scholarships.run(university="Purdue University", min_amount=10000)
print(result)
```

## Parameters

- `university` – Filter by university name (e.g. `"Ohio State University"`)
- `min_amount` – Minimum scholarship amount in dollars (e.g. `10000`)
- `scholarship_type` – Filter by type (`"Merit"`, `"Need"`, `"Need + Merit"`)

All filters are optional and case-insensitive.
