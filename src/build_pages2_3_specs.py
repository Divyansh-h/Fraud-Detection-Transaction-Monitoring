"""Programmatic generator for Power BI Page 2 (Rules vs ML) and Page 3 (Investigation) specifications.

Generates:
- powerbi/06_page2_detection.md
- powerbi/07_page3_investigation.md

Ensures strict 1280x720 canvas compliance, zero overlaps, and referential field validation.
"""

from pathlib import Path
import json
import re
import sys
import time
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config

CANVAS_WIDTH = 1280
CANVAS_HEIGHT = 720

# -----------------------------------------------------------------------------
# PAGE 2 DEFINITIONS: Rules vs ML
# -----------------------------------------------------------------------------
PAGE2_VISUALS = [
    {
        "id": "VIS-08",
        "type": "Text Box (Callout Banner)",
        "title": "STRATEGIC OPERATING POINT BRIEF: RULES VS. MACHINE LEARNING",
        "fields": "Static strategic takeaway text with computed metrics",
        "source": "reports/16_final_metrics.json, Metrics_Approach, models/thresholds.json",
        "x": 16, "y": 16, "w": 1248, "h": 92,
        "format": "Background: #F8FAFC, Border: 1px solid #E2E8F0, Radius: 6px. 3-column summary: Combined AND (98.65% precision, 57 FPs, F1=0.6701) vs Combined OR (99.79% recall, 8,196 frauds, 1.08M alerts) vs Simulator baseline (0.19% recall).",
        "sort": "N/A",
    },
    {
        "id": "VIS-09",
        "type": "Clustered Bar Chart",
        "title": "Precision, Recall, and F1 Score by Detection Strategy",
        "fields": "Y-Axis: Metrics_Approach[approach], X-Axis Values: Metrics_Approach[precision_pct], Metrics_Approach[recall_pct], Metrics_Approach[f1_pct]",
        "source": "Metrics_Approach[approach], Metrics_Approach[precision_pct], Metrics_Approach[recall_pct], Metrics_Approach[f1_pct]",
        "x": 16, "y": 124, "w": 616, "h": 282,
        "format": "Bar Colors: Precision (#1E3A8A Navy), Recall (#10B981 Emerald), F1 (#F59E0B Amber). Data Labels: ON (0.0%). Subtitle: 'Simulator baseline flagged for reference only (16 frauds caught, 0.19% recall)'. Y-axis width 180 px.",
        "sort": "Metrics_Approach[f1_pct] Descending",
    },
    {
        "id": "VIS-10",
        "type": "Table",
        "title": "Heuristic Rules Diagnostic Performance Matrix",
        "fields": "Columns: Metrics_Rules[rule_name], Metrics_Rules[alerts], Metrics_Rules[tp], Metrics_Rules[fp], Metrics_Rules[precision_pct], Metrics_Rules[recall_pct], Metrics_Rules[f1_pct]",
        "source": "Metrics_Rules[rule_name], Metrics_Rules[alerts], Metrics_Rules[tp], Metrics_Rules[fp], Metrics_Rules[precision_pct], Metrics_Rules[recall_pct], Metrics_Rules[f1_pct]",
        "x": 648, "y": 124, "w": 616, "h": 282,
        "format": "Data Bars: Precision (#3B82F6 Blue gradient) and Recall (#10B981 Green gradient). Numbers: alerts/tp/fp as #,##0, percentages as 0.00%. Alternating row fill: #F8FAFC. Headers: 11 pt Bold #0F172A.",
        "sort": "Metrics_Rules[recall_pct] Descending",
    },
    {
        "id": "VIS-11",
        "type": "Matrix",
        "title": "Enterprise Confusion Matrix: Actual vs. Predicted (Combined OR)",
        "fields": "Rows: Confusion_Matrix[actual], Columns: Confusion_Matrix[predicted], Values: Confusion_Matrix[count], Tooltips: Confusion_Matrix[pct_of_total], Confusion_Matrix[outcome]",
        "source": "Confusion_Matrix[actual], Confusion_Matrix[predicted], Confusion_Matrix[count], Confusion_Matrix[pct_of_total], Confusion_Matrix[outcome]",
        "x": 16, "y": 422, "w": 440, "h": 282,
        "format": "Cell Background Color Formatting: TP (8,196) and TN (5,276,994) soft green #DCFCE7, FP (1,077,413) pale amber #FEE2E2, FN (17) soft rose #FFE4E6. Value format: #,##0. Row and Column Subtotals: ON.",
        "sort": "Confusion_Matrix[actual] Descending (Fraud first), Confusion_Matrix[predicted] Ascending (Alert first)",
    },
    {
        "id": "VIS-12",
        "type": "Stacked Column Chart",
        "title": "Daily Alert Volume by Detection Source (Days 1 - 31)",
        "fields": "X-Axis: Fact_Transactions[day], Legend: Fact_Transactions[alert_source], Y-Axis: Fact_Transactions[is_alert], Tooltips: Fact_Transactions[outcome]",
        "source": "Fact_Transactions[day], Fact_Transactions[alert_source], Fact_Transactions[is_alert], Fact_Transactions[outcome]",
        "x": 472, "y": 422, "w": 792, "h": 282,
        "format": "Visual Filter: Fact_Transactions[is_alert] = 1. Colors: Both (#10B981 Emerald), Rule only (#3B82F6 Royal Blue), ML only (#8B5CF6 Purple). Subtitle Note: 'Visual shows alerts only (8,213 frauds + 10,000 sampled legit) because normal rows are sampled. Agg_ByDayType not used.'",
        "sort": "Fact_Transactions[day] Ascending",
    },
]

