---
name: entropy-analysis
description: Shannon entropy computation for DNS tunneling detection. Use when analyzing DNS query logs to find data exfiltration via DNS. Tunneling encodes data in subdomain labels, producing high-entropy random-looking strings. Normal subdomains like "www" or "api" have low entropy. Threshold of 3.5 bits/character separates benign from suspicious.
---

# Entropy Analysis for DNS Tunneling

## Shannon Entropy

Character-level Shannon entropy measures randomness of a string:

```python
import math

def shannon_entropy(s):
    if len(s) == 0:
        return 0.0
    freq = {}
    for c in s:
        freq[c] = freq.get(c, 0) + 1
    n = len(s)
    return -sum((count / n) * math.log2(count / n) for count in freq.values())
```

Reference values:

- "www" -> 0.0 (single repeated character)
- "mail" -> 2.0
- "api" -> 1.58
- Random hex (30 chars) -> ~3.8 to 4.1

## Extracting Subdomains

The subdomain is everything before the registered domain (last 2 labels):

```python
def extract_parts(domain):
    labels = domain.split(".")
    base_domain = ".".join(labels[-2:])       # For example "example.net"
    subdomain = ".".join(labels[:-2])          # For example "a3f8b2c1d9e4"
    return subdomain, base_domain
```

## Detection Workflow

1. For each DNS query, extract subdomain and compute its entropy
2. Filter queries where entropy exceeds the threshold (typically 3.5)
3. Group remaining queries by base domain
4. The base domain with the most high-entropy queries is the tunnel endpoint
5. Report: which host made these queries, the base domain, average entropy, count, and first timestamp

```python
dns["subdomain"], dns["base_domain"] = zip(*dns["query_domain"].apply(
    lambda d: (".".join(d.split(".")[:-2]), ".".join(d.split(".")[-2:]))
))
dns["entropy"] = dns["subdomain"].apply(shannon_entropy)

suspicious = dns[dns["entropy"] > threshold]
tunnel = suspicious.groupby("base_domain").agg(
    count=("entropy", "count"),
    mean_entropy=("entropy", "mean"),
    host=("src_ip", "first"),
    first_seen=("timestamp", "min"),
)
```

## Report Output

The `dns_tunneling` section of the report must use these exact field names:

```python
{
    "host": str(tunnel_domain["host"]),           # src_ip of the tunneling host
    "tunnel_domain": str(tunnel_domain["base_domain"]),  # the abused base domain
    "mean_subdomain_entropy": round(float(tunnel_domain["mean_entropy"]), 2),
    "query_count": int(tunnel_domain["count"]),
    "first_seen": str(tunnel_domain["first_seen"]),  # keep as string, not datetime
}
```
