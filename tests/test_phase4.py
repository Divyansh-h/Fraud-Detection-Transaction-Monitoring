"""Unit tests for Phase 4 master alerts dataset construction."""

from pathlib import Path
import re
import pytest
import pandas as pd
import numpy as np

import config
from src.build_alerts import RULE_COLUMNS


def test_master_alerts_parquet_exists_and_integrity():
    """Assert master_alerts.parquet exists, has 6,362,620 rows, and unique txn_ids."""
    assert config.MASTER_ALERTS_PARQUET.exists(), f"Missing {config.MASTER_ALERTS_PARQUET}"

    df = pd.read_parquet(config.MASTER_ALERTS_PARQUET)
    assert len(df) == config.EXPECTED_ROWS, (
        f"Expected {config.EXPECTED_ROWS:,} rows, got {len(df):,}"
    )
    assert df[config.COL_TXN_ID].nunique() == config.EXPECTED_ROWS, "txn_id not strictly unique"

    # Assert zero NaNs
    nan_count = int(df.isna().sum().sum())
    assert nan_count == 0, f"Detected {nan_count:,} NaNs in master_alerts.parquet"

    # Assert fraud count preserved
    assert int(df[config.COL_IS_FRAUD].sum()) == config.EXPECTED_FRAUD, "Fraud count mismatch"


def test_master_alerts_columns_and_out_of_scope_zero():
    """Assert required columns exist and out-of-scope rows have all zero flags."""
    df = pd.read_parquet(config.MASTER_ALERTS_PARQUET)

    required_cols = [
        "txn_id", "step", "day", "hour", "type", "amount", "nameOrig", "nameDest",
        "oldbalanceOrg", "newbalanceOrig", "oldbalanceDest", "newbalanceDest",
        "alert_score", "anomaly_score", "anomaly_score_pct", "ml_flag", "rule_alert",
        "is_rule_alert_1", "is_rule_alert_2", "isFraud", "split",
    ] + [c for c in RULE_COLUMNS if c not in ["alert_score", "is_rule_alert_1", "is_rule_alert_2"]]

    for col in required_cols:
        assert col in df.columns, f"Required column missing: {col}"

    # Check out-of-scope rows
    out_of_scope = df[~df["type"].isin(config.FRAUD_TYPES)]
    assert len(out_of_scope) == 3592211, f"Expected 3,592,211 out-of-scope rows, got {len(out_of_scope):,}"

    for col in RULE_COLUMNS:
        assert (out_of_scope[col] == 0).all(), f"Out-of-scope rows have non-zero values in {col}"

    assert (out_of_scope["rule_alert"] == 0).all(), "Non-zero rule_alert in out-of-scope rows"
    assert (out_of_scope["ml_flag"] == 0).all(), "Non-zero ml_flag in out-of-scope rows"
    assert (out_of_scope["anomaly_score"] == 0.0).all(), "Non-zero anomaly_score in out-of-scope rows"
    assert (out_of_scope["anomaly_score_pct"] == 0.0).all(), "Non-zero anomaly_score_pct in out-of-scope rows"
    assert (out_of_scope["split"] == "out_of_scope").all(), "Unexpected split in out-of-scope rows"


def test_combine_strategies_columns_and_distributions():
    """Assert hybrid strategy columns adhere to value constraints and zero NaNs."""
    df = pd.read_parquet(config.MASTER_ALERTS_PARQUET)

    # 1. Column existence
    combo_cols = ["alert_source", "combo_or", "combo_and", "combo_score", "risk_band"]
    for col in combo_cols:
        assert col in df.columns, f"Missing hybrid column: {col}"

    # 2. alert_source allowed values
    allowed_sources = {"Both", "Rule only", "ML only", "None"}
    assert set(df["alert_source"].unique()) == allowed_sources

    # 3. combo flags are int8 binary
    assert set(df["combo_or"].unique()).issubset({0, 1})
    assert set(df["combo_and"].unique()).issubset({0, 1})

    # 4. combo_score is within [0.0, 100.0]
    assert 0.0 <= df["combo_score"].min()
    assert df["combo_score"].max() <= 100.0

    # 5. risk_band allowed values
    allowed_bands = {"Critical", "High", "Medium", "Low"}
    assert set(df["risk_band"].unique()).issubset(allowed_bands)

    # 6. Out-of-scope rows must have combo_or=0, combo_and=0, alert_source='None', risk_band='Low'
    out_of_scope = df[~df["type"].isin(config.FRAUD_TYPES)]
    assert (out_of_scope["combo_or"] == 0).all()
    assert (out_of_scope["combo_and"] == 0).all()
    assert (out_of_scope["combo_score"] == 0.0).all()
    assert (out_of_scope["alert_source"] == "None").all()
    assert (out_of_scope["risk_band"] == "Low").all()


