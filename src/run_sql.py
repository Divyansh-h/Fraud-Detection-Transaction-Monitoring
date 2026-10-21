"""SQL file execution runner for DuckDB."""

import argparse
import re
import sys
import time
from pathlib import Path
import pandas as pd

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config
from src.db import get_connection


def split_sql_statements(sql_text: str) -> list[str]:
    """Split SQL text into individual executable statements on semicolons.

    Correctly ignores semicolons inside single-line comments (--),
    multi-line comments (/* ... */), single-quoted strings, and double-quoted identifiers.

    Args:
        sql_text: Raw SQL script content.

    Returns:
        list[str]: Clean list of SQL statements.
    """
    statements = []
    current: list[str] = []
    in_single_quote = False
    in_double_quote = False
    in_single_comment = False
    in_multi_comment = False
    i = 0
    n = len(sql_text)

    while i < n:
        c = sql_text[i]
        next_c = sql_text[i + 1] if i + 1 < n else ""

        if in_single_comment:
            current.append(c)
            if c == "\n":
                in_single_comment = False
            i += 1
            continue

        if in_multi_comment:
            current.append(c)
            if c == "*" and next_c == "/":
                current.append("/")
                in_multi_comment = False
                i += 2
                continue
            i += 1
            continue

        if in_single_quote:
            current.append(c)
            if c == "'":
                if next_c == "'":
                    current.append("'")
                    i += 2
                    continue
                in_single_quote = False
            i += 1
            continue

        if in_double_quote:
            current.append(c)
            if c == '"':
                if next_c == '"':
                    current.append('"')
                    i += 2
                    continue
                in_double_quote = False
            i += 1
            continue

        # Detect comment start
        if c == "-" and next_c == "-":
            in_single_comment = True
            current.append(c)
            current.append(next_c)
            i += 2
            continue

        if c == "/" and next_c == "*":
            in_multi_comment = True
            current.append(c)
            current.append(next_c)
            i += 2
            continue

        if c == "'":
            in_single_quote = True
            current.append(c)
            i += 1
            continue

        if c == '"':
            in_double_quote = True
            current.append(c)
            i += 1
            continue

        if c == ";":
            stmt = "".join(current).strip()
            if stmt:
                statements.append(stmt)
            current = []
            i += 1
            continue

        current.append(c)
        i += 1

    last_stmt = "".join(current).strip()
    if last_stmt:
        statements.append(last_stmt)

    return statements


def is_result_returning(stmt: str) -> bool:
    """Check if statement is a query expected to produce tabular results."""
    clean = re.sub(r"--.*?$|/\*.*?\*/", "", stmt, flags=re.DOTALL | re.MULTILINE).strip().upper()
    result_keywords = ("SELECT", "WITH", "DESCRIBE", "EXPLAIN", "SHOW", "PRAGMA")
    return any(clean.startswith(kw) for kw in result_keywords)


def run_sql_file(path: Path | str, conn=None) -> list[pd.DataFrame]:
    """Read a .sql file, execute all statements safely, and print SELECT results.

    Args:
        path: Path to the .sql file.
        conn: Optional active DuckDB connection. If None, acquired via get_connection().

    Returns:
        list[pd.DataFrame]: List of DataFrames returned by query statements in the file.
    """
    sql_path = Path(path)
    if not sql_path.is_absolute():
        sql_path = config.PROJECT_ROOT / sql_path

    if not sql_path.exists():
        raise FileNotFoundError(f"SQL file not found at: {sql_path}")

    print(f"\n==================================================")
    print(f"Executing SQL Script: {sql_path.relative_to(config.PROJECT_ROOT)}")
    print(f"==================================================")

    with open(sql_path, "r", encoding="utf-8") as f:
        sql_content = f.read()

    statements = split_sql_statements(sql_content)
    print(f"Found {len(statements)} executable SQL statement(s).")

    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    results = []
    try:
        pd.set_option("display.max_columns", None)
        pd.set_option("display.width", 1000)

        for idx, stmt in enumerate(statements, 1):
            # Print brief preview of statement
            first_line = stmt.strip().split("\n")[0][:80]
            print(f"\n[Statement {idx}/{len(statements)}] {first_line}...")

            t_start = time.perf_counter()
            rel = conn.execute(stmt)

            if is_result_returning(stmt):
                df = rel.df()
                elapsed = time.perf_counter() - t_start
                results.append(df)
                print(f"\nQuery Result ({elapsed:.3f}s, {len(df):,} rows):")
                print(df.to_string(index=False))
            else:
                elapsed = time.perf_counter() - t_start
                print(f"Executed successfully in {elapsed:.3f}s (no tabular output).")

    finally:
        if close_conn:
            conn.close()

    print(f"\nCompleted execution of: {sql_path.name}")
    return results


def main():
    """CLI entrypoint for run_sql.py."""
    parser = argparse.ArgumentParser(description="Execute .sql files against DuckDB database.")
    parser.add_argument("path", type=str, help="Relative or absolute path to .sql file")
    args = parser.parse_args()

    run_sql_file(args.path)


if __name__ == "__main__":
    main()
