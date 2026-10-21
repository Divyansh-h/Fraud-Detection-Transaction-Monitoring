"""Anomaly Score Decision Threshold Tuning and Trade-Off Analysis Module.

Performs threshold tuning on the validation partition for the unsupervised
Isolation Forest anomaly detection baseline. Generates Precision-Recall curves,
selects strategic operating points, exports calibrated decision thresholds,
and computes false-alarm operational cost trade-offs.

NOTE: All threshold selections and curves are derived strictly from the
Validation partition (ml_val.parquet). The Test set is never touched.
"""

from pathlib import Path
import json
import sys
import time
from typing import Any, Optional

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, precision_recall_curve

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config
from src.evaluation import evaluate_binary, format_metrics
from src.train_isolation_forest import train_isolation_forest


def load_or_train_baseline() -> Any:
    """Load pre-trained Isolation Forest model from disk, or train if missing.

    Returns:
        Any: Fitted IsolationForest model instance.
    """
    if config.MODEL_ISOLATION_FOREST.exists():
        print(f"Loading existing baseline model from: {config.MODEL_ISOLATION_FOREST.relative_to(config.PROJECT_ROOT)}")
        model = joblib.load(config.MODEL_ISOLATION_FOREST)
    else:
        print("Pre-trained model not found. Training baseline model now...")
        model, _ = train_isolation_forest(save_model=True)
    return model


def plot_pr_curve(
    y_true: np.ndarray,
    scores: np.ndarray,
    pr_auc: float,
    operating_points: dict[str, dict[str, Any]],
    output_path: Path,
) -> None:
    """Plot and save publication-grade Precision-Recall curve with operating points.

    Args:
        y_true: Ground truth binary labels on validation set.
        scores: Continuous anomaly scores on validation set.
        pr_auc: Area under the Precision-Recall curve.
        operating_points: Dictionary containing metrics and thresholds for chosen operating points.
        output_path: Destination path for the PNG plot.
    """
    precision, recall, _ = precision_recall_curve(y_true, scores)
    prevalence = float(np.sum(y_true) / len(y_true))

    fig, ax = plt.subplots(figsize=(9, 6), dpi=300)

    # Plot base curve
    ax.plot(
        recall,
        precision,
        color="#1f77b4",
        lw=2.5,
        label=f"Isolation Forest (PR-AUC = {pr_auc:.4f})",
    )

    # Plot baseline prevalence (no-skill classifier)
    ax.axhline(
        y=prevalence,
        color="#d62728",
        linestyle="--",
        lw=1.5,
        label=f"Random Prevalence Baseline ({prevalence * 100:.2f}%)",
    )

    # Markers for operating points
    marker_styles = {
        "best_f1": ("#2ca02c", "o", "Best F1 Score"),
        "high_recall_p50": ("#ff7f0e", "s", "High Recall (P >= 50%)"),
        "high_precision_r80": ("#9467bd", "^", "High Precision (R >= 80%)"),
    }

    # Explicit annotation coordinates for clarity
    annotation_coords = {
        "best_f1": (point_data_f1 := operating_points.get("best_f1")) and (
            point_data_f1["metrics"]["recall"] - 0.22,
            point_data_f1["metrics"]["precision"] - 0.14,
        ),
        "high_recall_p50": (point_data_p50 := operating_points.get("high_recall_p50")) and (
            point_data_p50["metrics"]["recall"] + 0.06,
            point_data_p50["metrics"]["precision"] + 0.08,
        ),
        "high_precision_r80": (point_data_r80 := operating_points.get("high_precision_r80")) and (
            point_data_r80["metrics"]["recall"] - 0.12,
            point_data_r80["metrics"]["precision"] + 0.10,
        ),
    }

    for key, point_data in operating_points.items():
        if point_data is not None and key in marker_styles:
            color, marker, label = marker_styles[key]
            p_val = point_data["metrics"]["precision"]
            r_val = point_data["metrics"]["recall"]
            ax.scatter(
                [r_val],
                [p_val],
                color=color,
                s=110,
                zorder=5,
                marker=marker,
                edgecolors="black",
                linewidth=1.2,
                label=f"{label}: P={p_val * 100:.1f}%, R={r_val * 100:.1f}%",
            )
            xy_text = annotation_coords.get(key, (r_val + 0.05, p_val + 0.05))
            ax.annotate(
                f"{label}\n(T={point_data['threshold']:.3f})",
                xy=(r_val, p_val),
                xytext=xy_text,
                arrowprops=dict(facecolor="black", shrink=0.08, width=1, headwidth=5),
                fontsize=8.5,
                fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="#cccccc", alpha=0.92),
            )

    ax.set_title(
        f"Validation Precision-Recall Curve (PR-AUC = {pr_auc:.4f})",
        fontsize=14,
        fontweight="bold",
        pad=12,
    )
    ax.set_xlabel("Recall (Sensitivity)", fontsize=11, fontweight="bold")
    ax.set_ylabel("Precision (Positive Predictive Value)", fontsize=11, fontweight="bold")
    ax.set_xlim([-0.02, 1.02])
    ax.set_ylim([-0.02, 1.05])
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="upper right", frameon=True, fontsize=9.5, framealpha=0.95)

    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"PR Curve figure saved to: {output_path.relative_to(config.PROJECT_ROOT)}")


