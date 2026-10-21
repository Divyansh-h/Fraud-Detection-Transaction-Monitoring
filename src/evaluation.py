"""Evaluation Module for Binary Fraud Classification and Anomaly Detection.

Provides robust, safe, and JSON-serializable binary metric evaluation functions
specifically tailored for extreme class-imbalanced transaction monitoring tasks.
"""

from typing import Any, Optional
import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score


def evaluate_binary(
    y_true: Any,
    y_flag: Any,
    scores: Optional[Any] = None,
) -> dict[str, Any]:
    """Compute comprehensive binary classification evaluation metrics.

    Calculates confusion matrix elements, precision, recall, FPR, F1, and accuracy.
    Optionally computes PR-AUC (Average Precision) and ROC-AUC when continuous
    scores are supplied.

    Note on Accuracy:
        Accuracy is included strictly for pedagogical/baseline reference. In highly
        imbalanced fraud detection (e.g. 0.30% fraud), a trivial model predicting
        all zeros achieves ~99.70% accuracy while failing to detect a single fraud event.
        Therefore, accuracy is misleading and should not be used as an optimization target.

    Args:
        y_true: Array-like of ground truth binary labels (0 or 1).
        y_flag: Array-like of predicted binary flags (0 or 1).
        scores: Optional array-like of continuous prediction scores or anomaly scores
            (higher values indicate higher likelihood of fraud / anomaly).

    Returns:
        dict[str, Any]: Dictionary containing native Python ints and floats:
            - 'TP': int
            - 'FP': int
            - 'FN': int
            - 'TN': int
            - 'precision': float
            - 'recall': float
            - 'fpr': float
            - 'f1': float
            - 'accuracy': float
            - 'pr_auc': float (if scores provided)
            - 'roc_auc': float (if scores provided)
    """
    y_t = np.asarray(y_true).astype(int).ravel()
    y_f = np.asarray(y_flag).astype(int).ravel()

    if len(y_t) != len(y_f):
        raise ValueError(
            f"Length mismatch: y_true has {len(y_t)} elements, y_flag has {len(y_f)} elements."
        )

    # Confusion matrix elements (strictly native Python ints)
    tp = int(np.sum((y_f == 1) & (y_t == 1)))
    fp = int(np.sum((y_f == 1) & (y_t == 0)))
    fn = int(np.sum((y_f == 0) & (y_t == 1)))
    tn = int(np.sum((y_f == 0) & (y_t == 0)))

    total = tp + fp + fn + tn

    # Safe divisions returning float 0.0 on zero denominators
    precision = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
    recall = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
    fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0

    if (precision + recall) > 0:
        f1 = float(2.0 * precision * recall / (precision + recall))
    else:
        f1 = 0.0

    accuracy = float((tp + tn) / total) if total > 0 else 0.0

    metrics: dict[str, Any] = {
        "TP": tp,
        "FP": fp,
        "FN": fn,
        "TN": tn,
        "precision": precision,
        "recall": recall,
        "fpr": fpr,
        "f1": f1,
        "accuracy": accuracy,
    }

    # Optional ranking metrics if continuous anomaly / risk scores are provided
    if scores is not None:
        s = np.asarray(scores).astype(float).ravel()
        if len(s) != len(y_t):
            raise ValueError(
                f"Length mismatch: scores has {len(s)} elements, y_true has {len(y_t)} elements."
            )

        # Check for single-class edge cases where AUC is undefined
        unique_classes = np.unique(y_t)
        if len(unique_classes) > 1:
            try:
                metrics["pr_auc"] = float(average_precision_score(y_t, s))
            except Exception:
                metrics["pr_auc"] = 0.0

            try:
                metrics["roc_auc"] = float(roc_auc_score(y_t, s))
            except Exception:
                metrics["roc_auc"] = 0.0
        else:
            metrics["pr_auc"] = 0.0
            metrics["roc_auc"] = 0.0

    return metrics


def format_metrics(metrics: dict[str, Any], title: Optional[str] = None) -> str:
    """Format an evaluation metrics dictionary into a readable tabular text display.

    Args:
        metrics: Dictionary returned by evaluate_binary().
        title: Optional title header for the table.

    Returns:
        str: Pretty-printed tabular text representation.
    """
    lines = []
    width = 54
    lines.append("=" * width)
    if title:
        lines.append(f"{title:^{width}}")
        lines.append("-" * width)

    # Confusion matrix
    lines.append(f"{'Metric':<36} | {'Value':>13}")
    lines.append("-" * width)
    lines.append(f"{'True Positives (TP)':<36} | {metrics['TP']:>13,}")
    lines.append(f"{'False Positives (FP)':<36} | {metrics['FP']:>13,}")
    lines.append(f"{'False Negatives (FN)':<36} | {metrics['FN']:>13,}")
    lines.append(f"{'True Negatives (TN)':<36} | {metrics['TN']:>13,}")
    lines.append("-" * width)

    # Primary detection rates
    prec_pct = metrics["precision"] * 100.0
    rec_pct = metrics["recall"] * 100.0
    fpr_pct = metrics["fpr"] * 100.0
    lines.append(f"{'Precision (TP / Flagged)':<36} | {metrics['precision']:>7.4f} ({prec_pct:>5.2f}%)")
    lines.append(f"{'Recall / Sensitivity (TP / Fraud)':<36} | {metrics['recall']:>7.4f} ({rec_pct:>5.2f}%)")
    lines.append(f"{'False Positive Rate (FPR)':<36} | {metrics['fpr']:>7.4f} ({fpr_pct:>5.2f}%)")
    lines.append(f"{'F1 Score':<36} | {metrics['f1']:>13.4f}")

    # Accuracy with explicit warning label
    acc_pct = metrics["accuracy"] * 100.0
    lines.append(f"{'Accuracy (MISLEADING on imbalanced)':<36} | {metrics['accuracy']:>7.4f} ({acc_pct:>5.2f}%)")

    # Optional ranking metrics
    if "pr_auc" in metrics:
        lines.append("-" * width)
        lines.append(f"{'PR-AUC (Average Precision)':<36} | {metrics['pr_auc']:>13.4f}")
    if "roc_auc" in metrics:
        lines.append(f"{'ROC-AUC':<36} | {metrics['roc_auc']:>13.4f}")

    lines.append("=" * width)
    return "\n".join(lines)
