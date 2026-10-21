"""Programmatic Data Dictionary Generator for Power BI CSV Exports.

Inspects all 18 CSV tables in data/outputs/powerbi/, computes exact row counts and column
types dynamically, joins them with verified business descriptions, and exports
powerbi/data_dictionary.md.
"""

from pathlib import Path
import sys
import time

import pandas as pd

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config

TABLE_METADATA = {
    # 1. Fact Table
    "fact_transactions.csv": {
        "category": "Fact Table (Sampled)",
        "purpose": (
            "Primary transactional fact table for Power BI Desktop. Contains 100% of all alerts and "
            "frauds (1,085,626 rows, capturing all 8,213 frauds including 17 false negatives) plus a "
            "50,000-row stratified sample of legitimate unalerted transactions (seed 42). High-cardinality "
            "raw balances are excluded to keep file size under 160MB for fast interactive rendering. "
            "NOTE: Enterprise-wide aggregate KPIs must be sourced from aggregate tables, not COUNTROWS(fact_transactions)."
        ),
        "column_descriptions": {
            "txn_id": "Unique zero-based transaction identifier (Primary Key in full clean dataset).",
            "step": "Simulation time step in hours from start of simulation (1 to 743).",
            "day": "Relative simulation day number (1 to 31, where day = (step-1)//24 + 1).",
            "hour": "Diurnal transaction hour (0 to 23, where hour = (step-1) % 24).",
            "type": "Transaction payment method (TRANSFER, CASH_OUT, CASH_IN, PAYMENT, DEBIT).",
            "amount": "Transaction amount in monetary currency units, rounded to 2 decimals.",
            "amount_band": "Discretized amount magnitude interval (<1K, 1K-10K, 10K-100K, 100K-1M, >1M).",
            "nameOrig": "Unique account identifier of the customer initiating the transaction.",
            "nameDest": "Unique account identifier of the recipient / merchant receiving funds.",
            "rule_emptied": "Heuristic Rule 1 flag: 1 if originator account was drained to 0.",
            "rule_large_amount": "Heuristic Rule 2 flag: 1 if amount exceeds 99th percentile ($1.62M for TRANSFER, $448K for CASH_OUT).",
            "rule_velocity": "Heuristic Rule 3 flag: 1 if originator executed >=3 transactions in rolling 6h.",
            "rule_transfer_then_cashout": "Heuristic Rule 4 flag: 1 if transfer was followed by cashout to mule dest within 24h.",
            "rule_mule_dest": "Heuristic Rule 5 flag: 1 if destination account received funds from >=3 distinct senders in day.",
            "rule_dest_unchanged": "Heuristic Rule 6 flag: 1 if transfer to non-merchant had unchanged destination balance.",
            "rule_balance_error": "Heuristic Rule 7 flag: 1 if both originator and recipient exhibited arithmetic balance discrepancies.",
            "alert_score": "Composite heuristic score: integer sum of triggered business rules (0 to 7).",
            "anomaly_score_pct": "Isolation Forest anomaly score normalized to 0-100% scale (higher = more anomalous).",
            "ml_flag": "Binary machine learning anomaly flag calibrated at optimal validation F1 threshold (0.595088).",
            "rule_alert": "Composite heuristic alert indicator (1 if alert_score >= 1, 0 otherwise).",
            "alert_source": "Attribution category: 'Both' (Rule & ML), 'Rule only', 'ML only', or 'None'.",
            "combo_score": "Blended risk score (0-100): 0.5 * (alert_score/7 * 100) + 0.5 * anomaly_score_pct.",
            "risk_band": "Operational triage band: 'Critical' (>=80), 'High' (>=60), 'Medium' (>=40), 'Low' (<40).",
            "is_alert": "Official production alert flag (Combined OR: rule_alert == 1 | ml_flag == 1).",
            "isFraud": "Ground-truth fraudulent transaction indicator (1 = Fraud, 0 = Legitimate).",
            "outcome": "Classification quadrant: 'True Positive', 'False Positive', 'False Negative', 'True Negative'.",
            "row_origin": "Sampling designation: 'Alert/Fraud' (100% census) or 'Normal sample' (stratified legitimate sample).",
        },
    },

    # 2. Dimensions
    "dim_type.csv": {
        "category": "Dimension Table",
        "purpose": "Dimension lookup table mapping transaction payment types to risk categories and custom visual sort orders.",
        "column_descriptions": {
            "type": "Transaction payment method name (Primary Key).",
            "type_group": "Regulatory risk grouping: 'Fraud-prone' (TRANSFER, CASH_OUT) vs. 'No fraud observed' (others).",
            "type_sort": "Visual sort order index (1 to 5).",
        },
    },
    "dim_day.csv": {
        "category": "Dimension Table",
        "purpose": "Calendar dimension table for simulation days (Day 01 to Day 31) with day-of-week and week index hierarchy.",
        "column_descriptions": {
            "day": "Simulation day number from 1 to 31 (Primary Key).",
            "day_label": "Zero-padded day display string ('Day 01' to 'Day 31').",
            "day_of_week_index": "Relative day of week index (1 to 7, where index = ((day-1) % 7) + 1).",
            "week_number": "Relative calendar week number (1 to 5, where week = ((day-1) // 7) + 1).",
        },
    },
    "dim_hour.csv": {
        "category": "Dimension Table",
        "purpose": "Diurnal hourly dimension table mapping transaction hours to operational investigation shifts.",
        "column_descriptions": {
            "hour": "Transaction hour from 0 to 23 (Primary Key).",
            "hour_label": "Clock format display label ('00:00' to '23:00').",
            "time_band": "Diurnal shift interval: 'Night' (0-5), 'Morning' (6-11), 'Afternoon' (12-17), 'Evening' (18-23).",
        },
    },
    "dim_alert_source.csv": {
        "category": "Dimension Table",
        "purpose": "Dimension table defining detection attribution sources (Both, Rule only, ML only, None).",
        "column_descriptions": {
            "alert_source": "Detection attribution name (Primary Key).",
            "alert_source_sort": "Priority sort order index (1 to 4).",
        },
    },
    "dim_risk_band.csv": {
        "category": "Dimension Table",
        "purpose": "Dimension table defining operational triaging risk bands (Critical, High, Medium, Low).",
        "column_descriptions": {
            "risk_band": "Risk band name (Primary Key).",
            "risk_band_sort": "Priority sort order index (1 to 4).",
        },
    },
    "dim_amount_band.csv": {
        "category": "Dimension Table",
        "purpose": "Dimension table defining transactional currency magnitude intervals.",
        "column_descriptions": {
            "amount_band": "Monetary magnitude interval label (Primary Key).",
            "amount_band_sort": "Magnitude sort order index (1 to 5).",
        },
    },

    # 3. Aggregate Summary Tables
    "agg_by_type.csv": {
        "category": "Aggregate Summary Table",
        "purpose": "Full-universe (6.36M) pre-aggregated volume, confusion matrix breakdown, and alert rates by transaction type.",
        "column_descriptions": {
            "type": "Transaction payment method name.",
            "total_txns": "Total enterprise transaction volume of this type.",
            "total_amount": "Total transactional currency volume ($).",
            "fraud_count": "Total confirmed fraudulent transactions.",
            "alert_count": "Total alerts triggered under official Combined OR definition.",
            "tp": "True positive fraud detections.",
            "fp": "False positive alarms (legitimate transactions flagged).",
            "fn": "False negatives (missed fraudulent transactions).",
            "tn": "True negatives (correctly unalerted legitimate transactions).",
            "flagged_value": "Total currency amount of flagged transactions ($).",
            "fraud_rate_pct": "Prevalence of fraud within this payment type (%).",
            "alert_rate_pct": "Proportion of transactions flagged for review (%).",
        },
    },
    "agg_by_day.csv": {
        "category": "Aggregate Summary Table",
        "purpose": "Full-universe daily aggregated temporal trend metrics across the 31-day monitoring window.",
        "column_descriptions": {
            "day": "Simulation day number (1 to 31).",
            "total_txns": "Total transaction volume on this day.",
            "fraud_count": "Confirmed fraud count on this day.",
            "alert_count": "Alerts triggered on this day.",
            "tp": "True positive detections on this day.",
            "fp": "False positive alarms on this day.",
            "fn": "Missed fraud cases on this day.",
            "flagged_value": "Total currency amount of alerted transactions on this day ($).",
        },
    },
    "agg_by_hour.csv": {
        "category": "Aggregate Summary Table",
        "purpose": "Full-universe hourly aggregated diurnal fraud and surveillance profile (hours 0 to 23).",
        "column_descriptions": {
            "hour": "Diurnal hour of the day (0 to 23).",
            "total_txns": "Total transaction volume at this hour.",
            "fraud_count": "Confirmed fraud count at this hour.",
            "alert_count": "Alerts triggered at this hour.",
            "tp": "True positive detections at this hour.",
            "fp": "False positive alarms at this hour.",
            "fn": "Missed fraud cases at this hour.",
            "flagged_value": "Total currency amount of alerted transactions at this hour ($).",
        },
    },
    "agg_by_day_type.csv": {
        "category": "Aggregate Summary Table",
        "purpose": "Granular cross-tabulation of daily transaction volume, fraud count, and alerts across all payment types.",
        "column_descriptions": {
            "day": "Simulation day number (1 to 31).",
            "type": "Transaction payment method.",
            "total_txns": "Total transaction volume for this day and type.",
            "fraud_count": "Confirmed fraud count for this day and type.",
            "alert_count": "Alerts triggered for this day and type.",
            "flagged_value": "Total currency amount of alerted transactions ($).",
        },
    },
    "agg_by_source.csv": {
        "category": "Aggregate Summary Table",
        "purpose": "Alert attribution breakdown comparing Consensus ('Both'), Rules only, ML only, and Unflagged ('None').",
        "column_descriptions": {
            "alert_source": "Attribution category ('Both', 'Rule only', 'ML only', 'None').",
            "alert_count": "Total transaction count falling into this attribution category.",
            "fraud_caught": "Confirmed fraud events intercepted.",
            "fp": "False positive alarms generated.",
            "flagged_value": "Total currency amount flagged in this attribution source ($).",
            "precision_pct": "Detection precision / hit rate within this attribution source (%).",
        },
    },
    "agg_by_risk_band.csv": {
        "category": "Aggregate Summary Table",
        "purpose": "Pre-aggregated operational distribution across the four tiered risk bands (Critical, High, Medium, Low).",
        "column_descriptions": {
            "risk_band": "Operational risk band name ('Critical', 'High', 'Medium', 'Low').",
            "rows": "Total transactions classified into this risk band.",
            "fraud_count": "Confirmed fraudulent transactions in this risk band.",
            "flagged_value": "Total currency amount flagged in this risk band ($).",
        },
    },
    "agg_by_amount_band_type.csv": {
        "category": "Aggregate Summary Table",
        "purpose": "Cross-tabulation matrix of transaction amount magnitude intervals vs. payment types.",
        "column_descriptions": {
            "amount_band": "Monetary magnitude interval label (<1K, 1K-10K, 10K-100K, 100K-1M, >1M).",
            "type": "Transaction payment method.",
            "total_txns": "Total transaction volume in this amount band and type.",
            "fraud_count": "Confirmed fraud count in this amount band and type.",
            "alert_count": "Alerts triggered in this amount band and type.",
        },
    },

    # 4. Performance Metrics Tables
    "metrics_overall.csv": {
        "category": "Performance Metrics Table",
        "purpose": "Single-row enterprise KPI summary card source for Power BI executive dashboard headers.",
        "column_descriptions": {
            "total_txns": "Total enterprise transaction volume (6,362,620).",
            "total_alerts": "Total alerts flagged under official Combined OR definition (1,085,609).",
            "total_flagged_value": "Total currency amount of alerted transactions ($407,883,914,866.30).",
            "fraud_count": "Total confirmed fraud count across enterprise (8,213).",
            "fraud_rate_pct": "Overall baseline fraud prevalence rate (0.1291%).",
            "tp": "True positive detections (8,196).",
            "fp": "False positive alarms (1,077,413).",
            "fn": "False negatives / missed frauds (17).",
            "tn": "True negatives / correctly unflagged legitimate transactions (5,276,994).",
            "precision_pct": "Global detection precision rate (0.7550%).",
            "recall_pct": "Global detection recall rate (99.7930%).",
            "fpr_pct": "Global false positive rate (16.9554%).",
            "f1_pct": "Balanced F1 score expressed as percentage (1.4986%).",
        },
    },
    "metrics_approach.csv": {
        "category": "Performance Metrics Table",
        "purpose": "Comparative strategy performance matrix comparing the 6 detection approaches across the Full Universe.",
        "column_descriptions": {
            "approach": "Detection strategy name (e.g. Combined AND, ML only, Combined OR, etc.).",
            "alerts": "Total alerts flagged by this strategy.",
            "tp": "True positive detections.",
            "fp": "False positive alarms.",
            "fn": "Missed fraud cases.",
            "precision_pct": "Precision rate of this strategy (%).",
            "recall_pct": "Recall rate of this strategy (%).",
            "fpr_pct": "False positive rate of this strategy (%).",
            "f1_pct": "Balanced F1 score of this strategy (%).",
            "flagged_value": "Total currency amount flagged by this strategy ($).",
        },
    },
    "metrics_rules.csv": {
        "category": "Performance Metrics Table",
        "purpose": "Evaluation table of individual heuristic SQL business rules and composite thresholds across the Full Universe.",
        "column_descriptions": {
            "rule_name": "Descriptive business rule name (Rule 1 through Rule 7, plus composites).",
            "alerts": "Alerts triggered by this rule.",
            "tp": "True positive detections by this rule.",
            "fp": "False positive alarms by this rule.",
            "precision_pct": "Precision rate of this rule (%).",
            "recall_pct": "Recall rate of this rule (%).",
            "fpr_pct": "False positive rate of this rule (%).",
            "f1_pct": "Balanced F1 score of this rule (%).",
        },
    },
    "confusion_matrix.csv": {
        "category": "Performance Metrics Table",
        "purpose": "Four-row classification quadrant table formatted for direct ingestion by Power BI matrix visuals.",
        "column_descriptions": {
            "outcome": "Classification quadrant name ('True Positive', 'False Positive', 'False Negative', 'True Negative').",
            "actual": "Ground truth condition ('Fraud' vs. 'Legit').",
            "predicted": "System detection action ('Alert' vs. 'No alert').",
            "count": "Total transaction count in this quadrant.",
            "pct_of_total": "Percentage share of total enterprise transaction volume (%).",
        },
    },
}


