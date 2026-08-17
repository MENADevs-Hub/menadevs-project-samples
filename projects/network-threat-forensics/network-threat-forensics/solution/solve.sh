#!/bin/bash
set -e
pip3 install --break-system-packages pandas numpy
python3 << 'PYEOF'
import json, math, pandas as pd, numpy as np
from collections import defaultdict
from datetime import datetime

nf = pd.read_csv("/root/netflow.csv")
dns = pd.read_csv("/root/dns_queries.csv")
with open("/root/investigation_config.json") as f:
    cfg = json.load(f)

BASELINE_END = cfg["baseline_end"]
INV_START = cfg["investigation_start"]
ENTROPY_THRESH = cfg["entropy_threshold"]
JITTER_THRESH = cfg["beaconing_jitter_threshold"]
MAD_THRESH = cfg["mad_zscore_threshold"]
MIN_BEACON = cfg["min_beaconing_connections"]

def is_internal(ip):
    return ip.startswith("10.0.1.")

# === 1. DNS Tunneling Detection ===
def shannon_entropy(s):
    if len(s) == 0:
        return 0.0
    freq = {}
    for c in s:
        freq[c] = freq.get(c, 0) + 1
    n = len(s)
    return -sum((count/n) * math.log2(count/n) for count in freq.values())

# Extract subdomain: everything before last 2 labels
dns["labels"] = dns["query_domain"].apply(lambda d: d.split("."))
dns["base_domain"] = dns["labels"].apply(lambda l: ".".join(l[-2:]) if len(l) >= 2 else l[0])
dns["subdomain"] = dns["labels"].apply(lambda l: ".".join(l[:-2]) if len(l) > 2 else "")
dns["subdomain_entropy"] = dns["subdomain"].apply(shannon_entropy)

# Group by base_domain, find high-entropy domains
tunnel_candidates = dns[dns["subdomain_entropy"] > ENTROPY_THRESH]
tunnel_by_domain = tunnel_candidates.groupby("base_domain").agg(
    query_count=("subdomain_entropy", "count"),
    mean_entropy=("subdomain_entropy", "mean"),
    host=("src_ip", "first"),
    first_seen=("timestamp", "min"),
).reset_index()
tunnel_domain = tunnel_by_domain.sort_values("query_count", ascending=False).iloc[0]

dns_tunneling = {
    "host": str(tunnel_domain["host"]),
    "tunnel_domain": str(tunnel_domain["base_domain"]),
    "mean_subdomain_entropy": round(float(tunnel_domain["mean_entropy"]), 2),
    "query_count": int(tunnel_domain["query_count"]),
    "first_seen": str(tunnel_domain["first_seen"]),
}

# === 2. C2 Beaconing Detection ===
# External connections from internal hosts
ext_conns = nf[(nf["src_ip"].apply(is_internal)) & (~nf["dst_ip"].apply(is_internal))]
ext_conns = ext_conns.copy()
ext_conns["ts"] = pd.to_datetime(ext_conns["timestamp"])

best_beacon = None
for (src, dst), grp in ext_conns.groupby(["src_ip", "dst_ip"]):
    if len(grp) < MIN_BEACON:
        continue
    times = sorted(grp["ts"].values)
    intervals = [(times[i+1] - times[i]) / np.timedelta64(1, 's') for i in range(len(times)-1)]
    if len(intervals) < 2:
        continue
    mean_int = float(np.mean(intervals))
    std_int = float(np.std(intervals, ddof=1))
    if mean_int == 0:
        continue
    jitter = std_int / mean_int
    if jitter < JITTER_THRESH:
        if best_beacon is None or len(grp) > best_beacon["connection_count"]:
            best_beacon = {
                "host": str(src),
                "destination": str(dst),
                "mean_interval_seconds": round(mean_int, 1),
                "jitter_coefficient": round(jitter, 4),
                "connection_count": int(len(grp)),
                "first_seen": str(grp["timestamp"].min()),
            }

c2_beaconing = best_beacon

# === 3. Lateral Movement Detection ===
int_conns = nf[(nf["src_ip"].apply(is_internal)) & (nf["dst_ip"].apply(is_internal))]
baseline_edges = set()
inv_new_edges = defaultdict(lambda: {"targets": set(), "first_seen": None})

