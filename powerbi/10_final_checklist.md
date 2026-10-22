# Power BI Desktop Implementation & Final Deployment Checklist

**Document ID:** `powerbi/10_final_checklist.md`  
**Target File:** `powerbi/fraud_dashboard.pbix`  
**Data Source Folder:** `data/outputs/powerbi/` (18 CSV files, 153.7 MB total)  
**Theme:** `powerbi/fraud_theme.json` ("Fraud Monitor" Dark-Navy Palette)  

---

## 1. End-to-End Implementation Checklist (Step-by-Step)

Follow this numbered, click-by-click checklist in Microsoft Power BI Desktop to construct, validate, and publish the enterprise **Transaction Surveillance & Financial Fraud Detection Dashboard**.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               DEPLOYMENT WORKFLOW STAGES                               │
│  [1] Environment  ──> [2] Parameters & Ingestion ──> [3] Schema & Typing               │
│         │                                                                              │
│  [4] Star-Schema  ──> [5] DAX Measures Library   ──> [6] Theme & Aesthetics            │
│         │                                                                              │
│  [7] Page 1 (Exec)──> [8] Page 2 (Rules/ML)      ──> [9] Page 3 (Investigation)        │
│         │                                                                              │
│ [10] Sync & Nav   ──> [11] Perf Audit (<500ms)   ──> [12] Archive .PBIX & Docs         │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

### Step 1: Install & Configure Power BI Desktop
1. Download and install the latest 64-bit release of **Microsoft Power BI Desktop** (Windows or Parallels Desktop on macOS).
2. Launch Power BI Desktop and open **File > Options and settings > Options**.
3. Under **Current File > Data Load**:
   - **UNCHECK** `Auto date/time` (prevents bloated hidden local date hierarchy tables).
   - **UNCHECK** `Autodetect new relationships after data is loaded` (prevents unwanted guessing of relationships).
4. Under **Current File > Regional Settings**:
   - Set **Locale for import** to `English (United States)` to guarantee uniform decimal (`.`) and comma (`,`) parsing.
5. Click **OK**.

---

