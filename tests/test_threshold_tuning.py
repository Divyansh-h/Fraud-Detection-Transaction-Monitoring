"""Unit tests for threshold tuning module and saved artifacts."""

import json
from pathlib import Path
import pytest
import numpy as np
import pandas as pd
import joblib

import config
from src.evaluation import evaluate_binary


def test_thresholds_json_exists_and_valid():
    """Assert models/thresholds.json exists and has expected schema."""
    assert config.THRESHOLDS_JSON.exists(), f"Missing {config.THRESHOLDS_JSON}"

    with open(config.THRESHOLDS_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "best_f1" in data
    assert "high_recall_p50" in data
    assert "high_precision_r80" in data

    for key in ["best_f1", "high_recall_p50", "high_precision_r80"]:
        val = data[key]
        assert val is None or isinstance(val, (float, int)), f"Key {key} has unexpected type: {type(val)}"


def test_pr_curve_figure_exists():
    """Assert reports/figures/pr_curve_val.png exists and has valid file size."""
    assert config.FIG_PR_CURVE_VAL.exists(), f"Missing {config.FIG_PR_CURVE_VAL}"
    assert config.FIG_PR_CURVE_VAL.stat().st_size > 10000, "Figure file size unexpectedly small"


def test_validation_operating_points_performance():
    """Assert operating points satisfy their calibration constraints on validation data."""
    with open(config.THRESHOLDS_JSON, "r", encoding="utf-8") as f:
        thresholds = json.load(f)

    model = joblib.load(config.MODEL_ISOLATION_FOREST)
    val_df = pd.read_parquet(config.ML_VAL_PARQUET)
    X_val = val_df[config.FEATURE_COLUMNS]
    y_val = val_df[config.COL_IS_FRAUD].values
    scores = -model.score_samples(X_val)

    # 1. Best F1
    t_f1 = thresholds["best_f1"]
    assert t_f1 is not None
    m_f1 = evaluate_binary(y_val, (scores >= t_f1).astype(int))
    assert m_f1["f1"] > 0.60, f"Expected F1 > 0.60, got {m_f1['f1']}"

    # 2. High recall with precision >= 0.50
    t_p50 = thresholds["high_recall_p50"]
    if t_p50 is not None:
        m_p50 = evaluate_binary(y_val, (scores >= t_p50).astype(int))
        assert m_p50["precision"] >= 0.499, f"Expected precision >= 0.50, got {m_p50['precision']}"
        assert m_p50["recall"] >= 0.50, f"Expected recall >= 0.50, got {m_p50['recall']}"

    # 3. High precision with recall >= 0.80
    t_r80 = thresholds["high_precision_r80"]
    if t_r80 is not None:
        m_r80 = evaluate_binary(y_val, (scores >= t_r80).astype(int))
        assert m_r80["recall"] >= 0.799, f"Expected recall >= 0.80, got {m_r80['recall']}"
