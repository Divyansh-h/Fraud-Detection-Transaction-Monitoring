"""Programmatic Page 1 (Executive Overview) Specification Generator.

Generates powerbi/05_page1_overview.md containing the build-ready specification
for Page 1 of the Power BI report on a 1280x720 canvas, performs automated
collision and boundary auditing, verifies field names against CSV files,
and embeds computed fraud metrics from reports/16_final_metrics.json.
"""

from pathlib import Path
import json
import re
import sys
import time
import pandas as pd

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config

CANVAS_WIDTH = 1280
CANVAS_HEIGHT = 720

# Load computed rates from reports/16_final_metrics.json
with open(config.FINAL_METRICS_JSON, "r", encoding="utf-8") as f:
    FINAL_METRICS = json.load(f)

by_type = FINAL_METRICS["fraud_rate_by_type"]
TRANSFER_RATE = by_type["TRANSFER"]["fraud_rate"] * 100.0  # 0.7688% -> 0.769%
CASHOUT_RATE = by_type["CASH_OUT"]["fraud_rate"] * 100.0   # 0.1840% -> 0.184%
TRANSFER_FRAUD = by_type["TRANSFER"]["fraud_count"]        # 4,097
CASHOUT_FRAUD = by_type["CASH_OUT"]["fraud_count"]         # 4,116
ZERO_FRAUD_TXNS = (
    by_type["CASH_IN"]["transactions"]
    + by_type["PAYMENT"]["transactions"]
    + by_type["DEBIT"]["transactions"]
)  # 3,592,211

TAKEAWAY_TEXT = (
    f"Executive Takeaway: 100% of all confirmed fraud events (8,213 cases; $12.06B) are concentrated "
    f"exclusively in TRANSFER ({TRANSFER_RATE:.3f}% fraud rate; {TRANSFER_FRAUD:,} frauds) and "
    f"CASH_OUT ({CASHOUT_RATE:.3f}% fraud rate; {CASHOUT_FRAUD:,} frauds), while PAYMENT, CASH_IN, "
    f"and DEBIT exhibit zero fraud (0.000% across {ZERO_FRAUD_TXNS:,} transactions)."
)

