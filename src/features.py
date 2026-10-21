"""Machine Learning Feature Engineering Module.

Single source of truth for ML feature engineering in the fraud detection pipeline.
Transforms scoped transactions (TRANSFER & CASH_OUT) into a clean, unskewed,
leakage-free feature matrix.
"""

from pathlib import Path
import sys
import numpy as np
import pandas as pd

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config

# Export canonical feature list and forbidden column list
FEATURE_COLUMNS = config.FEATURE_COLUMNS
FORBIDDEN_LEAKAGE_COLUMNS = config.FORBIDDEN_LEAKAGE_COLUMNS


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Build the canonical ML feature DataFrame from a scoped transaction DataFrame.

    Transforms raw and derived accounting fields into normalized, log-scaled,
    and clipped feature columns ready for machine learning model ingestion.
    Preserves the exact index of the input DataFrame.

    Args:
        df: Scoped DataFrame containing TRANSFER and CASH_OUT transactions
            with required raw and balance-derived columns.

    Returns:
        pd.DataFrame: Feature DataFrame with index matching df and exactly
            the columns in FEATURE_COLUMNS.

    Raises:
        AssertionError: If output contains NaNs, infinite values, incorrect columns,
            or target leakage / identifier columns.
    """
    features = pd.DataFrame(index=df.index)

    # 1. logAmt = log1p(amount)
    features["logAmt"] = np.log1p(df["amount"].astype(float))

    # 2. isTransfer = (type == "TRANSFER") as int8
    features["isTransfer"] = (df["type"] == "TRANSFER").astype("int8")

    # 3-6. Log-transformed balance fields
    features["logOldOrg"] = np.log1p(df["oldbalanceOrg"].astype(float))
    features["logNewOrig"] = np.log1p(df["newbalanceOrig"].astype(float))
    features["logOldDest"] = np.log1p(df["oldbalanceDest"].astype(float))
    features["logNewDest"] = np.log1p(df["newbalanceDest"].astype(float))

    # 7-8. Signed log-magnitude balance accounting errors
    features["errOrig_signed"] = (
        np.sign(df["errOrig"].astype(float)) * np.log1p(np.abs(df["errOrig"].astype(float)))
    )
    features["errDest_signed"] = (
        np.sign(df["errDest"].astype(float)) * np.log1p(np.abs(df["errDest"].astype(float)))
    )

    # 9-11. Behavioral indicator flags (int8)
    features["origEmptied"] = df["origEmptied"].astype("int8")
    features["destBalanceUnchanged"] = df["destBalanceUnchanged"].astype("int8")
    features["destIsMerchant"] = df["destIsMerchant"].astype("int8")

    # 12. Transaction amount to originator starting balance ratio (clipped to [0.0, 1.5])
    features["amtToBalanceRatio"] = (
        (df["amount"].astype(float) / (df["oldbalanceOrg"].astype(float) + 1.0))
        .clip(lower=0.0, upper=1.5)
        .astype(float)
    )

    # 13. Hour of day (int8, 0 to 23)
    features["hour"] = df["hour"].astype("int8")

    # Ensure exact column ordering matching FEATURE_COLUMNS
    features = features[FEATURE_COLUMNS]

    # --- Strict Integrity & Leakage Assertions ---
    assert list(features.columns) == FEATURE_COLUMNS, (
        f"Column mismatch! Expected: {FEATURE_COLUMNS}, Got: {list(features.columns)}"
    )
    assert len(features) == len(df), (
        f"Row count mismatch! Input has {len(df):,} rows, output has {len(features):,} rows"
    )
    assert (features.index == df.index).all(), "Feature index does not match input index"

    # NaN / Inf validation
    null_counts = features.isna().sum()
    assert null_counts.sum() == 0, f"NaN values detected in features:\n{null_counts[null_counts > 0]}"

    numeric_cols = features.select_dtypes(include=[np.number]).columns
    inf_mask = np.isinf(features[numeric_cols])
    assert not inf_mask.any().any(), (
        f"Infinite values detected in features:\n{inf_mask.sum()[inf_mask.sum() > 0]}"
    )

    # Strict Leakage & Identifier Guard
    for forbidden in FORBIDDEN_LEAKAGE_COLUMNS:
        assert forbidden not in features.columns, (
            f"CRITICAL LEAKAGE: Forbidden column '{forbidden}' found in feature matrix!"
        )

    return features


def main():
    """CLI execution: load clean parquet, filter scope, build features, and validate."""
    print("==================================================")
    print("Building Machine Learning Features (src/features.py)")
    print("==================================================")

    print(f"\nLoading cleaned master dataset from: {config.CLEAN_PARQUET.relative_to(config.PROJECT_ROOT)}")
    df_clean = pd.read_parquet(config.CLEAN_PARQUET)
    print(f"Total master dataset shape: {df_clean.shape[0]:,} rows, {df_clean.shape[1]} columns")

    # Filter to modeling scope: TRANSFER and CASH_OUT
    scoped_df = df_clean[df_clean["type"].isin(config.FRAUD_TYPES)].copy()
    print(f"Scoped dataset shape ({config.FRAUD_TYPES}): {scoped_df.shape[0]:,} rows, {scoped_df.shape[1]} columns")

    # Build features
    print("\nExecuting build_features()...")
    X = build_features(scoped_df)

    print(f"\nFeature matrix successfully generated:")
    print(f"  - Shape: {X.shape[0]:,} rows, {X.shape[1]} columns")
    print(f"  - Features count: {len(FEATURE_COLUMNS)}")
    print(f"  - Feature list: {FEATURE_COLUMNS}")

    # Leakage assertions
    print("\nVerifying absence of target and identifier leakage...")
    for forbidden in FORBIDDEN_LEAKAGE_COLUMNS:
        assert forbidden not in X.columns, f"Leakage detected: {forbidden}"
    print("  --> PASSED: No leakage columns (isFraud, isFlaggedFraud, nameOrig, nameDest, txn_id, step, day) present.")

    # NaN / Inf assertions
    print("\nVerifying absence of NaN and infinite values...")
    assert not X.isna().any().any(), "NaN values found"
    assert not np.isinf(X).any().any(), "Inf values found"
    print("  --> PASSED: 0 NaNs and 0 Infs across all feature columns.")

    # Describe features
    print("\n--- Feature Matrix Summary Statistics (describe) ---")
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 1000)
    print(X.describe().T[["count", "mean", "std", "min", "25%", "50%", "75%", "max"]])

    print("\nFeature engineering completed successfully.")


if __name__ == "__main__":
    main()
