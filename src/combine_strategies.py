"""Hybrid Strategy Combination Module (Phase 4).

Combines DuckDB deterministic rule flags and unsupervised Isolation Forest anomaly
scores into an integrated hybrid decision layer:
1. alert_source: "Both", "Rule only", "ML only", "None"
2. combo_or: Logical OR alert flag (rule_alert OR ml_flag)
3. combo_and: Logical AND alert flag (rule_alert AND ml_flag)
4. combo_score: Weighted composite risk score [0 - 100]
5. risk_band: "Critical", "High", "Medium", "Low"

Overwrites data/outputs/master_alerts.parquet with the enriched schema.
"""

from pathlib import Path
import sys
import time

import numpy as np
import pandas as pd

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config

ALLOWED_ALERT_SOURCES = {"Both", "Rule only", "ML only", "None"}
ALLOWED_RISK_BANDS = ["Critical", "High", "Medium", "Low"]


def combine_strategies(save_output: bool = True) -> pd.DataFrame:
    """Extend master_alerts with hybrid strategy combination columns.

    Args:
        save_output: Whether to overwrite master_alerts.parquet on disk.

    Returns:
        pd.DataFrame: Enriched master alerts DataFrame.
    """
    t_start = time.perf_counter()
    print("==================================================")
    print("Combining Rule & ML Strategies (Phase 4)")
    print("==================================================")

    # 1. Load master_alerts.parquet
    print(f"\n[1/4] Loading master alerts from: {config.MASTER_ALERTS_PARQUET.relative_to(config.PROJECT_ROOT)}")
    t0 = time.perf_counter()
    df = pd.read_parquet(config.MASTER_ALERTS_PARQUET)
    print(f"  - Loaded {len(df):,} rows with {len(df.columns)} columns in {time.perf_counter() - t0:.2f}s.")

    # 2. Compute hybrid strategy columns
    print("\n[2/4] Engineering hybrid strategy combination features...")
    t0 = time.perf_counter()

    # alert_source (string)
    conditions = [
        (df["rule_alert"] == 1) & (df["ml_flag"] == 1),
        (df["rule_alert"] == 1) & (df["ml_flag"] == 0),
        (df["rule_alert"] == 0) & (df["ml_flag"] == 1),
    ]
    choices = ["Both", "Rule only", "ML only"]
    df["alert_source"] = np.select(conditions, choices, default="None")

    # combo_or: rule_alert OR ml_flag (int8)
    df["combo_or"] = ((df["rule_alert"] == 1) | (df["ml_flag"] == 1)).astype(np.int8)

    # combo_and: rule_alert AND ml_flag (int8)
    df["combo_and"] = ((df["rule_alert"] == 1) & (df["ml_flag"] == 1)).astype(np.int8)

    # combo_score: 0.5 * (alert_score / 7 * 100) + 0.5 * anomaly_score_pct, rounded to 2 decimals
    # alert_score ranges from 0 to 7; anomaly_score_pct ranges from 0 to 100
    rule_score_scaled = (df["alert_score"].astype(float) / 7.0) * 100.0
    composite_raw = 0.5 * rule_score_scaled + 0.5 * df["anomaly_score_pct"].astype(float)
    df["combo_score"] = np.round(composite_raw, 2)

    # risk_band: "Critical" >= 80, "High" >= 60, "Medium" >= 40, "Low" otherwise
    band_conditions = [
        df["combo_score"] >= 80.0,
        df["combo_score"] >= 60.0,
        df["combo_score"] >= 40.0,
    ]
    band_choices = ["Critical", "High", "Medium"]
    df["risk_band"] = np.select(band_conditions, band_choices, default="Low")

    print(f"  - New columns engineered in {time.perf_counter() - t0:.2f}s.")

    # 3. Validation Assertions
    print("\n[3/4] Validating schema constraints and data integrity...")

    # Check alert_source unique values
    unique_sources = set(df["alert_source"].unique())
    assert unique_sources == ALLOWED_ALERT_SOURCES, (
        f"Unexpected alert_source values: {unique_sources} (expected {ALLOWED_ALERT_SOURCES})"
    )
    print(f"  --> Assertion PASSED: alert_source contains exactly the 4 allowed values: {sorted(list(ALLOWED_ALERT_SOURCES))}")

    # Check no NaN values anywhere in the dataframe
    nan_count = int(df.isna().sum().sum())
    assert nan_count == 0, f"Detected {nan_count:,} NaN values in enriched master_alerts!"
    print(f"  --> Assertion PASSED: Zero null/NaN values across all {len(df.columns)} columns")

    # Check row count preserved
    assert len(df) == config.EXPECTED_ROWS, f"Row count changed: {len(df)} != {config.EXPECTED_ROWS}"
    assert int(df[config.COL_IS_FRAUD].sum()) == config.EXPECTED_FRAUD, "Fraud count changed"
    print(f"  --> Assertion PASSED: Row count ({len(df):,}) and fraud count ({config.EXPECTED_FRAUD:,}) preserved")

    # 4. Display Distributions
    print("\n[4/4] Printing Distribution Reports:")

    # alert_source distribution
    print("\n" + "=" * 68)
    print(f"{'Distribution of alert_source':^68}")
    print("=" * 68)
    print(f"{'Alert Source':<15} | {'Rows':>12} | {'Share':>9} | {'Fraud Rows':>11} | {'Fraud Rate':>10}")
    print("-" * 68)

    order_sources = ["Both", "ML only", "Rule only", "None"]
    for src in order_sources:
        sub = df[df["alert_source"] == src]
        rows = len(sub)
        fraud = int(sub[config.COL_IS_FRAUD].sum())
        rate = (fraud / rows * 100.0) if rows > 0 else 0.0
        share = (rows / len(df)) * 100.0
        print(f"{src:<15} | {rows:>12,} | {share:>8.4f}% | {fraud:>11,} | {rate:>9.4f}%")
    print("=" * 68)

    # risk_band distribution
    print("\n" + "=" * 68)
    print(f"{'Distribution of risk_band':^68}")
    print("=" * 68)
    print(f"{'Risk Band':<15} | {'Rows':>12} | {'Share':>9} | {'Fraud Rows':>11} | {'Fraud Rate':>10}")
    print("-" * 68)

    for band in ALLOWED_RISK_BANDS:
        sub = df[df["risk_band"] == band]
        rows = len(sub)
        fraud = int(sub[config.COL_IS_FRAUD].sum())
        rate = (fraud / rows * 100.0) if rows > 0 else 0.0
        share = (rows / len(df)) * 100.0
        print(f"{band:<15} | {rows:>12,} | {share:>8.4f}% | {fraud:>11,} | {rate:>9.4f}%")
    print("=" * 68)

    # 5. Overwrite master_alerts.parquet
    if save_output:
        config.OUTPUTS_DATA_DIR.mkdir(parents=True, exist_ok=True)
        df.to_parquet(config.MASTER_ALERTS_PARQUET, compression="snappy", index=False)
        size_mb = config.MASTER_ALERTS_PARQUET.stat().st_size / (1024 * 1024)
        print(f"\nEnriched master alerts overwritten at: {config.MASTER_ALERTS_PARQUET.relative_to(config.PROJECT_ROOT)} ({size_mb:.2f} MB)")

    elapsed = time.perf_counter() - t_start
    print(f"Strategy combination completed successfully in {elapsed:.2f}s.")
    return df


def main() -> None:
    """CLI execution entrypoint."""
    combine_strategies(save_output=True)


if __name__ == "__main__":
    main()