def test_approach_comparison_artifacts_exist_and_valid():
    """Assert CSV, MD, and PNG comparison artifacts exist and are non-empty."""
    assert config.APPROACH_COMP_CSV.exists(), f"Missing {config.APPROACH_COMP_CSV}"
    assert config.APPROACH_COMP_MD.exists(), f"Missing {config.APPROACH_COMP_MD}"
    assert config.FIG_APPROACH_COMP.exists(), f"Missing {config.FIG_APPROACH_COMP}"

    assert config.APPROACH_COMP_CSV.stat().st_size > 0, "Empty comparison CSV"
    assert config.APPROACH_COMP_MD.stat().st_size > 0, "Empty comparison MD"
    assert config.FIG_APPROACH_COMP.stat().st_size > 10000, "Comparison PNG too small or invalid"

    # Verify CSV structure and approach presence
    comp_df = pd.read_csv(config.APPROACH_COMP_CSV)
    required_cols = ["universe", "approach", "alerts", "flagged_amount", "TP", "FP", "FN", "TN", "precision", "recall", "fpr", "f1"]
    for col in required_cols:
        assert col in comp_df.columns, f"Missing column in comparison CSV: {col}"

    expected_approaches = {
        "Rules only (rule_alert)",
        "Rules with threshold alert_score >= 2 (is_rule_alert_2)",
        "ML only (ml_flag)",
        "Combined OR (combo_or)",
        "Combined AND (combo_and)",
        "Simulator baseline (not used)",
        "ML only (test-only split)*",
    }
    present_approaches = set(comp_df["approach"].unique())
    assert expected_approaches.issubset(present_approaches), f"Missing approaches: {expected_approaches - present_approaches}"

    # Verify MD contains both tables, the test-only footnote, and conclusion
    md_text = config.APPROACH_COMP_MD.read_text(encoding="utf-8")
    assert "SCOPED Universe" in md_text
    assert "FULL Dataset Universe" in md_text
    assert "Footnote on Machine Learning Evaluation Scope" in md_text
    assert "Combined OR (combo_or)" in md_text
    assert "Combined AND (combo_and)" in md_text
    assert "Simulator baseline (not used)" in md_text
    assert "Empirical Conclusions & Strategic Insights" in md_text


def test_approach_comparison_metrics_consistency():
    """Assert numerical consistency of comparative metrics against known ground truth."""
    comp_df = pd.read_csv(config.APPROACH_COMP_CSV)
    scoped_df = comp_df[comp_df["universe"] == "Scoped Universe (TRANSFER & CASH_OUT)"].set_index("approach")

    # Combined OR: maximal recall
    combo_or = scoped_df.loc["Combined OR (combo_or)"]
    assert combo_or["TP"] == 8196
    assert combo_or["FN"] == 17
    assert np.isclose(combo_or["recall"], 8196 / 8213, atol=1e-4)

    # Combined AND: maximum operational precision
    combo_and = scoped_df.loc["Combined AND (combo_and)"]
    assert combo_and["TP"] == 4167
    assert combo_and["FP"] == 57
    assert combo_and["precision"] > 0.98

    # Simulator baseline: 16 TP, 0 FP, trivial precision 1.0, low recall
    sim = scoped_df.loc["Simulator baseline (not used)"]
    assert sim["TP"] == 16
    assert sim["FP"] == 0
    assert sim["precision"] == 1.0
    assert np.isclose(sim["recall"], 16 / 8213, atol=1e-4)

    # Test-only ML row
    test_ml = comp_df[comp_df["approach"] == "ML only (test-only split)*"].iloc[0]
    assert test_ml["alerts"] == 876
    assert test_ml["TP"] == 846
    assert test_ml["FP"] == 30
    assert test_ml["precision"] > 0.96
    assert test_ml["f1"] > 0.67


def test_final_alerts_columns_and_outcomes():
    """Assert master_alerts has is_alert, tp/fp/fn/tn flags, outcome, and amount_band."""
    df = pd.read_parquet(config.MASTER_ALERTS_PARQUET)

    # 1. is_alert matches ALERT_DEFINITION
    assert "is_alert" in df.columns
    assert (df["is_alert"] == df[config.ALERT_DEFINITION]).all()

    # 2. Confusion flags
    flag_cols = ["tp_flag", "fp_flag", "fn_flag", "tn_flag"]
    for col in flag_cols:
        assert col in df.columns
        assert set(df[col].unique()).issubset({0, 1})

    # Mutually exclusive and collectively exhaustive
    sum_flags = df["tp_flag"] + df["fp_flag"] + df["fn_flag"] + df["tn_flag"]
    assert (sum_flags == 1).all()

    # 3. outcome column
    assert "outcome" in df.columns
    expected_outcomes = {"True Positive", "False Positive", "False Negative", "True Negative"}
    assert set(df["outcome"].unique()) == expected_outcomes
    assert df["outcome"].isna().sum() == 0

    # 4. amount_band column
    assert "amount_band" in df.columns
    expected_bands = {"<1K", "1K-10K", "10K-100K", "100K-1M", ">1M"}
    assert set(df["amount_band"].unique()) == expected_bands
    assert df["amount_band"].isna().sum() == 0


