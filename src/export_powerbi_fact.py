"""Power BI Fact Transactions Table Exporter.

Constructs an optimized fact table (fact_transactions.csv) for Power BI Desktop
consumption without incurring the memory and rendering overhead of importing all
6.36 million rows.

Sampling Methodology & Row Composition:
    - 100% of Alert & Fraud Transactions: All transactions where is_alert = 1 OR isFraud = 1
      are preserved exhaustively (1,085,626 rows, capturing 100% of all 8,213 fraud events,
      including all 17 false-negative missed frauds).
    - Stratified Normal Sample: Exactly 50,000 legitimate, unalerted transactions
      (is_alert = 0 AND isFraud = 0) are sampled via stratified sampling across transaction
      types with fixed random seed 42.
    - Dropped Columns: High-cardinality raw balance columns (oldbalanceOrg, newbalanceOrig,
      oldbalanceDest, newbalanceDest, errOrig, errDest) are excluded, drastically shrinking
      file size while retaining all behavioral rule flags and risk scores.

CRITICAL KPI WARNING FOR POWER BI MODELING:
    Because unalerted legitimate transactions ('Normal sample') are deliberately downsampled
    to 50,000 rows to ensure fast interactive performance, Power BI measures representing
    ENTERPRISE-WIDE TOTALS (e.g. Total Transactions = 6.36M, Global Alert Rate = 17.06%,
    Global Fraud Rate = 0.129%) MUST BE SOURCED FROM DEDICATED AGGREGATE SUMMARY TABLES
    or explicit DAX scalar parameters, NOT from COUNTRows(fact_transactions).
"""

from pathlib import Path
import sys
import time

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config

FACT_COLUMNS = [
    "txn_id",
    "step",
    "day",
    "hour",
    "type",
    "amount",
    "amount_band",
    "nameOrig",
    "nameDest",
    "rule_emptied",
    "rule_large_amount",
    "rule_velocity",
    "rule_transfer_then_cashout",
    "rule_mule_dest",
    "rule_dest_unchanged",
    "rule_balance_error",
    "alert_score",
    "anomaly_score_pct",
    "ml_flag",
    "rule_alert",
    "alert_source",
    "combo_score",
    "risk_band",
    "is_alert",
    "isFraud",
    "outcome",
    "row_origin",
]


