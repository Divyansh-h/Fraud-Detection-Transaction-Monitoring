"""Unit tests for Isolation Forest hyperparameter & feature sweep artifacts."""

import json
from pathlib import Path
import pytest
import pandas as pd

import config


def test_if_sweep_csv_exists_and_complete():
    """Assert reports/10_if_sweep.csv exists with exact required schema and 54 rows."""
    assert config.IF_SWEEP_CSV.exists(), f"Missing {config.IF_SWEEP_CSV}"

    df = pd.read_csv(config.IF_SWEEP_CSV)
    assert len(df) == 54, f"Expected 54 grid combinations, got {len(df)}"

    expected_cols = [
        "n_estimators",
        "max_samples",
        "contamination",
        "feature_set",
        "pr_auc",
        "roc_auc",
        "precision",
        "recall",
        "fpr",
        "f1",
        "train_seconds",
    ]
    assert list(df.columns) == expected_cols, f"Column mismatch: {list(df.columns)}"

    # Check valid values
    assert set(df["feature_set"].unique()) == {"A", "B"}
    assert set(df["n_estimators"].unique()) == {100, 200, 400}
    assert set(df["contamination"].unique()) == {0.001, 0.003, 0.01}
    assert 0.0 <= df["pr_auc"].min() <= df["pr_auc"].max() <= 1.0
    assert 0.0 <= df["roc_auc"].min() <= df["roc_auc"].max() <= 1.0


def test_best_config_json_exists_and_valid():
    """Assert models/best_config.json exists and adheres to schema."""
    assert config.BEST_CONFIG_JSON.exists(), f"Missing {config.BEST_CONFIG_JSON}"

    with open(config.BEST_CONFIG_JSON, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    required_keys = [
        "n_estimators",
        "max_samples",
        "contamination",
        "feature_set",
        "pr_auc",
        "roc_auc",
        "precision",
        "recall",
        "fpr",
        "f1",
        "train_seconds",
    ]
    for key in required_keys:
        assert key in cfg, f"Missing key {key} in best_config.json"

    assert cfg["feature_set"] == "A", "Expected winning feature set to be A"
    assert cfg["pr_auc"] > 0.70, f"Expected PR-AUC > 0.70, got {cfg['pr_auc']}"