def test_final_metrics_json_integrity():
    """Assert reports/16_final_metrics.json adheres to all accounting and schema constraints."""
    import json
    assert config.FINAL_METRICS_JSON.exists(), f"Missing {config.FINAL_METRICS_JSON}"

    with open(config.FINAL_METRICS_JSON, "r", encoding="utf-8") as f:
        metrics = json.load(f)

    # Assert required keys
    required_keys = [
        "total_transactions", "total_alerts", "total_flagged_value", "fraud_count",
        "overall_fraud_rate", "TP", "FP", "FN", "TN", "precision", "recall", "FPR", "f1",
        "fraud_rate_by_type"
    ]
    for key in required_keys:
        assert key in metrics, f"Missing key in final metrics JSON: {key}"

    # Accounting assertions
    tp = metrics["TP"]
    fp = metrics["FP"]
    fn = metrics["FN"]
    tn = metrics["TN"]
    alerts = metrics["total_alerts"]

    assert tp + fp == alerts, f"TP ({tp}) + FP ({fp}) != alerts ({alerts})"
    assert tp + fn == config.EXPECTED_FRAUD, f"TP ({tp}) + FN ({fn}) != {config.EXPECTED_FRAUD}"
    assert tp + fp + fn + tn == config.EXPECTED_ROWS, f"Total confusion != {config.EXPECTED_ROWS}"

    # Fraud rate by type: all 5 types present, 3 at zero
    by_type = metrics["fraud_rate_by_type"]
    assert len(by_type) == 5
    for t in config.ALL_TYPES:
        assert t in by_type

    zero_count = sum(1 for t, info in by_type.items() if info["fraud_count"] == 0 and info["fraud_rate"] == 0.0)
    assert zero_count == 3, f"Expected 3 zero-fraud types, got {zero_count}"


def test_export_powerbi_fact_csv_integrity():
    """Assert fact_transactions.csv exists, is under ~170MB, has 27 columns, and preserves all fraud."""
    from src.export_powerbi_fact import FACT_COLUMNS

    assert config.FACT_TRANSACTIONS_CSV.exists(), f"Missing {config.FACT_TRANSACTIONS_CSV}"
    file_size_mb = config.FACT_TRANSACTIONS_CSV.stat().st_size / (1024 * 1024)
    assert 50.0 < file_size_mb < 200.0, f"Unexpected fact table size: {file_size_mb:.2f} MB"

    # Read sample/head and audit structure to avoid full CSV re-parsing in fast test runs
    sample_df = pd.read_csv(config.FACT_TRANSACTIONS_CSV, nrows=100)
    assert list(sample_df.columns) == FACT_COLUMNS, "Column mismatch in fact_transactions.csv"
    assert "oldbalanceOrg" not in sample_df.columns, "Raw balance column was not dropped"
    assert "newbalanceOrig" not in sample_df.columns, "Raw balance column was not dropped"

    # Fast validation using chunking or polars/pandas for fraud count
    fraud_count = 0
    total_rows = 0
    row_origins = set()
    for chunk in pd.read_csv(config.FACT_TRANSACTIONS_CSV, usecols=["isFraud", "row_origin"], chunksize=250_000):
        fraud_count += int(chunk["isFraud"].sum())
        total_rows += len(chunk)
        row_origins.update(chunk["row_origin"].unique())

    assert fraud_count == config.EXPECTED_FRAUD, f"Fraud count mismatch in fact table: {fraud_count}"
    assert total_rows == 1_135_626, f"Row count mismatch in fact table: {total_rows}"
    assert row_origins == {"Alert/Fraud", "Normal sample"}


