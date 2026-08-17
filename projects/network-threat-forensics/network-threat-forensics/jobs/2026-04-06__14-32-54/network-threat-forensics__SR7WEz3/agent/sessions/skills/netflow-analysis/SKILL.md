---
name: netflow-analysis
description: Parsing and aggregating NetFlow/network connection data from CSV logs. Use when working with network traffic data, identifying internal vs external connections, computing per-host hourly traffic statistics, or building connection graphs between hosts.
---

# NetFlow Analysis

## Loading and Classifying Connections

```python
import pandas as pd

nf = pd.read_csv("/root/netflow.csv")

def is_internal(ip):
    return ip.startswith("10.0.1.")

# External connections (outbound from internal hosts)
ext = nf[(nf["src_ip"].apply(is_internal)) & (~nf["dst_ip"].apply(is_internal))]

# Internal connections (both endpoints inside our subnet)
internal = nf[(nf["src_ip"].apply(is_internal)) & (nf["dst_ip"].apply(is_internal))]
```

## Hourly Traffic Aggregation

```python
# Parse timestamps and bucket into hours
nf["hour"] = pd.to_datetime(nf["timestamp"]).dt.strftime("%Y-%m-%dT%H:00:00Z")

# Per-host per-hour bytes sent
hourly = nf[nf["src_ip"].apply(is_internal)].groupby(
    ["src_ip", "hour"]
)["bytes_sent"].sum().reset_index()
```

## Splitting Baseline and Investigation Periods

```python
# Use timestamps from config to split data
baseline = hourly[hourly["hour"] <= config["baseline_end"]]
investigation = hourly[hourly["hour"] >= config["investigation_start"]]
```

## Connection Pair Analysis

```python
# Group connections by (src, dst) pair for pattern analysis
for (src, dst), grp in ext.groupby(["src_ip", "dst_ip"]):
    timestamps = sorted(pd.to_datetime(grp["timestamp"]).values)
    # compute intervals, jitter, etc.
```
