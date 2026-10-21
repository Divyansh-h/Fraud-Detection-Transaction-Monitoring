# Power BI Data Dictionary & Schema Documentation

**Document ID:** `powerbi/data_dictionary.md`  
**Source Directory:** `data/outputs/powerbi`  
**Generated Tables:** 18 CSV files  
**Integrity Standard:** Row counts, column names, and data types are programmatically audited directly from data files.

---

## Table of Contents

- [agg_by_amount_band_type.csv](#agg-by-amount-band-typecsv) — *Aggregate Summary Table*
- [agg_by_day.csv](#agg-by-daycsv) — *Aggregate Summary Table*
- [agg_by_day_type.csv](#agg-by-day-typecsv) — *Aggregate Summary Table*
- [agg_by_hour.csv](#agg-by-hourcsv) — *Aggregate Summary Table*
- [agg_by_risk_band.csv](#agg-by-risk-bandcsv) — *Aggregate Summary Table*
- [agg_by_source.csv](#agg-by-sourcecsv) — *Aggregate Summary Table*
- [agg_by_type.csv](#agg-by-typecsv) — *Aggregate Summary Table*
- [confusion_matrix.csv](#confusion-matrixcsv) — *Performance Metrics Table*
- [dim_alert_source.csv](#dim-alert-sourcecsv) — *Dimension Table*
- [dim_amount_band.csv](#dim-amount-bandcsv) — *Dimension Table*
- [dim_day.csv](#dim-daycsv) — *Dimension Table*
- [dim_hour.csv](#dim-hourcsv) — *Dimension Table*
- [dim_risk_band.csv](#dim-risk-bandcsv) — *Dimension Table*
- [dim_type.csv](#dim-typecsv) — *Dimension Table*
- [fact_transactions.csv](#fact-transactionscsv) — *Fact Table (Sampled)*
- [metrics_approach.csv](#metrics-approachcsv) — *Performance Metrics Table*
- [metrics_overall.csv](#metrics-overallcsv) — *Performance Metrics Table*
- [metrics_rules.csv](#metrics-rulescsv) — *Performance Metrics Table*

---

## `agg_by_amount_band_type.csv`

**Category:** Aggregate Summary Table  
**Row Count:** **23** rows (computed from file)  
**File Size:** 678 bytes  
**Purpose:** Cross-tabulation matrix of transaction amount magnitude intervals vs. payment types.

| Column Name | Inferred Data Type | Sample Value | Description & Business Meaning |
| :--- | :---: | :---: | :--- |
| `amount_band` | `Text / String` | `100K-1M` | Monetary magnitude interval label (<1K, 1K-10K, 10K-100K, 100K-1M, >1M). |
| `type` | `Text / String` | `CASH_IN` | Transaction payment method. |
| `total_txns` | `Integer` | `901759` | Total transaction volume in this amount band and type. |
| `fraud_count` | `Integer` | `0` | Confirmed fraud count in this amount band and type. |
| `alert_count` | `Integer` | `0` | Alerts triggered in this amount band and type. |

---

## `agg_by_day.csv`

**Category:** Aggregate Summary Table  
**Row Count:** **31** rows (computed from file)  
**File Size:** 1,408 bytes  
**Purpose:** Full-universe daily aggregated temporal trend metrics across the 31-day monitoring window.

| Column Name | Inferred Data Type | Sample Value | Description & Business Meaning |
| :--- | :---: | :---: | :--- |
| `day` | `Integer` | `1` | Simulation day number (1 to 31). |
| `total_txns` | `Integer` | `574255` | Total transaction volume on this day. |
| `fraud_count` | `Integer` | `271` | Confirmed fraud count on this day. |
| `alert_count` | `Integer` | `232177` | Alerts triggered on this day. |
| `tp` | `Integer` | `270` | True positive detections on this day. |
| `fp` | `Integer` | `231907` | False positive alarms on this day. |
| `fn` | `Integer` | `1` | Missed fraud cases on this day. |
| `flagged_value` | `Decimal / Float` | `65682848402.44` | Total currency amount of alerted transactions on this day ($). |

---

## `agg_by_day_type.csv`

**Category:** Aggregate Summary Table  
**Row Count:** **152** rows (computed from file)  
**File Size:** 4,635 bytes  
**Purpose:** Granular cross-tabulation of daily transaction volume, fraud count, and alerts across all payment types.

| Column Name | Inferred Data Type | Sample Value | Description & Business Meaning |
| :--- | :---: | :---: | :--- |
| `day` | `Integer` | `1` | Simulation day number (1 to 31). |
| `type` | `Text / String` | `CASH_IN` | Transaction payment method. |
| `total_txns` | `Integer` | `124026` | Total transaction volume for this day and type. |
| `fraud_count` | `Integer` | `0` | Confirmed fraud count for this day and type. |
| `alert_count` | `Integer` | `0` | Alerts triggered for this day and type. |
| `flagged_value` | `Decimal / Float` | `0.0` | Total currency amount of alerted transactions ($). |

---

## `agg_by_hour.csv`

**Category:** Aggregate Summary Table  
**Row Count:** **24** rows (computed from file)  
**File Size:** 1,123 bytes  
**Purpose:** Full-universe hourly aggregated diurnal fraud and surveillance profile (hours 0 to 23).

| Column Name | Inferred Data Type | Sample Value | Description & Business Meaning |
| :--- | :---: | :---: | :--- |
| `hour` | `Integer` | `0` | Diurnal hour of the day (0 to 23). |
| `total_txns` | `Integer` | `27111` | Total transaction volume at this hour. |
| `fraud_count` | `Integer` | `358` | Confirmed fraud count at this hour. |
| `alert_count` | `Integer` | `2628` | Alerts triggered at this hour. |
| `tp` | `Integer` | `358` | True positive detections at this hour. |
| `fp` | `Integer` | `2270` | False positive alarms at this hour. |
| `fn` | `Integer` | `0` | Missed fraud cases at this hour. |
| `flagged_value` | `Decimal / Float` | `1209224284.48` | Total currency amount of alerted transactions at this hour ($). |

---

## `agg_by_risk_band.csv`

**Category:** Aggregate Summary Table  
**Row Count:** **4** rows (computed from file)  
**File Size:** 153 bytes  
**Purpose:** Pre-aggregated operational distribution across the four tiered risk bands (Critical, High, Medium, Low).

| Column Name | Inferred Data Type | Sample Value | Description & Business Meaning |
| :--- | :---: | :---: | :--- |
| `risk_band` | `Text / String` | `Critical` | Operational risk band name ('Critical', 'High', 'Medium', 'Low'). |
| `rows` | `Integer` | `0` | Total transactions classified into this risk band. |
| `fraud_count` | `Integer` | `0` | Confirmed fraudulent transactions in this risk band. |
| `flagged_value` | `Decimal / Float` | `0.0` | Total currency amount flagged in this risk band ($). |

---

## `agg_by_source.csv`

**Category:** Aggregate Summary Table  
**Row Count:** **4** rows (computed from file)  
**File Size:** 225 bytes  
**Purpose:** Alert attribution breakdown comparing Consensus ('Both'), Rules only, ML only, and Unflagged ('None').

| Column Name | Inferred Data Type | Sample Value | Description & Business Meaning |
| :--- | :---: | :---: | :--- |
| `alert_source` | `Text / String` | `None` | Attribution category ('Both', 'Rule only', 'ML only', 'None'). |
| `alert_count` | `Integer` | `5277011` | Total transaction count falling into this attribution category. |
| `fraud_caught` | `Integer` | `17` | Confirmed fraud events intercepted. |
| `fp` | `Integer` | `0` | False positive alarms generated. |
| `flagged_value` | `Decimal / Float` | `0.0` | Total currency amount flagged in this attribution source ($). |
| `precision_pct` | `Decimal / Float` | `0.0003` | Detection precision / hit rate within this attribution source (%). |

---

## `agg_by_type.csv`

**Category:** Aggregate Summary Table  
**Row Count:** **5** rows (computed from file)  
**File Size:** 478 bytes  
**Purpose:** Full-universe (6.36M) pre-aggregated volume, confusion matrix breakdown, and alert rates by transaction type.

| Column Name | Inferred Data Type | Sample Value | Description & Business Meaning |
| :--- | :---: | :---: | :--- |
| `type` | `Text / String` | `CASH_OUT` | Transaction payment method name. |
| `total_txns` | `Integer` | `2237500` | Total enterprise transaction volume of this type. |
| `total_amount` | `Decimal / Float` | `394412995224.49` | Total transactional currency volume ($). |
| `fraud_count` | `Integer` | `4116` | Total confirmed fraudulent transactions. |
| `alert_count` | `Integer` | `865375` | Total alerts triggered under official Combined OR definition. |
| `tp` | `Integer` | `4100` | True positive fraud detections. |
| `fp` | `Integer` | `861275` | False positive alarms (legitimate transactions flagged). |
| `fn` | `Integer` | `16` | False negatives (missed fraudulent transactions). |
| `tn` | `Integer` | `1372109` | True negatives (correctly unalerted legitimate transactions). |
| `flagged_value` | `Decimal / Float` | `171525973861.11` | Total currency amount of flagged transactions ($). |
| `fraud_rate_pct` | `Decimal / Float` | `0.184` | Prevalence of fraud within this payment type (%). |
| `alert_rate_pct` | `Decimal / Float` | `38.676` | Proportion of transactions flagged for review (%). |

---

## `confusion_matrix.csv`

**Category:** Performance Metrics Table  
**Row Count:** **4** rows (computed from file)  
**File Size:** 210 bytes  
**Purpose:** Four-row classification quadrant table formatted for direct ingestion by Power BI matrix visuals.

| Column Name | Inferred Data Type | Sample Value | Description & Business Meaning |
| :--- | :---: | :---: | :--- |
| `outcome` | `Text / String` | `True Positive` | Classification quadrant name ('True Positive', 'False Positive', 'False Negative', 'True Negative'). |
| `actual` | `Text / String` | `Fraud` | Ground truth condition ('Fraud' vs. 'Legit'). |
| `predicted` | `Text / String` | `Alert` | System detection action ('Alert' vs. 'No alert'). |
| `count` | `Integer` | `8196` | Total transaction count in this quadrant. |
| `pct_of_total` | `Decimal / Float` | `0.1288` | Percentage share of total enterprise transaction volume (%). |

---

## `dim_alert_source.csv`

**Category:** Dimension Table  
**Row Count:** **4** rows (computed from file)  
**File Size:** 67 bytes  
**Purpose:** Dimension table defining detection attribution sources (Both, Rule only, ML only, None).

| Column Name | Inferred Data Type | Sample Value | Description & Business Meaning |
| :--- | :---: | :---: | :--- |
| `alert_source` | `Text / String` | `Both` | Detection attribution name (Primary Key). |
| `alert_source_sort` | `Integer` | `1` | Priority sort order index (1 to 4). |

---

## `dim_amount_band.csv`

**Category:** Dimension Table  
**Row Count:** **5** rows (computed from file)  
**File Size:** 71 bytes  
**Purpose:** Dimension table defining transactional currency magnitude intervals.

| Column Name | Inferred Data Type | Sample Value | Description & Business Meaning |
| :--- | :---: | :---: | :--- |
| `amount_band` | `Text / String` | `<1K` | Monetary magnitude interval label (Primary Key). |
| `amount_band_sort` | `Integer` | `1` | Magnitude sort order index (1 to 5). |

---

## `dim_day.csv`

**Category:** Dimension Table  
**Row Count:** **31** rows (computed from file)  
**File Size:** 469 bytes  
**Purpose:** Calendar dimension table for simulation days (Day 01 to Day 31) with day-of-week and week index hierarchy.

| Column Name | Inferred Data Type | Sample Value | Description & Business Meaning |
| :--- | :---: | :---: | :--- |
| `day` | `Integer` | `1` | Simulation day number from 1 to 31 (Primary Key). |
| `day_label` | `Text / String` | `Day 01` | Zero-padded day display string ('Day 01' to 'Day 31'). |
| `day_of_week_index` | `Integer` | `1` | Relative day of week index (1 to 7, where index = ((day-1) % 7) + 1). |
| `week_number` | `Integer` | `1` | Relative calendar week number (1 to 5, where week = ((day-1) // 7) + 1). |

---

## `dim_hour.csv`

**Category:** Dimension Table  
**Row Count:** **24** rows (computed from file)  
**File Size:** 424 bytes  
**Purpose:** Diurnal hourly dimension table mapping transaction hours to operational investigation shifts.

| Column Name | Inferred Data Type | Sample Value | Description & Business Meaning |
| :--- | :---: | :---: | :--- |
| `hour` | `Integer` | `0` | Transaction hour from 0 to 23 (Primary Key). |
| `hour_label` | `Text / String` | `00:00` | Clock format display label ('00:00' to '23:00'). |
| `time_band` | `Text / String` | `Night` | Diurnal shift interval: 'Night' (0-5), 'Morning' (6-11), 'Afternoon' (12-17), 'Evening' (18-23). |

---

## `dim_risk_band.csv`

**Category:** Dimension Table  
**Row Count:** **4** rows (computed from file)  
**File Size:** 58 bytes  
**Purpose:** Dimension table defining operational triaging risk bands (Critical, High, Medium, Low).

| Column Name | Inferred Data Type | Sample Value | Description & Business Meaning |
| :--- | :---: | :---: | :--- |
| `risk_band` | `Text / String` | `Critical` | Risk band name (Primary Key). |
| `risk_band_sort` | `Integer` | `1` | Priority sort order index (1 to 4). |

---

## `dim_type.csv`

**Category:** Dimension Table  
**Row Count:** **5** rows (computed from file)  
**File Size:** 154 bytes  
**Purpose:** Dimension lookup table mapping transaction payment types to risk categories and custom visual sort orders.

| Column Name | Inferred Data Type | Sample Value | Description & Business Meaning |
| :--- | :---: | :---: | :--- |
| `type` | `Text / String` | `TRANSFER` | Transaction payment method name (Primary Key). |
| `type_group` | `Text / String` | `Fraud-prone` | Regulatory risk grouping: 'Fraud-prone' (TRANSFER, CASH_OUT) vs. 'No fraud observed' (others). |
| `type_sort` | `Integer` | `1` | Visual sort order index (1 to 5). |

---

## `fact_transactions.csv`

**Category:** Fact Table (Sampled)  
**Row Count:** **1,135,626** rows (computed from file)  
**File Size:** 153.66 MB  
**Purpose:** Primary transactional fact table for Power BI Desktop. Contains 100% of all alerts and frauds (1,085,626 rows, capturing all 8,213 frauds including 17 false negatives) plus a 50,000-row stratified sample of legitimate unalerted transactions (seed 42). High-cardinality raw balances are excluded to keep file size under 160MB for fast interactive rendering. NOTE: Enterprise-wide aggregate KPIs must be sourced from aggregate tables, not COUNTROWS(fact_transactions).

| Column Name | Inferred Data Type | Sample Value | Description & Business Meaning |
| :--- | :---: | :---: | :--- |
| `txn_id` | `Integer` | `1` | Unique zero-based transaction identifier (Primary Key in full clean dataset). |
| `step` | `Integer` | `1` | Simulation time step in hours from start of simulation (1 to 743). |
| `day` | `Integer` | `1` | Relative simulation day number (1 to 31, where day = (step-1)//24 + 1). |
| `hour` | `Integer` | `0` | Diurnal transaction hour (0 to 23, where hour = (step-1) % 24). |
| `type` | `Text / String` | `PAYMENT` | Transaction payment method (TRANSFER, CASH_OUT, CASH_IN, PAYMENT, DEBIT). |
| `amount` | `Decimal / Float` | `1864.28` | Transaction amount in monetary currency units, rounded to 2 decimals. |
| `amount_band` | `Text / String` | `1K-10K` | Discretized amount magnitude interval (<1K, 1K-10K, 10K-100K, 100K-1M, >1M). |
| `nameOrig` | `Text / String` | `C1666544295` | Unique account identifier of the customer initiating the transaction. |
| `nameDest` | `Text / String` | `M2044282225` | Unique account identifier of the recipient / merchant receiving funds. |
| `rule_emptied` | `Integer` | `0` | Heuristic Rule 1 flag: 1 if originator account was drained to 0. |
| `rule_large_amount` | `Integer` | `0` | Heuristic Rule 2 flag: 1 if amount exceeds 99th percentile ($1.62M for TRANSFER, $448K for CASH_OUT). |
| `rule_velocity` | `Integer` | `0` | Heuristic Rule 3 flag: 1 if originator executed >=3 transactions in rolling 6h. |
| `rule_transfer_then_cashout` | `Integer` | `0` | Heuristic Rule 4 flag: 1 if transfer was followed by cashout to mule dest within 24h. |
| `rule_mule_dest` | `Integer` | `0` | Heuristic Rule 5 flag: 1 if destination account received funds from >=3 distinct senders in day. |
| `rule_dest_unchanged` | `Integer` | `0` | Heuristic Rule 6 flag: 1 if transfer to non-merchant had unchanged destination balance. |
| `rule_balance_error` | `Integer` | `0` | Heuristic Rule 7 flag: 1 if both originator and recipient exhibited arithmetic balance discrepancies. |
| `alert_score` | `Integer` | `0` | Composite heuristic score: integer sum of triggered business rules (0 to 7). |
| `anomaly_score_pct` | `Decimal / Float` | `0.0` | Isolation Forest anomaly score normalized to 0-100% scale (higher = more anomalous). |
| `ml_flag` | `Integer` | `0` | Binary machine learning anomaly flag calibrated at optimal validation F1 threshold (0.595088). |
| `rule_alert` | `Integer` | `0` | Composite heuristic alert indicator (1 if alert_score >= 1, 0 otherwise). |
| `alert_source` | `Text / String` | `None` | Attribution category: 'Both' (Rule & ML), 'Rule only', 'ML only', or 'None'. |
| `combo_score` | `Decimal / Float` | `0.0` | Blended risk score (0-100): 0.5 * (alert_score/7 * 100) + 0.5 * anomaly_score_pct. |
| `risk_band` | `Text / String` | `Low` | Operational triage band: 'Critical' (>=80), 'High' (>=60), 'Medium' (>=40), 'Low' (<40). |
| `is_alert` | `Integer` | `0` | Official production alert flag (Combined OR: rule_alert == 1 | ml_flag == 1). |
| `isFraud` | `Integer` | `0` | Ground-truth fraudulent transaction indicator (1 = Fraud, 0 = Legitimate). |
| `outcome` | `Text / String` | `True Negative` | Classification quadrant: 'True Positive', 'False Positive', 'False Negative', 'True Negative'. |
| `row_origin` | `Text / String` | `Normal sample` | Sampling designation: 'Alert/Fraud' (100% census) or 'Normal sample' (stratified legitimate sample). |

---

## `metrics_approach.csv`

**Category:** Performance Metrics Table  
**Row Count:** **6** rows (computed from file)  
**File Size:** 641 bytes  
**Purpose:** Comparative strategy performance matrix comparing the 6 detection approaches across the Full Universe.

| Column Name | Inferred Data Type | Sample Value | Description & Business Meaning |
| :--- | :---: | :---: | :--- |
| `approach` | `Text / String` | `Combined AND (combo_and)` | Detection strategy name (e.g. Combined AND, ML only, Combined OR, etc.). |
| `alerts` | `Integer` | `4224` | Total alerts flagged by this strategy. |
| `tp` | `Integer` | `4167` | True positive detections. |
| `fp` | `Integer` | `57` | False positive alarms. |
| `fn` | `Integer` | `4046` | Missed fraud cases. |
| `precision_pct` | `Decimal / Float` | `98.6506` | Precision rate of this strategy (%). |
| `recall_pct` | `Decimal / Float` | `50.7366` | Recall rate of this strategy (%). |
| `fpr_pct` | `Decimal / Float` | `0.0009` | False positive rate of this strategy (%). |
| `f1_pct` | `Decimal / Float` | `67.0097` | Balanced F1 score of this strategy (%). |
| `flagged_value` | `Decimal / Float` | `6450509292.42` | Total currency amount flagged by this strategy ($). |

---

## `metrics_overall.csv`

**Category:** Performance Metrics Table  
**Row Count:** **1** rows (computed from file)  
**File Size:** 218 bytes  
**Purpose:** Single-row enterprise KPI summary card source for Power BI executive dashboard headers.

| Column Name | Inferred Data Type | Sample Value | Description & Business Meaning |
| :--- | :---: | :---: | :--- |
| `total_txns` | `Integer` | `6362620` | Total enterprise transaction volume (6,362,620). |
| `total_alerts` | `Integer` | `1085609` | Total alerts flagged under official Combined OR definition (1,085,609). |
| `total_flagged_value` | `Decimal / Float` | `407883914866.3` | Total currency amount of alerted transactions ($407,883,914,866.30). |
| `fraud_count` | `Integer` | `8213` | Total confirmed fraud count across enterprise (8,213). |
| `fraud_rate_pct` | `Decimal / Float` | `0.1291` | Overall baseline fraud prevalence rate (0.1291%). |
| `tp` | `Integer` | `8196` | True positive detections (8,196). |
| `fp` | `Integer` | `1077413` | False positive alarms (1,077,413). |
| `fn` | `Integer` | `17` | False negatives / missed frauds (17). |
| `tn` | `Integer` | `5276994` | True negatives / correctly unflagged legitimate transactions (5,276,994). |
| `precision_pct` | `Decimal / Float` | `0.755` | Global detection precision rate (0.7550%). |
| `recall_pct` | `Decimal / Float` | `99.793` | Global detection recall rate (99.7930%). |
| `fpr_pct` | `Decimal / Float` | `16.9554` | Global false positive rate (16.9554%). |
| `f1_pct` | `Decimal / Float` | `1.4986` | Balanced F1 score expressed as percentage (1.4986%). |

---

## `metrics_rules.csv`

**Category:** Performance Metrics Table  
**Row Count:** **9** rows (computed from file)  
**File Size:** 700 bytes  
**Purpose:** Evaluation table of individual heuristic SQL business rules and composite thresholds across the Full Universe.

| Column Name | Inferred Data Type | Sample Value | Description & Business Meaning |
| :--- | :---: | :---: | :--- |
| `rule_name` | `Text / String` | `Rule 1: Account Emptied` | Descriptive business rule name (Rule 1 through Rule 7, plus composites). |
| `alerts` | `Integer` | `8008` | Alerts triggered by this rule. |
| `tp` | `Integer` | `8008` | True positive detections by this rule. |
| `fp` | `Integer` | `0` | False positive alarms by this rule. |
| `precision_pct` | `Decimal / Float` | `100.0` | Precision rate of this rule (%). |
| `recall_pct` | `Decimal / Float` | `97.504` | Recall rate of this rule (%). |
| `fpr_pct` | `Decimal / Float` | `0.0` | False positive rate of this rule (%). |
| `f1_pct` | `Decimal / Float` | `98.7362` | Balanced F1 score of this rule (%). |

---
