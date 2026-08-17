#!/usr/bin/env python3

import pandas as pd
import numpy as np
import json

def is_internal(ip):
    """Check if IP is internal (10.0.1.x subnet)"""
    return ip.startswith("10.0.1.")

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

def detect_c2_beaconing():
    """Detect C2 beaconing using jitter analysis"""

    # Load config and data
    with open('/root/investigation_config.json', 'r') as f:
        config = json.load(f)

    nf = pd.read_csv('/root/netflow.csv')

    # Filter for outbound connections (internal to external)
    outbound = nf[(nf['src_ip'].apply(is_internal)) & (~nf['dst_ip'].apply(is_internal))]

    print(f"Loaded {len(nf)} netflow records")
    print(f"Found {len(outbound)} outbound connections")
    print(f"Minimum connections threshold: {config['min_beaconing_connections']}")
    print(f"Jitter threshold: {config['beaconing_jitter_threshold']}")

    # Group by (src_ip, dst_ip) pairs
    beaconing_candidates = []

    for (src, dst), group in outbound.groupby(['src_ip', 'dst_ip']):
        # Filter pairs with enough connections
        if len(group) < config['min_beaconing_connections']:
            continue

        # Sort by timestamp and convert to datetime for interval calculation
        group_sorted = group.sort_values('timestamp')
        timestamps = pd.to_datetime(group_sorted['timestamp']).values

        # Compute jitter
        mean_interval, jitter = compute_jitter(timestamps)

        # Check if jitter is below threshold (indicating regular beaconing)
        if jitter < config['beaconing_jitter_threshold']:
            candidate = {
                'src_ip': src,
                'dst_ip': dst,
                'connection_count': len(group),
                'mean_interval': mean_interval,
                'jitter': jitter,
                'first_seen': group_sorted['timestamp'].iloc[0]  # Keep as string
            }
            beaconing_candidates.append(candidate)

    print(f"Found {len(beaconing_candidates)} beaconing candidates")

    if len(beaconing_candidates) == 0:
        print("No C2 beaconing detected")
        return None

    # Sort by connection count (most connections first), then by lowest jitter
    beaconing_candidates.sort(key=lambda x: (-x['connection_count'], x['jitter']))

    # Show all candidates
    for candidate in beaconing_candidates:
        print(f"  {candidate['src_ip']} -> {candidate['dst_ip']}: "
              f"{candidate['connection_count']} connections, "
              f"jitter {candidate['jitter']:.4f}, "
              f"interval {candidate['mean_interval']:.1f}s")

    # The strongest candidate has the most connections and lowest jitter
    strongest_candidate = beaconing_candidates[0]

    result = {
        "host": str(strongest_candidate['src_ip']),
        "destination": str(strongest_candidate['dst_ip']),
        "mean_interval_seconds": round(strongest_candidate['mean_interval'], 1),
        "jitter_coefficient": round(strongest_candidate['jitter'], 4),
        "connection_count": int(strongest_candidate['connection_count']),
        "first_seen": str(strongest_candidate['first_seen'])
    }

    print(f"\nC2 Beaconing Detection Result:")
    print(f"Host: {result['host']}")
    print(f"Destination: {result['destination']}")
    print(f"Mean Interval: {result['mean_interval_seconds']}s")
    print(f"Jitter: {result['jitter_coefficient']}")
    print(f"Connection Count: {result['connection_count']}")
    print(f"First Seen: {result['first_seen']}")

    return result

if __name__ == "__main__":
    result = detect_c2_beaconing()
    if result:
        # Save result for later use
        with open('/logs/agent/sessions/skills/beaconing-detection/c2_beaconing_result.json', 'w') as f:
            json.dump(result, f, indent=2)