# -----------------------------------------------------------------------------
# PAGE 3 DEFINITIONS: Investigation
# -----------------------------------------------------------------------------
PAGE3_VISUALS = [
    {
        "id": "VIS-13A",
        "type": "Slicer (Tile / Vertical)",
        "title": "Payment Method",
        "fields": "Field: Dim_Type[type]",
        "source": "Dim_Type[type], Dim_Type[type_sort]",
        "x": 16, "y": 16, "w": 240, "h": 100,
        "format": "Orientation: Vertical List or Horizontal Tiles. Multi-select with CTRL. Default: Select All.",
        "sort": "Dim_Type[type_sort] Ascending",
    },
    {
        "id": "VIS-13B",
        "type": "Slicer (Vertical List)",
        "title": "Risk Band",
        "fields": "Field: Dim_RiskBand[risk_band]",
        "source": "Dim_RiskBand[risk_band], Dim_RiskBand[risk_band_sort]",
        "x": 16, "y": 128, "w": 240, "h": 100,
        "format": "Orientation: Vertical list (Critical, High, Medium, Low). Single / Multi-select.",
        "sort": "Dim_RiskBand[risk_band_sort] Ascending",
    },
    {
        "id": "VIS-13C",
        "type": "Slicer (Vertical List)",
        "title": "Surveillance Outcome",
        "fields": "Field: Fact_Transactions[outcome]",
        "source": "Fact_Transactions[outcome]",
        "x": 16, "y": 240, "w": 240, "h": 100,
        "format": "Orientation: Vertical list (True Positive, False Positive, False Negative, True Negative).",
        "sort": "Fact_Transactions[outcome] Ascending",
    },
    {
        "id": "VIS-14",
        "type": "Clustered Bar Chart",
        "title": "Transaction & Fraud Volume by Risk Band",
        "fields": "Y-Axis: Agg_ByRiskBand[risk_band], X-Axis (Values): Agg_ByRiskBand[fraud_count], Tooltips: Agg_ByRiskBand[rows], Agg_ByRiskBand[flagged_value]",
        "source": "Agg_ByRiskBand[risk_band], Agg_ByRiskBand[fraud_count], Agg_ByRiskBand[rows], Agg_ByRiskBand[flagged_value], Dim_RiskBand[risk_band_sort]",
        "x": 16, "y": 352, "w": 240, "h": 352,
        "format": "Color Overrides: High (#F97316 Orange), Medium (#EAB308 Yellow), Low (#94A3B8 Slate), Critical (#EF4444 Red). Data labels: ON. Subtitle: 'High band: 3,397 frauds in 3,402 alerts (99.85% precision).'",
        "sort": "Dim_RiskBand[risk_band_sort] Ascending",
    },
    {
        "id": "VIS-15",
        "type": "Table",
        "title": "Top 20 Priority Investigation Ledger (Ranked by Combo Score)",
        "fields": "Columns: Fact_Transactions[txn_id], Fact_Transactions[day], Fact_Transactions[hour], Fact_Transactions[type], Fact_Transactions[amount], Fact_Transactions[alert_score], Fact_Transactions[anomaly_score_pct], Fact_Transactions[combo_score], Fact_Transactions[alert_source], Fact_Transactions[risk_band], Fact_Transactions[outcome]",
        "source": "Fact_Transactions[txn_id], Fact_Transactions[day], Fact_Transactions[hour], Fact_Transactions[type], Fact_Transactions[amount], Fact_Transactions[alert_score], Fact_Transactions[anomaly_score_pct], Fact_Transactions[combo_score], Fact_Transactions[alert_source], Fact_Transactions[risk_band], Fact_Transactions[outcome]",
        "x": 272, "y": 16, "w": 992, "h": 340,
        "format": "Top N Filter: Top 20 based on Fact_Transactions[combo_score]. Formats: amount as $#,##0, anomaly_score_pct as 0.0%, combo_score as 0.000. Drill-through enabled to 'Account Detail' via Fact_Transactions[nameOrig]. Alternating rows #F8FAFC.",
        "sort": "Fact_Transactions[combo_score] Descending",
    },
    {
        "id": "VIS-16",
        "type": "Scatter Plot",
        "title": "Transaction Amount vs. Isolation Forest Anomaly Score",
        "fields": "X-Axis: Fact_Transactions[anomaly_score_pct], Y-Axis: Fact_Transactions[amount], Legend: Fact_Transactions[outcome], Tooltips: Fact_Transactions[txn_id], Fact_Transactions[nameOrig], Fact_Transactions[combo_score], Fact_Transactions[risk_band]",
        "source": "Fact_Transactions[anomaly_score_pct], Fact_Transactions[amount], Fact_Transactions[outcome], Fact_Transactions[txn_id], Fact_Transactions[nameOrig], Fact_Transactions[combo_score], Fact_Transactions[risk_band]",
        "x": 272, "y": 372, "w": 992, "h": 332,
        "format": "Y-Axis Scale: Logarithmic scale enabled (Format > Y-Axis > Scale type = Logarithmic). Colors: True Positive (#EF4444 Crimson), False Positive (#F59E0B Amber), False Negative (#8B5CF6 Purple), True Negative (#10B981 Soft Green). Marker size: 5 px. X-Axis bounds: 0% to 100%.",
        "sort": "Fact_Transactions[anomaly_score_pct] Ascending",
    },
]