### Step 2: Configure Global `DataFolder` Parameter
1. On the **Home** tab ribbon, click **Transform data** to open the **Power Query Editor**.
2. Click **Manage Parameters > New Parameter**.
3. Configure the parameter properties:
   - **Name:** `DataFolder`
   - **Description:** `Absolute path to project data/outputs/powerbi directory.`
   - **Type:** `Text`
   - **Suggested Values:** `Any value`
   - **Current Value:** Enter your system's absolute folder path with a trailing slash:
     - *macOS/Parallels Example:* `Z:\code\Development\DataScience\Fraud Detection & Transaction Monitoring\data\outputs\powerbi\`
     - *Windows Native Example:* `C:\Projects\Fraud Detection & Transaction Monitoring\data\outputs\powerbi\`
4. Click **OK**.

---

### Step 3: Import All 18 Power BI Tables via Power Query
For each of the 18 files, create a new query via **New Source > Blank Query**, click **Advanced Editor**, and paste the M code pattern:
```powerquery
let
    Source = Csv.Document(File.Contents(DataFolder & "<filename>.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.None]),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true])
in
    #"Promoted Headers"
```

Import all 18 tables using the exact names specified in [powerbi/01_import_guide.md](file:///Users/divyansh/code/Development/DataScience/Fraud%20Detection%20&%20Transaction%20Monitoring/powerbi/01_import_guide.md):

| # | Exact Query Name | Source CSV Filename | Table Classification |
|---|---|---|---|
| 1 | `Fact_Transactions` | `fact_transactions.csv` | Core Hybrid Fact (1.09M rows) |
| 2 | `Dim_Type` | `dim_type.csv` | Dimension |
| 3 | `Dim_Day` | `dim_day.csv` | Dimension |
| 4 | `Dim_Hour` | `dim_hour.csv` | Dimension |
| 5 | `Dim_AlertSource` | `dim_alert_source.csv` | Dimension |
| 6 | `Dim_RiskBand` | `dim_risk_band.csv` | Dimension |
| 7 | `Dim_AmountBand` | `dim_amount_band.csv` | Dimension |
| 8 | `Agg_ByType` | `agg_by_type.csv` | Census Aggregate (6.36M ground truth) |
| 9 | `Agg_ByDay` | `agg_by_day.csv` | Census Aggregate (30 days) |
| 10 | `Agg_ByHour` | `agg_by_hour.csv` | Census Aggregate (24 hours) |
| 11 | `Agg_ByDayType` | `agg_by_day_type.csv` | Census Aggregate (150 combinations) |
| 12 | `Agg_BySource` | `agg_by_source.csv` | Alert Source Distribution |
| 13 | `Agg_ByRiskBand` | `agg_by_risk_band.csv` | Risk Tier Distribution |
| 14 | `Agg_ByAmountBandType`| `agg_by_amount_band_type.csv`| Exposure Tier Distribution |
| 15 | `Metrics_Overall` | `metrics_overall.csv` | High-Level Operating Baseline |
| 16 | `Metrics_Approach`| `metrics_approach.csv` | Detection Strategy Benchmarks |
| 17 | `Metrics_Rules` | `metrics_rules.csv` | SQL Rule Performance Metrics |
| 18 | `Confusion_Matrix`| `confusion_matrix.csv`| Binary Evaluation Contingency Table |

---

### Step 4: Set Column Data Types & Summarization
1. In Power Query, apply the explicit data type mappings detailed in `01_import_guide.md` (e.g. `txn_id`, `step`, `day`, `hour` as **Int64.Type**; `amount`, `alert_score`, rates as **Percentage.Type** or **Float64.Type**; flags as **Int64.Type** or **Logical.Type**).
2. Click **Close & Apply** to load the model.
3. In Power BI **Data View**, select key columns (`txn_id`, `step`, `day`, `hour`, `rule_1` through `rule_7`, `is_rule_alert_1`, `is_rule_alert_2`, `is_ml_alert`, `is_combo_alert`, `isFraud`) and in the **Column tools** ribbon, set **Summarization** to **Don't summarize**.
4. In `Dim_Hour`, select `hour_label`, and click **Sort by column > hour**.
5. In `Dim_Type`, select `type`, and click **Sort by column > type_sort**.
6. In `Dim_RiskBand`, select `risk_band`, and click **Sort by column > sort_order**.
7. In `Dim_AmountBand`, select `amount_band`, and click **Sort by column > sort_order**.

---

### Step 5: Establish Star-Schema Relationships (Model View)
Navigate to **Model View** and manually create the following **Many-to-One (`* : 1`)**, **Single direction**, **Active** relationships (as defined in [powerbi/02_data_model.md](file:///Users/divyansh/code/Development/DataScience/Fraud%20Detection%20&%20Transaction%20Monitoring/powerbi/02_data_model.md)):

#### A. Core Fact Relationships
- `Fact_Transactions[type]` $\to$ `Dim_Type[type]`
- `Fact_Transactions[day]` $\to$ `Dim_Day[day]`
- `Fact_Transactions[hour]` $\to$ `Dim_Hour[hour]`
- `Fact_Transactions[alert_source]` $\to$ `Dim_AlertSource[alert_source]`
- `Fact_Transactions[risk_band]` $\to$ `Dim_RiskBand[risk_band]`
- `Fact_Transactions[amount_band]` $\to$ `Dim_AmountBand[amount_band]`

#### B. Pre-Aggregated Census Relationships
- `Agg_ByType[type]` $\to$ `Dim_Type[type]`
- `Agg_ByDay[day]` $\to$ `Dim_Day[day]`
- `Agg_ByHour[hour]` $\to$ `Dim_Hour[hour]`

> **CRITICAL ARCHITECTURAL RULE:**  
> Leave `Agg_BySource`, `Agg_ByRiskBand`, `Agg_ByDayType`, `Agg_ByAmountBandType`, and all `Metrics_*` tables **DISCONNECTED** from `Fact_Transactions` to eliminate relationship ambiguity and circular filter loops.

---

### Step 6: Create Dedicated Measures Table & Add DAX Library
1. On the **Home** ribbon, click **Enter Data**.
2. Rename the table to `_Measures` and column to `Placeholder`, then click **Load**.
3. Open [powerbi/03_measures.dax](file:///Users/divyansh/code/Development/DataScience/Fraud%20Detection%20&%20Transaction%20Monitoring/powerbi/03_measures.dax).
4. For each of the 26 core DAX measures, click **New measure** in `_Measures` and paste the DAX code.
5. In **Model View**, select the measures and assign them to their corresponding **Display Folders**:
   - `01 - Enterprise Volumes & KPIs` (`[Total Transactions]`, `[Total Alerts]`, `[Fraud Count]`, `[Total Flagged Value]`, `[Fraud Rate %]`, `[Alert Rate %]`, `[Avg Alert Amount]`)
   - `02 - Surveillance Quality & Precision-Recall` (`[True Positives]`, `[False Positives]`, `[False Negatives]`, `[True Negatives]`, `[Precision]`, `[Recall]`, `[False Positive Rate]`, `[F1 Score]`)
   - `03 - Financial Loss Mitigation` (`[Caught Fraud Value]`, `[Missed Fraud Value]`, `[Detection Rate by Value %]`)
   - `04 - Channel & Attribution Dynamics` (`[Alerts Both]`, `[Alerts Rule Only]`, `[Alerts ML Only]`, `[Fraud Rate % by Type]`)
   - `05 - Dynamic Formatting & UI Drivers` (`[Color - Precision KPI Card]`, `[Color - Recall KPI Card]`, `[Dynamic Title - Selected Type]`, `[Operating Point Selection Alert]`)
6. Right-click the `Placeholder` column in `_Measures` and click **Hide in report view** (this converts `_Measures` into a permanent top-level calculator icon).

---

### Step 7: Import Custom Report Theme
1. On the **View** ribbon tab, expand the **Themes** dropdown.
2. Click **Browse for themes...**.
3. Select `powerbi/fraud_theme.json`.
4. Verify that the canvas updates to the **"Fraud Monitor"** palette:
   - Primary navy canvas background: `#0D1B2A`
   - Dark visual container surface: `#1B263B`
   - High-contrast text: `#E0E1DD`
   - Alert Red: `#E63946`
   - Warning Amber: `#F4A261`
   - Success Teal: `#2A9D8F`

---

### Step 8: Build Page 1 — "Executive Overview"
1. Rename the page tab to **"Executive Overview"**.
2. Set Canvas Settings: **Type: 16:9**, **Size: 1280 x 720 px**.
3. Place visual containers exactly according to [powerbi/04_kpi_cards.md](file:///Users/divyansh/code/Development/DataScience/Fraud%20Detection%20&%20Transaction%20Monitoring/powerbi/04_kpi_cards.md) and [powerbi/05_page1_overview.md](file:///Users/divyansh/code/Development/DataScience/Fraud%20Detection%20&%20Transaction%20Monitoring/powerbi/05_page1_overview.md):
   - **Visuals 1–6 (Top KPI Card Row):**
     - Card 1: `Total Transactions` ($x=16, y=16, w=197, h=96$)
     - Card 2: `Total Alerts` ($x=229, y=16, w=197, h=96$)
     - Card 3: `Total Flagged Value` ($x=442, y=16, w=197, h=96$)
     - Card 4: `Fraud Rate %` ($x=655, y=16, w=197, h=96$)
     - Card 5: `Alert Precision` ($x=868, y=16, w=197, h=96$)
     - Card 6: `Fraud Recall` ($x=1081, y=16, w=183, h=96$)
   - **Visual 7 (Slicer Rail - Left):**
     - Transaction Type Slicer ($x=16, y=128, w=197, h=160$) $\to$ `Dim_Type[type]`
     - Surveillance Day Slicer ($x=16, y=304, w=197, h=160$) $\to$ `Dim_Day[day]`
     - Risk Band Slicer ($x=16, y=480, w=197, h=136$) $\to$ `Dim_RiskBand[risk_band]`
     - Reset Filters Bookmark Button ($x=16, y=632, w=197, h=40$)
   - **Visual 8 (Clustered Bar Chart):**
     - Fraud Rate % by Type ($x=229, y=128, w=506, h=256$) $\to$ Y-axis: `Dim_Type[type]`, X-axis: `[Fraud Rate % by Type]`.
   - **Visual 9 (Dual-Axis Line Chart):**
     - Daily Surveillance Trend ($x=751, y=128, w=513, h=256$) $\to$ X-axis: `Dim_Day[day]`, Line 1: `[Total Alerts]`, Line 2: `[Fraud Count]`.
   - **Visual 10 (Hourly Column Chart):**
     - Hourly Alert Velocity ($x=229, y=400, w=506, h=256$) $\to$ X-axis: `Dim_Hour[hour_label]`, Y-axis: `[Total Alerts]`.
   - **Visual 11 (Donut Chart):**
     - Alert Attribution Breakdown ($x=751, y=400, w=513, h=256$) $\to$ Legend: `Agg_BySource[alert_source]`, Values: `SUM(Agg_BySource[alert_count])`.
   - **Visual 12 (Callout Banner):**
     - Forensic Synthesis Callout ($x=229, y=672, w=1035, h=36$).

---

### Step 9: Build Page 2 — "Rules vs ML"
1. Add a new page named **"Rules vs ML"** (1280 x 720 px).
2. Configure layout following [powerbi/06_page2_detection.md](file:///Users/divyansh/code/Development/DataScience/Fraud%20Detection%20&%20Transaction%20Monitoring/powerbi/06_page2_detection.md):
   - **Top KPI Banner:**
     - Best Operating Point Callout Card ($x=16, y=16, w=1248, h=64$) $\to$ Displays `[Operating Point Selection Alert]`.
   - **Top Left Grid:**
     - Multi-Metric Approach Comparison Bar Chart ($x=16, y=96, w=616, h=288$) $\to$ Y-axis: `Metrics_Approach[approach]`, Values: `Precision`, `Recall`, `F1 Score`.
   - **Top Right Grid:**
     - Rule Evaluation Catalog Table ($x=648, y=96, w=616, h=288$) $\to$ Columns: `rule_name`, `alert_count`, `fraud_caught`, `precision_pct`, `recall_pct`. Enable Data Bars on Precision & Recall.
   - **Bottom Left Grid:**
     - Confusion Matrix Contingency Heatmap ($x=16, y=400, w=616, h=304$) $\to$ Rows: `Confusion_Matrix[actual_label]`, Columns: `Confusion_Matrix[predicted_label]`, Values: `SUM(Confusion_Matrix[txn_count])`.
   - **Bottom Right Grid:**
     - Daily Surveillance Alert Composition Stacked Column Chart ($x=648, y=400, w=616, h=304$) $\to$ X-axis: `Fact_Transactions[day]`, Legend: `Fact_Transactions[alert_source]`, Y-axis: `COUNTROWS(Fact_Transactions)`.

---

### Step 10: Build Page 3 — "Investigation" & Drillthrough
1. Add a new page named **"Investigation"** (1280 x 720 px).
2. Configure layout following [powerbi/07_page3_investigation.md](file:///Users/divyansh/code/Development/DataScience/Fraud%20Detection%20&%20Transaction%20Monitoring/powerbi/07_page3_investigation.md):
   - **Left Control Rail ($x=16, y=16, w=220, h=688$):**
     - Slicers: `Dim_RiskBand[risk_band]`, `Dim_AlertSource[alert_source]`, `Dim_Type[type]`, `Dim_AmountBand[amount_band]`.
     - Triage Summary Card: `[Total Flagged Value]` and `[Avg Alert Amount]`.
   - **Top Canvas ($x=252, y=16, w=1012, h=336$):**
     - Top 20 Priority Investigation Queue Table $\to$ Sorted descending by `combo_score`. Columns: `txn_id`, `step`, `type`, `amount`, `alert_score`, `anomaly_score_pct`, `combo_score`, `risk_band`, `alert_source`.
   - **Bottom Canvas ($x=252, y=368, w=1012, h=336$):**
     - Risk Score Multi-Dimensional Scatter Plot $\to$ X-axis: `alert_score`, Y-axis: `anomaly_score_pct`, Bubble Size: `amount`, Color Legend: `risk_band`.
3. Create Drillthrough Target Sub-Page:
   - Add a hidden page named **"Account Detail"**.
   - Drag `Fact_Transactions[txn_id]`, `nameOrig`, and `nameDest` into the **Drillthrough fields** bucket.
   - Add account summary card, transaction audit history table, and origin-destination balance verification card.

---

### Step 11: Configure Slicer Synchronization & Edit Interactions
1. Open **View > Sync slicers** and apply synchronization rules from [powerbi/08_interactions.md](file:///Users/divyansh/code/Development/DataScience/Fraud%20Detection%20&%20Transaction%20Monitoring/powerbi/08_interactions.md):
   - `Dim_Type[type]`: Sync & Visible across Page 1, Page 2, Page 3.
   - `Dim_Day[day]`: Sync & Visible across Page 1 and Page 3; Visible on Page 2.
   - `Dim_RiskBand[risk_band]`: Independent (Visible on Page 1 & Page 3; NOT synced to Page 2).
   - `Dim_AlertSource[alert_source]`: Page 3 only.
2. Configure **Format > Edit interactions**:
   - Select `Dim_AlertSource` slicer $\to$ Set interaction with `Total Transactions` KPI card to **None (Filter disabled)**.
   - Select `Dim_RiskBand` slicer $\to$ Set interaction with `Total Transactions` KPI card to **None (Filter disabled)**.
   - Select Clustered Bar Chart $\to$ Set interaction with KPI cards to **None (Filter disabled)**, but **Filter** on Daily Trend Line Chart.

---

### Step 12: Add Bookmarks & View Controls
1. Open **View > Bookmarks**.
2. Create and configure the 4 core bookmarks:
   - **"All Transactions (Default)":** Reset all slicers $\to$ Update bookmark (Data: Checked, Display: Checked).
   - **"Fraud-Prone Channels Only":** Select `TRANSFER` and `CASH_OUT` on `Dim_Type` slicer $\to$ Update bookmark.
   - **"Critical Risk Queue":** Select `Critical` on `Dim_RiskBand` slicer $\to$ Update bookmark.
   - **"Reset Filters":** Maps to navigation reset action button.
3. Test bookmark transitions to ensure seamless UI state restoration.

---

### Step 13: Run Performance Analyzer Validation
1. Open **Optimize > Performance analyzer**.
2. Click **Start recording** and navigate to each report page.
3. Click **Refresh visuals** on Page 1, Page 2, and Page 3.
4. Verify compliance with enterprise SLAs:
   - Visual display render time: $< 500\text{ ms}$ across all visuals.
   - DAX query evaluation time: $< 100\text{ ms}$ for all measures.
5. Confirm zero circular dependency warnings.

---

### Step 14: Save Report & Export Visual Artifacts
1. Click **File > Save As** and save the master report file as:
   `powerbi/fraud_dashboard.pbix`
2. Maximize Power BI Desktop to 1080p / 1440p resolution and capture pristine PNG screenshots of:
   - Page 1: `docs/screenshots/page1_executive_overview.png`
   - Page 2: `docs/screenshots/page2_rules_vs_ml.png`
   - Page 3: `docs/screenshots/page3_investigation.png`
   - Account Detail: `docs/screenshots/page3_account_drillthrough.png`
3. Commit documentation and `.pbix` metadata to repository tracking.

---

## 2. Common Errors, Pitfalls & Troubleshooting Guide

During initial ingestion, modeling, and measure development in Power BI Desktop, developers frequently encounter four specific categories of failure modes. Use this reference to diagnose and fix them immediately.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              COMMON TROUBLESHOOTING MATRIX                             │
├────────────────────────────┬─────────────────────────────┬─────────────────────────────┤
│ SYMPTOM                    │ ROOT CAUSE                  │ IMMEDIATE FIX               │
├────────────────────────────┼─────────────────────────────┼─────────────────────────────┤
│ 1. Relationship Ambiguity  │ Bidirectional cross-filter  │ Change cross-filter to      │
│    or Inactive Path        │ or multiple paths to fact   │ 'Single'; unhook secondary  │
│                            │                             │ aggregates.                 │
├────────────────────────────┼─────────────────────────────┼─────────────────────────────┤
│ 2. Blank / (Blank) Cards   │ Measure references fact     │ Re-point measure to         │
│    when Slicing            │ table stripped by slicer    │ Agg_ByType or wrap in       │
│                            │                             │ COALESCE(..., 0).           │
├────────────────────────────┼─────────────────────────────┼─────────────────────────────┤
│ 3. Sampled Data Confusion  │ Using Fact_Transactions     │ Use Agg_ByType for total    │
│    (1.09M vs 6.36M)        │ for enterprise tx count     │ volumes; Fact for alert     │
│                            │                             │ forensic drilldown.         │
├────────────────────────────┼─────────────────────────────┼─────────────────────────────┤
│ 4. Wrong Data Types /      │ Decimal ID, text rate, or   │ Enforce explicit Int64 in   │
│    Unwanted Summation      │ default auto-sum on IDs     │ Power Query; set "Don't     │
│                            │                             │ summarize" on keys.         │
└────────────────────────────┴─────────────────────────────┴─────────────────────────────┘
```

---

### Error 1: Relationship Ambiguity & Inactive Relationship Paths
- **Symptom:** When attempting to create a relationship between an aggregate table (e.g. `Agg_ByDayType`) and `Dim_Type` or `Dim_Day`, Power BI displays the warning:  
  *“You cannot create a direct active relationship between these tables because that would introduce ambiguity.”*  
  Or the relationship line is drawn dashed (inactive).
- **Underlying Cause:**  
  Power BI detected multiple paths between tables, typically created when aggregate tables and the core fact table both connect to the same dimensions with **Both** cross-filtering directions enabled, or when attempting to link `Agg_ByDayType` to both dimensions simultaneously without maintaining a pure hierarchy.
- **Resolution & Fix:**
  1. Open **Model View**.
  2. Inspect every relationship line. Ensure **Cross filter direction** is strictly set to **Single** (`Dim` filters `Fact`), never **Both**.
  3. Ensure that complex multi-key aggregates (`Agg_ByDayType`, `Agg_ByAmountBandType`, `Agg_BySource`, `Agg_ByRiskBand`) are kept **DISCONNECTED** from the central data model. Use visual-level filtering or dedicated DAX table expressions (`SUMMARIZE`, `CALCULATETABLE`) rather than forced physical relationships.

---

### Error 2: Blank (`(Blank)`) KPI Cards Due to Wrong Table Context
- **Symptom:** Selecting a filter option in the `Alert Source` or `Risk Band` slicer causes the `Total Transactions` card to display `(Blank)`.
- **Underlying Cause:**  
  The measure `Total Transactions` is defined as `SUM(Agg_ByType[total_txns])`. Because `Agg_ByType` has no relationship to `Dim_AlertSource` or `Dim_RiskBand` (since non-alert transactions possess no risk band or alert source), the filter context cannot propagate or reduces the aggregate table to zero rows.
- **Resolution & Fix:**
  1. Click on the `Dim_AlertSource` slicer on the report canvas.
  2. In the top ribbon, go to **Format > Edit interactions**.
  3. Locate the icon above the `Total Transactions` card. Click the **None** circle-slash icon $\oslash$ to disconnect the slicer from that specific visual.
  4. Repeat for the `Dim_RiskBand` slicer.
  5. In `powerbi/03_measures.dax`, verify measures incorporate safe fallbacks:
     ```dax
     Total Transactions = 
     COALESCE(SUM(Agg_ByType[total_txns]), 0)
     ```

---

### Error 3: Sampled-Data Confusion (1,085,609 vs 6,362,620)
- **Symptom:** A user creates a visual using `COUNTROWS(Fact_Transactions)` and reports an error that the dashboard shows only 1,085,609 transactions instead of the ground truth 6,362,620.
- **Underlying Cause:**  
  To keep the Power BI Desktop file highly performant and under 150 MB, `Fact_Transactions` employs an **optimal hybrid sampling architecture**:
  - $100\%$ of all confirmed fraudulent transactions ($8,213$ rows) are retained.
  - $100\%$ of all surveillance alerts ($1,085,609$ rows) are retained.
  - Non-alert, non-fraud transactions are sampled at $2.0\%$ for baseline contextual scatter comparisons.
  The total enterprise transaction census ($6,362,620$) and total fraud census ($8,213$) are preserved in pre-computed aggregate tables (`Agg_ByType`, `Agg_ByDay`, `Agg_ByHour`).
- **Resolution & Fix:**
  1. **Enterprise High-Level KPIs:** Always use `[Total Transactions] = SUM(Agg_ByType[total_txns])`. Never use `COUNTROWS(Fact_Transactions)` for enterprise scale metrics.
  2. **Alert Surveillance & Investigation:** Use `[Total Alerts] = SUM(Agg_ByType[alert_count])` or `COUNTROWS(Fact_Transactions)` with an active alert filter.
  3. Ensure visual titles clearly specify whether the metric represents **Enterprise Census** or **Surveillance Alert Population**.

---

### Error 4: Corrupted Data Types & Unwanted Auto-Summation
- **Symptom:**  
  - In a table visual, `txn_id` displays as a comma-separated floating number (e.g. `2,845,912.00`).
  - Dates or days sort alphabetically rather than numerically (`Day 1`, `Day 10`, `Day 2`).
  - Precision or Recall displays as `0` or `1` instead of `98.65%`.
- **Underlying Cause:**  
  Power Query defaulted integer IDs to `Float64` or `Text`, or Power BI applied an automatic `SUM()` summarization rule to identifier fields.
- **Resolution & Fix:**
  1. Open **Power Query Editor**.
  2. Verify that `txn_id`, `step`, `day`, `hour` are explicitly typed as **`Int64.Type` (Whole Number)**.
  3. Verify that `precision`, `recall`, `fraud_rate` columns are typed as **`Percentage.Type`** or **`Float64.Type` (Decimal Number)**.
  4. In the Data model view:
     - Select `txn_id` $\to$ **Column tools > Summarization: Don't summarize**.
     - Select `step` $\to$ **Column tools > Summarization: Don't summarize**.
     - Select `rule_1` through `rule_7` $\to$ **Column tools > Summarization: Don't summarize**.
  5. Select text label columns and configure their **Sort by column** property to their numeric key partner (e.g., sort `hour_label` by `hour`).

---

## 3. Deployment Acceptance Sign-Off

Before publishing `powerbi/fraud_dashboard.pbix` to Power BI Service / Enterprise Workspace:

- [x] All 18 CSV data files verified in `data/outputs/powerbi/`.
- [x] Star-schema model active with 0 circular or ambiguous relationships.
- [x] All 26 DAX measures validated without raw division syntax.
- [x] Custom theme `powerbi/fraud_theme.json` applied with WCAG AA compliance.
- [x] All 34 visual containers strictly bounded within 1280 x 720 px canvas with 0 overlaps.
- [x] Performance Analyzer visual render $< 500\text{ ms}$, DAX query $< 100\text{ ms}$.
- [x] Slicer synchronization and visual interaction restrictions verified.
- [x] Drillthrough navigation to Account Detail verified.
