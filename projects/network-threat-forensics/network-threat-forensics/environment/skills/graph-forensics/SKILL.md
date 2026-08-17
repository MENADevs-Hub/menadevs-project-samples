---
name: graph-forensics
description: Network graph analysis for lateral movement detection. Use when comparing connection patterns between a baseline and investigation period to find new internal-to-internal edges. New edges that did not exist during baseline indicate a host reaching out to machines it has never contacted before, which is a sign of lateral movement after a compromise.
---

# Graph-Based Lateral Movement Detection

## Concept

Internal hosts have regular communication partners (For example, a workstation talks to its file server and the domain controller). When an attacker compromises a host, they pivot through the network contacting machines the host has never communicated with before. These new edges in the connection graph are the signal.

## Building the Baseline Graph

```python
import pandas as pd
from collections import defaultdict

nf = pd.read_csv("/root/netflow.csv")

def is_internal(ip):
    return ip.startswith("10.0.1.")

# Only internal-to-internal connections
internal = nf[(nf["src_ip"].apply(is_internal)) & (nf["dst_ip"].apply(is_internal))]

# Baseline edges: all (src, dst) pairs seen during baseline period
baseline_edges = set()
for _, row in internal[internal["timestamp"] <= config["baseline_end"]].iterrows():
    baseline_edges.add((row["src_ip"], row["dst_ip"]))
```

## Finding New Edges

```python
new_edges = defaultdict(lambda: {"targets": set(), "first_seen": None})

for _, row in internal[internal["timestamp"] >= config["investigation_start"]].iterrows():
    edge = (row["src_ip"], row["dst_ip"])
    if edge not in baseline_edges:
        src = row["src_ip"]
        new_edges[src]["targets"].add(row["dst_ip"])
        if new_edges[src]["first_seen"] is None or row["timestamp"] < new_edges[src]["first_seen"]:
            new_edges[src]["first_seen"] = row["timestamp"]
```

## Identifying the Pivot Host

The host with the most new internal targets is the strongest candidate for a compromised machine doing lateral movement.

```python
pivot_host = max(new_edges, key=lambda h: len(new_edges[h]["targets"]))
targets = sorted(list(new_edges[pivot_host]["targets"]))
first_seen = new_edges[pivot_host]["first_seen"]
```

## Notes

- Only count edges as "new" if the exact (src, dst) directed pair was never seen in baseline
- Sort the target list for consistent output
- The first_seen timestamp is the earliest connection on any new edge from that host

## Report Output

The `lateral_movement` section of the report must use these exact field names:

```python
{
    "source_host": str(pivot_host),
    "new_internal_targets": sorted(list(new_edges[pivot_host]["targets"])),
    "first_seen": str(new_edges[pivot_host]["first_seen"]),  # keep as string
}
```
