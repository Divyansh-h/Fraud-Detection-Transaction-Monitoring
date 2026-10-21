"""Power BI Dimension Tables Exporter.

Constructs normalized star-schema dimension tables for Power BI Desktop:
1. dim_type.csv: Transaction types categorized by fraud risk and display sort order.
2. dim_day.csv: Relative simulated simulation days (Day 01 to Day 31), day-of-week, and week index.
3. dim_hour.csv: Transaction hours (00:00 to 23:00) mapped to operational time bands.
4. dim_alert_source.csv: Attribution classification (Both, Rule only, ML only, None) and sort order.
5. dim_risk_band.csv: Tiered risk bands (Critical, High, Medium, Low) and priority sort order.
6. dim_amount_band.csv: Monetary bands (<1K, 1K-10K, 10K-100K, 100K-1M, >1M) and magnitude sort order.

Enforces strict primary key uniqueness across all dimension tables and verifies
referential integrity against fact_transactions.csv.
"""

from pathlib import Path
import sys
import time

import numpy as np
import pandas as pd

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config


def build_dim_type() -> pd.DataFrame:
    """Generate dim_type DataFrame.

    Returns:
        pd.DataFrame: Dimension table for transaction types.
    """
    records = [
        {"type": "TRANSFER", "type_group": "Fraud-prone", "type_sort": 1},
        {"type": "CASH_OUT", "type_group": "Fraud-prone", "type_sort": 2},
        {"type": "CASH_IN", "type_group": "No fraud observed", "type_sort": 3},
        {"type": "PAYMENT", "type_group": "No fraud observed", "type_sort": 4},
        {"type": "DEBIT", "type_group": "No fraud observed", "type_sort": 5},
    ]
    df = pd.DataFrame(records)
    assert df["type"].is_unique, "dim_type primary key 'type' is not unique"
    return df


