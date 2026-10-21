"""Export Rule Flags from DuckDB to Parquet and CSV Preview.

Exports the rule_flags table from DuckDB to data/outputs/rule_flags.parquet (Snappy compressed)
and writes data/outputs/rule_flags_head1000.csv for inspection.
"""

from pathlib import Path
import sys
import time

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config
from src.db import get_connection


def export_rules(conn=None, verbose: bool = True) -> tuple[Path, Path]:
    """Export rule_flags table to Parquet (Snappy) and a 1000-row preview CSV.

    Args:
        conn: Optional active DuckDB connection. If None, acquires one via get_connection().
        verbose: Whether to print export summaries.

    Returns:
        tuple[Path, Path]: (parquet_path, csv_path)
    """
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    try:
        config.OUTPUTS_DATA_DIR.mkdir(parents=True, exist_ok=True)
        parquet_path = config.RULE_FLAGS_PARQUET
        csv_path = config.RULE_FLAGS_PREVIEW_CSV

        t_start = time.perf_counter()

        # 1. Export entire rule_flags table to Parquet with Snappy compression
        conn.execute(
            f"COPY rule_flags TO '{parquet_path}' (FORMAT PARQUET, COMPRESSION 'SNAPPY')"
        )
        t_parquet = time.perf_counter() - t_start

        # 2. Export 1000-row preview CSV
        conn.execute(
            f"COPY (SELECT * FROM rule_flags LIMIT 1000) TO '{csv_path}' (HEADER, DELIMITER ',')"
        )
        t_total = time.perf_counter() - t_start

        # Validate row count and file size
        row_count = conn.execute("SELECT COUNT(*) FROM rule_flags").fetchone()[0]
        size_mb = parquet_path.stat().st_size / (1024 * 1024)

        if verbose:
            print(f"Exported rule_flags table ({row_count:,} rows) to:")
            print(f"  - Parquet: {parquet_path.relative_to(config.PROJECT_ROOT)} ({size_mb:.2f} MB, {t_parquet:.3f}s)")
            print(f"  - Preview: {csv_path.relative_to(config.PROJECT_ROOT)} (1,000 rows)")

        return parquet_path, csv_path

    finally:
        if close_conn:
            conn.close()


def main():
    """CLI entrypoint for export_rules.py."""
    print("==================================================")
    print("Exporting Rule Flags to Parquet & CSV Preview")
    print("==================================================")
    export_rules(verbose=True)
    print("\nExport completed successfully.")


if __name__ == "__main__":
    main()