def test_export_powerbi_dims_integrity_and_referential():
    """Assert all 6 dimension CSVs exist, have unique keys, and satisfy referential integrity."""
    dim_configs = [
        (config.DIM_TYPE_CSV, "type", 5),
        (config.DIM_DAY_CSV, "day", 31),
        (config.DIM_HOUR_CSV, "hour", 24),
        (config.DIM_ALERT_SOURCE_CSV, "alert_source", 4),
        (config.DIM_RISK_BAND_CSV, "risk_band", 4),
        (config.DIM_AMOUNT_BAND_CSV, "amount_band", 5),
    ]

    # 1. Existence, row count, uniqueness
    dim_dfs = {}
    for path, key_col, expected_rows in dim_configs:
        assert path.exists(), f"Missing dimension CSV: {path}"
        df = pd.read_csv(path, keep_default_na=False)
        assert len(df) == expected_rows, f"Row count mismatch on {path.name}: expected {expected_rows}, got {len(df)}"
        assert df[key_col].is_unique, f"Primary key {key_col} is not unique in {path.name}"
        dim_dfs[key_col] = (df, set(df[key_col].unique()))

    # 2. Referential integrity against fact_transactions.csv
    fact_cols = [k for _, k, _ in dim_configs]
    fact_sample = pd.read_csv(config.FACT_TRANSACTIONS_CSV, usecols=fact_cols, keep_default_na=False)

    for key_col in fact_cols:
        fact_values = set(fact_sample[key_col].unique())
        _, dim_values = dim_dfs[key_col]
        unmatched = fact_values - dim_values
        assert not unmatched, f"Referential integrity failure for {key_col}: unmatched values {unmatched}"


def test_export_powerbi_aggs_reconciliation_and_schema():
    """Assert all 7 aggregate CSVs exist, match expected schemas, and pass 6.36M / 8213 reconciliation."""
    agg_configs = [
        (
            config.AGG_BY_TYPE_CSV,
            ["type", "total_txns", "total_amount", "fraud_count", "alert_count", "tp", "fp", "fn", "tn", "flagged_value", "fraud_rate_pct", "alert_rate_pct"],
            "total_txns",
            "fraud_count",
        ),
        (
            config.AGG_BY_DAY_CSV,
            ["day", "total_txns", "fraud_count", "alert_count", "tp", "fp", "fn", "flagged_value"],
            "total_txns",
            "fraud_count",
        ),
        (
            config.AGG_BY_HOUR_CSV,
            ["hour", "total_txns", "fraud_count", "alert_count", "tp", "fp", "fn", "flagged_value"],
            "total_txns",
            "fraud_count",
        ),
        (
            config.AGG_BY_DAY_TYPE_CSV,
            ["day", "type", "total_txns", "fraud_count", "alert_count", "flagged_value"],
            "total_txns",
            "fraud_count",
        ),
        (
            config.AGG_BY_SOURCE_CSV,
            ["alert_source", "alert_count", "fraud_caught", "fp", "flagged_value", "precision_pct"],
            "alert_count",
            "fraud_caught",
        ),
        (
            config.AGG_BY_RISK_BAND_CSV,
            ["risk_band", "rows", "fraud_count", "flagged_value"],
            "rows",
            "fraud_count",
        ),
        (
            config.AGG_BY_AMOUNT_BAND_TYPE_CSV,
            ["amount_band", "type", "total_txns", "fraud_count", "alert_count"],
            "total_txns",
            "fraud_count",
        ),
    ]

    for path, expected_cols, tx_col, fraud_col in agg_configs:
        assert path.exists(), f"Missing aggregate CSV: {path}"
        df = pd.read_csv(path, keep_default_na=False)

        # Schema match
        assert list(df.columns) == expected_cols, f"Column mismatch in {path.name}: {list(df.columns)} vs {expected_cols}"

        # Reconciliation
        sum_txns = int(df[tx_col].sum())
        sum_fraud = int(df[fraud_col].sum())
        assert sum_txns == config.EXPECTED_ROWS, f"Volume mismatch in {path.name}: {sum_txns} != {config.EXPECTED_ROWS}"
        assert sum_fraud == config.EXPECTED_FRAUD, f"Fraud count mismatch in {path.name}: {sum_fraud} != {config.EXPECTED_FRAUD}"

        # No NaN in numeric columns
        num_df = df.select_dtypes(include=[np.number])
        nan_count = int(num_df.isna().sum().sum())
        assert nan_count == 0, f"Detected {nan_count} NaNs in numeric columns of {path.name}"


