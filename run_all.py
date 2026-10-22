"""Master Pipeline Runner.

Executes all project stages end-to-end:
1. Phase 1: Ingestion, cleaning, feature engineering, split generation, EDA figures (run_phase1.py)
2. Phase 2: DuckDB SQL rule engine & rule evaluation reporting (run_phase2.py)
3. Phase 3: Unsupervised Isolation Forest modeling, sweep, and diagnostics (run_phase3.py)
4. Phase 4: Strategy fusion, cost optimization, and Power BI CSV exports (run_phase4.py)
5. Documentation: Automated README.md compilation and verification (build_readme.py)

Tracks individual stage elapsed timings and prints a final PIPELINE COMPLETE summary.
Stops execution immediately with a clear error if any stage fails.
"""

from pathlib import Path
import sys
import time

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.run_phase1 import run_phase1
from src.run_phase2 import run_phase2
from src.run_phase3 import run_phase3
from src.run_phase4 import run_phase4
from src.build_readme import main as build_readme


def run_pipeline() -> None:
    """Execute end-to-end pipeline with error handling and stage timing."""
    stages = [
        ("Phase 1: Ingestion, Cleaning & EDA", run_phase1),
        ("Phase 2: DuckDB SQL Rule Engine", run_phase2),
        ("Phase 3: Machine Learning & Isolation Forest", run_phase3),
        ("Phase 4: Strategy Fusion & Power BI Exports", run_phase4),
        ("Documentation: Compile README.md", build_readme),
    ]

    t_global_start = time.perf_counter()
    timings = []

    print("==============================================================================")
    print("STARTING COMPLETE TRANSACTION MONITORING & FRAUD SURVEILLANCE PIPELINE")
    print(f"Project Root: {PROJECT_ROOT}")
    print("==============================================================================")

    for idx, (stage_name, stage_fn) in enumerate(stages, 1):
        print(f"\n[{idx}/{len(stages)}] >>> STARTING: {stage_name}...")
        t_stage_start = time.perf_counter()
        try:
            stage_fn()
            elapsed = time.perf_counter() - t_stage_start
            timings.append((stage_name, elapsed, "SUCCESS"))
            print(f"[{idx}/{len(stages)}] <<< COMPLETED: {stage_name} in {elapsed:.2f}s")
        except Exception as e:
            elapsed = time.perf_counter() - t_stage_start
            timings.append((stage_name, elapsed, f"FAILED: {e}"))
            print(f"\n[FATAL ERROR] Stage '{stage_name}' failed after {elapsed:.2f}s with error:")
            print(f"  {type(e).__name__}: {e}")
            print("\nExecution stopped. Fix the error above and rerun.")
            sys.exit(1)

    total_time = time.perf_counter() - t_global_start

    print("\n==============================================================================")
    print("STAGE EXECUTION TIMINGS SUMMARY:")
    print("------------------------------------------------------------------------------")
    for name, elapsed, status in timings:
        print(f"  * {name:<46} : {elapsed:6.2f}s [{status}]")
    print("------------------------------------------------------------------------------")
    print(f"  TOTAL END-TO-END PIPELINE RUNTIME         : {total_time:6.2f}s ({total_time / 60:.2f} min)")
    print("==============================================================================")
    print("PIPELINE COMPLETE")
    print("==============================================================================")


if __name__ == "__main__":
    run_pipeline()