for _, row in int_conns.iterrows():
    edge = (row["src_ip"], row["dst_ip"])
    if row["timestamp"] <= BASELINE_END:
        baseline_edges.add(edge)
    elif row["timestamp"] >= INV_START:
        if edge not in baseline_edges:
            src = row["src_ip"]
            inv_new_edges[src]["targets"].add(row["dst_ip"])
            if inv_new_edges[src]["first_seen"] is None or row["timestamp"] < inv_new_edges[src]["first_seen"]:
                inv_new_edges[src]["first_seen"] = row["timestamp"]

# Find the host with the most new internal targets
lateral_host = max(inv_new_edges, key=lambda h: len(inv_new_edges[h]["targets"]))
lateral_info = inv_new_edges[lateral_host]

lateral_movement = {
    "source_host": str(lateral_host),
    "new_internal_targets": sorted(list(lateral_info["targets"])),
    "first_seen": str(lateral_info["first_seen"]),
}

# === 4. Data Exfiltration (MAD z-score) ===
nf["hour"] = pd.to_datetime(nf["timestamp"]).dt.strftime("%Y-%m-%dT%H:00:00Z")

# Per-host per-hour bytes_sent
hourly = nf[nf["src_ip"].apply(is_internal)].groupby(["src_ip", "hour"])["bytes_sent"].sum().reset_index()

# Baseline stats per host
baseline_hourly = hourly[hourly["hour"] <= BASELINE_END]
inv_hourly = hourly[hourly["hour"] >= INV_START]

max_z = 0
exfil_info = None

for host in hourly["src_ip"].unique():
    bh = baseline_hourly[baseline_hourly["src_ip"] == host]["bytes_sent"]
    if len(bh) < 3:
        continue
    median_b = float(bh.median())
    mad = float((bh - median_b).abs().median())
    if mad == 0:
        mad = 1.0  # avoid division by zero

    ih = inv_hourly[inv_hourly["src_ip"] == host]
    for _, row in ih.iterrows():
        z = 0.6745 * (row["bytes_sent"] - median_b) / mad
        if z > max_z:
            max_z = z
            exfil_info = {
                "host": str(host),
                "destination": None,
                "peak_hour": str(row["hour"]),
                "bytes_sent": int(row["bytes_sent"]),
                "mad_z_score": round(float(z), 1),
                "baseline_median_bytes_per_hour": int(round(median_b, 0)),
            }

# Find the destination for the exfiltration hour
if exfil_info:
    peak_flows = nf[(nf["src_ip"] == exfil_info["host"]) &
                     (nf["hour"] == exfil_info["peak_hour"])]
    top_dst = peak_flows.groupby("dst_ip")["bytes_sent"].sum().idxmax()
    exfil_info["destination"] = str(top_dst)

# === 5. Identify compromised host ===
suspects = set()
suspects.add(dns_tunneling["host"])
if c2_beaconing:
    suspects.add(c2_beaconing["host"])
suspects.add(lateral_movement["source_host"])
suspects.add(exfil_info["host"])

# === 6. Timeline ===
timeline = sorted([
    {"timestamp": dns_tunneling["first_seen"], "event": "dns_tunneling_start"},
    {"timestamp": c2_beaconing["first_seen"], "event": "c2_beaconing_start"},
    {"timestamp": lateral_movement["first_seen"], "event": "lateral_movement_start"},
    {"timestamp": exfil_info["peak_hour"], "event": "data_exfiltration"},
], key=lambda x: x["timestamp"])

report = {
    "compromised_hosts": sorted(list(suspects)),
    "c2_server": c2_beaconing["destination"] if c2_beaconing else None,
    "exfiltration_destination": exfil_info["destination"],
    "dns_tunneling": dns_tunneling,
    "c2_beaconing": c2_beaconing,
    "lateral_movement": lateral_movement,
    "exfiltration": exfil_info,
    "timeline": timeline,
}

with open("/root/forensic_report.json", "w") as f:
    json.dump(report, f, indent=2)

print(json.dumps(report, indent=2))
PYEOF
