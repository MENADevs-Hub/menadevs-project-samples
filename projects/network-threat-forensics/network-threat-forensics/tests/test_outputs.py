import json
import os
import pytest


def load_report():
    path = "/root/forensic_report.json"
    assert os.path.exists(path), f"Report not found at {path}"
    with open(path) as f:
        return json.load(f)


def normalize_ts(ts):
    """Accept both 'Z' and '+00:00' timezone suffixes."""
    return str(ts).replace("+00:00", "Z")


def test_report_exists_and_valid():
    assert os.path.exists("/root/forensic_report.json")
    report = load_report()
    assert isinstance(report, dict)
    for key in ["compromised_hosts", "c2_server", "exfiltration_destination",
                 "dns_tunneling", "c2_beaconing", "lateral_movement", "exfiltration", "timeline"]:
        assert key in report, f"Missing key: {key}"


def test_compromised_host():
    report = load_report()
    assert "10.0.1.7" in report["compromised_hosts"]


def test_dns_tunneling():
    report = load_report()
    d = report["dns_tunneling"]
    assert d["host"] == "10.0.1.7"
    assert d["tunnel_domain"] == "example.net"
    assert 3.5 < d["mean_subdomain_entropy"] < 4.0, f"Entropy unexpected: {d['mean_subdomain_entropy']}"
    assert 600 <= d["query_count"] <= 660, f"Query count unexpected: {d['query_count']}"
    assert normalize_ts(d["first_seen"]) == "2025-03-05T02:15:00Z"


def test_c2_beaconing_identification():
    report = load_report()
    assert report["c2_server"] == "203.0.113.50"
    b = report["c2_beaconing"]
    assert b["host"] == "10.0.1.7"
    assert b["destination"] == "203.0.113.50"
    assert normalize_ts(b["first_seen"]) == "2025-03-05T02:17:00Z"


def test_c2_beaconing_metrics():
    report = load_report()
    b = report["c2_beaconing"]
    assert 295 <= b["mean_interval_seconds"] <= 305, f"Interval unexpected: {b['mean_interval_seconds']}"
    assert b["jitter_coefficient"] < 0.05, f"Jitter too high: {b['jitter_coefficient']}"
    assert 800 <= b["connection_count"] <= 880, f"Connection count unexpected: {b['connection_count']}"


def test_lateral_movement():
    report = load_report()
    lm = report["lateral_movement"]
    assert lm["source_host"] == "10.0.1.7"
    assert sorted(lm["new_internal_targets"]) == ["10.0.1.11", "10.0.1.14", "10.0.1.3"]
    assert normalize_ts(lm["first_seen"]) == "2025-03-06T09:30:00Z"


def test_exfiltration_identification():
    report = load_report()
    assert report["exfiltration_destination"] == "198.51.100.77"
    e = report["exfiltration"]
    assert e["host"] == "10.0.1.7"
    assert e["destination"] == "198.51.100.77"


def test_exfiltration_stats():
    report = load_report()
    e = report["exfiltration"]
    assert normalize_ts(e["peak_hour"]) == "2025-03-07T15:00:00Z"
    assert 280_000_000 <= e["bytes_sent"] <= 300_000_000, f"Bytes unexpected: {e['bytes_sent']}"
    assert e["mad_z_score"] > 1000, f"Z-score too low: {e['mad_z_score']}"
    assert 140_000 <= e["baseline_median_bytes_per_hour"] <= 170_000


def test_timeline_order_and_events():
    report = load_report()
    tl = report["timeline"]
    assert len(tl) == 4
    timestamps = [e["timestamp"] for e in tl]
    assert timestamps == sorted(timestamps), "Timeline not in chronological order"
    events = {e["event"] for e in tl}
    assert events == {"dns_tunneling_start", "c2_beaconing_start", "lateral_movement_start", "data_exfiltration"}
