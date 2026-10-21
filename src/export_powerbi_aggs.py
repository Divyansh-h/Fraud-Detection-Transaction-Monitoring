"""Power BI Pre-Aggregated Summary Tables Exporter.

Executes enterprise-scale aggregation queries across the FULL 6,362,620 transactions
in master_alerts.parquet using DuckDB. Generates seven high-performance aggregate CSV
tables for Power BI Desktop reporting:

1. agg_by_type.csv: KPI volume, alert counts, confusion breakdown, and value by payment type.
2. agg_by_day.csv: Daily temporal trends across the 31-day monitoring horizon.
3. agg_by_hour.csv: Diurnal hourly fraud/alert activity profiles (00:00 to 23:00).
4. agg_by_day_type.csv: Granular day-by-type operational transaction and alert volume.
5. agg_by_source.csv: Alert source attribution breakdown (Both, Rule only, ML only, None).
6. agg_by_risk_band.csv: Distribution across risk tiers (Critical, High, Medium, Low).
7. agg_by_amount_band_type.csv: Matrix of transaction amounts vs. payment types.

Enforces strict mathematical reconciliation across all 7 aggregate tables:
    - sum(total_txns / rows / alert_count) == 6,362,620 (100% transaction coverage)
    - sum(fraud_count / fraud_caught) == 8,213 (100% fraud events preserved)
"""

from pathlib import Path
import sys
import time

import duckdb
import numpy as np
import pandas as pd

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config