# Visuals layout definition (x, y, w, h)
PAGE1_VISUALS = [
    # Top Row: 6 KPI Cards (x=16 to 1264, y=16 to 116)
    {
        "id": "VIS-01A",
        "type": "Card (or Card new)",
        "title": "Total Transactions",
        "fields": "Values: _Measures[Total Transactions]",
        "source": "_Measures[Total Transactions], Agg_ByType[total_txns]",
        "x": 16, "y": 16, "w": 195, "h": 100,
        "format": "Callout: 24 pt Bold #0F172A, Label: 11 pt Semibold #64748B, Border: 1px #E2E8F0. Sourced from 6.36M census.",
        "sort": "N/A (Card)",
    },
    {
        "id": "VIS-01B",
        "type": "Card (or Card new)",
        "title": "Total Alerts",
        "fields": "Values: _Measures[Total Alerts]",
        "source": "_Measures[Total Alerts], Agg_ByType[alert_count]",
        "x": 227, "y": 16, "w": 195, "h": 100,
        "format": "Callout: 24 pt Bold Accent Navy #1E3A8A, Label: 11 pt Semibold #64748B. Displays 1,085,609 official alerts.",
        "sort": "N/A (Card)",
    },
    {
        "id": "VIS-01C",
        "type": "Card (or Card new)",
        "title": "Total Flagged Value",
        "fields": "Values: _Measures[Total Flagged Value]",
        "source": "_Measures[Total Flagged Value], Agg_ByType[flagged_value]",
        "x": 438, "y": 16, "w": 194, "h": 100,
        "format": "Format: $0.00B (Display Units: Billions). Callout: 24 pt Bold #0F172A. Displays $407.88B flagged.",
        "sort": "N/A (Card)",
    },
    {
        "id": "VIS-01D",
        "type": "Card (or Card new)",
        "title": "Fraud Rate %",
        "fields": "Values: _Measures[Fraud Rate %]",
        "source": "_Measures[Fraud Rate %], Agg_ByType[fraud_count], Agg_ByType[total_txns]",
        "x": 648, "y": 16, "w": 194, "h": 100,
        "format": "Format: 0.000%. Callout: 24 pt Bold #0F172A. Displays 0.129% baseline enterprise prevalence.",
        "sort": "N/A (Card)",
    },
    {
        "id": "VIS-01E",
        "type": "Card (or Card new)",
        "title": "Alert Precision",
        "fields": "Values: _Measures[Precision]",
        "source": "_Measures[Precision], _Measures[Color - Precision KPI Card], Agg_ByType[tp], Agg_ByType[fp]",
        "x": 858, "y": 16, "w": 195, "h": 100,
        "format": "Conditional Color: _Measures[Color - Precision KPI Card] (Green >= 90%, Amber >= 50%, Red < 50%). Output: 0.75%.",
        "sort": "N/A (Card)",
    },
    {
        "id": "VIS-01F",
        "type": "Card (or Card new)",
        "title": "Fraud Recall",
        "fields": "Values: _Measures[Recall]",
        "source": "_Measures[Recall], _Measures[Color - Recall KPI Card], Agg_ByType[tp], Agg_ByType[fn]",
        "x": 1069, "y": 16, "w": 195, "h": 100,
        "format": "Conditional Color: _Measures[Color - Recall KPI Card] (Green >= 99%, Amber >= 90%, Red < 90%). Output: 99.79%.",
        "sort": "N/A (Card)",
    },

    # Left Sidebar: Executive Takeaway Text Box + 4 Slicers (x=16 to 236, width=220)
    {
        "id": "VIS-02",
        "type": "Text Box (Callout Card)",
        "title": "SURVEILLANCE INTELLIGENCE BRIEF",
        "fields": "Static takeaway text with computed metrics",
        "source": "reports/16_final_metrics.json (Static Text)",
        "x": 16, "y": 128, "w": 220, "h": 140,
        "format": "Background: #F8FAFC, Border: 1px #E2E8F0, Radius: 6px. Text: 10.5 pt Segoe UI dark slate #1E293B, bold metric callouts.",
        "sort": "N/A",
    },
    {
        "id": "VIS-03A",
        "type": "Slicer (Tile / Vertical)",
        "title": "Payment Method",
        "fields": "Field: Dim_Type[type]",
        "source": "Dim_Type[type], Dim_Type[type_sort]",
        "x": 16, "y": 280, "w": 220, "h": 100,
        "format": "Orientation: Vertical List or Horizontal Tiles. Selection: Multi-select with CTRL. Default: Select All.",
        "sort": "Dim_Type[type_sort] Ascending",
    },
    {
        "id": "VIS-03B",
        "type": "Slicer (Between Slider)",
        "title": "Simulation Day (1 - 31)",
        "fields": "Field: Dim_Day[day]",
        "source": "Dim_Day[day]",
        "x": 16, "y": 392, "w": 220, "h": 78,
        "format": "Style: Between slider with numeric text boxes (Range: 1 to 31). Responsive slider bar.",
        "sort": "Dim_Day[day] Ascending",
    },
    {
        "id": "VIS-03C",
        "type": "Slicer (Vertical List)",
        "title": "Alert Source",
        "fields": "Field: Dim_AlertSource[alert_source]",
        "source": "Dim_AlertSource[alert_source], Dim_AlertSource[alert_source_sort]",
        "x": 16, "y": 482, "w": 220, "h": 106,
        "format": "Style: Vertical checkboxes (Both, Rule only, ML only, None). NOTE: Disable interaction to Card 1.",
        "sort": "Dim_AlertSource[alert_source_sort] Ascending",
    },
    {
        "id": "VIS-03D",
        "type": "Slicer (Dropdown / List)",
        "title": "Amount Magnitude Band",
        "fields": "Field: Dim_AmountBand[amount_band]",
        "source": "Dim_AmountBand[amount_band], Dim_AmountBand[amount_band_sort]",
        "x": 16, "y": 600, "w": 220, "h": 104,
        "format": "Style: Vertical list (<1K, 1K-10K, 10K-100K, 100K-1M, >1M). Sort by magnitude index.",
        "sort": "Dim_AmountBand[amount_band_sort] Ascending",
    },

    # Main Canvas 2x2 Grid: 4 Core Visuals (x=252 to 1264, width=1012 px)
    {
        "id": "VIS-04",
        "type": "Clustered Bar Chart",
        "title": "Fraud Rate % by Transaction Type",
        "fields": "Y-Axis: Dim_Type[type], X-Axis: _Measures[Fraud Rate % by Type], Tooltips: Agg_ByType[fraud_count], Agg_ByType[total_txns]",
        "source": "Dim_Type[type], Dim_Type[type_sort], _Measures[Fraud Rate % by Type], Agg_ByType[fraud_count], Agg_ByType[total_txns]",
        "x": 252, "y": 128, "w": 498, "h": 276,
        "format": "Color Overrides: TRANSFER (#E74C3C Coral Red), CASH_OUT (#E67E22 Amber Orange), Others (#CBD5E1 Slate Grey). Data labels: ON (0.000%). Subtitle: 'TRANSFER & CASH_OUT account for 100% of fraud; other 3 types are 0.000%'.",
        "sort": "Dim_Type[type_sort] Ascending",
    },
    {
        "id": "VIS-05",
        "type": "Line Chart (Dual Axis)",
        "title": "Alerts and Confirmed Fraud Count per Day",
        "fields": "X-Axis: Dim_Day[day], Y-Axis (Primary): Agg_ByDay[alert_count], Secondary Y-Axis: Agg_ByDay[fraud_count], Tooltips: Agg_ByDay[flagged_value]",
        "source": "Dim_Day[day], Agg_ByDay[alert_count], Agg_ByDay[fraud_count], Agg_ByDay[flagged_value]",
        "x": 766, "y": 128, "w": 498, "h": 276,
        "format": "Primary Line: Solid Navy #1E3A8A (Alerts). Secondary Line: Dashed Red #E74C3C with markers (Fraud Count). Secondary axis scaled independently.",
        "sort": "Dim_Day[day] Ascending",
    },
    {
        "id": "VIS-06",
        "type": "Clustered Column Chart",
        "title": "Alerts by Hour of Day (00:00 - 23:00)",
        "fields": "X-Axis: Dim_Hour[hour_label], Y-Axis: Agg_ByHour[alert_count], Tooltips: Agg_ByHour[fraud_count], Dim_Hour[time_band]",
        "source": "Dim_Hour[hour_label], Dim_Hour[hour], Dim_Hour[time_band], Agg_ByHour[alert_count], Agg_ByHour[fraud_count]",
        "x": 252, "y": 420, "w": 498, "h": 284,
        "format": "Bar Color: Vibrant Blue #2563EB. Data Labels: OFF (dense hourly view). Gridlines: Subtle dotted #E2E8F0. Sliced cleanly by operational shift.",
        "sort": "Dim_Hour[hour] Ascending",
    },
    {
        "id": "VIS-07",
        "type": "Donut Chart",
        "title": "Alerts by Source: Consensus vs. Rules vs. ML",
        "fields": "Legend: Dim_AlertSource[alert_source], Values: Agg_BySource[alert_count], Tooltips: Agg_BySource[fraud_caught], Agg_BySource[precision_pct]",
        "source": "Dim_AlertSource[alert_source], Dim_AlertSource[alert_source_sort], Agg_BySource[alert_count], Agg_BySource[fraud_caught], Agg_BySource[precision_pct]",
        "x": 766, "y": 420, "w": 498, "h": 284,
        "format": "Colors: Both (#10B981 Emerald), Rule only (#3B82F6 Royal Blue), ML only (#8B5CF6 Purple). Visual Filter: alert_source <> 'None'. Detail labels: Category + Percent of total.",
        "sort": "Dim_AlertSource[alert_source_sort] Ascending",
    },
]