def test_export_powerbi_metrics_integrity_and_reconciliation():
    """Assert all 4 performance metric CSVs exist, schema matches, and numbers reconcile."""
    import json
    assert config.METRICS_OVERALL_CSV.exists()
    assert config.METRICS_APPROACH_CSV.exists()
    assert config.METRICS_RULES_CSV.exists()
    assert config.CONFUSION_MATRIX_CSV.exists()

    with open(config.FINAL_METRICS_JSON, "r", encoding="utf-8") as f:
        m_json = json.load(f)

    # 1. metrics_overall.csv
    df_overall = pd.read_csv(config.METRICS_OVERALL_CSV)
    assert len(df_overall) == 1
    r_overall = df_overall.iloc[0]
    assert r_overall["total_txns"] == config.EXPECTED_ROWS
    assert r_overall["fraud_count"] == config.EXPECTED_FRAUD
    assert r_overall["total_alerts"] == 1_085_609
    assert r_overall["tp"] == 8196
    assert r_overall["fp"] == 1_077_413
    assert r_overall["fn"] == 17
    assert r_overall["tn"] == 5_276_994
    # Confusion matrix sum must equal 6,362,620
    cm_sum = int(r_overall["tp"] + r_overall["fp"] + r_overall["fn"] + r_overall["tn"])
    assert cm_sum == config.EXPECTED_ROWS, f"Confusion sum ({cm_sum}) != {config.EXPECTED_ROWS}"

    assert abs(r_overall["precision_pct"] - m_json["precision"] * 100.0) < 0.01
    assert abs(r_overall["recall_pct"] - m_json["recall"] * 100.0) < 0.01

    # 2. metrics_approach.csv
    df_approach = pd.read_csv(config.METRICS_APPROACH_CSV)
    assert len(df_approach) == 6
    assert "Simulator baseline (reference only)" in set(df_approach["approach"])
    assert "Simulator baseline (not used)" not in set(df_approach["approach"])
    expected_app_cols = ["approach", "alerts", "tp", "fp", "fn", "precision_pct", "recall_pct", "fpr_pct", "f1_pct", "flagged_value"]
    assert list(df_approach.columns) == expected_app_cols

    # 3. metrics_rules.csv
    df_rules = pd.read_csv(config.METRICS_RULES_CSV)
    assert len(df_rules) == 9
    expected_rule_cols = ["rule_name", "alerts", "tp", "fp", "precision_pct", "recall_pct", "fpr_pct", "f1_pct"]
    assert list(df_rules.columns) == expected_rule_cols

    # 4. confusion_matrix.csv
    df_cm = pd.read_csv(config.CONFUSION_MATRIX_CSV)
    assert len(df_cm) == 4
    assert list(df_cm.columns) == ["outcome", "actual", "predicted", "count", "pct_of_total"]
    assert int(df_cm["count"].sum()) == config.EXPECTED_ROWS
    assert set(df_cm["actual"].unique()) == {"Fraud", "Legit"}
    assert set(df_cm["predicted"].unique()) == {"Alert", "No alert"}


def test_all_18_powerbi_csvs_and_data_dictionary_exist():
    """Assert all 18 Power BI CSVs exist and powerbi/data_dictionary.md documents them."""
    expected_csvs = [
        "fact_transactions.csv",
        "dim_type.csv",
        "dim_day.csv",
        "dim_hour.csv",
        "dim_alert_source.csv",
        "dim_risk_band.csv",
        "dim_amount_band.csv",
        "agg_by_type.csv",
        "agg_by_day.csv",
        "agg_by_hour.csv",
        "agg_by_day_type.csv",
        "agg_by_source.csv",
        "agg_by_risk_band.csv",
        "agg_by_amount_band_type.csv",
        "metrics_overall.csv",
        "metrics_approach.csv",
        "metrics_rules.csv",
        "confusion_matrix.csv",
    ]

    for fname in expected_csvs:
        p = config.POWERBI_OUTPUT_DIR / fname
        assert p.exists(), f"Missing expected Power BI CSV: {fname}"
        assert p.stat().st_size > 0, f"Empty CSV file: {fname}"

    dict_md = config.POWERBI_DIR / "data_dictionary.md"
    assert dict_md.exists(), f"Missing {dict_md}"
    text = dict_md.read_text(encoding="utf-8")
    for fname in expected_csvs:
        assert fname in text, f"Table {fname} missing from data dictionary!"


def test_alert_source_strictly_four_allowed_values():
    """Assert alert_source has only the four allowed values across all outputs."""
    allowed = {"Both", "Rule only", "ML only", "None"}

    # In master_alerts.parquet
    df_master = pd.read_parquet(config.MASTER_ALERTS_PARQUET, columns=["alert_source"])
    assert set(df_master["alert_source"].unique()) == allowed

    # In fact_transactions.csv
    df_fact = pd.read_csv(config.FACT_TRANSACTIONS_CSV, usecols=["alert_source"], keep_default_na=False)
    assert set(df_fact["alert_source"].unique()) == allowed

    # In dim_alert_source.csv
    df_dim = pd.read_csv(config.DIM_ALERT_SOURCE_CSV, keep_default_na=False)
    assert set(df_dim["alert_source"].unique()) == allowed

    # In agg_by_source.csv
    df_agg = pd.read_csv(config.AGG_BY_SOURCE_CSV, keep_default_na=False)
    assert set(df_agg["alert_source"].unique()) == allowed

