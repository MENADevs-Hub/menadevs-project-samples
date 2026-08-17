---
name: anomaly-detection
description: MAD-based modified z-score for detecting traffic volume anomalies. Use when comparing current traffic to a baseline period to find hosts sending abnormally large amounts of data. The modified z-score uses median and MAD instead of mean and standard deviation, making it robust to outliers. A z-score above 3.5 is considered anomalous.
---

# Traffic Anomaly Detection with Modified Z-Score

## Why MAD Instead of Standard Deviation

Standard z-scores use mean and std, which are sensitive to outliers. MAD (median absolute deviation) is a robust alternative. One extreme value won't skew your baseline the way it would with standard deviation.

## Computing MAD and Modified Z-Score

```python
import numpy as np

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
```

The constant 0.6745 is the 0.75th quantile of the standard normal distribution. It makes the modified z-score comparable to a standard z-score when the data is normally distributed.

## Detection Workflow

1. Aggregate bytes_sent per host per hour across all data
2. Split into baseline and investigation periods using config timestamps
3. For each host, compute median and MAD from baseline hourly values
4. Score each investigation hour using the modified z-score formula
5. Flag hours where z-score exceeds the threshold (typically 3.5)
6. The host+hour with the highest z-score is the strongest exfiltration candidate
7. To find the destination, look at the raw flows for that host during that peak hour and find which destination IP received the most bytes

## Example

```python
baseline_bytes = hourly[hourly["hour"] <= config["baseline_end"]]
investigation_bytes = hourly[hourly["hour"] >= config["investigation_start"]]

for host in hosts:
    bh = baseline_bytes[baseline_bytes["src_ip"] == host]["bytes_sent"]
    median_b = float(bh.median())
    mad = float((bh - median_b).abs().median())
    if mad == 0:
        mad = 1.0

    ih = investigation_bytes[investigation_bytes["src_ip"] == host]
    for _, row in ih.iterrows():
        z = 0.6745 * (row["bytes_sent"] - median_b) / mad
        if z > threshold:
            # flag this host+hour as anomalous

## Report Output

The `exfiltration` section of the report must use these exact field names:

```python
{
    "host": str(host),
    "destination": str(top_dst_ip),         # external IP that received the most bytes in the peak hour
    "peak_hour": str(row["hour"]),           # the anomalous hour bucket, e.g. "2025-03-07T15:00:00Z"
    "bytes_sent": int(row["bytes_sent"]),
    "mad_z_score": round(float(z), 1),
    "baseline_median_bytes_per_hour": int(round(median_b, 0)),
}
```
```