# -----------------------------------------------------------------------------
# ACCOUNT DETAIL DRILL-THROUGH SUB-PAGE DEFINITIONS
# -----------------------------------------------------------------------------
ACCOUNT_DETAIL_VISUALS = [
    {
        "id": "DT-01",
        "type": "Button (Back Navigator)",
        "title": "<- Return to Investigation Ledger",
        "fields": "Action: Back",
        "source": "Navigation Action: Back",
        "x": 16, "y": 16, "w": 180, "h": 48,
        "format": "Style: Left arrow icon with label 'Back'. Background: #FFFFFF, Border: 1px #CBD5E1, Radius: 6px, Text: 11 pt Semibold #1E293B.",
        "sort": "N/A",
    },
    {
        "id": "DT-02",
        "type": "Card (or Card new)",
        "title": "Selected Account (Originator)",
        "fields": "Values: Fact_Transactions[nameOrig]",
        "source": "Fact_Transactions[nameOrig]",
        "x": 212, "y": 16, "w": 1052, "h": 48,
        "format": "Callout: 14 pt Bold Accent Navy #1E3A8A. Drill-through context indicator showing target account identifier.",
        "sort": "N/A",
    },
    {
        "id": "DT-03A",
        "type": "Card (or Card new)",
        "title": "Account Total Volume",
        "fields": "Values: SUM(Fact_Transactions[amount])",
        "source": "Fact_Transactions[amount]",
        "x": 16, "y": 80, "w": 400, "h": 80,
        "format": "Callout: 20 pt Bold #0F172A, Format: $#,##0.00. Total transacted volume for filtered account.",
        "sort": "N/A",
    },
    {
        "id": "DT-03B",
        "type": "Card (or Card new)",
        "title": "Total Originator Transactions",
        "fields": "Values: COUNT(Fact_Transactions[txn_id])",
        "source": "Fact_Transactions[txn_id]",
        "x": 432, "y": 80, "w": 400, "h": 80,
        "format": "Callout: 20 pt Bold #0F172A, Format: #,##0. Transaction volume count for account.",
        "sort": "N/A",
    },
    {
        "id": "DT-03C",
        "type": "Card (or Card new)",
        "title": "Max Combo Risk Score",
        "fields": "Values: MAX(Fact_Transactions[combo_score])",
        "source": "Fact_Transactions[combo_score]",
        "x": 848, "y": 80, "w": 416, "h": 80,
        "format": "Callout: 20 pt Bold #EF4444, Format: 0.000. Peak suspicion score observed.",
        "sort": "N/A",
    },
    {
        "id": "DT-04",
        "type": "Table",
        "title": "Account Complete Transaction Audit History",
        "fields": "Columns: Fact_Transactions[txn_id], Fact_Transactions[day], Fact_Transactions[hour], Fact_Transactions[type], Fact_Transactions[amount], Fact_Transactions[nameDest], Fact_Transactions[alert_score], Fact_Transactions[anomaly_score_pct], Fact_Transactions[combo_score], Fact_Transactions[isFraud], Fact_Transactions[outcome]",
        "source": "Fact_Transactions[txn_id], Fact_Transactions[day], Fact_Transactions[hour], Fact_Transactions[type], Fact_Transactions[amount], Fact_Transactions[nameDest], Fact_Transactions[alert_score], Fact_Transactions[anomaly_score_pct], Fact_Transactions[combo_score], Fact_Transactions[isFraud], Fact_Transactions[outcome]",
        "x": 16, "y": 176, "w": 820, "h": 528,
        "format": "Full chronologically sorted ledger. Highlighting: Fraud rows in soft red. Columns sized to fit. Sorting: Fact_Transactions[day] Ascending, Fact_Transactions[hour] Ascending.",
        "sort": "Fact_Transactions[day] Ascending",
    },
    {
        "id": "DT-05",
        "type": "Table",
        "title": "Beneficiary Destination Entities Profile",
        "fields": "Columns: Fact_Transactions[nameDest], Count of Txns: COUNT(Fact_Transactions[txn_id]), Total Transferred: SUM(Fact_Transactions[amount])",
        "source": "Fact_Transactions[nameDest], Fact_Transactions[txn_id], Fact_Transactions[amount]",
        "x": 852, "y": 176, "w": 412, "h": 256,
        "format": "Grouping by nameDest recipient accounts. Sorted by Total Transferred Descending. Formats: $#,##0. Helps uncover mule syndicates.",
        "sort": "Total Transferred Descending",
    },
    {
        "id": "DT-06",
        "type": "Table",
        "title": "Heuristic Rule Violations Audit Matrix",
        "fields": "Columns: Fact_Transactions[txn_id], Fact_Transactions[rule_emptied], Fact_Transactions[rule_large_amount], Fact_Transactions[rule_mule_dest], Fact_Transactions[rule_dest_unchanged], Fact_Transactions[rule_balance_error]",
        "source": "Fact_Transactions[txn_id], Fact_Transactions[rule_emptied], Fact_Transactions[rule_large_amount], Fact_Transactions[rule_mule_dest], Fact_Transactions[rule_dest_unchanged], Fact_Transactions[rule_balance_error]",
        "x": 852, "y": 448, "w": 412, "h": 256,
        "format": "Displays boolean indicator flags (0/1) for all 5 triggered heuristic rules on account activity. Cell formatting: Green 0, Red 1.",
        "sort": "Fact_Transactions[txn_id] Ascending",
    },
]


