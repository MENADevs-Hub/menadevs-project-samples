---
name: search-nightlife
description: Search nightlife and entertainment options by city from the bundled dataset. Use this skill when you need to compare social scenes or entertainment options across college towns.
---

# Search Nightlife

Look up bars, clubs, and entertainment venues for US cities.

## Installation

```bash
pip install pandas
```

## Quick Start

```python
from search_nightlife import Nightlife

nightlife = Nightlife()
result = nightlife.run(city="Austin")
print(result)
```

## Parameters

- `city` – City name to look up (e.g. `"Austin"`)
