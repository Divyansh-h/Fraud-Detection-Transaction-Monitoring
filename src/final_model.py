"""Final Model Training, Test Evaluation, and Production Anomaly Scoring.

Loads optimal hyperparameter configurations and calibrated operating thresholds,
trains the final Isolation Forest model on the FULL training partition,
evaluates generalization performance ONCE on the isolated Test partition,
and scores all 2.77M scoped transactions for Phase 4 hybrid ensemble integration.

NOTE: The test partition (ml_test.parquet) is accessed strictly ONCE here
for final out-of-sample evaluation. It was never used for tuning or calibration.
"""

from pathlib import Path
import json
import sys
import time
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config
from src.evaluation import evaluate_binary, format_metrics


def train_final_model(
    best_config: dict[str, Any],
    save_artifact: bool = True,
) -> tuple[IsolationForest, float]:
    """Train the final Isolation Forest model on the FULL training partition.

    Args:
        best_config: Dictionary containing optimal hyperparameters from grid sweep.
        save_artifact: Whether to serialize the fitted model to disk.

    Returns:
        tuple[IsolationForest, float]: Fitted model instance and elapsed training time in seconds.
    """
    print(f"\n[1/5] Training final Isolation Forest on FULL training partition...")
    df_train = pd.read_parquet(config.ML_TRAIN_PARQUET)
    X_train = df_train[config.FEATURE_COLUMNS]

    n_samples = len(X_train)
    print(f"  - Full training dataset size: {n_samples:,} rows (NO subsampling applied)")
    print(f"  - Hyperparameters: n_estimators={best_config['n_estimators']}, "
          f"max_samples={best_config['max_samples']}, contamination={best_config['contamination']}")
    print(f"  - Feature set: {best_config['feature_set']} ({len(config.FEATURE_COLUMNS)} features)")

    t0 = time.perf_counter()
    model = IsolationForest(
        n_estimators=best_config["n_estimators"],
        max_samples=best_config["max_samples"],
        contamination=best_config["contamination"],
        random_state=config.RANDOM_SEED,
        n_jobs=-1,
    )
    model.fit(X_train)
    train_time = time.perf_counter() - t0
    print(f"  - Full training completed in {train_time:.2f}s.")

    if save_artifact:
        import sklearn
        from datetime import datetime, timezone

        config.MODELS_DIR.mkdir(parents=True, exist_ok=True)

        # 1. Save model binary to canonical path
        joblib.dump(model, config.MODEL_FINAL_JOBLIB)
        joblib.dump(model, config.MODEL_ISOLATION_FOREST_FINAL)
        model_size_mb = config.MODEL_FINAL_JOBLIB.stat().st_size / (1024 * 1024)
        print(f"  - Serialized final model to: {config.MODEL_FINAL_JOBLIB.relative_to(config.PROJECT_ROOT)} ({model_size_mb:.2f} MB)")

    return model, train_time


def save_model_metadata(
    best_config: dict[str, Any],
    thresholds: dict[str, Any],
    train_row_count: int,
) -> None:
    """Save models/model_metadata.json documenting training lineage and features."""
    import sklearn
    from datetime import datetime, timezone

    config.MODELS_DIR.mkdir(parents=True, exist_ok=True)

    metadata = {
        "sklearn_version": str(sklearn.__version__),
        "training_date": datetime.now(timezone.utc).isoformat(),
        "config_used": best_config,
        "feature_columns": list(config.FEATURE_COLUMNS),
        "FEATURE_COLUMNS": list(config.FEATURE_COLUMNS),
        "thresholds": thresholds,
        "train_row_count": int(train_row_count),
        "random_seed": int(config.RANDOM_SEED),
    }

    with open(config.MODEL_METADATA_JSON, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"  - Serialized model metadata to: {config.MODEL_METADATA_JSON.relative_to(config.PROJECT_ROOT)}")


