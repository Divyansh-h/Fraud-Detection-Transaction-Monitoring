"""Isolation Forest Anomaly Detection Baseline Model.

Trains an unsupervised Isolation Forest model on training features (without labels),
evaluates anomaly scoring on the validation partition, and formats binary metrics
using src.evaluation.evaluate_binary and format_metrics.
"""

from pathlib import Path
import sys
import time
import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config
from src.evaluation import evaluate_binary, format_metrics


def train_isolation_forest(
    save_model: bool = True,
    contamination: float = 0.003,
    n_estimators: int = 100,
    random_state: int = config.RANDOM_SEED,
) -> tuple[IsolationForest, dict]:
    """Train unsupervised Isolation Forest on train features and evaluate on validation data.

    Args:
        save_model: Whether to serialize model artifact to models/isolation_forest_baseline.joblib.
        contamination: Expected proportion of outliers in the training data (default ~0.30% fraud rate).
        n_estimators: Number of isolation trees in the ensemble.
        random_state: Deterministic random seed for reproducibility.

    Returns:
        tuple[IsolationForest, dict]: Trained model instance and validation evaluation metrics dictionary.
    """
    print("==================================================")
    print("Training Isolation Forest Baseline Model")
    print("==================================================")

    # 1. Load train partition (features only, strictly unsupervised)
    t0 = time.perf_counter()
    print(f"\n[1/4] Loading training dataset: {config.ML_TRAIN_PARQUET.relative_to(config.PROJECT_ROOT)}")
    df_train = pd.read_parquet(config.ML_TRAIN_PARQUET)
    X_train = df_train[config.FEATURE_COLUMNS]
    print(f"  - Training samples: {len(X_train):,} rows")
    print(f"  - Feature count: {len(config.FEATURE_COLUMNS)} columns")
    print(f"  - Unsupervised constraint: Target 'isFraud' strictly omitted from model training.")

    # 2. Fit IsolationForest
    t_fit_start = time.perf_counter()
    print(f"\n[2/4] Fitting IsolationForest (n_estimators={n_estimators}, contamination={contamination})...")
    model = IsolationForest(
        n_estimators=n_estimators,
        max_samples="auto",
        contamination=contamination,
        random_state=random_state,
        n_jobs=-1,
    )
    model.fit(X_train)
    fit_duration = time.perf_counter() - t_fit_start
    print(f"  - Training completed in {fit_duration:.2f}s.")

    # 3. Load validation partition
    print(f"\n[3/4] Loading validation dataset: {config.ML_VAL_PARQUET.relative_to(config.PROJECT_ROOT)}")
    df_val = pd.read_parquet(config.ML_VAL_PARQUET)
    X_val = df_val[config.FEATURE_COLUMNS]
    y_val = df_val[config.COL_IS_FRAUD].values
    print(f"  - Validation samples: {len(X_val):,} rows")
    print(f"  - Validation fraud cases: {int(y_val.sum()):,} ({100.0 * y_val.sum() / len(y_val):.4f}%)")

    # 4. Predict and evaluate
    t_pred_start = time.perf_counter()
    print("\n[4/4] Generating predictions and evaluating validation performance...")
    # sklearn returns -1 for anomalies, 1 for inliers; map to binary: 1 = fraud/anomaly, 0 = normal
    y_pred_flag = (model.predict(X_val) == -1).astype(int)

    # score_samples returns negative anomaly scores; invert so higher value = higher fraud risk
    anomaly_scores = -model.score_samples(X_val)
    pred_duration = time.perf_counter() - t_pred_start

    # Compute binary evaluation metrics
    metrics = evaluate_binary(y_true=y_val, y_flag=y_pred_flag, scores=anomaly_scores)

    # Print formatted metrics table
    print("\n" + format_metrics(metrics, title="Isolation Forest Baseline - Validation Performance"))

    # Save model artifact if requested
    if save_model:
        config.MODELS_DIR.mkdir(parents=True, exist_ok=True)
        joblib.dump(model, config.MODEL_ISOLATION_FOREST)
        size_mb = config.MODEL_ISOLATION_FOREST.stat().st_size / (1024 * 1024)
        print(f"\nTrained model serialized to: {config.MODEL_ISOLATION_FOREST.relative_to(config.PROJECT_ROOT)} ({size_mb:.2f} MB)")

    total_time = time.perf_counter() - t0
    print(f"Workflow completed successfully in {total_time:.2f}s.")
    return model, metrics


def main():
    """CLI execution entrypoint."""
    train_isolation_forest()


if __name__ == "__main__":
    main()