def generate_data_dictionary(
    csv_dir: Path = config.POWERBI_OUTPUT_DIR,
    output_md_path: Path = config.POWERBI_DIR / "data_dictionary.md",
) -> str:
    """Read all CSVs programmatically and write powerbi/data_dictionary.md.

    Args:
        csv_dir: Path to directory containing the 18 exported CSVs.
        output_md_path: Path to write powerbi/data_dictionary.md.

    Returns:
        str: Generated Markdown content.
    """
    t_start = time.perf_counter()
    print("==================================================")
    print("Generating Power BI Data Dictionary Programmatically")
    print("==================================================")

    csv_files = sorted(csv_dir.glob("*.csv"))
    print(f"Discovered {len(csv_files)} CSV files in {csv_dir.relative_to(config.PROJECT_ROOT)}")

    sections = []
    sections.append("# Power BI Data Dictionary & Schema Documentation\n")
    sections.append(
        "**Document ID:** `powerbi/data_dictionary.md`  \n"
        f"**Source Directory:** `{csv_dir.relative_to(config.PROJECT_ROOT)}`  \n"
        f"**Generated Tables:** {len(csv_files)} CSV files  \n"
        "**Integrity Standard:** Row counts, column names, and data types are programmatically audited directly from data files.\n\n"
        "---\n"
    )

    # Table of contents
    sections.append("## Table of Contents\n")
    for csv_file in csv_files:
        name = csv_file.name
        cat = TABLE_METADATA.get(name, {}).get("category", "General")
        sections.append(f"- [{name}](#{name.replace('.', '').replace('_', '-')}) — *{cat}*")
    sections.append("\n---\n")

    # Detailed file documentation
    for csv_file in csv_files:
        name = csv_file.name
        meta = TABLE_METADATA.get(name, {
            "category": "General",
            "purpose": "Exported table for Power BI reporting.",
            "column_descriptions": {},
        })

        # Load CSV and inspect structure programmatically
        # Use keep_default_na=False so that "None" in alert_source is treated as string
        df = pd.read_csv(csv_file, nrows=1000, keep_default_na=False)

        # Count total rows programmatically without loading whole 150MB file into memory
        if name == "fact_transactions.csv":
            total_rows = 0
            with open(csv_file, "r", encoding="utf-8") as f:
                for _ in f:
                    total_rows += 1
            total_rows -= 1  # exclude header row
        else:
            with open(csv_file, "r", encoding="utf-8") as f:
                total_rows = sum(1 for _ in f) - 1

        file_size_bytes = csv_file.stat().st_size
        file_size_str = f"{file_size_bytes / (1024 * 1024):.2f} MB" if file_size_bytes >= 1024 * 1024 else f"{file_size_bytes:,} bytes"

        sections.append(f"## `{name}`\n")
        sections.append(f"**Category:** {meta['category']}  ")
        sections.append(f"**Row Count:** **{total_rows:,}** rows (computed from file)  ")
        sections.append(f"**File Size:** {file_size_str}  ")
        sections.append(f"**Purpose:** {meta['purpose']}\n")

        # Column Table
        sections.append("| Column Name | Inferred Data Type | Sample Value | Description & Business Meaning |")
        sections.append("| :--- | :---: | :---: | :--- |")

        for col in df.columns:
            dtype_str = str(df[col].dtype)
            if "int" in dtype_str:
                dtype_display = "Integer"
            elif "float" in dtype_str:
                dtype_display = "Decimal / Float"
            else:
                dtype_display = "Text / String"

            sample_val = str(df[col].iloc[0]) if len(df) > 0 else ""
            if len(sample_val) > 25:
                sample_val = sample_val[:22] + "..."

            desc = meta["column_descriptions"].get(col, f"Field '{col}' exported from data pipeline.")
            sections.append(f"| `{col}` | `{dtype_display}` | `{sample_val}` | {desc} |")

        sections.append("\n---\n")

    content = "\n".join(sections)

    output_md_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_md_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Data dictionary successfully written to: {output_md_path.relative_to(config.PROJECT_ROOT)}")
    print(f"Completed in {time.perf_counter() - t_start:.2f}s.")
    return content


def main() -> None:
    """CLI execution entrypoint."""
    generate_data_dictionary()


if __name__ == "__main__":
    main()
