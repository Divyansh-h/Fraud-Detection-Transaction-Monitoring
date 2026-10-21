"""Configuration module for Financial Fraud Detection & Transaction Monitoring project."""

from pathlib import Path

# Project root resolved from this file's location
PROJECT_ROOT = Path(__file__).resolve().parent

# Directory paths
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
OUTPUTS_DATA_DIR = DATA_DIR / "outputs"

SRC_DIR = PROJECT_ROOT / "src"
SQL_DIR = PROJECT_ROOT / "sql"
MODELS_DIR = PROJECT_ROOT / "models"
REPORTS_DIR = PROJECT_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"
POWERBI_DIR = PROJECT_ROOT / "powerbi"
TESTS_DIR = PROJECT_ROOT / "tests"

# File paths
RAW_CSV = RAW_DATA_DIR / "PS_20174392719_1491204439457_log.csv"
CLEAN_PARQUET = PROCESSED_DATA_DIR / "transactions_clean.parquet"
PROFILE_REPORT_MD = REPORTS_DIR / "01_profile.md"
FRAUD_BY_TYPE_CSV = REPORTS_DIR / "01_fraud_by_type.csv"
DUPLICATES_REPORT_MD = REPORTS_DIR / "02_duplicates_and_ids.md"
BALANCE_REPORT_MD = REPORTS_DIR / "03_balance_consistency.md"
BALANCE_REPORT_CSV = REPORTS_DIR / "03_balance_consistency.csv"
VALIDITY_REPORT_MD = REPORTS_DIR / "04_validity.md"
VALIDITY_REPORT_CSV = REPORTS_DIR / "04_validity.csv"
OUTLIERS_REPORT_MD = REPORTS_DIR / "05_outliers.md"
IMBALANCE_REPORT_MD = REPORTS_DIR / "06_imbalance_strategy.md"
PHASE1_SUMMARY_MD = REPORTS_DIR / "07_phase1_summary.md"
RULE_EVAL_CSV = REPORTS_DIR / "08_rule_evaluation.csv"
RULE_EVAL_MD = REPORTS_DIR / "08_rule_evaluation.md"
ML_DATA_NOTES_MD = REPORTS_DIR / "09_ml_data_notes.md"
IF_SWEEP_CSV = REPORTS_DIR / "10_if_sweep.csv"
ML_TEST_RESULTS_CSV = REPORTS_DIR / "11_ml_test_results.csv"
ML_DIAGNOSTICS_MD = REPORTS_DIR / "12_ml_diagnostics.md"
PHASE3_SUMMARY_MD = REPORTS_DIR / "13_phase3_summary.md"
APPROACH_COMP_CSV = REPORTS_DIR / "14_approach_comparison.csv"
APPROACH_COMP_MD = REPORTS_DIR / "14_approach_comparison.md"
COST_ANALYSIS_CSV = REPORTS_DIR / "15_cost_analysis.csv"
COST_ANALYSIS_MD = REPORTS_DIR / "15_cost_analysis.md"
FINAL_METRICS_JSON = REPORTS_DIR / "16_final_metrics.json"
SPLIT_ASSIGNMENT_PARQUET = PROCESSED_DATA_DIR / "split_assignment.parquet"
ML_TRAIN_PARQUET = PROCESSED_DATA_DIR / "ml_train.parquet"
ML_VAL_PARQUET = PROCESSED_DATA_DIR / "ml_val.parquet"
ML_TEST_PARQUET = PROCESSED_DATA_DIR / "ml_test.parquet"

# DuckDB Database path
DB_PATH = PROCESSED_DATA_DIR / "fraud.duckdb"

# SQL files
SQL_LOAD_FILE = SQL_DIR / "01_load.sql"
SQL_VERIFY_FILE = SQL_DIR / "00_verify.sql"
SQL_RULES_FILE = SQL_DIR / "02_rules.sql"

