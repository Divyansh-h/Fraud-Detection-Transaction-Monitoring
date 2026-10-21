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
SPLIT_ASSIGNMENT_PARQUET = PROCESSED_DATA_DIR / "split_assignment.parquet"

FIG_HIST_AMOUNT = FIGURES_DIR / "01_amount_distribution_by_fraud.png"
FIG_BOXPLOT_AMOUNT = FIGURES_DIR / "02_amount_boxplot_by_type.png"
FIG_BAR_FRAUD_RATE = FIGURES_DIR / "03_fraud_rate_by_type.png"
FIG_TX_PER_DAY = FIGURES_DIR / "04_transactions_per_day.png"
FIG_FRAUD_PER_DAY = FIGURES_DIR / "05_fraud_count_per_day.png"
FIG_FRAUD_BY_HOUR = FIGURES_DIR / "06_fraud_by_hour.png"
FIG_ORIG_EMPTIED = FIGURES_DIR / "07_orig_emptied_comparison.png"
FIG_AVG_AMOUNT_BY_TYPE = FIGURES_DIR / "08_avg_amount_by_type.png"

# Core constants
RANDOM_SEED = 42
FRAUD_TYPES = ["TRANSFER", "CASH_OUT"]
ALL_TYPES = ["CASH_IN", "CASH_OUT", "DEBIT", "PAYMENT", "TRANSFER"]

EXPECTED_ROWS = 6362620
EXPECTED_FRAUD = 8213

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
