"""DuckDB connection and database management module."""

import sys
from pathlib import Path
import duckdb

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config


def get_connection(
    db_path: Path | str | None = None, read_only: bool = False
) -> duckdb.DuckDBPyConnection:
    """Open (creating if necessary) and return a DuckDB connection to fraud.duckdb.

    Args:
        db_path: Path to DuckDB database file. Defaults to config.DB_PATH.
        read_only: Whether to open database in read-only mode.

    Returns:
        duckdb.DuckDBPyConnection: Active database connection.
    """
    target_path = Path(db_path) if db_path is not None else config.DB_PATH
    target_path.parent.mkdir(parents=True, exist_ok=True)

    conn = duckdb.connect(database=str(target_path), read_only=read_only)
    return conn


if __name__ == "__main__":
    conn = get_connection()
    ver = conn.execute("SELECT version();").fetchone()[0]
    print(f"Connected to DuckDB at: {config.DB_PATH}")
    print(f"DuckDB engine version: {ver}")
    conn.close()
