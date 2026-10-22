# Page 1 Executive Overview: KPI Card Row Layout & Configuration Guide

**Document ID:** `powerbi/04_kpi_cards.md`  
**Target Page:** Page 1 — Executive Overview  
**Canvas Dimensions:** 1280 x 720 pixels (Standard 16:9 HD)  
**KPI Row Geometry:** Height = 100 px, Top Gutter (Y) = 16 px, Inter-Card Gutter = 16 px  
**Visual Type:** Power BI `Card (new)` (Recommended) or 6 Individual `Card` Visual Containers  
**Verification:** Arithmetically validated down to the exact pixel.  

---

## Table of Contents
1. [Executive KPI Row Architecture & Visual Overview](#1-executive-kpi-row-architecture--visual-overview)
2. [Exact Pixel Coordinates & Arithmetic Verification](#2-exact-pixel-coordinates--arithmetic-verification)
3. [Detailed Specifications for Each of the 6 Cards](#3-detailed-specifications-for-each-of-the-6-cards)
4. [Conditional Formatting Rules (Hex Strings & Thresholds)](#4-conditional-formatting-rules-hex-strings--thresholds)
5. [Visual Interactions & Slicer Decoupling Rules](#5-visual-interactions--slicer-decoupling-rules)
6. [Step-by-Step Implementation in Power BI Desktop](#6-step-by-step-implementation-in-power-bi-desktop)

---

## 1. Executive KPI Row Architecture & Visual Overview

The executive KPI header establishes the critical headline metrics for surveillance leaders and risk committees at first glance.
It sits along the very top of **Page 1 (Executive Overview)** across `y = 16` to `y = 116`, spanning the full canvas width from `x = 16` to `x = 1264` (leaving 16 px margins on both sides).

### The Six Executive Headline Metrics:
1. **Total Transactions:** Full-universe business scale (6,362,620 transactions).
2. **Total Alerts:** Total alert volume flagged for review under the official Combined OR definition (1,085,609 alerts).
3. **Total Flagged Value:** Gross dollar exposure intercepted for investigator triage ($407.88 Billion).
4. **Fraud Rate %:** Baseline enterprise fraud prevalence rate (0.129%).
5. **Alert Precision:** Operational hit rate of triggered alerts (0.755% under Combined OR safety net).
6. **Fraud Recall:** Executive surveillance coverage rate (99.793% — 8,196 of 8,213 frauds captured).

---

## 2. Exact Pixel Coordinates & Arithmetic Verification

To achieve pixel-perfect alignment in Power BI Desktop without manual eyeballing, use the exact coordinates below:

### Coordinate Master Table (1280 x 720 Canvas):

| Card # | Card Title | X (px) | Y (px) | Width (px) | Height (px) | Right Edge (X + W) | Next Gutter |
| :-: | :--- | --: | --: | --: | --: | --: | :---: |
| **Card 1** | **Total Transactions** | `16` | `16` | `195` | `100` | `211` | `16 px` |
| **Card 2** | **Total Alerts** | `227` | `16` | `195` | `100` | `422` | `16 px` |
| **Card 3** | **Total Flagged Value** | `438` | `16` | `194` | `100` | `632` | `16 px` |
| **Card 4** | **Fraud Rate %** | `648` | `16` | `194` | `100` | `842` | `16 px` |
| **Card 5** | **Alert Precision** | `858` | `16` | `195` | `100` | `1053` | `16 px` |
| **Card 6** | **Fraud Recall** | `1069` | `16` | `195` | `100` | `1264` | `16 px` |

### Arithmetic Proof of Canvas Fit:
```text
Left Margin:                                                 16 px
+ Card 1 Width:                                             195 px  (x = 16 to 211)
+ Gutter 1:                                                  16 px
+ Card 2 Width:                                             195 px  (x = 227 to 422)
+ Gutter 2:                                                  16 px
+ Card 3 Width:                                             194 px  (x = 438 to 632)
+ Gutter 3:                                                  16 px
+ Card 4 Width:                                             194 px  (x = 648 to 842)
+ Gutter 4:                                                  16 px
+ Card 5 Width:                                             195 px  (x = 858 to 1053)
+ Gutter 5:                                                  16 px
+ Card 6 Width:                                             195 px  (x = 1069 to 1264)
+ Right Margin:                                               16 px
-------------------------------------------------------------------------
TOTAL EXACT HORIZONTAL PIXELS:                             1280 px (100% Canvas Fit)
```

> [!TIP]
> **Why 195 px vs. 194 px?** Dividing the 1,168 px of available card space equally among 6 cards results in 194.67 px. Allocating 195 px to cards 1, 2, 5, 6 and 194 px to cards 3, 4 creates a perfectly symmetrical row with identical 16 px gutters, with a 1-pixel variance that is completely imperceptible to the human eye.

---

## 3. Detailed Specifications for Each of the 6 Cards

### Card 1: Total Transactions
- **DAX Measure Name:** `[Total Transactions]`
- **Source Table in Model:** `_Measures (or Agg_ByType[total_txns])`
- **Visual Type:** `Card (new)` or standard `Card` visual
- **Title / Category Label:** "Total Transactions"
- **Format String:** `#,##0`
- **Sample Output Value:** **`6,362,620`**
- **Typography:**
  - Callout Value: **24 pt (Bold)**, Font: Segoe UI or DIN
  - Category / Title Label: **11 pt (Semibold)**, Font: Segoe UI
- **Position & Geometry:** `X = 16 px`, `Y = 16 px`, `Width = 195 px`, `Height = 100 px`
- **Color Rule:** Primary Dark Slate `#0F172A` (Callout), Neutral Slate `#64748B` (Title/Label), Card Background `#FFFFFF`, Border 1px `#E2E8F0`.
- **Slicer Interaction:** CRITICAL: Disable interactions from Alert Source and Risk Band slicers.
- **Business Context:** Full-universe transaction population. Sourced from 6.36M ground-truth census.

### Card 2: Total Alerts
- **DAX Measure Name:** `[Total Alerts]`
- **Source Table in Model:** `_Measures (or Agg_ByType[alert_count])`
- **Visual Type:** `Card (new)` or standard `Card` visual
- **Title / Category Label:** "Total Alerts"
- **Format String:** `#,##0`
- **Sample Output Value:** **`1,085,609`**
- **Typography:**
  - Callout Value: **24 pt (Bold)**, Font: Segoe UI or DIN
  - Category / Title Label: **11 pt (Semibold)**, Font: Segoe UI
- **Position & Geometry:** `X = 227 px`, `Y = 16 px`, `Width = 195 px`, `Height = 100 px`
- **Color Rule:** Accent Navy `#1E3A8A` (Callout), Slate `#64748B` (Label), Background `#FFFFFF`, Border 1px `#E2E8F0`.
- **Slicer Interaction:** Filtered by Type, Day, and Hour slicers.
- **Business Context:** Total transactions flagged for investigator review under official Combined OR strategy.

### Card 3: Total Flagged Value
- **DAX Measure Name:** `[Total Flagged Value]`
- **Source Table in Model:** `_Measures (or Agg_ByType[flagged_value])`
- **Visual Type:** `Card (new)` or standard `Card` visual
- **Title / Category Label:** "Total Flagged Value"
- **Format String:** `$#,##0 (or $0.00B with Display Units = Billions)`
- **Sample Output Value:** **`$407.88B`**
- **Typography:**
  - Callout Value: **24 pt (Bold)**, Font: Segoe UI or DIN
  - Category / Title Label: **11 pt (Semibold)**, Font: Segoe UI
- **Position & Geometry:** `X = 438 px`, `Y = 16 px`, `Width = 194 px`, `Height = 100 px`
- **Color Rule:** Dark Slate `#0F172A` (Callout), Slate `#64748B` (Label), Background `#FFFFFF`, Border 1px `#E2E8F0`.
- **Slicer Interaction:** Filtered by Type, Day, and Hour slicers.
- **Business Context:** Total currency value of alerted transactions under review ($407,883,914,866.30).

### Card 4: Fraud Rate %
- **DAX Measure Name:** `[Fraud Rate %]`
- **Source Table in Model:** `_Measures (DIVIDE([Fraud Count], [Total Transactions]))`
- **Visual Type:** `Card (new)` or standard `Card` visual
- **Title / Category Label:** "Fraud Rate %"
- **Format String:** `0.000%`
- **Sample Output Value:** **`0.129%`**
- **Typography:**
  - Callout Value: **24 pt (Bold)**, Font: Segoe UI or DIN
  - Category / Title Label: **11 pt (Semibold)**, Font: Segoe UI
- **Position & Geometry:** `X = 648 px`, `Y = 16 px`, `Width = 194 px`, `Height = 100 px`
- **Color Rule:** Dark Slate `#0F172A` (Callout), Slate `#64748B` (Label), Background `#FFFFFF`, Border 1px `#E2E8F0`.
- **Slicer Interaction:** Filtered by Type slicer (shows 0.769% for TRANSFER, 0.184% for CASH_OUT, 0.000% others).
- **Business Context:** Baseline fraud occurrence prevalence (8,213 frauds / 6,362,620 transactions).

### Card 5: Alert Precision
- **DAX Measure Name:** `[Precision]`
- **Source Table in Model:** `_Measures (DIVIDE([True Positives], [True Positives]+[False Positives]))`
- **Visual Type:** `Card (new)` or standard `Card` visual
- **Title / Category Label:** "Alert Precision"
- **Format String:** `0.00%`
- **Sample Output Value:** **`0.75%`**
- **Typography:**
  - Callout Value: **24 pt (Bold)**, Font: Segoe UI or DIN
  - Category / Title Label: **11 pt (Semibold)**, Font: Segoe UI
- **Position & Geometry:** `X = 858 px`, `Y = 16 px`, `Width = 195 px`, `Height = 100 px`
- **Color Rule:** Driven by DAX measure `[Color - Precision KPI Card]`: Emerald Green `#2ECC71` if >= 90%, Amber `#F1C40F` if >= 50%, Coral Red `#E74C3C` if < 50%.
- **Slicer Interaction:** Filtered by Type, Day, and Hour slicers.
- **Business Context:** Hit rate of alerts: 8,196 TP / (8,196 TP + 1,077,413 FP) = 0.755% under Combined OR safety net.

### Card 6: Fraud Recall
- **DAX Measure Name:** `[Recall]`
- **Source Table in Model:** `_Measures (DIVIDE([True Positives], [True Positives]+[False Negatives]))`
- **Visual Type:** `Card (new)` or standard `Card` visual
- **Title / Category Label:** "Fraud Recall"
- **Format String:** `0.00%`
- **Sample Output Value:** **`99.79%`**
- **Typography:**
  - Callout Value: **24 pt (Bold)**, Font: Segoe UI or DIN
  - Category / Title Label: **11 pt (Semibold)**, Font: Segoe UI
- **Position & Geometry:** `X = 1069 px`, `Y = 16 px`, `Width = 195 px`, `Height = 100 px`
- **Color Rule:** Driven by DAX measure `[Color - Recall KPI Card]`: Emerald Green `#2ECC71` if >= 99.0% (Current: 99.79%), Amber `#F1C40F` if >= 90.0%, Coral Red `#E74C3C` if < 90.0%.
- **Slicer Interaction:** Filtered by Type, Day, and Hour slicers.
- **Business Context:** Detection capture coverage: 8,196 detected out of 8,213 total frauds (only 17 missed).

---

## 4. Conditional Formatting Rules (Hex Strings & Thresholds)

To communicate risk state dynamically without cognitive overload, **Card 5 (Alert Precision)** and **Card 6 (Fraud Recall)** use automated conditional formatting driven by DAX measures in `03_measures.dax`:

### A. Card 5: Alert Precision (`[Precision]`)
- **Measure Driving Color:** `[Color - Precision KPI Card]`
- **Operational Rationale:** Under the official Combined OR strategy, precision is naturally diluted to **0.755%** in exchange for near-total 99.79% fraud capture. However, when an investigator slices by `alert_source = 'Both'` (Consensus alerts), precision jumps to **98.65%** (Green).
- **Threshold Logic:**

```dax
VAR Prec = [Precision]
RETURN
    SWITCH(
        TRUE(),
        Prec >= 0.90, "#2ECC71",  // Emerald Green: High operational efficiency (Consensus tier)
        Prec >= 0.50, "#F1C40F",  // Amber: Balanced ML-only tier
        "#E74C3C"                 // Coral Red: Broad safety net tier (Combined OR)
    )
```

### B. Card 6: Fraud Recall (`[Recall]`)
- **Measure Driving Color:** `[Color - Recall KPI Card]`
- **Operational Rationale:** In financial crime compliance, **regulatory penalties and fraud losses scale with missed fraud (False Negatives)**. Recall must remain at or above 99% across production operations.
- **Threshold Logic:**

```dax
VAR Rec = [Recall]
RETURN
    SWITCH(
        TRUE(),
        Rec >= 0.99, "#2ECC71",   // Emerald Green: Exemplary capture (Combined OR = 99.79%)
        Rec >= 0.90, "#F1C40F",   // Amber: Acceptable ML-only or score>=2 tier
        "#E74C3C"                 // Coral Red: Unacceptable leakage (Baseline = 0.19%)
    )
```

### How to Apply Conditional Color in Power BI Desktop:
1. Select **Card 5** (Alert Precision).
2. In the **Visualizations** pane, go to **Format visual** > **Callout value**.
3. Next to the **Color** picker, click the **`fx`** (Conditional formatting) button.
4. In the dialog:
   - **Format style:** Select `Field value`.
   - **What field should we base this on?:** Select `_Measures` > `[Color - Precision KPI Card]`.
5. Click **OK**.
6. Repeat the same steps for **Card 6** (Fraud Recall), selecting `_Measures` > `[Color - Recall KPI Card]`.

---

## 5. Visual Interactions & Slicer Decoupling Rules

In financial surveillance dashboards, slicers must filter relevant sub-populations without breaking baseline enterprise denominators.

### Slicers That Must NOT Filter Card 1 (`Total Transactions`):
1. **`Alert Source` Slicer (`Dim_AlertSource`):** MUST NOT filter Card 1.
2. **`Risk Band` Slicer (`Dim_RiskBand`):** MUST NOT filter Card 1.

### The Architectural Reason:
- `[Total Transactions]` is defined as `SUM(Agg_ByType[total_txns])`.
- The aggregate table `Agg_ByType` has conforming links to `Dim_Type[type]`, so selecting `TRANSFER` or `CASH_OUT` correctly filters enterprise volume for that payment method.
- However, `Agg_ByType` has **no foreign key** to `Dim_AlertSource` or `Dim_RiskBand` (because 3.59 million legitimate transactions outside Transfer/Cash-out have no alert triage attribution).
- If an investigator selects `alert_source = 'Both'` to audit the 4,224 consensus alerts, **Total Transactions should remain the benchmark business volume (6,362,620)** rather than displaying an invalid or confusing value.

### Step-by-Step Instructions to Disable Visual Interactions:

```text
[Step 1] Click on the 'Alert Source' Slicer visual on Page 1.
[Step 2] In the top Power BI Desktop ribbon, click the 'Format' tab.
[Step 3] In the 'Interactions' group on the left of the ribbon, click 'Edit interactions'.
         --> Small filter/block icons will appear in the top-right of every other visual.
[Step 4] Locate Card 1 ('Total Transactions') at x=16, y=16.
[Step 5] Click the 'None' icon (circle with diagonal slash) on Card 1.
         --> This severs the filter link between Alert Source and Card 1.
[Step 6] Now click on the 'Risk Band' Slicer visual on Page 1.
[Step 7] Again, click the 'None' icon on Card 1 ('Total Transactions').
[Step 8] Click 'Edit interactions' on the Format ribbon to exit interaction edit mode.
```

---

## 6. Step-by-Step Implementation in Power BI Desktop

### Option A: Using the Modern `Card (new)` Multi-Card Visual (Recommended)
Power BI Desktop's new card visual allows all 6 cards to be hosted inside a single visual container:
1. On the **Home** ribbon, click the **Card (new)** visual icon.
2. Set its position and dimensions in **Format visual > General > Properties**:
   - `Horizontal (X) = 16 px`, `Vertical (Y) = 16 px`
   - `Width = 1248 px`, `Height = 100 px`
3. Drag the 6 measures from `_Measures` into the **Data** field well in order:
   1. `[Total Transactions]`
   2. `[Total Alerts]`
   3. `[Total Flagged Value]`
   4. `[Fraud Rate %]`
   5. `[Precision]`
   6. `[Recall]`
4. Under **Format visual > Layout**:
   - Orientation: `Horizontal`
   - Columns: `6`
   - Card spacing: `16 px`
5. Under **Cards > Shape**, select `Rounded rectangle` with `6 px` corner radius.
6. Apply conditional callout value colors to Card 5 and Card 6 via `fx`.

### Option B: Using 6 Individual Visual Containers
If using traditional single-value cards, create 6 separate cards and enter the exact pixel coordinates from Section 2 into **Format visual > General > Properties > Size and position**:
- Card 1: `X = 16, Y = 16, W = 195, H = 100`
- Card 2: `X = 227, Y = 16, W = 195, H = 100`
- Card 3: `X = 438, Y = 16, W = 194, H = 100`
- Card 4: `X = 648, Y = 16, W = 194, H = 100`
- Card 5: `X = 858, Y = 16, W = 195, H = 100`
- Card 6: `X = 1069, Y = 16, W = 195, H = 100`

---
*Guide generated programmatically by `src/build_kpi_cards_doc.py`.*