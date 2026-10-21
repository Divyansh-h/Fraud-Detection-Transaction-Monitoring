"""Phase 3 Orchestration Driver Script.

Executes the complete Phase 3 machine learning pipeline in sequence:
1. src/prepare_ml_data.py: Partition scoped data into Train (60%), Val (20%), Test (20%) Parquets
2. src/threshold_tuning.py: Precision-Recall curve, operating points & decision thresholds on Validation
3. src/sweep_isolation_forest.py: Grid sweep over hyperparameters and feature sets (A vs B)
4. src/final_model.py: Full training on Train partition, single-pass evaluation on Test, and full scoring
5. src/ml_diagnostics.py: Score distribution diagnostics & compiling reports/13_phase3_summary.md
"""

from pathlib import Path
import sys
import time

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config
from src.prepare_ml_data import prepare_ml_data
from src.threshold_tuning import tune_thresholds
from src.sweep_isolation_forest import run_if_sweep
from src.final_model import main as run_final_model
from src.ml_diagnostics import run_diagnostics


def run_phase3() -> None:
    """Execute the end-to-end Phase 3 machine learning pipeline in sequence."""
    t_global = time.perf_counter()

    print("==============================================================================")
    print("STARTING PHASE 3: UNSUPERVISED ISOLATION FOREST ANOMALY DETECTION PIPELINE")
    print("==============================================================================")

    # Step 1: src/prepare_ml_data.py
    t0 = time.perf_counter()
    print("\n[Step 1/5] Running src/prepare_ml_data.py: Preparing ML features & partitioned datasets...", flush=True)
    prepare_ml_data()
    print(f"--> [Step 1/5 Completed in {time.perf_counter() - t0:.2f}s]")

    # Step 2: src/threshold_tuning.py
    t0 = time.perf_counter()
    print("\n[Step 2/5] Running src/threshold_tuning.py: Calibrating validation PR curve & thresholds...", flush=True)
    tune_thresholds()
    print(f"--> [Step 2/5 Completed in {time.perf_counter() - t0:.2f}s]")

    # Step 3: src/sweep_isolation_forest.py
    t0 = time.perf_counter()
    print("\n[Step 3/5] Running src/sweep_isolation_forest.py: Executing hyperparameter & feature sweep...", flush=True)
    run_if_sweep()
    print(f"--> [Step 3/5 Completed in {time.perf_counter() - t0:.2f}s]")

    # Step 4: src/final_model.py
    t0 = time.perf_counter()
    print("\n[Step 4/5] Running src/final_model.py: Training final model on FULL data & scoring scoped transactions...", flush=True)
    run_final_model()
    print(f"--> [Step 4/5 Completed in {time.perf_counter() - t0:.2f}s]")

    # Step 5: src/ml_diagnostics.py
    t0 = time.perf_counter()
    print("\n[Step 5/5] Running src/ml_diagnostics.py: Compiling Phase 3 diagnostics & summary report...", flush=True)
    run_diagnostics()
    print(f"--> [Step 5/5 Completed in {time.perf_counter() - t0:.2f}s]")

    total_time = time.perf_counter() - t_global
    print("\n==============================================================================")
    print(f"PHASE 3 COMPLETED SUCCESSFULLY in {total_time:.2f}s")
    print("Key Artifacts Generated:")
    print(f"  - Partitions: ml_train.parquet, ml_val.parquet, ml_test.parquet")
    print(f"  - Trained Models: {config.MODEL_FINAL_JOBLIB.relative_to(config.PROJECT_ROOT)}")
    print(f"  - Lineage Metadata: {config.MODEL_METADATA_JSON.relative_to(config.PROJECT_ROOT)}")
    print(f"  - PR Curve Plot: {config.FIG_PR_CURVE_VAL.relative_to(config.PROJECT_ROOT)}")
    print(f"  - Grid Sweep CSV: {config.IF_SWEEP_CSV.relative_to(config.PROJECT_ROOT)}")
    print(f"  - Test Evaluation CSV: {config.ML_TEST_RESULTS_CSV.relative_to(config.PROJECT_ROOT)}")
    print(f"  - Production Scored Parquet: {config.ML_SCORES_PARQUET.relative_to(config.PROJECT_ROOT)}")
    print(f"  - Phase 3 Summary Report: {config.PHASE3_SUMMARY_MD.relative_to(config.PROJECT_ROOT)}")
    print("==============================================================================")


if __name__ == "__main__":
    run_phase3()