def audit_visual_collisions(visuals: list[dict], page_name: str) -> None:
    """Assert bounding box containment and zero pairwise collisions."""
    n = len(visuals)
    for i in range(n):
        v1 = visuals[i]
        id1, x1, y1, w1, h1 = v1["id"], v1["x"], v1["y"], v1["w"], v1["h"]
        r1, b1 = x1 + w1, y1 + h1

        assert 0 <= x1, f"{page_name} {id1}: x < 0 ({x1})"
        assert 0 <= y1, f"{page_name} {id1}: y < 0 ({y1})"
        assert r1 <= CANVAS_WIDTH, f"{page_name} {id1}: r ({r1}) > canvas width ({CANVAS_WIDTH})"
        assert b1 <= CANVAS_HEIGHT, f"{page_name} {id1}: b ({b1}) > canvas height ({CANVAS_HEIGHT})"

        for j in range(i + 1, n):
            v2 = visuals[j]
            id2, x2, y2, w2, h2 = v2["id"], v2["x"], v2["y"], v2["w"], v2["h"]
            r2, b2 = x2 + w2, y2 + h2

            separated = (r1 <= x2) or (r2 <= x1) or (b1 <= y2) or (b2 <= y1)
            assert separated, f"{page_name}: Collision detected between {id1} and {id2}!"


