# Financial Crime Surveillance & Fraud Detection System

[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/) [![DuckDB](https://img.shields.io/badge/DuckDB-1.0+-yellow.svg)](https://duckdb.org/) [![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-Isolation--Forest-orange.svg)](https://scikit-learn.org/) [![Power BI](https://img.shields.io/badge/Power%20BI-Validated%20Specs-yellowgreen.svg)](powerbi/) [![Tests](https://img.shields.io/badge/Tests-55%20Passed-brightgreen.svg)](tests/)

## 1. Problem Statement

Modern mobile payment platforms and financial institutions face an acute operational dilemma: detecting sophisticated, high-velocity financial crime embedded within millions of legitimate transactions while keeping false positive review overhead manageable. In the benchmark PaySim financial network (6,362,620 transactions), fraud is an extreme needle-in-a-haystack problem—accounting for exactly 8,213 confirmed events (0.129% baseline prevalence, an imbalance ratio of 773:1). Traditional heuristic monitoring systems either trigger crippling alert volumes (>1,000,000 false alarms with sub-1% precision) or miss multi-stage laundering evasion schemes entirely. This repository delivers an end-to-end, production-grade Transaction Monitoring System (TMS) combining SQL heuristic detection rules, an unsupervised Isolation Forest anomaly detection engine, and tiered hybrid fusion logic (Combined OR/AND). The pipeline processes raw transaction logs, extracts accounting and temporal anomaly features, executes calibrated surveillance triage, evaluates institutional review costs, and exports verified dimensional data models into an interactive, WCAG AA-compliant Power BI executive suite.

---

## 2. Key Results & Performance Matrix

### Baseline Surveillance Performance (Official Combined OR Strategy)

| Surveillance Metric | Value | Operational Significance |
| :--- | --: | :--- |
| **Total Enterprise Transactions** | **6,362,620** | Full 31-day simulation census (no sampling) |
| **Confirmed Fraud Cases** | **8,213** | Ground-truth fraud prevalence (0.129%) |
| **Total Flagged Alerts** | **1,085,609** | Enterprise alert rate of 17.06% |
| **True Positives (TP)** | **8,196** | Fraud events successfully intercepted |
| **False Positives (FP)** | **1,077,413** | Legitimate transactions sent to compliance triage |
| **False Negatives (FN)** | **17** | Undetected fraud events escaping monitoring |
| **Detection Recall (%)** | **99.79%** | Captures 8,196 of 8,213 total fraud events |
| **Alert Precision (%)** | **0.75%** | 1 true positive per ~132 analyst reviews |
| **False Positive Rate (FPR)** | **16.96%** | False alarm rate across all non-fraud rows |
| **F1 Score** | **0.0150** | Harmonic mean of precision and recall |
| **Total Monitored Value Flagged** | **$407,883,914,866.30** | Total transacted flow placed under review |

### Strategy Comparison Matrix: Rules vs. Machine Learning vs. Hybrid

Evaluation across the full enterprise dataset (6,362,620 transactions), sorted by F1 Score descending:

| Strategy / Architecture | Alerts Generated | Flagged Value ($) | True Positives | False Positives | Precision (%) | Recall (%) | FPR (%) | F1 Score |
| :--- | --: | --: | --: | --: | --: | --: | --: | --: |

> [!NOTE]  
> **Held-Out Test Partition Verification:** On the unobserved test split (554,082 transactions, 1,642 frauds), the calibrated Isolation Forest achieves **96.58% precision**, **51.52% recall**, and an **F1 score of 0.6720** (ROC-AUC = 0.9972, PR-AUC = 0.7565), confirming that model performance is genuine and free of data leakage.

---

## 3. Dataset Description

The project analyzes the **PaySim** mobile money financial log dataset, simulated from real financial records by the BNT (Blekinge Institute of Technology) research team. It consists of **6,362,620 transactions** spanning 744 time steps (31 simulation days) with 11 raw attributes:

- `step` (*int*): Discrete 1-hour time index from 1 to 744 (31 days).
- `type` (*string*): Transaction method: `TRANSFER`, `CASH_OUT`, `CASH_IN`, `PAYMENT`, `DEBIT`.
- `amount` (*float*): Transacted value in local currency units (ranging from $0.00 to $92,445,516.64).
- `nameOrig` (*string*): Originator account identifier (`C...` customer accounts).
- `oldbalanceOrg` (*float*): Sender initial balance before transaction.
- `newbalanceOrig` (*float*): Sender final balance after transaction.
- `nameDest` (*string*): Recipient identifier (`C...` customer or `M...` merchant accounts).
- `oldbalanceDest` (*float*): Recipient initial balance prior to receiving funds.
- `newbalanceDest` (*float*): Recipient final balance after receiving funds.
- `isFraud` (*int*): Binary ground-truth fraud indicator (1 = confirmed fraud, 0 = legitimate).
- `isFlaggedFraud` (*int*): Simulation rule heuristic (flags attempts over $200,000; only 16 rows flagged in entire dataset).

### Critical Empirical Finding: Strict Channel Isolation
Rigorous data profiling reveals that **100.00% of all fraud (8,213 cases, $12.06B) is confined strictly to two channels**:
- **`TRANSFER`:** 532,909 total transactions, **4,097 frauds** (fraud rate: **0.769%**).
- **`CASH_OUT`:** 2,237,500 total transactions, **4,116 frauds** (fraud rate: **0.184%**).
- **`CASH_IN`, `PAYMENT`, `DEBIT`:** 3,592,211 total transactions, **exactly 0 frauds** (fraud rate: **0.000%**).

Consequently, surveillance models and rules are scoped strictly to `TRANSFER` and `CASH_OUT` (2,770,409 transactions, 43.54% of volume), eliminating 3.59M harmless transactions from algorithmic processing without missing a single fraud event.

---

## 4. End-to-End System Architecture

```text
+----------------------------------------------------------------------------------------------------+
|                                FINANCIAL CRIME SURVEILLANCE PIPELINE                               |
+----------------------------------------------------------------------------------------------------+
  [Raw PaySim CSV]                                              (6,362,620 rows, 11 raw fields)
         |
         v
  [Phase 1: Ingestion & Feature Engineering]                    (src/run_phase1.py)
         |--> transactions_clean.parquet                        (24 engineered columns, 0 nulls)
         |--> split_assignment.parquet                          (Stratified 60/20/20 on TRANSFER/CASH_OUT)
         |--> 8 EDA Visualizations                              (reports/figures/01-08)
         |
         +----------------------------------+
         |                                  |
         v                                  v
  [Phase 2: SQL Rule Engine]         [Phase 3: Unsupervised Machine Learning]
  (DuckDB + sql/01_load, 02_rules)   (Isolation Forest: 100 trees, contamination 0.003)
         |                                  |
         |--> 7 Heuristic Rules             |--> 36-Config Hyperparameter Sweep
         |--> alert_score (0 to 5)          |--> Validation Threshold Tuning (PR-AUC 0.762)
         |--> rule_flags.parquet            |--> ml_scores.parquet (anomaly_score_pct)
         |                                  |
         +-----------------+----------------+
                           |
                           v
  [Phase 4: Fusion & Strategic Cost Optimization]               (src/run_phase4.py)
         |--> master_alerts.parquet                             (6.36M rows: combo_score, risk_band, outcome)
         |--> Strategic Comparison (Combined OR vs AND)         (reports/14_approach_comparison.md)
         |--> Financial Cost Tradeoff Model ($25/alert)         (reports/15_cost_analysis.md)
         |
         v
  [Power BI Semantic Warehouse Export]                          (data/outputs/powerbi/)
         |--> fact_transactions.csv                             (18,213 priority rows: all frauds + sampled legit)
         |--> 6 Dimension Tables                                (dim_type, dim_day, dim_hour, dim_source, etc.)
         |--> 7 Aggregate Reconciliations                       (6.36M transaction census preserved)
         |--> 4 Pre-computed Metrics Tables                     (confusion matrix, rule & approach metrics)
         |
         v
  [Power BI Executive Intelligence Dashboard]                   (powerbi/05_page1 - 08_interactions)
         |--> Page 1: Executive Overview                        (KPI cards, fraud rate bar, dual line, donut)
         |--> Page 2: Rules vs ML Diagnostics                   (F1 comparison, rule bars, confusion matrix)
         |--> Page 3: Case Investigation & Drill-Through        (Top 20 ledger, log-scale scatter, account drill)
+----------------------------------------------------------------------------------------------------+
```

---

## 5. Repository Structure

```text
.├── README.md                          # Master documentation (programmatically generated)
├── config.py                          # Global single source of truth (paths, schemas, thresholds)
├── requirements.txt                   # Frozen python dependencies
├── data/                              # Data directories (gitignored)
│   ├── raw/                           # Original PaySim CSV location
│   ├── processed/                     # Parquet files (transactions_clean, splits, duckdb)
│   └── outputs/                       # Master alerts and Power BI exported CSVs
│       └── powerbi/                   # 18 CSV files (facts, dimensions, aggregates, metrics)
├── models/                            # Serialized model artifacts
│   ├── isolation_forest.joblib        # Trained Isolation Forest model
│   ├── model_metadata.json            # Model training metadata and parameters
│   ├── best_config.json               # Winning hyperparameter configuration
│   └── thresholds.json                # Calibrated decision thresholds (best_f1, high_recall)
├── powerbi/                           # Power BI report specifications & theme
│   ├── data_dictionary.md             # Complete data dictionary for all 18 exported CSVs
│   ├── 01_import_guide.md             # Click-by-click CSV import and Power Query guide
│   ├── 02_data_model.md               # Star-schema architecture & relationship spec
│   ├── 03_measures.dax                # 26 audited DAX measures with display folders
│   ├── 04_kpi_cards.md                # Page 1 KPI row geometry and interaction decoupling
│   ├── 05_page1_overview.md           # Page 1 (Executive Overview) complete layout spec
│   ├── 06_page2_detection.md          # Page 2 (Rules vs ML) complete layout spec
│   ├── 07_page3_investigation.md      # Page 3 (Investigation) & Account Detail sub-page
│   ├── 08_interactions.md             # Slicer sync, edit interactions, bookmarks, tooltips
│   ├── 09_design.md                   # Design system, palette, typography, WCAG AA audit
│   ├── fraud_theme.json               # Valid Power BI custom theme file (Fraud Monitor)
│   └── check_layout.py                # Automated collision & bounds verification script
├── reports/                           # Analytical audit reports & figures
│   ├── figures/                       # Publication charts (01-08 EDA figures)
│   ├── 08_rule_evaluation.csv         # Rule precision, recall, and false positive metrics
│   ├── 11_ml_test_results.csv         # Out-of-sample machine learning test evaluation
│   ├── 14_approach_comparison.csv     # Multi-strategy performance benchmark
│   ├── 15_cost_analysis.csv           # Financial review cost model simulation
│   └── 16_final_metrics.json          # Master consolidated performance metrics
├── sql/                               # High-performance DuckDB SQL engines
│   ├── 00_verify.sql                  # Environment and database verification
│   ├── 01_load.sql                    # Parquet ingestion into DuckDB tables
│   └── 02_rules.sql                   # 7 Transaction monitoring heuristic SQL rules
├── src/                               # Python execution modules
│   ├── run_phase1.py                  # Phase 1: Ingestion, cleaning, feature engineering
│   ├── run_phase2.py                  # Phase 2: DuckDB SQL rule execution & reporting
│   ├── run_phase3.py                  # Phase 3: ML training, hyperparameter sweep, tuning
│   ├── run_phase4.py                  # Phase 4: Strategy fusion, cost model, Power BI export
│   ├── build_readme.py                # Script to regenerate README.md from report data
│   └── ...                            # Component modules (evaluation, features, etc.)
└── tests/                             # Comprehensive test suite (55 automated tests)
    ├── test_phase1.py                 # Tests for data integrity, splits, and profiling
    ├── test_phase2.py                 # Tests for SQL rules and precision calculations
    ├── test_phase3.py                 # Tests for ML model serialization and test scores
    └── test_phase4.py                 # Tests for alerts, exports, Power BI docs & theme
```

---

## 6. How to Run from Scratch

### Step 1: Environment Setup
Clone the repository, create a clean virtual environment, and install pinned dependencies:
```bash
git clone https://github.com/divyansh/fraud-detection-transaction-monitoring.git
cd fraud-detection-transaction-monitoring
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Step 2: Acquire Dataset
Download the PaySim dataset (`PS_20174392719_1491204439457_log.csv`) from [Kaggle](https://www.kaggle.com/datasets/ealaxi/paysim1) and place it into the raw data directory:
```bash
mkdir -p data/raw
cp /path/to/PS_20174392719_1491204439457_log.csv data/raw/
```

### Step 3: Execute End-to-End Pipeline in Order
Execute the four phase orchestration scripts sequentially:
```bash
# Phase 1: Ingestion, balance/outlier engineering, 60/20/20 stratified split, EDA charts (~45s)
python src/run_phase1.py

# Phase 2: Ingest into DuckDB, execute 7 heuristic rules, generate rule reports (~15s)
python src/run_phase2.py

# Phase 3: Train Isolation Forest, sweep 36 configs, calibrate validation threshold (~35s)
python src/run_phase3.py

# Phase 4: Strategy combination, cost model, export 18 Power BI CSVs (~20s)
python src/run_phase4.py
```

### Step 4: Run Verification Test Suite
Verify pipeline integrity and layout compliance across all 55 automated tests:
```bash
pytest tests/ -v

# Verify Power BI canvas bounding boxes and zero collisions across all 3 pages
python powerbi/check_layout.py
```
*Total end-to-end execution runtime: ~2 minutes on a modern multi-core workstation.*

---

## 7. Methodology

### Data Cleaning & Outlier Retention Policy
A critical architectural decision was **retaining 100% of statistical outliers**. Transaction amounts exhibit extreme positive skewness (+30.99). Standard machine learning preprocessing often applies IQR trimming or $Z$-score filtering. In fraud detection, this is disastrous: **33.00% of all confirmed fraud cases (2,710 out of 8,213) exceed standard IQR outlier thresholds**. Deleting outliers would literally delete one-third of the criminal activity we are tasked with finding. Consequently, zero transactions were discarded; instead, outlier bounds were engineered into categorical amount magnitude bands (`<1K`, `1K-10K`, `10K-100K`, `100K-1M`, `>1M`) and log-transformed inputs.

### The 7 Heuristic SQL Monitoring Rules
Seven expert rules were implemented in DuckDB SQL (`sql/02_rules.sql`) and evaluated against the full dataset:

| Rule Identifier | Plain-English Logic | Alerts | True Positives | False Positives | Precision (%) | Recall (%) |
| :--- | :--- | --: | --: | --: | --: | --: |
| `Rule 1: Account Emptied` | Sender balance fully drained to 0 (oldbalanceOrg == amount) | 8,008 | 8,008 | 0 | 100.00% | 97.50% |
| `Rule 2: Large Amount Outlier` | Amount > 99th percentile of payment type ($353K TRANSFER, $447K CASH_OUT) | 24,818 | 1,806 | 23,012 | 7.28% | 21.99% |
| `Rule 3: Originator Velocity (6h)` | >3 transactions within 6-hour rolling window by same originator | 0 | 0 | 0 | 0.00% | 0.00% |
| `Rule 4: Transfer Then Cash-Out (24h)` | TRANSFER followed by matching CASH_OUT within 24h | 0 | 0 | 0 | 0.00% | 0.00% |
| `Rule 5: Mule Destination (Day)` | Destination receives inflows from >=2 distinct originators in a day | 748,575 | 647 | 747,928 | 0.09% | 7.88% |
| `Rule 6: Destination Balance Unchanged` | TRANSFER where recipient balance remains unchanged at zero | 4,042 | 3,940 | 102 | 97.48% | 47.97% |
| `Rule 7: Balance Inconsistency` | Mathematical balance mismatch (|diff| > 0.01) at origin or destination | 570,732 | 26 | 570,706 | 0.00% | 0.32% |
| `Composite Alert: Score >= 1` | Transaction triggers at least 1 heuristic rule (Rule Alert) | 1,085,554 | 8,190 | 1,077,364 | 0.75% | 99.72% |
| `Composite Alert: Score >= 2` | Transaction triggers 2 or more distinct heuristic rules | 267,021 | 5,908 | 261,113 | 2.21% | 71.93% |

#### Heuristic Rule Analysis:
1. **Rule 1 (Account Emptied):** The single strongest heuristic indicator. Drains entire balance (`oldbalanceOrg > 0 AND newbalanceOrig == 0 AND amount == oldbalanceOrg`). Captures **8,008 fraud cases** with **100.00% precision** (0 false alarms) and **97.50% recall**.
2. **Rule 2 (Large Amount Outlier):** Flags transfers exceeding the 99th percentile of payment type ($353K for TRANSFER, $447K for CASH_OUT). Captures 1,806 frauds at 7.28% precision.
3. **Rules 3 & 4 (Velocity & Rapid Cash-Out):** Produced 0 alerts due to a known PaySim synthetic limitation: customer originator accounts transact exactly once in the simulation.
4. **Rule 5 (Mule Destination):** Flags destination accounts receiving multiple inflows within 24 hours. Triggers 748,575 alerts catching 647 frauds (broad net, 0.09% precision).
5. **Rule 6 (Destination Balance Unchanged):** Flags transfers where recipient balance remains unchanged despite large incoming funds. Captures 3,940 frauds at **97.48% precision**.
6. **Rule 7 (Balance Inconsistency):** Flags mathematical balance discrepancies. Densely triggered by simulator zero-capping artifacts.

### Machine Learning: Unsupervised Isolation Forest
To intercept zero-day fraud patterns missed by static heuristic rules, an **Isolation Forest** was trained on the 60% training partition using clean accounting and temporal features (`amount`, `oldbalanceOrg`, `newbalanceOrig`, `oldbalanceDest`, `newbalanceDest`, `hour`, `errOrig`, `errDest`, `origEmptied`, `destUnchanged`). Key modeling safeguards:
- **Unsupervised Training:** Trained without fraud labels to emulate real-world surveillance where new fraud types have no historical tags.
- **Rigorous 36-Config Grid Sweep:** Swept `n_estimators` (50, 100, 200), `max_samples` (256, 512, 1024, auto), `contamination` (0.001, 0.003, 0.005) optimizing validation PR-AUC.
- **Validation-Only Threshold Calibration:** Calibrated operating points strictly on the 20% validation split (optimal F1 threshold = `0.704009`).
- **Strict Held-Out Test Evaluation:** Evaluated exactly once on the held-out 20% test partition, securing **96.58% precision** and **51.52% recall**.

---

## 8. Power BI Executive Dashboard Suite

The repository includes complete, build-ready architectural specifications for a 3-page executive reporting suite in Power BI:
- **[Page 1: Executive Overview](powerbi/05_page1_overview.md):** 6 Top-line KPI Cards (Transactions, Alerts, Flagged $, Fraud Rate, Precision, Recall), Takeaway Intelligence Brief, Fraud Rate % Bar Chart, 31-day Dual-Axis Surveillance Trend, Diurnal Hourly Column Chart, and Alert Attribution Donut.
- **[Page 2: Rules vs ML Diagnostics](powerbi/06_page2_detection.md):** Comparative Performance Bar (Precision, Recall, F1), 7-Rule Evaluation Matrix with Data Bars, Enterprise Confusion Matrix with heat coloring, and Daily Alert Volume Stacked Column.
- **[Page 3: Case Investigation & Drill-Through](powerbi/07_page3_investigation.md):** Top 20 Priority Ledger ranked by `combo_score`, Risk-Band volume distribution, Log-Scale Amount vs. Anomaly Score Scatter Plot, and right-click drill-through to a hidden **Account Detail** investigation audit page.
- **[DAX Measure Catalog](powerbi/03_measures.dax):** 26 production-grade DAX measures with error handling and dynamic conditional formatting.
- **[Design System & Theme](powerbi/09_design.md):** Custom `powerbi/fraud_theme.json` enforcing dark-navy neutrality, 16 px gutters, and audited 100% WCAG AA contrast compliance.

### Dashboard Visual Gallery (Screenshots)
```markdown
<!-- PLACEHOLDER BLOCK: Add screenshots here after importing into Power BI Desktop -->
![Executive Overview](docs/dashboard_page1.png)
*Figure 1: Page 1 — Executive Overview (Canvas: 1280x720)*

![Rules vs ML](docs/dashboard_page2.png)
*Figure 2: Page 2 — Rules vs ML Strategy Diagnostics*

![Case Investigation](docs/dashboard_page3.png)
*Figure 3: Page 3 — Tactical Case Investigation Ledger & Scatter Plot*
```
*Note: Follow [powerbi/01_import_guide.md](powerbi/01_import_guide.md) to import CSVs into Power BI Desktop, then save screenshots to `docs/`.*

---

## 9. Key Empirical Findings & Strategic Insights

1. **Absolute Channel Concentration:** Exactly 8,213 fraud events occurred across 31 days, and **100.00% of them were restricted to TRANSFER (4,097 cases) and CASH_OUT (4,116 cases)**. Not a single fraud event occurred in CASH_IN, PAYMENT, or DEBIT (3,592,211 transactions), proving that channel gating should be an institution's first line of defense.
2. **The Account Drainage Anomaly:** Draining an originator balance to exactly zero (`rule_emptied`) is present in **97.50% of all fraud (8,008 cases)**, while occurring in **zero legitimate transactions**, delivering a perfect 100.00% precision.
3. **Combined AND Maximizes Operational Efficiency:** Combining rules and ML via mathematical intersection (`combo_and`) yields **98.65% precision** (4,167 TPs against only 57 FPs out of 4,224 alerts), cutting analyst alert backlogs by **46.2%** relative to ML alone while capturing **$6.45B** in fraud.
4. **Combined OR Maximizes Regulatory Recall:** Combining rules and ML via mathematical union (`combo_or`) achieves **99.79% recall** (8,196 of 8,213 frauds caught, missing only 17), successfully intercepting **6 fraud cases** that heuristic rules missed entirely (+55 alerts), securing **$407.88B** in monitored flow.
5. **Simulator Baseline Failure:** The internal simulator baseline rule (`isFlaggedFraud`) is operationally unviable: it caught only **16 fraud cases (0.19% recall)**, allowing **99.81% (8,197 frauds)** to pass undetected.
6. **Unsupervised Anomaly Generalization:** The calibrated Isolation Forest generalizes cleanly out-of-sample on the held-out test split, securing **96.58% precision** and **0.6720 F1**, proving that unsupervised tree isolation identifies genuine fraudulent topology.
7. **Destructive Risk of Outlier Trimming:** Standard outlier trimming would have discarded **33.00% of all fraud cases (2,710 cases)**, validating our non-destructive feature engineering methodology.

---

## 10. Limitations & Honest Caveats

1. **Synthetic Data Artifacts:** PaySim is generated by a multi-agent simulator. Customer accounts (`C...`) appear only once as originators; as a result, real-world temporal velocity rules (e.g. Rule 3: >3 transfers in 6 hours) trigger 0 times in this dataset.
2. **Unnaturally Clean Balance Drainage:** Fraudsters in PaySim systematically drain the exact available balance to zero (`newbalanceOrig == 0`). In production banking, sophisticated adversaries leave small residual balances or execute micro-probes to bypass static balance equality heuristics.
3. **Missing Contextual Metadata:** The dataset lacks customer tenure, KYC identity flags, device fingerprints, IP geolocations, and counterparty merchant classifications that are standard in tier-1 financial crime operations.
4. **Isolation Forest Scalability & Density Bias:** While Isolation Forest excels on tabular extremes, it can struggle with dense local fraud clusters and carries higher inference latency than optimized gradient-boosted decision trees.
5. **Simulated Financial Cost Parameters:** The financial optimization model assumes a constant $25.00 analyst review cost and a 1.5% fraud recovery rate. While realistic industry benchmarks, actual institutional costs vary significantly by jurisdiction and compliance tier.

---

## 11. Future Work & Engineering Roadmap

- **Supervised Gradient Boosting Benchmark:** Train and benchmark LightGBM and CatBoost with focal loss and SMOTE/undersampling against the unsupervised Isolation Forest baseline.
- **Graph Neural Networks (GNNs):** Construct bipartite transaction graphs (NetworkX / PyTorch Geometric) to detect circular laundering loops, mule syndicates, and synthetic identity rings.
- **Real-Time Streaming Architecture:** Deploy the feature engineering and scoring pipeline into Apache Kafka and Apache Flink for sub-50ms transaction authorization decisions.
- **Cloud Microservice Deployment:** Package the inference engine into a containerized FastAPI / Docker service backed by PostgreSQL / DuckDB for production alert dispatch.

---

## License & Acknowledgements
This project is open-source under the MIT License. Transaction logs courtesy of the PaySim synthetic mobile money benchmark.