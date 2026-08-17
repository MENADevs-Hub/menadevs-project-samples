#!/usr/bin/env python3

import pandas as pd
import json
import math

def shannon_entropy(s):
    """Calculate Shannon entropy for a string"""
    if len(s) == 0:
        return 0.0
    freq = {}
    for c in s:
        freq[c] = freq.get(c, 0) + 1
    n = len(s)
    return -sum((count / n) * math.log2(count / n) for count in freq.values())

def extract_parts(domain):
    """Extract subdomain and base domain from a full domain"""
    labels = domain.split(".")
    if len(labels) < 2:
        return "", domain
    base_domain = ".".join(labels[-2:])       # e.g. "example.net"
    subdomain = ".".join(labels[:-2])          # e.g. "a3f8b2c1d9e4"
    return subdomain, base_domain

def detect_dns_tunneling():
    """Detect DNS tunneling using entropy analysis"""

    # Load config and data
    with open('/root/investigation_config.json', 'r') as f:
        config = json.load(f)

    dns = pd.read_csv('/root/dns_queries.csv')

    # Extract subdomains and base domains
    dns['subdomain'], dns['base_domain'] = zip(*dns['query_domain'].apply(extract_parts))

    # Calculate entropy for each subdomain
    dns['entropy'] = dns['subdomain'].apply(shannon_entropy)

    print(f"Loaded {len(dns)} DNS queries")
    print(f"Entropy threshold: {config['entropy_threshold']}")

    # Filter for high-entropy queries
    threshold = config['entropy_threshold']
    suspicious = dns[dns['entropy'] > threshold]

    print(f"Found {len(suspicious)} high-entropy queries")

    if len(suspicious) == 0:
        print("No DNS tunneling detected")
        return None

    # Group by base domain and aggregate statistics
    tunnel_stats = suspicious.groupby('base_domain').agg(
        count=('entropy', 'count'),
        mean_entropy=('entropy', 'mean'),
        host=('src_ip', 'first'),
        first_seen=('timestamp', 'min'),
    ).reset_index()

    # Sort by count (most queries first) to find the strongest tunnel candidate
    tunnel_stats = tunnel_stats.sort_values('count', ascending=False)

    print(f"Suspicious base domains found: {len(tunnel_stats)}")
    for _, row in tunnel_stats.iterrows():
        print(f"  {row['base_domain']}: {row['count']} queries, avg entropy {row['mean_entropy']:.2f}, host {row['host']}")

    # The domain with the most high-entropy queries is the tunnel
    if len(tunnel_stats) > 0:
        tunnel_domain = tunnel_stats.iloc[0]

        result = {
            "host": str(tunnel_domain["host"]),
            "tunnel_domain": str(tunnel_domain["base_domain"]),
            "mean_subdomain_entropy": round(float(tunnel_domain["mean_entropy"]), 2),
            "query_count": int(tunnel_domain["count"]),
            "first_seen": str(tunnel_domain["first_seen"])
        }

        print(f"\nDNS Tunneling Detection Result:")
        print(f"Host: {result['host']}")
        print(f"Tunnel Domain: {result['tunnel_domain']}")
        print(f"Mean Entropy: {result['mean_subdomain_entropy']}")
        print(f"Query Count: {result['query_count']}")
        print(f"First Seen: {result['first_seen']}")

        return result

    return None

if __name__ == "__main__":
    result = detect_dns_tunneling()
    if result:
        # Save result for later use
        with open('/logs/agent/sessions/skills/entropy-analysis/dns_tunneling_result.json', 'w') as f:
            json.dump(result, f, indent=2)