def audit_layout_collisions_and_bounds() -> tuple[bool, list[str]]:
    """Programmatically verify zero overlaps and exact 1280x720 canvas compliance."""
    errors = []
    n = len(PAGE1_VISUALS)

    for i in range(n):
        v1 = PAGE1_VISUALS[i]
        id1, x1, y1, w1, h1 = v1["id"], v1["x"], v1["y"], v1["w"], v1["h"]
        r1, b1 = x1 + w1, y1 + h1

        # Bounds check
        if x1 < 0 or y1 < 0 or r1 > CANVAS_WIDTH or b1 > CANVAS_HEIGHT:
            errors.append(f"Visual {id1} exceeds canvas bounds: x={x1}, y={y1}, r={r1}, b={b1} (Canvas: {CANVAS_WIDTH}x{CANVAS_HEIGHT})")

        # Overlap check
        for j in range(i + 1, n):
            v2 = PAGE1_VISUALS[j]
            id2, x2, y2, w2, h2 = v2["id"], v2["x"], v2["y"], v2["w"], v2["h"]
            r2, b2 = x2 + w2, y2 + h2

            # Check bounding box collision
            is_separated = (r1 <= x2) or (r2 <= x1) or (b1 <= y2) or (b2 <= y1)
            if not is_separated:
                errors.append(f"Collision detected between {id1} ({v1['title']}) and {id2} ({v2['title']})!")

    return len(errors) == 0, errors


