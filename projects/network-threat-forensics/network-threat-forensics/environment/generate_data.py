#!/usr/bin/env python3
"""Generate synthetic network forensics data."""
import csv, json, random
from datetime import datetime, timedelta

random.seed(2024)

HOSTS = [f"10.0.1.{i}" for i in range(1, 16)]
COMPROMISED = "10.0.1.7"
C2_SERVER = "203.0.113.50"
EXFIL_DST = "198.51.100.77"
TUNNEL_BASE = "example.net"
EXT_IPS = [f"192.0.2.{i}" for i in range(10, 26)]
DOMAINS = [
    "www.google.com", "api.stripe.com", "cdn.cloudflare.com",
    "mail.microsoft.com", "fonts.googleapis.com", "api.github.com",
    "slack.com", "zoom.us", "office365.com", "docs.python.org",
    "pypi.org", "npmjs.org", "update.windows.com", "icloud.com",
]
PEERS = {
    "10.0.1.1":  ["10.0.1.2", "10.0.1.5"],
    "10.0.1.2":  ["10.0.1.1", "10.0.1.3"],
    "10.0.1.3":  ["10.0.1.2", "10.0.1.4"],
    "10.0.1.4":  ["10.0.1.3", "10.0.1.5"],
    "10.0.1.5":  ["10.0.1.1", "10.0.1.4"],
    "10.0.1.6":  ["10.0.1.7", "10.0.1.8"],
    "10.0.1.7":  ["10.0.1.6", "10.0.1.8"],
    "10.0.1.8":  ["10.0.1.6", "10.0.1.7"],
    "10.0.1.9":  ["10.0.1.10", "10.0.1.15"],
    "10.0.1.10": ["10.0.1.9", "10.0.1.11"],
    "10.0.1.11": ["10.0.1.10", "10.0.1.12"],
    "10.0.1.12": ["10.0.1.11", "10.0.1.13"],
    "10.0.1.13": ["10.0.1.12", "10.0.1.14"],
    "10.0.1.14": ["10.0.1.13", "10.0.1.15"],
    "10.0.1.15": ["10.0.1.14", "10.0.1.9"],
}
LAT_TARGETS = ["10.0.1.3", "10.0.1.11", "10.0.1.14"]

START = datetime(2025, 3, 1)
END = datetime(2025, 3, 8)
T_TUNNEL = datetime(2025, 3, 5, 2, 15)
T_BEACON = datetime(2025, 3, 5, 2, 17)
T_LATERAL = datetime(2025, 3, 6, 9, 30)
T_EXFIL = datetime(2025, 3, 7, 14, 0)

nf, dn = [], []
fmt = "%Y-%m-%dT%H:%M:%SZ"

# Normal traffic
for day in range(7):
    for hour in range(24):
        h = START + timedelta(days=day, hours=hour)
        for host in HOSTS:
            for _ in range(random.randint(4, 8)):
                m, s = random.randint(0, 59), random.randint(0, 59)
                ts = (h + timedelta(minutes=m, seconds=s)).strftime(fmt)
                port = random.choices([443, 80, 53, 8080], weights=[60, 25, 10, 5])[0]
                nf.append({"timestamp": ts, "src_ip": host, "dst_ip": random.choice(EXT_IPS),
                    "src_port": random.randint(49152, 65535), "dst_port": port,
                    "protocol": "UDP" if port == 53 else "TCP",
                    "bytes_sent": random.randint(500, 50000),
                    "bytes_received": random.randint(1000, 200000),
                    "packets": random.randint(5, 200),
                    "duration_ms": random.randint(100, 120000)})

            peers = PEERS[host]
            for peer in random.sample(peers, random.randint(1, len(peers))):
                m, s = random.randint(0, 59), random.randint(0, 59)
                ts = (h + timedelta(minutes=m, seconds=s)).strftime(fmt)
                nf.append({"timestamp": ts, "src_ip": host, "dst_ip": peer,
                    "src_port": random.randint(49152, 65535),
                    "dst_port": random.choice([445, 3389, 22, 8080]),
                    "protocol": "TCP",
                    "bytes_sent": random.randint(200, 20000),
                    "bytes_received": random.randint(200, 20000),
                    "packets": random.randint(3, 50),
                    "duration_ms": random.randint(50, 30000)})

            for _ in range(random.randint(1, 3)):
                m, s = random.randint(0, 59), random.randint(0, 59)
                ts = (h + timedelta(minutes=m, seconds=s)).strftime(fmt)
                dn.append({"timestamp": ts, "src_ip": host,
                    "query_domain": random.choice(DOMAINS),
                    "query_type": "A", "response_code": "NOERROR"})