def test_powerbi_import_guide_exists_and_complete():
    """Assert powerbi/01_import_guide.md exists, covers all 18 tables, and includes key instructions."""
    guide_path = config.POWERBI_DIR / "01_import_guide.md"
    assert guide_path.exists(), f"Missing {guide_path}"
    assert guide_path.stat().st_size > 10000, f"Guide file too small: {guide_path.stat().st_size} bytes"

    content = guide_path.read_text(encoding="utf-8")

    # Key instructions
    assert "DataFolder" in content
    assert "Auto date/time" in content
    assert "Don't summarize" in content
    assert "Get Data" in content or "Text/CSV" in content

    # All 18 Power BI table names
    expected_tables = [
        "Fact_Transactions",
        "Dim_Type",
        "Dim_Day",
        "Dim_Hour",
        "Dim_AlertSource",
        "Dim_RiskBand",
        "Dim_AmountBand",
        "Agg_ByType",
        "Agg_ByDay",
        "Agg_ByHour",
        "Agg_ByDayType",
        "Agg_BySource",
        "Agg_ByRiskBand",
        "Agg_ByAmountBandType",
        "Metrics_Overall",
        "Metrics_Approach",
        "Metrics_Rules",
        "Confusion_Matrix",
    ]
    for tbl in expected_tables:
        assert tbl in content, f"Table '{tbl}' missing from 01_import_guide.md"


def test_powerbi_data_model_doc_exists_and_complete():
    """Assert powerbi/02_data_model.md exists, specifies all relationships, Do Not Do list, and visual mapping."""
    doc_path = config.POWERBI_DIR / "02_data_model.md"
    assert doc_path.exists(), f"Missing {doc_path}"
    assert doc_path.stat().st_size > 10000, f"Doc file too small: {doc_path.stat().st_size} bytes"

    content = doc_path.read_text(encoding="utf-8")

    # Star schema and Fact table center
    assert "Fact_Transactions" in content
    assert "Star Schema" in content or "star-schema" in content.lower()

    # Core relationship targets
    assert "Fact_Transactions[type]" in content
    assert "Fact_Transactions[day]" in content
    assert "Fact_Transactions[hour]" in content
    assert "Fact_Transactions[alert_source]" in content
    assert "Fact_Transactions[risk_band]" in content
    assert "Fact_Transactions[amount_band]" in content

    # Aggregate relationship targets
    assert "Agg_ByType[type]" in content
    assert "Agg_ByDay[day]" in content
    assert "Agg_ByHour[hour]" in content
    assert "Agg_ByDayType" in content
    assert "Agg_ByAmountBandType" in content
    assert "Agg_BySource" in content
    assert "Agg_ByRiskBand" in content

    # "Do not do" list items
    assert "NEVER Use Bidirectional" in content or "bidirectional" in content.lower()
    assert "KEEP Metrics_* Tables Disconnected" in content or "disconnected" in content.lower()
    assert "DO NOT Use COUNTROWS(Fact_Transactions)" in content or "sampled" in content.lower()

    # Visual mapping
    assert "Visual-to-Table Mapping Matrix" in content


def test_powerbi_dax_measures_file_exists_and_valid():
    """Assert powerbi/03_measures.dax exists, contains all required DAX measures, and passes schema validation."""
    dax_path = config.POWERBI_DIR / "03_measures.dax"
    assert dax_path.exists(), f"Missing {dax_path}"
    assert dax_path.stat().st_size > 10000, f"DAX file too small: {dax_path.stat().st_size} bytes"

    content = dax_path.read_text(encoding="utf-8")

    # Dedicated table instruction
    assert "_Measures" in content
    assert "Enter Data" in content

    # Check required measures
    required_measures = [
        "[Total Transactions]",
        "[Total Alerts]",
        "[Total Flagged Value]",
        "[Fraud Count]",
        "[Fraud Rate %]",
        "[Alert Rate %]",
        "[True Positives]",
        "[False Positives]",
        "[False Negatives]",
        "[True Negatives]",
        "[Precision]",
        "[Recall]",
        "[False Positive Rate]",
        "[F1 Score]",
        "[Avg Alert Amount]",
        "[Fraud Rate % by Type]",
        "[Missed Fraud Value]",
        "[Caught Fraud Value]",
        "[Alerts Both]",
        "[Alerts Rule Only]",
        "[Alerts ML Only]",
        "[Alert Rank]",
        "[Dynamic Title - Selected Type]",
        "[Color - Precision KPI Card]",
        "[Color - Recall KPI Card]",
    ]
    for m in required_measures:
        assert m in content, f"Measure {m} missing from 03_measures.dax"

    # Division safety: ensure no raw arithmetic division
    lines = [l for l in content.splitlines() if not l.strip().startswith("//") and not l.strip().startswith("/*")]
    stripped = " ".join(lines)
    assert not re.search(r"\]\s*/\s*\[", stripped), "Raw measure division detected without DIVIDE()!"