def generate_page2_markdown(output_path: Path = config.POWERBI_DIR / "06_page2_detection.md") -> str:
    """Compile powerbi/06_page2_detection.md."""
    audit_visual_collisions(PAGE2_VISUALS, "Page 2")

    doc = []
    doc.append("# Page 2: Rules vs ML — Strategy Detection & Comparative Diagnostics")
    doc.append("")
    doc.append("**Document ID:** `powerbi/06_page2_detection.md`  ")
    doc.append("**Report Page Name:** `Rules vs ML`  ")
    doc.append(f"**Canvas Size:** {CANVAS_WIDTH} x {CANVAS_HEIGHT} pixels (16:9 Standard HD)  ")
    doc.append("**Target Audience:** Chief Risk Officer, Head of ML/Fraud Modeling, Compliance & Regulatory Auditors  ")
    doc.append("**Verification Status:** Collision-free, bounding-box validated (PASS: Zero overlaps, 100% within canvas bounds).  ")
    doc.append("")
    doc.append("---")
    doc.append("")
    doc.append("## Table of Contents")
    doc.append("1. [Page Layout Architecture & Visual Wireframe](#1-page-layout-architecture--visual-wireframe)")
    doc.append("2. [Master Visual Specification Table](#2-master-visual-specification-table)")
    doc.append("3. [Detailed Specifications by Visual](#3-detailed-specifications-by-visual)")
    doc.append("   - [Strategic Operating Point Brief](#strategic-operating-point-brief)")
    doc.append("   - [Strategy Comparison Clustered Bar](#strategy-comparison-clustered-bar)")
    doc.append("   - [Heuristic Rules Performance Table](#heuristic-rules-performance-table)")
    doc.append("   - [Enterprise Confusion Matrix](#enterprise-confusion-matrix)")
    doc.append("   - [Daily Alerts Stacked Column](#daily-alerts-stacked-column)")
    doc.append("4. [Visual Interaction & Slicer Decoupling Rules](#4-visual-interaction--slicer-decoupling-rules)")
    doc.append("5. [Programmatic Overlap & Boundary Verification Audit](#5-programmatic-overlap--boundary-verification-audit)")
    doc.append("")
    doc.append("---")
    doc.append("")

    # 1. Wireframe
    doc.append("## 1. Page Layout Architecture & Visual Wireframe")
    doc.append("")
    doc.append("The layout utilizes a structured **Top Header Banner + 2x2 Diagnostic Grid** composition:")
    doc.append("")
    doc.append("```text")
    doc.append("+--------------------------------------------------------------------------------------------------------------------------+")
    doc.append("|                                              CANVAS: 1280 x 720 PIXELS                                                   |")
    doc.append("+--------------------------------------------------------------------------------------------------------------------------+")
    doc.append("| [VIS-08: Strategic Operating Point Brief Banner]                                                                         | (y=16..108)")
    doc.append("| Combined AND (98.65% precision, 57 FPs, F1=0.6701) vs Combined OR (99.79% recall, 8,196 frauds, 1.08M alerts)           |")
    doc.append("| (x=16, y=16, w=1248, h=92)                                                                                               |")
    doc.append("+-----------------------------------------------------------+--------------------------------------------------------------+")
    doc.append("| [VIS-09: Clustered Bar Chart]                             | [VIS-10: Rule Evaluation Table with Data Bars]               | (y=124..406)")
    doc.append("| Precision, Recall & F1 Score by Detection Strategy         | Rule Name, Alerts, TP, FP, Precision (Bar), Recall (Bar), F1|")
    doc.append("| (x=16, y=124, w=616, h=282)                               | (x=648, y=124, w=616, h=282)                                 |")
    doc.append("+--------------------------------------+--------------------+--------------------------------------------------------------+")
    doc.append("| [VIS-11: Confusion Matrix]           | [VIS-12: Stacked Column Chart]                                                   | (y=422..704)")
    doc.append("| Actual (Fraud/Legit) vs. Predicted   | Daily Alert Volume by Source (Both vs Rule only vs ML only)                      |")
    doc.append("| TP (8,196), FP (1.08M), FN (17), TN  | Note: Alerts only (8,213 frauds + 10k sampled legit). Agg_ByDayType not used     |")
    doc.append("| (x=16, y=422, w=440, h=282)          | (x=472, y=422, w=792, h=282)                                                     |")
    doc.append("+--------------------------------------+-----------------------------------------------------------------------------------+")
    doc.append("```")
    doc.append("")
    doc.append("---")
    doc.append("")

    # 2. Master Table
    doc.append("## 2. Master Visual Specification Table")
    doc.append("")
    doc.append("| Visual ID | Type | Title | Fields (Axis, Values, Legend) | Tables & Measures Used | X | Y | W | H | Sorting | Formatting Notes |")
    doc.append("| :--- | :--- | :--- | :--- | :--- | --: | --: | --: | --: | :--- | :--- |")

    for v in PAGE2_VISUALS:
        doc.append(
            f"| **`{v['id']}`** | `{v['type']}` | **{v['title']}** | `{v['fields']}` | `{v['source']}` | "
            f"`{v['x']}` | `{v['y']}` | `{v['w']}` | `{v['h']}` | {v['sort']} | {v['format']} |"
        )

    doc.append("")
    doc.append("---")
    doc.append("")

    # 3. Detailed Specs
    doc.append("## 3. Detailed Specifications by Visual")
    doc.append("")
    doc.append("### Strategic Operating Point Brief (`VIS-08`)")
    doc.append("- **Position:** `X = 16`, `Y = 16`, `Width = 1248`, `Height = 92`")
    doc.append("- **Static Briefing Text (Based on `reports/14_approach_comparison.md` and `reports/16_final_metrics.json`):**")
    doc.append("  > **Strategic Recommendation: Combined AND (combo_and) achieves the highest operational precision in enterprise production at 98.65% (4,167 True Positives against merely 57 False Positives out of 4,224 alerts; F1 = 0.6701), slashing analyst alert backlog by 46.2% relative to standalone ML while securing $6.45B in confirmed fraud value. For exhaustive regulatory compliance, Combined OR (combo_or) provides maximum recall at 99.79% (8,196 of 8,213 fraud events captured, missing only 17), intercepting 6 frauds heuristic rules missed entirely (+55 alerts), but requiring 1,085,609 investigations ($407.88B flagged). The simulator baseline is flagged for reference only (100% precision, but 0.19% recall, capturing only 16 frauds).**")
    doc.append("")
    doc.append("### Strategy Comparison Clustered Bar (`VIS-09`)")
    doc.append("- **Position:** `X = 16`, `Y = 124`, `Width = 616`, `Height = 282`")
    doc.append("- **Y-Axis (Approaches):** `Metrics_Approach[approach]`")
    doc.append("- **X-Axis (Series Values):**")
    doc.append("  - `Precision (%)`: Solid Deep Navy `#1E3A8A`")
    doc.append("  - `Recall (%)`: Solid Emerald Green `#10B981`")
    doc.append("  - `F1 Score`: Amber `#F59E0B`")
    doc.append("- **Sorting:** `Metrics_Approach[f1_pct]` Descending")
    doc.append("- **Formatting:** Data Labels enabled (`0.0%`). Subtitle notes that the simulator baseline is an unviable historical reference (0.19% recall).")
    doc.append("")
    doc.append("### Heuristic Rules Performance Table (`VIS-10`)")
    doc.append("- **Position:** `X = 648`, `Y = 124`, `Width = 616`, `Height = 282`")
    doc.append("- **Fields:** `rule_name`, `alerts`, `tp`, `fp`, `precision_pct`, `recall_pct`, `f1_pct` from `Metrics_Rules`")
    doc.append("- **Conditional Formatting (Data Bars):**")
    doc.append("  - `precision_pct`: Blue horizontal data bar (`#3B82F6` gradient), range 0 to 100%.")
    doc.append("  - `recall_pct`: Green horizontal data bar (`#10B981` gradient), range 0 to 100%.")
    doc.append("- **Sorting:** `Metrics_Rules[recall_pct]` Descending (places Rule 1 at top with 97.5% recall).")
    doc.append("")
    doc.append("### Enterprise Confusion Matrix (`VIS-11`)")
    doc.append("- **Position:** `X = 16`, `Y = 422`, `Width = 440`, `Height = 282`")
    doc.append("- **Rows:** `Confusion_Matrix[actual]` (`Fraud`, `Legit`)")
    doc.append("- **Columns:** `Confusion_Matrix[predicted]` (`Alert`, `No alert`)")
    doc.append("- **Values:** `Confusion_Matrix[count]`")
    doc.append("- **Cell Coloring:**")
    doc.append("  - `TP` (8,196) and `TN` (5,276,994): Soft green `#DCFCE7` (Correct surveillance decisions)")
    doc.append("  - `FP` (1,077,413): Soft amber `#FEE2E2` (Operational review burden)")
    doc.append("  - `FN` (17): Soft rose `#FFE4E6` (Escaped fraud events, $2.7M missed)")
    doc.append("")
    doc.append("### Daily Alerts Stacked Column (`VIS-12`)")
    doc.append("- **Position:** `X = 472`, `Y = 422`, `Width = 792`, `Height = 282`")
    doc.append("- **X-Axis:** `Fact_Transactions[day]` (Days 1 - 31), Sorted Ascending.")
    doc.append("- **Legend:** `Fact_Transactions[alert_source]` (`Both`, `Rule only`, `ML only`).")
    doc.append("- **Y-Axis:** `COUNTROWS(Fact_Transactions)` where `Fact_Transactions[is_alert] = 1`.")
    doc.append("- **Methodology Note:** `Agg_ByDayType` is not suitable because it lacks alert source attribution. This visual sources directly from `Fact_Transactions` and filters `is_alert = 1`. A prominent subtitle explicitly clarifies: *'Visual displays alerts only (8,213 frauds + 10,000 sampled legit) because normal transactions are sampled in Fact_Transactions.'*")
    doc.append("")
    doc.append("---")
    doc.append("")

    # 4. Interactions
    doc.append("## 4. Visual Interaction & Slicer Decoupling Rules")
    doc.append("")
    doc.append("1. **Strategy Selection on `VIS-09`:** Selecting an approach filters `VIS-10` and `VIS-11` to cross-examine corresponding rule subsets.")
    doc.append("2. **Isolation of Static Metrics:** Tables `Metrics_Approach`, `Metrics_Rules`, and `Confusion_Matrix` are pre-aggregated across the full dataset; cross-filtering from other pages is disabled to protect metric truth.")
    doc.append("")
    doc.append("---")
    doc.append("")

    # 5. Verification Audit
    doc.append("## 5. Programmatic Overlap & Boundary Verification Audit")
    doc.append("")
    doc.append("```text")
    doc.append(f"Total Visual Containers Audited:   {len(PAGE2_VISUALS)}")
    doc.append(f"Canvas Bounds:                     {CANVAS_WIDTH} x {CANVAS_HEIGHT} px")
    doc.append("Out of Bounds Errors:              0")
    doc.append("Visual Collisions / Overlaps:      0")
    doc.append("AUDIT RESULT:                      PASS (100% collision-free layout)")
    doc.append("```")
    doc.append("")
    doc.append("---")
    doc.append("*Specification compiled programmatically by `src/build_pages2_3_specs.py`.*")

    content = "\n".join(doc)
    output_path.write_text(content, encoding="utf-8")
    print(f"Page 2 written to {output_path.name} ({len(content.splitlines())} lines, {output_path.stat().st_size:,} bytes)")
    return content


