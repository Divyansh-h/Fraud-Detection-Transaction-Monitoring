"""Module for loading and validating the raw PaySim dataset."""

import sys
from pathlib import Path
from typing import Optional
import pandas as pd

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config

RAW_DTYPES = {
    config.COL_STEP: "int16",
    config.COL_TYPE: "category",
    config.COL_AMOUNT: "float64",
    config.COL_NAME_ORIG: "string",
    config.COL_OLD_BALANCE_ORG: "float64",
    config.COL_NEW_BALANCE_ORIG: "float64",
    config.COL_NAME_DEST: "string",
    config.COL_OLD_BALANCE_DEST: "float64",
    config.COL_NEW_BALANCE_DEST: "float64",
    config.COL_IS_FRAUD: "int8",
    config.COL_IS_FLAGGED_FRAUD: "int8",
}

EXPECTED_DTYPE_NAMES = {
    config.COL_STEP: {"int16"},
    config.COL_TYPE: {"category"},
    config.COL_AMOUNT: {"float64"},
    config.COL_NAME_ORIG: {"string", "object"},
    config.COL_OLD_BALANCE_ORG: {"float64"},
    config.COL_NEW_BALANCE_ORIG: {"float64"},
    config.COL_NAME_DEST: {"string", "object"},
    config.COL_OLD_BALANCE_DEST: {"float64"},
    config.COL_NEW_BALANCE_DEST: {"float64"},
    config.COL_IS_FRAUD: {"int8"},
    config.COL_IS_FLAGGED_FRAUD: {"int8"},
}


def validate_schema(df: pd.DataFrame) -> None:
    """Validate that df contains exactly the expected columns with matching dtypes."""
    expected_cols = list(RAW_DTYPES.keys())
    actual_cols = list(df.columns)

    missing_cols = set(expected_cols) - set(actual_cols)
    extra_cols = set(actual_cols) - set(expected_cols)

    mismatches = []
    if missing_cols:
        mismatches.append(f"Missing columns: {sorted(missing_cols)}")
    if extra_cols:
        mismatches.append(f"Unexpected extra columns: {sorted(extra_cols)}")

    for col in expected_cols:
        if col in df.columns:
            actual_dtype = df[col].dtype.name
            allowed_dtypes = EXPECTED_DTYPE_NAMES[col]
            if actual_dtype not in allowed_dtypes:
                mismatches.append(
                    f"Column '{col}' dtype mismatch: expected one of {allowed_dtypes}, got '{actual_dtype}'"
                )

    if mismatches:
        raise ValueError(
            "Schema validation failed:\n" + "\n".join(f"- {m}" for m in mismatches)
        )


def load_raw(
    nrows: Optional[int] = None, filepath: Optional[Path | str] = None
) -> pd.DataFrame:
    """Read the raw PaySim CSV file efficiently with explicit dtypes and validate schema.

    Args:
        nrows: Optional number of rows to read.
        filepath: Optional path to the CSV file (defaults to config.RAW_CSV).

    Returns:
        pd.DataFrame: Cleanly typed and validated raw transaction DataFrame.

    Raises:
        FileNotFoundError: If the raw CSV does not exist.
        ValueError: If schema validation fails.
    """
    csv_path = Path(filepath) if filepath is not None else config.RAW_CSV

    if not csv_path.exists():
        raise FileNotFoundError(
            f"Download PaySim from Kaggle (ealaxi/paysim1) and place it at {csv_path}"
        )

    print(f"Loading raw data from: {csv_path}")
    if nrows is not None:
        print(f"Reading first {nrows:,} rows...")

    df = pd.read_csv(csv_path, dtype=RAW_DTYPES, nrows=nrows)

    # Schema validation
    validate_schema(df)

    # Row count & fraud count checks (when loading the entire file)
    if nrows is None:
        if len(df) != config.EXPECTED_ROWS:
            print(
                f"WARNING: Expected {config.EXPECTED_ROWS:,} rows, but loaded {len(df):,} rows."
            )
        fraud_count = int(df[config.COL_IS_FRAUD].sum())
        if fraud_count != config.EXPECTED_FRAUD:
            print(
                f"WARNING: Expected {config.EXPECTED_FRAUD:,} fraud records, but found {fraud_count:,}."
            )

    # Memory usage
    mem_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
    print(f"Memory footprint: {mem_mb:.2f} MB")

    return df


if __name__ == "__main__":
    df = load_raw()
    print("\n--- Dataset Summary ---")
    print(f"Shape: {df.shape}")
    print("\nDtypes:")
    print(df.dtypes)
    print("\nHead (5 rows):")
    print(df.head())
    fraud_total = int(df[config.COL_IS_FRAUD].sum())
    print(f"\nTotal Fraud Count: {fraud_total:,}")
    mem_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
    print(f"Total Memory Usage: {mem_mb:.2f} MB")
