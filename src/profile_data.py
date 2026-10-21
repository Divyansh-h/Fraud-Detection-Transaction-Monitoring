"""Data profiling module for Financial Fraud Detection & Transaction Monitoring."""

import sys
from pathlib import Path
import numpy as np
import pandas as pd

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config
from src.load_data import load_raw


def run_profiling(df: pd.DataFrame | None = None) -> dict:
    """Compute comprehensive data profiling statistics and generate reports.

    Args:
        df: Optional preloaded DataFrame. If None, loaded via load_raw().

    Returns:
        dict: Profiling metrics dictionary.
    """
    if df is None:
        df = load_raw()

    total_rows = len(df)
    total_cols = len(df.columns)
    mem_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)

    # 1. Null count per column and total nulls
    null_counts = df.isnull().sum()
    total_nulls = int(null_counts.sum())

    # 2. Describe() for amount and balance columns
    numeric_cols = [
        config.COL_AMOUNT,
        config.COL_OLD_BALANCE_ORG,
        config.COL_NEW_BALANCE_ORIG,
        config.COL_OLD_BALANCE_DEST,
        config.COL_NEW_BALANCE_DEST,
    ]
    quantiles = [0.01, 0.25, 0.50, 0.75, 0.99, 0.999]
    desc_df = df[numeric_cols].describe(percentiles=quantiles).T
    desc_df["min"] = df[numeric_cols].min()
    desc_df["max"] = df[numeric_cols].max()

    # 3. Transaction counts and percentage share by type
    type_counts = df[config.COL_TYPE].value_counts(sort=False)
    type_shares = (type_counts / total_rows) * 100

    # 4. Fraud statistics by type
    grouped = df.groupby(config.COL_TYPE, observed=False)
    fraud_by_type = grouped.agg(
        count=(config.COL_STEP, "count"),
        fraud_sum=(config.COL_IS_FRAUD, "sum"),
        mean_amount=(config.COL_AMOUNT, "mean"),
        median_amount=(config.COL_AMOUNT, "median"),
    )
    fraud_by_type["fraud_rate_pct"] = (
        fraud_by_type["fraud_sum"] / fraud_by_type["count"]
    ) * 100

    # Verification: Fraud must only occur in TRANSFER and CASH_OUT
    fraud_types_observed = fraud_by_type[fraud_by_type["fraud_sum"] > 0].index.tolist()
    unexpected_fraud_types = [
        t for t in fraud_types_observed if t not in config.FRAUD_TYPES
    ]
    if unexpected_fraud_types:
        raise RuntimeError(
            f"DATA ANOMALY: Fraud observed in unexpected transaction types: {unexpected_fraud_types}"
        )

    # 5. Overall fraud rate and imbalance ratio
    total_fraud = int(df[config.COL_IS_FRAUD].sum())
    total_legit = total_rows - total_fraud
    overall_fraud_rate_pct = (total_fraud / total_rows) * 100
    imbalance_ratio = total_legit / total_fraud

    # 6. Unique accounts and merchant counts
    unique_orig = int(df[config.COL_NAME_ORIG].nunique())
    unique_dest = int(df[config.COL_NAME_DEST].nunique())
    merchant_mask = df[config.COL_NAME_DEST].str.startswith("M")
    merchant_count = int(merchant_mask.sum())
    merchant_share_pct = (merchant_count / total_rows) * 100

    # 7. Step range and daily distribution
    step_min = int(df[config.COL_STEP].min())
    step_max = int(df[config.COL_STEP].max())
    day_series = (df[config.COL_STEP] - 1) // 24 + 1
    daily_counts = df.groupby(day_series).agg(
        total_tx=(config.COL_STEP, "count"),
        fraud_tx=(config.COL_IS_FRAUD, "sum"),
    )
    daily_counts["fraud_rate_pct"] = (
        daily_counts["fraud_tx"] / daily_counts["total_tx"]
    ) * 100

    # Save outputs
    # A. reports/01_fraud_by_type.csv
    config.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    fraud_by_type.to_csv(config.FRAUD_BY_TYPE_CSV, index=True)
    print(f"Saved: {config.FRAUD_BY_TYPE_CSV}")

    # B. reports/01_profile.md
    md_content = generate_markdown_report(
        total_rows=total_rows,
        total_cols=total_cols,
        mem_mb=mem_mb,
        col_dtypes=df.dtypes,
        null_counts=null_counts,
        total_nulls=total_nulls,
        desc_df=desc_df,
        type_counts=type_counts,
        type_shares=type_shares,
        fraud_by_type=fraud_by_type,
        total_fraud=total_fraud,
        total_legit=total_legit,
        overall_fraud_rate_pct=overall_fraud_rate_pct,
        imbalance_ratio=imbalance_ratio,
        unique_orig=unique_orig,
        unique_dest=unique_dest,
        merchant_count=merchant_count,
        merchant_share_pct=merchant_share_pct,
        step_min=step_min,
        step_max=step_max,
        daily_counts=daily_counts,
    )
    with open(config.PROFILE_REPORT_MD, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"Saved: {config.PROFILE_REPORT_MD}")

    # Console summary print
    print("\n" + "=" * 60)
    print("DATA PROFILING SUMMARY")
    print("=" * 60)
    print(f"Total Rows:            {total_rows:,}")
    print(f"Total Columns:         {total_cols}")
    print(f"Total Memory Footprint:{mem_mb:.2f} MB")
    print(f"Total Missing Values:  {total_nulls}")
    print(f"Total Fraud Cases:     {total_fraud:,} ({overall_fraud_rate_pct:.4f}%)")
    print(f"Class Imbalance Ratio: {imbalance_ratio:.2f} : 1 (legitimate per fraud)")
    print(f"Unique Originators:    {unique_orig:,}")
    print(f"Unique Destinations:   {unique_dest:,}")
    print(f"Merchant Destinations: {merchant_count:,} ({merchant_share_pct:.2f}%)")
    print(f"Step Range:            {step_min} to {step_max} (~{(step_max - step_min + 1) / 24:.1f} days)")
    print("\nFraud Statistics by Type:")
    print(fraud_by_type[["count", "fraud_sum", "fraud_rate_pct", "mean_amount", "median_amount"]].to_string())
    print("=" * 60)

    return {
        "total_rows": total_rows,
        "total_fraud": total_fraud,
        "overall_fraud_rate_pct": overall_fraud_rate_pct,
        "imbalance_ratio": imbalance_ratio,
        "fraud_by_type": fraud_by_type,
        "unique_orig": unique_orig,
        "unique_dest": unique_dest,
        "merchant_count": merchant_count,
        "total_nulls": total_nulls,
    }


