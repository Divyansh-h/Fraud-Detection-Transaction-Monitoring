"""Machine Learning Dataset Preparation Module.

Extracts scoped transactions, computes canonical ML features via build_features(),
partitions records into Train (60%), Validation (20%), and Test (20%) datasets
based on pre-assigned stratified splits, and exports partitioned Parquet files.
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
from src.features import build_features


def generate_ml_data_notes(split_stats: dict[str, dict], output_path: Path) -> None:
    """Generate reports/09_ml_data_notes.md documenting modeling philosophy and split partitions."""
    total_rows = sum(s["rows"] for s in split_stats.values())
    total_fraud = sum(s["fraud"] for s in split_stats.values())

    content = f"""# Machine Learning Data Preparation & Modeling Architecture Notes

**Document ID:** `09_ml_data_notes.md`  
**Modeling Scope:** `TRANSFER` and `CASH_OUT` transactions only ($N = {total_rows:,}$)  
**Total Target Fraud Events:** {total_fraud:,}  
**Master Input Source:** `{config.CLEAN_PARQUET.name}`  
**Split Assignment Source:** `{config.SPLIT_ASSIGNMENT_PARQUET.name}`  

---

## 1. Partition Distribution & Stratification Audit

The scoped dataset is partitioned into three disjoint sets using row-index stratified splitting (`random_state={config.RANDOM_SEED}`) on `isFraud`:

| Split Partition | File Artifact | Row Count | Share of Scope | Fraud Count | Fraud Rate |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Train (60%)** | `ml_train.parquet` | {split_stats['train']['rows']:,} | {split_stats['train']['rows']/total_rows*100:.2f}% | {split_stats['train']['fraud']:,} | {split_stats['train']['rate']:.4f}% |
| **Validation (20%)** | `ml_val.parquet` | {split_stats['val']['rows']:,} | {split_stats['val']['rows']/total_rows*100:.2f}% | {split_stats['val']['fraud']:,} | {split_stats['val']['rate']:.4f}% |
| **Test (20%)** | `ml_test.parquet` | {split_stats['test']['rows']:,} | {split_stats['test']['rows']/total_rows*100:.2f}% | {split_stats['test']['fraud']:,} | {split_stats['test']['rate']:.4f}% |
| **Total Scope** | **Combined** | **{total_rows:,}** | **100.00%** | **{total_fraud:,}** | **{total_fraud/total_rows*100:.4f}%** |

---

## 2. Feature Schema & Column Layout

Each partitioned dataset (`ml_train.parquet`, `ml_val.parquet`, `ml_test.parquet`) contains exactly **15 columns**:
1. `txn_id` (`int32`): Global unique transaction identifier (row position in raw dataset).
2. `logAmt` (`float64`): `log1p(amount)`.
3. `isTransfer` (`int8`): Binary indicator (1 for `TRANSFER`, 0 for `CASH_OUT`).
4. `logOldOrg` (`float64`): `log1p(oldbalanceOrg)`.
5. `logNewOrig` (`float64`): `log1p(newbalanceOrig)`.
6. `logOldDest` (`float64`): `log1p(oldbalanceDest)`.
7. `logNewDest` (`float64`): `log1p(newbalanceDest)`.
8. `errOrig_signed` (`float64`): Signed log-magnitude origin accounting discrepancy.
9. `errDest_signed` (`float64`): Signed log-magnitude destination accounting discrepancy.
10. `origEmptied` (`int8`): Balance drained to zero indicator.
11. `destBalanceUnchanged` (`int8`): Destination balance unchanged indicator.
12. `destIsMerchant` (`int8`): Destination merchant indicator.
13. `amtToBalanceRatio` (`float64`): Transaction amount to origin balance ratio (clipped to $[0.0, 1.5]$).
14. `hour` (`int8`): Cyclical time feature ($0 \dots 23$).
15. `isFraud` (`int8`): Ground truth target label (evaluation only).

---

## 3. Modeling Philosophy: Unsupervised Isolation Forest

1. **Unsupervised Training on Train Features Only:**
   - The Isolation Forest anomaly detector is trained **strictly on the feature matrix of `ml_train.parquet` without labels** (`isFraud` is completely withheld during `model.fit()`).
   - In production financial crime systems, newly emerging attack vectors and zero-day fraud rings operate without historical ground-truth annotations. The model learns the multi-dimensional geometric topology of legitimate banking behavior purely through recursive tree isolation depth.

2. **Validation Set for Evaluation and Threshold Calibration:**
   - Ground truth labels (`isFraud`) are introduced **only during validation on `ml_val.parquet`**.
   - Hyperparameter search (number of estimators, max samples) and anomaly score threshold tuning (decision boundary / contamination percentile) are performed **strictly against the Validation set**.

3. **Strict No-Test-Tuning Rule:**
   - **The Test dataset (`ml_test.parquet`) is held out in an isolated evaluation vault and is NEVER used for tuning, contamination calibration, feature selection, or iterative threshold adjustments.**
   - The test set is evaluated exactly once at the conclusion of model selection to provide an uncompromised, unbiased measurement of out-of-sample generalization performance on unseen production data.

---

## 4. Partition Integrity & Leakage Guarantees

- **Disjoint Identifiers:** Pairwise intersection checks confirm that no transaction identifier (`txn_id`) appears in more than one partition:
  $$\\text{{Train}} \\cap \\text{{Val}} = \\emptyset, \\quad \\text{{Train}} \\cap \\text{{Test}} = \\emptyset, \\quad \\text{{Val}} \\cap \\text{{Test}} = \\emptyset$$
