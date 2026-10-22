# Page 3: Investigation — Case Triage, Score Diagnostics & Drill-Through Ledger

**Document ID:** `powerbi/07_page3_investigation.md`  
**Report Page Name:** `Investigation`  
**Canvas Size:** 1280 x 720 pixels (16:9 Standard HD)  
**Target Audience:** AML Investigators, Fraud Triage Analysts, Case Management Leads  
**Verification Status:** Collision-free, bounding-box validated (PASS: Zero overlaps, 100% within canvas bounds).  

---

## Table of Contents
1. [Page Layout Architecture & Visual Wireframe](#1-page-layout-architecture--visual-wireframe)
2. [Master Visual Specification Table](#2-master-visual-specification-table)
3. [Detailed Specifications by Visual](#3-detailed-specifications-by-visual)
   - [Sidebar: Triage Filter Slicers](#sidebar-triage-filter-slicers)
   - [Risk-Band Distribution Bar Chart](#risk-band-distribution-bar-chart)
   - [Top 20 Priority Investigation Ledger Table](#top-20-priority-investigation-ledger-table)
   - [Amount vs Anomaly Score Scatter Plot](#amount-vs-anomaly-score-scatter-plot)
4. [Drill-Through Architecture: 'Account Detail' Sub-Page](#4-drill-through-architecture-account-detail-sub-page)
5. [Programmatic Overlap & Boundary Verification Audit](#5-programmatic-overlap--boundary-verification-audit)

---

## 1. Page Layout Architecture & Visual Wireframe

The layout utilizes a structured **Left Rail (Filters + Risk Band) + Right Diagnostic Canvas (Top 20 + Scatter)** composition:

```text
+--------------------------------------------------------------------------------------------------------------------------+
|                                              CANVAS: 1280 x 720 PIXELS                                                   |
+-----------------------+--------------------------------------------------------------------------------------------------+
| [VIS-13A: Type Sl.]   | [VIS-15: Top 20 Priority Investigation Ledger Table]                                              | (y=16..356)
| Dim_Type[type]        | txn_id, day, hour, type, amount, alert_score, anomaly_score_pct, combo_score, alert_source,      |
| (x=16, w=240, h=100)  | risk_band, outcome (Top N Filter on combo_score Top 20) -> Drill-through to 'Account Detail'    |
|-----------------------| (x=272, y=16, w=992, h=340)                                                                      |
| [VIS-13B: Risk Sl.]   |                                                                                                  |
| Dim_RiskBand[band]    |                                                                                                  |
| (x=16, w=240, h=100)  |                                                                                                  |
|-----------------------+--------------------------------------------------------------------------------------------------+
| [VIS-13C: Outcome Sl.]| [VIS-16: Scatter Plot (Log Scale Amount vs Anomaly Score)]                                       | (y=372..704)
| Fact_Transactions[out]| X-Axis: Fact_Transactions[anomaly_score_pct] (0% to 100%)                                        |
| (x=16, w=240, h=100)  | Y-Axis: Fact_Transactions[amount] (Logarithmic Scale: $1 to $100M+)                              |
|-----------------------| Legend: Fact_Transactions[outcome] (TP: Red, FP: Amber, FN: Purple, TN: Green)                  |
| [VIS-14: Risk Bar]    | (x=272, y=372, w=992, h=332)                                                                     |
| Agg_ByRiskBand        |                                                                                                  |
| (x=16, w=240, h=352)  |                                                                                                  |
+-----------------------+--------------------------------------------------------------------------------------------------+
```

---

## 2. Master Visual Specification Table

| Visual ID | Type | Title | Fields (Axis, Values, Legend) | Tables & Measures Used | X | Y | W | H | Sorting | Formatting Notes |
| :--- | :--- | :--- | :--- | :--- | --: | --: | --: | --: | :--- | :--- |
| **`VIS-13A`** | `Slicer (Tile / Vertical)` | **Payment Method** | `Field: Dim_Type[type]` | `Dim_Type[type], Dim_Type[type_sort]` | `16` | `16` | `240` | `100` | Dim_Type[type_sort] Ascending | Orientation: Vertical List or Horizontal Tiles. Multi-select with CTRL. Default: Select All. |
| **`VIS-13B`** | `Slicer (Vertical List)` | **Risk Band** | `Field: Dim_RiskBand[risk_band]` | `Dim_RiskBand[risk_band], Dim_RiskBand[risk_band_sort]` | `16` | `128` | `240` | `100` | Dim_RiskBand[risk_band_sort] Ascending | Orientation: Vertical list (Critical, High, Medium, Low). Single / Multi-select. |
| **`VIS-13C`** | `Slicer (Vertical List)` | **Surveillance Outcome** | `Field: Fact_Transactions[outcome]` | `Fact_Transactions[outcome]` | `16` | `240` | `240` | `100` | Fact_Transactions[outcome] Ascending | Orientation: Vertical list (True Positive, False Positive, False Negative, True Negative). |
| **`VIS-14`** | `Clustered Bar Chart` | **Transaction & Fraud Volume by Risk Band** | `Y-Axis: Agg_ByRiskBand[risk_band], X-Axis (Values): Agg_ByRiskBand[fraud_count], Tooltips: Agg_ByRiskBand[rows], Agg_ByRiskBand[flagged_value]` | `Agg_ByRiskBand[risk_band], Agg_ByRiskBand[fraud_count], Agg_ByRiskBand[rows], Agg_ByRiskBand[flagged_value], Dim_RiskBand[risk_band_sort]` | `16` | `352` | `240` | `352` | Dim_RiskBand[risk_band_sort] Ascending | Color Overrides: High (#F97316 Orange), Medium (#EAB308 Yellow), Low (#94A3B8 Slate), Critical (#EF4444 Red). Data labels: ON. Subtitle: 'High band: 3,397 frauds in 3,402 alerts (99.85% precision).' |
| **`VIS-15`** | `Table` | **Top 20 Priority Investigation Ledger (Ranked by Combo Score)** | `Columns: Fact_Transactions[txn_id], Fact_Transactions[day], Fact_Transactions[hour], Fact_Transactions[type], Fact_Transactions[amount], Fact_Transactions[alert_score], Fact_Transactions[anomaly_score_pct], Fact_Transactions[combo_score], Fact_Transactions[alert_source], Fact_Transactions[risk_band], Fact_Transactions[outcome]` | `Fact_Transactions[txn_id], Fact_Transactions[day], Fact_Transactions[hour], Fact_Transactions[type], Fact_Transactions[amount], Fact_Transactions[alert_score], Fact_Transactions[anomaly_score_pct], Fact_Transactions[combo_score], Fact_Transactions[alert_source], Fact_Transactions[risk_band], Fact_Transactions[outcome]` | `272` | `16` | `992` | `340` | Fact_Transactions[combo_score] Descending | Top N Filter: Top 20 based on Fact_Transactions[combo_score]. Formats: amount as $#,##0, anomaly_score_pct as 0.0%, combo_score as 0.000. Drill-through enabled to 'Account Detail' via Fact_Transactions[nameOrig]. Alternating rows #F8FAFC. |
| **`VIS-16`** | `Scatter Plot` | **Transaction Amount vs. Isolation Forest Anomaly Score** | `X-Axis: Fact_Transactions[anomaly_score_pct], Y-Axis: Fact_Transactions[amount], Legend: Fact_Transactions[outcome], Tooltips: Fact_Transactions[txn_id], Fact_Transactions[nameOrig], Fact_Transactions[combo_score], Fact_Transactions[risk_band]` | `Fact_Transactions[anomaly_score_pct], Fact_Transactions[amount], Fact_Transactions[outcome], Fact_Transactions[txn_id], Fact_Transactions[nameOrig], Fact_Transactions[combo_score], Fact_Transactions[risk_band]` | `272` | `372` | `992` | `332` | Fact_Transactions[anomaly_score_pct] Ascending | Y-Axis Scale: Logarithmic scale enabled (Format > Y-Axis > Scale type = Logarithmic). Colors: True Positive (#EF4444 Crimson), False Positive (#F59E0B Amber), False Negative (#8B5CF6 Purple), True Negative (#10B981 Soft Green). Marker size: 5 px. X-Axis bounds: 0% to 100%. |

---

## 3. Detailed Specifications by Visual

### Sidebar: Triage Filter Slicers
- **`VIS-13A` (Payment Type):** `Dim_Type[type]`, sorted by `Dim_Type[type_sort]`. Position: `X = 16`, `Y = 16`, `W = 240`, `H = 100`.
- **`VIS-13B` (Risk Band):** `Dim_RiskBand[risk_band]`, sorted by `Dim_RiskBand[risk_band_sort]`. Position: `X = 16`, `Y = 128`, `W = 240`, `H = 100`.
- **`VIS-13C` (Surveillance Outcome):** `Fact_Transactions[outcome]`. Position: `X = 16`, `Y = 240`, `W = 240`, `H = 100`.

### Risk-Band Distribution Bar Chart (`VIS-14`)
- **Position:** `X = 16`, `Y = 352`, `Width = 240`, `Height = 352`
- **Y-Axis:** `Agg_ByRiskBand[risk_band]`
- **X-Axis:** `Agg_ByRiskBand[fraud_count]`
- **Tooltips:** `Agg_ByRiskBand[rows]`, `Agg_ByRiskBand[flagged_value]`
- **Sorting:** `Dim_RiskBand[risk_band_sort]` Ascending
- **Colors:** High (`#F97316` Orange), Medium (`#EAB308` Yellow), Low (`#94A3B8` Slate), Critical (`#EF4444` Red)
- **Data Labels:** ON (`#,##0`). High band displays 3,397 fraud cases out of 3,402 alerts (99.85% operational precision).

### Top 20 Priority Investigation Ledger Table (`VIS-15`)
- **Position:** `X = 272`, `Y = 16`, `Width = 992`, `Height = 340`
- **Columns (11 Fields):**
  `txn_id`, `day`, `hour`, `type`, `amount`, `alert_score`, `anomaly_score_pct`, `combo_score`, `alert_source`, `risk_band`, `outcome`
- **Top N Filter:** Filter on visual > `combo_score` Top 20 by `Fact_Transactions[combo_score]`.
- **Sorting:** `Fact_Transactions[combo_score]` Descending.
- **Formats:** `amount` formatted as `$#,##0`; `anomaly_score_pct` as `0.0%`; `combo_score` as `0.000`.
- **Drill-Through Action:** Right-click row > **Drill through > Account Detail** (passes `Fact_Transactions[nameOrig]`).

### Amount vs Anomaly Score Scatter Plot (`VIS-16`)
- **Position:** `X = 272`, `Y = 372`, `Width = 992`, `Height = 332`
- **X-Axis:** `Fact_Transactions[anomaly_score_pct]` (Linear scale, 0.0% to 100.0%)
- **Y-Axis:** `Fact_Transactions[amount]` (**Logarithmic Scale** enabled in Format > Y-Axis > Scale type = Logarithmic, displaying values from $10^0 to $10^8)
- **Legend:** `Fact_Transactions[outcome]` (`True Positive`, `False Positive`, `False Negative`, `True Negative`)
- **Marker Colors:**
  - `True Positive`: Crimson Red `#EF4444`
  - `False Positive`: Amber Orange `#F59E0B`
  - `False Negative`: Purple `#8B5CF6`
  - `True Negative`: Soft Emerald `#10B981`
- **Tooltips:** `Fact_Transactions[txn_id]`, `Fact_Transactions[nameOrig]`, `Fact_Transactions[combo_score]`, `Fact_Transactions[risk_band]`

---

## 4. Drill-Through Architecture: 'Account Detail' Sub-Page

### Page Configuration:
- **Page Name:** `Account Detail`
- **Page Visibility:** Hidden in report navigation (accessible solely via right-click drill-through).
- **Drill-Through Field:** `Fact_Transactions[nameOrig]` (Originator Account Identifier).
- **Drill-Through Settings:** `Keep all filters = ON`, `Cross-report = OFF`.

### Visual Wireframe: Account Detail Sub-Page (1280 x 720 px):
```text
+--------------------------------------------------------------------------------------------------------------------------+
|                                         ACCOUNT DETAIL SUB-PAGE: 1280 x 720 PIXELS                                       |
+-----------------------+--------------------------------------------------------------------------------------------------+
| [DT-01: Back Button]  | [DT-02: Target Account Context Header: Fact_Transactions[nameOrig]]                             | (y=16..64)
| (x=16, w=180, h=48)   | (x=212, y=16, w=1052, h=48)                                                                      |
+-----------------------+------------------------------------+-------------------------------------------------------------+
| [DT-03A: Total Vol $]              | [DT-03B: Total Txn Count]     | [DT-03C: Max Combo Score]                                   | (y=80..160)
| SUM(Fact_Transactions[amount])     | COUNT(Fact_Transactions[id])  | MAX(Fact_Transactions[combo_score])                          |
| (x=16, w=400, h=80)                | (x=432, w=400, h=80)          | (x=848, w=416, h=80)                                        |
+------------------------------------+-------------------------------+-------------------------------------------------------------+
| [DT-04: Account Complete Transaction Audit History Table]          | [DT-05: Destination Entities Profile Table]                 | (y=176..704)
| txn_id, day, hour, type, amount, nameDest, alert_score,            | nameDest, Txn Count, Total Volume Transferred               | (y=176..432)
| anomaly_score_pct, combo_score, isFraud, outcome                   | (x=852, y=176, w=412, h=256)                                |
| (Chronological order: day, hour Ascending)                         |-------------------------------------------------------------|
|                                                                    | [DT-06: Heuristic Rule Violations Matrix]                   | (y=448..704)
|                                                                    | Rule Emptied, Large Amount, Mule Dest, Dest Unchanged, Error|
| (x=16, y=176, w=820, h=528)                                        | (x=852, y=448, w=412, h=256)                                |
+--------------------------------------------------------------------+-------------------------------------------------------------+
```

### Master Visual Table: Account Detail Sub-Page

| Visual ID | Type | Title | Fields (Axis, Values, Legend) | Tables & Measures Used | X | Y | W | H | Sorting | Formatting Notes |
| :--- | :--- | :--- | :--- | :--- | --: | --: | --: | --: | :--- | :--- |
| **`DT-01`** | `Button (Back Navigator)` | **<- Return to Investigation Ledger** | `Action: Back` | `Navigation Action: Back` | `16` | `16` | `180` | `48` | N/A | Style: Left arrow icon with label 'Back'. Background: #FFFFFF, Border: 1px #CBD5E1, Radius: 6px, Text: 11 pt Semibold #1E293B. |
| **`DT-02`** | `Card (or Card new)` | **Selected Account (Originator)** | `Values: Fact_Transactions[nameOrig]` | `Fact_Transactions[nameOrig]` | `212` | `16` | `1052` | `48` | N/A | Callout: 14 pt Bold Accent Navy #1E3A8A. Drill-through context indicator showing target account identifier. |
| **`DT-03A`** | `Card (or Card new)` | **Account Total Volume** | `Values: SUM(Fact_Transactions[amount])` | `Fact_Transactions[amount]` | `16` | `80` | `400` | `80` | N/A | Callout: 20 pt Bold #0F172A, Format: $#,##0.00. Total transacted volume for filtered account. |
| **`DT-03B`** | `Card (or Card new)` | **Total Originator Transactions** | `Values: COUNT(Fact_Transactions[txn_id])` | `Fact_Transactions[txn_id]` | `432` | `80` | `400` | `80` | N/A | Callout: 20 pt Bold #0F172A, Format: #,##0. Transaction volume count for account. |
| **`DT-03C`** | `Card (or Card new)` | **Max Combo Risk Score** | `Values: MAX(Fact_Transactions[combo_score])` | `Fact_Transactions[combo_score]` | `848` | `80` | `416` | `80` | N/A | Callout: 20 pt Bold #EF4444, Format: 0.000. Peak suspicion score observed. |
| **`DT-04`** | `Table` | **Account Complete Transaction Audit History** | `Columns: Fact_Transactions[txn_id], Fact_Transactions[day], Fact_Transactions[hour], Fact_Transactions[type], Fact_Transactions[amount], Fact_Transactions[nameDest], Fact_Transactions[alert_score], Fact_Transactions[anomaly_score_pct], Fact_Transactions[combo_score], Fact_Transactions[isFraud], Fact_Transactions[outcome]` | `Fact_Transactions[txn_id], Fact_Transactions[day], Fact_Transactions[hour], Fact_Transactions[type], Fact_Transactions[amount], Fact_Transactions[nameDest], Fact_Transactions[alert_score], Fact_Transactions[anomaly_score_pct], Fact_Transactions[combo_score], Fact_Transactions[isFraud], Fact_Transactions[outcome]` | `16` | `176` | `820` | `528` | Fact_Transactions[day] Ascending | Full chronologically sorted ledger. Highlighting: Fraud rows in soft red. Columns sized to fit. Sorting: Fact_Transactions[day] Ascending, Fact_Transactions[hour] Ascending. |
| **`DT-05`** | `Table` | **Beneficiary Destination Entities Profile** | `Columns: Fact_Transactions[nameDest], Count of Txns: COUNT(Fact_Transactions[txn_id]), Total Transferred: SUM(Fact_Transactions[amount])` | `Fact_Transactions[nameDest], Fact_Transactions[txn_id], Fact_Transactions[amount]` | `852` | `176` | `412` | `256` | Total Transferred Descending | Grouping by nameDest recipient accounts. Sorted by Total Transferred Descending. Formats: $#,##0. Helps uncover mule syndicates. |
| **`DT-06`** | `Table` | **Heuristic Rule Violations Audit Matrix** | `Columns: Fact_Transactions[txn_id], Fact_Transactions[rule_emptied], Fact_Transactions[rule_large_amount], Fact_Transactions[rule_mule_dest], Fact_Transactions[rule_dest_unchanged], Fact_Transactions[rule_balance_error]` | `Fact_Transactions[txn_id], Fact_Transactions[rule_emptied], Fact_Transactions[rule_large_amount], Fact_Transactions[rule_mule_dest], Fact_Transactions[rule_dest_unchanged], Fact_Transactions[rule_balance_error]` | `852` | `448` | `412` | `256` | Fact_Transactions[txn_id] Ascending | Displays boolean indicator flags (0/1) for all 5 triggered heuristic rules on account activity. Cell formatting: Green 0, Red 1. |

---

## 5. Programmatic Overlap & Boundary Verification Audit

```text
Total Visual Containers Audited:   6 (Main Page) + 8 (Sub-Page)
Canvas Bounds:                     1280 x 720 px
Out of Bounds Errors:              0
Visual Collisions / Overlaps:      0
AUDIT RESULT:                      PASS (100% collision-free layout)
```

---
*Specification compiled programmatically by `src/build_pages2_3_specs.py`.*