# Power BI Semantic Data Model & Relationship Architecture

**Document ID:** `powerbi/02_data_model.md`  
**Model Architecture:** Pure Star Schema with Conforming Dimensional Constellation  
**Central Fact Table:** `Fact_Transactions` (1,135,626 sampled rows, 100% alert & fraud census)  
**Conforming Dimensions:** 6 Dimension Tables (`Dim_Type`, `Dim_Day`, `Dim_Hour`, `Dim_AlertSource`, `Dim_RiskBand`, `Dim_AmountBand`)  
**Enterprise Aggregates:** 7 Full-Universe (6.36M) Summary Tables  
**Enterprise Metrics:** 4 Standalone Diagnostic & Benchmark KPI Tables  
**Verification Status:** 100% Programmatically verified by `src/build_data_model_doc.py` against exported CSVs.  

---

## Table of Contents
1. [Star-Schema Architecture & Topology](#1-star-schema-architecture--topology)
2. [Complete Relationship Master Table (Model View Configuration)](#2-complete-relationship-master-table-model-view-configuration)
3. [Aggregate Table Relationship Strategy & Multi-Dimensional Keys](#3-aggregate-table-relationship-strategy--multi-dimensional-keys)
4. [Strict "Do Not Do" Modeling Rules](#4-strict-do-not-do-modeling-rules)
5. [Visual-to-Table Mapping Matrix (Which Table Feeds What)](#5-visual-to-table-mapping-matrix-which-table-feeds-what)
6. [Programmatic Column & Referential Integrity Verification Report](#6-programmatic-column--referential-integrity-verification-report)

---

## 1. Star-Schema Architecture & Topology

The Power BI semantic layer uses a **pure Star Schema with conforming dimensional sharing**:

1. **Core Fact Table (`Fact_Transactions`):**
   - Sits at the geometric centre of the data model.
   - Captures granular transactional surveillance outcomes: individual alert flags, rule triggers, ML anomaly scores, amounts, timestamps, and customer accounts.
   - Contains **100% of all alerts and confirmed fraud cases (1,085,626 rows)**, preserving all 8,213 ground-truth frauds (including 17 missed false negatives), plus a **50,000-row stratified random sample** of legitimate transactions (seed 42).
   - Total row count: **1,135,626 rows**.

2. **Six Conforming Dimension Tables (Surrounding the Fact Table):**
   - Provide standardized business filter context and custom visual sorting for all reports:
     - `Dim_Type`: Payment methods (TRANSFER, CASH_OUT, etc.) mapped to regulatory risk groups.
     - `Dim_Day`: 31 simulation days with chronological labels and calendar hierarchies.
     - `Dim_Hour`: 24 diurnal hours (00:00 to 23:00) mapped to four operational investigation shifts.
     - `Dim_AlertSource`: Four detection triage categories (`Both`, `Rule only`, `ML only`, `None`).
     - `Dim_RiskBand`: Four prioritized triage risk tiers (`Critical`, `High`, `Medium`, `Low`).
     - `Dim_AmountBand`: Logarithmic monetary magnitude intervals (`<1K` to `>1M`).

3. **Shared Dimensional Constellation (Aggregate Tables):**
   - Pre-aggregated full-universe summary tables (`Agg_ByType`, `Agg_ByDay`, `Agg_ByHour`, `Agg_ByDayType`, `Agg_ByAmountBandType`, `Agg_BySource`, `Agg_ByRiskBand`) connect directly to the same dimension tables.
   - Slicers placed on `Dim_Type`, `Dim_Day`, or `Dim_Hour` simultaneously filter both the granular fact table and the full-universe aggregate charts, without cross-filtering artifacts.

4. **Disconnected Metric Tables (Standalone):**
   - `Metrics_Overall`, `Metrics_Approach`, `Metrics_Rules`, and `Confusion_Matrix` remain **completely disconnected** to provide immutable enterprise benchmarks.

### Semantic Model Architecture Diagram (Mermaid)

```mermaid
graph TD
    %% Conforming Dimensions
    subgraph Dimensions [Conforming Dimensions]
        D_TYPE["Dim_Type (PK: type)"]
        D_DAY["Dim_Day (PK: day)"]
        D_HOUR["Dim_Hour (PK: hour)"]
        D_SRC["Dim_AlertSource (PK: alert_source)"]
        D_RISK["Dim_RiskBand (PK: risk_band)"]
        D_AMT["Dim_AmountBand (PK: amount_band)"]
    end

    %% Central Fact Table
    subgraph CoreFact [Central Fact Table]
        FACT["Fact_Transactions<br/>(1,135,626 rows | 100% Alerts & Frauds)"]
    end

    %% Aggregate Tables (Constellation)
    subgraph Aggregates [Full-Universe Pre-Aggregated Summaries (6.36M Census)]
        AGG_TYPE["Agg_ByType"]
        AGG_DAY["Agg_ByDay"]
        AGG_HOUR["Agg_ByHour"]
        AGG_DAYTYPE["Agg_ByDayType"]
        AGG_AMTTYPE["Agg_ByAmountBandType"]
        AGG_SRC["Agg_BySource"]
        AGG_RISK["Agg_ByRiskBand"]
    end

    %% Disconnected Metric Tables
    subgraph Standalone [Disconnected Enterprise Benchmarks]
        MET_OVERALL["Metrics_Overall<br/>(Headline KPIs)"]
        MET_APP["Metrics_Approach<br/>(Strategy Matrix)"]
        MET_RULES["Metrics_Rules<br/>(Rule Diagnostics)"]
        MET_CM["Confusion_Matrix<br/>(2x2 Matrix Visual)"]
    end

    %% Core Fact Relationships (1 to Many, Single Direction)
    D_TYPE -->|"1 : *"| FACT
    D_DAY -->|"1 : *"| FACT
    D_HOUR -->|"1 : *"| FACT
    D_SRC -->|"1 : *"| FACT
    D_RISK -->|"1 : *"| FACT
    D_AMT -->|"1 : *"| FACT

    %% Aggregate Relationships (Conforming Dimension Links)
    D_TYPE -->|"1 : *"| AGG_TYPE
    D_DAY -->|"1 : *"| AGG_DAY
    D_HOUR -->|"1 : *"| AGG_HOUR
    D_DAY -->|"1 : *"| AGG_DAYTYPE
    D_TYPE -->|"1 : *"| AGG_DAYTYPE
    D_AMT -->|"1 : *"| AGG_AMTTYPE
    D_TYPE -->|"1 : *"| AGG_AMTTYPE
    D_SRC -->|"1 : *"| AGG_SRC
    D_RISK -->|"1 : *"| AGG_RISK
```

---

## 2. Complete Relationship Master Table (Model View Configuration)

Configure the **15 explicit relationships** below in the Power BI Desktop **Model View**.
Every column named here has been programmatically audited and verified against the underlying CSV files.

| # | From Table [Column] | To Table [Column] | Cardinality | Cross Filter Direction | Active? | Business Purpose |
| :-: | :--- | :--- | :---: | :---: | :---: | :--- |
| 1 | **`Fact_Transactions[type]`** | **`Dim_Type[type]`** | **Many-to-One (*:1)** | **Single (Dim -> Fact)** | **Active** | Core Star Schema: Filters fact table by payment method |
| 2 | **`Fact_Transactions[day]`** | **`Dim_Day[day]`** | **Many-to-One (*:1)** | **Single (Dim -> Fact)** | **Active** | Core Star Schema: Filters fact table by calendar day (Day 01 to Day 31) |
| 3 | **`Fact_Transactions[hour]`** | **`Dim_Hour[hour]`** | **Many-to-One (*:1)** | **Single (Dim -> Fact)** | **Active** | Core Star Schema: Filters fact table by diurnal hour (0 to 23) |
| 4 | **`Fact_Transactions[alert_source]`** | **`Dim_AlertSource[alert_source]`** | **Many-to-One (*:1)** | **Single (Dim -> Fact)** | **Active** | Core Star Schema: Filters fact table by attribution source (Both, Rule only, ML only, None) |
| 5 | **`Fact_Transactions[risk_band]`** | **`Dim_RiskBand[risk_band]`** | **Many-to-One (*:1)** | **Single (Dim -> Fact)** | **Active** | Core Star Schema: Filters fact table by triage risk tier (Critical, High, Medium, Low) |
| 6 | **`Fact_Transactions[amount_band]`** | **`Dim_AmountBand[amount_band]`** | **Many-to-One (*:1)** | **Single (Dim -> Fact)** | **Active** | Core Star Schema: Filters fact table by monetary magnitude (<1K to >1M) |
| 7 | **`Agg_ByType[type]`** | **`Dim_Type[type]`** | **Many-to-One (*:1)** | **Single (Dim -> Agg)** | **Active** | Constellation: Connects full 6.36M type aggregate to payment type slicers |
| 8 | **`Agg_ByDay[day]`** | **`Dim_Day[day]`** | **Many-to-One (*:1)** | **Single (Dim -> Agg)** | **Active** | Constellation: Connects full 6.36M daily temporal aggregate to calendar day slicers |
| 9 | **`Agg_ByHour[hour]`** | **`Dim_Hour[hour]`** | **Many-to-One (*:1)** | **Single (Dim -> Agg)** | **Active** | Constellation: Connects full 6.36M hourly diurnal aggregate to hour/shift slicers |
| 10 | **`Agg_ByDayType[day]`** | **`Dim_Day[day]`** | **Many-to-One (*:1)** | **Single (Dim -> Agg)** | **Active** | Cross-Tabulation Key 1: Connects day-by-type aggregate to calendar day slicers |
| 11 | **`Agg_ByDayType[type]`** | **`Dim_Type[type]`** | **Many-to-One (*:1)** | **Single (Dim -> Agg)** | **Active** | Cross-Tabulation Key 2: Connects day-by-type aggregate to payment type slicers |
| 12 | **`Agg_ByAmountBandType[amount_band]`** | **`Dim_AmountBand[amount_band]`** | **Many-to-One (*:1)** | **Single (Dim -> Agg)** | **Active** | Cross-Tabulation Key 1: Connects amount-band-by-type aggregate to amount band slicers |
| 13 | **`Agg_ByAmountBandType[type]`** | **`Dim_Type[type]`** | **Many-to-One (*:1)** | **Single (Dim -> Agg)** | **Active** | Cross-Tabulation Key 2: Connects amount-band-by-type aggregate to payment type slicers |
| 14 | **`Agg_BySource[alert_source]`** | **`Dim_AlertSource[alert_source]`** | **Many-to-One (*:1)** | **Single (Dim -> Agg)** | **Active** | Attribution Summary: Connects alert attribution aggregate to triage source slicers |
| 15 | **`Agg_ByRiskBand[risk_band]`** | **`Dim_RiskBand[risk_band]`** | **Many-to-One (*:1)** | **Single (Dim -> Agg)** | **Active** | Risk Tier Summary: Connects risk tier aggregate to operational risk slicers |

> [!NOTE]
> In Power BI Desktop's **Create Relationship** dialog, selecting `Fact_Transactions[type]` and `Dim_Type[type]` automatically sets **Cardinality: Many to one (*:1)** and **Cross filter direction: Single**.

---

## 3. Aggregate Table Relationship Strategy & Multi-Dimensional Keys

A common challenge in dimensional modeling is how to connect pre-aggregated summary tables to conforming dimensions without introducing ambiguous circular relationship paths or many-to-many bridges.

### A. Single-Dimension Aggregates (Direct Conforming Links)
- **`Agg_ByType[type]` -> `Dim_Type[type]`:**
  - Grained strictly at the payment type level (5 rows).
  - Slicing by payment method (e.g. selecting `TRANSFER` or `CASH_OUT`) cleanly filters `Agg_ByType` to the selected row, driving donut charts and bar visual totals.
- **`Agg_ByDay[day]` -> `Dim_Day[day]`:**
  - Grained strictly by simulation day (31 rows).
  - Slicers on `Dim_Day` (e.g. Day 01 to Day 15, or calendar week index) filter `Agg_ByDay` cleanly for time-series trendlines.
- **`Agg_ByHour[hour]` -> `Dim_Hour[hour]`:**
  - Grained strictly by diurnal hour (24 rows).
  - Slicers on operational shifts (`time_band` = 'Night' vs. 'Morning') in `Dim_Hour` filter `Agg_ByHour` cleanly.

### B. Multi-Dimension Aggregates: Why Single Keys Fail & How Dual Keys Resolve Them
Certain aggregate tables contain multi-dimensional intersections and cannot be linked to a single dimension alone:

1. **`Agg_ByDayType` (152 rows):**
   - **Grain:** Daily volume and fraud counts cross-tabulated by payment type (`day` + `type`).
   - **Why a single relationship fails:** If you only connect `day`, filtering by `Dim_Type` has no effect on the table. If you only connect `type`, filtering by `Dim_Day` has no effect.
   - **Solution (Dual Many-to-One Relationships):**
     - Relationship 10: `Agg_ByDayType[day]` to `Dim_Day[day]` (Many-to-One, Single, Active).
     - Relationship 11: `Agg_ByDayType[type]` to `Dim_Type[type]` (Many-to-One, Single, Active).
     - **Outcome:** Both dimensions simultaneously filter `Agg_ByDayType`. A user selecting `TRANSFER` in `Dim_Type` AND `Week 1` in `Dim_Day` sees only the transfer transactions for Week 1.

2. **`Agg_ByAmountBandType` (23 rows):**
   - **Grain:** Transaction counts categorized by amount interval and payment type (`amount_band` + `type`).
   - **Solution (Dual Many-to-One Relationships):**
     - Relationship 12: `Agg_ByAmountBandType[amount_band]` to `Dim_AmountBand[amount_band]` (Many-to-One, Single, Active).
     - Relationship 13: `Agg_ByAmountBandType[type]` to `Dim_Type[type]` (Many-to-One, Single, Active).
     - **Outcome:** Enables dynamic matrix cross-tabulation visuals filtered by both magnitude slicers and payment type slicers.

### C. Marginal Enterprise Aggregates: `Agg_BySource` and `Agg_ByRiskBand`
- **`Agg_BySource[alert_source]` -> `Dim_AlertSource[alert_source]`:**
  - Table has 4 rows (`Both`, `Rule only`, `ML only`, `None`).
  - Connects cleanly to `Dim_AlertSource` for attribution prioritization.
  - **Structural Limitation:** Because this table summarizes the entire 6.36M enterprise dataset without temporal coordinates (`day`, `hour`) or `type`, **it cannot and will not be filtered by day, hour, or payment type slicers**. This is mathematically intentional: it represents an immutable global triage breakdown.
- **`Agg_ByRiskBand[risk_band]` -> `Dim_RiskBand[risk_band]`:**
  - Table has 4 rows (`Critical`, `High`, `Medium`, `Low`).
  - Connects cleanly to `Dim_RiskBand` for risk funnel visuals.
  - **Structural Limitation:** Like `Agg_BySource`, it summarizes the full enterprise census. Filtering on Day or Type does not filter `Agg_ByRiskBand`. For filtered risk analysis at the daily or type level, use `Fact_Transactions`.

---

## 4. Strict "Do Not Do" Modeling Rules

To prevent data corruption, incorrect totals, and severe performance degradation, enforce these **three golden rules**:

### 1. NEVER Use Bidirectional Cross-Filtering (Both-Direction)
- **Rule:** Every relationship in Model View must have **Cross filter direction: Single** (Dimension filters Fact or Aggregate). **NEVER change to "Both".**
- **Why:**
  - Bidirectional filtering allows filter context to pass from `Fact_Transactions` back up into other dimension tables.
  - Example of failure: Selecting a specific hour in `Dim_Hour` would filter `Fact_Transactions`, which would then filter `Dim_Type`, which would in turn filter `Agg_ByType`. In a model with multiple fact and aggregate tables, this creates **circular filter loops**, ambiguous query execution plans, invalid DAX context transition, and unpredictable visual results.
  - Pure single-direction filtering guarantees deterministic, top-down filter propagation.

### 2. KEEP `Metrics_*` Tables Disconnected (Standalone)
- **Rule:** Do NOT attempt to wire `Metrics_Overall`, `Metrics_Approach`, `Metrics_Rules`, or `Confusion_Matrix` to any dimension or fact table. Leave them **floating / disconnected** in Model View.
- **Why:**
  - These tables contain immutable model evaluation metrics and enterprise benchmark constants computed across the full 6,362,620 transactions (e.g. F1 scores, AUCPR, precision, false positive rates, 2x2 confusion matrix).
  - They do not have foreign keys to dimensions (e.g. `Metrics_Approach` has strategy names like "Combined AND", not payment types or days).
  - Connecting them to dimensions would require artificial many-to-many bridges, distort benchmark numbers, or produce blank Cartesian rows in executive scorecards.

### 3. DO NOT Use `COUNTROWS(Fact_Transactions)` for Enterprise Total Transactions
- **Rule:** Never use `COUNTROWS(Fact_Transactions)` or `COUNT(Fact_Transactions[txn_id])` to calculate total enterprise volume or overall fraud rates in executive KPI cards.
- **Why:**
  - `Fact_Transactions` is a **sampled fact table** created specifically for fast, interactive desktop report rendering without loading all 6.36 million rows into local RAM.
  - It contains **100% of all alerts and confirmed fraud cases (1,085,626 rows)**, but contains only a **50,000-row stratified sample of legitimate unalerted transactions**.
  - **The Math:**
    - `COUNTROWS(Fact_Transactions)` = **1,135,626** *(Misleading if displayed as total transactions!)*
    - True Enterprise Volume = **6,362,620** transactions.
  - **However, Fraud Counting IS 100% Accurate:**
    - `SUM(Fact_Transactions[isFraud])` = **8,213** *(Exact match to enterprise ground truth, because 100% of fraud was preserved).*
  - **Where to get enterprise totals:** Always source enterprise transaction volume from `SUM(Agg_ByType[total_txns])`, `SUM(Agg_ByDay[total_txns])`, or `Metrics_Overall[total_txns]`.

---

## 5. Visual-to-Table Mapping Matrix (Which Table Feeds What)

To eliminate ambiguity during dashboard page construction, use this definitive visual mapping matrix:

| Dashboard Page / Visual Group | Visual Type | Visual Title | Primary Feeding Table | Slicer Dimensions Supported | DAX Measures / Fields Used | Strategic Rationale |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Executive Overview** | Card / KPI | Total Enterprise Transactions | **`Metrics_Overall`** or **`Agg_ByType`** | None (Global KPI) | `Metrics_Overall[total_txns]` | Must reflect true 6,362,620 census, not sampled fact count. |
| **Executive Overview** | Card / KPI | Total Confirmed Fraud Events | **`Metrics_Overall`** or **`Fact_Transactions`** | `Dim_Type`, `Dim_Day` | `SUM(Fact_Transactions[isFraud])` | Outputs exactly 8,213. Safe on both fact and metric tables. |
| **Executive Overview** | Card / KPI | Global Detection Recall | **`Metrics_Overall`** | None (Global KPI) | `Metrics_Overall[recall_pct]` | Headline 99.79% recall of official Combined OR strategy. |
| **Executive Overview** | Card / KPI | Total Flagged Exposure ($) | **`Metrics_Overall`** or **`Agg_ByType`** | None (Global KPI) | `Metrics_Overall[total_flagged_value]` | Headline $407.88B flagged exposure across enterprise. |
| **Executive Overview** | Donut / Bar | Fraud Volume by Payment Type | **`Agg_ByType`** | `Dim_Type` | `Agg_ByType[fraud_count]`, `Dim_Type[type]` | Sourced from 6.36M full universe: TRANSFER (4,097), CASH_OUT (4,116). |
| **Executive Overview** | Line Chart | 31-Day Transaction & Fraud Trend | **`Agg_ByDay`** | `Dim_Day` | `Agg_ByDay[total_txns]`, `Agg_ByDay[fraud_count]`, `Dim_Day[day_label]` | Sourced from full 6.36M daily census across 31 days. |
| **Temporal Analytics** | Heatmap / Clustered Bar | Hourly Diurnal Surveillance Profile | **`Agg_ByHour`** | `Dim_Hour` | `Agg_ByHour[fraud_count]`, `Agg_ByHour[alert_count]`, `Dim_Hour[hour_label]` | Shows diurnal spikes (e.g. steady fraud occurrence around the clock vs daytime transaction surges). |
| **Temporal Analytics** | Matrix Visual | Day vs. Payment Type Cross-Tab | **`Agg_ByDayType`** | `Dim_Day`, `Dim_Type` | `Agg_ByDayType[fraud_count]`, `Dim_Day[day_label]`, `Dim_Type[type]` | Uses dual-dimension relationships to provide granular daily breakdown by type. |
| **Amount & Exposure** | Stacked Column | Amount Magnitude by Payment Type | **`Agg_ByAmountBandType`** | `Dim_AmountBand`, `Dim_Type` | `Agg_ByAmountBandType[total_txns]`, `Dim_AmountBand[amount_band]` | Dual-dimension visual sorting magnitude intervals <1K to >1M. |
| **Detection Strategy** | Table Visual | Multi-Strategy Benchmark Matrix | **`Metrics_Approach`** | Standalone | All 10 columns in `Metrics_Approach` | Compares Combined AND (F1=0.67), ML only (F1=0.67), Rules (F1=0.015), and baseline. |
| **Detection Strategy** | Matrix Visual | 2x2 Confusion Matrix Quadrant | **`Confusion_Matrix`** | Standalone | Rows: `actual`, Cols: `predicted`, Values: `count`, `pct_of_total` | Reconciles exact TP (8,196), FP (1,077,413), FN (17), TN (5,276,994). |
| **Rule Diagnostics** | Bar Chart / Table | Heuristic Rule Efficacy & Precision | **`Metrics_Rules`** | Standalone | `Metrics_Rules[rule_name]`, `tp`, `fp`, `precision_pct`, `recall_pct` | Benchmarks Rule 1 through Rule 7 hit rates and false alarms. |
| **Alert Triage** | Bar / Donut | Alert Attribution Distribution | **`Agg_BySource`** | `Dim_AlertSource` | `Agg_BySource[alert_count]`, `Dim_AlertSource[alert_source]` | Shows consensus ('Both': 4,224, 98.6% prec), Rule only (1.08M), ML only (55). |
| **Alert Triage** | Funnel / Bar | Operational Risk Tier Pipeline | **`Agg_ByRiskBand`** | `Dim_RiskBand` | `Agg_ByRiskBand[rows]`, `Dim_RiskBand[risk_band]` | Funnel triage: Critical (0), High (3,402; 99.8% fraud), Medium (14,156), Low (6.34M). |
| **Investigator Workbench** | Table / Detail Grid | Granular Alert & Fraud Case Drill-Down | **`Fact_Transactions`** | All 6 Dimensions (`Dim_*`) | `txn_id`, `step`, `type`, `amount`, `nameOrig`, `nameDest`, `alert_score`, `anomaly_score_pct`, `isFraud`, `outcome` | Individual case drilldown. Slices cleanly across all 6 dimensions with sub-second response. |

---

## 6. Programmatic Column & Referential Integrity Verification Report

This document was generated automatically by `src/build_data_model_doc.py`. The table below records the exact verification status for each relationship key:

| # | Relationship Path | Source Table & Column | Target Table & Column | Source Distinct Keys | Target Distinct Keys | Referential Status |
| :-: | :--- | :--- | :--- | --: | --: | :---: |
| 1 | `Fact_Transactions -> Dim_Type` | `Fact_Transactions[type]` | `Dim_Type[type]` | 5 | 5 | **100% PASS (Zero Unmatched)** |
| 2 | `Fact_Transactions -> Dim_Day` | `Fact_Transactions[day]` | `Dim_Day[day]` | 31 | 31 | **100% PASS (Zero Unmatched)** |
| 3 | `Fact_Transactions -> Dim_Hour` | `Fact_Transactions[hour]` | `Dim_Hour[hour]` | 24 | 24 | **100% PASS (Zero Unmatched)** |
| 4 | `Fact_Transactions -> Dim_AlertSource` | `Fact_Transactions[alert_source]` | `Dim_AlertSource[alert_source]` | 4 | 4 | **100% PASS (Zero Unmatched)** |
| 5 | `Fact_Transactions -> Dim_RiskBand` | `Fact_Transactions[risk_band]` | `Dim_RiskBand[risk_band]` | 3 | 4 | **100% PASS (Zero Unmatched)** |
| 6 | `Fact_Transactions -> Dim_AmountBand` | `Fact_Transactions[amount_band]` | `Dim_AmountBand[amount_band]` | 5 | 5 | **100% PASS (Zero Unmatched)** |
| 7 | `Agg_ByType -> Dim_Type` | `Agg_ByType[type]` | `Dim_Type[type]` | 5 | 5 | **100% PASS (Zero Unmatched)** |
| 8 | `Agg_ByDay -> Dim_Day` | `Agg_ByDay[day]` | `Dim_Day[day]` | 31 | 31 | **100% PASS (Zero Unmatched)** |
| 9 | `Agg_ByHour -> Dim_Hour` | `Agg_ByHour[hour]` | `Dim_Hour[hour]` | 24 | 24 | **100% PASS (Zero Unmatched)** |
| 10 | `Agg_ByDayType -> Dim_Day` | `Agg_ByDayType[day]` | `Dim_Day[day]` | 31 | 31 | **100% PASS (Zero Unmatched)** |
| 11 | `Agg_ByDayType -> Dim_Type` | `Agg_ByDayType[type]` | `Dim_Type[type]` | 5 | 5 | **100% PASS (Zero Unmatched)** |
| 12 | `Agg_ByAmountBandType -> Dim_AmountBand` | `Agg_ByAmountBandType[amount_band]` | `Dim_AmountBand[amount_band]` | 5 | 5 | **100% PASS (Zero Unmatched)** |
| 13 | `Agg_ByAmountBandType -> Dim_Type` | `Agg_ByAmountBandType[type]` | `Dim_Type[type]` | 5 | 5 | **100% PASS (Zero Unmatched)** |
| 14 | `Agg_BySource -> Dim_AlertSource` | `Agg_BySource[alert_source]` | `Dim_AlertSource[alert_source]` | 4 | 4 | **100% PASS (Zero Unmatched)** |
| 15 | `Agg_ByRiskBand -> Dim_RiskBand` | `Agg_ByRiskBand[risk_band]` | `Dim_RiskBand[risk_band]` | 4 | 4 | **100% PASS (Zero Unmatched)** |

---
*Report generated programmatically from CSV headers and data contents by `src/build_data_model_doc.py`.*