- **Identifier & Target Leakage Prevention:** High-cardinality identity strings (`nameOrig`, `nameDest`), simulation timestamps (`step`, `day`), and synthetic reference flags (`isFlaggedFraud`) are strictly excluded from all training feature vectors.
"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)


def prepare_ml_data() -> dict[str, pd.DataFrame]:
    """Execute end-to-end ML dataset preparation, partitioning, and Parquet export.

    Returns:
        dict[str, pd.DataFrame]: Dictionary containing 'train', 'val', and 'test' DataFrames.
    """
    t_start = time.perf_counter()
    print("==================================================")
    print("Preparing ML Datasets (src/prepare_ml_data.py)")
    print("==================================================")

    # 1. Load clean master parquet and filter to modeling scope
    print(f"\n[1/5] Loading cleaned master data from: {config.CLEAN_PARQUET.relative_to(config.PROJECT_ROOT)}")
    df_clean = pd.read_parquet(config.CLEAN_PARQUET)
    scoped_df = df_clean[df_clean["type"].isin(config.FRAUD_TYPES)].copy()
    print(f"  - Master rows: {len(df_clean):,}")
    print(f"  - Scoped rows ({config.FRAUD_TYPES}): {len(scoped_df):,}")
    assert len(scoped_df) == config.EXPECTED_SCOPED_ROWS, (
        f"Scoped row count mismatch: expected {config.EXPECTED_SCOPED_ROWS:,}, got {len(scoped_df):,}"
    )

    # 2. Build canonical features
    print("\n[2/5] Building feature matrix with build_features()...")
    X = build_features(scoped_df)
    X[config.COL_TXN_ID] = scoped_df[config.COL_TXN_ID].values
    X[config.COL_IS_FRAUD] = scoped_df[config.COL_IS_FRAUD].values
    print(f"  - Features built: {len(config.FEATURE_COLUMNS)} columns")

    # 3. Join with split_assignment.parquet on txn_id
    print(f"\n[3/5] Merging split assignments from: {config.SPLIT_ASSIGNMENT_PARQUET.relative_to(config.PROJECT_ROOT)}")
    split_df = pd.read_parquet(config.SPLIT_ASSIGNMENT_PARQUET)
    merged = X.merge(split_df, on=config.COL_TXN_ID, how="left")

    # Assert every scoped row has an assigned split
    missing_splits = merged[config.COL_SPLIT].isna().sum()
    assert missing_splits == 0, f"Found {missing_splits:,} scoped rows missing a split assignment!"
    print("  --> Assertion PASSED: Every scoped transaction has an assigned split.")

    # 4. Partition datasets and export to Parquet
    print("\n[4/5] Partitioning datasets and writing Parquet files...")
    target_columns = [config.COL_TXN_ID] + config.FEATURE_COLUMNS + [config.COL_IS_FRAUD]

    split_configs = {
        "train": (config.ML_TRAIN_PARQUET, "ml_train.parquet"),
        "val": (config.ML_VAL_PARQUET, "ml_val.parquet"),
        "test": (config.ML_TEST_PARQUET, "ml_test.parquet"),
    }

    datasets = {}
    split_stats = {}
    seen_ids = set()

    print("\nSplit Partition Summary:")
    print("-" * 65)
    print(f"{'Split':<8} {'Rows':<12} {'Share':<10} {'Fraud Rows':<12} {'Fraud Rate':<10}")
    print("-" * 65)

    for split_name, (out_path, file_name) in split_configs.items():
        sub_df = merged[merged[config.COL_SPLIT] == split_name][target_columns].copy()
        
        # Validate uniqueness and disjoint partition
        sub_ids = set(sub_df[config.COL_TXN_ID].values)
        overlap = seen_ids.intersection(sub_ids)
        assert len(overlap) == 0, f"Overlap detected between splits: {len(overlap)} duplicate txn_ids!"
        seen_ids.update(sub_ids)

        # Write Parquet with snappy compression
        sub_df.to_parquet(out_path, compression="snappy", index=False)
        size_mb = out_path.stat().st_size / (1024 * 1024)

        rows = len(sub_df)
        fraud = int(sub_df[config.COL_IS_FRAUD].sum())
        rate = 100.0 * fraud / rows if rows > 0 else 0.0
        share = 100.0 * rows / len(merged)

        split_stats[split_name] = {
            "rows": rows,
            "fraud": fraud,
            "rate": rate,
            "share": share,
            "size_mb": size_mb,
        }
        datasets[split_name] = sub_df

        print(f"{split_name:<8} {rows:<12,} {share:>6.2f}%    {fraud:<12,} {rate:>6.4f}%")

    print("-" * 65)

    # Assert total partition matches scoped rows
    total_partitioned = sum(s["rows"] for s in split_stats.values())
    assert total_partitioned == len(scoped_df), (
        f"Total partitioned rows ({total_partitioned:,}) != scoped rows ({len(scoped_df):,})"
    )

    # 5. Generate Documentation Report
    print(f"\n[5/5] Generating documentation report: {config.ML_DATA_NOTES_MD.relative_to(config.PROJECT_ROOT)}")
    generate_ml_data_notes(split_stats, config.ML_DATA_NOTES_MD)

    total_time = time.perf_counter() - t_start
    print(f"\nML data preparation completed successfully in {total_time:.2f}s.")
    return datasets


def main():
    """CLI execution entrypoint."""
    prepare_ml_data()


if __name__ == "__main__":
    main()