# Output files
RULE_FLAGS_PARQUET = OUTPUTS_DATA_DIR / "rule_flags.parquet"
RULE_FLAGS_PREVIEW_CSV = OUTPUTS_DATA_DIR / "rule_flags_head1000.csv"
ML_SCORES_PARQUET = OUTPUTS_DATA_DIR / "ml_scores.parquet"
MASTER_ALERTS_PARQUET = OUTPUTS_DATA_DIR / "master_alerts.parquet"
POWERBI_OUTPUT_DIR = OUTPUTS_DATA_DIR / "powerbi"
FACT_TRANSACTIONS_CSV = POWERBI_OUTPUT_DIR / "fact_transactions.csv"
DIM_TYPE_CSV = POWERBI_OUTPUT_DIR / "dim_type.csv"
DIM_DAY_CSV = POWERBI_OUTPUT_DIR / "dim_day.csv"
DIM_HOUR_CSV = POWERBI_OUTPUT_DIR / "dim_hour.csv"
DIM_ALERT_SOURCE_CSV = POWERBI_OUTPUT_DIR / "dim_alert_source.csv"
DIM_RISK_BAND_CSV = POWERBI_OUTPUT_DIR / "dim_risk_band.csv"
DIM_AMOUNT_BAND_CSV = POWERBI_OUTPUT_DIR / "dim_amount_band.csv"
AGG_BY_TYPE_CSV = POWERBI_OUTPUT_DIR / "agg_by_type.csv"
AGG_BY_DAY_CSV = POWERBI_OUTPUT_DIR / "agg_by_day.csv"
AGG_BY_HOUR_CSV = POWERBI_OUTPUT_DIR / "agg_by_hour.csv"
AGG_BY_DAY_TYPE_CSV = POWERBI_OUTPUT_DIR / "agg_by_day_type.csv"
AGG_BY_SOURCE_CSV = POWERBI_OUTPUT_DIR / "agg_by_source.csv"
AGG_BY_RISK_BAND_CSV = POWERBI_OUTPUT_DIR / "agg_by_risk_band.csv"
AGG_BY_AMOUNT_BAND_TYPE_CSV = POWERBI_OUTPUT_DIR / "agg_by_amount_band_type.csv"
METRICS_OVERALL_CSV = POWERBI_OUTPUT_DIR / "metrics_overall.csv"
METRICS_APPROACH_CSV = POWERBI_OUTPUT_DIR / "metrics_approach.csv"
METRICS_RULES_CSV = POWERBI_OUTPUT_DIR / "metrics_rules.csv"
CONFUSION_MATRIX_CSV = POWERBI_OUTPUT_DIR / "confusion_matrix.csv"

# Saved Models and Thresholds
MODEL_ISOLATION_FOREST = MODELS_DIR / "isolation_forest_baseline.joblib"
MODEL_ISOLATION_FOREST_FINAL = MODELS_DIR / "isolation_forest_final.joblib"
MODEL_FINAL_JOBLIB = MODELS_DIR / "isolation_forest.joblib"
MODEL_METADATA_JSON = MODELS_DIR / "model_metadata.json"
THRESHOLDS_JSON = MODELS_DIR / "thresholds.json"
BEST_CONFIG_JSON = MODELS_DIR / "best_config.json"

FIG_HIST_AMOUNT = FIGURES_DIR / "01_amount_distribution_by_fraud.png"
FIG_BOXPLOT_AMOUNT = FIGURES_DIR / "02_amount_boxplot_by_type.png"
FIG_BAR_FRAUD_RATE = FIGURES_DIR / "03_fraud_rate_by_type.png"
FIG_TX_PER_DAY = FIGURES_DIR / "04_transactions_per_day.png"
FIG_FRAUD_PER_DAY = FIGURES_DIR / "05_fraud_count_per_day.png"
FIG_FRAUD_BY_HOUR = FIGURES_DIR / "06_fraud_by_hour.png"
FIG_ORIG_EMPTIED = FIGURES_DIR / "07_orig_emptied_comparison.png"
FIG_AVG_AMOUNT_BY_TYPE = FIGURES_DIR / "08_avg_amount_by_type.png"
FIG_PR_CURVE_VAL = FIGURES_DIR / "pr_curve_val.png"
FIG_APPROACH_COMP = FIGURES_DIR / "approach_comparison.png"


# Core constants
RANDOM_SEED = 42
FRAUD_TYPES = ["TRANSFER", "CASH_OUT"]
ALL_TYPES = ["CASH_IN", "CASH_OUT", "DEBIT", "PAYMENT", "TRANSFER"]

EXPECTED_ROWS = 6362620
EXPECTED_FRAUD = 8213
EXPECTED_SCOPED_ROWS = 2770409

# Train / Validation / Test stratified split ratios
TRAIN_RATIO = 0.60
VAL_RATIO = 0.20
TEST_RATIO = 0.20

# txn_id: 0-based original row position in the raw CSV (int32).
# Single source of truth for unique transaction identifiers across all project modules.
COL_TXN_ID = "txn_id"
COL_SPLIT = "split"

# Balance consistency threshold
BALANCE_ERR_TOLERANCE = 0.01

