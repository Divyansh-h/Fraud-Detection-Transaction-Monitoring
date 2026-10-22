"""Programmatic KPI Cards Documentation Generator for Power BI Desktop.

Generates powerbi/04_kpi_cards.md specifying the 6 executive KPI cards for Page 1,
computes and audits exact pixel layout arithmetic on a 1280x720 canvas,
details visual interaction configurations, and formats color rules.
"""

from pathlib import Path
import sys
import time

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config

CANVAS_WIDTH = 1280
CANVAS_HEIGHT = 720
GUTTER = 16
LEFT_MARGIN = 16
RIGHT_MARGIN = 16
CARD_Y = 16
CARD_HEIGHT = 100

# Primary Layout: Left margin = 16, Right margin = 16, 5 gutters of 16 px
# Width remaining for 6 cards = 1280 - 16 - 16 - (5 * 16) = 1168 px
# Cards 1, 2, 5, 6 = 195 px; Cards 3, 4 = 194 px
LAYOUT_SPECS = [
    {
        "card_num": 1,
        "title": "Total Transactions",
        "measure_name": "[Total Transactions]",
        "source_table": "_Measures (or Agg_ByType[total_txns])",
        "width": 195,
        "number_format": "#,##0",
        "sample_display": "6,362,620",
        "callout_size": "24 pt (Bold)",
        "label_size": "11 pt (Semibold)",
        "color_type": "Static Neutral",
        "color_rule": "Primary Dark Slate `#0F172A` (Callout), Neutral Slate `#64748B` (Title/Label), Card Background `#FFFFFF`, Border 1px `#E2E8F0`.",
        "conditional_measure": "None",
        "interaction_note": "CRITICAL: Disable interactions from Alert Source and Risk Band slicers.",
        "business_meaning": "Full-universe transaction population. Sourced from 6.36M ground-truth census.",
    },
    {
        "card_num": 2,
        "title": "Total Alerts",
        "measure_name": "[Total Alerts]",
        "source_table": "_Measures (or Agg_ByType[alert_count])",
        "width": 195,
        "number_format": "#,##0",
        "sample_display": "1,085,609",
        "callout_size": "24 pt (Bold)",
        "label_size": "11 pt (Semibold)",
        "color_type": "Static Accent",
        "color_rule": "Accent Navy `#1E3A8A` (Callout), Slate `#64748B` (Label), Background `#FFFFFF`, Border 1px `#E2E8F0`.",
        "conditional_measure": "None",
        "interaction_note": "Filtered by Type, Day, and Hour slicers.",
        "business_meaning": "Total transactions flagged for investigator review under official Combined OR strategy.",
    },
    {
        "card_num": 3,
        "title": "Total Flagged Value",
        "measure_name": "[Total Flagged Value]",
        "source_table": "_Measures (or Agg_ByType[flagged_value])",
        "width": 194,
        "number_format": "$#,##0 (or $0.00B with Display Units = Billions)",
        "sample_display": "$407.88B",
        "callout_size": "24 pt (Bold)",
        "label_size": "11 pt (Semibold)",
        "color_type": "Static Neutral",
        "color_rule": "Dark Slate `#0F172A` (Callout), Slate `#64748B` (Label), Background `#FFFFFF`, Border 1px `#E2E8F0`.",
        "conditional_measure": "None",
        "interaction_note": "Filtered by Type, Day, and Hour slicers.",
        "business_meaning": "Total currency value of alerted transactions under review ($407,883,914,866.30).",
    },
    {
        "card_num": 4,
        "title": "Fraud Rate %",
        "measure_name": "[Fraud Rate %]",
        "source_table": "_Measures (DIVIDE([Fraud Count], [Total Transactions]))",
        "width": 194,
        "number_format": "0.000%",
        "sample_display": "0.129%",
        "callout_size": "24 pt (Bold)",
        "label_size": "11 pt (Semibold)",
        "color_type": "Static Neutral",
        "color_rule": "Dark Slate `#0F172A` (Callout), Slate `#64748B` (Label), Background `#FFFFFF`, Border 1px `#E2E8F0`.",
        "conditional_measure": "None",
        "interaction_note": "Filtered by Type slicer (shows 0.769% for TRANSFER, 0.184% for CASH_OUT, 0.000% others).",
        "business_meaning": "Baseline fraud occurrence prevalence (8,213 frauds / 6,362,620 transactions).",
    },
    {
        "card_num": 5,
        "title": "Alert Precision",
        "measure_name": "[Precision]",
        "source_table": "_Measures (DIVIDE([True Positives], [True Positives]+[False Positives]))",
        "width": 195,
        "number_format": "0.00%",
        "sample_display": "0.75%",
        "callout_size": "24 pt (Bold)",
        "label_size": "11 pt (Semibold)",
        "color_type": "Dynamic Conditional (Hex Measure)",
        "color_rule": "Driven by DAX measure `[Color - Precision KPI Card]`: Emerald Green `#2ECC71` if >= 90%, Amber `#F1C40F` if >= 50%, Coral Red `#E74C3C` if < 50%.",
        "conditional_measure": "[Color - Precision KPI Card]",
        "interaction_note": "Filtered by Type, Day, and Hour slicers.",
        "business_meaning": "Hit rate of alerts: 8,196 TP / (8,196 TP + 1,077,413 FP) = 0.755% under Combined OR safety net.",
    },
    {
        "card_num": 6,
        "title": "Fraud Recall",
        "measure_name": "[Recall]",
        "source_table": "_Measures (DIVIDE([True Positives], [True Positives]+[False Negatives]))",
        "width": 195,
        "number_format": "0.00%",
        "sample_display": "99.79%",
        "callout_size": "24 pt (Bold)",
        "label_size": "11 pt (Semibold)",
        "color_type": "Dynamic Conditional (Hex Measure)",
        "color_rule": "Driven by DAX measure `[Color - Recall KPI Card]`: Emerald Green `#2ECC71` if >= 99.0% (Current: 99.79%), Amber `#F1C40F` if >= 90.0%, Coral Red `#E74C3C` if < 90.0%.",
        "conditional_measure": "[Color - Recall KPI Card]",
        "interaction_note": "Filtered by Type, Day, and Hour slicers.",
        "business_meaning": "Detection capture coverage: 8,196 detected out of 8,213 total frauds (only 17 missed).",
    },
]


