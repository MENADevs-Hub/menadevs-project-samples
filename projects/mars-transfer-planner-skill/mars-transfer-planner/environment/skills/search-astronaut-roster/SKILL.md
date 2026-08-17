---
name: search-astronaut-roster
description: "Search the astronaut roster database for crew assignment and qualification data. Use when selecting crew members for crewed missions based on qualifications, flight hours, and medical status."
---

# Search Astronaut Roster

Query the astronaut roster for crew assignments.

## Usage

```python
from search_astronaut_roster import AstronautRoster
ar = AstronautRoster()
result = ar.run(min_flight_hours=1000, qualification="mars-rated")
```
