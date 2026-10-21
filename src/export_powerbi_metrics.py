"""Power BI Performance Metrics and Confusion Matrix Tables Exporter.

Extracts, transforms, and exports specialized performance metric tables for Power BI:
1. metrics_overall.csv: Single-row high-level KPI card metric summary from reports/16_final_metrics.json
   (re-verified against master_alerts.parquet).
2. metrics_approach.csv: Enterprise-wide strategy comparison matrix across the 6 approaches from
   reports/14_approach_comparison.csv, renaming the simulator row to 'Simulator baseline (reference only)'.
3. metrics_rules.csv: Standalone SQL business heuristic rule evaluation from reports/08_rule_evaluation.csv.
4. confusion_matrix.csv: 4-row classification matrix (TP, FP, FN, TN) structured for direct visualization
   in Power BI matrix and stacked bar visuals.

Enforces cross-table reconciliation and mathematical agreement with prior reporting artifacts.
"""

from pathlib import Path
import json
import sys
import time
from typing import Any

import duckdb
import numpy as np
import pandas as pd

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config


def build_metrics_overall(
    metrics_json_path: Path = config.FINAL_METRICS_JSON,
    master_alerts_path: Path = config.MASTER_ALERTS_PARQUET,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Generate metrics_overall.csv single-row summary and audit against master_alerts.parquet.

    Args:
        metrics_json_path: Path to reports/16_final_metrics.json.
        master_alerts_path: Path to master_alerts.parquet.

    Returns:
        tuple[pd.DataFrame, dict[str, Any]]: (metrics_overall_df, raw_json_metrics)
    """
    print("\n[1/4] Processing metrics_overall.csv...")
    if not metrics_json_path.exists():
        raise FileNotFoundError(f"Missing final metrics JSON at {metrics_json_path}")

    with open(metrics_json_path, "r", encoding="utf-8") as f:
        m = json.load(f)

    # Re-verify against master_alerts.parquet via DuckDB
    con = duckdb.connect()
    p_path = str(master_alerts_path)
    res = con.execute(f"""
        SELECT
            COUNT(*) AS total_txns,
            SUM(is_alert) AS total_alerts,
            SUM(isFraud) AS fraud_count,
            SUM(tp_flag) AS tp,
            SUM(fp_flag) AS fp,
            SUM(fn_flag) AS fn,
            SUM(tn_flag) AS tn,
            ROUND(SUM(CASE WHEN is_alert = 1 THEN amount ELSE 0.0 END), 2) AS flagged_val
        FROM '{p_path}'
    """).fetchone()

    assert res is not None
    m_txns, m_alerts, m_frauds, m_tp, m_fp, m_fn, m_tn, m_val = res

    assert m["total_transactions"] == m_txns, f"Total txns mismatch: {m['total_transactions']} != {m_txns}"
    assert m["total_alerts"] == m_alerts, f"Alert count mismatch: {m['total_alerts']} != {m_alerts}"
    assert m["fraud_count"] == m_frauds, f"Fraud count mismatch: {m['fraud_count']} != {m_frauds}"
    assert m["TP"] == m_tp, f"TP mismatch: {m['TP']} != {m_tp}"
    assert m["FP"] == m_fp, f"FP mismatch: {m['FP']} != {m_fp}"
    assert m["FN"] == m_fn, f"FN mismatch: {m['FN']} != {m_fn}"
    assert m["TN"] == m_tn, f"TN mismatch: {m['TN']} != {m_tn}"
    assert np.isclose(m["total_flagged_value"], m_val, atol=1.0), f"Flagged val mismatch: {m['total_flagged_value']} != {m_val}"
    print("  --> Re-verification against master_alerts.parquet PASSED (exact agreement).")

    row = {
        "total_txns": int(m["total_transactions"]),
        "total_alerts": int(m["total_alerts"]),
        "total_flagged_value": round(float(m["total_flagged_value"]), 2),
        "fraud_count": int(m["fraud_count"]),
        "fraud_rate_pct": round(float(m["overall_fraud_rate"]) * 100.0, 4),
        "tp": int(m["TP"]),
        "fp": int(m["FP"]),
        "fn": int(m["FN"]),
        "tn": int(m["TN"]),
        "precision_pct": round(float(m["precision"]) * 100.0, 4),
        "recall_pct": round(float(m["recall"]) * 100.0, 4),
        "fpr_pct": round(float(m["FPR"]) * 100.0, 4),
        "f1_pct": round(float(m["F1"]) * 100.0, 4),
    }

    df = pd.DataFrame([row])
    return df, m


def build_metrics_approach(
    approach_csv_path: Path = config.APPROACH_COMP_CSV,
) -> pd.DataFrame:
    """Generate metrics_approach.csv from reports/14_approach_comparison.csv (FULL universe).

    Args:
        approach_csv_path: Path to reports/14_approach_comparison.csv.

    Returns:
        pd.DataFrame: Formatted strategy comparison metrics for Power BI.
    """
    print("\n[2/4] Processing metrics_approach.csv...")
    if not approach_csv_path.exists():
        raise FileNotFoundError(f"Missing approach comparison CSV at {approach_csv_path}")

    df_raw = pd.read_csv(approach_csv_path)
    full_df = df_raw[df_raw["universe"] == "Full Universe (All Transactions)"].copy()

    # Rename simulator row
    full_df["approach"] = full_df["approach"].replace({
        "Simulator baseline (not used)": "Simulator baseline (reference only)"
    })

    records = []
    for _, r in full_df.iterrows():
        records.append({
            "approach": r["approach"],
            "alerts": int(r["alerts"]),
            "tp": int(r["TP"]),
            "fp": int(r["FP"]),
            "fn": int(r["FN"]),
            "precision_pct": round(float(r["precision"]) * 100.0, 4),
            "recall_pct": round(float(r["recall"]) * 100.0, 4),
            "fpr_pct": round(float(r["fpr"]) * 100.0, 4),
            "f1_pct": round(float(r["f1"]) * 100.0, 4),
            "flagged_value": round(float(r["flagged_amount"]), 2),
        })

    df = pd.DataFrame(records)
    assert len(df) == 6, f"Expected 6 approaches in metrics_approach.csv, got {len(df)}"
    return df


def build_metrics_rules(
    rules_csv_path: Path = config.RULE_EVAL_CSV,
) -> pd.DataFrame:
    """Generate metrics_rules.csv from reports/08_rule_evaluation.csv (FULL universe).

    Args:
        rules_csv_path: Path to reports/08_rule_evaluation.csv.

    Returns:
        pd.DataFrame: Formatted rule evaluation metrics for Power BI.
    """
    print("\n[3/4] Processing metrics_rules.csv...")
    if not rules_csv_path.exists():
        raise FileNotFoundError(f"Missing rule evaluation CSV at {rules_csv_path}")

    df_raw = pd.read_csv(rules_csv_path)
    full_df = df_raw[df_raw["universe"] == "FULL"].copy()

    records = []
    for _, r in full_df.iterrows():
        records.append({
            "rule_name": r["rule_name"],
            "alerts": int(r["alerts"]),
            "tp": int(r["tp"]),
            "fp": int(r["fp"]),
            "precision_pct": round(float(r["precision"]) * 100.0, 4),
            "recall_pct": round(float(r["recall"]) * 100.0, 4),
            "fpr_pct": round(float(r["fpr"]) * 100.0, 4),
            "f1_pct": round(float(r["f1"]) * 100.0, 4),
        })

    df = pd.DataFrame(records)
    assert len(df) == 9, f"Expected 9 rules/composites in metrics_rules.csv, got {len(df)}"
    return df


def build_confusion_matrix(
    m: dict[str, Any],
) -> pd.DataFrame:
    """Generate confusion_matrix.csv classification matrix.

    Args:
        m: Parsed metrics dictionary from reports/16_final_metrics.json.

    Returns:
        pd.DataFrame: 4-row confusion matrix DataFrame.
    """
    print("\n[4/4] Processing confusion_matrix.csv...")
    total_txns = float(m["total_transactions"])
    tp = int(m["TP"])
    fp = int(m["FP"])
    fn = int(m["FN"])
    tn = int(m["TN"])

    rows = [
        {
            "outcome": "True Positive",
            "actual": "Fraud",
            "predicted": "Alert",
            "count": tp,
            "pct_of_total": round((tp / total_txns) * 100.0, 4),
        },
        {
            "outcome": "False Positive",
            "actual": "Legit",
            "predicted": "Alert",
            "count": fp,
            "pct_of_total": round((fp / total_txns) * 100.0, 4),
        },
        {
            "outcome": "False Negative",
            "actual": "Fraud",
            "predicted": "No alert",
            "count": fn,
            "pct_of_total": round((fn / total_txns) * 100.0, 4),
        },
        {
            "outcome": "True Negative",
            "actual": "Legit",
            "predicted": "No alert",
            "count": tn,
            "pct_of_total": round((tn / total_txns) * 100.0, 4),
        },
    ]

    df = pd.DataFrame(rows)
    assert len(df) == 4, "Expected exactly 4 rows in confusion_matrix.csv"
    assert int(df["count"].sum()) == config.EXPECTED_ROWS, (
        f"Confusion matrix sum mismatch: {df['count'].sum():,} != {config.EXPECTED_ROWS:,}"
    )
    return df


def export_powerbi_metrics(
    output_dir: Path = config.POWERBI_OUTPUT_DIR,
) -> dict[str, pd.DataFrame]:
    """Generate and write all four Power BI performance metric CSVs.

    Args:
        output_dir: Destination folder for exported CSV tables.

    Returns:
        dict[str, pd.DataFrame]: Mapping of exported filenames to DataFrames.
    """
    t_start = time.perf_counter()
    print("==================================================")
    print("Exporting Power BI Performance Metrics & Matrix")
    print("==================================================")

    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Build metrics
    df_overall, raw_json = build_metrics_overall()
    df_approach = build_metrics_approach()
    df_rules = build_metrics_rules()
    df_cm = build_confusion_matrix(raw_json)

    # Acceptance Criteria Assertions
    # 1. Confusion matrix counts sum to 6,362,620
    cm_total = int(df_cm["count"].sum())
    assert cm_total == config.EXPECTED_ROWS, f"Confusion sum ({cm_total}) != {config.EXPECTED_ROWS}"

    # 2. Precision & recall agreement within 0.01 tolerance
    overall_row = df_overall.iloc[0]
    json_prec_pct = raw_json["precision"] * 100.0
    json_rec_pct = raw_json["recall"] * 100.0

    assert abs(overall_row["precision_pct"] - json_prec_pct) < 0.01, (
        f"Precision tolerance exceeded: {overall_row['precision_pct']} vs {json_prec_pct}"
    )
    assert abs(overall_row["recall_pct"] - json_rec_pct) < 0.01, (
        f"Recall tolerance exceeded: {overall_row['recall_pct']} vs {json_rec_pct}"
    )

    outputs = {
        "metrics_overall.csv": df_overall,
        "metrics_approach.csv": df_approach,
        "metrics_rules.csv": df_rules,
        "confusion_matrix.csv": df_cm,
    }

    print("\nWriting tables to disk...")
    print("=" * 70)
    print(f"{'Metrics File':<25} | {'Rows':>6} | {'Columns':>8} | {'Destination':<20}")
    print("-" * 70)

    for filename, df in outputs.items():
        dest = output_dir / filename
        df.to_csv(dest, index=False, encoding="utf-8")
        print(f"{filename:<25} | {len(df):>6} | {len(df.columns):>8} | {dest.name}")

    print("=" * 70)

    # Display Previews
    for filename, df in outputs.items():
        print(f"\n--- {filename} ---")
        print(df.to_string(index=False))

    print(f"\nExport completed successfully in {time.perf_counter() - t_start:.2f}s.")
    return outputs


def main() -> None:
    """CLI execution entrypoint."""
    export_powerbi_metrics()


if __name__ == "__main__":
    main()