def build_dim_day(max_day: int = 31) -> pd.DataFrame:
    """Generate dim_day DataFrame.

    Args:
        max_day: Maximum day number in the dataset (PaySim max step 743 -> Day 31).

    Returns:
        pd.DataFrame: Dimension table for simulation days.
    """
    records = []
    for d in range(1, max_day + 1):
        records.append({
            "day": d,
            "day_label": f"Day {d:02d}",
            "day_of_week_index": ((d - 1) % 7) + 1,
            "week_number": ((d - 1) // 7) + 1,
        })
    df = pd.DataFrame(records)
    assert df["day"].is_unique, "dim_day primary key 'day' is not unique"
    return df


def build_dim_hour() -> pd.DataFrame:
    """Generate dim_hour DataFrame.

    Returns:
        pd.DataFrame: Dimension table for transaction hours and time bands.
    """
    records = []
    for h in range(24):
        if 0 <= h <= 5:
            band = "Night"
        elif 6 <= h <= 11:
            band = "Morning"
        elif 12 <= h <= 17:
            band = "Afternoon"
        else:
            band = "Evening"

        records.append({
            "hour": h,
            "hour_label": f"{h:02d}:00",
            "time_band": band,
        })
    df = pd.DataFrame(records)
    assert df["hour"].is_unique, "dim_hour primary key 'hour' is not unique"
    return df


def build_dim_alert_source() -> pd.DataFrame:
    """Generate dim_alert_source DataFrame.

    Returns:
        pd.DataFrame: Dimension table for alert attribution sources.
    """
    records = [
        {"alert_source": "Both", "alert_source_sort": 1},
        {"alert_source": "Rule only", "alert_source_sort": 2},
        {"alert_source": "ML only", "alert_source_sort": 3},
        {"alert_source": "None", "alert_source_sort": 4},
    ]
    df = pd.DataFrame(records)
    assert df["alert_source"].is_unique, "dim_alert_source primary key is not unique"
    return df


def build_dim_risk_band() -> pd.DataFrame:
    """Generate dim_risk_band DataFrame.

    Returns:
        pd.DataFrame: Dimension table for composite risk bands.
    """
    records = [
        {"risk_band": "Critical", "risk_band_sort": 1},
        {"risk_band": "High", "risk_band_sort": 2},
        {"risk_band": "Medium", "risk_band_sort": 3},
        {"risk_band": "Low", "risk_band_sort": 4},
    ]
    df = pd.DataFrame(records)
    assert df["risk_band"].is_unique, "dim_risk_band primary key is not unique"
    return df


def build_dim_amount_band() -> pd.DataFrame:
    """Generate dim_amount_band DataFrame.

    Returns:
        pd.DataFrame: Dimension table for amount magnitude intervals.
    """
    records = [
        {"amount_band": "<1K", "amount_band_sort": 1},
        {"amount_band": "1K-10K", "amount_band_sort": 2},
        {"amount_band": "10K-100K", "amount_band_sort": 3},
        {"amount_band": "100K-1M", "amount_band_sort": 4},
        {"amount_band": ">1M", "amount_band_sort": 5},
    ]
    df = pd.DataFrame(records)
    assert df["amount_band"].is_unique, "dim_amount_band primary key is not unique"
    return df


def verify_referential_integrity(
    fact_csv_path: Path,
    dims: dict[str, tuple[pd.DataFrame, str]],
) -> None:
    """Verify that every foreign key in fact_transactions.csv exists in its dimension table.

    Args:
        fact_csv_path: Path to fact_transactions.csv.
        dims: Mapping of dimension names to (dimension_df, key_column).
    """
    print("\nAuditing star-schema referential integrity against fact_transactions.csv...")
    if not fact_csv_path.exists():
        raise FileNotFoundError(f"Fact table not found at {fact_csv_path}")

    # Use keep_default_na=False so that literal string "None" in alert_source is not parsed as NaN
    req_cols = [key_col for _, key_col in dims.values()]
    fact_df = pd.read_csv(fact_csv_path, usecols=req_cols, keep_default_na=False)

    for dim_name, (dim_df, key_col) in dims.items():
        fact_keys = set(fact_df[key_col].unique())
        dim_keys = set(dim_df[key_col].unique())

        unmatched = fact_keys - dim_keys
        assert not unmatched, (
            f"Referential integrity VIOLATION on {dim_name} ({key_col})! "
            f"Unmatched keys in fact table: {unmatched}"
        )
        print(f"  --> Referential integrity PASSED: fact.{key_col} (distinct: {len(fact_keys)}) is 100% covered by {dim_name}.{key_col}")


def export_powerbi_dims(
    output_dir: Path = config.POWERBI_OUTPUT_DIR,
    fact_csv_path: Path = config.FACT_TRANSACTIONS_CSV,
) -> dict[str, pd.DataFrame]:
    """Generate, validate, and serialize the six Power BI dimension CSV tables.

    Args:
        output_dir: Destination folder for dimension CSV files.
        fact_csv_path: Path to fact_transactions.csv for referential integrity audits.

    Returns:
        dict[str, pd.DataFrame]: Dictionary mapping dimension table names to DataFrames.
    """
    t_start = time.perf_counter()
    print("==================================================")
    print("Generating Power BI Dimension Tables (Star Schema)")
    print("==================================================")

    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Build dimension DataFrames
    dim_type = build_dim_type()
    dim_day = build_dim_day(max_day=31)
    dim_hour = build_dim_hour()
    dim_alert_source = build_dim_alert_source()
    dim_risk_band = build_dim_risk_band()
    dim_amount_band = build_dim_amount_band()

    dim_files = {
        "dim_type.csv": (dim_type, "type"),
        "dim_day.csv": (dim_day, "day"),
        "dim_hour.csv": (dim_hour, "hour"),
        "dim_alert_source.csv": (dim_alert_source, "alert_source"),
        "dim_risk_band.csv": (dim_risk_band, "risk_band"),
        "dim_amount_band.csv": (dim_amount_band, "amount_band"),
    }

    # 2. Check referential integrity with fact_transactions.csv
    verify_referential_integrity(fact_csv_path, dim_files)

    # 3. Export CSV files
    print("\nWriting dimension tables to disk...")
    print("=" * 65)
    print(f"{'Dimension File':<25} | {'Rows':>6} | {'Columns':>8} | {'Destination':<20}")
    print("-" * 65)

    for filename, (df, _) in dim_files.items():
        dest_path = output_dir / filename
        df.to_csv(dest_path, index=False, encoding="utf-8")
        print(f"{filename:<25} | {len(df):>6} | {len(df.columns):>8} | {dest_path.name}")

    print("=" * 65)
    print(f"\nAll 6 dimension tables exported and verified in {time.perf_counter() - t_start:.2f}s.")

    return {name: df for name, (df, _) in dim_files.items()}


def main() -> None:
    """CLI execution entrypoint."""
    export_powerbi_dims()


if __name__ == "__main__":
    main()