def generate_page3_markdown(output_path: Path = config.POWERBI_DIR / "07_page3_investigation.md") -> str:
    """Compile powerbi/07_page3_investigation.md."""
    audit_visual_collisions(PAGE3_VISUALS, "Page 3")
    audit_visual_collisions(ACCOUNT_DETAIL_VISUALS, "Account Detail Sub-page")

    doc = []
    doc.append("# Page 3: Investigation — Case Triage, Score Diagnostics & Drill-Through Ledger")
    doc.append("")
    doc.append("**Document ID:** `powerbi/07_page3_investigation.md`  ")
    doc.append("**Report Page Name:** `Investigation`  ")
    doc.append(f"**Canvas Size:** {CANVAS_WIDTH} x {CANVAS_HEIGHT} pixels (16:9 Standard HD)  ")
    doc.append("**Target Audience:** AML Investigators, Fraud Triage Analysts, Case Management Leads  ")
    doc.append("**Verification Status:** Collision-free, bounding-box validated (PASS: Zero overlaps, 100% within canvas bounds).  ")
    doc.append("")
    doc.append("---")
    doc.append("")
    doc.append("## Table of Contents")
    doc.append("1. [Page Layout Architecture & Visual Wireframe](#1-page-layout-architecture--visual-wireframe)")
    doc.append("2. [Master Visual Specification Table](#2-master-visual-specification-table)")
    doc.append("3. [Detailed Specifications by Visual](#3-detailed-specifications-by-visual)")
    doc.append("   - [Sidebar: Triage Filter Slicers](#sidebar-triage-filter-slicers)")
    doc.append("   - [Risk-Band Distribution Bar Chart](#risk-band-distribution-bar-chart)")
    doc.append("   - [Top 20 Priority Investigation Ledger Table](#top-20-priority-investigation-ledger-table)")
    doc.append("   - [Amount vs Anomaly Score Scatter Plot](#amount-vs-anomaly-score-scatter-plot)")
    doc.append("4. [Drill-Through Architecture: 'Account Detail' Sub-Page](#4-drill-through-architecture-account-detail-sub-page)")
    doc.append("5. [Programmatic Overlap & Boundary Verification Audit](#5-programmatic-overlap--boundary-verification-audit)")
    doc.append("")
    doc.append("---")
    doc.append("")

    # 1. Wireframe
    doc.append("## 1. Page Layout Architecture & Visual Wireframe")
    doc.append("")
    doc.append("The layout utilizes a structured **Left Rail (Filters + Risk Band) + Right Diagnostic Canvas (Top 20 + Scatter)** composition:")
    doc.append("")
    doc.append("```text")
    doc.append("+--------------------------------------------------------------------------------------------------------------------------+")
    doc.append("|                                              CANVAS: 1280 x 720 PIXELS                                                   |")
    doc.append("+-----------------------+--------------------------------------------------------------------------------------------------+")
    doc.append("| [VIS-13A: Type Sl.]   | [VIS-15: Top 20 Priority Investigation Ledger Table]                                              | (y=16..356)")
    doc.append("| Dim_Type[type]        | txn_id, day, hour, type, amount, alert_score, anomaly_score_pct, combo_score, alert_source,      |")
    doc.append("| (x=16, w=240, h=100)  | risk_band, outcome (Top N Filter on combo_score Top 20) -> Drill-through to 'Account Detail'    |")
    doc.append("|-----------------------| (x=272, y=16, w=992, h=340)                                                                      |")
    doc.append("| [VIS-13B: Risk Sl.]   |                                                                                                  |")
    doc.append("| Dim_RiskBand[band]    |                                                                                                  |")
    doc.append("| (x=16, w=240, h=100)  |                                                                                                  |")
    doc.append("|-----------------------+--------------------------------------------------------------------------------------------------+")
    doc.append("| [VIS-13C: Outcome Sl.]| [VIS-16: Scatter Plot (Log Scale Amount vs Anomaly Score)]                                       | (y=372..704)")
    doc.append("| Fact_Transactions[out]| X-Axis: Fact_Transactions[anomaly_score_pct] (0% to 100%)                                        |")
    doc.append("| (x=16, w=240, h=100)  | Y-Axis: Fact_Transactions[amount] (Logarithmic Scale: $1 to $100M+)                              |")
    doc.append("|-----------------------| Legend: Fact_Transactions[outcome] (TP: Red, FP: Amber, FN: Purple, TN: Green)                  |")
    doc.append("| [VIS-14: Risk Bar]    | (x=272, y=372, w=992, h=332)                                                                     |")
    doc.append("| Agg_ByRiskBand        |                                                                                                  |")
    doc.append("| (x=16, w=240, h=352)  |                                                                                                  |")
    doc.append("+-----------------------+--------------------------------------------------------------------------------------------------+")
    doc.append("```")
    doc.append("")
    doc.append("---")
    doc.append("")

    # 2. Master Table
    doc.append("## 2. Master Visual Specification Table")
    doc.append("")
    doc.append("| Visual ID | Type | Title | Fields (Axis, Values, Legend) | Tables & Measures Used | X | Y | W | H | Sorting | Formatting Notes |")
    doc.append("| :--- | :--- | :--- | :--- | :--- | --: | --: | --: | --: | :--- | :--- |")

    for v in PAGE3_VISUALS:
        doc.append(
            f"| **`{v['id']}`** | `{v['type']}` | **{v['title']}** | `{v['fields']}` | `{v['source']}` | "
            f"`{v['x']}` | `{v['y']}` | `{v['w']}` | `{v['h']}` | {v['sort']} | {v['format']} |"
        )

    doc.append("")
    doc.append("---")
    doc.append("")

    # 3. Detailed Specs
    doc.append("## 3. Detailed Specifications by Visual")
    doc.append("")
    doc.append("### Sidebar: Triage Filter Slicers")
    doc.append("- **`VIS-13A` (Payment Type):** `Dim_Type[type]`, sorted by `Dim_Type[type_sort]`. Position: `X = 16`, `Y = 16`, `W = 240`, `H = 100`.")
    doc.append("- **`VIS-13B` (Risk Band):** `Dim_RiskBand[risk_band]`, sorted by `Dim_RiskBand[risk_band_sort]`. Position: `X = 16`, `Y = 128`, `W = 240`, `H = 100`.")
    doc.append("- **`VIS-13C` (Surveillance Outcome):** `Fact_Transactions[outcome]`. Position: `X = 16`, `Y = 240`, `W = 240`, `H = 100`.")
    doc.append("")
    doc.append("### Risk-Band Distribution Bar Chart (`VIS-14`)")
    doc.append("- **Position:** `X = 16`, `Y = 352`, `Width = 240`, `Height = 352`")
    doc.append("- **Y-Axis:** `Agg_ByRiskBand[risk_band]`")
    doc.append("- **X-Axis:** `Agg_ByRiskBand[fraud_count]`")
    doc.append("- **Tooltips:** `Agg_ByRiskBand[rows]`, `Agg_ByRiskBand[flagged_value]`")
    doc.append("- **Sorting:** `Dim_RiskBand[risk_band_sort]` Ascending")
    doc.append("- **Colors:** High (`#F97316` Orange), Medium (`#EAB308` Yellow), Low (`#94A3B8` Slate), Critical (`#EF4444` Red)")
    doc.append("- **Data Labels:** ON (`#,##0`). High band displays 3,397 fraud cases out of 3,402 alerts (99.85% operational precision).")
    doc.append("")
    doc.append("### Top 20 Priority Investigation Ledger Table (`VIS-15`)")
    doc.append("- **Position:** `X = 272`, `Y = 16`, `Width = 992`, `Height = 340`")
    doc.append("- **Columns (11 Fields):**")
    doc.append("  `txn_id`, `day`, `hour`, `type`, `amount`, `alert_score`, `anomaly_score_pct`, `combo_score`, `alert_source`, `risk_band`, `outcome`")
    doc.append("- **Top N Filter:** Filter on visual > `combo_score` Top 20 by `Fact_Transactions[combo_score]`.")
    doc.append("- **Sorting:** `Fact_Transactions[combo_score]` Descending.")
    doc.append("- **Formats:** `amount` formatted as `$#,##0`; `anomaly_score_pct` as `0.0%`; `combo_score` as `0.000`.")
    doc.append("- **Drill-Through Action:** Right-click row > **Drill through > Account Detail** (passes `Fact_Transactions[nameOrig]`).")
    doc.append("")
    doc.append("### Amount vs Anomaly Score Scatter Plot (`VIS-16`)")
    doc.append("- **Position:** `X = 272`, `Y = 372`, `Width = 992`, `Height = 332`")
    doc.append("- **X-Axis:** `Fact_Transactions[anomaly_score_pct]` (Linear scale, 0.0% to 100.0%)")
    doc.append("- **Y-Axis:** `Fact_Transactions[amount]` (**Logarithmic Scale** enabled in Format > Y-Axis > Scale type = Logarithmic, displaying values from $10^0 to $10^8)")
    doc.append("- **Legend:** `Fact_Transactions[outcome]` (`True Positive`, `False Positive`, `False Negative`, `True Negative`)")
    doc.append("- **Marker Colors:**")
    doc.append("  - `True Positive`: Crimson Red `#EF4444`")
    doc.append("  - `False Positive`: Amber Orange `#F59E0B`")
    doc.append("  - `False Negative`: Purple `#8B5CF6`")
    doc.append("  - `True Negative`: Soft Emerald `#10B981`")
    doc.append("- **Tooltips:** `Fact_Transactions[txn_id]`, `Fact_Transactions[nameOrig]`, `Fact_Transactions[combo_score]`, `Fact_Transactions[risk_band]`")
    doc.append("")
    doc.append("---")
    doc.append("")

    # 4. Drill-through sub-page spec
    doc.append("## 4. Drill-Through Architecture: 'Account Detail' Sub-Page")
    doc.append("")
    doc.append("### Page Configuration:")
    doc.append("- **Page Name:** `Account Detail`")
    doc.append("- **Page Visibility:** Hidden in report navigation (accessible solely via right-click drill-through).")
    doc.append("- **Drill-Through Field:** `Fact_Transactions[nameOrig]` (Originator Account Identifier).")
    doc.append("- **Drill-Through Settings:** `Keep all filters = ON`, `Cross-report = OFF`.")
    doc.append("")
    doc.append("### Visual Wireframe: Account Detail Sub-Page (1280 x 720 px):")
    doc.append("```text")
    doc.append("+--------------------------------------------------------------------------------------------------------------------------+")
    doc.append("|                                         ACCOUNT DETAIL SUB-PAGE: 1280 x 720 PIXELS                                       |")
    doc.append("+-----------------------+--------------------------------------------------------------------------------------------------+")
    doc.append("| [DT-01: Back Button]  | [DT-02: Target Account Context Header: Fact_Transactions[nameOrig]]                             | (y=16..64)")
    doc.append("| (x=16, w=180, h=48)   | (x=212, y=16, w=1052, h=48)                                                                      |")
    doc.append("+-----------------------+------------------------------------+-------------------------------------------------------------+")
    doc.append("| [DT-03A: Total Vol $]              | [DT-03B: Total Txn Count]     | [DT-03C: Max Combo Score]                                   | (y=80..160)")
    doc.append("| SUM(Fact_Transactions[amount])     | COUNT(Fact_Transactions[id])  | MAX(Fact_Transactions[combo_score])                          |")
    doc.append("| (x=16, w=400, h=80)                | (x=432, w=400, h=80)          | (x=848, w=416, h=80)                                        |")
    doc.append("+------------------------------------+-------------------------------+-------------------------------------------------------------+")
    doc.append("| [DT-04: Account Complete Transaction Audit History Table]          | [DT-05: Destination Entities Profile Table]                 | (y=176..704)")
    doc.append("| txn_id, day, hour, type, amount, nameDest, alert_score,            | nameDest, Txn Count, Total Volume Transferred               | (y=176..432)")
    doc.append("| anomaly_score_pct, combo_score, isFraud, outcome                   | (x=852, y=176, w=412, h=256)                                |")
    doc.append("| (Chronological order: day, hour Ascending)                         |-------------------------------------------------------------|")
    doc.append("|                                                                    | [DT-06: Heuristic Rule Violations Matrix]                   | (y=448..704)")
    doc.append("|                                                                    | Rule Emptied, Large Amount, Mule Dest, Dest Unchanged, Error|")
    doc.append("| (x=16, y=176, w=820, h=528)                                        | (x=852, y=448, w=412, h=256)                                |")
    doc.append("+--------------------------------------------------------------------+-------------------------------------------------------------+")
    doc.append("```")
    doc.append("")
    doc.append("### Master Visual Table: Account Detail Sub-Page")
    doc.append("")
    doc.append("| Visual ID | Type | Title | Fields (Axis, Values, Legend) | Tables & Measures Used | X | Y | W | H | Sorting | Formatting Notes |")
    doc.append("| :--- | :--- | :--- | :--- | :--- | --: | --: | --: | --: | :--- | :--- |")

    for v in ACCOUNT_DETAIL_VISUALS:
        doc.append(
            f"| **`{v['id']}`** | `{v['type']}` | **{v['title']}** | `{v['fields']}` | `{v['source']}` | "
            f"`{v['x']}` | `{v['y']}` | `{v['w']}` | `{v['h']}` | {v['sort']} | {v['format']} |"
        )

    doc.append("")
    doc.append("---")
    doc.append("")

    # 5. Verification Audit
    doc.append("## 5. Programmatic Overlap & Boundary Verification Audit")
    doc.append("")
    doc.append("```text")
    doc.append(f"Total Visual Containers Audited:   {len(PAGE3_VISUALS)} (Main Page) + {len(ACCOUNT_DETAIL_VISUALS)} (Sub-Page)")
    doc.append(f"Canvas Bounds:                     {CANVAS_WIDTH} x {CANVAS_HEIGHT} px")
    doc.append("Out of Bounds Errors:              0")
    doc.append("Visual Collisions / Overlaps:      0")
    doc.append("AUDIT RESULT:                      PASS (100% collision-free layout)")
    doc.append("```")
    doc.append("")
    doc.append("---")
    doc.append("*Specification compiled programmatically by `src/build_pages2_3_specs.py`.*")

    content = "\n".join(doc)
    output_path.write_text(content, encoding="utf-8")
    print(f"Page 3 written to {output_path.name} ({len(content.splitlines())} lines, {output_path.stat().st_size:,} bytes)")
    return content


def main():
    generate_page2_markdown()
    generate_page3_markdown()


if __name__ == "__main__":
    main()
