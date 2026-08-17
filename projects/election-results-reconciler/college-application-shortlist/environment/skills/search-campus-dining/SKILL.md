---
name: search-campus-dining
description: Search campus dining and meal plan options by university from the bundled dataset. Use this skill when you need to compare food services and dining costs across universities.
---

# Search Campus Dining

Look up dining halls, meal plans, and food options for universities.

## Installation

```bash
pip install pandas
```

## Quick Start

```python
from search_campus_dining import CampusDining

dining = CampusDining()
result = dining.run(university="Ohio State University")
print(result)
```

## Parameters

- `university` – University name to look up (e.g. `"Purdue University"`)
