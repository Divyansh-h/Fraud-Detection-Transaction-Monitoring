"""Phase 2 Orchestration Driver Script.

Executes the end-to-end SQL transaction monitoring and rule evaluation pipeline:
1. sql/01_load.sql (Load cleaned parquet into DuckDB transactions table)
2. sql/02_rules.sql (Evaluate rules, create base_scope, and build rule_flags table)
3. src/evaluate_rules.py (Compute precision, recall, F1 metrics & write reports)
4. src/export_rules.py (Export rule_flags table to Parquet & CSV preview)
"""

from pathlib import Path
import sys
import time

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config
from src.run_sql import run_sql_file
from src.evaluate_rules import evaluate_rules, generate_markdown_report
from src.export_rules import export_rules


def run_phase2() -> None:
    """Execute the complete Phase 2 pipeline in sequence with progress messages."""
    t_pipeline_start = time.perf_counter()

    print("==============================================================================")
    print("STARTING PHASE 2: TRANSACTION MONITORING SQL RULE ENGINE & EVALUATION PIPELINE")
    print("==============================================================================")

    # Step 1: Run sql/01_load.sql
    t0 = time.perf_counter()
    print("\n[Step 1/4] Running sql/01_load.sql: Ingesting cleaned transactions into DuckDB...", end=" ", flush=True)
    run_sql_file(config.SQL_LOAD_FILE)
    print(f"--> [Step 1/4 Completed in {time.perf_counter() - t0:.2f}s]")

    # Step 2: Run sql/02_rules.sql
    t0 = time.perf_counter()
    print("\n[Step 2/4] Running sql/02_rules.sql: Evaluating rules and creating rule_flags table...", end=" ", flush=True)
    run_sql_file(config.SQL_RULES_FILE)
    print(f"--> [Step 2/4 Completed in {time.perf_counter() - t0:.2f}s]")

    # Step 3: Run src/evaluate_rules.py
    t0 = time.perf_counter()
    print("\n[Step 3/4] Running src/evaluate_rules.py: Generating CSV and Markdown evaluation reports...", end=" ", flush=True)
    df_eval = evaluate_rules()
    config.RULE_EVAL_CSV.parent.mkdir(parents=True, exist_ok=True)
    df_eval.to_csv(config.RULE_EVAL_CSV, index=False)
    generate_markdown_report(df_eval, config.RULE_EVAL_MD)
    print(f"--> [Step 3/4 Completed in {time.perf_counter() - t0:.2f}s]")

    # Step 4: Run src/export_rules.py
    t0 = time.perf_counter()
    print("\n[Step 4/4] Running src/export_rules.py: Exporting rule_flags table to Parquet & CSV preview...", end=" ", flush=True)
    export_rules(verbose=False)
    print(f"--> [Step 4/4 Completed in {time.perf_counter() - t0:.2f}s]")

    total_time = time.perf_counter() - t_pipeline_start
    print("\n==============================================================================")
    print(f"PHASE 2 COMPLETED SUCCESSFULLY in {total_time:.2f}s")
    print(f"Artifacts Created:")
    print(f"  - Database: {config.DB_PATH.relative_to(config.PROJECT_ROOT)}")
    print(f"  - Parquet Export: {config.RULE_FLAGS_PARQUET.relative_to(config.PROJECT_ROOT)}")
    print(f"  - CSV Preview: {config.RULE_FLAGS_PREVIEW_CSV.relative_to(config.PROJECT_ROOT)}")
    print(f"  - Evaluation CSV: {config.RULE_EVAL_CSV.relative_to(config.PROJECT_ROOT)}")
    print(f"  - Evaluation Report: {config.RULE_EVAL_MD.relative_to(config.PROJECT_ROOT)}")
    print("==============================================================================")


if __name__ == "__main__":
    run_phase2()