def evaluate_on_test_set(
    model: IsolationForest,
    thresholds: dict[str, float],
) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    """Evaluate generalization performance once on the held-out test partition.

    Args:
        model: Fitted final Isolation Forest model.
        thresholds: Calibrated operating-point thresholds dictionary.

    Returns:
        tuple[pd.DataFrame, np.ndarray, np.ndarray]: Evaluation metrics DataFrame, test anomaly scores, and test txn_ids.
    """
    print(f"\n[2/5] Evaluating once on isolated TEST partition...")
    print(f"  - Loading test dataset: {config.ML_TEST_PARQUET.relative_to(config.PROJECT_ROOT)}")
    df_test = pd.read_parquet(config.ML_TEST_PARQUET)
    X_test = df_test[config.FEATURE_COLUMNS]
    y_test = df_test[config.COL_IS_FRAUD].values
    test_txn_ids = df_test[config.COL_TXN_ID].values

    n_test = len(df_test)
    n_fraud = int(y_test.sum())
    print(f"  - Test transactions: {n_test:,} rows")
    print(f"  - Test ground-truth fraud events: {n_fraud:,} ({100.0 * n_fraud / n_test:.4f}%)")

    # Compute continuous anomaly scores on test set
    t0_score = time.perf_counter()
    test_scores = -model.score_samples(X_test)
    score_time = time.perf_counter() - t0_score
    print(f"  - Computed anomaly scores in {score_time:.2f}s.")

    # Define test evaluation operating configurations
    eval_configs = [
        ("default_contamination", "model_default", (model.predict(X_test) == -1).astype(int)),
    ]

    for thresh_name in ["best_f1", "high_recall_p50", "high_precision_r80"]:
        t_val = thresholds.get(thresh_name)
        if t_val is not None:
            flag = (test_scores >= t_val).astype(int)
            eval_configs.append((thresh_name, t_val, flag))

    test_results = []
    print("\n" + "=" * 105)
    print(f"{'Test Partition Out-of-Sample Evaluation Results':^105}")
    print("=" * 105)
    print(f"{'Operating Condition':<22} | {'Threshold':<10} | {'TP':>6} | {'FP':>6} | {'Precision':>9} | {'Recall':>9} | {'FPR':>9} | {'F1':>8} | {'Alerts':>8}")
    print("-" * 105)

    for name, t_spec, flag_pred in eval_configs:
        m = evaluate_binary(y_true=y_test, y_flag=flag_pred, scores=test_scores)
        alerts = m["TP"] + m["FP"]
        t_display = f"{t_spec:.6f}" if isinstance(t_spec, (float, int)) else str(t_spec)

        row = {
            "condition": name,
            "threshold": t_display,
            "TP": m["TP"],
            "FP": m["FP"],
            "FN": m["FN"],
            "TN": m["TN"],
            "precision": float(m["precision"]),
            "recall": float(m["recall"]),
            "fpr": float(m["fpr"]),
            "f1": float(m["f1"]),
            "accuracy": float(m["accuracy"]),
            "pr_auc": float(m["pr_auc"]),
            "roc_auc": float(m["roc_auc"]),
            "alerts": int(alerts),
        }
        test_results.append(row)

        print(
            f"{name:<22} | {t_display:<10} | {m['TP']:>6,} | {m['FP']:>6,} | "
            f"{m['precision']*100:>8.2f}% | {m['recall']*100:>8.2f}% | "
            f"{m['fpr']*100:>8.4f}% | {m['f1']:>8.4f} | {alerts:>8,}"
        )

    print("=" * 105)
    print(f"Out-of-Sample Ranking Summary: PR-AUC = {test_results[0]['pr_auc']:.4f} | ROC-AUC = {test_results[0]['roc_auc']:.4f}")

    df_test_metrics = pd.DataFrame(test_results)
    config.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    df_test_metrics.to_csv(config.ML_TEST_RESULTS_CSV, index=False)
    print(f"\nSaved test metrics report to: {config.ML_TEST_RESULTS_CSV.relative_to(config.PROJECT_ROOT)}")

    return df_test_metrics, test_scores, test_txn_ids


