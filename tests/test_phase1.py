"""Pytest test suite for Phase 1 data validation and pipeline outputs."""

import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config


@pytest.fixture(scope="module")
def clean_df() -> pd.DataFrame:
    """Fixture to load transactions_clean.parquet once for the test module."""
    assert config.CLEAN_PARQUET.exists(), f"Missing clean parquet at {config.CLEAN_PARQUET}"
    return pd.read_parquet(config.CLEAN_PARQUET)


@pytest.fixture(scope="module")
def split_df() -> pd.DataFrame:
    """Fixture to load split_assignment.parquet once for the test module."""
    assert (
        config.SPLIT_ASSIGNMENT_PARQUET.exists()
    ), f"Missing split assignment parquet at {config.SPLIT_ASSIGNMENT_PARQUET}"
    return pd.read_parquet(config.SPLIT_ASSIGNMENT_PARQUET)


def test_clean_parquet_exists():
    """Verify that transactions_clean.parquet exists and has positive size."""
    assert config.CLEAN_PARQUET.exists(), "transactions_clean.parquet does not exist"
    assert config.CLEAN_PARQUET.stat().st_size > 0, "transactions_clean.parquet is empty"


def test_row_count(clean_df: pd.DataFrame):
    """Verify row count strictly equals EXPECTED_ROWS (6,362,620)."""
    assert (
        len(clean_df) == config.EXPECTED_ROWS
    ), f"Row count {len(clean_df):,} != expected {config.EXPECTED_ROWS:,}"


def test_txn_id_unique(clean_df: pd.DataFrame):
    """Verify txn_id is strictly unique and equals the 0..N-1 sequence."""
    assert (
        clean_df[config.COL_TXN_ID].nunique() == config.EXPECTED_ROWS
    ), "txn_id column contains duplicates or missing IDs"
    assert (
        clean_df[config.COL_TXN_ID].to_numpy()
        == np.arange(config.EXPECTED_ROWS, dtype="int32")
    ).all(), "txn_id does not form a strict 0..N-1 sequence"


def test_fraud_count(clean_df: pd.DataFrame):
    """Verify total fraud count strictly equals EXPECTED_FRAUD (8,213)."""
    total_fraud = int(clean_df[config.COL_IS_FRAUD].sum())
    assert (
        total_fraud == config.EXPECTED_FRAUD
    ), f"Fraud count {total_fraud:,} != expected {config.EXPECTED_FRAUD:,}"


def test_fraud_only_in_transfer_and_cash_out(clean_df: pd.DataFrame):
    """Verify that fraud cases occur strictly in TRANSFER and CASH_OUT."""
    outside_scope_fraud = int(
        clean_df.loc[
            ~clean_df[config.COL_TYPE].isin(config.FRAUD_TYPES), config.COL_IS_FRAUD
        ].sum()
    )
    assert (
        outside_scope_fraud == 0
    ), f"Fraud detected outside TRANSFER/CASH_OUT: {outside_scope_fraud} cases"

    # Also verify that both TRANSFER and CASH_OUT contain fraud
    tf_fraud = int(clean_df.loc[clean_df[config.COL_TYPE] == "TRANSFER", config.COL_IS_FRAUD].sum())
    co_fraud = int(clean_df.loc[clean_df[config.COL_TYPE] == "CASH_OUT", config.COL_IS_FRAUD].sum())
    assert tf_fraud > 0, "No fraud found in TRANSFER transactions"
    assert co_fraud > 0, "No fraud found in CASH_OUT transactions"
    assert tf_fraud + co_fraud == config.EXPECTED_FRAUD


def test_no_nulls(clean_df: pd.DataFrame):
    """Verify zero null or missing values exist in the cleaned dataset."""
    null_counts = clean_df.isna().sum().sum()
    assert null_counts == 0, f"Found {null_counts} null values in cleaned dataset"


def test_required_columns_exist(clean_df: pd.DataFrame):
    """Verify that required temporal, balance, and indicator columns exist."""
    required_cols = [
        config.COL_DAY,
        config.COL_HOUR,
        config.COL_ERR_ORIG,
        config.COL_ERR_DEST,
        config.COL_ORIG_EMPTIED,
        config.COL_DEST_IS_MERCHANT,
    ]
    for col in required_cols:
        assert (
            col in clean_df.columns
        ), f"Missing required column '{col}' in cleaned dataset"


def test_split_assignment_coverage_and_uniqueness(
    clean_df: pd.DataFrame, split_df: pd.DataFrame
):
    """Verify split_assignment has no overlap and covers every in-scope row exactly once."""
    # 1. Check columns
    assert list(split_df.columns) == [
        config.COL_TXN_ID,
        config.COL_SPLIT,
    ], f"Unexpected columns in split_df: {list(split_df.columns)}"

    # 2. Check no duplicates
    assert (
        split_df[config.COL_TXN_ID].duplicated().sum() == 0
    ), "Duplicate txn_ids found in split_assignment"

    # 3. Check allowed split partitions with no overlap
    valid_splits = {"train", "val", "test"}
    actual_splits = set(split_df[config.COL_SPLIT].unique())
    assert actual_splits.issubset(
        valid_splits
    ), f"Invalid split names: {actual_splits - valid_splits}"

    # 4. Check exact coverage of all in-scope rows
    in_scope_ids = set(
        clean_df.loc[
            clean_df[config.COL_TYPE].isin(config.FRAUD_TYPES), config.COL_TXN_ID
        ].to_numpy()
    )
    split_ids = set(split_df[config.COL_TXN_ID].to_numpy())

    assert len(split_df) == len(
        in_scope_ids
    ), f"Split count {len(split_df):,} != in-scope count {len(in_scope_ids):,}"
    assert split_ids == in_scope_ids, "split_assignment does not exactly match in-scope txn_ids"
