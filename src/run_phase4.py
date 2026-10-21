"""Phase 4 Master Orchestration Pipeline.

Executes the entire Phase 4 Transaction Monitoring & Reporting pipeline in sequence:
1. src/build_alerts.py: Merges clean data, DuckDB SQL rule flags, and ML anomaly scores into master_alerts.parquet.
2. src/combine_strategies.py: Computes hybrid union (combo_or), consensus (combo_and), combo_score, and risk bands.
3. src/compare_approaches.py: Benchmarks strategies across Full & Scoped universes and exports report 14.
4. src/cost_analysis.py: Calculates operational review costs, direct fraud loss, and savings across strategies.
5. src/final_alerts.py: Enriches master_alerts with official alert flags and outputs reports/16_final_metrics.json.
6. src/export_powerbi_fact.py: Exports fact_transactions.csv (100% of alerts/frauds + stratified legitimate sample).
7. src/export_powerbi_dims.py: Exports six star-schema dimension tables (type, day, hour, source, risk, amount).
8. src/export_powerbi_aggs.py: Pre-aggregates 7 summary CSV tables over the full 6.36M transaction universe.
9. src/export_powerbi_metrics.py: Exports performance metric summary cards, approach matrix, and confusion matrix.
"""

from pathlib import Path
import sys
import time

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config
from src.build_alerts import build_alerts
from src.combine_strategies import combine_strategies
from src.compare_approaches import compare_approaches
from src.cost_analysis import run_cost_analysis
from src.final_alerts import compute_final_alerts
from src.export_powerbi_fact import export_powerbi_fact
from src.export_powerbi_dims import export_powerbi_dims
from src.export_powerbi_aggs import export_powerbi_aggs
from src.export_powerbi_metrics import export_powerbi_metrics


def run_phase4() -> None:
    """Execute the complete Phase 4 pipeline in sequential dependency order."""
    t_global = time.perf_counter()
    print("==============================================================================")
    print("STARTING PHASE 4: TRANSACTION MONITORING, STRATEGY ENRICHMENT & REPORTING")
    print("==============================================================================")

    # Step 1: build_alerts
    t0 = time.perf_counter()
    print("\n[Step 1/9] Running src/build_alerts.py...", flush=True)
    build_alerts()
    print(f"--> [Step 1/9 Completed in {time.perf_counter() - t0:.2f}s]")

    # Step 2: combine_strategies
    t0 = time.perf_counter()
    print("\n[Step 2/9] Running src/combine_strategies.py...", flush=True)
    combine_strategies()
    print(f"--> [Step 2/9 Completed in {time.perf_counter() - t0:.2f}s]")

    # Step 3: compare_approaches
    t0 = time.perf_counter()
    print("\n[Step 3/9] Running src/compare_approaches.py...", flush=True)
    compare_approaches()
    print(f"--> [Step 3/9 Completed in {time.perf_counter() - t0:.2f}s]")

    # Step 4: cost_analysis
    t0 = time.perf_counter()
    print("\n[Step 4/9] Running src/cost_analysis.py...", flush=True)
    run_cost_analysis()
    print(f"--> [Step 4/9 Completed in {time.perf_counter() - t0:.2f}s]")

    # Step 5: final_alerts
    t0 = time.perf_counter()
    print("\n[Step 5/9] Running src/final_alerts.py...", flush=True)
    compute_final_alerts()
    print(f"--> [Step 5/9 Completed in {time.perf_counter() - t0:.2f}s]")

    # Step 6: export_powerbi_fact
    t0 = time.perf_counter()
    print("\n[Step 6/9] Running src/export_powerbi_fact.py...", flush=True)
    export_powerbi_fact()
    print(f"--> [Step 6/9 Completed in {time.perf_counter() - t0:.2f}s]")

    # Step 7: export_powerbi_dims
    t0 = time.perf_counter()
    print("\n[Step 7/9] Running src/export_powerbi_dims.py...", flush=True)
    export_powerbi_dims()
    print(f"--> [Step 7/9 Completed in {time.perf_counter() - t0:.2f}s]")

    # Step 8: export_powerbi_aggs
    t0 = time.perf_counter()
    print("\n[Step 8/9] Running src/export_powerbi_aggs.py...", flush=True)
    export_powerbi_aggs()
    print(f"--> [Step 8/9 Completed in {time.perf_counter() - t0:.2f}s]")

    # Step 9: export_powerbi_metrics
    t0 = time.perf_counter()
    print("\n[Step 9/9] Running src/export_powerbi_metrics.py...", flush=True)
    export_powerbi_metrics()
    print(f"--> [Step 9/9 Completed in {time.perf_counter() - t0:.2f}s]")

    total_time = time.perf_counter() - t_global
    print("\n==============================================================================")
    print(f"PHASE 4 COMPLETED SUCCESSFULLY in {total_time:.2f}s")
    print("Master Outputs Generated:")
    print(f"  - Master Alerts Dataset: {config.MASTER_ALERTS_PARQUET.relative_to(config.PROJECT_ROOT)}")
    print(f"  - Strategy Comparison:   {config.APPROACH_COMP_MD.relative_to(config.PROJECT_ROOT)}")
    print(f"  - Cost-Benefit Analysis: {config.COST_ANALYSIS_MD.relative_to(config.PROJECT_ROOT)}")
    print(f"  - Final Metrics JSON:    {config.FINAL_METRICS_JSON.relative_to(config.PROJECT_ROOT)}")
    print(f"  - Power BI Export Dir:   {config.POWERBI_OUTPUT_DIR.relative_to(config.PROJECT_ROOT)} (18 CSV tables)")
    print("==============================================================================")


def main() -> None:
    """CLI execution entrypoint."""
    run_phase4()


if __name__ == "__main__":
    main()
