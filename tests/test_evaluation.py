"""Unit tests for binary evaluation metrics module."""

import json
import pytest
import numpy as np

from src.evaluation import evaluate_binary, format_metrics


def test_evaluate_binary_example_from_spec():
    """Test standard hand-crafted toy dataset specified in user prompt."""
    y_true = [1, 0, 0, 1, 0]
    y_flag = [1, 0, 1, 0, 0]

    metrics = evaluate_binary(y_true, y_flag)

    assert metrics["TP"] == 1
    assert metrics["FP"] == 1
    assert metrics["FN"] == 1
    assert metrics["TN"] == 2
    assert pytest.approx(metrics["precision"], 1e-6) == 0.5
    assert pytest.approx(metrics["recall"], 1e-6) == 0.5
    assert pytest.approx(metrics["fpr"], 1e-6) == 1.0 / 3.0
    assert pytest.approx(metrics["f1"], 1e-6) == 0.5
    assert pytest.approx(metrics["accuracy"], 1e-6) == 0.6


def test_evaluate_binary_json_serializable():
    """Assert all returned metrics are pure Python ints and floats, and JSON-serializable."""
    y_true = [1, 0, 1, 0]
    y_flag = [1, 0, 0, 1]
    scores = [0.9, 0.2, 0.4, 0.8]

    metrics = evaluate_binary(y_true, y_flag, scores=scores)

    # Check native types
    for key in ["TP", "FP", "FN", "TN"]:
        assert type(metrics[key]) is int, f"Key {key} is {type(metrics[key])}, expected int"

    for key in ["precision", "recall", "fpr", "f1", "accuracy", "pr_auc", "roc_auc"]:
        assert type(metrics[key]) is float, f"Key {key} is {type(metrics[key])}, expected float"

    # Must serialize to valid JSON without error
    serialized = json.dumps(metrics)
    deserialized = json.loads(serialized)
    assert deserialized["TP"] == metrics["TP"]


def test_evaluate_binary_zero_flagged_denominator():
    """Test safe division when no records are flagged (TP + FP = 0)."""
    y_true = [1, 0, 1, 0]
    y_flag = [0, 0, 0, 0]

    metrics = evaluate_binary(y_true, y_flag)

    assert metrics["TP"] == 0
    assert metrics["FP"] == 0
    assert metrics["FN"] == 2
    assert metrics["TN"] == 2
    assert metrics["precision"] == 0.0
    assert metrics["recall"] == 0.0
    assert metrics["fpr"] == 0.0
    assert metrics["f1"] == 0.0
    assert metrics["accuracy"] == 0.5


def test_evaluate_binary_zero_true_positive_denominator():
    """Test safe division when no ground truth positives exist (TP + FN = 0)."""
    y_true = [0, 0, 0, 0]
    y_flag = [1, 0, 1, 0]

    metrics = evaluate_binary(y_true, y_flag)

    assert metrics["TP"] == 0
    assert metrics["FP"] == 2
    assert metrics["FN"] == 0
    assert metrics["TN"] == 2
    assert metrics["precision"] == 0.0
    assert metrics["recall"] == 0.0
    assert metrics["fpr"] == 0.5
    assert metrics["f1"] == 0.0
    assert metrics["accuracy"] == 0.5


def test_evaluate_binary_zero_true_negative_denominator():
    """Test safe division when no ground truth negatives exist (FP + TN = 0)."""
    y_true = [1, 1, 1, 1]
    y_flag = [1, 1, 0, 0]

    metrics = evaluate_binary(y_true, y_flag)

    assert metrics["TP"] == 2
    assert metrics["FP"] == 0
    assert metrics["FN"] == 2
    assert metrics["TN"] == 0
    assert metrics["precision"] == 1.0
    assert metrics["recall"] == 0.5
    assert metrics["fpr"] == 0.0
    assert pytest.approx(metrics["f1"], 1e-6) == 2.0 / 3.0
    assert metrics["accuracy"] == 0.5


def test_evaluate_binary_with_scores_auc():
    """Test PR-AUC and ROC-AUC calculations when continuous scores are provided."""
    y_true = [1, 0, 0, 1, 0]
    y_flag = [1, 0, 1, 0, 0]
    scores = [0.9, 0.1, 0.8, 0.4, 0.2]

    metrics = evaluate_binary(y_true, y_flag, scores=scores)

    assert "pr_auc" in metrics
    assert "roc_auc" in metrics
    assert 0.0 <= metrics["pr_auc"] <= 1.0
    assert 0.0 <= metrics["roc_auc"] <= 1.0
    assert pytest.approx(metrics["pr_auc"], 1e-4) == 0.8333
    assert pytest.approx(metrics["roc_auc"], 1e-4) == 0.8333


def test_evaluate_binary_mismatched_lengths():
    """Assert ValueError is raised when input lengths differ."""
    with pytest.raises(ValueError, match="Length mismatch"):
        evaluate_binary([1, 0], [1])

    with pytest.raises(ValueError, match="Length mismatch"):
        evaluate_binary([1, 0], [1, 0], scores=[0.5])


def test_format_metrics_output():
    """Assert format_metrics produces tabular output with misleading accuracy notice."""
    metrics = {
        "TP": 10,
        "FP": 5,
        "FN": 2,
        "TN": 100,
        "precision": 0.6667,
        "recall": 0.8333,
        "fpr": 0.0476,
        "f1": 0.7407,
        "accuracy": 0.9402,
        "pr_auc": 0.7850,
        "roc_auc": 0.9200,
    }
    table_str = format_metrics(metrics, title="Test Baseline Performance")

    assert "Test Baseline Performance" in table_str
    assert "True Positives (TP)" in table_str
    assert "MISLEADING on imbalanced" in table_str
    assert "Precision" in table_str
    assert "Recall" in table_str
    assert "PR-AUC" in table_str
    assert "ROC-AUC" in table_str
