---
name: compute-communication-delay
description: "Compute one-way and round-trip communication delay between Earth and a target planet based on orbital positions. Use when planning communication windows and signal latency for deep space missions."
---

# Compute Communication Delay

Calculates signal travel time between Earth and a distant body.

## Usage

```python
from compute_communication_delay import CommDelay
cd = CommDelay()
result = cd.run(distance_km=225000000)
```
