"""Logical validity checking and simulation anomaly profiling module."""

import sys
from pathlib import Path
import pandas as pd

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config
from src.load_data import load_raw
from src.balance_checks import add_balance_features


def run_validity_checks(df: pd.DataFrame | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Execute logical validity checks on transactions with balance features.

    Does NOT modify, drop, or mutate any data rows.

    Args:
        df: Optional preloaded DataFrame. If None, loaded via load_raw() and augmented.

    Returns:
        tuple[pd.DataFrame, pd.DataFrame]: (validity_summary_df, overdraft_by_type_df)
    """
    if df is None:
        raw_df = load_raw()
        df = add_balance_features(raw_df)

    total_rows = len(df)
    fraud_mask = df[config.COL_IS_FRAUD] == 1
    total_fraud = int(fraud_mask.sum())

    checks = []

    # 1. Negative amounts, negative balances in any of the four balance columns
    neg_mask = (
        (df[config.COL_AMOUNT] < 0)
        | (df[config.COL_OLD_BALANCE_ORG] < 0)
        | (df[config.COL_NEW_BALANCE_ORIG] < 0)
        | (df[config.COL_OLD_BALANCE_DEST] < 0)
        | (df[config.COL_NEW_BALANCE_DEST] < 0)
    )
    neg_count = int(neg_mask.sum())
    neg_fraud = int(neg_mask[fraud_mask].sum())
    checks.append({
        "check_name": "1. Negative amounts or balances in any column",
        "count": neg_count,
        "pct_of_rows": (neg_count / total_rows) * 100,
        "count_in_fraud": neg_fraud,
        "comment": "No negative monetary amounts or balances exist; dataset respects non-negative domain rules.",
    })

    # 2. amount == 0 rows
    zero_amt_mask = df[config.COL_AMOUNT] == 0
    zero_amt_count = int(zero_amt_mask.sum())
    zero_amt_fraud = int(zero_amt_mask[fraud_mask].sum())
    checks.append({
        "check_name": "2. Transactions with amount == 0",
        "count": zero_amt_count,
        "pct_of_rows": (zero_amt_count / total_rows) * 100,
        "count_in_fraud": zero_amt_fraud,
        "comment": "Exactly 16 zero-amount rows exist, and 100% are fraudulent CASH_OUT attempts on drained accounts.",
    })

    # 3. oldbalanceOrg == 0 while amount > 0 (sender had no money but sent money)
    zero_orig_pos_amt = (df[config.COL_OLD_BALANCE_ORG] == 0) & (df[config.COL_AMOUNT] > 0)
    zero_orig_count = int(zero_orig_pos_amt.sum())
    zero_orig_fraud = int(zero_orig_pos_amt[fraud_mask].sum())
    checks.append({
        "check_name": "3. Sender oldbalanceOrg == 0 while amount > 0",
        "count": zero_orig_count,
        "pct_of_rows": (zero_orig_count / total_rows) * 100,
        "count_in_fraud": zero_orig_fraud,
        "comment": "Over 2.1M transactions have zero sender balance; frequent in legitimate cash-ins/payments, rare in fraud (25 cases).",
    })

    # 4. newbalanceOrig < 0 or amount > oldbalanceOrg (overdraft) by type
    overdraft_mask = (df[config.COL_NEW_BALANCE_ORIG] < 0) | (
        df[config.COL_AMOUNT] > df[config.COL_OLD_BALANCE_ORG]
    )
    overdraft_count = int(overdraft_mask.sum())
    overdraft_fraud = int(overdraft_mask[fraud_mask].sum())
    checks.append({
        "check_name": "4. Overdraft: newbalanceOrig < 0 or amount > oldbalanceOrg",
        "count": overdraft_count,
        "pct_of_rows": (overdraft_count / total_rows) * 100,
        "count_in_fraud": overdraft_fraud,
        "comment": "Simulator clamps newbalanceOrig at 0 without negative balances; 64.1% of transactions show amount > old balance, but only 29 frauds exhibit this.",
    })

    # Compute breakdown for check 4
    overdraft_by_type = df.groupby(config.COL_TYPE, observed=False).agg(
        total_tx=(config.COL_STEP, "count"),
        overdraft_tx=(config.COL_AMOUNT, lambda s: int(overdraft_mask.loc[s.index].sum())),
        overdraft_fraud=(config.COL_IS_FRAUD, lambda s: int((overdraft_mask & fraud_mask).loc[s.index].sum())),
    )
    overdraft_by_type["overdraft_rate_pct"] = (
        overdraft_by_type["overdraft_tx"] / overdraft_by_type["total_tx"]
    ) * 100

    # 5. oldbalanceDest == 0 and newbalanceDest == 0 while amount > 0 for non-merchant destinations
    zero_dest_pair = (
        (df[config.COL_OLD_BALANCE_DEST] == 0)
        & (df[config.COL_NEW_BALANCE_DEST] == 0)
        & (df[config.COL_AMOUNT] > 0)
        & (df[config.COL_DEST_IS_MERCHANT] == 0)
    )
    zero_dest_count = int(zero_dest_pair.sum())
    zero_dest_fraud = int(zero_dest_pair[fraud_mask].sum())
    checks.append({
        "check_name": "5. Receiver old & new balance both 0 (non-merchant, amount > 0)",
        "count": zero_dest_count,
        "pct_of_rows": (zero_dest_count / total_rows) * 100,
        "count_in_fraud": zero_dest_fraud,
        "comment": "Recipient balances remain 0.0 despite funds sent; strong fraud indicator (captures 4,070 fraud cases, 49.56% of total fraud).",
    })

    # 6. TRANSFER or CASH_OUT where amount > oldbalanceOrg
    tf_co_overdraft = (
        df[config.COL_TYPE].isin(config.FRAUD_TYPES)
        & (df[config.COL_AMOUNT] > df[config.COL_OLD_BALANCE_ORG])
    )
    tf_co_od_count = int(tf_co_overdraft.sum())
    tf_co_od_fraud = int(tf_co_overdraft[fraud_mask].sum())
    checks.append({
        "check_name": "6. TRANSFER or CASH_OUT with amount > oldbalanceOrg",
        "count": tf_co_od_count,
        "pct_of_rows": (tf_co_od_count / total_rows) * 100,
        "count_in_fraud": tf_co_od_fraud,
        "comment": "Common in legitimate activity (39.1%) due to missing initial balances; rare in fraud (only 29 fraud cases) where exact balance is drained.",
    })

    # 7. isFlaggedFraud == 1
    flagged_mask = df[config.COL_IS_FLAGGED_FRAUD] == 1
    flagged_count = int(flagged_mask.sum())
    flagged_fraud = int(flagged_mask[fraud_mask].sum())
    flagged_min_amt = float(df.loc[flagged_mask, config.COL_AMOUNT].min())
    checks.append({
        "check_name": "7. Simulator rule flag: isFlaggedFraud == 1",
        "count": flagged_count,
        "pct_of_rows": (flagged_count / total_rows) * 100,
        "count_in_fraud": flagged_fraud,
        "comment": f"Extremely weak heuristic: fires on only 16 rows (100% precision, but 0.19% recall; misses 99.81% of fraud); only triggers on TRANSFER >= ${flagged_min_amt:,.2f}.",
    })

    # 8. Rows where type is CASH_IN, DEBIT, or PAYMENT but isFraud == 1
    non_fraud_type_fraud = (
        df[config.COL_TYPE].isin(["CASH_IN", "DEBIT", "PAYMENT"])
        & fraud_mask
    )
    nftf_count = int(non_fraud_type_fraud.sum())
    nftf_fraud = int(non_fraud_type_fraud[fraud_mask].sum())
    checks.append({
        "check_name": "8. Fraud in CASH_IN, DEBIT, or PAYMENT (expected 0)",
        "count": nftf_count,
        "pct_of_rows": (nftf_count / total_rows) * 100,
        "count_in_fraud": nftf_fraud,
        "comment": "Zero fraud instances exist in CASH_IN, DEBIT, or PAYMENT; confirms fraud is strictly confined to TRANSFER and CASH_OUT.",
    })

    # Create summary DataFrame
    validity_df = pd.DataFrame(checks)

    # Save to CSV
    config.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    validity_df.to_csv(config.VALIDITY_REPORT_CSV, index=False)
    print(f"Saved: {config.VALIDITY_REPORT_CSV}")

    # Generate Markdown Report
    md_content = generate_markdown(
        total_rows=total_rows,
        total_fraud=total_fraud,
        validity_df=validity_df,
        overdraft_by_type=overdraft_by_type,
        flagged_count=flagged_count,
        flagged_fraud=flagged_fraud,
        flagged_min_amt=flagged_min_amt,
    )
    with open(config.VALIDITY_REPORT_MD, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"Saved: {config.VALIDITY_REPORT_MD}")

    # Print table to console
    print("\n" + "=" * 90)
    print("LOGICAL VALIDITY & SIMULATION ANOMALY CHECKS SUMMARY")
    print("=" * 90)
    for _, row in validity_df.iterrows():
        print(f"\n[{row['check_name']}]")
        print(f"  Count:          {row['count']:,} ({row['pct_of_rows']:.6f}% of rows)")
        print(f"  Count in Fraud: {row['count_in_fraud']:,} / {total_fraud:,}")
        print(f"  Finding:        {row['comment']}")
    print("\n" + "=" * 90)

    return validity_df, overdraft_by_type


def generate_markdown(
    total_rows: int,
    total_fraud: int,
    validity_df: pd.DataFrame,
    overdraft_by_type: pd.DataFrame,
    flagged_count: int,
    flagged_fraud: int,
    flagged_min_amt: float,
) -> str:
    """Format markdown report with tables and commentary."""
    md = []
    md.append("# Logical Validity and Simulation Anomaly Report\n")
    md.append("## 1. Overview\n")
    md.append("This report examines logical domain constraints, simulation quirks, and accounting validity across all 6,362,620 transactions. ")
    md.append("**Standing Rule Compliance:** No rows were removed or altered during this analysis. All quirks are documented for model feature engineering.\n")

    md.append("## 2. Logical Validity Check Results\n")
    md.append("| Check Name | Count | % of Rows | Count in Fraud | Analytical Finding & Quirk Explanation |")
    md.append("|---|---|---|---|---|")
    for _, row in validity_df.iterrows():
        md.append(
            f"| **{row['check_name']}** | {row['count']:,} | {row['pct_of_rows']:.4f}% | "
            f"{row['count_in_fraud']:,} | {row['comment']} |"
        )
    md.append("\n")

    md.append("## 3. Deep-Dive: Check 4 (Overdraft by Transaction Type)\n")
    md.append("The PaySim simulator does not permit negative balances; instead, whenever `amount > oldbalanceOrg`, `newbalanceOrig` is clamped at `0.0`.\n")
    md.append("| Transaction Type | Total Transactions | Overdraft Count | Overdraft Rate (%) | Overdraft in Fraud |")
    md.append("|---|---|---|---|---|")
    for t, row in overdraft_by_type.iterrows():
        md.append(
            f"| **{t}** | {int(row['total_tx']):,} | {int(row['overdraft_tx']):,} | "
            f"{row['overdraft_rate_pct']:.2f}% | {int(row['overdraft_fraud']):,} |"
        )
    md.append("\n")

    md.append("## 4. Deep-Dive: Check 7 (`isFlaggedFraud` Weakness Analysis)\n")
    recall_pct = (flagged_fraud / total_fraud) * 100
    md.append(f"- **Total Flagged Rows:** {flagged_count}")
    md.append(f"- **Flagged Rows that are Actually Fraud:** {flagged_fraud} (100.00% precision)")
    md.append(f"- **Total Actual Fraud in Dataset:** {total_fraud:,}")
    md.append(f"- **Empirical Recall of Rule:** **{recall_pct:.2f}%** (Misses {total_fraud - flagged_fraud:,} frauds or {100 - recall_pct:.2f}%)")
    md.append(f"- **Minimum Transaction Amount Among Flagged Rows:** **${flagged_min_amt:,.2f}**")
    md.append("- **Transaction Types Flagged:** Exclusively `TRANSFER`")
    md.append("\n### Crucial Architectural Decision:")
    md.append("> `isFlaggedFraud` represents a naive static rule baked into the PaySim simulator (flagging single transfer attempts > $200,000 under specific circumstances). Because it has near-zero recall (0.19%) and introduces severe target leakage / simulator bias, **it must NEVER be used as a model feature, nor as a benchmark for production detection systems**.\n")

    return "\n".join(md)


if __name__ == "__main__":
    run_validity_checks()