def compute_coordinates() -> list[dict]:
    """Calculate exact pixel coordinates and verify zero overlap and exact canvas fit."""
    current_x = LEFT_MARGIN
    cards_with_coords = []

    for item in LAYOUT_SPECS:
        w = item["width"]
        x = current_x
        y = CARD_Y
        h = CARD_HEIGHT
        x_end = x + w

        cards_with_coords.append({
            **item,
            "x": x,
            "y": y,
            "w": w,
            "h": h,
            "x_end": x_end,
        })
        current_x = x_end + GUTTER

    total_width_consumed = cards_with_coords[-1]["x_end"] + RIGHT_MARGIN
    assert total_width_consumed == CANVAS_WIDTH, f"Layout width mismatch: {total_width_consumed} != {CANVAS_WIDTH}"
    return cards_with_coords


def generate_kpi_cards_markdown(
    cards: list[dict],
    output_path: Path = config.POWERBI_DIR / "04_kpi_cards.md",
) -> str:
    """Compile powerbi/04_kpi_cards.md."""
    t0 = time.perf_counter()

    doc = []
    doc.append("# Page 1 Executive Overview: KPI Card Row Layout & Configuration Guide")
    doc.append("")
    doc.append("**Document ID:** `powerbi/04_kpi_cards.md`  ")
    doc.append("**Target Page:** Page 1 — Executive Overview  ")
    doc.append(f"**Canvas Dimensions:** {CANVAS_WIDTH} x {CANVAS_HEIGHT} pixels (Standard 16:9 HD)  ")
    doc.append(f"**KPI Row Geometry:** Height = {CARD_HEIGHT} px, Top Gutter (Y) = {CARD_Y} px, Inter-Card Gutter = {GUTTER} px  ")
    doc.append("**Visual Type:** Power BI `Card (new)` (Recommended) or 6 Individual `Card` Visual Containers  ")
    doc.append("**Verification:** Arithmetically validated down to the exact pixel.  ")
    doc.append("")
    doc.append("---")
    doc.append("")
    doc.append("## Table of Contents")
    doc.append("1. [Executive KPI Row Architecture & Visual Overview](#1-executive-kpi-row-architecture--visual-overview)")
    doc.append("2. [Exact Pixel Coordinates & Arithmetic Verification](#2-exact-pixel-coordinates--arithmetic-verification)")
    doc.append("3. [Detailed Specifications for Each of the 6 Cards](#3-detailed-specifications-for-each-of-the-6-cards)")
    doc.append("4. [Conditional Formatting Rules (Hex Strings & Thresholds)](#4-conditional-formatting-rules-hex-strings--thresholds)")
    doc.append("5. [Visual Interactions & Slicer Decoupling Rules](#5-visual-interactions--slicer-decoupling-rules)")
    doc.append("6. [Step-by-Step Implementation in Power BI Desktop](#6-step-by-step-implementation-in-power-bi-desktop)")
    doc.append("")
    doc.append("---")
    doc.append("")

    # Section 1
    doc.append("## 1. Executive KPI Row Architecture & Visual Overview")
    doc.append("")
    doc.append("The executive KPI header establishes the critical headline metrics for surveillance leaders and risk committees at first glance.")
    doc.append("It sits along the very top of **Page 1 (Executive Overview)** across `y = 16` to `y = 116`, spanning the full canvas width from `x = 16` to `x = 1264` (leaving 16 px margins on both sides).")
    doc.append("")
    doc.append("### The Six Executive Headline Metrics:")
    doc.append("1. **Total Transactions:** Full-universe business scale (6,362,620 transactions).")
    doc.append("2. **Total Alerts:** Total alert volume flagged for review under the official Combined OR definition (1,085,609 alerts).")
    doc.append("3. **Total Flagged Value:** Gross dollar exposure intercepted for investigator triage ($407.88 Billion).")
    doc.append("4. **Fraud Rate %:** Baseline enterprise fraud prevalence rate (0.129%).")
    doc.append("5. **Alert Precision:** Operational hit rate of triggered alerts (0.755% under Combined OR safety net).")
    doc.append("6. **Fraud Recall:** Executive surveillance coverage rate (99.793% — 8,196 of 8,213 frauds captured).")
    doc.append("")
    doc.append("---")
    doc.append("")

    # Section 2: Exact Pixel Coordinates & Arithmetic
    doc.append("## 2. Exact Pixel Coordinates & Arithmetic Verification")
    doc.append("")
    doc.append("To achieve pixel-perfect alignment in Power BI Desktop without manual eyeballing, use the exact coordinates below:")
    doc.append("")
    doc.append("### Coordinate Master Table (1280 x 720 Canvas):")
    doc.append("")
    doc.append("| Card # | Card Title | X (px) | Y (px) | Width (px) | Height (px) | Right Edge (X + W) | Next Gutter |")
    doc.append("| :-: | :--- | --: | --: | --: | --: | --: | :---: |")

    for c in cards:
        doc.append(
            f"| **Card {c['card_num']}** | **{c['title']}** | `{c['x']}` | `{c['y']}` | "
            f"`{c['w']}` | `{c['h']}` | `{c['x_end']}` | `{GUTTER} px` |"
        )

    doc.append("")
    doc.append("### Arithmetic Proof of Canvas Fit:")
    doc.append("```text")
    doc.append(f"Left Margin:                                                 {LEFT_MARGIN} px")
    doc.append(f"+ Card 1 Width:                                             {cards[0]['w']} px  (x = 16 to 211)")
    doc.append(f"+ Gutter 1:                                                  {GUTTER} px")
    doc.append(f"+ Card 2 Width:                                             {cards[1]['w']} px  (x = 227 to 422)")
    doc.append(f"+ Gutter 2:                                                  {GUTTER} px")
    doc.append(f"+ Card 3 Width:                                             {cards[2]['w']} px  (x = 438 to 632)")
    doc.append(f"+ Gutter 3:                                                  {GUTTER} px")
    doc.append(f"+ Card 4 Width:                                             {cards[3]['w']} px  (x = 648 to 842)")
    doc.append(f"+ Gutter 4:                                                  {GUTTER} px")
    doc.append(f"+ Card 5 Width:                                             {cards[4]['w']} px  (x = 858 to 1053)")
    doc.append(f"+ Gutter 5:                                                  {GUTTER} px")
    doc.append(f"+ Card 6 Width:                                             {cards[5]['w']} px  (x = 1069 to 1264)")
    doc.append(f"+ Right Margin:                                               {RIGHT_MARGIN} px")
    doc.append("-------------------------------------------------------------------------")
    doc.append(f"TOTAL EXACT HORIZONTAL PIXELS:                             {CANVAS_WIDTH} px (100% Canvas Fit)")
    doc.append("```")
    doc.append("")
    doc.append("> [!TIP]")
    doc.append("> **Why 195 px vs. 194 px?** Dividing the 1,168 px of available card space equally among 6 cards results in 194.67 px. Allocating 195 px to cards 1, 2, 5, 6 and 194 px to cards 3, 4 creates a perfectly symmetrical row with identical 16 px gutters, with a 1-pixel variance that is completely imperceptible to the human eye.")
    doc.append("")
    doc.append("---")
    doc.append("")

    # Section 3: Detailed Specifications
    doc.append("## 3. Detailed Specifications for Each of the 6 Cards")
    doc.append("")

    for c in cards:
        doc.append(f"### Card {c['card_num']}: {c['title']}")
        doc.append(f"- **DAX Measure Name:** `{c['measure_name']}`")
        doc.append(f"- **Source Table in Model:** `{c['source_table']}`")
        doc.append(f"- **Visual Type:** `Card (new)` or standard `Card` visual")
        doc.append(f"- **Title / Category Label:** \"{c['title']}\"")
        doc.append(f"- **Format String:** `{c['number_format']}`")
        doc.append(f"- **Sample Output Value:** **`{c['sample_display']}`**")
        doc.append(f"- **Typography:**")
        doc.append(f"  - Callout Value: **{c['callout_size']}**, Font: Segoe UI or DIN")
        doc.append(f"  - Category / Title Label: **{c['label_size']}**, Font: Segoe UI")
        doc.append(f"- **Position & Geometry:** `X = {c['x']} px`, `Y = {c['y']} px`, `Width = {c['w']} px`, `Height = {c['h']} px`")
        doc.append(f"- **Color Rule:** {c['color_rule']}")
        doc.append(f"- **Slicer Interaction:** {c['interaction_note']}")
        doc.append(f"- **Business Context:** {c['business_meaning']}")
        doc.append("")

    doc.append("---")
    doc.append("")

    # Section 4: Conditional Formatting
    doc.append("## 4. Conditional Formatting Rules (Hex Strings & Thresholds)")
    doc.append("")
    doc.append("To communicate risk state dynamically without cognitive overload, **Card 5 (Alert Precision)** and **Card 6 (Fraud Recall)** use automated conditional formatting driven by DAX measures in `03_measures.dax`:")
    doc.append("")
    doc.append("### A. Card 5: Alert Precision (`[Precision]`)")
    doc.append("- **Measure Driving Color:** `[Color - Precision KPI Card]`")
    doc.append("- **Operational Rationale:** Under the official Combined OR strategy, precision is naturally diluted to **0.755%** in exchange for near-total 99.79% fraud capture. However, when an investigator slices by `alert_source = 'Both'` (Consensus alerts), precision jumps to **98.65%** (Green).")
    doc.append("- **Threshold Logic:**")
    doc.append("")
    doc.append("```dax")
    doc.append("VAR Prec = [Precision]")
    doc.append("RETURN")
    doc.append("    SWITCH(")
    doc.append("        TRUE(),")
    doc.append("        Prec >= 0.90, \"#2ECC71\",  // Emerald Green: High operational efficiency (Consensus tier)")
    doc.append("        Prec >= 0.50, \"#F1C40F\",  // Amber: Balanced ML-only tier")
    doc.append("        \"#E74C3C\"                 // Coral Red: Broad safety net tier (Combined OR)")
    doc.append("    )")
    doc.append("```")
    doc.append("")
    doc.append("### B. Card 6: Fraud Recall (`[Recall]`)")
    doc.append("- **Measure Driving Color:** `[Color - Recall KPI Card]`")
    doc.append("- **Operational Rationale:** In financial crime compliance, **regulatory penalties and fraud losses scale with missed fraud (False Negatives)**. Recall must remain at or above 99% across production operations.")
    doc.append("- **Threshold Logic:**")
    doc.append("")
    doc.append("```dax")
    doc.append("VAR Rec = [Recall]")
    doc.append("RETURN")
    doc.append("    SWITCH(")
    doc.append("        TRUE(),")
    doc.append("        Rec >= 0.99, \"#2ECC71\",   // Emerald Green: Exemplary capture (Combined OR = 99.79%)")
    doc.append("        Rec >= 0.90, \"#F1C40F\",   // Amber: Acceptable ML-only or score>=2 tier")
    doc.append("        \"#E74C3C\"                 // Coral Red: Unacceptable leakage (Baseline = 0.19%)")
    doc.append("    )")
    doc.append("```")
    doc.append("")
    doc.append("### How to Apply Conditional Color in Power BI Desktop:")
    doc.append("1. Select **Card 5** (Alert Precision).")
    doc.append("2. In the **Visualizations** pane, go to **Format visual** > **Callout value**.")
    doc.append("3. Next to the **Color** picker, click the **`fx`** (Conditional formatting) button.")
    doc.append("4. In the dialog:")
    doc.append("   - **Format style:** Select `Field value`.")
    doc.append("   - **What field should we base this on?:** Select `_Measures` > `[Color - Precision KPI Card]`.")
    doc.append("5. Click **OK**.")
    doc.append("6. Repeat the same steps for **Card 6** (Fraud Recall), selecting `_Measures` > `[Color - Recall KPI Card]`.")
    doc.append("")
    doc.append("---")
    doc.append("")

    # Section 5: Visual Interactions
    doc.append("## 5. Visual Interactions & Slicer Decoupling Rules")
    doc.append("")
    doc.append("In financial surveillance dashboards, slicers must filter relevant sub-populations without breaking baseline enterprise denominators.")
    doc.append("")
    doc.append("### Slicers That Must NOT Filter Card 1 (`Total Transactions`):")
    doc.append("1. **`Alert Source` Slicer (`Dim_AlertSource`):** MUST NOT filter Card 1.")
    doc.append("2. **`Risk Band` Slicer (`Dim_RiskBand`):** MUST NOT filter Card 1.")
    doc.append("")
    doc.append("### The Architectural Reason:")
    doc.append("- `[Total Transactions]` is defined as `SUM(Agg_ByType[total_txns])`.")
    doc.append("- The aggregate table `Agg_ByType` has conforming links to `Dim_Type[type]`, so selecting `TRANSFER` or `CASH_OUT` correctly filters enterprise volume for that payment method.")
    doc.append("- However, `Agg_ByType` has **no foreign key** to `Dim_AlertSource` or `Dim_RiskBand` (because 3.59 million legitimate transactions outside Transfer/Cash-out have no alert triage attribution).")
    doc.append("- If an investigator selects `alert_source = 'Both'` to audit the 4,224 consensus alerts, **Total Transactions should remain the benchmark business volume (6,362,620)** rather than displaying an invalid or confusing value.")
    doc.append("")
    doc.append("### Step-by-Step Instructions to Disable Visual Interactions:")
    doc.append("")
    doc.append("```text")
    doc.append("[Step 1] Click on the 'Alert Source' Slicer visual on Page 1.")
    doc.append("[Step 2] In the top Power BI Desktop ribbon, click the 'Format' tab.")
    doc.append("[Step 3] In the 'Interactions' group on the left of the ribbon, click 'Edit interactions'.")
    doc.append("         --> Small filter/block icons will appear in the top-right of every other visual.")
    doc.append("[Step 4] Locate Card 1 ('Total Transactions') at x=16, y=16.")
    doc.append("[Step 5] Click the 'None' icon (circle with diagonal slash) on Card 1.")
    doc.append("         --> This severs the filter link between Alert Source and Card 1.")
    doc.append("[Step 6] Now click on the 'Risk Band' Slicer visual on Page 1.")
    doc.append("[Step 7] Again, click the 'None' icon on Card 1 ('Total Transactions').")
    doc.append("[Step 8] Click 'Edit interactions' on the Format ribbon to exit interaction edit mode.")
    doc.append("```")
    doc.append("")
    doc.append("---")
    doc.append("")

    # Section 6: Step-by-Step
    doc.append("## 6. Step-by-Step Implementation in Power BI Desktop")
    doc.append("")
    doc.append("### Option A: Using the Modern `Card (new)` Multi-Card Visual (Recommended)")
    doc.append("Power BI Desktop's new card visual allows all 6 cards to be hosted inside a single visual container:")
    doc.append("1. On the **Home** ribbon, click the **Card (new)** visual icon.")
    doc.append("2. Set its position and dimensions in **Format visual > General > Properties**:")
    doc.append("   - `Horizontal (X) = 16 px`, `Vertical (Y) = 16 px`")
    doc.append("   - `Width = 1248 px`, `Height = 100 px`")
    doc.append("3. Drag the 6 measures from `_Measures` into the **Data** field well in order:")
    doc.append("   1. `[Total Transactions]`")
    doc.append("   2. `[Total Alerts]`")
    doc.append("   3. `[Total Flagged Value]`")
    doc.append("   4. `[Fraud Rate %]`")
    doc.append("   5. `[Precision]`")
    doc.append("   6. `[Recall]`")
    doc.append("4. Under **Format visual > Layout**:")
    doc.append("   - Orientation: `Horizontal`")
    doc.append("   - Columns: `6`")
    doc.append("   - Card spacing: `16 px`")
    doc.append("5. Under **Cards > Shape**, select `Rounded rectangle` with `6 px` corner radius.")
    doc.append("6. Apply conditional callout value colors to Card 5 and Card 6 via `fx`.")
    doc.append("")
    doc.append("### Option B: Using 6 Individual Visual Containers")
    doc.append("If using traditional single-value cards, create 6 separate cards and enter the exact pixel coordinates from Section 2 into **Format visual > General > Properties > Size and position**:")
    doc.append("- Card 1: `X = 16, Y = 16, W = 195, H = 100`")
    doc.append("- Card 2: `X = 227, Y = 16, W = 195, H = 100`")
    doc.append("- Card 3: `X = 438, Y = 16, W = 194, H = 100`")
    doc.append("- Card 4: `X = 648, Y = 16, W = 194, H = 100`")
    doc.append("- Card 5: `X = 858, Y = 16, W = 195, H = 100`")
    doc.append("- Card 6: `X = 1069, Y = 16, W = 195, H = 100`")
    doc.append("")
    doc.append("---")
    doc.append("*Guide generated programmatically by `src/build_kpi_cards_doc.py`.*")

    output_content = "\n".join(doc)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(output_content, encoding="utf-8")
    elapsed = time.perf_counter() - t0

    print(f"KPI cards guide written to: {output_path.relative_to(config.PROJECT_ROOT)} ({elapsed:.2f}s)")
    print(f"File size: {output_path.stat().st_size:,} bytes | Lines: {len(output_content.splitlines()):,}")
    return output_content


def main() -> None:
    """CLI execution entrypoint."""
    cards = compute_coordinates()
    generate_kpi_cards_markdown(cards)


if __name__ == "__main__":
    main()
