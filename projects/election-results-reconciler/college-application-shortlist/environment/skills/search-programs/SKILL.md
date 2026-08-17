---
name: search-programs
description: Search academic programs by university or program name from the bundled dataset. Use this skill when you need to look up tuition, program rankings, co-op availability, or starting salaries for specific degree programs.
---

# Search Programs

Filter the programs CSV by university and/or program name.

## Installation

```bash
pip install pandas
```

## Quick Start

```python
from search_programs import Programs

programs = Programs()
result = programs.run(university="Purdue University")
print(result)

# Or filter by program name across all universities
result = programs.run(program="Computer Science")
print(result)
```

## Parameters

- `university` – Filter by university name (e.g. `"Georgia Institute of Technology"`)
- `program` – Filter by program name (e.g. `"Computer Science"`, `"Data Science"`)

Both filters are optional and case-insensitive.
