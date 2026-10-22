# Power BI Desktop End-to-End Data Import & Modeling Guide

**Document ID:** `powerbi/01_import_guide.md`  
**Target Directory:** `data/outputs/powerbi`  
**Scope:** All 18 CSV datasets (1 Fact table, 6 Dimensions, 7 Aggregate summaries, 4 Performance metric tables)  
**Standard:** 100% Programmatically verified against source CSV files. Every column name, data type, and row count is code-audited.  

---

## Table of Contents
1. [Executive Overview & Star-Schema Architecture](#1-executive-overview--star-schema-architecture)
2. [Critical Pre-Import Settings (Auto Date/Time & Options)](#2-critical-pre-import-settings-auto-datetime--options)
3. [Step 1: Create the `DataFolder` Parameter](#3-step-1-create-the-datafolder-parameter)
4. [Step 2: Universal CSV Import Workflow (Power Query)](#4-step-2-universal-csv-import-workflow-power-query)
5. [Master Table Inventory & Query Naming](#5-master-table-inventory--query-naming)
6. [Table-by-Table Data Type & Schema Specifications (All 18 Tables)](#6-table-by-table-data-type--schema-specifications-all-18-tables)
   - [Fact Table](#fact-table)
   - [Dimension Tables (6)](#dimension-tables-6)
   - [Aggregate Summary Tables (7)](#aggregate-summary-tables-7)
   - [Performance Metrics Tables (4)](#performance-metrics-tables-4)
7. [Step 3: Post-Load Modeling Configurations (Summarization & Sort Orders)](#7-step-3-post-load-modeling-configurations-summarization--sort-orders)
8. [Step 4: Star-Schema Relationship Wiring (Model View)](#8-step-4-star-schema-relationship-wiring-model-view)
9. [Quality Assurance & Pre-Flight Checklist](#9-quality-assurance--pre-flight-checklist)

---

## 1. Executive Overview & Star-Schema Architecture

This guide delivers a rigorous, click-by-click procedure for loading the synthetic anti-fraud transaction surveillance dataset into **Power BI Desktop**.

### Key Architectural Principles:
1. **Dual-Granularity Architecture:**
   - **`Fact_Transactions` (1,135,626 rows):** A highly performant sampled fact table containing **100% of all alerts and confirmed frauds** (1,085,626 rows, capturing all 8,213 frauds including 17 false negatives) plus a **50,000-row stratified random sample** of legitimate transactions. Raw balance columns are omitted to keep the file under 165MB for instantaneous visual responsiveness.
   - **`Agg_*` and `Metrics_*` Tables (Full 6,362,620 Universe):** 11 pre-aggregated summary and KPI tables derived directly from the full 6.36-million transaction census. Enterprise-wide figures (e.g., total transactions = 6,362,620, overall fraud count = 8,213, total flagged volume = $407.88B) are sourced directly from these tables.
2. **Pure Star-Schema Modeling:**
   - The fact table (`Fact_Transactions`) connects via clean **1-to-Many (`1:*`)**, single-directional relationships to six conforming dimension tables (`Dim_Type`, `Dim_Day`, `Dim_Hour`, `Dim_AlertSource`, `Dim_RiskBand`, `Dim_AmountBand`).
   - All aggregate and metric summary tables remain **disconnected / standalone** to prevent circular relationship paths and ambiguous filter context.
3. **Single-Source Portability (`DataFolder` Parameter):**
   - All 18 queries reference a single Power Query parameter named `DataFolder`. When cloning this repository or switching machines (macOS to Windows, local to cloud VM), you only modify this single text parameter to repoint all 18 tables simultaneously.

---

## 2. Critical Pre-Import Settings (Auto Date/Time & Options)

Before importing any data, configure Power BI Desktop to prevent automated behaviors that bloat memory and corrupt custom sort indexes:

### Action A: Disable Auto Date/Time (MANDATORY)
Power BI automatically creates hidden hierarchy calendar tables for every numeric/date column by default. In high-volume models, this consumes hundreds of megabytes of memory and generates invalid date hierarchies.

1. Launch **Power BI Desktop**.
2. In the top-left ribbon, click **File** > **Options and settings** > **Options**.
3. In the left navigation panel, scroll down to the **CURRENT FILE** section and click **Data Load**.
4. Under **Time Intelligence**:
   - **UNCHECK** the checkbox: `[ ] Auto date/time`.
5. Under **Type Detection**:
   - Recommended: Select `Never detect column types and headers for unstructured sources` (or ensure you inspect Power Query steps to avoid automatic type misinference).
6. Under **Relationships**:
   - **UNCHECK**: `[ ] Autodetect new relationships after data is loaded`.
   - **UNCHECK**: `[ ] Import relationships from data sources on first load`.
   *(Reason: You will manually wire the verified 1-to-Many Star Schema in Step 4, avoiding auto-generated bidirectional links).*
7. Click **OK** to save.

---

## 3. Step 1: Create the `DataFolder` Parameter

To avoid hardcoding absolute local file paths into all 18 queries, we establish a global Power Query parameter named `DataFolder`.

### Step-by-Step Instructions:
1. In Power BI Desktop, click **Transform data** on the **Home** ribbon. This opens the **Power Query Editor**.
2. On the **Home** tab of Power Query Editor, click the **Manage Parameters** dropdown and select **New Parameter**.
3. In the Parameter dialog, enter the following settings:
   - **Name:** `DataFolder` *(Must match exact casing)*
   - **Description:** `Absolute file system directory path to data/outputs/powerbi containing the 18 exported CSV tables.`
   - **Required:** Check the box `[X]`.
   - **Type:** Select `Text`.
   - **Suggested Values:** Select `Any value`.
   - **Current Value:** Enter your absolute directory path:
     - *macOS/Linux Example:* `/Users/divyansh/code/Development/DataScience/Fraud Detection & Transaction Monitoring/data/outputs/powerbi`
     - *Windows Example:* `C:\Users\username\Projects\Fraud-Detection-Transaction-Monitoring\data\outputs\powerbi`
4. Click **OK**.

> [!TIP]
> **Universal File Path Formatting:** Power Query supports forward slashes (`/`) universally across Windows, macOS, and Linux. When concatenating paths in M code, always use `DataFolder & "/filename.csv"`.

---

## 4. Step 2: Universal CSV Import Workflow (Power Query)

For each of the 18 tables, follow this standard, reproducible 4-step import sequence:

### Method 1: Graphical Import via `Get Data > Text/CSV`
1. In Power Query Editor, click **New Source** > **Text/CSV** (or **Home** > **Get Data** > **Text/CSV**).
2. Browse to your `data/outputs/powerbi` folder and select the desired file (e.g., `dim_type.csv`). Click **Open**.
3. In the preview dialog:
   - **File Origin:** Verify `65001: Unicode (UTF-8)`.
   - **Delimiter:** Select `Comma`.
   - **Data Type Detection:** Select `Based on first 200 rows`.
   - Click **OK**.
4. **Rename the Query:**
   - In the right-hand **Query Settings** pane under **Properties > Name**, change the default filename to the **Exact Power BI Table Name** listed in Section 5 (e.g. `Dim_Type`).
5. **Parameterize the Source Step (Crucial Step):**
   - On the **Home** tab, click **Advanced Editor**.
   - Look at the first line (`Source = Csv.Document(...)`).
   - Replace the hardcoded string path with `DataFolder & "/filename.csv"`.
   - Click **Done**.

### Method 2: Direct M-Code Pattern (Fastest & 100% Reproducible)
Instead of clicking through dialogs, you can create each query in seconds:
1. Click **New Source** > **Blank Query**.
2. In the right-hand **Query Settings** pane, rename the query to the exact table name (e.g. `Dim_Type`).
3. Click **Advanced Editor** on the **Home** tab.
4. Paste the standardized M code template:

```powerquery
let
    // 1. Ingest CSV file dynamically via DataFolder parameter
    Source = Csv.Document(File.Contents(DataFolder & "/dim_type.csv"), [Delimiter=",", Columns=3, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    
    // 2. Promote first row to column headers
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    
    // 3. Enforce strict Power Query data types
    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers",{
        {"type", type text},
        {"type_group", type text},
        {"type_sort", Int64.Type}
    })
in
    #"Changed Type"
```
5. Click **Done**.

---

## 5. Master Table Inventory & Query Naming

You MUST name every query **exactly as specified below**. Downstream DAX measures, data model relationships, and visualization templates reference these exact names.

| # | Source CSV File Name | Exact Power BI Table Name | Category | Rows | Columns | Model Role |
| :-: | :--- | :--- | :---: | --: | --: | :--- |
| 1 | `fact_transactions.csv` | **`Fact_Transactions`** | Fact Table (Sampled) | 1,135,626 | 27 | Star-Schema Fact |
| 2 | `dim_type.csv` | **`Dim_Type`** | Dimension Table | 5 | 3 | Star-Schema Dimension |
| 3 | `dim_day.csv` | **`Dim_Day`** | Dimension Table | 31 | 4 | Star-Schema Dimension |
| 4 | `dim_hour.csv` | **`Dim_Hour`** | Dimension Table | 24 | 3 | Star-Schema Dimension |
| 5 | `dim_alert_source.csv` | **`Dim_AlertSource`** | Dimension Table | 4 | 2 | Star-Schema Dimension |
| 6 | `dim_risk_band.csv` | **`Dim_RiskBand`** | Dimension Table | 4 | 2 | Star-Schema Dimension |
| 7 | `dim_amount_band.csv` | **`Dim_AmountBand`** | Dimension Table | 5 | 2 | Star-Schema Dimension |
| 8 | `agg_by_type.csv` | **`Agg_ByType`** | Aggregate Summary Table | 5 | 12 | Disconnected Summary / KPI |
| 9 | `agg_by_day.csv` | **`Agg_ByDay`** | Aggregate Summary Table | 31 | 8 | Disconnected Summary / KPI |
| 10 | `agg_by_hour.csv` | **`Agg_ByHour`** | Aggregate Summary Table | 24 | 8 | Disconnected Summary / KPI |
| 11 | `agg_by_day_type.csv` | **`Agg_ByDayType`** | Aggregate Summary Table | 152 | 6 | Disconnected Summary / KPI |
| 12 | `agg_by_source.csv` | **`Agg_BySource`** | Aggregate Summary Table | 4 | 6 | Disconnected Summary / KPI |
| 13 | `agg_by_risk_band.csv` | **`Agg_ByRiskBand`** | Aggregate Summary Table | 4 | 4 | Disconnected Summary / KPI |
| 14 | `agg_by_amount_band_type.csv` | **`Agg_ByAmountBandType`** | Aggregate Summary Table | 23 | 5 | Disconnected Summary / KPI |
| 15 | `metrics_overall.csv` | **`Metrics_Overall`** | Performance Metrics Table | 1 | 13 | Disconnected Summary / KPI |
| 16 | `metrics_approach.csv` | **`Metrics_Approach`** | Performance Metrics Table | 6 | 10 | Disconnected Summary / KPI |
| 17 | `metrics_rules.csv` | **`Metrics_Rules`** | Performance Metrics Table | 9 | 8 | Disconnected Summary / KPI |
| 18 | `confusion_matrix.csv` | **`Confusion_Matrix`** | Performance Metrics Table | 4 | 5 | Disconnected Summary / KPI |

---

## 6. Table-by-Table Data Type & Schema Specifications (All 18 Tables)

The tables below list every column across all 18 files. Every column name and data type has been programmatically verified from the underlying CSV file headers.

### Fact Table
### `Fact_Transactions` (Fact Table (Sampled))

- **Source File:** `data/outputs/powerbi/fact_transactions.csv`
- **Exact Power BI Table Name:** `Fact_Transactions`
- **Row Count:** **1,135,626** rows (verified by code)
- **Column Count:** **27** columns
- **Purpose:** Primary transaction-level fact table for granular investigator drill-downs, case triage, and alert review. Contains 100% of all alerts and confirmed fraud cases (1,085,626 rows, preserving all 8,213 frauds including 17 false negatives) plus a 50,000-row stratified sample of legitimate unalerted transactions (seed 42). High-cardinality raw balances are excluded to ensure rapid sub-second rendering in Power BI Desktop.
- **Modeling Note:** CRITICAL: Enterprise-wide aggregate metrics (total volume = 6,362,620 txns, total fraud = 8,213) must be sourced from the Agg_* and Metrics_* tables, not COUNTROWS(Fact_Transactions).

| Column Name | Power Query Data Type | Key / Role Classification | Default Summarization | Business Description & Formatting |
| :--- | :---: | :---: | :---: | :--- |
| `txn_id` | **`Whole Number`** | `[PK] Primary Key` | **`Don't summarize`** | Unique transaction identifier from clean dataset. *(Sample: `1`)* |
| `step` | **`Whole Number`** | `[ATTR] Time Step` | **`Don't summarize`** | Hourly simulation step (1 to 743). *(Sample: `1`)* |
| `day` | **`Whole Number`** | `[FK] Foreign Key -> Dim_Day[day]` | **`Don't summarize`** | Relative day of simulation (1 to 31). *(Sample: `1`)* |
| `hour` | **`Whole Number`** | `[FK] Foreign Key -> Dim_Hour[hour]` | **`Don't summarize`** | Diurnal hour of transaction (0 to 23). *(Sample: `0`)* |
| `type` | **`Text`** | `[FK] Foreign Key -> Dim_Type[type]` | **`None`** | Transaction payment method (TRANSFER, CASH_OUT, CASH_IN, PAYMENT, DEBIT). *(Sample: `PAYMENT`)* |
| `amount` | **`Decimal Number`** | `[MEASURE] Monetary Amount` | **`Sum`** | Transaction currency amount ($), rounded to 2 decimals. *(Sample: `1864.28`)* |
| `amount_band` | **`Text`** | `[FK] Foreign Key -> Dim_AmountBand[amount_band]` | **`None`** | Magnitude interval (<1K, 1K-10K, 10K-100K, 100K-1M, >1M). *(Sample: `1K-10K`)* |
| `nameOrig` | **`Text`** | `[ATTR] Account ID` | **`None`** | Customer originator account ID (C-prefixed). *(Sample: `C1666544295`)* |
| `nameDest` | **`Text`** | `[ATTR] Account ID` | **`None`** | Recipient account ID (C-prefixed customer or M-prefixed merchant). *(Sample: `M2044282225`)* |
| `rule_emptied` | **`Whole Number`** | `[FLAG] Rule 1 Flag` | **`Don't summarize`** | 1 if originator account was drained to 0, else 0. *(Sample: `0`)* |
| `rule_large_amount` | **`Whole Number`** | `[FLAG] Rule 2 Flag` | **`Don't summarize`** | 1 if transaction exceeds 99th percentile threshold for type. *(Sample: `0`)* |
| `rule_velocity` | **`Whole Number`** | `[FLAG] Rule 3 Flag` | **`Don't summarize`** | 1 if originator executed >=3 transactions in rolling 6h window. *(Sample: `0`)* |
| `rule_transfer_then_cashout` | **`Whole Number`** | `[FLAG] Rule 4 Flag` | **`Don't summarize`** | 1 if transfer was followed by cashout to mule within 24h. *(Sample: `0`)* |
| `rule_mule_dest` | **`Whole Number`** | `[FLAG] Rule 5 Flag` | **`Don't summarize`** | 1 if destination account received funds from >=3 senders in a day. *(Sample: `0`)* |
| `rule_dest_unchanged` | **`Whole Number`** | `[FLAG] Rule 6 Flag` | **`Don't summarize`** | 1 if transfer to non-merchant resulted in 0 destination balance change. *(Sample: `0`)* |
| `rule_balance_error` | **`Whole Number`** | `[FLAG] Rule 7 Flag` | **`Don't summarize`** | 1 if both originator and recipient arithmetic balances disagree. *(Sample: `0`)* |
| `alert_score` | **`Whole Number`** | `[SCORE] Heuristic Score` | **`Don't summarize`** | Composite rule score: integer sum of triggered rules (0 to 7). *(Sample: `0`)* |
| `anomaly_score_pct` | **`Decimal Number`** | `[SCORE] ML Score` | **`Don't summarize`** | Calibrated Isolation Forest anomaly percentile (0.0 to 100.0). *(Sample: `0.0`)* |
| `ml_flag` | **`Whole Number`** | `[FLAG] ML Flag` | **`Don't summarize`** | 1 if anomaly_score >= optimal F1 threshold (0.595088), else 0. *(Sample: `0`)* |
| `rule_alert` | **`Whole Number`** | `[FLAG] Rule Alert` | **`Don't summarize`** | 1 if alert_score >= 1, else 0. *(Sample: `0`)* |
| `alert_source` | **`Text`** | `[FK] Foreign Key -> Dim_AlertSource[alert_source]` | **`None`** | Attribution source ('Both', 'Rule only', 'ML only', 'None'). *(Sample: `None`)* |
| `combo_score` | **`Decimal Number`** | `[SCORE] Hybrid Score` | **`Don't summarize`** | Blended risk score (0-100): 0.5*(alert_score/7*100) + 0.5*anomaly_score_pct. *(Sample: `0.0`)* |
| `risk_band` | **`Text`** | `[FK] Foreign Key -> Dim_RiskBand[risk_band]` | **`None`** | Operational triage tier ('Critical', 'High', 'Medium', 'Low'). *(Sample: `Low`)* |
| `is_alert` | **`Whole Number`** | `[FLAG] Official Alert` | **`Don't summarize`** | Official production alert flag (Combined OR: rule_alert=1 | ml_flag=1). *(Sample: `0`)* |
| `isFraud` | **`Whole Number`** | `[FLAG] Ground Truth Fraud` | **`Don't summarize`** | Actual ground-truth fraud label (1 = Fraud, 0 = Legitimate). *(Sample: `0`)* |
| `outcome` | **`Text`** | `[ATTR] Confusion Quadrant` | **`None`** | Quadrant label ('True Positive', 'False Positive', 'False Negative', 'True Negative'). *(Sample: `True Negative`)* |
| `row_origin` | **`Text`** | `[ATTR] Sampling Designator` | **`None`** | 'Alert/Fraud' (100% census) or 'Normal sample' (stratified sample). *(Sample: `Normal sample`)* |

---

### Dimension Tables (6)
### `Dim_Type` (Dimension Table)

- **Source File:** `data/outputs/powerbi/dim_type.csv`
- **Exact Power BI Table Name:** `Dim_Type`
- **Row Count:** **5** rows (verified by code)
- **Column Count:** **3** columns
- **Purpose:** Dimension lookup table mapping transaction payment types to risk categories and custom visual sort orders.
- **Modeling Note:** Set 'type' to Sort by Column -> 'type_sort'.

| Column Name | Power Query Data Type | Key / Role Classification | Default Summarization | Business Description & Formatting |
| :--- | :---: | :---: | :---: | :--- |
| `type` | **`Text`** | `[PK] Primary Key` | **`None`** | Transaction payment method name (TRANSFER, CASH_OUT, CASH_IN, PAYMENT, DEBIT). *(Sample: `TRANSFER`)* |
| `type_group` | **`Text`** | `[ATTR] Risk Group` | **`None`** | Regulatory risk category ('Fraud-prone' vs. 'No fraud observed'). *(Sample: `Fraud-prone`)* |
| `type_sort` | **`Whole Number`** | `[SORT] Sort Order` | **`Don't summarize`** | Custom visual sort index (1 to 5). *(Sample: `1`)* |

### `Dim_Day` (Dimension Table)

- **Source File:** `data/outputs/powerbi/dim_day.csv`
- **Exact Power BI Table Name:** `Dim_Day`
- **Row Count:** **31** rows (verified by code)
- **Column Count:** **4** columns
- **Purpose:** Calendar dimension table for simulation days (Day 01 to Day 31) with day-of-week and week index hierarchy.
- **Modeling Note:** Set 'day_label' to Sort by Column -> 'day'.

| Column Name | Power Query Data Type | Key / Role Classification | Default Summarization | Business Description & Formatting |
| :--- | :---: | :---: | :---: | :--- |
| `day` | **`Whole Number`** | `[PK] Primary Key` | **`Don't summarize`** | Simulation day number (1 to 31). *(Sample: `1`)* |
| `day_label` | **`Text`** | `[ATTR] Display Label` | **`None`** | Formatted zero-padded day display string ('Day 01' to 'Day 31'). *(Sample: `Day 01`)* |
| `day_of_week_index` | **`Whole Number`** | `[ATTR] Day of Week` | **`Don't summarize`** | Relative day of week index (1 to 7). *(Sample: `1`)* |
| `week_number` | **`Whole Number`** | `[ATTR] Week Number` | **`Don't summarize`** | Relative calendar week index (1 to 5). *(Sample: `1`)* |

### `Dim_Hour` (Dimension Table)

- **Source File:** `data/outputs/powerbi/dim_hour.csv`
- **Exact Power BI Table Name:** `Dim_Hour`
- **Row Count:** **24** rows (verified by code)
- **Column Count:** **3** columns
- **Purpose:** Diurnal hourly dimension table mapping transaction hours to operational investigation shifts.
- **Modeling Note:** Set 'hour_label' to Sort by Column -> 'hour'.

| Column Name | Power Query Data Type | Key / Role Classification | Default Summarization | Business Description & Formatting |
| :--- | :---: | :---: | :---: | :--- |
| `hour` | **`Whole Number`** | `[PK] Primary Key` | **`Don't summarize`** | Diurnal hour of the day (0 to 23). *(Sample: `0`)* |
| `hour_label` | **`Text`** | `[ATTR] Display Label` | **`None`** | Clock format display label ('00:00' to '23:00'). *(Sample: `00:00`)* |
| `time_band` | **`Text`** | `[ATTR] Shift Band` | **`None`** | Operational shift interval ('Night', 'Morning', 'Afternoon', 'Evening'). *(Sample: `Night`)* |

### `Dim_AlertSource` (Dimension Table)

- **Source File:** `data/outputs/powerbi/dim_alert_source.csv`
- **Exact Power BI Table Name:** `Dim_AlertSource`
- **Row Count:** **4** rows (verified by code)
- **Column Count:** **2** columns
- **Purpose:** Dimension table defining detection attribution sources (Both, Rule only, ML only, None).
- **Modeling Note:** Set 'alert_source' to Sort by Column -> 'alert_source_sort'.

| Column Name | Power Query Data Type | Key / Role Classification | Default Summarization | Business Description & Formatting |
| :--- | :---: | :---: | :---: | :--- |
| `alert_source` | **`Text`** | `[PK] Primary Key` | **`None`** | Detection attribution name ('Both', 'Rule only', 'ML only', 'None'). *(Sample: `Both`)* |
| `alert_source_sort` | **`Whole Number`** | `[SORT] Sort Order` | **`Don't summarize`** | Custom visual sort index (1 to 4). *(Sample: `1`)* |

### `Dim_RiskBand` (Dimension Table)

- **Source File:** `data/outputs/powerbi/dim_risk_band.csv`
- **Exact Power BI Table Name:** `Dim_RiskBand`
- **Row Count:** **4** rows (verified by code)
- **Column Count:** **2** columns
- **Purpose:** Dimension table defining operational triaging risk bands (Critical, High, Medium, Low).
- **Modeling Note:** Set 'risk_band' to Sort by Column -> 'risk_band_sort'.

| Column Name | Power Query Data Type | Key / Role Classification | Default Summarization | Business Description & Formatting |
| :--- | :---: | :---: | :---: | :--- |
| `risk_band` | **`Text`** | `[PK] Primary Key` | **`None`** | Operational risk tier ('Critical', 'High', 'Medium', 'Low'). *(Sample: `Critical`)* |
| `risk_band_sort` | **`Whole Number`** | `[SORT] Sort Order` | **`Don't summarize`** | Custom visual sort index (1 to 4). *(Sample: `1`)* |

### `Dim_AmountBand` (Dimension Table)

- **Source File:** `data/outputs/powerbi/dim_amount_band.csv`
- **Exact Power BI Table Name:** `Dim_AmountBand`
- **Row Count:** **5** rows (verified by code)
- **Column Count:** **2** columns
- **Purpose:** Dimension table defining transactional currency magnitude intervals.
- **Modeling Note:** Set 'amount_band' to Sort by Column -> 'amount_band_sort'.

| Column Name | Power Query Data Type | Key / Role Classification | Default Summarization | Business Description & Formatting |
| :--- | :---: | :---: | :---: | :--- |
| `amount_band` | **`Text`** | `[PK] Primary Key` | **`None`** | Monetary magnitude interval label (<1K, 1K-10K, 10K-100K, 100K-1M, >1M). *(Sample: `<1K`)* |
| `amount_band_sort` | **`Whole Number`** | `[SORT] Sort Order` | **`Don't summarize`** | Magnitude sort index (1 to 5). *(Sample: `1`)* |

---

### Aggregate Summary Tables (7)
### `Agg_ByType` (Aggregate Summary Table)

- **Source File:** `data/outputs/powerbi/agg_by_type.csv`
- **Exact Power BI Table Name:** `Agg_ByType`
- **Row Count:** **5** rows (verified by code)
- **Column Count:** **12** columns
- **Purpose:** Full-universe (6.36M) pre-aggregated volume, confusion matrix breakdown, and alert rates by transaction type.
- **Modeling Note:** Standalone aggregate table. Total txns sum to 6,362,620; total fraud sums to 8,213.

| Column Name | Power Query Data Type | Key / Role Classification | Default Summarization | Business Description & Formatting |
| :--- | :---: | :---: | :---: | :--- |
| `type` | **`Text`** | `[ATTR] Payment Type` | **`None`** | Transaction payment method name. *(Sample: `CASH_OUT`)* |
| `total_txns` | **`Whole Number`** | `[MEASURE] Total Volume` | **`Sum`** | Total enterprise transaction volume of this type. *(Sample: `2237500`)* |
| `total_amount` | **`Decimal Number`** | `[MEASURE] Currency Volume` | **`Sum`** | Total transactional currency amount ($). *(Sample: `394412995224.49`)* |
| `fraud_count` | **`Whole Number`** | `[MEASURE] Fraud Count` | **`Sum`** | Total confirmed fraudulent transactions. *(Sample: `4116`)* |
| `alert_count` | **`Whole Number`** | `[MEASURE] Alert Count` | **`Sum`** | Total alerts triggered under official Combined OR definition. *(Sample: `865375`)* |
| `tp` | **`Whole Number`** | `[MEASURE] True Positives` | **`Sum`** | True positive fraud detections. *(Sample: `4100`)* |
| `fp` | **`Whole Number`** | `[MEASURE] False Positives` | **`Sum`** | False positive alarms (legitimate transactions flagged). *(Sample: `861275`)* |
| `fn` | **`Whole Number`** | `[MEASURE] False Negatives` | **`Sum`** | False negatives (missed fraudulent transactions). *(Sample: `16`)* |
| `tn` | **`Whole Number`** | `[MEASURE] True Negatives` | **`Sum`** | True negatives (correctly unalerted legitimate transactions). *(Sample: `1372109`)* |
| `flagged_value` | **`Decimal Number`** | `[MEASURE] Flagged Exposure` | **`Sum`** | Total currency amount of flagged transactions ($). *(Sample: `171525973861.11`)* |
| `fraud_rate_pct` | **`Decimal Number`** | `[METRIC] Fraud Rate (%)` | **`Average`** | Prevalence of fraud within this payment type (%). *(Sample: `0.184`)* |
| `alert_rate_pct` | **`Decimal Number`** | `[METRIC] Alert Rate (%)` | **`Average`** | Proportion of transactions flagged for review (%). *(Sample: `38.676`)* |

### `Agg_ByDay` (Aggregate Summary Table)

- **Source File:** `data/outputs/powerbi/agg_by_day.csv`
- **Exact Power BI Table Name:** `Agg_ByDay`
- **Row Count:** **31** rows (verified by code)
- **Column Count:** **8** columns
- **Purpose:** Full-universe daily aggregated temporal trend metrics across the 31-day monitoring window.
- **Modeling Note:** Standalone aggregate table. Do not summarize 'day'.

| Column Name | Power Query Data Type | Key / Role Classification | Default Summarization | Business Description & Formatting |
| :--- | :---: | :---: | :---: | :--- |
| `day` | **`Whole Number`** | `[ATTR] Simulation Day` | **`Don't summarize`** | Simulation day number (1 to 31). *(Sample: `1`)* |
| `total_txns` | **`Whole Number`** | `[MEASURE] Total Volume` | **`Sum`** | Total enterprise transaction volume on this day. *(Sample: `574255`)* |
| `fraud_count` | **`Whole Number`** | `[MEASURE] Fraud Count` | **`Sum`** | Confirmed fraud count on this day. *(Sample: `271`)* |
| `alert_count` | **`Whole Number`** | `[MEASURE] Alert Count` | **`Sum`** | Alerts triggered on this day. *(Sample: `232177`)* |
| `tp` | **`Whole Number`** | `[MEASURE] True Positives` | **`Sum`** | True positive detections on this day. *(Sample: `270`)* |
| `fp` | **`Whole Number`** | `[MEASURE] False Positives` | **`Sum`** | False positive alarms on this day. *(Sample: `231907`)* |
| `fn` | **`Whole Number`** | `[MEASURE] False Negatives` | **`Sum`** | Missed fraud cases on this day. *(Sample: `1`)* |
| `flagged_value` | **`Decimal Number`** | `[MEASURE] Flagged Exposure` | **`Sum`** | Total currency amount of alerted transactions on this day ($). *(Sample: `65682848402.44`)* |

### `Agg_ByHour` (Aggregate Summary Table)

- **Source File:** `data/outputs/powerbi/agg_by_hour.csv`
- **Exact Power BI Table Name:** `Agg_ByHour`
- **Row Count:** **24** rows (verified by code)
- **Column Count:** **8** columns
- **Purpose:** Full-universe hourly aggregated diurnal fraud and surveillance profile (hours 0 to 23).
- **Modeling Note:** Standalone aggregate table. Do not summarize 'hour'.

| Column Name | Power Query Data Type | Key / Role Classification | Default Summarization | Business Description & Formatting |
| :--- | :---: | :---: | :---: | :--- |
| `hour` | **`Whole Number`** | `[ATTR] Diurnal Hour` | **`Don't summarize`** | Diurnal hour of the day (0 to 23). *(Sample: `0`)* |
| `total_txns` | **`Whole Number`** | `[MEASURE] Total Volume` | **`Sum`** | Total enterprise transaction volume at this hour. *(Sample: `27111`)* |
| `fraud_count` | **`Whole Number`** | `[MEASURE] Fraud Count` | **`Sum`** | Confirmed fraud count at this hour. *(Sample: `358`)* |
| `alert_count` | **`Whole Number`** | `[MEASURE] Alert Count` | **`Sum`** | Alerts triggered at this hour. *(Sample: `2628`)* |
| `tp` | **`Whole Number`** | `[MEASURE] True Positives` | **`Sum`** | True positive detections at this hour. *(Sample: `358`)* |
| `fp` | **`Whole Number`** | `[MEASURE] False Positives` | **`Sum`** | False positive alarms at this hour. *(Sample: `2270`)* |
| `fn` | **`Whole Number`** | `[MEASURE] False Negatives` | **`Sum`** | Missed fraud cases at this hour. *(Sample: `0`)* |
| `flagged_value` | **`Decimal Number`** | `[MEASURE] Flagged Exposure` | **`Sum`** | Total currency amount of alerted transactions at this hour ($). *(Sample: `1209224284.48`)* |

### `Agg_ByDayType` (Aggregate Summary Table)

- **Source File:** `data/outputs/powerbi/agg_by_day_type.csv`
- **Exact Power BI Table Name:** `Agg_ByDayType`
- **Row Count:** **152** rows (verified by code)
- **Column Count:** **6** columns
- **Purpose:** Granular cross-tabulation of daily transaction volume, fraud count, and alerts across all payment types.
- **Modeling Note:** Standalone aggregate table. Do not summarize 'day'.

| Column Name | Power Query Data Type | Key / Role Classification | Default Summarization | Business Description & Formatting |
| :--- | :---: | :---: | :---: | :--- |
| `day` | **`Whole Number`** | `[ATTR] Simulation Day` | **`Don't summarize`** | Simulation day number (1 to 31). *(Sample: `1`)* |
| `type` | **`Text`** | `[ATTR] Payment Type` | **`None`** | Transaction payment method name. *(Sample: `CASH_IN`)* |
| `total_txns` | **`Whole Number`** | `[MEASURE] Total Volume` | **`Sum`** | Total transaction volume for this day and type. *(Sample: `124026`)* |
| `fraud_count` | **`Whole Number`** | `[MEASURE] Fraud Count` | **`Sum`** | Confirmed fraud count for this day and type. *(Sample: `0`)* |
| `alert_count` | **`Whole Number`** | `[MEASURE] Alert Count` | **`Sum`** | Alerts triggered for this day and type. *(Sample: `0`)* |
| `flagged_value` | **`Decimal Number`** | `[MEASURE] Flagged Exposure` | **`Sum`** | Total currency amount of alerted transactions ($). *(Sample: `0.0`)* |

### `Agg_BySource` (Aggregate Summary Table)

- **Source File:** `data/outputs/powerbi/agg_by_source.csv`
- **Exact Power BI Table Name:** `Agg_BySource`
- **Row Count:** **4** rows (verified by code)
- **Column Count:** **6** columns
- **Purpose:** Alert attribution breakdown comparing Consensus ('Both'), Rules only, ML only, and Unflagged ('None').
- **Modeling Note:** Standalone aggregate table. Shows alert triage efficacy across the four sources.

| Column Name | Power Query Data Type | Key / Role Classification | Default Summarization | Business Description & Formatting |
| :--- | :---: | :---: | :---: | :--- |
| `alert_source` | **`Text`** | `[ATTR] Attribution Source` | **`None`** | Attribution category ('Both', 'Rule only', 'ML only', 'None'). *(Sample: `None`)* |
| `alert_count` | **`Whole Number`** | `[MEASURE] Alert Count` | **`Sum`** | Total transaction count in this attribution category. *(Sample: `5277011`)* |
| `fraud_caught` | **`Whole Number`** | `[MEASURE] Fraud Caught` | **`Sum`** | Confirmed fraud events intercepted. *(Sample: `17`)* |
| `fp` | **`Whole Number`** | `[MEASURE] False Positives` | **`Sum`** | False positive alarms generated. *(Sample: `0`)* |
| `flagged_value` | **`Decimal Number`** | `[MEASURE] Flagged Exposure` | **`Sum`** | Total currency amount flagged in this attribution source ($). *(Sample: `0.0`)* |
| `precision_pct` | **`Decimal Number`** | `[METRIC] Precision (%)` | **`Average`** | Detection precision / hit rate within this attribution source (%). *(Sample: `0.0003`)* |

### `Agg_ByRiskBand` (Aggregate Summary Table)

- **Source File:** `data/outputs/powerbi/agg_by_risk_band.csv`
- **Exact Power BI Table Name:** `Agg_ByRiskBand`
- **Row Count:** **4** rows (verified by code)
- **Column Count:** **4** columns
- **Purpose:** Pre-aggregated operational distribution across the four tiered risk bands (Critical, High, Medium, Low).
- **Modeling Note:** Standalone aggregate table. Rows sum to 6,362,620; fraud count sums to 8,213.

| Column Name | Power Query Data Type | Key / Role Classification | Default Summarization | Business Description & Formatting |
| :--- | :---: | :---: | :---: | :--- |
| `risk_band` | **`Text`** | `[ATTR] Risk Band` | **`None`** | Operational risk band name ('Critical', 'High', 'Medium', 'Low'). *(Sample: `Critical`)* |
| `rows` | **`Whole Number`** | `[MEASURE] Transaction Count` | **`Sum`** | Total transactions classified into this risk band. *(Sample: `0`)* |
| `fraud_count` | **`Whole Number`** | `[MEASURE] Fraud Count` | **`Sum`** | Confirmed fraudulent transactions in this risk band. *(Sample: `0`)* |
| `flagged_value` | **`Decimal Number`** | `[MEASURE] Flagged Exposure` | **`Sum`** | Total currency amount flagged in this risk band ($). *(Sample: `0.0`)* |

### `Agg_ByAmountBandType` (Aggregate Summary Table)

- **Source File:** `data/outputs/powerbi/agg_by_amount_band_type.csv`
- **Exact Power BI Table Name:** `Agg_ByAmountBandType`
- **Row Count:** **23** rows (verified by code)
- **Column Count:** **5** columns
- **Purpose:** Cross-tabulation matrix of transaction amount magnitude intervals vs. payment types.
- **Modeling Note:** Standalone aggregate table. Total txns sum to 6,362,620; fraud count sums to 8,213.

| Column Name | Power Query Data Type | Key / Role Classification | Default Summarization | Business Description & Formatting |
| :--- | :---: | :---: | :---: | :--- |
| `amount_band` | **`Text`** | `[ATTR] Amount Band` | **`None`** | Monetary magnitude interval label (<1K, 1K-10K, 10K-100K, 100K-1M, >1M). *(Sample: `100K-1M`)* |
| `type` | **`Text`** | `[ATTR] Payment Type` | **`None`** | Transaction payment method. *(Sample: `CASH_IN`)* |
| `total_txns` | **`Whole Number`** | `[MEASURE] Total Volume` | **`Sum`** | Total transaction volume in this amount band and type. *(Sample: `901759`)* |
| `fraud_count` | **`Whole Number`** | `[MEASURE] Fraud Count` | **`Sum`** | Confirmed fraud count in this amount band and type. *(Sample: `0`)* |
| `alert_count` | **`Whole Number`** | `[MEASURE] Alert Count` | **`Sum`** | Alerts triggered in this amount band and type. *(Sample: `0`)* |

---

### Performance Metrics Tables (4)
### `Metrics_Overall` (Performance Metrics Table)

- **Source File:** `data/outputs/powerbi/metrics_overall.csv`
- **Exact Power BI Table Name:** `Metrics_Overall`
- **Row Count:** **1** rows (verified by code)
- **Column Count:** **13** columns
- **Purpose:** Single-row enterprise KPI summary card source for Power BI executive dashboard headers.
- **Modeling Note:** Single-row summary table for headline card visuals. Do not aggregate further.

| Column Name | Power Query Data Type | Key / Role Classification | Default Summarization | Business Description & Formatting |
| :--- | :---: | :---: | :---: | :--- |
| `total_txns` | **`Whole Number`** | `[KPI] Total Transactions` | **`Don't summarize`** | Total enterprise transaction volume (6,362,620). *(Sample: `6362620`)* |
| `total_alerts` | **`Whole Number`** | `[KPI] Total Alerts` | **`Don't summarize`** | Total alerts flagged under official Combined OR definition (1,085,609). *(Sample: `1085609`)* |
| `total_flagged_value` | **`Decimal Number`** | `[KPI] Flagged Value ($)` | **`Don't summarize`** | Total currency amount of alerted transactions ($407,883,914,866.30). *(Sample: `407883914866.3`)* |
| `fraud_count` | **`Whole Number`** | `[KPI] Fraud Count` | **`Don't summarize`** | Total confirmed fraud count across enterprise (8,213). *(Sample: `8213`)* |
| `fraud_rate_pct` | **`Decimal Number`** | `[KPI] Fraud Rate (%)` | **`Don't summarize`** | Overall baseline fraud prevalence rate (0.1291%). *(Sample: `0.1291`)* |
| `tp` | **`Whole Number`** | `[KPI] True Positives` | **`Don't summarize`** | True positive detections (8,196). *(Sample: `8196`)* |
| `fp` | **`Whole Number`** | `[KPI] False Positives` | **`Don't summarize`** | False positive alarms (1,077,413). *(Sample: `1077413`)* |
| `fn` | **`Whole Number`** | `[KPI] False Negatives` | **`Don't summarize`** | False negatives / missed frauds (17). *(Sample: `17`)* |
| `tn` | **`Whole Number`** | `[KPI] True Negatives` | **`Don't summarize`** | True negatives / correctly unflagged legitimate transactions (5,276,994). *(Sample: `5276994`)* |
| `precision_pct` | **`Decimal Number`** | `[KPI] Precision (%)` | **`Don't summarize`** | Global detection precision rate (0.7550%). *(Sample: `0.755`)* |
| `recall_pct` | **`Decimal Number`** | `[KPI] Recall (%)` | **`Don't summarize`** | Global detection recall rate (99.7930%). *(Sample: `99.793`)* |
| `fpr_pct` | **`Decimal Number`** | `[KPI] False Positive Rate (%)` | **`Don't summarize`** | Global false positive rate (16.9554%). *(Sample: `16.9554`)* |
| `f1_pct` | **`Decimal Number`** | `[KPI] F1 Score (%)` | **`Don't summarize`** | Balanced F1 score expressed as percentage (1.4986%). *(Sample: `1.4986`)* |

### `Metrics_Approach` (Performance Metrics Table)

- **Source File:** `data/outputs/powerbi/metrics_approach.csv`
- **Exact Power BI Table Name:** `Metrics_Approach`
- **Row Count:** **6** rows (verified by code)
- **Column Count:** **10** columns
- **Purpose:** Comparative strategy performance matrix comparing the 6 detection approaches across the Full Universe.
- **Modeling Note:** Sorted by operational utility. Use to drive strategy comparison tables and visual matrices.

| Column Name | Power Query Data Type | Key / Role Classification | Default Summarization | Business Description & Formatting |
| :--- | :---: | :---: | :---: | :--- |
| `approach` | **`Text`** | `[ATTR] Strategy Name` | **`None`** | Detection strategy name (e.g. Combined AND, ML only, Combined OR, etc.). *(Sample: `Combined AND (combo_and)`)* |
| `alerts` | **`Whole Number`** | `[MEASURE] Total Alerts` | **`Sum`** | Total alerts flagged by this strategy. *(Sample: `4224`)* |
| `tp` | **`Whole Number`** | `[MEASURE] True Positives` | **`Sum`** | True positive detections. *(Sample: `4167`)* |
| `fp` | **`Whole Number`** | `[MEASURE] False Positives` | **`Sum`** | False positive alarms. *(Sample: `57`)* |
| `fn` | **`Whole Number`** | `[MEASURE] False Negatives` | **`Sum`** | Missed fraud cases. *(Sample: `4046`)* |
| `precision_pct` | **`Decimal Number`** | `[METRIC] Precision (%)` | **`Average`** | Precision rate of this strategy (%). *(Sample: `98.6506`)* |
| `recall_pct` | **`Decimal Number`** | `[METRIC] Recall (%)` | **`Average`** | Recall rate of this strategy (%). *(Sample: `50.7366`)* |
| `fpr_pct` | **`Decimal Number`** | `[METRIC] FPR (%)` | **`Average`** | False positive rate of this strategy (%). *(Sample: `0.0009`)* |
| `f1_pct` | **`Decimal Number`** | `[METRIC] F1 (%)` | **`Average`** | Balanced F1 score of this strategy (%). *(Sample: `67.0097`)* |
| `flagged_value` | **`Decimal Number`** | `[MEASURE] Flagged Exposure` | **`Sum`** | Total currency amount flagged by this strategy ($). *(Sample: `6450509292.42`)* |

### `Metrics_Rules` (Performance Metrics Table)

- **Source File:** `data/outputs/powerbi/metrics_rules.csv`
- **Exact Power BI Table Name:** `Metrics_Rules`
- **Row Count:** **9** rows (verified by code)
- **Column Count:** **8** columns
- **Purpose:** Evaluation table of individual heuristic SQL business rules and composite thresholds across the Full Universe.
- **Modeling Note:** Benchmarking source for rule attribution charts and investigator rule tuning.

| Column Name | Power Query Data Type | Key / Role Classification | Default Summarization | Business Description & Formatting |
| :--- | :---: | :---: | :---: | :--- |
| `rule_name` | **`Text`** | `[ATTR] Rule Identifier` | **`None`** | Descriptive business rule name (Rule 1 through Rule 7, plus composites). *(Sample: `Rule 1: Account Emptied`)* |
| `alerts` | **`Whole Number`** | `[MEASURE] Total Alerts` | **`Sum`** | Alerts triggered by this rule. *(Sample: `8008`)* |
| `tp` | **`Whole Number`** | `[MEASURE] True Positives` | **`Sum`** | True positive detections by this rule. *(Sample: `8008`)* |
| `fp` | **`Whole Number`** | `[MEASURE] False Positives` | **`Sum`** | False positive alarms by this rule. *(Sample: `0`)* |
| `precision_pct` | **`Decimal Number`** | `[METRIC] Precision (%)` | **`Average`** | Precision rate of this rule (%). *(Sample: `100.0`)* |
| `recall_pct` | **`Decimal Number`** | `[METRIC] Recall (%)` | **`Average`** | Recall rate of this rule (%). *(Sample: `97.504`)* |
| `fpr_pct` | **`Decimal Number`** | `[METRIC] FPR (%)` | **`Average`** | False positive rate of this rule (%). *(Sample: `0.0`)* |
| `f1_pct` | **`Decimal Number`** | `[METRIC] F1 (%)` | **`Average`** | Balanced F1 score of this rule (%). *(Sample: `98.7362`)* |

### `Confusion_Matrix` (Performance Metrics Table)

- **Source File:** `data/outputs/powerbi/confusion_matrix.csv`
- **Exact Power BI Table Name:** `Confusion_Matrix`
- **Row Count:** **4** rows (verified by code)
- **Column Count:** **5** columns
- **Purpose:** Four-row classification quadrant table formatted for direct ingestion by Power BI matrix visuals.
- **Modeling Note:** Direct source for 2x2 confusion matrix visual. Counts sum to 6,362,620.

| Column Name | Power Query Data Type | Key / Role Classification | Default Summarization | Business Description & Formatting |
| :--- | :---: | :---: | :---: | :--- |
| `outcome` | **`Text`** | `[ATTR] Quadrant Name` | **`None`** | Classification quadrant name ('True Positive', 'False Positive', 'False Negative', 'True Negative'). *(Sample: `True Positive`)* |
| `actual` | **`Text`** | `[ATTR] Actual Condition` | **`None`** | Ground truth condition ('Fraud' vs. 'Legit'). *(Sample: `Fraud`)* |
| `predicted` | **`Text`** | `[ATTR] System Action` | **`None`** | System detection action ('Alert' vs. 'No alert'). *(Sample: `Alert`)* |
| `count` | **`Whole Number`** | `[MEASURE] Quadrant Count` | **`Sum`** | Total transaction count in this quadrant. *(Sample: `8196`)* |
| `pct_of_total` | **`Decimal Number`** | `[METRIC] Share of Total (%)` | **`Sum`** | Percentage share of total enterprise transaction volume (%). *(Sample: `0.1288`)* |

---

## 7. Step 3: Post-Load Modeling Configurations (Summarization & Sort Orders)

Once all 18 queries are loaded (click **Close & Apply** in Power Query Editor), configure column summarization and sort orders in the **Data View** or **Model View**.

### A. Setting Column Summarization to "Don't summarize"
By default, Power BI automatically sets any numeric column to `Sum`. For ID keys, temporal steps, scores, and binary 0/1 flags, this causes nonsensical sums if dragged into visual tables.

#### Click-by-Click Instructions:
1. Switch to **Data View** (table icon on the left rail) or **Model View**.
2. In the **Data** pane on the right, expand the table and select the column.
3. On the top ribbon, select the **Column tools** tab.
4. In the **Structure** group, locate **Summarization**.
5. Click the dropdown and change `Sum` to **`Don't summarize`**.

#### Complete Checklist of Columns Requiring "Don't summarize":

| Table Name | Columns to set to "Don't summarize" | Rationale |
| :--- | :--- | :--- |
| **`Fact_Transactions`** | `txn_id`, `step`, `day`, `hour`, `rule_emptied`, `rule_large_amount`, `rule_velocity`, `rule_transfer_then_cashout`, `rule_mule_dest`, `rule_dest_unchanged`, `rule_balance_error`, `alert_score`, `anomaly_score_pct`, `ml_flag`, `rule_alert`, `combo_score`, `is_alert`, `isFraud` | Prevents nonsensical summing of primary keys, temporal indices, scores, and 0/1 binary indicator flags. |
| **`Dim_Type`** | `type_sort` | Sort order index. |
| **`Dim_Day`** | `day`, `day_of_week_index`, `week_number` | Day keys and calendar hierarchy indices. |
| **`Dim_Hour`** | `hour` | Hour coordinate (0-23). |
| **`Dim_AlertSource`** | `alert_source_sort` | Sort order index. |
| **`Dim_RiskBand`** | `risk_band_sort` | Sort order index. |
| **`Dim_AmountBand`** | `amount_band_sort` | Sort order index. |
| **`Agg_ByDay`** | `day` | Day coordinate (1-31). |
| **`Agg_ByHour`** | `hour` | Hour coordinate (0-23). |
| **`Agg_ByDayType`** | `day` | Day coordinate (1-31). |
| **`Metrics_Overall`** | *All 13 numeric columns* | Single-row headline card source; must not be aggregated further. |

---

### B. Configuring Custom Sort Orders ("Sort by Column")
By default, Power BI sorts text fields alphabetically (e.g. "Critical", "High", "Low", "Medium" or "Day 01", "Day 10", "Day 02"). You must configure custom sort columns on all dimensions:

#### Click-by-Click Instructions:
1. In **Data View**, select the table in the right **Data** pane.
2. Click on the display text column to select it.
3. On the **Column tools** ribbon, click **Sort by column**.
4. Select the matching numeric sort column from the dropdown.

#### Required Sort-By-Column Mappings:

| Table Name | Display Column (Sort Target) | Sort-by Column (Numeric Index) | Resulting Visual Order |
| :--- | :--- | :--- | :--- |
| **`Dim_Type`** | `type` | `type_sort` | `TRANSFER`, `CASH_OUT`, `CASH_IN`, `PAYMENT`, `DEBIT` |
| **`Dim_Day`** | `day_label` | `day` | `Day 01`, `Day 02`, ..., `Day 31` (chronological) |
| **`Dim_Hour`** | `hour_label` | `hour` | `00:00`, `01:00`, ..., `23:00` (diurnal sequence) |
| **`Dim_AlertSource`** | `alert_source` | `alert_source_sort` | `Both`, `Rule only`, `ML only`, `None` (by triage priority) |
| **`Dim_RiskBand`** | `risk_band` | `risk_band_sort` | `Critical`, `High`, `Medium`, `Low` (highest risk first) |
| **`Dim_AmountBand`** | `amount_band` | `amount_band_sort` | `<1K`, `1K-10K`, `10K-100K`, `100K-1M`, `>1M` (magnitude order) |

---

## 8. Step 4: Star-Schema Relationship Wiring (Model View)

Switch to **Model View** (diagram icon on the left rail) and wire the relationships between dimensions and the fact table.

### Relationship Specifications Table:

| From Table (Dimension) | From Column (PK) | To Table (Fact) | To Column (FK) | Cardinality | Cross Filter Direction | Active? |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| **`Dim_Type`** | `type` | **`Fact_Transactions`** | `type` | **1 to Many (`1:*`)** | Single (Dim filters Fact) | **Yes** |
| **`Dim_Day`** | `day` | **`Fact_Transactions`** | `day` | **1 to Many (`1:*`)** | Single (Dim filters Fact) | **Yes** |
| **`Dim_Hour`** | `hour` | **`Fact_Transactions`** | `hour` | **1 to Many (`1:*`)** | Single (Dim filters Fact) | **Yes** |
| **`Dim_AlertSource`** | `alert_source` | **`Fact_Transactions`** | `alert_source` | **1 to Many (`1:*`)** | Single (Dim filters Fact) | **Yes** |
| **`Dim_RiskBand`** | `risk_band` | **`Fact_Transactions`** | `risk_band` | **1 to Many (`1:*`)** | Single (Dim filters Fact) | **Yes** |
| **`Dim_AmountBand`** | `amount_band` | **`Fact_Transactions`** | `amount_band` | **1 to Many (`1:*`)** | Single (Dim filters Fact) | **Yes** |

> [!IMPORTANT]
> **Keep Summary Tables Disconnected:** The 7 `Agg_*` tables and 4 `Metrics_*` tables should remain **completely disconnected** in the Model View. They provide full-universe pre-aggregated baselines and must not be filtered by dimension slicers unless explicitly intended.

---

## 9. Quality Assurance & Pre-Flight Checklist

Before building dashboard canvases and report visuals, verify these 8 validation criteria:

- [ ] **Check 1: Table Count:** Exactly **18 queries** appear in the Power Query Queries pane.
- [ ] **Check 2: Dynamic Path:** Changing the `DataFolder` parameter value repoints all 18 queries cleanly.
- [ ] **Check 3: Fact Table Row Count:** `Fact_Transactions` displays exactly **1,135,626 rows** in Power BI Desktop.
- [ ] **Check 4: 100% Fraud Preservation:** A card visual showing `SUM(Fact_Transactions[isFraud])` outputs exactly **8,213**.
- [ ] **Check 5: Full-Universe Reconciliation:** `SUM(Agg_ByType[total_txns])` outputs exactly **6,362,620** and `SUM(Agg_ByType[fraud_count])` outputs **8,213**.
- [ ] **Check 6: Zero Misinferred Types:** No string column (e.g. `nameOrig`, `nameDest`, `alert_source`) is typed as numeric.
- [ ] **Check 7: Custom Sorters Active:** Slicers for `risk_band` display *Critical* at the top and *Low* at the bottom; slicers for `amount_band` display in ascending magnitude order.
- [ ] **Check 8: Auto Date/Time Inactive:** No automatic calendar hierarchy tables (`LocalDateTable_*`) appear in the Model View.

---
*Guide generated programmatically by `src/build_import_guide.py` directly from `data/outputs/powerbi/*.csv`.*