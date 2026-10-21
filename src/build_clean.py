"""Master data pipeline module to generate transactions_clean.parquet."""

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
from src.balance_checks import add_balance_features
from src.outlier_analysis import add_outlier_features


def build_clean_dataset() -> pd.DataFrame:
    """Build the clean, consolidated, single-source-of-truth dataset.

    Pipeline operations:
    1. Loads raw CSV data via load_raw() with explicit dtypes.
    2. Assigns txn_id (int32) as 0-based original row position in raw CSV.
    3. Adds balance accounting discrepancy features via add_balance_features().
    4. Adds per-type outlier indicators via add_outlier_features().
    5. Adds temporal features: day (int8, 1..31) and hour (int8, 0..23).
    6. Appends isDuplicateRow (int8) to preserve all rows while tracking exact duplicates.
    7. Retains isFlaggedFraud strictly for reference (never to be used in ML).
    8. Orders columns canonically according to config.CLEAN_COLUMNS.
    9. Saves to config.CLEAN_PARQUET with snappy compression.
    10. Reloads and executes verification assertions.

    Returns:
        pd.DataFrame: Reloaded and verified clean DataFrame.
    """
    print("--- Step 1: Loading raw data ---")
    df = load_raw()

    # Step 1b: Define txn_id as 0-based original row position in raw CSV (int32)
    print("--- Step 2: Assigning txn_id ---")
    df[config.COL_TXN_ID] = np.arange(len(df), dtype="int32")

    # Step 1c: Add balance features
    print("--- Step 3: Adding balance features ---")
    df = add_balance_features(df)

    # Step 1d: Add outlier features
    print("--- Step 4: Adding outlier features ---")
    df = add_outlier_features(df)

    # Step 2: Add temporal features
    print("--- Step 5: Adding temporal features (day, hour) ---")
    df[config.COL_DAY] = ((df[config.COL_STEP] - 1) // 24 + 1).astype("int8")
    df[config.COL_HOUR] = ((df[config.COL_STEP] - 1) % 24).astype("int8")

    # Step 3: Identify full-row duplicates across raw columns without dropping any row
    print("--- Step 6: Tracking full-row duplicates ---")
    df[config.COL_IS_DUPLICATE_ROW] = df.duplicated(
        subset=config.ALL_COLUMNS, keep="first"
    ).astype("int8")

    # Step 4: isFlaggedFraud is retained strictly for historical auditing & reference
    # NOTE: isFlaggedFraud is simulator-internal and MUST NEVER be used as a model feature.

    # Step 5: Canonical column ordering
    print("--- Step 7: Ordering columns canonically ---")
    df_clean = df[config.CLEAN_COLUMNS].copy()

    # Step 6: Save to config.CLEAN_PARQUET using pyarrow with snappy compression
    print(f"--- Step 8: Writing to {config.CLEAN_PARQUET} ---")
    config.PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    df_clean.to_parquet(
        config.CLEAN_PARQUET,
        engine="pyarrow",
        compression="snappy",
        index=False,
    )
    print("Write complete.")

    # Step 7: Reload and verify assertions
    print(f"--- Step 9: Reloading and verifying {config.CLEAN_PARQUET.name} ---")
    reloaded = pd.read_parquet(config.CLEAN_PARQUET)

    # Assert 1: Same row count as raw
    assert len(reloaded) == config.EXPECTED_ROWS, (
        f"Row count mismatch: {len(reloaded):,} vs expected {config.EXPECTED_ROWS:,}"
    )
    print(f"  [PASS] Row count verified: {len(reloaded):,} rows")

    # Assert 2: txn_id unique and equals 0..N-1
    assert reloaded[config.COL_TXN_ID].nunique() == config.EXPECTED_ROWS, (
        "Duplicate txn_id detected!"
    )
    assert (
        reloaded[config.COL_TXN_ID].to_numpy() == np.arange(config.EXPECTED_ROWS, dtype="int32")
    ).all(), "txn_id does not equal exactly 0..N-1 sequence!"
    print("  [PASS] txn_id verified: unique and strictly equals 0..N-1 sequence")

    # Assert 3: No null values
    total_nulls = int(reloaded.isna().sum().sum())
    assert total_nulls == 0, f"Found {total_nulls} null values in clean dataset!"
    print(f"  [PASS] Null check verified: {total_nulls} nulls across all columns")

    # Assert 4: Dtypes match specification
    expected_dtypes = {
        config.COL_TXN_ID: "int32",
        config.COL_STEP: "int16",
        config.COL_DAY: "int8",
        config.COL_HOUR: "int8",
        config.COL_TYPE: "category",
        config.COL_AMOUNT: "float64",
        config.COL_NAME_ORIG: "string",
        config.COL_OLD_BALANCE_ORG: "float64",
        config.COL_NEW_BALANCE_ORIG: "float64",
        config.COL_NAME_DEST: "string",
        config.COL_OLD_BALANCE_DEST: "float64",
        config.COL_NEW_BALANCE_DEST: "float64",
        config.COL_ERR_ORIG: "float64",
        config.COL_ERR_DEST: "float64",
        config.COL_DEST_IS_MERCHANT: "int8",
        config.COL_ORIG_EMPTIED: "int8",
        config.COL_DEST_BALANCE_UNCHANGED: "int8",
        config.COL_ORIG_INCONSISTENT: "int8",
        config.COL_DEST_INCONSISTENT: "int8",
        config.COL_IS_AMOUNT_OUTLIER_IQR: "int8",
        config.COL_IS_TOP_1PCT_AMOUNT: "int8",
        config.COL_IS_DUPLICATE_ROW: "int8",
        config.COL_IS_FRAUD: "int8",
        config.COL_IS_FLAGGED_FRAUD: "int8",
    }
    for col, exp_dt in expected_dtypes.items():
        act_dt = reloaded[col].dtype.name
        if exp_dt == "string":
            assert act_dt in ["string", "object"], (
                f"Column {col} dtype mismatch: {act_dt} vs {exp_dt}"
            )
        else:
            assert act_dt == exp_dt, (
                f"Column {col} dtype mismatch: {act_dt} vs {exp_dt}"
            )
    print("  [PASS] Dtypes verified: all 24 columns match expected types")

    # Assert 5: Fraud count equals 8,213
    fraud_count = int(reloaded[config.COL_IS_FRAUD].sum())
    assert fraud_count == config.EXPECTED_FRAUD, (
        f"Fraud count mismatch: {fraud_count:,} vs expected {config.EXPECTED_FRAUD:,}"
    )
    print(f"  [PASS] Fraud count verified: {fraud_count:,} fraud records")

    # File size and preview
    file_size_mb = config.CLEAN_PARQUET.stat().st_size / (1024 * 1024)
    print("\n" + "=" * 80)
    print("MASTER CLEAN DATASET SUMMARY")
    print("=" * 80)
    print(f"Parquet File Path: {config.CLEAN_PARQUET}")
    print(f"Parquet File Size: {file_size_mb:.2f} MB")
    print(f"Total Rows:        {len(reloaded):,}")
    print(f"Total Columns:     {len(reloaded.columns)}")
    print("\nFirst 3 Rows:")
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 1000)
    print(reloaded.head(3))
    print("=" * 80)

    return reloaded


if __name__ == "__main__":
    build_clean_dataset()