def score_all_scoped_partitions(
    model: IsolationForest,
    best_f1_threshold: float,
    test_scores: np.ndarray,
    test_txn_ids: np.ndarray,
) -> pd.DataFrame:
    """Score all scoped transactions across Train, Validation, and Test partitions.

    Normalises anomaly scores to a 0-100 percentile scale using Train min/max bounds,
    generates production ml_flag based on best_f1 threshold, and exports Parquet.

    Args:
        model: Fitted final Isolation Forest model.
        best_f1_threshold: Score threshold corresponding to optimal F1 operating point.
        test_scores: Pre-computed test anomaly scores.
        test_txn_ids: Test transaction IDs.

    Returns:
        pd.DataFrame: Complete scored DataFrame for all scoped transactions.
    """
    print(f"\n[3/5] Scoring all scoped transactions across Train, Val, and Test...")

    # 1. Score Train partition
    t0_train = time.perf_counter()
    df_train = pd.read_parquet(config.ML_TRAIN_PARQUET)
    train_scores = -model.score_samples(df_train[config.FEATURE_COLUMNS])
    train_txn_ids = df_train[config.COL_TXN_ID].values
    train_duration = time.perf_counter() - t0_train
    print(f"  - Scored Train partition ({len(df_train):,} rows) in {train_duration:.2f}s.")

    # 2. Score Validation partition
    t0_val = time.perf_counter()
    df_val = pd.read_parquet(config.ML_VAL_PARQUET)
    val_scores = -model.score_samples(df_val[config.FEATURE_COLUMNS])
    val_txn_ids = df_val[config.COL_TXN_ID].values
    val_duration = time.perf_counter() - t0_val
    print(f"  - Scored Validation partition ({len(df_val):,} rows) in {val_duration:.2f}s.")

    # 3. Compute normalisation bounds strictly on TRAIN scores
    print(f"\n[4/5] Normalising anomaly scores to 0-100 scale using Train bounds...")
    train_min = float(train_scores.min())
    train_max = float(train_scores.max())
    score_range = train_max - train_min
    print(f"  - Training score bounds: min = {train_min:.6f}, max = {train_max:.6f}, range = {score_range:.6f}")

    def normalize_scores(raw_scores: np.ndarray) -> np.ndarray:
        pct = ((raw_scores - train_min) / score_range) * 100.0
        return np.clip(pct, 0.0, 100.0)

    train_pct = normalize_scores(train_scores)
    val_pct = normalize_scores(val_scores)
    test_pct = normalize_scores(test_scores)

    # 4. Assemble consolidated scored partitions
    print(f"\n[5/5] Assembling consolidated ml_scores table and exporting Parquet...")
    train_part = pd.DataFrame({
        config.COL_TXN_ID: train_txn_ids,
        "anomaly_score": train_scores,
        "anomaly_score_pct": train_pct,
        "ml_flag": (train_scores >= best_f1_threshold).astype(np.int8),
        "split": "train",
    })

    val_part = pd.DataFrame({
        config.COL_TXN_ID: val_txn_ids,
        "anomaly_score": val_scores,
        "anomaly_score_pct": val_pct,
        "ml_flag": (val_scores >= best_f1_threshold).astype(np.int8),
        "split": "val",
    })

    test_part = pd.DataFrame({
        config.COL_TXN_ID: test_txn_ids,
        "anomaly_score": test_scores,
        "anomaly_score_pct": test_pct,
        "ml_flag": (test_scores >= best_f1_threshold).astype(np.int8),
        "split": "test",
    })

    ml_scores = pd.concat([train_part, val_part, test_part], ignore_index=True)

    # Assert row count equals expected scoped row count
    total_scoped = len(ml_scores)
    assert total_scoped == config.EXPECTED_SCOPED_ROWS, (
        f"Scoped count mismatch: expected {config.EXPECTED_SCOPED_ROWS:,}, got {total_scoped:,}"
    )

    # Assert unique transaction IDs
    assert ml_scores[config.COL_TXN_ID].nunique() == total_scoped, (
        "Duplicate txn_id detected in ml_scores!"
    )

    # Export to Parquet
    config.OUTPUTS_DATA_DIR.mkdir(parents=True, exist_ok=True)
    ml_scores.to_parquet(config.ML_SCORES_PARQUET, compression="snappy", index=False)
    file_size_mb = config.ML_SCORES_PARQUET.stat().st_size / (1024 * 1024)
    print(f"  - Scored Parquet written to: {config.ML_SCORES_PARQUET.relative_to(config.PROJECT_ROOT)} ({file_size_mb:.2f} MB)")
    print(f"  - Total scoped rows: {total_scoped:,} (100.0% coverage of TRANSFER and CASH_OUT)")
    print(f"  - Alerted transactions (ml_flag=1): {int(ml_scores['ml_flag'].sum()):,} ({100.0 * ml_scores['ml_flag'].sum() / total_scoped:.4f}%)")

    return ml_scores


def main() -> None:
    """Execution orchestrator for final model training and scoring."""
    t_global = time.perf_counter()
    print("==================================================")
    print("Final Model Training & Production Scoring Pipeline")
    print("==================================================")

    # 1. Load best_config.json and thresholds.json
    print(f"\nLoading configuration and thresholds from disk...")
    with open(config.BEST_CONFIG_JSON, "r", encoding="utf-8") as f:
        best_cfg = json.load(f)
    print(f"  - Best Config: {best_cfg}")

    with open(config.THRESHOLDS_JSON, "r", encoding="utf-8") as f:
        thresholds = json.load(f)
    print(f"  - Thresholds: {thresholds}")

    best_f1_thresh = float(thresholds["best_f1"])

    # 2. Train on full train partition
    model, _ = train_final_model(best_config=best_cfg, save_artifact=True)
    df_train_len = len(pd.read_parquet(config.ML_TRAIN_PARQUET, columns=[config.COL_TXN_ID]))
    save_model_metadata(best_config=best_cfg, thresholds=thresholds, train_row_count=df_train_len)

    # 3. Evaluate ONCE on test partition
    _, test_scores, test_txn_ids = evaluate_on_test_set(model=model, thresholds=thresholds)

    # 4. Score all scoped rows and write data/outputs/ml_scores.parquet
    score_all_scoped_partitions(
        model=model,
        best_f1_threshold=best_f1_thresh,
        test_scores=test_scores,
        test_txn_ids=test_txn_ids,
    )

    # 5. Methodological compliance statement
    print("\n" + "*" * 85)
    print("METHODOLOGICAL COMPLIANCE & TEST ISOLATION STATEMENT:")
    print("The test partition (ml_test.parquet) was accessed and evaluated strictly ONCE")
    print("in this script for final generalization measurement.")
    print("It was NEVER used for model training, tuning, feature selection, or calibration.")
    print("*" * 85)

    elapsed = time.perf_counter() - t_global
    print(f"\nFinal model workflow completed successfully in {elapsed:.2f}s.")


if __name__ == "__main__":
    main()