def export_powerbi_aggs(
    master_alerts_path: Path = config.MASTER_ALERTS_PARQUET,
    output_dir: Path = config.POWERBI_OUTPUT_DIR,
) -> dict[str, pd.DataFrame]:
    """Execute SQL aggregation queries over master_alerts.parquet and write 7 CSVs.

    Args:
        master_alerts_path: Path to master_alerts.parquet.
        output_dir: Destination folder for the aggregate CSV tables.

    Returns:
        dict[str, pd.DataFrame]: Mapping of aggregate CSV filenames to DataFrames.
    """
    t_start = time.perf_counter()
    print("==================================================")
    print("Exporting Power BI Pre-Aggregated Summary Tables")
    print("==================================================")

    if not master_alerts_path.exists():
        raise FileNotFoundError(f"Master alerts dataset not found at {master_alerts_path}")

    output_dir.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    p_path = str(master_alerts_path)

    # 1. agg_by_type
    print("\n[1/7] Computing agg_by_type.csv...")
    q1 = f"""
        SELECT
            type,
            CAST(COUNT(*) AS BIGINT) AS total_txns,
            ROUND(SUM(amount), 2) AS total_amount,
            CAST(SUM(isFraud) AS BIGINT) AS fraud_count,
            CAST(SUM(is_alert) AS BIGINT) AS alert_count,
            CAST(SUM(tp_flag) AS BIGINT) AS tp,
            CAST(SUM(fp_flag) AS BIGINT) AS fp,
            CAST(SUM(fn_flag) AS BIGINT) AS fn,
            CAST(SUM(tn_flag) AS BIGINT) AS tn,
            ROUND(SUM(CASE WHEN is_alert = 1 THEN amount ELSE 0.0 END), 2) AS flagged_value,
            ROUND(SUM(isFraud) * 100.0 / COUNT(*), 4) AS fraud_rate_pct,
            ROUND(SUM(is_alert) * 100.0 / COUNT(*), 4) AS alert_rate_pct
        FROM '{p_path}'
        GROUP BY type
        ORDER BY total_txns DESC
    """
    df_type = con.execute(q1).df()

    # 2. agg_by_day
    print("\n[2/7] Computing agg_by_day.csv...")
    q2 = f"""
        SELECT
            CAST(day AS BIGINT) AS day,
            CAST(COUNT(*) AS BIGINT) AS total_txns,
            CAST(SUM(isFraud) AS BIGINT) AS fraud_count,
            CAST(SUM(is_alert) AS BIGINT) AS alert_count,
            CAST(SUM(tp_flag) AS BIGINT) AS tp,
            CAST(SUM(fp_flag) AS BIGINT) AS fp,
            CAST(SUM(fn_flag) AS BIGINT) AS fn,
            ROUND(SUM(CASE WHEN is_alert = 1 THEN amount ELSE 0.0 END), 2) AS flagged_value
        FROM '{p_path}'
        GROUP BY day
        ORDER BY day ASC
    """
    df_day = con.execute(q2).df()

    # 3. agg_by_hour
    print("\n[3/7] Computing agg_by_hour.csv...")
    q3 = f"""
        SELECT
            CAST(hour AS BIGINT) AS hour,
            CAST(COUNT(*) AS BIGINT) AS total_txns,
            CAST(SUM(isFraud) AS BIGINT) AS fraud_count,
            CAST(SUM(is_alert) AS BIGINT) AS alert_count,
            CAST(SUM(tp_flag) AS BIGINT) AS tp,
            CAST(SUM(fp_flag) AS BIGINT) AS fp,
            CAST(SUM(fn_flag) AS BIGINT) AS fn,
            ROUND(SUM(CASE WHEN is_alert = 1 THEN amount ELSE 0.0 END), 2) AS flagged_value
        FROM '{p_path}'
        GROUP BY hour
        ORDER BY hour ASC
    """
    df_hour = con.execute(q3).df()

    # 4. agg_by_day_type
    print("\n[4/7] Computing agg_by_day_type.csv...")
    q4 = f"""
        SELECT
            CAST(day AS BIGINT) AS day,
            type,
            CAST(COUNT(*) AS BIGINT) AS total_txns,
            CAST(SUM(isFraud) AS BIGINT) AS fraud_count,
            CAST(SUM(is_alert) AS BIGINT) AS alert_count,
            ROUND(SUM(CASE WHEN is_alert = 1 THEN amount ELSE 0.0 END), 2) AS flagged_value
        FROM '{p_path}'
        GROUP BY day, type
        ORDER BY day ASC, type ASC
    """
    df_day_type = con.execute(q4).df()

    # 5. agg_by_source
    print("\n[5/7] Computing agg_by_source.csv...")
    q5 = f"""
        SELECT
            alert_source,
            CAST(COUNT(*) AS BIGINT) AS alert_count,
            CAST(SUM(isFraud) AS BIGINT) AS fraud_caught,
            CAST(SUM(fp_flag) AS BIGINT) AS fp,
            ROUND(SUM(CASE WHEN is_alert = 1 THEN amount ELSE 0.0 END), 2) AS flagged_value,
            ROUND(SUM(isFraud) * 100.0 / NULLIF(COUNT(*), 0), 4) AS precision_pct
        FROM '{p_path}'
        GROUP BY alert_source
        ORDER BY alert_count DESC
    """
    df_source = con.execute(q5).df()

    # 6. agg_by_risk_band (Enforcing all 4 bands: Critical, High, Medium, Low)
    print("\n[6/7] Computing agg_by_risk_band.csv...")
    q6 = f"""
        WITH all_bands AS (
            SELECT 'Critical' AS risk_band, 1 AS ord
            UNION ALL SELECT 'High', 2
            UNION ALL SELECT 'Medium', 3
            UNION ALL SELECT 'Low', 4
        ),
        agg AS (
            SELECT
                risk_band,
                COUNT(*) AS rows,
                SUM(isFraud) AS fraud_count,
                ROUND(SUM(CASE WHEN is_alert = 1 THEN amount ELSE 0.0 END), 2) AS flagged_value
            FROM '{p_path}'
            GROUP BY risk_band
        )
        SELECT
            b.risk_band,
            CAST(COALESCE(a.rows, 0) AS BIGINT) AS rows,
            CAST(COALESCE(a.fraud_count, 0) AS BIGINT) AS fraud_count,
            COALESCE(a.flagged_value, 0.00) AS flagged_value
        FROM all_bands b
        LEFT JOIN agg a ON b.risk_band = a.risk_band
        ORDER BY b.ord ASC
    """
    df_risk = con.execute(q6).df()

    # 7. agg_by_amount_band_type
    print("\n[7/7] Computing agg_by_amount_band_type.csv...")
    q7 = f"""
        SELECT
            amount_band,
            type,
            CAST(COUNT(*) AS BIGINT) AS total_txns,
            CAST(SUM(isFraud) AS BIGINT) AS fraud_count,
            CAST(SUM(is_alert) AS BIGINT) AS alert_count
        FROM '{p_path}'
        GROUP BY amount_band, type
        ORDER BY amount_band ASC, type ASC
    """
    df_amount_band = con.execute(q7).df()

    # Aggregates Dictionary
    aggs = {
        "agg_by_type.csv": (df_type, "total_txns", "fraud_count"),
        "agg_by_day.csv": (df_day, "total_txns", "fraud_count"),
        "agg_by_hour.csv": (df_hour, "total_txns", "fraud_count"),
        "agg_by_day_type.csv": (df_day_type, "total_txns", "fraud_count"),
        "agg_by_source.csv": (df_source, "alert_count", "fraud_caught"),
        "agg_by_risk_band.csv": (df_risk, "rows", "fraud_count"),
        "agg_by_amount_band_type.csv": (df_amount_band, "total_txns", "fraud_count"),
    }

    # Reconciliation and Acceptance Verification
    print("\n" + "=" * 80)
    print(f"{'Reconciliation Audit (Expected: Txns = 6,362,620 | Frauds = 8,213)':^80}")
    print("=" * 80)

    for filename, (df_agg, tx_col, fraud_col) in aggs.items():
        sum_txns = int(df_agg[tx_col].sum())
        sum_frauds = int(df_agg[fraud_col].sum())

        assert sum_txns == config.EXPECTED_ROWS, (
            f"Reconciliation FAILED for {filename}: {tx_col}.sum() = {sum_txns:,} != {config.EXPECTED_ROWS:,}"
        )
        assert sum_frauds == config.EXPECTED_FRAUD, (
            f"Reconciliation FAILED for {filename}: {fraud_col}.sum() = {sum_frauds:,} != {config.EXPECTED_FRAUD:,}"
        )

        print(f"  --> {filename:<28} | {tx_col}.sum() = {sum_txns:>9,} | {fraud_col}.sum() = {sum_frauds:>5,} [PASSED]")

        # Write to disk
        dest_file = output_dir / filename
        df_agg.to_csv(dest_file, index=False, encoding="utf-8")

    # Display Preview Heads
    print("\n" + "=" * 80)
    print(f"{'Summary Table Previews (Heads)':^80}")
    print("=" * 80)
    for filename, (df_agg, _, _) in aggs.items():
        print(f"\n--- {filename} ({len(df_agg)} rows) ---")
        print(df_agg.head(5).to_string(index=False))

    print("\n" + "=" * 80)
    print(f"All 7 aggregate tables exported and verified successfully in {time.perf_counter() - t_start:.2f}s.")

    return {filename: df for filename, (df, _, _) in aggs.items()}


def main() -> None:
    """CLI execution entrypoint."""
    export_powerbi_aggs()


if __name__ == "__main__":
    main()
