"""Final Alerts Dataset and Production Metrics Generation (Phase 4).

Enriches master_alerts.parquet with official dashboard alert indicators, confusion
matrix outcome flags, and transactional amount bands. Computes and exports
the production monitoring metrics payload to reports/16_final_metrics.json.

Operational Decision:
    Combined OR (combo_or) is adopted as the official production alert definition
    (ALERT_DEFINITION = 'combo_or' in config.py) to provide maximal fraud recall
    (99.79%, 8,196 / 8,213 frauds detected, missing only 17), serving as an exhaustive
    supervisory safety net across all transaction streams.
"""

from pathlib import Path
import json
import sys
import time
from typing import Any

import numpy as np
import pandas as pd

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config
from src.evaluation import evaluate_binary

AMOUNT_BINS = [-np.inf, 1000.0, 10000.0, 100000.0, 1000000.0, np.inf]
AMOUNT_LABELS = ["<1K", "1K-10K", "10K-100K", "100K-1M", ">1M"]


def compute_final_alerts(
    master_alerts_path: Path = config.MASTER_ALERTS_PARQUET,
    metrics_output_path: Path = config.FINAL_METRICS_JSON,
    save_output: bool = True,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Enrich master_alerts.parquet with final alert flags and export 16_final_metrics.json.

    Args:
        master_alerts_path: Path to master_alerts.parquet.
        metrics_output_path: Destination path for 16_final_metrics.json.
        save_output: Whether to persist enriched DataFrame and metrics to disk.

    Returns:
        tuple[pd.DataFrame, dict[str, Any]]: (enriched_df, metrics_dict)
    """
    t_start = time.perf_counter()
    print("==================================================")
    print("Enriching Final Master Alerts & Production Metrics")
    print("==================================================")

    # 1. Load dataset
    print(f"\n[1/4] Loading master alerts dataset from {master_alerts_path.name}...")
    df = pd.read_parquet(master_alerts_path)
    print(f"  - Loaded {len(df):,} transactions ({len(df.columns)} columns).")

    # 2. Add is_alert based on official ALERT_DEFINITION (combo_or)
    print(f"\n[2/4] Applying official alert definition: {config.ALERT_DEFINITION}...")
    if config.ALERT_DEFINITION not in df.columns:
        raise KeyError(
            f"Alert definition column '{config.ALERT_DEFINITION}' not found in master alerts dataset."
        )
    df["is_alert"] = df[config.ALERT_DEFINITION].astype(np.int8)

    # 3. Add confusion outcome flags and outcome string
    print("  - Computing confusion outcome flags (tp_flag, fp_flag, fn_flag, tn_flag)...")
    is_alert = df["is_alert"] == 1
    is_fraud = df[config.COL_IS_FRAUD] == 1

    df["tp_flag"] = (is_alert & is_fraud).astype(np.int8)
    df["fp_flag"] = (is_alert & ~is_fraud).astype(np.int8)
    df["fn_flag"] = (~is_alert & is_fraud).astype(np.int8)
    df["tn_flag"] = (~is_alert & ~is_fraud).astype(np.int8)

    outcome_conditions = [
        df["tp_flag"] == 1,
        df["fp_flag"] == 1,
        df["fn_flag"] == 1,
        df["tn_flag"] == 1,
    ]
    outcome_choices = [
        "True Positive",
        "False Positive",
        "False Negative",
        "True Negative",
    ]
    df["outcome"] = np.select(outcome_conditions, outcome_choices, default="Unknown").astype(str)

    # 4. Add amount_band
    print("  - Discretizing transaction amount into standard amount bands...")
    df["amount_band"] = pd.cut(
        df[config.COL_AMOUNT],
        bins=AMOUNT_BINS,
        labels=AMOUNT_LABELS,
        right=False,
    ).astype(str)

    # Structural Integrity Assertions
    print("\n[3/4] Running data integrity and outcome completeness checks...")
    assert len(df) == config.EXPECTED_ROWS, (
        f"Row count mismatch: expected {config.EXPECTED_ROWS:,}, got {len(df):,}"
    )
    assert int(df.isna().sum().sum()) == 0, "Detected nulls/NaNs in enriched dataset"
    assert (df["outcome"] == "Unknown").sum() == 0, "Detected unknown outcome values"
    assert set(df["outcome"].unique()) == set(outcome_choices), "Unexpected outcome categories"
    assert set(df["amount_band"].unique()) == set(AMOUNT_LABELS), "Unexpected amount bands"

    # Outcome sum equals total transactions
    sum_flags = int(df["tp_flag"].sum() + df["fp_flag"].sum() + df["fn_flag"].sum() + df["tn_flag"].sum())
    assert sum_flags == config.EXPECTED_ROWS, (
        f"Sum of confusion flags ({sum_flags:,}) does not equal total rows ({config.EXPECTED_ROWS:,})"
    )
    print("  --> Integrity assertions PASSED: 0 nulls, exact row count, exhaustive partitions.")

    # 5. Compute Production Metrics Payload
    print("\n[4/4] Computing final monitoring evaluation metrics...")
    eval_res = evaluate_binary(df[config.COL_IS_FRAUD], df["is_alert"])

    total_transactions = len(df)
    total_alerts = int(df["is_alert"].sum())
    total_flagged_value = float(df.loc[df["is_alert"] == 1, config.COL_AMOUNT].sum())
    fraud_count = int(df[config.COL_IS_FRAUD].sum())
    overall_fraud_rate = float(fraud_count / total_transactions)

    tp = int(df["tp_flag"].sum())
    fp = int(df["fp_flag"].sum())
    fn = int(df["fn_flag"].sum())
    tn = int(df["tn_flag"].sum())

    # Mandatory Acceptance Criteria Assertions
    assert tp + fp == total_alerts, f"TP ({tp}) + FP ({fp}) != alerts ({total_alerts})"
    assert tp + fn == config.EXPECTED_FRAUD, f"TP ({tp}) + FN ({fn}) != expected fraud ({config.EXPECTED_FRAUD})"
    assert tp + fp + fn + tn == config.EXPECTED_ROWS, f"Total confusion elements != {config.EXPECTED_ROWS}"

    # Fraud rate by type across all 5 transaction types
    fraud_rate_by_type: dict[str, dict[str, Any]] = {}
    zero_fraud_type_count = 0

    for txn_type in sorted(config.ALL_TYPES):
        type_df = df[df[config.COL_TYPE] == txn_type]
        type_txns = len(type_df)
        type_frauds = int(type_df[config.COL_IS_FRAUD].sum())
        type_rate = float(type_frauds / type_txns) if type_txns > 0 else 0.0

        if type_frauds == 0:
            zero_fraud_type_count += 1

        fraud_rate_by_type[txn_type] = {
            "transactions": type_txns,
            "fraud_count": type_frauds,
            "fraud_rate": type_rate,
        }

    # Assert 5 types present, exactly 3 at 0 fraud
    assert len(fraud_rate_by_type) == 5, f"Expected 5 transaction types, got {len(fraud_rate_by_type)}"
    assert zero_fraud_type_count == 3, f"Expected exactly 3 types with 0 fraud, got {zero_fraud_type_count}"

    metrics_payload: dict[str, Any] = {
        "alert_definition": config.ALERT_DEFINITION,
        "total_transactions": total_transactions,
        "total_alerts": total_alerts,
        "total_flagged_value": total_flagged_value,
        "fraud_count": fraud_count,
        "overall_fraud_rate": overall_fraud_rate,
        "TP": tp,
        "FP": fp,
        "FN": fn,
        "TN": tn,
        "precision": float(eval_res["precision"]),
        "recall": float(eval_res["recall"]),
        "FPR": float(eval_res["fpr"]),
        "fpr": float(eval_res["fpr"]),
        "F1": float(eval_res["f1"]),
        "f1": float(eval_res["f1"]),
        "fraud_rate_by_type": fraud_rate_by_type,
    }

    # 6. Save Artifacts
    if save_output:
        print("\nSerializing enriched dataset and metrics payload...")
        df.to_parquet(master_alerts_path, compression="snappy", index=False)
        size_mb = master_alerts_path.stat().st_size / (1024 * 1024)
        print(f"  - Overwrote: {master_alerts_path.relative_to(config.PROJECT_ROOT)} ({size_mb:.2f} MB, {len(df.columns)} columns)")

        metrics_output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(metrics_output_path, "w", encoding="utf-8") as f:
            json.dump(metrics_payload, f, indent=2)
        print(f"  - Saved metrics: {metrics_output_path.relative_to(config.PROJECT_ROOT)}")

    # Print summary
    print("\n" + "=" * 65)
    print(f"{'Final Production Monitoring Metrics':^65}")
    print("=" * 65)
    print(f"Alert Definition:               {config.ALERT_DEFINITION}")
    print(f"Total Transactions:             {total_transactions:,}")
    print(f"Total Alerts Flagged:           {total_alerts:,} ({total_alerts / total_transactions * 100:.2f}%)")
    print(f"Total Flagged Value:            ${total_flagged_value:,.2f}")
    print(f"True Positives (TP):            {tp:>9,}")
    print(f"False Positives (FP):           {fp:>9,}")
    print(f"False Negatives (FN):           {fn:>9,}")
    print(f"True Negatives (TN):            {tn:>9,}")
    print(f"Precision:                      {metrics_payload['precision'] * 100:.4f}%")
    print(f"Recall:                         {metrics_payload['recall'] * 100:.4f}%")
    print(f"False Positive Rate (FPR):      {metrics_payload['FPR'] * 100:.4f}%")
    print(f"F1 Score:                       {metrics_payload['F1']:.4f}")
    print("-" * 65)
    print("Fraud Rate by Transaction Type:")
    for t_name, t_info in fraud_rate_by_type.items():
        print(f"  - {t_name:<10}: {t_info['transactions']:>9,} txns | {t_info['fraud_count']:>5,} frauds | {t_info['fraud_rate'] * 100:.4f}% fraud rate")
    print("=" * 65)
    print(f"Completed in {time.perf_counter() - t_start:.2f}s.")

    return df, metrics_payload


def main() -> None:
    """CLI execution entrypoint."""
    compute_final_alerts()


if __name__ == "__main__":
    main()
