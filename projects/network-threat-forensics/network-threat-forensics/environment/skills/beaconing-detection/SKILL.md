---
name: beaconing-detection
description: Detecting C2 beaconing in network traffic using inter-arrival time analysis. Use when looking for command-and-control communication where malware connects to an external server at regular automated intervals. The key indicator is low jitter coefficient (std/mean of connection intervals), typically below 0.1 for beaconing vs above 0.5 for human browsing.
---

# Beaconing Detection

## Concept

C2 beaconing is when malware periodically "phones home" to receive commands. Because it is automated, connections happen at very regular intervals (For example, every 300 seconds with minimal variation). Normal human browsing has highly irregular timing.

## Jitter Coefficient

```python
import numpy as np

def compute_jitter(timestamps_sorted):
    """
    timestamps_sorted: sorted numpy datetime64 array
    Returns: (mean_interval_seconds, jitter_coefficient)
    """
    intervals = [
        (timestamps_sorted[i+1] - timestamps_sorted[i]) / np.timedelta64(1, 's')
        for i in range(len(timestamps_sorted) - 1)
    ]
    mean_interval = float(np.mean(intervals))
    std_interval = float(np.std(intervals, ddof=1))
    jitter = std_interval / mean_interval if mean_interval > 0 else float('inf')
    return mean_interval, jitter
```

| Traffic Type        | Jitter Coefficient |
| ------------------- | ------------------ |
| C2 beaconing        | < 0.05             |
| Heartbeat/keepalive | 0.05 - 0.1         |
| Automated polling   | 0.1 - 0.3          |
| Human browsing      | 0.5 - 2.0+         |

## Detection Workflow

1. Group outbound connections by (src_ip, dst_ip) pair
2. Filter pairs with enough connections (check config for minimum, typically 20+)
3. Sort connections by timestamp within each pair
4. Compute inter-arrival intervals and jitter coefficient
5. Flag pairs where jitter < threshold (typically 0.1)
6. Report: host, destination, mean interval, jitter, connection count, first seen

The pair with the most connections and lowest jitter is the strongest C2 candidate.

## Report Output

The `c2_beaconing` section of the report must use these exact field names:

```python
{
    "host": str(src),                                    # internal source IP
    "destination": str(dst),                             # external C2 server IP
    "mean_interval_seconds": round(mean_interval, 1),
    "jitter_coefficient": round(jitter, 4),
    "connection_count": int(len(group)),
    "first_seen": str(group["timestamp"].min()),  # read from string column, don't convert to datetime
}
```

> **Important**: read `timestamp` from the CSV as a string (default pandas behavior). Do not call `pd.to_datetime()` on it before taking `.min()`, otherwise the timestamp will have nanosecond formatting. Take `.min()` directly on the string column.