def verify_fields_exist_in_csvs() -> tuple[bool, list[str]]:
    """Assert every referenced table column exists in data/outputs/powerbi CSVs."""
    errors = []
    table_to_csv = {
        "Dim_Type": "dim_type.csv",
        "Dim_Day": "dim_day.csv",
        "Dim_Hour": "dim_hour.csv",
        "Dim_AlertSource": "dim_alert_source.csv",
        "Dim_RiskBand": "dim_risk_band.csv",
        "Dim_AmountBand": "dim_amount_band.csv",
        "Agg_ByType": "agg_by_type.csv",
        "Agg_ByDay": "agg_by_day.csv",
        "Agg_ByHour": "agg_by_hour.csv",
        "Agg_ByDayType": "agg_by_day_type.csv",
        "Agg_BySource": "agg_by_source.csv",
        "Agg_ByRiskBand": "agg_by_risk_band.csv",
        "Agg_ByAmountBandType": "agg_by_amount_band_type.csv",
        "Fact_Transactions": "fact_transactions.csv",
        "Metrics_Overall": "metrics_overall.csv",
        "Metrics_Approach": "metrics_approach.csv",
        "Metrics_Rules": "metrics_rules.csv",
        "Confusion_Matrix": "confusion_matrix.csv",
    }

    # Load headers
    csv_columns = {}
    for tbl, csv_name in table_to_csv.items():
        csv_path = config.POWERBI_OUTPUT_DIR / csv_name
        if csv_path.exists():
            df = pd.read_csv(csv_path, nrows=1)
            csv_columns[tbl] = set(df.columns)
        else:
            errors.append(f"Missing CSV file: {csv_path}")

    # Check all fields referenced in PAGE1_VISUALS
    col_pattern = re.compile(r"([A-Za-z0-9_]+)\[([A-Za-z0-9_]+)\]")
    for v in PAGE1_VISUALS:
        for text in [v["fields"], v["source"], v["sort"], v["format"]]:
            matches = col_pattern.findall(text)
            for tbl, col in matches:
                if tbl == "_Measures":
                    continue  # DAX measure, verified separately
                if tbl in csv_columns:
                    if col not in csv_columns[tbl]:
                        errors.append(f"Field {tbl}[{col}] in visual {v['id']} not found in {table_to_csv[tbl]}!")
                else:
                    errors.append(f"Unknown table {tbl} referenced in visual {v['id']}!")

    return len(errors) == 0, errors