def export_powerbi_fact(
    master_alerts_path: Path = config.MASTER_ALERTS_PARQUET,
    output_csv_path: Path = config.FACT_TRANSACTIONS_CSV,
    normal_sample_size: int = 50_000,
    random_seed: int = config.RANDOM_SEED,
) -> pd.DataFrame:
    """Build and export fact_transactions.csv for Power BI Desktop.

    Args:
        master_alerts_path: Path to master_alerts.parquet.
        output_csv_path: Path to write fact_transactions.csv.
        normal_sample_size: Number of normal (is_alert=0 and isFraud=0) rows to sample.
        random_seed: Random seed for stratified sampling.

    Returns:
        pd.DataFrame: The exported fact DataFrame.
    """
    t_start = time.perf_counter()
    print("==================================================")
    print("Exporting Power BI Fact Table (fact_transactions.csv)")
    print("==================================================")

    # 1. Load dataset
    print(f"\n[1/4] Loading master alerts dataset from {master_alerts_path.name}...")
    df = pd.read_parquet(master_alerts_path)
    print(f"  - Loaded {len(df):,} transactions ({len(df.columns)} columns).")

    # 2. Filter Alert & Fraud universe (100% preservation)
    print("\n[2/4] Isolating all alert and fraud transactions...")
    alert_or_fraud_mask = (df["is_alert"] == 1) | (df[config.COL_IS_FRAUD] == 1)
    alert_fraud_df = df[alert_or_fraud_mask].copy()
    alert_fraud_df["row_origin"] = "Alert/Fraud"

    n_alert_fraud = len(alert_fraud_df)
    n_fraud_in_alert_subset = int(alert_fraud_df[config.COL_IS_FRAUD].sum())
    print(f"  - Alert/Fraud rows: {n_alert_fraud:,} (Fraud count: {n_fraud_in_alert_subset:,} / {config.EXPECTED_FRAUD:,})")
    assert n_fraud_in_alert_subset == config.EXPECTED_FRAUD, (
        f"Missing fraud rows: expected {config.EXPECTED_FRAUD}, got {n_fraud_in_alert_subset}"
    )

    # 3. Stratified sampling of normal (unalerted, legitimate) rows
    print(f"\n[3/4] Performing stratified sampling of {normal_sample_size:,} normal rows (seed {random_seed})...")
    normal_mask = (df["is_alert"] == 0) & (df[config.COL_IS_FRAUD] == 0)
    normal_df = df[normal_mask].copy()
    n_normal_available = len(normal_df)
    print(f"  - Available normal legitimate transactions: {n_normal_available:,}")

    normal_sample, _ = train_test_split(
        normal_df,
        train_size=normal_sample_size,
        stratify=normal_df[config.COL_TYPE],
        random_state=random_seed,
    )
    normal_sample["row_origin"] = "Normal sample"
    print(f"  - Sampled {len(normal_sample):,} rows stratified across all payment types.")

    # 4. Concatenate and sort by txn_id
    print("\n[4/4] Assembling, formatting, and serializing fact table...")
    fact_df = pd.concat([alert_fraud_df, normal_sample], ignore_index=True)
    fact_df = fact_df.sort_values(by=config.COL_TXN_ID).reset_index(drop=True)

    # Format numeric precision
    fact_df["amount"] = fact_df["amount"].round(2)
    fact_df["anomaly_score_pct"] = fact_df["anomaly_score_pct"].round(2)
    fact_df["combo_score"] = fact_df["combo_score"].round(2)

    # Column subset enforcement
    fact_df = fact_df[FACT_COLUMNS]

    # Acceptance Assertions
    total_fact_rows = len(fact_df)
    expected_total_rows = n_alert_fraud + normal_sample_size
    assert total_fact_rows == expected_total_rows, (
        f"Row count mismatch: expected {expected_total_rows:,}, got {total_fact_rows:,}"
    )

    total_fraud_in_fact = int(fact_df[config.COL_IS_FRAUD].sum())
    assert total_fraud_in_fact == config.EXPECTED_FRAUD, (
        f"Fraud row count assertion failed: expected {config.EXPECTED_FRAUD}, got {total_fraud_in_fact}"
    )

    nan_count = int(fact_df.isna().sum().sum())
    assert nan_count == 0, f"Detected {nan_count:,} NaN values in fact table"

    # Export CSV
    output_csv_path.parent.mkdir(parents=True, exist_ok=True)
    fact_df.to_csv(output_csv_path, index=False, encoding="utf-8")

    file_size_bytes = output_csv_path.stat().st_size
    file_size_mb = file_size_bytes / (1024 * 1024)

    # Operational summary and prominent KPI advisory
    print("\n" + "=" * 75)
    print(f"{'Power BI Fact Table Generation Summary':^75}")
    print("=" * 75)
    print(f"Output File Path:        {output_csv_path.relative_to(config.PROJECT_ROOT)}")
    print(f"Total Rows in Fact:      {total_fact_rows:,}")
    print(f"  - Alert / Fraud Rows:  {n_alert_fraud:>9,} (100% of all alerts and frauds)")
    print(f"  - Normal Sample Rows:  {normal_sample_size:>9,} (Stratified legitimate sample)")
    print(f"Total Fraud Rows:        {total_fraud_in_fact:>9,} (Asserted: 100% of {config.EXPECTED_FRAUD:,} preserved)")
    print(f"Total Columns:           {len(fact_df.columns)}")
    print(f"File Size on Disk:       {file_size_mb:.2f} MB ({file_size_bytes:,} bytes)")
    print("-" * 75)
    print("CRITICAL POWER BI MODELING ADVISORY:")
    print("  * Normal legitimate rows are sampled (50,000 rows) to keep the fact table")
    print("    manageable (~130-150 MB) for Power BI Desktop.")
    print("  * Enterprise-wide aggregate KPIs (such as Total Transactions = 6,362,620,")
    print("    Global Alert Rate = 17.06%, Overall Fraud Rate = 0.129%) MUST be sourced")
    print("    from pre-computed aggregate tables or DAX scalar parameters,")
    print("    NOT from COUNTROWS(fact_transactions)!")
    print("=" * 75)

    print(f"\nExport completed successfully in {time.perf_counter() - t_start:.2f}s.")
    return fact_df


def main() -> None:
    """CLI execution entrypoint."""
    export_powerbi_fact()


if __name__ == "__main__":
    main()
