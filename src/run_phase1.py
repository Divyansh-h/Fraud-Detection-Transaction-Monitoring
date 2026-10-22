"""Phase 1 Master Pipeline Runner.

File: src/run_phase1.py
Purpose: Executes all Phase 1 data ingestion, profiling, cleaning, feature engineering,
stratified partitioning, and exploratory visual analysis steps sequentially:
1. Ingest raw CSV, validate schemas, engineer balance/outlier features, export transactions_clean.parquet.
2. Run data profiling, duplicate analysis, balance checks, validity verification, and outlier diagnostics.
3. Generate leak-free 60/20/20 stratified split assignments (split_assignment.parquet).
4. Generate publication-grade EDA figures in reports/figures/ and compile reports/07_phase1_summary.md.

Logs individual execution durations and reports total phase runtime.
"""

from pathlib import Path
import sys
import time

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config
from src.build_clean import build_clean_dataset
from src.profile_data import run_profiling
from src.validate_duplicates import validate_duplicates_and_ids
from src.balance_checks import run_balance_analysis
from src.validity_checks import run_validity_checks
from src.outlier_analysis import run_outlier_analysis
from src.imbalance_split import create_imbalance_splits
from src.eda_figures import generate_eda_figures, build_phase1_summary_report


def run_phase1() -> None:
    """Execute complete Phase 1 pipeline in sequence."""
    t_start = time.perf_counter()

    print("==============================================================================")
    print("STARTING PHASE 1: DATA INGESTION, PROFILING, VALIDATION & CLEANING PIPELINE")
    print("==============================================================================")

    # Step 1: Ingest, clean, engineer balance/outlier features, and export clean parquet
    print("\n[Step 1/4] Building clean master dataset (transactions_clean.parquet)...")
    t0 = time.perf_counter()
    df_clean = build_clean_dataset()
    print(f"--> [Step 1/4 Completed in {time.perf_counter() - t0:.2f}s]")

    # Step 2: In-depth profiling, balance, validity, and outlier audit reports
    print("\n[Step 2/4] Executing Phase 1 analytical audits and diagnostic reports...")
    t0 = time.perf_counter()
    run_profiling(df_clean)
    validate_duplicates_and_ids(df_clean)
    run_balance_analysis(df_clean)
    run_validity_checks(df_clean)
    run_outlier_analysis(df_clean)
    print(f"--> [Step 2/4 Completed in {time.perf_counter() - t0:.2f}s]")

    # Step 3: Stratified split generation on TRANSFER & CASH_OUT
    print("\n[Step 3/4] Generating stratified split assignments (split_assignment.parquet)...")
    t0 = time.perf_counter()
    create_imbalance_splits()
    print(f"--> [Step 3/4 Completed in {time.perf_counter() - t0:.2f}s]")

    # Step 4: Exploratory data visualization and summary report
    print("\n[Step 4/4] Generating EDA figures and Phase 1 executive summary report...")
    t0 = time.perf_counter()
    generate_eda_figures(df_clean)
    build_phase1_summary_report(df_clean)
    print(f"--> [Step 4/4 Completed in {time.perf_counter() - t0:.2f}s]")

    total_time = time.perf_counter() - t_start
    print("\n==============================================================================")
    print(f"PHASE 1 COMPLETE: Successfully generated clean data, splits, figures & reports in {total_time:.2f}s")
    print("==============================================================================")


if __name__ == "__main__":
    run_phase1()