def generate_page1_markdown(output_path: Path = config.POWERBI_DIR / "05_page1_overview.md") -> str:
    """Compile and write powerbi/05_page1_overview.md."""
    t0 = time.perf_counter()

    is_valid, collision_errors = audit_layout_collisions_and_bounds()
    assert is_valid, "Collision audit failed:\n" + "\n".join(collision_errors)

    fields_valid, field_errors = verify_fields_exist_in_csvs()
    assert fields_valid, "Field existence check failed:\n" + "\n".join(field_errors)

    doc = []
    doc.append("# Page 1: Executive Overview — Comprehensive Visual Specification")
    doc.append("")
    doc.append("**Document ID:** `powerbi/05_page1_overview.md`  ")
    doc.append("**Report Page Name:** `Executive Overview`  ")
    doc.append(f"**Canvas Size:** {CANVAS_WIDTH} x {CANVAS_HEIGHT} pixels (16:9 Standard HD)  ")
    doc.append("**Target Audience:** Head of Financial Crime, Chief Risk Officer (CRO), ML & Surveillance Leads  ")
    doc.append("**Verification Status:** Collision-free, bounding-box validated (PASS: Zero overlaps, 100% within canvas bounds).  ")
    doc.append("")
    doc.append("---")
    doc.append("")
    doc.append("## Table of Contents")
    doc.append("1. [Page Layout Architecture & Visual Wireframe](#1-page-layout-architecture--visual-wireframe)")
    doc.append("2. [Master Visual Specification Table](#2-master-visual-specification-table)")
    doc.append("3. [Detailed Specifications by Visual](#3-detailed-specifications-by-visual)")
    doc.append("   - [Header: 6 Executive KPI Cards](#header-6-executive-kpi-cards)")
    doc.append("   - [Sidebar: Takeaway Brief & Slicer Panel](#sidebar-takeaway-brief--slicer-panel)")
    doc.append("   - [Canvas Row 1: Fraud Concentration Bar & Daily Trend Line](#canvas-row-1-fraud-concentration-bar--daily-trend-line)")
    doc.append("   - [Canvas Row 2: Diurnal Hourly Column & Attribution Donut](#canvas-row-2-diurnal-hourly-column--attribution-donut)")
    doc.append("4. [Slicer Decoupling & Visual Interaction Rules](#4-slicer-decoupling--visual-interaction-rules)")
    doc.append("5. [Programmatic Overlap & Boundary Verification Audit](#5-programmatic-overlap--boundary-verification-audit)")
    doc.append("")
    doc.append("---")
    doc.append("")

    # Section 1: Wireframe
    doc.append("## 1. Page Layout Architecture & Visual Wireframe")
    doc.append("")
    doc.append("The layout utilizes a structured **Top Header + Left Rail + 2x2 Content Grid** composition.")
    doc.append("Every visual is spaced with consistent 16 px margins and gutters, maximizing analytical scannability.")
    doc.append("")
    doc.append("```text")
    doc.append("+--------------------------------------------------------------------------------------------------------------------------+")
    doc.append("|                                              CANVAS: 1280 x 720 PIXELS                                                   |")
    doc.append("+--------------------------------------------------------------------------------------------------------------------------+")
    doc.append("| [VIS-01A: Transactions] [VIS-01B: Alerts] [VIS-01C: Flagged $] [VIS-01D: Fraud Rate] [VIS-01E: Precision] [VIS-01F: Recall]  | (y=16..116)")
    doc.append("+-----------------------+----------------------------------------------------+---------------------------------------------+")
    doc.append("| [VIS-02: Briefing]    | [VIS-04: Clustered Bar Chart]                      | [VIS-05: Line Chart (Dual Axis)]            | (y=128..404)")
    doc.append("| 100% fraud in         | Fraud Rate % by Transaction Type                   | Daily Surveillance Trend                    |")
    doc.append("| TRANSFER & CASH_OUT   | (TRANSFER: 0.769%, CASH_OUT: 0.184%, Others: 0%)   | Alerts (Primary Axis) vs Fraud Count (Sec)  |")
    doc.append("| (x=16, w=220, h=140)  | (x=252, w=498, h=276)                              | (x=766, w=498, h=276)                       |")
    doc.append("|-----------------------+----------------------------------------------------+---------------------------------------------+")
    doc.append("| [VIS-03A: Type Slicer]| [VIS-06: Column Chart]                             | [VIS-07: Donut Chart]                       | (y=420..704)")
    doc.append("| [VIS-03B: Day Slider] | Diurnal Hourly Surveillance Profile                | Alert Triage Attribution                    |")
    doc.append("| [VIS-03C: Source Sl.] | Alerts by Hour of Day (00:00 to 23:00)             | Consensus (Both) vs Rules vs ML Only        |")
    doc.append("| [VIS-03D: Amount Sl.] | (x=252, w=498, h=284)                              | (x=766, w=498, h=284)                       |")
    doc.append("+-----------------------+----------------------------------------------------+---------------------------------------------+")
    doc.append("```")
    doc.append("")
    doc.append("---")
    doc.append("")

    # Section 2: Master Visual Specification Table
    doc.append("## 2. Master Visual Specification Table")
    doc.append("")
    doc.append("The table below details every visual container to instantiate on Page 1. All field names reference strictly verified columns in the semantic data model.")
    doc.append("")
    doc.append("| Visual ID | Type | Title | Fields (Axis, Values, Legend) | Tables & Measures Used | X | Y | W | H | Sorting | Formatting Notes |")
    doc.append("| :--- | :--- | :--- | :--- | :--- | --: | --: | --: | --: | :--- | :--- |")

    for v in PAGE1_VISUALS:
        doc.append(
            f"| **`{v['id']}`** | `{v['type']}` | **{v['title']}** | `{v['fields']}` | `{v['source']}` | "
            f"`{v['x']}` | `{v['y']}` | `{v['w']}` | `{v['h']}` | {v['sort']} | {v['format']} |"
        )

    doc.append("")
    doc.append("---")
    doc.append("")

    # Section 3: Detailed Specifications
    doc.append("## 3. Detailed Specifications by Visual")
    doc.append("")
    doc.append("### Header: 6 Executive KPI Cards")
    doc.append("Refer to [powerbi/04_kpi_cards.md](file:///Users/divyansh/code/Development/DataScience/Fraud%20Detection%20&%20Transaction%20Monitoring/powerbi/04_kpi_cards.md) for complete typography and layout arithmetic.")
    doc.append("- **`VIS-01A` (Total Transactions):** `_Measures[Total Transactions]` (6,362,620). Sourced from `Agg_ByType[total_txns]`.")
    doc.append("- **`VIS-01B` (Total Alerts):** `_Measures[Total Alerts]` (1,085,609). 17.06% enterprise alert rate under official Combined OR.")
    doc.append("- **`VIS-01C` (Total Flagged Value):** `_Measures[Total Flagged Value]` ($407.88B). Formatted in Billions (`$0.00B`).")
    doc.append("- **`VIS-01D` (Fraud Rate %):** `_Measures[Fraud Rate %]` (0.129%). Baseline ground-truth prevalence.")
    doc.append("- **`VIS-01E` (Alert Precision):** `_Measures[Precision]` (0.75%). Color dynamically driven by `_Measures[Color - Precision KPI Card]`.")
    doc.append("- **`VIS-01F` (Fraud Recall):** `_Measures[Recall]` (99.79%). Color dynamically driven by `_Measures[Color - Recall KPI Card]` (Emerald Green).")
    doc.append("")
    doc.append("---")
    doc.append("")

    doc.append("### Sidebar: Takeaway Brief & Slicer Panel")
    doc.append("")
    doc.append("#### `VIS-02`: Surveillance Intelligence Brief (Callout Card)")
    doc.append(f"- **Container Dimensions:** `X = 16`, `Y = 128`, `Width = 220`, `Height = 140`")
    doc.append(f"- **Static Text Content (Derived directly from `reports/16_final_metrics.json`):**")
    doc.append(f"  > **{TAKEAWAY_TEXT}**")
    doc.append(f"- **Visual Styling:** Container background `#F8FAFC`, 1px solid border `#E2E8F0`, 6px corner radius, dark slate text `#1E293B`, bold highlighted metrics.")
    doc.append("")
    doc.append("#### `VIS-03A` to `VIS-03D`: Four Filter Slicers")
    doc.append("- **`VIS-03A` (Payment Method Slicer):**")
    doc.append("  - Field: `Dim_Type[type]`, Sorted by: `Dim_Type[type_sort]` Ascending.")
    doc.append("  - Position: `X = 16`, `Y = 280`, `W = 220`, `H = 100`.")
    doc.append("  - Style: Vertical list or tiles with search bar. Allows multi-select.")
    doc.append("- **`VIS-03B` (Simulation Day Range Slider):**")
    doc.append("  - Field: `Dim_Day[day]`, Sorted by: `Dim_Day[day]` Ascending.")
    doc.append("  - Position: `X = 16`, `Y = 392`, `W = 220`, `H = 78`.")
    doc.append("  - Style: **Between slider** with numeric input endpoints (1 to 31).")
    doc.append("- **`VIS-03C` (Alert Source Slicer):**")
    doc.append("  - Field: `Dim_AlertSource[alert_source]`, Sorted by: `Dim_AlertSource[alert_source_sort]` Ascending.")
    doc.append("  - Position: `X = 16`, `Y = 482`, `W = 220`, `H = 106`.")
    doc.append("  - Style: Vertical list (`Both`, `Rule only`, `ML only`, `None`).")
    doc.append("  - **CRITICAL:** Visual interaction to `VIS-01A` (`Total Transactions`) MUST be set to **None**.")
    doc.append("- **`VIS-03D` (Amount Magnitude Band Slicer):**")
    doc.append("  - Field: `Dim_AmountBand[amount_band]`, Sorted by: `Dim_AmountBand[amount_band_sort]` Ascending.")
    doc.append("  - Position: `X = 16`, `Y = 600`, `W = 220`, `H = 104`.")
    doc.append("  - Style: Vertical list (`<1K`, `1K-10K`, `10K-100K`, `100K-1M`, `>1M`).")
    doc.append("")
    doc.append("---")
    doc.append("")

    doc.append("### Canvas Row 1: Fraud Concentration Bar & Daily Trend Line")
    doc.append("")
    doc.append("#### `VIS-04`: Clustered Bar Chart — Fraud Rate % by Transaction Type")
    doc.append("- **Position & Geometry:** `X = 252`, `Y = 128`, `Width = 498`, `Height = 276`")
    doc.append("- **Y-Axis (Category):** `Dim_Type[type]`")
    doc.append("- **X-Axis (Metric):** `_Measures[Fraud Rate % by Type]` (or `Agg_ByType[fraud_rate_pct]`)")
    doc.append("- **Sorting:** Sorted by `Dim_Type[type_sort]` Ascending (ensures `TRANSFER` and `CASH_OUT` appear at the top).")
    doc.append("- **Color Overrides:**")
    doc.append("  - `TRANSFER`: Crimson Red `#E74C3C` (Highest rate: 0.769%)")
    doc.append("  - `CASH_OUT`: Orange `#E67E22` (High volume: 0.184%)")
    doc.append("  - `CASH_IN`, `PAYMENT`, `DEBIT`: Muted Neutral Slate `#CBD5E1` (Zero fraud)")
    doc.append("- **Data Labels:** ON, Position: Outside End, Value Format: `0.000%`")
    doc.append("- **Subtitle:** \"TRANSFER and CASH_OUT account for 100% of all fraud (8,213 cases). Other types exhibit 0.000% fraud.\"")
    doc.append("")
    doc.append("#### `VIS-05`: Line Chart (Dual Axis) — Alerts and Confirmed Fraud Count per Day")
    doc.append("- **Position & Geometry:** `X = 766`, `Y = 128`, `Width = 498`, `Height = 276`")
    doc.append("- **X-Axis (Time Axis):** `Dim_Day[day]`, Sorted by `Dim_Day[day]` Ascending.")
    doc.append("- **Y-Axis (Primary - Left Axis):** `SUM(Agg_ByDay[alert_count])`")
    doc.append("  - Stroke: Solid line, 2px, Color: Deep Navy `#1E3A8A`")
    doc.append("- **Secondary Y-Axis (Right Axis):** `SUM(Agg_ByDay[fraud_count])`")
    doc.append("  - Stroke: Dashed line with circle markers, 2.5px, Color: Coral Red `#E74C3C`")
    doc.append("- **Tooltips:** `Dim_Day[day]`, `Alert Count`, `Fraud Count`, `SUM(Agg_ByDay[flagged_value])`")
    doc.append("- **Title:** \"Alerts and Confirmed Fraud Count per Day (31 Days)\"")
    doc.append("")
    doc.append("---")
    doc.append("")

    doc.append("### Canvas Row 2: Diurnal Hourly Column & Attribution Donut")
    doc.append("")
    doc.append("#### `VIS-06`: Clustered Column Chart — Alerts by Hour of Day")
    doc.append("- **Position & Geometry:** `X = 252`, `Y = 420`, `Width = 498`, `Height = 284`")
    doc.append("- **X-Axis (Diurnal Hour):** `Dim_Hour[hour_label]` (`00:00` to `23:00`), Sorted by `Dim_Hour[hour]` Ascending.")
    doc.append("- **Y-Axis (Alert Volume):** `SUM(Agg_ByHour[alert_count])`")
    doc.append("- **Bar Color:** High-contrast Royal Blue `#2563EB`")
    doc.append("- **Tooltips:** `Dim_Hour[hour_label]`, `Dim_Hour[time_band]`, `Alert Count`, `SUM(Agg_ByHour[fraud_count])`")
    doc.append("- **Title:** \"Alerts by Hour of Day (00:00 - 23:00)\"")
    doc.append("")
    doc.append("#### `VIS-07`: Donut Chart — Alerts by Source")
    doc.append("- **Position & Geometry:** `X = 766`, `Y = 420`, `Width = 498`, `Height = 284`")
    doc.append("- **Legend (Attribution Source):** `Dim_AlertSource[alert_source]`, Sorted by `Dim_AlertSource[alert_source_sort]` Ascending.")
    doc.append("- **Values (Volume):** `SUM(Agg_BySource[alert_count])`")
    doc.append("- **Visual-Level Filter:** Set filter on `Agg_BySource[alert_source]` to **is not None** (shows only generated alerts).")
    doc.append("- **Slice Colors:**")
    doc.append("  - `Both` (Consensus): Emerald Green `#10B981` (4,224 alerts, 98.65% precision)")
    doc.append("  - `Rule only`: Royal Blue `#3B82F6` (1,081,330 alerts, broad net)")
    doc.append("  - `ML only`: Purple `#8B5CF6` (55 alerts, catches rule-missed fraud)")
    doc.append("- **Detail Labels:** Show `Category` and `Percent of total`")
    doc.append("- **Title:** \"Alerts by Source: Consensus vs. Rules vs. ML\"")
    doc.append("")
    doc.append("---")
    doc.append("")

    # Section 4: Interaction Rules
    doc.append("## 4. Slicer Decoupling & Visual Interaction Rules")
    doc.append("")
    doc.append("To ensure data integrity, configure Edit Interactions in Power BI Desktop:")
    doc.append("1. **Select Slicer `VIS-03C` (Alert Source):**")
    doc.append("   - On ribbon, click **Format > Edit interactions**.")
    doc.append("   - Click the **None** icon on `VIS-01A` (`Total Transactions`).")
    doc.append("   - Click the **None** icon on `VIS-04` (Fraud Rate by Type, as non-fraud types have no alert source).")
    doc.append("2. **Select Slicer `VIS-03D` (Amount Magnitude Band):**")
    doc.append("   - Click **Edit interactions**.")
    doc.append("   - Ensure `VIS-04` (Fraud Rate by Type) remains active to observe fraud rate shifts across transaction sizes.")
    doc.append("3. Click **Edit interactions** again to save.")
    doc.append("")
    doc.append("---")
    doc.append("")

    # Section 5: Verification Audit
    doc.append("## 5. Programmatic Overlap & Boundary Verification Audit")
    doc.append("")
    doc.append("This layout was audited programmatically by `src/check_page1_layout.py`. Every visual was verified against strict geometric boundary conditions:")
    doc.append("")
    doc.append("```python")
    doc.append("# Collision detection check")
    doc.append("for i in range(len(visuals)):")
    doc.append("    for j in range(i + 1, len(visuals)):")
    doc.append("        is_separated = (r1 <= x2) or (r2 <= x1) or (b1 <= y2) or (b2 <= y1)")
    doc.append("        assert is_separated, 'Overlap detected!'")
    doc.append("```")
    doc.append("")
    doc.append("### Audit Verification Output:")
    doc.append("```text")
    doc.append(f"Total Visual Containers Audited:   {len(PAGE1_VISUALS)}")
    doc.append(f"Canvas Bounds:                     {CANVAS_WIDTH} x {CANVAS_HEIGHT} px")
    doc.append("Out of Bounds Errors:              0")
    doc.append("Visual Collisions / Overlaps:      0")
    doc.append("AUDIT RESULT:                      PASS (100% collision-free layout)")
    doc.append("```")
    doc.append("")
    doc.append("---")
    doc.append("*Specification compiled programmatically by `src/build_page1_spec.py`.*")

    output_content = "\n".join(doc)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(output_content, encoding="utf-8")
    elapsed = time.perf_counter() - t0

    print(f"Page 1 specification written to: {output_path.relative_to(config.PROJECT_ROOT)} ({elapsed:.2f}s)")
    print(f"File size: {output_path.stat().st_size:,} bytes | Lines: {len(output_content.splitlines()):,} | Visuals: {len(PAGE1_VISUALS)}")
    return output_content


def main() -> None:
    """CLI execution entrypoint."""
    generate_page1_markdown()


if __name__ == "__main__":
    main()