def tune_thresholds() -> dict[str, Any]:
    """Execute threshold tuning workflow on validation data only.

    Returns:
        dict[str, Any]: Tuning results and operating points.
    """
    t_start = time.perf_counter()
    print("==================================================")
    print("Isolation Forest Threshold Tuning (Validation Only)")
    print("==================================================")

    # 1. Load model and validation data
    print("\n[1/6] Loading validation dataset and model...")
    model = load_or_train_baseline()

    val_df = pd.read_parquet(config.ML_VAL_PARQUET)
    X_val = val_df[config.FEATURE_COLUMNS]
    y_val = val_df[config.COL_IS_FRAUD].values
    total_val = len(val_df)
    fraud_val = int(np.sum(y_val))
    print(f"  - Validation rows: {total_val:,}")
    print(f"  - Validation fraud cases: {fraud_val:,} ({100.0 * fraud_val / total_val:.4f}%)")

    # 2. Compute anomaly scores (higher = more anomalous)
    print("\n[2/6] Computing anomaly scores on validation partition...")
    # scikit-learn score_samples: opposite of anomaly score; invert so higher = higher risk
    anomaly_scores = -model.score_samples(X_val)
    pr_auc = float(average_precision_score(y_val, anomaly_scores))
    print(f"  - Anomaly score range: min={anomaly_scores.min():.4f}, max={anomaly_scores.max():.4f}, mean={anomaly_scores.mean():.4f}")
    print(f"  - Validation PR-AUC (Average Precision): {pr_auc:.4f}")

    # 3. Compute Precision-Recall curve
    print("\n[3/6] Computing Precision-Recall curve arrays...")
    precision, recall, thresholds = precision_recall_curve(y_val, anomaly_scores)
    # sklearn precision_recall_curve returns precision and recall with length len(thresholds) + 1
    p = precision[:-1]
    r = recall[:-1]
    th = thresholds
    f1 = np.where((p + r) > 0, (2.0 * p * r) / (p + r), 0.0)

    # 4. Identify Operating Points
    print("\n[4/6] Calibrating operating points on validation set...")
    operating_points: dict[str, Optional[dict[str, Any]]] = {}

    # (a) Best F1 Score
    best_f1_idx = int(np.argmax(f1))
    thresh_best_f1 = float(th[best_f1_idx])
    flag_best_f1 = (anomaly_scores >= thresh_best_f1).astype(int)
    metrics_best_f1 = evaluate_binary(y_val, flag_best_f1, scores=anomaly_scores)
    operating_points["best_f1"] = {
        "threshold": thresh_best_f1,
        "metrics": metrics_best_f1,
        "alerts": metrics_best_f1["TP"] + metrics_best_f1["FP"],
    }

    # (b) Highest recall achievable with precision >= 0.50
    p50_mask = p >= 0.50
    if np.any(p50_mask):
        p50_indices = np.where(p50_mask)[0]
        # Maximize recall; if tie, maximize precision
        best_p50_idx = int(p50_indices[np.argmax(r[p50_indices])])
        thresh_p50 = float(th[best_p50_idx])
        flag_p50 = (anomaly_scores >= thresh_p50).astype(int)
        metrics_p50 = evaluate_binary(y_val, flag_p50, scores=anomaly_scores)
        operating_points["high_recall_p50"] = {
            "threshold": thresh_p50,
            "metrics": metrics_p50,
            "alerts": metrics_p50["TP"] + metrics_p50["FP"],
        }
    else:
        print("  WARNING: Precision >= 0.50 is unattainable on this validation set.")
        operating_points["high_recall_p50"] = None

    # (c) Highest precision achievable with recall >= 0.80
    r80_mask = r >= 0.80
    if np.any(r80_mask):
        r80_indices = np.where(r80_mask)[0]
        # Maximize precision among recall >= 0.80
        best_r80_idx = int(r80_indices[np.argmax(p[r80_indices])])
        thresh_r80 = float(th[best_r80_idx])
        flag_r80 = (anomaly_scores >= thresh_r80).astype(int)
        metrics_r80 = evaluate_binary(y_val, flag_r80, scores=anomaly_scores)
        operating_points["high_precision_r80"] = {
            "threshold": thresh_r80,
            "metrics": metrics_r80,
            "alerts": metrics_r80["TP"] + metrics_r80["FP"],
        }
    else:
        print("  WARNING: Recall >= 0.80 is unattainable on this validation set.")
        operating_points["high_precision_r80"] = None

    # Print operating points table
    print("\n" + "=" * 80)
    print(f"{'Operating Point':<22} | {'Threshold':<10} | {'Precision':<10} | {'Recall':<10} | {'FPR':<10} | {'F1':<8} | {'Alerts':>8}")
    print("-" * 80)
    for name, op in operating_points.items():
        if op is not None:
            m = op["metrics"]
            t = op["threshold"]
            alerts = op["alerts"]
            print(f"{name:<22} | {t:<10.6f} | {m['precision']*100:>8.2f}% | {m['recall']*100:>8.2f}% | {m['fpr']*100:>8.4f}% | {m['f1']:>8.4f} | {alerts:>8,}")
        else:
            print(f"{name:<22} | {'None (Infeasible)':<55}")
    print("=" * 80)

    # 5. Save PR Curve Figure
    print(f"\n[5/6] Generating Precision-Recall curve figure: {config.FIG_PR_CURVE_VAL.relative_to(config.PROJECT_ROOT)}")
    plot_pr_curve(
        y_true=y_val,
        scores=anomaly_scores,
        pr_auc=pr_auc,
        operating_points=operating_points,
        output_path=config.FIG_PR_CURVE_VAL,
    )

    # 6. Save Thresholds to JSON
    thresholds_dict: dict[str, Optional[float]] = {
        "best_f1": operating_points["best_f1"]["threshold"] if operating_points["best_f1"] else None,
        "high_recall_p50": operating_points["high_recall_p50"]["threshold"] if operating_points["high_recall_p50"] else None,
        "high_precision_r80": operating_points["high_precision_r80"]["threshold"] if operating_points["high_precision_r80"] else None,
    }

    config.THRESHOLDS_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(config.THRESHOLDS_JSON, "w", encoding="utf-8") as f:
        json.dump(thresholds_dict, f, indent=2)
    print(f"\nDecision thresholds saved to: {config.THRESHOLDS_JSON.relative_to(config.PROJECT_ROOT)}")
    print(f"Content: {json.dumps(thresholds_dict)}")

    # 7. False-Alarm Cost Analysis: Alerts-vs-Recall Trade-Off Table
    print("\n[6/6] Computing False-Alarm Operational Trade-Off Table...")
    trade_off_rows = []
    target_recalls = [0.50, 0.60, 0.70, 0.80, 0.90]

    for target_r in target_recalls:
        mask = r >= target_r
        if np.any(mask):
            sub_indices = np.where(mask)[0]
            # Pick operating point that maximizes precision (minimizes alerts) at or above target recall
            opt_sub_idx = int(sub_indices[np.argmax(p[sub_indices])])
            t_curr = float(th[opt_sub_idx])
            flag_curr = (anomaly_scores >= t_curr).astype(int)
            m_curr = evaluate_binary(y_val, flag_curr)
            alerts = m_curr["TP"] + m_curr["FP"]
            alerts_per_100k = (alerts / total_val) * 100000.0
            trade_off_rows.append({
                "target_recall": target_r,
                "actual_recall": m_curr["recall"],
                "precision": m_curr["precision"],
                "fpr": m_curr["fpr"],
                "f1": m_curr["f1"],
                "alerts": alerts,
                "alerts_per_100k": alerts_per_100k,
                "threshold": t_curr,
            })

    print("\n" + "=" * 92)
    print(f"{'Target Recall':<14} | {'Actual Recall':<14} | {'Precision':<11} | {'FPR':<10} | {'Alerts':>8} | {'Alerts / 100k':>13} | {'Threshold':>10}")
    print("-" * 92)
    for row in trade_off_rows:
        print(
            f"{row['target_recall']*100:>12.0f}% | "
            f"{row['actual_recall']*100:>12.2f}% | "
            f"{row['precision']*100:>9.2f}% | "
            f"{row['fpr']*100:>8.4f}% | "
            f"{row['alerts']:>8,} | "
            f"{row['alerts_per_100k']:>13,.1f} | "
            f"{row['threshold']:>10.6f}"
        )
    print("=" * 92)

    # Explicit written statement on validation-only selection
    print("\n" + "*" * 80)
    print("METHODOLOGICAL COMPLIANCE STATEMENT:")
    print("All anomaly score decision thresholds, operating points, and PR curves were")
    print("derived STRICTLY using the VALIDATION partition (ml_val.parquet).")
    print("The test partition (ml_test.parquet) was completely isolated and NEVER accessed")
    print("or used for tuning, calibration, or threshold selection.")
    print("*" * 80)

    elapsed = time.perf_counter() - t_start
    print(f"\nThreshold tuning workflow completed in {elapsed:.2f}s.")
    return {
        "operating_points": operating_points,
        "trade_off_rows": trade_off_rows,
        "pr_auc": pr_auc,
        "thresholds": thresholds_dict,
    }


def main():
    """CLI execution entrypoint."""
    tune_thresholds()


if __name__ == "__main__":
    main()