def test_powerbi_kpi_cards_doc_exists_and_complete():
    """Assert powerbi/04_kpi_cards.md exists, specifies all 6 cards, arithmetic coordinates, and interaction rules."""
    kpi_path = config.POWERBI_DIR / "04_kpi_cards.md"
    assert kpi_path.exists(), f"Missing {kpi_path}"
    assert kpi_path.stat().st_size > 10000, f"KPI guide file too small: {kpi_path.stat().st_size} bytes"

    content = kpi_path.read_text(encoding="utf-8")

    # 6 cards specified
    required_cards = [
        "Total Transactions",
        "Total Alerts",
        "Total Flagged Value",
        "Fraud Rate %",
        "Alert Precision",
        "Fraud Recall",
    ]
    for card in required_cards:
        assert card in content, f"Card '{card}' missing from 04_kpi_cards.md"

    # Coordinates and arithmetic
    assert "1280" in content
    assert "16 px" in content
    assert "Edit interactions" in content
    assert "Alert Source" in content
    assert "Risk Band" in content
    assert "Color - Precision KPI Card" in content
    assert "Color - Recall KPI Card" in content


def test_powerbi_page1_overview_doc_exists_and_complete():
    """Assert powerbi/05_page1_overview.md exists, has complete spec, passes collision checks, and validates fields."""
    from src.check_page1_layout import (
        parse_markdown_visuals_table,
        verify_layout,
        verify_fields_in_csvs,
    )

    doc_path = config.POWERBI_DIR / "05_page1_overview.md"
    assert doc_path.exists(), f"Missing {doc_path}"
    assert doc_path.stat().st_size > 10000, f"Page 1 spec file too small: {doc_path.stat().st_size} bytes"

    content = doc_path.read_text(encoding="utf-8")

    # 1. Page title and metadata
    assert "Executive Overview" in content
    assert "1280 x 720" in content

    # 2. ASCII Wireframe presence
    assert "CANVAS: 1280 x 720 PIXELS" in content
    assert "VIS-01A" in content
    assert "VIS-07" in content

    # 3. Static takeaway with computed metrics
    assert "0.769%" in content
    assert "0.184%" in content
    assert "0.000%" in content
    assert "8,213" in content

    # 4. Required visuals present in markdown table
    required_visual_ids = [
        "VIS-01A", "VIS-01B", "VIS-01C", "VIS-01D", "VIS-01E", "VIS-01F",
        "VIS-02", "VIS-03A", "VIS-03B", "VIS-03C", "VIS-03D",
        "VIS-04", "VIS-05", "VIS-06", "VIS-07"
    ]
    visuals = parse_markdown_visuals_table(doc_path)
    found_ids = [v["clean_id"] for v in visuals]
    for vid in required_visual_ids:
        assert vid in found_ids, f"Visual ID {vid} missing from markdown table"

    # 5. Programmatic collision and canvas bounds check
    verify_layout(visuals)

    # 6. Field existence in exported CSVs
    verify_fields_in_csvs(visuals)


def test_powerbi_page2_and_page3_docs_and_unified_check():
    """Assert powerbi/06_page2_detection.md and powerbi/07_page3_investigation.md exist and pass layout verification."""
    from powerbi.check_layout import (
        load_csv_schemas,
        verify_page,
    )

    page2_path = config.POWERBI_DIR / "06_page2_detection.md"
    page3_path = config.POWERBI_DIR / "07_page3_investigation.md"

    assert page2_path.exists(), f"Missing {page2_path}"
    assert page3_path.exists(), f"Missing {page3_path}"
    assert page2_path.stat().st_size > 10000, f"Page 2 spec too small: {page2_path.stat().st_size} bytes"
    assert page3_path.stat().st_size > 15000, f"Page 3 spec too small: {page3_path.stat().st_size} bytes"

    p2_content = page2_path.read_text(encoding="utf-8")
    assert "Rules vs ML" in p2_content
    assert "VIS-08" in p2_content
    assert "VIS-09" in p2_content
    assert "VIS-10" in p2_content
    assert "VIS-11" in p2_content
    assert "VIS-12" in p2_content

    p3_content = page3_path.read_text(encoding="utf-8")
    assert "Investigation" in p3_content
    assert "VIS-13A" in p3_content
    assert "VIS-14" in p3_content
    assert "VIS-15" in p3_content
    assert "VIS-16" in p3_content
    assert "Account Detail" in p3_content
    assert "DT-01" in p3_content
    assert "DT-04" in p3_content

    # Run unified audit
    csv_schemas = load_csv_schemas()
    p2_visuals = verify_page(page2_path, csv_schemas)
    assert p2_visuals >= 5, f"Expected at least 5 visuals on Page 2, got {p2_visuals}"

    p3_visuals = verify_page(page3_path, csv_schemas)
    assert p3_visuals >= 12, f"Expected at least 12 visuals on Page 3 (including sub-page), got {p3_visuals}"


