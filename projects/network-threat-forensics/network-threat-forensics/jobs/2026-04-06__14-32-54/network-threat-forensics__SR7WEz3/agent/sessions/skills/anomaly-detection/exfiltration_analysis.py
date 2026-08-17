#!/usr/bin/env python3

import pandas as pd
import numpy as np
import json

def is_internal(ip):
    """Check if IP is internal (10.0.1.x subnet)"""
    return ip.startswith("10.0.1.")

def mad_zscore(value, baseline_values):
    """
    value: single observation to test
    baseline_values: array of baseline observations
    Returns: modified z-score
    """
    median = np.median(baseline_values)
    mad = np.median(np.abs(baseline_values - median))
    if mad == 0:
        mad = 1.0  # fallback to avoid division by zero
    return 0.6745 * (value - median) / mad

def detect_data_exfiltration():
    """Detect data exfiltration using MAD-based anomaly detection"""

    # Load config and data
    with open('/root/investigation_config.json', 'r') as f:
        config = json.load(f)

    nf = pd.read_csv('/root/netflow.csv')

    # Filter for outbound connections from internal hosts
    outbound = nf[nf['src_ip'].apply(is_internal)]

    print(f"Loaded {len(nf)} netflow records")
    print(f"Found {len(outbound)} outbound connections")
    print(f"MAD z-score threshold: {config['mad_zscore_threshold']}")

    # Parse timestamps and bucket into hours
    outbound['hour'] = pd.to_datetime(outbound['timestamp']).dt.strftime("%Y-%m-%dT%H:00:00Z")

    # Aggregate bytes_sent per host per hour
    hourly = outbound.groupby(['src_ip', 'hour'])['bytes_sent'].sum().reset_index()

    print(f"Aggregated into {len(hourly)} host-hour records")

    # Split into baseline and investigation periods
    baseline_bytes = hourly[hourly['hour'] <= config['baseline_end']]
    investigation_bytes = hourly[hourly['hour'] >= config['investigation_start']]

    print(f"Baseline records: {len(baseline_bytes)}")
    print(f"Investigation records: {len(investigation_bytes)}")

    # Find anomalous traffic patterns
    anomalies = []
    hosts = hourly['src_ip'].unique()

    for host in hosts:
        # Get baseline hourly bytes for this host
        bh = baseline_bytes[baseline_bytes['src_ip'] == host]['bytes_sent']

        if len(bh) == 0:  # No baseline data for this host
            continue

        median_b = float(bh.median())
        mad = float((bh - median_b).abs().median())
        if mad == 0:
            mad = 1.0

        # Check investigation period for anomalies
        ih = investigation_bytes[investigation_bytes['src_ip'] == host]

        for _, row in ih.iterrows():
            z = mad_zscore(row['bytes_sent'], bh.values)

            if z > config['mad_zscore_threshold']:
                anomalies.append({
                    'host': host,
                    'hour': row['hour'],
                    'bytes_sent': row['bytes_sent'],
                    'z_score': z,
                    'baseline_median': median_b
                })

    print(f"Found {len(anomalies)} anomalous hours")

    if len(anomalies) == 0:
        print("No data exfiltration detected")
        return None

    # Sort by z-score (highest first) to find the strongest anomaly
    anomalies.sort(key=lambda x: x['z_score'], reverse=True)

    # Show all anomalies
    for anomaly in anomalies:
        print(f"  {anomaly['host']} at {anomaly['hour']}: "
              f"{anomaly['bytes_sent']} bytes (z-score: {anomaly['z_score']:.1f})")

    # Get the strongest anomaly
    peak_anomaly = anomalies[0]

    # Find the destination that received the most bytes during this peak hour
    peak_host = peak_anomaly['host']
    peak_hour = peak_anomaly['hour']

    # Get all flows from this host during the peak hour
    peak_flows = outbound[
        (outbound['src_ip'] == peak_host) &
        (outbound['hour'] == peak_hour)
    ]

    # Group by destination and sum bytes to find top destination
    dst_bytes = peak_flows.groupby('dst_ip')['bytes_sent'].sum().reset_index()
    dst_bytes = dst_bytes.sort_values('bytes_sent', ascending=False)

    if len(dst_bytes) > 0:
        top_dst_ip = dst_bytes.iloc[0]['dst_ip']
        print(f"\nTop destination during peak hour: {top_dst_ip}")
    else:
        top_dst_ip = "unknown"

    result = {
        "host": str(peak_anomaly['host']),
        "destination": str(top_dst_ip),
        "peak_hour": str(peak_anomaly['hour']),
        "bytes_sent": int(peak_anomaly['bytes_sent']),
        "mad_z_score": round(float(peak_anomaly['z_score']), 1),
        "baseline_median_bytes_per_hour": int(round(peak_anomaly['baseline_median'], 0))
    }

    print(f"\nData Exfiltration Detection Result:")
    print(f"Host: {result['host']}")
    print(f"Destination: {result['destination']}")
    print(f"Peak Hour: {result['peak_hour']}")
    print(f"Bytes Sent: {result['bytes_sent']}")
    print(f"MAD Z-Score: {result['mad_z_score']}")
    print(f"Baseline Median: {result['baseline_median_bytes_per_hour']}")

    return result

if __name__ == "__main__":
    result = detect_data_exfiltration()
    if result:
        # Save result for later use
        with open('/logs/agent/sessions/skills/anomaly-detection/exfiltration_result.json', 'w') as f:
            json.dump(result, f, indent=2)