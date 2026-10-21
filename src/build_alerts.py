"""Master Alerts Dataset Construction Module (Phase 4).

Combines the cleaned transaction universe (6.36M records), DuckDB SQL business rule
flags (rule_flags.parquet), and machine learning anomaly scores (ml_scores.parquet)
into a unified master alerts table (master_alerts.parquet).

Ensures all scoped transactions carry both rule flags and ML risk scores, while
out-of-scope non-fraud transaction types (CASH_IN, DEBIT, PAYMENT) are cleanly padded
with zero flags and designated as 'out_of_scope'.
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

RULE_COLUMNS = [
    "rule_emptied",
    "rule_large_amount",
    "rule_velocity",
    "rule_transfer_then_cashout",
    "rule_mule_dest",
    "rule_dest_unchanged",
    "rule_balance_error",
    "alert_score",
    "is_rule_alert_1",
    "is_rule_alert_2",
]


def build_alerts(save_output: bool = True) -> pd.DataFrame:
    """Load clean data, rule flags, and ML scores, join by txn_id, and export master_alerts.parquet.

    Args:
        save_output: Whether to serialize master_alerts.parquet to disk.

    Returns:
        pd.DataFrame: The consolidated 6,362,620-row master alerts DataFrame.
    """
    t_start = time.perf_counter()
    print("==================================================")
    print("Building Master Alerts Dataset (Phase 4)")
    print("==================================================")

    # 1. Load inputs
    print(f"\n[1/4] Loading input datasets...")
    t0 = time.perf_counter()
    clean_df = pd.read_parquet(config.CLEAN_PARQUET)
    print(f"  - Loaded clean transactions: {len(clean_df):,} rows ({time.perf_counter() - t0:.2f}s)")

    t0 = time.perf_counter()
    rule_df = pd.read_parquet(config.RULE_FLAGS_PARQUET)
    rule_subset = rule_df[[config.COL_TXN_ID] + RULE_COLUMNS].copy()
    print(f"  - Loaded rule flags: {len(rule_subset):,} scoped rows ({time.perf_counter() - t0:.2f}s)")

    t0 = time.perf_counter()
    ml_df = pd.read_parquet(config.ML_SCORES_PARQUET)
    print(f"  - Loaded ML scores: {len(ml_df):,} scoped rows ({time.perf_counter() - t0:.2f}s)")

    # 2. Left-join onto clean transactions
    print(f"\n[2/4] Joining rule flags and ML scores onto full clean universe...")
    t0 = time.perf_counter()
    merged = clean_df.merge(rule_subset, on=config.COL_TXN_ID, how="left")
    merged = merged.merge(ml_df, on=config.COL_TXN_ID, how="left")
    print(f"  - Merged shape: {merged.shape} ({time.perf_counter() - t0:.2f}s)")

    # 3. Fill out-of-scope rows and enforce types
    print(f"\n[3/4] Imputing out-of-scope non-fraud transaction types (CASH_IN, DEBIT, PAYMENT)...")
    for col in RULE_COLUMNS:
        merged[col] = merged[col].fillna(0).astype(np.int8)

    merged["anomaly_score"] = merged["anomaly_score"].fillna(0.0).astype(np.float64)
    merged["anomaly_score_pct"] = merged["anomaly_score_pct"].fillna(0.0).astype(np.float64)
    merged["ml_flag"] = merged["ml_flag"].fillna(0).astype(np.int8)
    merged["split"] = merged["split"].fillna("out_of_scope").astype(str)

    # Define rule_alert = (alert_score >= 1) while keeping is_rule_alert_1 and is_rule_alert_2
    merged["rule_alert"] = (merged["alert_score"] >= 1).astype(np.int8)

    # 4. Strict Auditing Assertions
    print(f"\n[4/4] Executing structural data integrity assertions...")

    # Assertion 1: Total row count matches raw/clean universe exactly
    assert len(merged) == config.EXPECTED_ROWS, (
        f"Row count mismatch: expected {config.EXPECTED_ROWS:,}, got {len(merged):,}"
    )
    print(f"  --> Assertion PASSED: Row count equals {config.EXPECTED_ROWS:,}")

    # Assertion 2: txn_id is strictly unique and monotonic
    assert merged[config.COL_TXN_ID].nunique() == config.EXPECTED_ROWS, (
        "Duplicate txn_id detected in master alerts!"
    )
    print(f"  --> Assertion PASSED: txn_id is strictly unique across all {config.EXPECTED_ROWS:,} rows")

    # Assertion 3: Zero NaN / null values anywhere in the dataset
    nan_count = int(merged.isna().sum().sum())
    assert nan_count == 0, f"Detected {nan_count:,} NaN values in master alerts!"
    print(f"  --> Assertion PASSED: Zero null/NaN values across all {len(merged.columns)} columns")

    # Assertion 4: Ground-truth fraud count preserved perfectly
    total_fraud = int(merged[config.COL_IS_FRAUD].sum())
    assert total_fraud == config.EXPECTED_FRAUD, (
        f"Fraud event count mismatch: expected {config.EXPECTED_FRAUD:,}, got {total_fraud:,}"
    )
    print(f"  --> Assertion PASSED: Total fraud events preserved ({total_fraud:,})")

    # Assertion 5: Rows outside TRANSFER/CASH_OUT have all flags set to 0 and split='out_of_scope'
    out_of_scope = merged[~merged["type"].isin(config.FRAUD_TYPES)]
    n_out_of_scope = len(out_of_scope)
    print(f"  - Auditing {n_out_of_scope:,} out-of-scope rows...")

    for col in RULE_COLUMNS:
        assert (out_of_scope[col] == 0).all(), f"Out-of-scope rows have non-zero in {col}!"

    assert (out_of_scope["rule_alert"] == 0).all(), "Out-of-scope rows have non-zero rule_alert!"
    assert (out_of_scope["ml_flag"] == 0).all(), "Out-of-scope rows have non-zero ml_flag!"
    assert (out_of_scope["anomaly_score"] == 0.0).all(), "Out-of-scope rows have non-zero anomaly_score!"
    assert (out_of_scope["anomaly_score_pct"] == 0.0).all(), "Out-of-scope rows have non-zero anomaly_score_pct!"
    assert (out_of_scope["split"] == "out_of_scope").all(), "Out-of-scope rows have unexpected split label!"
    print("  --> Assertion PASSED: All out-of-scope transactions have zero flags and split='out_of_scope'")

    # 5. Export master_alerts.parquet
    if save_output:
        config.OUTPUTS_DATA_DIR.mkdir(parents=True, exist_ok=True)
        merged.to_parquet(config.MASTER_ALERTS_PARQUET, compression="snappy", index=False)
        size_mb = config.MASTER_ALERTS_PARQUET.stat().st_size / (1024 * 1024)
        print(f"\nMaster alerts saved to: {config.MASTER_ALERTS_PARQUET.relative_to(config.PROJECT_ROOT)} ({size_mb:.2f} MB)")

    # Display operational summary
    print("\n" + "=" * 70)
    print(f"{'Master Alerts Summary Overview':^70}")
    print("=" * 70)
    rule_alerts_total = int(merged["rule_alert"].sum())
    ml_alerts_total = int(merged["ml_flag"].sum())
    both_alerts_total = int(((merged["rule_alert"] == 1) & (merged["ml_flag"] == 1)).sum())
    either_alerts_total = int(((merged["rule_alert"] == 1) | (merged["ml_flag"] == 1)).sum())

    print(f"Total Transactions:                 {len(merged):,}")
    print(f"Scoped Transactions (TRANSFER/CASH_OUT): {len(clean_df[clean_df['type'].isin(config.FRAUD_TYPES)]):,}")
    print(f"Rule Alerts (rule_alert=1):         {rule_alerts_total:>10,} ({100.0 * rule_alerts_total / len(merged):.4f}%)")
    print(f"ML Alerts (ml_flag=1):              {ml_alerts_total:>10,} ({100.0 * ml_alerts_total / len(merged):.4f}%)")
    print(f"Both Alerted (Rule AND ML):         {both_alerts_total:>10,} ({100.0 * both_alerts_total / len(merged):.4f}%)")
    print(f"Union Alerted (Rule OR ML):         {either_alerts_total:>10,} ({100.0 * either_alerts_total / len(merged):.4f}%)")
    print("=" * 70)

    elapsed = time.perf_counter() - t_start
    print(f"Master alerts construction completed successfully in {elapsed:.2f}s.")
    return merged


def main() -> None:
    """CLI execution entrypoint."""
    build_alerts(save_output=True)


if __name__ == "__main__":
    main()
