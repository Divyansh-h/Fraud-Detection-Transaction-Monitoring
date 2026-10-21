"""Unit tests for final model outputs and test evaluation artifacts."""

from pathlib import Path
import pytest
import pandas as pd

import config


def test_ml_scores_parquet_integrity():
    """Assert data/outputs/ml_scores.parquet adheres to schema and row counts."""
    assert config.ML_SCORES_PARQUET.exists(), f"Missing {config.ML_SCORES_PARQUET}"

    df = pd.read_parquet(config.ML_SCORES_PARQUET)
    assert len(df) == config.EXPECTED_SCOPED_ROWS, (
        f"Expected {config.EXPECTED_SCOPED_ROWS} rows, got {len(df)}"
    )

    expected_cols = ["txn_id", "anomaly_score", "anomaly_score_pct", "ml_flag", "split"]
    assert list(df.columns) == expected_cols, f"Unexpected columns: {list(df.columns)}"

    # Assert uniqueness and coverage
    assert df["txn_id"].nunique() == len(df), "txn_id not unique in ml_scores"
    assert set(df["split"].unique()) == {"train", "val", "test"}
    assert set(df["ml_flag"].unique()).issubset({0, 1})

    # Assert percentile bounds
    assert 0.0 <= df["anomaly_score_pct"].min()
    assert df["anomaly_score_pct"].max() <= 100.0


def test_ml_test_results_csv_exists_and_valid():
    """Assert reports/11_ml_test_results.csv contains all evaluation conditions."""
    assert config.ML_TEST_RESULTS_CSV.exists(), f"Missing {config.ML_TEST_RESULTS_CSV}"

    df = pd.read_csv(config.ML_TEST_RESULTS_CSV)
    assert len(df) == 4, f"Expected 4 evaluation rows, got {len(df)}"

    conditions = set(df["condition"].tolist())
    expected_conditions = {
        "default_contamination",
        "best_f1",
        "high_recall_p50",
        "high_precision_r80",
    }
    assert conditions == expected_conditions, f"Conditions mismatch: {conditions}"

    for col in ["precision", "recall", "fpr", "f1", "pr_auc", "roc_auc"]:
        assert 0.0 <= df[col].min() <= df[col].max() <= 1.0, f"Metric {col} out of [0, 1] range"
