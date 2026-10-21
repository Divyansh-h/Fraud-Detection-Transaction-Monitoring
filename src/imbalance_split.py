"""Stratified data splitting and class imbalance strategy module."""

import sys
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config
from src.load_data import load_raw


def create_imbalance_splits(df: pd.DataFrame | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Scope data to TRANSFER & CASH_OUT, generate stratified splits, and save assignment parquet.

    Args:
        df: Optional preloaded raw DataFrame. If None, loaded via load_raw().

    Returns:
        tuple[pd.DataFrame, pd.DataFrame]: (split_table_df, split_assignment_df)
    """
    if df is None:
        df = load_raw()

    # Step 1: Assign txn_id (0-based original row position in raw CSV, int32)
    # This is the single source of truth for transaction IDs across all downstream modules.
    df[config.COL_TXN_ID] = np.arange(len(df), dtype="int32")

    total_raw_rows = len(df)
    total_raw_fraud = int(df[config.COL_IS_FRAUD].sum())
    overall_no_fraud_acc = ((total_raw_rows - total_raw_fraud) / total_raw_rows) * 100

    # Step 2: Restrict to modeling scope: TRANSFER and CASH_OUT
    scoped_mask = df[config.COL_TYPE].isin(config.FRAUD_TYPES)
    scoped_df = df.loc[scoped_mask, [config.COL_TXN_ID, config.COL_TYPE, config.COL_IS_FRAUD]].copy()

    scoped_rows = len(scoped_df)
    scoped_fraud = int(scoped_df[config.COL_IS_FRAUD].sum())
    scoped_fraud_rate = (scoped_fraud / scoped_rows) * 100
    scoped_no_fraud_acc = ((scoped_rows - scoped_fraud) / scoped_rows) * 100

    print("\n--- Modeling Scope Filter ---")
    print(f"Scoped Transaction Types: {config.FRAUD_TYPES}")
    print(f"Scoped Row Count:         {scoped_rows:,} (Expected: ~2,770,409)")
    print(f"Scoped Fraud Count:       {scoped_fraud:,} (Expected: 8,213)")
    print(f"Scoped Fraud Rate:        {scoped_fraud_rate:.4f}% (Expected: ~0.30%)")

    # Step 3: Stratified split: 60% train, 20% validation, 20% test
    # First split: 60% train, 40% temp
    train_data, temp_data = train_test_split(
        scoped_df,
        test_size=(config.VAL_RATIO + config.TEST_RATIO),
        stratify=scoped_df[config.COL_IS_FRAUD],
        random_state=config.RANDOM_SEED,
    )

    # Second split: 50% of temp = 20% validation, 50% of temp = 20% test
    val_data, test_data = train_test_split(
        temp_data,
        test_size=0.50,
        stratify=temp_data[config.COL_IS_FRAUD],
        random_state=config.RANDOM_SEED,
    )

    # Compute metrics for each split
    splits_summary = []
    split_dfs = [("train", train_data), ("val", val_data), ("test", test_data)]
    for name, s_df in split_dfs:
        n_rows = len(s_df)
        n_fraud = int(s_df[config.COL_IS_FRAUD].sum())
        f_rate = (n_fraud / n_rows) * 100
        pct_of_scope = (n_rows / scoped_rows) * 100
        splits_summary.append({
            "split": name,
            "rows": n_rows,
            "pct_of_scope": pct_of_scope,
            "fraud_rows": n_fraud,
            "fraud_rate_pct": f_rate,
        })

    split_table = pd.DataFrame(splits_summary)

    # Step 4: Assert fraud proportions are within 0.02 percentage points
    rates = split_table["fraud_rate_pct"].tolist()
    max_rate_diff = max(rates) - min(rates)
    assert max_rate_diff <= 0.02, (
        f"Fraud rates mismatch across splits: {rates} (diff = {max_rate_diff:.6f}% > 0.02%)"
    )

    # Step 5: Build split_assignment DataFrame with txn_id and split
    train_assign = pd.DataFrame({
        config.COL_TXN_ID: train_data[config.COL_TXN_ID].astype("int32"),
        config.COL_SPLIT: "train",
    })
    val_assign = pd.DataFrame({
        config.COL_TXN_ID: val_data[config.COL_TXN_ID].astype("int32"),
        config.COL_SPLIT: "val",
    })
    test_assign = pd.DataFrame({
        config.COL_TXN_ID: test_data[config.COL_TXN_ID].astype("int32"),
        config.COL_SPLIT: "test",
    })

    split_assignment = pd.concat([train_assign, val_assign, test_assign], ignore_index=True)
    split_assignment = split_assignment.sort_values(config.COL_TXN_ID).reset_index(drop=True)

    # Verification assertions on split assignment
    assert len(split_assignment) == scoped_rows, (
        f"Length mismatch: {len(split_assignment)} vs {scoped_rows}"
    )
    dup_txns = split_assignment[config.COL_TXN_ID].duplicated().sum()
    assert dup_txns == 0, f"Found {dup_txns} duplicate txn_ids in split_assignment!"
    assert list(split_assignment.columns) == [config.COL_TXN_ID, config.COL_SPLIT], (
        f"Unexpected columns: {list(split_assignment.columns)}"
    )

    # Save to data/processed/split_assignment.parquet
    config.PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    split_assignment.to_parquet(config.SPLIT_ASSIGNMENT_PARQUET, index=False)
    print(f"Saved: {config.SPLIT_ASSIGNMENT_PARQUET}")

    # Step 6: Write reports/06_imbalance_strategy.md
    config.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    md_content = generate_markdown_report(
        scoped_rows=scoped_rows,
        scoped_fraud=scoped_fraud,
        scoped_fraud_rate=scoped_fraud_rate,
        total_raw_rows=total_raw_rows,
        total_raw_fraud=total_raw_fraud,
        overall_no_fraud_acc=overall_no_fraud_acc,
        scoped_no_fraud_acc=scoped_no_fraud_acc,
        split_table=split_table,
        max_rate_diff=max_rate_diff,
    )
    with open(config.IMBALANCE_REPORT_MD, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"Saved: {config.IMBALANCE_REPORT_MD}")

    # Step 7: Print clean table to console
    print("\n" + "=" * 75)
    print("STRATIFIED DATA SPLIT SUMMARY (TRANSFER & CASH_OUT)")
    print("=" * 75)
    print(split_table.to_string(index=False))
    print("-" * 75)
    print(f"Max difference between split fraud rates: {max_rate_diff:.6f} percentage points (<= 0.02% threshold: PASS)")
    print(f"Trivial Majority Classifier Accuracy ('Always predict no fraud'):")
    print(f"  - Full Dataset (6.36M rows): {overall_no_fraud_acc:.4f}%")
    print(f"  - Scoped Dataset (2.77M rows): {scoped_no_fraud_acc:.4f}%")
    print(f"Single source of truth assignment saved to: {config.SPLIT_ASSIGNMENT_PARQUET.name}")
    print("=" * 75)

    return split_table, split_assignment


def generate_markdown_report(
    scoped_rows: int,
    scoped_fraud: int,
    scoped_fraud_rate: float,
    total_raw_rows: int,
    total_raw_fraud: int,
    overall_no_fraud_acc: float,
    scoped_no_fraud_acc: float,
    split_table: pd.DataFrame,
    max_rate_diff: float,
) -> str:
    """Format markdown report with methodology, split statistics, and evaluation guidelines."""
    md = []
    md.append("# Class Imbalance and Data Splitting Strategy Report\n")

    md.append("## 1. Modeling Scope Definition\n")
    md.append("Machine learning and detection algorithms are strictly confined to transaction types where fraud exists:")
    md.append(f"- **In-Scope Types:** `TRANSFER` and `CASH_OUT`")
    md.append(f"- **In-Scope Transactions:** {scoped_rows:,} ({scoped_rows / total_raw_rows * 100:.2f}% of the total dataset)")
    md.append(f"- **In-Scope Fraud Cases:** {scoped_fraud:,} (100.00% of all fraud in the dataset)")
    md.append(f"- **In-Scope Fraud Prevalence:** **{scoped_fraud_rate:.4f}%** (~0.30%)\n")
    md.append("> **Architectural Justification:** In previous profiling, `CASH_IN`, `DEBIT`, and `PAYMENT` showed **exactly 0** fraud cases across 3,592,211 rows. Training models on 0% fraud types introduces unnecessary computational overhead and distorts decision boundaries. These non-scoped transactions remain fully available for portfolio-level analytics and executive dashboard totals, while ML models focus on fraud-active channels.\n")

    md.append("## 2. Stratified Data Split\n")
    md.append("To prevent data leakage while preserving class distribution across train, validation, and test partitions, stratified sampling was applied on `isFraud` with `random_state=42`:\n")
    md.append("| Split | Rows | % of Scope | Fraud Rows | Fraud Rate (%) |")
    md.append("|---|---|---|---|---|")
    for _, row in split_table.iterrows():
        md.append(
            f"| **{row['split']}** | {int(row['rows']):,} | {row['pct_of_scope']:.1f}% | "
            f"{int(row['fraud_rows']):,} | {row['fraud_rate_pct']:.4f}% |"
        )
    md.append(f"\n- **Stratification Quality:** Maximum difference in fraud rate across splits is **{max_rate_diff:.6f} percentage points**, well within the 0.02 percentage point tolerance.\n")

    md.append("## 3. Why Accuracy is a Misleading Metric\n")
    md.append(f"In highly imbalanced datasets, raw classification accuracy is fundamentally deceptive. A trivial dummy model that predicts \"no fraud\" for every transaction achieves:")
    md.append(f"- **{overall_no_fraud_acc:.2f}% accuracy** on the full dataset ({overall_no_fraud_acc:.4f}%)")
    md.append(f"- **{scoped_no_fraud_acc:.2f}% accuracy** on the scoped dataset ({scoped_no_fraud_acc:.4f}%)\n")
    md.append("Such a model catches 0 fraud events (0% recall) yet appears virtually flawless under accuracy. Consequently, **accuracy is strictly banned as an evaluation metric** in this project.\n")

    md.append("## 4. Imbalance-Aware Evaluation Metrics\n")
    md.append("All rule-based and machine-learning models will be evaluated strictly using:")
    md.append("1. **Precision (Positive Predictive Value):** Avoid wasting compliance officer time on false alerts.")
    md.append("2. **Recall (Sensitivity / Detection Rate):** Maximize recovery of fraudulent funds.")
    md.append("3. **False Positive Rate (FPR):** Monitor operational impact on legitimate customers.")
    md.append("4. **F1-Score / PR-AUC (Precision-Recall Area Under Curve):** Benchmark overall detection tradeoff without distortion from majority negatives.\n")

    md.append("## 5. Handling Imbalance Without Synthetic Oversampling (No SMOTE)\n")
    md.append("- **No SMOTE or Synthetic Oversampling:** SMOTE synthesizes artificial minority points via nearest neighbors, which distorts boundary distributions and risks generating unrealistic financial account states. Furthermore, unsupervised anomaly detectors like **Isolation Forest** learn density topology on uncontaminated empirical distributions.\n")

    md.append("## 6. Single Source of Truth for Identifiers (`txn_id`)\n")
    md.append(f"- **Identifier (`txn_id`):** Defined as the 0-based original row position in the raw CSV (`int32`).")
    md.append(f"- **Artifact Generated:** `{config.SPLIT_ASSIGNMENT_PARQUET.name}` containing exactly `{len(split_table):,}` partitions across `{scoped_rows:,}` transactions with **0 duplicate IDs**.\n")

    return "\n".join(md)


if __name__ == "__main__":
    create_imbalance_splits()
