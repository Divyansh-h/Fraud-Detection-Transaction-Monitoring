"""Pytest test suite for Phase 2: Transaction Monitoring Rule Engine."""

import pytest
import pandas as pd
import pyarrow.parquet as pq

import config

RULE_COLS = [
    "rule_emptied",
    "rule_large_amount",
    "rule_velocity",
    "rule_transfer_then_cashout",
    "rule_mule_dest",
    "rule_dest_unchanged",
    "rule_balance_error",
]

ALERT_COLS = [
    "is_rule_alert_1",
    "is_rule_alert_2",
]


@pytest.fixture(scope="module")
def rule_flags_df() -> pd.DataFrame:
    """Fixture providing loaded rule_flags Parquet dataset for Phase 2 assertions."""
    assert config.RULE_FLAGS_PARQUET.exists(), f"Missing rule_flags Parquet file at {config.RULE_FLAGS_PARQUET}"
    df = pd.read_parquet(config.RULE_FLAGS_PARQUET)
    return df


def test_rule_flags_parquet_exists():
    """Assert data/outputs/rule_flags.parquet and preview CSV exist."""
    assert config.RULE_FLAGS_PARQUET.exists(), "rule_flags.parquet does not exist"
    assert config.RULE_FLAGS_PREVIEW_CSV.exists(), "rule_flags_head1000.csv does not exist"
    assert config.RULE_FLAGS_PARQUET.stat().st_size > 0, "rule_flags.parquet is empty"


def test_rule_flags_row_count(rule_flags_df: pd.DataFrame):
    """Assert row count equals exactly the expected scoped row count (2,770,409)."""
    assert len(rule_flags_df) == config.EXPECTED_SCOPED_ROWS, (
        f"Expected {config.EXPECTED_SCOPED_ROWS:,} scoped rows, found {len(rule_flags_df):,}"
    )


def test_rule_flags_txn_id_unique(rule_flags_df: pd.DataFrame):
    """Assert txn_id is strictly unique and contains no nulls."""
    assert rule_flags_df["txn_id"].nunique() == len(rule_flags_df), (
        "Duplicate txn_id values detected in rule_flags"
    )
    assert not rule_flags_df["txn_id"].isna().any(), "Null txn_id values detected"


def test_rule_columns_binary(rule_flags_df: pd.DataFrame):
    """Assert all rule flags and alert flags contain only binary 0 or 1 values."""
    for col in RULE_COLS + ALERT_COLS:
        assert col in rule_flags_df.columns, f"Missing expected rule column: {col}"
        unique_vals = set(rule_flags_df[col].unique())
        assert unique_vals.issubset({0, 1}), (
            f"Column {col} contains non-binary values: {unique_vals}"
        )


def test_alert_score_equals_sum_of_rules(rule_flags_df: pd.DataFrame):
    """Assert alert_score equals the exact sum of the seven rule flags for every row."""
    assert "alert_score" in rule_flags_df.columns, "Missing alert_score column"
    sum_flags = rule_flags_df[RULE_COLS].sum(axis=1)
    diffs = (rule_flags_df["alert_score"] != sum_flags).sum()
    assert diffs == 0, f"Found {diffs:,} rows where alert_score != sum of the seven rule flags"


def test_is_rule_alert_thresholds(rule_flags_df: pd.DataFrame):
    """Assert is_rule_alert_1 == (alert_score >= 1) and is_rule_alert_2 == (alert_score >= 2)."""
    expected_alert_1 = (rule_flags_df["alert_score"] >= 1).astype(int)
    diffs_1 = (rule_flags_df["is_rule_alert_1"] != expected_alert_1).sum()
    assert diffs_1 == 0, f"Found {diffs_1:,} rows where is_rule_alert_1 != (alert_score >= 1)"

    expected_alert_2 = (rule_flags_df["alert_score"] >= 2).astype(int)
    diffs_2 = (rule_flags_df["is_rule_alert_2"] != expected_alert_2).sum()
    assert diffs_2 == 0, f"Found {diffs_2:,} rows where is_rule_alert_2 != (alert_score >= 2)"


def test_no_is_flagged_fraud_in_rule_flags(rule_flags_df: pd.DataFrame):
    """Assert no column in rule_flags is named isFlaggedFraud (strictly excluding target leakage)."""
    assert "isFlaggedFraud" not in rule_flags_df.columns, (
        "Forbidden reference column 'isFlaggedFraud' found in rule_flags"
    )


def test_rule_evaluation_reports_exist():
    """Assert reports/08_rule_evaluation.csv and reports/08_rule_evaluation.md exist."""
    assert config.RULE_EVAL_CSV.exists(), "08_rule_evaluation.csv does not exist"
    assert config.RULE_EVAL_MD.exists(), "08_rule_evaluation.md does not exist"

    df_eval = pd.read_csv(config.RULE_EVAL_CSV)
    assert len(df_eval) == 18, f"Expected 18 rows in evaluation CSV, found {len(df_eval)}"
    assert set(df_eval["universe"].unique()) == {"SCOPED", "FULL"}