# Business rule engine thresholds
RULE2_AMOUNT_PERCENTILE_THRESHOLD = 0.99
RULE3_VELOCITY_WINDOW_STEPS = 5  # RANGE BETWEEN 5 PRECEDING AND CURRENT ROW (6-hour rolling window)
RULE3_VELOCITY_THRESHOLD = 3     # txns_last_6h >= 3
RULE4_TRANSFER_CASHOUT_WINDOW_STEPS = 24  # Max 24 steps (24 hours) between transfer and cashout
RULE4_TRANSFER_CASHOUT_AMT_TOLERANCE = 0.10  # Cashout amount within 10% of transfer amount
RULE5_MULE_DEST_SENDERS_THRESHOLD = 3  # Distinct senders to destination per day >= 3
RULE6_DEST_UNCHANGED_MIN_AMOUNT = 10000.0  # Transfer amount >= 10,000
RULE7_BALANCE_ERROR_TOLERANCE = 0.01  # abs(errOrig) > 0.01 and abs(errDest) > 0.01
RULE_ALERT_THRESHOLD_1 = 1  # Alert score >= 1
RULE_ALERT_THRESHOLD_2 = 2  # Alert score >= 2

# Official Production / Dashboard Alert Definition
# Combined OR strategy ('combo_or') is selected as the official dashboard alert definition
# to guarantee maximal fraud recall (99.79%, 8,196 / 8,213 frauds detected, missing only 17)
# as an exhaustive supervisory safety net across all monitoring pipelines.
ALERT_DEFINITION = "combo_or"

# Column definitions
COL_STEP = "step"
COL_TYPE = "type"
COL_AMOUNT = "amount"
COL_NAME_ORIG = "nameOrig"
COL_OLD_BALANCE_ORG = "oldbalanceOrg"
COL_NEW_BALANCE_ORIG = "newbalanceOrig"
COL_NAME_DEST = "nameDest"
COL_OLD_BALANCE_DEST = "oldbalanceDest"
COL_NEW_BALANCE_DEST = "newbalanceDest"
COL_IS_FRAUD = "isFraud"
COL_IS_FLAGGED_FRAUD = "isFlaggedFraud"

# Balance feature column names
COL_ERR_ORIG = "errOrig"
COL_ERR_DEST = "errDest"
COL_DEST_IS_MERCHANT = "destIsMerchant"
COL_ORIG_EMPTIED = "origEmptied"
COL_DEST_BALANCE_UNCHANGED = "destBalanceUnchanged"
COL_ORIG_INCONSISTENT = "origInconsistent"
COL_DEST_INCONSISTENT = "destInconsistent"

# Time feature column names
COL_DAY = "day"
COL_HOUR = "hour"

# Duplicate flag column name
COL_IS_DUPLICATE_ROW = "isDuplicateRow"

# Outlier feature column names
COL_IS_AMOUNT_OUTLIER_IQR = "isAmountOutlierIQR"
COL_IS_TOP_1PCT_AMOUNT = "isTop1PctAmount"

# Machine Learning Feature Column Names
FEATURE_COLUMNS = [
    "logAmt",
    "isTransfer",
    "logOldOrg",
    "logNewOrig",
    "logOldDest",
    "logNewDest",
    "errOrig_signed",
    "errDest_signed",
    "origEmptied",
    "destBalanceUnchanged",
    "destIsMerchant",
    "amtToBalanceRatio",
    "hour",
]

# Forbidden columns that must NEVER be used as model features
FORBIDDEN_LEAKAGE_COLUMNS = [
    "isFraud",
    "isFlaggedFraud",
    "nameOrig",
    "nameDest",
    "txn_id",
    "step",
    "day",
]

ALL_COLUMNS = [
    COL_STEP,
    COL_TYPE,
    COL_AMOUNT,
    COL_NAME_ORIG,
    COL_OLD_BALANCE_ORG,
    COL_NEW_BALANCE_ORIG,
    COL_NAME_DEST,
    COL_OLD_BALANCE_DEST,
    COL_NEW_BALANCE_DEST,
    COL_IS_FRAUD,
    COL_IS_FLAGGED_FRAUD,
]

# Canonical column ordering for transactions_clean.parquet
CLEAN_COLUMNS = [
    COL_TXN_ID,
    COL_STEP,
    COL_DAY,
    COL_HOUR,
    COL_TYPE,
    COL_AMOUNT,
    COL_NAME_ORIG,
    COL_OLD_BALANCE_ORG,
    COL_NEW_BALANCE_ORIG,
    COL_NAME_DEST,
    COL_OLD_BALANCE_DEST,
    COL_NEW_BALANCE_DEST,
    # Derived balance features
    COL_ERR_ORIG,
    COL_ERR_DEST,
    COL_DEST_IS_MERCHANT,
    COL_ORIG_EMPTIED,
    COL_DEST_BALANCE_UNCHANGED,
    COL_ORIG_INCONSISTENT,
    COL_DEST_INCONSISTENT,
    # Derived outlier features
    COL_IS_AMOUNT_OUTLIER_IQR,
    COL_IS_TOP_1PCT_AMOUNT,
    COL_IS_DUPLICATE_ROW,
    # Targets and simulator reference flags (placed last)
    COL_IS_FRAUD,
    COL_IS_FLAGGED_FRAUD,  # For historical reference only; never used as a model feature
]
