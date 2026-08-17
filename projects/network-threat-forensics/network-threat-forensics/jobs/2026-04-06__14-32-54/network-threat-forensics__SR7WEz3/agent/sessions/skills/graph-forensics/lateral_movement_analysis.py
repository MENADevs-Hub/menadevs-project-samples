#!/usr/bin/env python3

import pandas as pd
import json
from collections import defaultdict

def is_internal(ip):
    """Check if IP is internal (10.0.1.x subnet)"""
    return ip.startswith("10.0.1.")

def detect_lateral_movement():
    """Detect lateral movement using graph analysis"""

    # Load config and data
    with open('/root/investigation_config.json', 'r') as f:
        config = json.load(f)

    nf = pd.read_csv('/root/netflow.csv')

    # Filter for internal-to-internal connections only
    internal = nf[(nf['src_ip'].apply(is_internal)) & (nf['dst_ip'].apply(is_internal))]

    print(f"Loaded {len(nf)} netflow records")
    print(f"Found {len(internal)} internal-to-internal connections")
    print(f"Baseline period: {config['baseline_start']} to {config['baseline_end']}")
    print(f"Investigation period: {config['investigation_start']} to {config['investigation_end']}")

    # Build baseline edges: all (src, dst) pairs seen during baseline period
    baseline_internal = internal[internal['timestamp'] <= config['baseline_end']]
    baseline_edges = set()

    for _, row in baseline_internal.iterrows():
        baseline_edges.add((row['src_ip'], row['dst_ip']))

    print(f"Baseline edges: {len(baseline_edges)}")

    # Find new edges during investigation period
    investigation_internal = internal[internal['timestamp'] >= config['investigation_start']]
    new_edges = defaultdict(lambda: {"targets": set(), "first_seen": None})

    for _, row in investigation_internal.iterrows():
        edge = (row['src_ip'], row['dst_ip'])
        if edge not in baseline_edges:
            src = row['src_ip']
            new_edges[src]['targets'].add(row['dst_ip'])
            # Track the earliest timestamp for this source host's new connections
            if new_edges[src]['first_seen'] is None or row['timestamp'] < new_edges[src]['first_seen']:
                new_edges[src]['first_seen'] = row['timestamp']

    print(f"Hosts with new internal connections: {len(new_edges)}")

    if len(new_edges) == 0:
        print("No lateral movement detected")
        return None

    # Show all hosts with new connections
    for src, data in new_edges.items():
        targets = sorted(list(data['targets']))
        print(f"  {src}: {len(targets)} new targets - {targets}")

    # The host with the most new internal targets is the strongest lateral movement candidate
    pivot_host = max(new_edges, key=lambda h: len(new_edges[h]["targets"]))
    targets = sorted(list(new_edges[pivot_host]["targets"]))
    first_seen = new_edges[pivot_host]["first_seen"]

    result = {
        "source_host": str(pivot_host),
        "new_internal_targets": targets,
        "first_seen": str(first_seen)
    }

    print(f"\nLateral Movement Detection Result:")
    print(f"Source Host: {result['source_host']}")
    print(f"New Internal Targets: {result['new_internal_targets']}")
    print(f"First Seen: {result['first_seen']}")

    return result

if __name__ == "__main__":
    result = detect_lateral_movement()
    if result:
        # Save result for later use
        with open('/logs/agent/sessions/skills/graph-forensics/lateral_movement_result.json', 'w') as f:
            json.dump(result, f, indent=2)