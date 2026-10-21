"""Phase 3 Test Suite: ML Model Persistence, Metadata, and Scoring Reproducibility."""

import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

import config
from src.predict import score_dataframe


def test_saved_model_and_metadata_exist():
    """Assert saved model joblib exists and metadata JSON loads with required fields."""
    assert config.MODEL_FINAL_JOBLIB.exists(), f"Model file missing: {config.MODEL_FINAL_JOBLIB}"
    assert config.MODEL_FINAL_JOBLIB.stat().st_size > 100000, "Model file size unexpectedly small"

    assert config.MODEL_METADATA_JSON.exists(), f"Metadata JSON missing: {config.MODEL_METADATA_JSON}"

    with open(config.MODEL_METADATA_JSON, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    # Check required fields
    required_keys = [
        "sklearn_version",
        "training_date",
        "config_used",
        "feature_columns",
        "thresholds",
        "train_row_count",
        "random_seed",
    ]
    for key in required_keys:
        assert key in metadata, f"Missing key in model_metadata.json: {key}"

    assert metadata["feature_columns"] == config.FEATURE_COLUMNS, "Feature columns mismatch"
    assert metadata["train_row_count"] == 1662245, "Train row count mismatch in metadata"
    assert metadata["random_seed"] == config.RANDOM_SEED, "Random seed mismatch in metadata"


def test_ml_scores_parquet_has_no_nan():
    """Assert data/outputs/ml_scores.parquet exists, has expected rows, and contains zero NaNs."""
    assert config.ML_SCORES_PARQUET.exists(), f"Missing {config.ML_SCORES_PARQUET}"

    df = pd.read_parquet(config.ML_SCORES_PARQUET)
    assert len(df) == config.EXPECTED_SCOPED_ROWS, (
        f"Expected {config.EXPECTED_SCOPED_ROWS:,} rows, got {len(df):,}"
    )

    # Assert zero NaNs across all columns
    nan_count = int(df.isna().sum().sum())
    assert nan_count == 0, f"Detected {nan_count:,} NaN values in ml_scores.parquet!"

    # Assert column definitions
    expected_cols = ["txn_id", "anomaly_score", "anomaly_score_pct", "ml_flag", "split"]
    assert list(df.columns) == expected_cols, f"Column mismatch: {list(df.columns)}"

    # Assert uniqueness
    assert df["txn_id"].nunique() == len(df), "Duplicate txn_id detected in ml_scores.parquet"


def test_score_dataframe_reproducibility():
    """Sample 5,000 random scoped rows, score with predict.score_dataframe, and assert exact match."""
    # 1. Load clean data and filter to scoped transactions
    df_clean = pd.read_parquet(config.CLEAN_PARQUET)
    scoped_df = df_clean[df_clean["type"].isin(config.FRAUD_TYPES)].copy()

    # 2. Sample 5,000 random scoped rows with fixed seed
    sample_df = scoped_df.sample(n=5000, random_state=config.RANDOM_SEED)

    # 3. Score with predict.score_dataframe
    res = score_dataframe(sample_df)
    scores, flags = res

    # 4. Load ground truth scores from ml_scores.parquet
    df_ml_scores = pd.read_parquet(config.ML_SCORES_PARQUET).set_index(config.COL_TXN_ID)
    saved_sub = df_ml_scores.loc[sample_df[config.COL_TXN_ID].values]

    expected_scores = saved_sub["anomaly_score"].values
    expected_flags = saved_sub["ml_flag"].values

    # 5. Assert numeric equality within 1e-9 tolerance
    max_diff = float(np.max(np.abs(scores - expected_scores)))
    assert np.allclose(scores, expected_scores, atol=1e-9), (
        f"Score reproducibility failed! Max difference = {max_diff}"
    )

    # 6. Assert binary flag equality
    assert np.array_equal(flags, expected_flags), "ml_flag reproducibility failed!"