# C2 Beaconing
t = T_BEACON
while t < END:
    nf.append({"timestamp": t.strftime(fmt), "src_ip": COMPROMISED, "dst_ip": C2_SERVER,
        "src_port": random.randint(49152, 65535), "dst_port": 443, "protocol": "TCP",
        "bytes_sent": random.randint(200, 1500), "bytes_received": random.randint(500, 3000),
        "packets": random.randint(5, 20), "duration_ms": random.randint(500, 5000)})
    t += timedelta(seconds=300 + random.uniform(-5, 5))

# DNS Tunneling
t = T_TUNNEL
while t < END:
    sub = ''.join(random.choices('0123456789abcdef', k=30))
    dn.append({"timestamp": t.strftime(fmt), "src_ip": COMPROMISED,
        "query_domain": f"{sub}.{TUNNEL_BASE}", "query_type": "TXT",
        "response_code": "NOERROR"})
    t += timedelta(seconds=random.randint(200, 400))

# Lateral movement
for target in LAT_TARGETS:
    nf.append({"timestamp": T_LATERAL.strftime(fmt),
        "src_ip": COMPROMISED, "dst_ip": target,
        "src_port": random.randint(49152, 65535), "dst_port": 445, "protocol": "TCP",
        "bytes_sent": random.randint(5000, 50000),
        "bytes_received": random.randint(10000, 100000),
        "packets": random.randint(20, 200), "duration_ms": random.randint(5000, 60000)})
    for _ in range(9):
        dt = timedelta(hours=random.uniform(0.5, 24))
        tt = T_LATERAL + dt
        if tt >= END: continue
        nf.append({"timestamp": tt.strftime(fmt),
            "src_ip": COMPROMISED, "dst_ip": target,
            "src_port": random.randint(49152, 65535),
            "dst_port": random.choice([445, 3389, 22]), "protocol": "TCP",
            "bytes_sent": random.randint(5000, 50000),
            "bytes_received": random.randint(10000, 100000),
            "packets": random.randint(20, 200), "duration_ms": random.randint(5000, 60000)})

# Exfiltration
nf.append({"timestamp": T_EXFIL.strftime(fmt),
    "src_ip": COMPROMISED, "dst_ip": EXFIL_DST,
    "src_port": random.randint(49152, 65535), "dst_port": 443, "protocol": "TCP",
    "bytes_sent": 25_000_000, "bytes_received": random.randint(500, 5000),
    "packets": random.randint(5000, 20000), "duration_ms": random.randint(30000, 120000)})
for _ in range(19):
    tt = T_EXFIL + timedelta(minutes=random.uniform(1, 120))
    nf.append({"timestamp": tt.strftime(fmt),
        "src_ip": COMPROMISED, "dst_ip": EXFIL_DST,
        "src_port": random.randint(49152, 65535), "dst_port": 443, "protocol": "TCP",
        "bytes_sent": random.randint(20_000_000, 30_000_000),
        "bytes_received": random.randint(500, 5000),
        "packets": random.randint(5000, 20000), "duration_ms": random.randint(30000, 120000)})

nf.sort(key=lambda x: x["timestamp"])
dn.sort(key=lambda x: x["timestamp"])

nf_fields = ["timestamp","src_ip","dst_ip","src_port","dst_port","protocol","bytes_sent","bytes_received","packets","duration_ms"]
with open("netflow.csv", "w", newline="") as f:
    csv.DictWriter(f, fieldnames=nf_fields).writeheader()
    csv.DictWriter(f, fieldnames=nf_fields).writerows(nf)

dn_fields = ["timestamp","src_ip","query_domain","query_type","response_code"]
with open("dns_queries.csv", "w", newline="") as f:
    csv.DictWriter(f, fieldnames=dn_fields).writeheader()
    csv.DictWriter(f, fieldnames=dn_fields).writerows(dn)

config = {
    "internal_subnet": "10.0.1.0/24",
    "baseline_start": "2025-03-01T00:00:00Z",
    "baseline_end": "2025-03-04T23:59:59Z",
    "investigation_start": "2025-03-05T00:00:00Z",
    "investigation_end": "2025-03-07T23:59:59Z",
    "entropy_threshold": 3.5,
    "beaconing_jitter_threshold": 0.1,
    "mad_zscore_threshold": 3.5,
    "min_beaconing_connections": 20,
}
with open("investigation_config.json", "w") as f:
    json.dump(config, f, indent=2)

print(f"Netflow: {len(nf)} rows, DNS: {len(dn)} rows")
