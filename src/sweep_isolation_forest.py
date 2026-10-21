"""Hyperparameter & Feature Set Grid Sweep for Isolation Forest.

Executes a controlled grid search over tree counts, subsample depths, contamination
rates, and feature sets (Set A vs Set B) on the training set, evaluating ranking
performance via validation PR-AUC and ROC-AUC, alongside operational decision metrics.

Saves results to reports/10_if_sweep.csv and serializes the optimal configuration
to models/best_config.json.

NOTE: All evaluations are strictly computed on the Validation set (ml_val.parquet).
The Test partition (ml_test.parquet) is held out and remains completely untouched.
"""

from pathlib import Path
import json
import sys
import time
from typing import Any, Union

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config
from src.evaluation import evaluate_binary


def get_feature_sets() -> dict[str, list[str]]:
    """Define Feature Set A (canonical 13 features) and Feature Set B (no hand-crafted rules).

    Returns:
        dict[str, list[str]]: Dictionary with keys 'A' and 'B'.
    """
    rule_features = ["origEmptied", "destBalanceUnchanged"]
    feat_a = list(config.FEATURE_COLUMNS)
    feat_b = [f for f in config.FEATURE_COLUMNS if f not in rule_features]
    return {"A": feat_a, "B": feat_b}


def run_if_sweep(
    sample_train_size: int = 500000,
    random_state: int = config.RANDOM_SEED,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Execute hyperparameter and feature set grid sweep on validation data.

    Args:
        sample_train_size: Number of training rows to subsample for tractable runtime.
        random_state: Deterministic random seed for subsampling and tree construction.

    Returns:
        tuple[pd.DataFrame, dict[str, Any]]: Sweep results DataFrame and best configuration dictionary.
    """
    t_start = time.perf_counter()
    print("==================================================")
    print("Isolation Forest Hyperparameter & Feature Set Sweep")
    print("==================================================")

    # 1. Load data
    print(f"\n[1/4] Loading partitioned datasets...")
    full_train_df = pd.read_parquet(config.ML_TRAIN_PARQUET)
    val_df = pd.read_parquet(config.ML_VAL_PARQUET)
    y_val = val_df[config.COL_IS_FRAUD].values

    total_train_rows = len(full_train_df)
    if sample_train_size and sample_train_size < total_train_rows:
        print(f"  - Subsampling training rows: {sample_train_size:,} out of {total_train_rows:,} (seed={random_state}) for fast grid execution.")
        train_df = full_train_df.sample(n=sample_train_size, random_state=random_state)
    else:
        print(f"  - Using full training partition: {total_train_rows:,} rows.")
        train_df = full_train_df

    print(f"  - Validation partition: {len(val_df):,} rows ({int(y_val.sum()):,} fraud events).")
    print("  - Test set status: Isolated vault (UNTOUCHED).")

    # 2. Define grid parameters
    n_estimators_list = [100, 200, 400]
    max_samples_list: list[Union[int, str]] = [256, 1024, "auto"]
    contaminations = [0.001, 0.003, 0.01]
    feature_sets = get_feature_sets()

    total_fits = len(n_estimators_list) * len(max_samples_list) * len(feature_sets)
    total_combinations = total_fits * len(contaminations)
    print(f"\n[2/4] Grid Architecture: {total_fits} model fits across {total_combinations} total parameter combinations.")
    print(f"  - n_estimators: {n_estimators_list}")
    print(f"  - max_samples: {max_samples_list}")
    print(f"  - contaminations: {contaminations}")
    print(f"  - feature sets: A ({len(feature_sets['A'])} features) vs B ({len(feature_sets['B'])} features, rule-free)")

    # 3. Execute sweep
    print(f"\n[3/4] Running grid sweep across combinations...")
    results = []
    fit_count = 0

    for fs_name, feats in feature_sets.items():
        X_train_sub = train_df[feats]
        X_val_sub = val_df[feats]

        for n_est in n_estimators_list:
            for ms in max_samples_list:
                fit_count += 1
                t0_fit = time.perf_counter()

                # Fit base IsolationForest (trees depend solely on n_est, max_samples, and features)
                clf = IsolationForest(
                    n_estimators=n_est,
                    max_samples=ms,
                    contamination=0.003,  # default placeholder; offset calibrated below
                    random_state=random_state,
                    n_jobs=-1,
                )
                clf.fit(X_train_sub)
                t_fit = time.perf_counter() - t0_fit

                # Compute anomaly score ranking on validation set (higher score = higher anomaly)
                val_scores = -clf.score_samples(X_val_sub)
                train_scores = -clf.score_samples(X_train_sub)

                # Compute rank-based metrics (constant across contamination levels)
                # Note: evaluate_binary calculates PR-AUC and ROC-AUC
                base_eval = evaluate_binary(y_true=y_val, y_flag=np.zeros_like(y_val), scores=val_scores)
                pr_auc = base_eval["pr_auc"]
                roc_auc = base_eval["roc_auc"]

                # Evaluate decision metrics across the three contamination levels
                for contam in contaminations:
                    # In scikit-learn, contamination c sets offset such that the top c proportion of train samples are flagged
                    score_threshold = float(np.percentile(train_scores, 100.0 * (1.0 - contam)))
                    val_pred_flag = (val_scores >= score_threshold).astype(int)

                    m = evaluate_binary(y_true=y_val, y_flag=val_pred_flag, scores=val_scores)

                    row = {
                        "n_estimators": int(n_est),
                        "max_samples": str(ms) if ms == "auto" else int(ms),
                        "contamination": float(contam),
                        "feature_set": fs_name,
                        "pr_auc": float(pr_auc),
                        "roc_auc": float(roc_auc),
                        "precision": float(m["precision"]),
                        "recall": float(m["recall"]),
                        "fpr": float(m["fpr"]),
                        "f1": float(m["f1"]),
                        "train_seconds": round(float(t_fit), 3),
                    }
                    results.append(row)

                print(
                    f"  [{fit_count:>2}/{total_fits}] Set {fs_name} | n={n_est:>3} | ms={str(ms):<5} | "
                    f"PR-AUC={pr_auc:.4f} | ROC-AUC={roc_auc:.4f} | Fit={t_fit:.2f}s"
                )

    df_results = pd.DataFrame(results)

    # 4. Save results to CSV
    config.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    df_results.to_csv(config.IF_SWEEP_CSV, index=False)
    print(f"\n[4/4] Sweep results saved to: {config.IF_SWEEP_CSV.relative_to(config.PROJECT_ROOT)} ({len(df_results)} rows)")

    # 5. Pick Best Configuration
    # Sort by PR-AUC descending, ties broken by shorter train_seconds ascending
    # For contamination ties with identical PR-AUC, pick the highest F1
    df_sorted = df_results.sort_values(
        by=["pr_auc", "f1", "train_seconds"],
        ascending=[False, False, True],
    ).reset_index(drop=True)

    best_row = df_sorted.iloc[0].to_dict()

    # Format best configuration for JSON export
    best_config = {
        "n_estimators": int(best_row["n_estimators"]),
        "max_samples": int(best_row["max_samples"]) if str(best_row["max_samples"]).isdigit() else str(best_row["max_samples"]),
        "contamination": float(best_row["contamination"]),
        "feature_set": str(best_row["feature_set"]),
        "pr_auc": round(float(best_row["pr_auc"]), 6),
        "roc_auc": round(float(best_row["roc_auc"]), 6),
        "precision": round(float(best_row["precision"]), 6),
        "recall": round(float(best_row["recall"]), 6),
        "fpr": round(float(best_row["fpr"]), 6),
        "f1": round(float(best_row["f1"]), 6),
        "train_seconds": float(best_row["train_seconds"]),
        "selection_metric": "validation_pr_auc",
        "tie_breaker": "higher_f1_then_shorter_train_seconds",
    }

    config.BEST_CONFIG_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(config.BEST_CONFIG_JSON, "w", encoding="utf-8") as f:
        json.dump(best_config, f, indent=2)
    print(f"Optimal configuration saved to: {config.BEST_CONFIG_JSON.relative_to(config.PROJECT_ROOT)}")

    # 6. Display Summary Comparison
    print("\n" + "=" * 95)
    print(f"{'Top 5 Configurations (Ranked by Validation PR-AUC)':^95}")
    print("=" * 95)
    print(f"{'Rank':<5} {'Set':<5} {'n_est':<7} {'max_samp':<10} {'contam':<8} {'PR-AUC':<10} {'ROC-AUC':<10} {'F1':<8} {'Train(s)':<8}")
    print("-" * 95)
    for i in range(min(5, len(df_sorted))):
        r = df_sorted.iloc[i]
        print(
            f"#{i+1:<4} {r['feature_set']:<5} {r['n_estimators']:<7} {str(r['max_samples']):<10} "
            f"{r['contamination']:<8.3f} {r['pr_auc']:<10.4f} {r['roc_auc']:<10.4f} {r['f1']:<8.4f} {r['train_seconds']:<8.2f}"
        )
    print("=" * 95)

    # Display comparison between Set A and Set B
    mean_a_pr = df_results[df_results["feature_set"] == "A"]["pr_auc"].mean()
    max_a_pr = df_results[df_results["feature_set"] == "A"]["pr_auc"].max()
    mean_b_pr = df_results[df_results["feature_set"] == "B"]["pr_auc"].mean()
    max_b_pr = df_results[df_results["feature_set"] == "B"]["pr_auc"].max()

    print("\nFeature Set Performance Comparison:")
    print(f"  - Feature Set A (All 13 features): Mean PR-AUC = {mean_a_pr:.4f}, Peak PR-AUC = {max_a_pr:.4f}")
    print(f"  - Feature Set B (11 features, no hand-crafted rules): Mean PR-AUC = {mean_b_pr:.4f}, Peak PR-AUC = {max_b_pr:.4f}")
    delta_pr = max_a_pr - max_b_pr
    print(f"  - Peak Improvement with Hand-Crafted Features: +{delta_pr:.4f} PR-AUC ({delta_pr/max_b_pr*100:+.2f}%)")

    total_time = time.perf_counter() - t_start
    print(f"\nSweep completed successfully in {total_time:.2f}s.")
    return df_results, best_config


def main():
    """CLI execution entrypoint."""
    run_if_sweep()


if __name__ == "__main__":
    main()
