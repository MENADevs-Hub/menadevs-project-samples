---
name: search-weather
description: Search average weather conditions by city from the bundled dataset. Use this skill when you need to compare climate across cities for relocation or travel planning.
---

# Search Weather

Look up average temperature, rainfall, and sunshine data for US cities.

## Installation

```bash
pip install pandas
```

## Quick Start

```python
from search_weather import Weather

weather = Weather()
result = weather.run(city="Boston")
print(result)
```

## Parameters

- `city` – City name to look up (e.g. `"Seattle"`)
- `state` – Filter by state (e.g. `"California"`)