def test_powerbi_interactions_doc_exists_and_complete():
    """Assert powerbi/08_interactions.md exists and contains complete sync, interaction, bookmark, and tooltip specs."""
    inter_path = config.POWERBI_DIR / "08_interactions.md"
    assert inter_path.exists(), f"Missing {inter_path}"
    assert inter_path.stat().st_size > 15000, f"Interactions file too small: {inter_path.stat().st_size} bytes"

    content = inter_path.read_text(encoding="utf-8")

    # 1. Slicer synchronization
    assert "View > Sync slicers" in content
    assert "Sync_PaymentType" in content
    assert "Sync_DayRange" in content
    assert "Dim_Type[type]" in content
    assert "Dim_Day[day]" in content
    assert "Dim_AlertSource[alert_source]" in content
    assert "Dim_RiskBand[risk_band]" in content

    # 2. Edit-Interactions rules
    assert "Edit interactions" in content
    assert "Total Transactions" in content
    assert "VIS-01A" in content
    assert "VIS-04" in content
    assert "VIS-05" in content

    # 3. Bookmarks
    assert "All transactions" in content
    assert "Fraud-prone types only (TRANSFER + CASH_OUT)" in content
    assert "Critical risk only" in content
    assert "Reset filters" in content

    # 4. Navigation & Alert Definition Tooltip
    assert "Page navigator" in content
    assert "Tooltip - Alert Definition" in content
    assert "7 heuristic SQL rules" in content
    assert "Isolation Forest" in content

    # 5. Tooltip page for VIS-04
    assert "Tooltip - Type Details" in content
    assert "TT-01" in content
    assert "TT-02" in content
    assert "TT-03" in content
    assert "TT-04" in content
    assert "TT-05" in content


def test_powerbi_theme_and_design_doc_exists_and_valid():
    """Assert fraud_theme.json is valid Power BI theme and 09_design.md contains palette and >= 4.5 contrast ratios."""
    import json
    theme_path = config.POWERBI_DIR / "fraud_theme.json"
    design_path = config.POWERBI_DIR / "09_design.md"

    assert theme_path.exists(), f"Missing {theme_path}"
    assert design_path.exists(), f"Missing {design_path}"

    # 1. Validate theme JSON
    with open(theme_path, "r", encoding="utf-8") as f:
        theme = json.load(f)

    assert theme["name"] == "Fraud Monitor"
    assert len(theme["dataColors"]) >= 8
    assert "foreground" in theme
    assert "background" in theme
    assert "tableAccent" in theme
    assert "good" in theme and "neutral" in theme and "bad" in theme
    assert "visualStyles" in theme
    for v in ["card", "slicer", "table", "lineChart", "clusteredBarChart"]:
        assert v in theme["visualStyles"], f"Visual style {v} missing in theme"

    # 2. Validate design document content
    content = design_path.read_text(encoding="utf-8")
    assert "Fraud Monitor" in content
    assert "16 px" in content
    assert "Single Alert Accent Color per Page Rule" in content
    assert "0.000%" in content
    assert "WCAG" in content
    assert "Contrast Ratio" in content

    # 3. Compute and assert all contrast ratios in design doc are >= 4.5
    from src.build_design_theme import CONTRAST_AUDIT_PAIRS, contrast_ratio

    for item in CONTRAST_AUDIT_PAIRS:
        cr = contrast_ratio(item["fg"], item["bg"])
        assert cr >= 4.5, f"Contrast ratio {cr:.2f} for {item['element']} is below 4.5:1!"


def test_readme_and_phase1_runner_integrity():
    """Assert README.md exists, regenerates cleanly without placeholders, and run_phase1.py exists."""
    from src.build_readme import generate_readme_content, README_PATH

    assert README_PATH.exists(), "README.md does not exist"
    assert (config.PROJECT_ROOT / "src" / "run_phase1.py").exists(), "src/run_phase1.py missing"

    content = generate_readme_content()
    assert len(content) > 10000, f"README content too small: {len(content)} chars"

    # Verify no placeholder strings
    for pattern in [r"\bTODO\b", r"\bTBD\b", r"\bX%\b", r"\[Insert", r"\[TBD"]:
        match = re.search(pattern, content)
        assert not match, f"Placeholder pattern {pattern} found in README!"

    # Key metric numbers present
    assert "6,362,620" in content
    assert "8,213" in content
    assert "0.129%" in content
    assert "1,085,609" in content
    assert "99.79%" in content
    assert "98.65%" in content
    assert "TRANSFER" in content
    assert "CASH_OUT" in content


def test_final_audit_suite_passes():
    """Assert src/final_audit.py passes all 10 consistency checks."""
    from src.final_audit import AuditRunner
    runner = AuditRunner()
    success = runner.run_all()
    assert success, "One or more checks in src/final_audit.py failed!"
