# Page 1: Executive Overview — Comprehensive Visual Specification

**Document ID:** `powerbi/05_page1_overview.md`  
**Report Page Name:** `Executive Overview`  
**Canvas Size:** 1280 x 720 pixels (16:9 Standard HD)  
**Target Audience:** Head of Financial Crime, Chief Risk Officer (CRO), ML & Surveillance Leads  
**Verification Status:** Collision-free, bounding-box validated (PASS: Zero overlaps, 100% within canvas bounds).  

---

## Table of Contents
1. [Page Layout Architecture & Visual Wireframe](#1-page-layout-architecture--visual-wireframe)
2. [Master Visual Specification Table](#2-master-visual-specification-table)
3. [Detailed Specifications by Visual](#3-detailed-specifications-by-visual)
   - [Header: 6 Executive KPI Cards](#header-6-executive-kpi-cards)
   - [Sidebar: Takeaway Brief & Slicer Panel](#sidebar-takeaway-brief--slicer-panel)
   - [Canvas Row 1: Fraud Concentration Bar & Daily Trend Line](#canvas-row-1-fraud-concentration-bar--daily-trend-line)
   - [Canvas Row 2: Diurnal Hourly Column & Attribution Donut](#canvas-row-2-diurnal-hourly-column--attribution-donut)
4. [Slicer Decoupling & Visual Interaction Rules](#4-slicer-decoupling--visual-interaction-rules)
5. [Programmatic Overlap & Boundary Verification Audit](#5-programmatic-overlap--boundary-verification-audit)

---

## 1. Page Layout Architecture & Visual Wireframe

The layout utilizes a structured **Top Header + Left Rail + 2x2 Content Grid** composition.
Every visual is spaced with consistent 16 px margins and gutters, maximizing analytical scannability.

```text
+--------------------------------------------------------------------------------------------------------------------------+
|                                              CANVAS: 1280 x 720 PIXELS                                                   |
+--------------------------------------------------------------------------------------------------------------------------+
| [VIS-01A: Transactions] [VIS-01B: Alerts] [VIS-01C: Flagged $] [VIS-01D: Fraud Rate] [VIS-01E: Precision] [VIS-01F: Recall]  | (y=16..116)
+-----------------------+----------------------------------------------------+---------------------------------------------+
| [VIS-02: Briefing]    | [VIS-04: Clustered Bar Chart]                      | [VIS-05: Line Chart (Dual Axis)]            | (y=128..404)
| 100% fraud in         | Fraud Rate % by Transaction Type                   | Daily Surveillance Trend                    |
| TRANSFER & CASH_OUT   | (TRANSFER: 0.769%, CASH_OUT: 0.184%, Others: 0%)   | Alerts (Primary Axis) vs Fraud Count (Sec)  |
| (x=16, w=220, h=140)  | (x=252, w=498, h=276)                              | (x=766, w=498, h=276)                       |
|-----------------------+----------------------------------------------------+---------------------------------------------+
| [VIS-03A: Type Slicer]| [VIS-06: Column Chart]                             | [VIS-07: Donut Chart]                       | (y=420..704)
| [VIS-03B: Day Slider] | Diurnal Hourly Surveillance Profile                | Alert Triage Attribution                    |
| [VIS-03C: Source Sl.] | Alerts by Hour of Day (00:00 to 23:00)             | Consensus (Both) vs Rules vs ML Only        |
| [VIS-03D: Amount Sl.] | (x=252, w=498, h=284)                              | (x=766, w=498, h=284)                       |
+-----------------------+----------------------------------------------------+---------------------------------------------+
```

---

## 2. Master Visual Specification Table

The table below details every visual container to instantiate on Page 1. All field names reference strictly verified columns in the semantic data model.

| Visual ID | Type | Title | Fields (Axis, Values, Legend) | Tables & Measures Used | X | Y | W | H | Sorting | Formatting Notes |
| :--- | :--- | :--- | :--- | :--- | --: | --: | --: | --: | :--- | :--- |
| **`VIS-01A`** | `Card (or Card new)` | **Total Transactions** | `Values: _Measures[Total Transactions]` | `_Measures[Total Transactions], Agg_ByType[total_txns]` | `16` | `16` | `195` | `100` | N/A (Card) | Callout: 24 pt Bold #0F172A, Label: 11 pt Semibold #64748B, Border: 1px #E2E8F0. Sourced from 6.36M census. |
| **`VIS-01B`** | `Card (or Card new)` | **Total Alerts** | `Values: _Measures[Total Alerts]` | `_Measures[Total Alerts], Agg_ByType[alert_count]` | `227` | `16` | `195` | `100` | N/A (Card) | Callout: 24 pt Bold Accent Navy #1E3A8A, Label: 11 pt Semibold #64748B. Displays 1,085,609 official alerts. |
| **`VIS-01C`** | `Card (or Card new)` | **Total Flagged Value** | `Values: _Measures[Total Flagged Value]` | `_Measures[Total Flagged Value], Agg_ByType[flagged_value]` | `438` | `16` | `194` | `100` | N/A (Card) | Format: $0.00B (Display Units: Billions). Callout: 24 pt Bold #0F172A. Displays $407.88B flagged. |
| **`VIS-01D`** | `Card (or Card new)` | **Fraud Rate %** | `Values: _Measures[Fraud Rate %]` | `_Measures[Fraud Rate %], Agg_ByType[fraud_count], Agg_ByType[total_txns]` | `648` | `16` | `194` | `100` | N/A (Card) | Format: 0.000%. Callout: 24 pt Bold #0F172A. Displays 0.129% baseline enterprise prevalence. |
| **`VIS-01E`** | `Card (or Card new)` | **Alert Precision** | `Values: _Measures[Precision]` | `_Measures[Precision], _Measures[Color - Precision KPI Card], Agg_ByType[tp], Agg_ByType[fp]` | `858` | `16` | `195` | `100` | N/A (Card) | Conditional Color: _Measures[Color - Precision KPI Card] (Green >= 90%, Amber >= 50%, Red < 50%). Output: 0.75%. |
| **`VIS-01F`** | `Card (or Card new)` | **Fraud Recall** | `Values: _Measures[Recall]` | `_Measures[Recall], _Measures[Color - Recall KPI Card], Agg_ByType[tp], Agg_ByType[fn]` | `1069` | `16` | `195` | `100` | N/A (Card) | Conditional Color: _Measures[Color - Recall KPI Card] (Green >= 99%, Amber >= 90%, Red < 90%). Output: 99.79%. |
| **`VIS-02`** | `Text Box (Callout Card)` | **SURVEILLANCE INTELLIGENCE BRIEF** | `Static takeaway text with computed metrics` | `reports/16_final_metrics.json (Static Text)` | `16` | `128` | `220` | `140` | N/A | Background: #F8FAFC, Border: 1px #E2E8F0, Radius: 6px. Text: 10.5 pt Segoe UI dark slate #1E293B, bold metric callouts. |
| **`VIS-03A`** | `Slicer (Tile / Vertical)` | **Payment Method** | `Field: Dim_Type[type]` | `Dim_Type[type], Dim_Type[type_sort]` | `16` | `280` | `220` | `100` | Dim_Type[type_sort] Ascending | Orientation: Vertical List or Horizontal Tiles. Selection: Multi-select with CTRL. Default: Select All. |
| **`VIS-03B`** | `Slicer (Between Slider)` | **Simulation Day (1 - 31)** | `Field: Dim_Day[day]` | `Dim_Day[day]` | `16` | `392` | `220` | `78` | Dim_Day[day] Ascending | Style: Between slider with numeric text boxes (Range: 1 to 31). Responsive slider bar. |
| **`VIS-03C`** | `Slicer (Vertical List)` | **Alert Source** | `Field: Dim_AlertSource[alert_source]` | `Dim_AlertSource[alert_source], Dim_AlertSource[alert_source_sort]` | `16` | `482` | `220` | `106` | Dim_AlertSource[alert_source_sort] Ascending | Style: Vertical checkboxes (Both, Rule only, ML only, None). NOTE: Disable interaction to Card 1. |
| **`VIS-03D`** | `Slicer (Dropdown / List)` | **Amount Magnitude Band** | `Field: Dim_AmountBand[amount_band]` | `Dim_AmountBand[amount_band], Dim_AmountBand[amount_band_sort]` | `16` | `600` | `220` | `104` | Dim_AmountBand[amount_band_sort] Ascending | Style: Vertical list (<1K, 1K-10K, 10K-100K, 100K-1M, >1M). Sort by magnitude index. |
| **`VIS-04`** | `Clustered Bar Chart` | **Fraud Rate % by Transaction Type** | `Y-Axis: Dim_Type[type], X-Axis: _Measures[Fraud Rate % by Type], Tooltips: Agg_ByType[fraud_count], Agg_ByType[total_txns]` | `Dim_Type[type], Dim_Type[type_sort], _Measures[Fraud Rate % by Type], Agg_ByType[fraud_count], Agg_ByType[total_txns]` | `252` | `128` | `498` | `276` | Dim_Type[type_sort] Ascending | Color Overrides: TRANSFER (#E74C3C Coral Red), CASH_OUT (#E67E22 Amber Orange), Others (#CBD5E1 Slate Grey). Data labels: ON (0.000%). Subtitle: 'TRANSFER & CASH_OUT account for 100% of fraud; other 3 types are 0.000%'. |
| **`VIS-05`** | `Line Chart (Dual Axis)` | **Alerts and Confirmed Fraud Count per Day** | `X-Axis: Dim_Day[day], Y-Axis (Primary): Agg_ByDay[alert_count], Secondary Y-Axis: Agg_ByDay[fraud_count], Tooltips: Agg_ByDay[flagged_value]` | `Dim_Day[day], Agg_ByDay[alert_count], Agg_ByDay[fraud_count], Agg_ByDay[flagged_value]` | `766` | `128` | `498` | `276` | Dim_Day[day] Ascending | Primary Line: Solid Navy #1E3A8A (Alerts). Secondary Line: Dashed Red #E74C3C with markers (Fraud Count). Secondary axis scaled independently. |
| **`VIS-06`** | `Clustered Column Chart` | **Alerts by Hour of Day (00:00 - 23:00)** | `X-Axis: Dim_Hour[hour_label], Y-Axis: Agg_ByHour[alert_count], Tooltips: Agg_ByHour[fraud_count], Dim_Hour[time_band]` | `Dim_Hour[hour_label], Dim_Hour[hour], Dim_Hour[time_band], Agg_ByHour[alert_count], Agg_ByHour[fraud_count]` | `252` | `420` | `498` | `284` | Dim_Hour[hour] Ascending | Bar Color: Vibrant Blue #2563EB. Data Labels: OFF (dense hourly view). Gridlines: Subtle dotted #E2E8F0. Sliced cleanly by operational shift. |
| **`VIS-07`** | `Donut Chart` | **Alerts by Source: Consensus vs. Rules vs. ML** | `Legend: Dim_AlertSource[alert_source], Values: Agg_BySource[alert_count], Tooltips: Agg_BySource[fraud_caught], Agg_BySource[precision_pct]` | `Dim_AlertSource[alert_source], Dim_AlertSource[alert_source_sort], Agg_BySource[alert_count], Agg_BySource[fraud_caught], Agg_BySource[precision_pct]` | `766` | `420` | `498` | `284` | Dim_AlertSource[alert_source_sort] Ascending | Colors: Both (#10B981 Emerald), Rule only (#3B82F6 Royal Blue), ML only (#8B5CF6 Purple). Visual Filter: alert_source <> 'None'. Detail labels: Category + Percent of total. |

---

## 3. Detailed Specifications by Visual

### Header: 6 Executive KPI Cards
Refer to [powerbi/04_kpi_cards.md](file:///Users/divyansh/code/Development/DataScience/Fraud%20Detection%20&%20Transaction%20Monitoring/powerbi/04_kpi_cards.md) for complete typography and layout arithmetic.
- **`VIS-01A` (Total Transactions):** `_Measures[Total Transactions]` (6,362,620). Sourced from `Agg_ByType[total_txns]`.
- **`VIS-01B` (Total Alerts):** `_Measures[Total Alerts]` (1,085,609). 17.06% enterprise alert rate under official Combined OR.
- **`VIS-01C` (Total Flagged Value):** `_Measures[Total Flagged Value]` ($407.88B). Formatted in Billions (`$0.00B`).
- **`VIS-01D` (Fraud Rate %):** `_Measures[Fraud Rate %]` (0.129%). Baseline ground-truth prevalence.
- **`VIS-01E` (Alert Precision):** `_Measures[Precision]` (0.75%). Color dynamically driven by `_Measures[Color - Precision KPI Card]`.
- **`VIS-01F` (Fraud Recall):** `_Measures[Recall]` (99.79%). Color dynamically driven by `_Measures[Color - Recall KPI Card]` (Emerald Green).

---

### Sidebar: Takeaway Brief & Slicer Panel

#### `VIS-02`: Surveillance Intelligence Brief (Callout Card)
- **Container Dimensions:** `X = 16`, `Y = 128`, `Width = 220`, `Height = 140`
- **Static Text Content (Derived directly from `reports/16_final_metrics.json`):**
  > **Executive Takeaway: 100% of all confirmed fraud events (8,213 cases; $12.06B) are concentrated exclusively in TRANSFER (0.769% fraud rate; 4,097 frauds) and CASH_OUT (0.184% fraud rate; 4,116 frauds), while PAYMENT, CASH_IN, and DEBIT exhibit zero fraud (0.000% across 3,592,211 transactions).**
- **Visual Styling:** Container background `#F8FAFC`, 1px solid border `#E2E8F0`, 6px corner radius, dark slate text `#1E293B`, bold highlighted metrics.

#### `VIS-03A` to `VIS-03D`: Four Filter Slicers
- **`VIS-03A` (Payment Method Slicer):**
  - Field: `Dim_Type[type]`, Sorted by: `Dim_Type[type_sort]` Ascending.
  - Position: `X = 16`, `Y = 280`, `W = 220`, `H = 100`.
  - Style: Vertical list or tiles with search bar. Allows multi-select.
- **`VIS-03B` (Simulation Day Range Slider):**
  - Field: `Dim_Day[day]`, Sorted by: `Dim_Day[day]` Ascending.
  - Position: `X = 16`, `Y = 392`, `W = 220`, `H = 78`.
  - Style: **Between slider** with numeric input endpoints (1 to 31).
- **`VIS-03C` (Alert Source Slicer):**
  - Field: `Dim_AlertSource[alert_source]`, Sorted by: `Dim_AlertSource[alert_source_sort]` Ascending.
  - Position: `X = 16`, `Y = 482`, `W = 220`, `H = 106`.
  - Style: Vertical list (`Both`, `Rule only`, `ML only`, `None`).
  - **CRITICAL:** Visual interaction to `VIS-01A` (`Total Transactions`) MUST be set to **None**.
- **`VIS-03D` (Amount Magnitude Band Slicer):**
  - Field: `Dim_AmountBand[amount_band]`, Sorted by: `Dim_AmountBand[amount_band_sort]` Ascending.
  - Position: `X = 16`, `Y = 600`, `W = 220`, `H = 104`.
  - Style: Vertical list (`<1K`, `1K-10K`, `10K-100K`, `100K-1M`, `>1M`).

---

### Canvas Row 1: Fraud Concentration Bar & Daily Trend Line

#### `VIS-04`: Clustered Bar Chart — Fraud Rate % by Transaction Type
- **Position & Geometry:** `X = 252`, `Y = 128`, `Width = 498`, `Height = 276`
- **Y-Axis (Category):** `Dim_Type[type]`
- **X-Axis (Metric):** `_Measures[Fraud Rate % by Type]` (or `Agg_ByType[fraud_rate_pct]`)
- **Sorting:** Sorted by `Dim_Type[type_sort]` Ascending (ensures `TRANSFER` and `CASH_OUT` appear at the top).
- **Color Overrides:**
  - `TRANSFER`: Crimson Red `#E74C3C` (Highest rate: 0.769%)
  - `CASH_OUT`: Orange `#E67E22` (High volume: 0.184%)
  - `CASH_IN`, `PAYMENT`, `DEBIT`: Muted Neutral Slate `#CBD5E1` (Zero fraud)
- **Data Labels:** ON, Position: Outside End, Value Format: `0.000%`
- **Subtitle:** "TRANSFER and CASH_OUT account for 100% of all fraud (8,213 cases). Other types exhibit 0.000% fraud."

#### `VIS-05`: Line Chart (Dual Axis) — Alerts and Confirmed Fraud Count per Day
- **Position & Geometry:** `X = 766`, `Y = 128`, `Width = 498`, `Height = 276`
- **X-Axis (Time Axis):** `Dim_Day[day]`, Sorted by `Dim_Day[day]` Ascending.
- **Y-Axis (Primary - Left Axis):** `SUM(Agg_ByDay[alert_count])`
  - Stroke: Solid line, 2px, Color: Deep Navy `#1E3A8A`
- **Secondary Y-Axis (Right Axis):** `SUM(Agg_ByDay[fraud_count])`
  - Stroke: Dashed line with circle markers, 2.5px, Color: Coral Red `#E74C3C`
- **Tooltips:** `Dim_Day[day]`, `Alert Count`, `Fraud Count`, `SUM(Agg_ByDay[flagged_value])`
- **Title:** "Alerts and Confirmed Fraud Count per Day (31 Days)"

---

### Canvas Row 2: Diurnal Hourly Column & Attribution Donut

#### `VIS-06`: Clustered Column Chart — Alerts by Hour of Day
- **Position & Geometry:** `X = 252`, `Y = 420`, `Width = 498`, `Height = 284`
- **X-Axis (Diurnal Hour):** `Dim_Hour[hour_label]` (`00:00` to `23:00`), Sorted by `Dim_Hour[hour]` Ascending.
- **Y-Axis (Alert Volume):** `SUM(Agg_ByHour[alert_count])`
- **Bar Color:** High-contrast Royal Blue `#2563EB`
- **Tooltips:** `Dim_Hour[hour_label]`, `Dim_Hour[time_band]`, `Alert Count`, `SUM(Agg_ByHour[fraud_count])`
- **Title:** "Alerts by Hour of Day (00:00 - 23:00)"

#### `VIS-07`: Donut Chart — Alerts by Source
- **Position & Geometry:** `X = 766`, `Y = 420`, `Width = 498`, `Height = 284`
- **Legend (Attribution Source):** `Dim_AlertSource[alert_source]`, Sorted by `Dim_AlertSource[alert_source_sort]` Ascending.
- **Values (Volume):** `SUM(Agg_BySource[alert_count])`
- **Visual-Level Filter:** Set filter on `Agg_BySource[alert_source]` to **is not None** (shows only generated alerts).
- **Slice Colors:**
  - `Both` (Consensus): Emerald Green `#10B981` (4,224 alerts, 98.65% precision)
  - `Rule only`: Royal Blue `#3B82F6` (1,081,330 alerts, broad net)
  - `ML only`: Purple `#8B5CF6` (55 alerts, catches rule-missed fraud)
- **Detail Labels:** Show `Category` and `Percent of total`
- **Title:** "Alerts by Source: Consensus vs. Rules vs. ML"

---

## 4. Slicer Decoupling & Visual Interaction Rules

To ensure data integrity, configure Edit Interactions in Power BI Desktop:
1. **Select Slicer `VIS-03C` (Alert Source):**
   - On ribbon, click **Format > Edit interactions**.
   - Click the **None** icon on `VIS-01A` (`Total Transactions`).
   - Click the **None** icon on `VIS-04` (Fraud Rate by Type, as non-fraud types have no alert source).
2. **Select Slicer `VIS-03D` (Amount Magnitude Band):**
   - Click **Edit interactions**.
   - Ensure `VIS-04` (Fraud Rate by Type) remains active to observe fraud rate shifts across transaction sizes.
3. Click **Edit interactions** again to save.

---

## 5. Programmatic Overlap & Boundary Verification Audit

This layout was audited programmatically by `src/check_page1_layout.py`. Every visual was verified against strict geometric boundary conditions:

```python
# Collision detection check
for i in range(len(visuals)):
    for j in range(i + 1, len(visuals)):
        is_separated = (r1 <= x2) or (r2 <= x1) or (b1 <= y2) or (b2 <= y1)
        assert is_separated, 'Overlap detected!'
```

### Audit Verification Output:
```text
Total Visual Containers Audited:   15
Canvas Bounds:                     1280 x 720 px
Out of Bounds Errors:              0
Visual Collisions / Overlaps:      0
AUDIT RESULT:                      PASS (100% collision-free layout)
```

---
*Specification compiled programmatically by `src/build_page1_spec.py`.*