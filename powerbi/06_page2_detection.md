# Page 2: Rules vs ML — Strategy Detection & Comparative Diagnostics

**Document ID:** `powerbi/06_page2_detection.md`  
**Report Page Name:** `Rules vs ML`  
**Canvas Size:** 1280 x 720 pixels (16:9 Standard HD)  
**Target Audience:** Chief Risk Officer, Head of ML/Fraud Modeling, Compliance & Regulatory Auditors  
**Verification Status:** Collision-free, bounding-box validated (PASS: Zero overlaps, 100% within canvas bounds).  

---

## Table of Contents
1. [Page Layout Architecture & Visual Wireframe](#1-page-layout-architecture--visual-wireframe)
2. [Master Visual Specification Table](#2-master-visual-specification-table)
3. [Detailed Specifications by Visual](#3-detailed-specifications-by-visual)
   - [Strategic Operating Point Brief](#strategic-operating-point-brief)
   - [Strategy Comparison Clustered Bar](#strategy-comparison-clustered-bar)
   - [Heuristic Rules Performance Table](#heuristic-rules-performance-table)
   - [Enterprise Confusion Matrix](#enterprise-confusion-matrix)
   - [Daily Alerts Stacked Column](#daily-alerts-stacked-column)
4. [Visual Interaction & Slicer Decoupling Rules](#4-visual-interaction--slicer-decoupling-rules)
5. [Programmatic Overlap & Boundary Verification Audit](#5-programmatic-overlap--boundary-verification-audit)

---

## 1. Page Layout Architecture & Visual Wireframe

The layout utilizes a structured **Top Header Banner + 2x2 Diagnostic Grid** composition:

```text
+--------------------------------------------------------------------------------------------------------------------------+
|                                              CANVAS: 1280 x 720 PIXELS                                                   |
+--------------------------------------------------------------------------------------------------------------------------+
| [VIS-08: Strategic Operating Point Brief Banner]                                                                         | (y=16..108)
| Combined AND (98.65% precision, 57 FPs, F1=0.6701) vs Combined OR (99.79% recall, 8,196 frauds, 1.08M alerts)           |
| (x=16, y=16, w=1248, h=92)                                                                                               |
+-----------------------------------------------------------+--------------------------------------------------------------+
| [VIS-09: Clustered Bar Chart]                             | [VIS-10: Rule Evaluation Table with Data Bars]               | (y=124..406)
| Precision, Recall & F1 Score by Detection Strategy         | Rule Name, Alerts, TP, FP, Precision (Bar), Recall (Bar), F1|
| (x=16, y=124, w=616, h=282)                               | (x=648, y=124, w=616, h=282)                                 |
+--------------------------------------+--------------------+--------------------------------------------------------------+
| [VIS-11: Confusion Matrix]           | [VIS-12: Stacked Column Chart]                                                   | (y=422..704)
| Actual (Fraud/Legit) vs. Predicted   | Daily Alert Volume by Source (Both vs Rule only vs ML only)                      |
| TP (8,196), FP (1.08M), FN (17), TN  | Note: Alerts only (8,213 frauds + 10k sampled legit). Agg_ByDayType not used     |
| (x=16, y=422, w=440, h=282)          | (x=472, y=422, w=792, h=282)                                                     |
+--------------------------------------+-----------------------------------------------------------------------------------+
```

---

## 2. Master Visual Specification Table

| Visual ID | Type | Title | Fields (Axis, Values, Legend) | Tables & Measures Used | X | Y | W | H | Sorting | Formatting Notes |
| :--- | :--- | :--- | :--- | :--- | --: | --: | --: | --: | :--- | :--- |
| **`VIS-08`** | `Text Box (Callout Banner)` | **STRATEGIC OPERATING POINT BRIEF: RULES VS. MACHINE LEARNING** | `Static strategic takeaway text with computed metrics` | `reports/16_final_metrics.json, Metrics_Approach, models/thresholds.json` | `16` | `16` | `1248` | `92` | N/A | Background: #F8FAFC, Border: 1px solid #E2E8F0, Radius: 6px. 3-column summary: Combined AND (98.65% precision, 57 FPs, F1=0.6701) vs Combined OR (99.79% recall, 8,196 frauds, 1.08M alerts) vs Simulator baseline (0.19% recall). |
| **`VIS-09`** | `Clustered Bar Chart` | **Precision, Recall, and F1 Score by Detection Strategy** | `Y-Axis: Metrics_Approach[approach], X-Axis Values: Metrics_Approach[precision_pct], Metrics_Approach[recall_pct], Metrics_Approach[f1_pct]` | `Metrics_Approach[approach], Metrics_Approach[precision_pct], Metrics_Approach[recall_pct], Metrics_Approach[f1_pct]` | `16` | `124` | `616` | `282` | Metrics_Approach[f1_pct] Descending | Bar Colors: Precision (#1E3A8A Navy), Recall (#10B981 Emerald), F1 (#F59E0B Amber). Data Labels: ON (0.0%). Subtitle: 'Simulator baseline flagged for reference only (16 frauds caught, 0.19% recall)'. Y-axis width 180 px. |
| **`VIS-10`** | `Table` | **Heuristic Rules Diagnostic Performance Matrix** | `Columns: Metrics_Rules[rule_name], Metrics_Rules[alerts], Metrics_Rules[tp], Metrics_Rules[fp], Metrics_Rules[precision_pct], Metrics_Rules[recall_pct], Metrics_Rules[f1_pct]` | `Metrics_Rules[rule_name], Metrics_Rules[alerts], Metrics_Rules[tp], Metrics_Rules[fp], Metrics_Rules[precision_pct], Metrics_Rules[recall_pct], Metrics_Rules[f1_pct]` | `648` | `124` | `616` | `282` | Metrics_Rules[recall_pct] Descending | Data Bars: Precision (#3B82F6 Blue gradient) and Recall (#10B981 Green gradient). Numbers: alerts/tp/fp as #,##0, percentages as 0.00%. Alternating row fill: #F8FAFC. Headers: 11 pt Bold #0F172A. |
| **`VIS-11`** | `Matrix` | **Enterprise Confusion Matrix: Actual vs. Predicted (Combined OR)** | `Rows: Confusion_Matrix[actual], Columns: Confusion_Matrix[predicted], Values: Confusion_Matrix[count], Tooltips: Confusion_Matrix[pct_of_total], Confusion_Matrix[outcome]` | `Confusion_Matrix[actual], Confusion_Matrix[predicted], Confusion_Matrix[count], Confusion_Matrix[pct_of_total], Confusion_Matrix[outcome]` | `16` | `422` | `440` | `282` | Confusion_Matrix[actual] Descending (Fraud first), Confusion_Matrix[predicted] Ascending (Alert first) | Cell Background Color Formatting: TP (8,196) and TN (5,276,994) soft green #DCFCE7, FP (1,077,413) pale amber #FEE2E2, FN (17) soft rose #FFE4E6. Value format: #,##0. Row and Column Subtotals: ON. |
| **`VIS-12`** | `Stacked Column Chart` | **Daily Alert Volume by Detection Source (Days 1 - 31)** | `X-Axis: Fact_Transactions[day], Legend: Fact_Transactions[alert_source], Y-Axis: Fact_Transactions[is_alert], Tooltips: Fact_Transactions[outcome]` | `Fact_Transactions[day], Fact_Transactions[alert_source], Fact_Transactions[is_alert], Fact_Transactions[outcome]` | `472` | `422` | `792` | `282` | Fact_Transactions[day] Ascending | Visual Filter: Fact_Transactions[is_alert] = 1. Colors: Both (#10B981 Emerald), Rule only (#3B82F6 Royal Blue), ML only (#8B5CF6 Purple). Subtitle Note: 'Visual shows alerts only (8,213 frauds + 10,000 sampled legit) because normal rows are sampled. Agg_ByDayType not used.' |

---

## 3. Detailed Specifications by Visual

### Strategic Operating Point Brief (`VIS-08`)
- **Position:** `X = 16`, `Y = 16`, `Width = 1248`, `Height = 92`
- **Static Briefing Text (Based on `reports/14_approach_comparison.md` and `reports/16_final_metrics.json`):**
  > **Strategic Recommendation: Combined AND (combo_and) achieves the highest operational precision in enterprise production at 98.65% (4,167 True Positives against merely 57 False Positives out of 4,224 alerts; F1 = 0.6701), slashing analyst alert backlog by 46.2% relative to standalone ML while securing $6.45B in confirmed fraud value. For exhaustive regulatory compliance, Combined OR (combo_or) provides maximum recall at 99.79% (8,196 of 8,213 fraud events captured, missing only 17), intercepting 6 frauds heuristic rules missed entirely (+55 alerts), but requiring 1,085,609 investigations ($407.88B flagged). The simulator baseline is flagged for reference only (100% precision, but 0.19% recall, capturing only 16 frauds).**

### Strategy Comparison Clustered Bar (`VIS-09`)
- **Position:** `X = 16`, `Y = 124`, `Width = 616`, `Height = 282`
- **Y-Axis (Approaches):** `Metrics_Approach[approach]`
- **X-Axis (Series Values):**
  - `Precision (%)`: Solid Deep Navy `#1E3A8A`
  - `Recall (%)`: Solid Emerald Green `#10B981`
  - `F1 Score`: Amber `#F59E0B`
- **Sorting:** `Metrics_Approach[f1_pct]` Descending
- **Formatting:** Data Labels enabled (`0.0%`). Subtitle notes that the simulator baseline is an unviable historical reference (0.19% recall).

### Heuristic Rules Performance Table (`VIS-10`)
- **Position:** `X = 648`, `Y = 124`, `Width = 616`, `Height = 282`
- **Fields:** `rule_name`, `alerts`, `tp`, `fp`, `precision_pct`, `recall_pct`, `f1_pct` from `Metrics_Rules`
- **Conditional Formatting (Data Bars):**
  - `precision_pct`: Blue horizontal data bar (`#3B82F6` gradient), range 0 to 100%.
  - `recall_pct`: Green horizontal data bar (`#10B981` gradient), range 0 to 100%.
- **Sorting:** `Metrics_Rules[recall_pct]` Descending (places Rule 1 at top with 97.5% recall).

### Enterprise Confusion Matrix (`VIS-11`)
- **Position:** `X = 16`, `Y = 422`, `Width = 440`, `Height = 282`
- **Rows:** `Confusion_Matrix[actual]` (`Fraud`, `Legit`)
- **Columns:** `Confusion_Matrix[predicted]` (`Alert`, `No alert`)
- **Values:** `Confusion_Matrix[count]`
- **Cell Coloring:**
  - `TP` (8,196) and `TN` (5,276,994): Soft green `#DCFCE7` (Correct surveillance decisions)
  - `FP` (1,077,413): Soft amber `#FEE2E2` (Operational review burden)
  - `FN` (17): Soft rose `#FFE4E6` (Escaped fraud events, $2.7M missed)

### Daily Alerts Stacked Column (`VIS-12`)
- **Position:** `X = 472`, `Y = 422`, `Width = 792`, `Height = 282`
- **X-Axis:** `Fact_Transactions[day]` (Days 1 - 31), Sorted Ascending.
- **Legend:** `Fact_Transactions[alert_source]` (`Both`, `Rule only`, `ML only`).
- **Y-Axis:** `COUNTROWS(Fact_Transactions)` where `Fact_Transactions[is_alert] = 1`.
- **Methodology Note:** `Agg_ByDayType` is not suitable because it lacks alert source attribution. This visual sources directly from `Fact_Transactions` and filters `is_alert = 1`. A prominent subtitle explicitly clarifies: *'Visual displays alerts only (8,213 frauds + 10,000 sampled legit) because normal transactions are sampled in Fact_Transactions.'*

---

## 4. Visual Interaction & Slicer Decoupling Rules

1. **Strategy Selection on `VIS-09`:** Selecting an approach filters `VIS-10` and `VIS-11` to cross-examine corresponding rule subsets.
2. **Isolation of Static Metrics:** Tables `Metrics_Approach`, `Metrics_Rules`, and `Confusion_Matrix` are pre-aggregated across the full dataset; cross-filtering from other pages is disabled to protect metric truth.

---

## 5. Programmatic Overlap & Boundary Verification Audit

```text
Total Visual Containers Audited:   5
Canvas Bounds:                     1280 x 720 px
Out of Bounds Errors:              0
Visual Collisions / Overlaps:      0
AUDIT RESULT:                      PASS (100% collision-free layout)
```

---
*Specification compiled programmatically by `src/build_pages2_3_specs.py`.*