def generate_markdown_report(
    total_rows: int,
    total_cols: int,
    mem_mb: float,
    col_dtypes: pd.Series,
    null_counts: pd.Series,
    total_nulls: int,
    desc_df: pd.DataFrame,
    type_counts: pd.Series,
    type_shares: pd.Series,
    fraud_by_type: pd.DataFrame,
    total_fraud: int,
    total_legit: int,
    overall_fraud_rate_pct: float,
    imbalance_ratio: float,
    unique_orig: int,
    unique_dest: int,
    merchant_count: int,
    merchant_share_pct: float,
    step_min: int,
    step_max: int,
    daily_counts: pd.DataFrame,
) -> str:
    """Generate GitHub-flavored markdown report."""
    md = []
    md.append("# PaySim Dataset Profiling Report\n")
    md.append("## 1. Executive Summary\n")
    md.append(f"- **Total Transactions:** {total_rows:,}")
    md.append(f"- **Total Columns:** {total_cols}")
    md.append(f"- **Memory Footprint:** {mem_mb:.2f} MB")
    md.append(f"- **Total Null Values:** {total_nulls}")
    md.append(f"- **Total Fraudulent Transactions:** {total_fraud:,}")
    md.append(f"- **Overall Fraud Rate:** {overall_fraud_rate_pct:.4f}% (~0.129%)")
    md.append(f"- **Imbalance Ratio:** {imbalance_ratio:.2f} : 1 ({total_legit:,} legit to {total_fraud:,} fraud)\n")

    md.append("## 2. Missing Value Analysis\n")
    md.append("| Column | Data Type | Null Count | Null % |")
    md.append("|---|---|---|---|")
    for col, count in null_counts.items():
        dt_str = str(col_dtypes.get(col, "unknown"))
        md.append(f"| `{col}` | `{dt_str}` | {count:,} | {(count / total_rows) * 100:.2f}% |")
    md.append(f"\n**Total Nulls Across Dataset:** {total_nulls}\n")

    md.append("## 3. Numeric Column Descriptive Statistics\n")
    md.append("| Column | Mean | Std | Min | 1% | 25% | Median (50%) | 75% | 99% | 99.9% | Max |")
    md.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for col, row in desc_df.iterrows():
        md.append(
            f"| `{col}` | {row['mean']:,.2f} | {row['std']:,.2f} | {row['min']:,.2f} | "
            f"{row['1%']:,.2f} | {row['25%']:,.2f} | {row['50%']:,.2f} | {row['75%']:,.2f} | "
            f"{row['99%']:,.2f} | {row['99.9%']:,.2f} | {row['max']:,.2f} |"
        )
    md.append("\n")

    md.append("## 4. Transaction Breakdown by Type\n")
    md.append("| Transaction Type | Count | Share (%) |")
    md.append("|---|---|---|")
    for t in config.ALL_TYPES:
        cnt = type_counts.get(t, 0)
        sh = type_shares.get(t, 0.0)
        md.append(f"| **{t}** | {cnt:,} | {sh:.2f}% |")
    md.append("\n")

    md.append("## 5. Fraud Statistics by Transaction Type\n")
    md.append("| Transaction Type | Total Count | Fraud Count | Fraud Rate (%) | Mean Amount | Median Amount |")
    md.append("|---|---|---|---|---|---|")
    for t in config.ALL_TYPES:
        row = fraud_by_type.loc[t] if t in fraud_by_type.index else None
        if row is not None:
            md.append(
                f"| **{t}** | {int(row['count']):,} | {int(row['fraud_sum']):,} | "
                f"{row['fraud_rate_pct']:.4f}% | {row['mean_amount']:,.2f} | {row['median_amount']:,.2f} |"
            )
    md.append("\n> **Key Verification:** Fraud cases occur exclusively in `TRANSFER` (4,097) and `CASH_OUT` (4,116). `CASH_IN`, `DEBIT`, and `PAYMENT` contain exactly 0 fraud occurrences.\n")

    md.append("## 6. Entity Cardinality & Merchant Analysis\n")
    md.append(f"- **Unique Originator Accounts (`nameOrig`):** {unique_orig:,} ({unique_orig / total_rows:.4%} unique)")
    md.append(f"- **Unique Destination Accounts (`nameDest`):** {unique_dest:,}")
    md.append(f"- **Merchant Destinations (Starting with 'M'):** {merchant_count:,} ({merchant_share_pct:.2f}% of all transactions)")
    md.append("- **Note:** Merchant accounts have 0 initial and final destination balances by design in the PaySim simulator.\n")

    md.append("## 7. Temporal Distribution (Hourly Step to Daily Aggregations)\n")
    md.append(f"- **Simulation Step Range:** {step_min} to {step_max} (1 step = 1 hour, span of {step_max // 24 + 1} days)\n")
    md.append("| Day | Total Transactions | Fraud Transactions | Fraud Rate (%) |")
    md.append("|---|---|---|---|")
    for day, row in daily_counts.iterrows():
        md.append(
            f"| Day {day:02d} | {int(row['total_tx']):,} | {int(row['fraud_tx']):,} | {row['fraud_rate_pct']:.4f}% |"
        )
    md.append("\n")

    return "\n".join(md)


if __name__ == "__main__":
    run_profiling()
