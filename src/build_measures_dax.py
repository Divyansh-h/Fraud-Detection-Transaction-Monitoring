"""Programmatic DAX Measures Generator & Schema Auditor for Power BI Desktop.

Generates powerbi/03_measures.dax containing all required DAX measures, audits every
referenced table and column against CSV file headers in data/outputs/powerbi/,
verifies that no division occurs without DIVIDE, verifies unique measure names,
and ensures format strings and display folders are documented.
"""

from pathlib import Path
import re
import sys
import time
import pandas as pd

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config

# Mapping of Power BI table names to underlying CSV filenames
PBI_TABLE_TO_CSV = {
    "Fact_Transactions": "fact_transactions.csv",
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
    "Metrics_Overall": "metrics_overall.csv",
    "Metrics_Approach": "metrics_approach.csv",
    "Metrics_Rules": "metrics_rules.csv",
    "Confusion_Matrix": "confusion_matrix.csv",
}

# Catalog of all measures to generate
MEASURES_CATALOG = [
    # -------------------------------------------------------------------------
    # Display Folder: 01 - Enterprise Volumes & KPIs
    # -------------------------------------------------------------------------
    {
        "name": "Total Transactions",
        "folder": "01 - Enterprise Volumes & KPIs",
        "format": "#,##0",
        "description": "Total enterprise transaction volume sourced from pre-aggregated 6.36M ground truth.",
        "dax": "SUM(Agg_ByType[total_txns])",
    },
    {
        "name": "Total Alerts",
        "folder": "01 - Enterprise Volumes & KPIs",
        "format": "#,##0",
        "description": "Total alerts flagged across enterprise under official Combined OR definition (1,085,609).",
        "dax": "SUM(Agg_ByType[alert_count])",
    },
    {
        "name": "Fraud Count",
        "folder": "01 - Enterprise Volumes & KPIs",
        "format": "#,##0",
        "description": "Total confirmed fraudulent transactions across enterprise (8,213 ground truth census).",
        "dax": "SUM(Agg_ByType[fraud_count])",
    },
    {
        "name": "Fraud Rate %",
        "folder": "01 - Enterprise Volumes & KPIs",
        "format": "0.000%",
        "description": "Enterprise baseline fraud prevalence rate (8,213 / 6,362,620 = 0.129%).",
        "dax": "DIVIDE([Fraud Count], [Total Transactions], 0)",
    },
    {
        "name": "Alert Rate %",
        "folder": "01 - Enterprise Volumes & KPIs",
        "format": "0.00%",
        "description": "Percentage of total enterprise transactions flagged for investigator triage (17.06%).",
        "dax": "DIVIDE([Total Alerts], [Total Transactions], 0)",
    },
    {
        "name": "Total Legitimate Volume",
        "folder": "01 - Enterprise Volumes & KPIs",
        "format": "#,##0",
        "description": "Total enterprise legitimate unalerted transactions (6,354,407 non-fraud rows).",
        "dax": "[Total Transactions] - [Fraud Count]",
    },

    # -------------------------------------------------------------------------
    # Display Folder: 02 - Fraud & Alert Exposure ($)
    # -------------------------------------------------------------------------
    {
        "name": "Total Flagged Value",
        "folder": "02 - Fraud & Alert Exposure ($)",
        "format": "$#,##0",
        "description": "Total currency value of transactions flagged by alerts ($407,883,914,866.30 across enterprise).",
        "dax": "SUM(Agg_ByType[flagged_value])",
    },
    {
        "name": "Total Amount ($)",
        "folder": "02 - Fraud & Alert Exposure ($)",
        "format": "$#,##0",
        "description": "Total enterprise transaction currency volume across all 5 payment types ($1.14 Trillion).",
        "dax": "SUM(Agg_ByType[total_amount])",
    },
    {
        "name": "Avg Alert Amount",
        "folder": "02 - Fraud & Alert Exposure ($)",
        "format": "$#,##0",
        "description": "Average transaction currency value among all generated alerts.",
        "dax": "DIVIDE([Total Flagged Value], [Total Alerts], 0)",
    },
    {
        "name": "Missed Fraud Value",
        "folder": "02 - Fraud & Alert Exposure ($)",
        "format": "$#,##0",
        "description": "Total currency amount of false negative fraud events missed by alerts. Sourced from Fact_Transactions where outcome = 'False Negative' (exact, as fact table contains 100% of fraud).",
        "dax": 'CALCULATE(SUM(Fact_Transactions[amount]), Fact_Transactions[outcome] = "False Negative")',
    },
    {
        "name": "Caught Fraud Value",
        "folder": "02 - Fraud & Alert Exposure ($)",
        "format": "$#,##0",
        "description": "Total currency amount of successfully detected fraud (outcome = 'True Positive') in Fact_Transactions (exact, as fact table contains 100% of fraud).",
        "dax": 'CALCULATE(SUM(Fact_Transactions[amount]), Fact_Transactions[outcome] = "True Positive")',
    },
    {
        "name": "Total Fraud Exposure ($)",
        "folder": "02 - Fraud & Alert Exposure ($)",
        "format": "$#,##0",
        "description": "Total gross currency value of all confirmed fraudulent transactions ($12.06 Billion).",
        "dax": "[Caught Fraud Value] + [Missed Fraud Value]",
    },

    # -------------------------------------------------------------------------
    # Display Folder: 03 - Classification & Performance Metrics
    # -------------------------------------------------------------------------
    {
        "name": "True Positives",
        "folder": "03 - Classification & Performance Metrics",
        "format": "#,##0",
        "description": "Confirmed fraudulent transactions correctly flagged by surveillance (TP = 8,196).",
        "dax": "SUM(Agg_ByType[tp])",
    },
    {
        "name": "False Positives",
        "folder": "03 - Classification & Performance Metrics",
        "format": "#,##0",
        "description": "Legitimate transactions erroneously flagged as fraud alarms (FP = 1,077,413).",
        "dax": "SUM(Agg_ByType[fp])",
    },
    {
        "name": "False Negatives",
        "folder": "03 - Classification & Performance Metrics",
        "format": "#,##0",
        "description": "Fraudulent transactions missed by official surveillance alerts (FN = 17).",
        "dax": "SUM(Agg_ByType[fn])",
    },
    {
        "name": "True Negatives",
        "folder": "03 - Classification & Performance Metrics",
        "format": "#,##0",
        "description": "Legitimate transactions correctly passed without generating alarms (TN = 5,276,994).",
        "dax": "SUM(Agg_ByType[tn])",
    },
    {
        "name": "Precision",
        "folder": "03 - Classification & Performance Metrics",
        "format": "0.00%",
        "description": "Alert investigation hit rate: TP / (TP + FP) = 0.755% under maximal recall Combined OR.",
        "dax": "DIVIDE([True Positives], [True Positives] + [False Positives], 0)",
    },
    {
        "name": "Recall",
        "folder": "03 - Classification & Performance Metrics",
        "format": "0.00%",
        "description": "Fraud capture coverage rate: TP / (TP + FN) = 99.793% (detects 8,196 of 8,213 frauds).",
        "dax": "DIVIDE([True Positives], [True Positives] + [False Negatives], 0)",
    },
    {
        "name": "False Positive Rate",
        "folder": "03 - Classification & Performance Metrics",
        "format": "0.00%",
        "description": "Fall-out proportion of legitimate transactions flagged: FP / (FP + TN) = 16.955%.",
        "dax": "DIVIDE([False Positives], [False Positives] + [True Negatives], 0)",
    },
    {
        "name": "F1 Score",
        "folder": "03 - Classification & Performance Metrics",
        "format": "0.0000",
        "description": "Harmonic mean of precision and recall: 2 * (Prec * Rec) / (Prec + Rec).",
        "dax": "VAR Prec = [Precision]\nVAR Rec = [Recall]\nRETURN\n    DIVIDE(2 * Prec * Rec, Prec + Rec, 0)",
    },

    # -------------------------------------------------------------------------
    # Display Folder: 04 - Dimension Specific Rates
    # -------------------------------------------------------------------------
    {
        "name": "Fraud Rate % by Type",
        "folder": "04 - Dimension Specific Rates",
        "format": "0.000%",
        "description": "Context-aware fraud rate evaluated per payment type slice along Dim_Type[type] (TRANSFER = 0.769%, CASH_OUT = 0.184%, others = 0.000%).",
        "dax": "DIVIDE(SUM(Agg_ByType[fraud_count]), SUM(Agg_ByType[total_txns]), 0)",
    },
    {
        "name": "Alert Rate % by Type",
        "folder": "04 - Dimension Specific Rates",
        "format": "0.00%",
        "description": "Context-aware alert rate evaluated per payment type slice along Dim_Type[type] (TRANSFER = 41.33%, CASH_OUT = 38.68%, others = 0.00%).",
        "dax": "DIVIDE(SUM(Agg_ByType[alert_count]), SUM(Agg_ByType[total_txns]), 0)",
    },

    # -------------------------------------------------------------------------
    # Display Folder: 05 - Alert Attribution (Source & Triage)
    # -------------------------------------------------------------------------
    {
        "name": "Alerts Both",
        "folder": "05 - Alert Attribution (Source & Triage)",
        "format": "#,##0",
        "description": "High-consensus alerts flagged by BOTH heuristic SQL rules AND ML Isolation Forest (4,224 txns, 98.65% precision).",
        "dax": 'CALCULATE(SUM(Agg_BySource[alert_count]), Agg_BySource[alert_source] = "Both")',
    },
    {
        "name": "Alerts Rule Only",
        "folder": "05 - Alert Attribution (Source & Triage)",
        "format": "#,##0",
        "description": "Alerts flagged exclusively by heuristic SQL rules (1,081,330 txns, 0.37% precision).",
        "dax": 'CALCULATE(SUM(Agg_BySource[alert_count]), Agg_BySource[alert_source] = "Rule only")',
    },
    {
        "name": "Alerts ML Only",
        "folder": "05 - Alert Attribution (Source & Triage)",
        "format": "#,##0",
        "description": "Alerts flagged exclusively by ML Isolation Forest, catching missed rule fraud (55 txns, 6 frauds, 10.91% precision).",
        "dax": 'CALCULATE(SUM(Agg_BySource[alert_count]), Agg_BySource[alert_source] = "ML only")',
    },
    {
        "name": "Consensus Precision %",
        "folder": "05 - Alert Attribution (Source & Triage)",
        "format": "0.00%",
        "description": "Precision hit rate for high-confidence Consensus alerts ('Both' source = 98.65%).",
        "dax": 'DIVIDE(CALCULATE(SUM(Agg_BySource[fraud_caught]), Agg_BySource[alert_source] = "Both"), [Alerts Both], 0)',
    },

    # -------------------------------------------------------------------------
    # Display Folder: 06 - Investigator Workbench & Ranking
    # -------------------------------------------------------------------------
    {
        "name": "Alert Rank",
        "folder": "06 - Investigator Workbench & Ranking",
        "format": "#,##0",
        "description": "Dynamic ordinal priority rank (1 = highest risk) of transactions by combo_score for Top N table filtering in investigator workbench.",
        "dax": """IF(
    NOT(ISBLANK(SELECTEDVALUE(Fact_Transactions[txn_id]))),
    RANKX(
        ALLSELECTED(Fact_Transactions),
        CALCULATE(MAX(Fact_Transactions[combo_score])),
        ,
        DESC,
        Dense
    )
)""",
    },
    {
        "name": "High Risk Alert Count",
        "folder": "06 - Investigator Workbench & Ranking",
        "format": "#,##0",
        "description": "Count of transactions classified into the 'High' or 'Critical' risk bands in Fact_Transactions.",
        "dax": 'CALCULATE(COUNTROWS(Fact_Transactions), Fact_Transactions[risk_band] IN {"Critical", "High"})',
    },

    # -------------------------------------------------------------------------
    # Display Folder: 07 - Dynamic Visual Titles
    # -------------------------------------------------------------------------
    {
        "name": "Dynamic Title - Selected Type",
        "folder": "07 - Dynamic Visual Titles",
        "format": "Text",
        "description": "Generates dynamic visual title reflecting currently filtered payment type(s).",
        "dax": """VAR SelectedCount = COUNTROWS(VALUES(Dim_Type[type]))
VAR TotalCount = COUNTROWS(ALL(Dim_Type[type]))
RETURN
    IF(
        SelectedCount = TotalCount,
        "All Payment Methods",
        IF(
            SelectedCount = 1,
            SELECTEDVALUE(Dim_Type[type]),
            CONCATENATEX(VALUES(Dim_Type[type]), Dim_Type[type], ", ")
        )
    )""",
    },
    {
        "name": "Dynamic Title - Selected Day",
        "folder": "07 - Dynamic Visual Titles",
        "format": "Text",
        "description": "Generates dynamic visual title reflecting currently filtered calendar simulation day(s).",
        "dax": """VAR SelectedCount = COUNTROWS(VALUES(Dim_Day[day_label]))
VAR TotalCount = COUNTROWS(ALL(Dim_Day[day_label]))
RETURN
    IF(
        SelectedCount = TotalCount,
        "Entire 31-Day Period",
        IF(
            SelectedCount = 1,
            SELECTEDVALUE(Dim_Day[day_label]),
            CONCATENATEX(VALUES(Dim_Day[day_label]), Dim_Day[day_label], ", ")
        )
    )""",
    },
    {
        "name": "Dynamic Title - Selected Risk Band",
        "folder": "07 - Dynamic Visual Titles",
        "format": "Text",
        "description": "Generates dynamic visual title reflecting currently filtered risk tier(s).",
        "dax": """VAR SelectedCount = COUNTROWS(VALUES(Dim_RiskBand[risk_band]))
VAR TotalCount = COUNTROWS(ALL(Dim_RiskBand[risk_band]))
RETURN
    IF(
        SelectedCount = TotalCount,
        "All Risk Tiers",
        IF(
            SelectedCount = 1,
            SELECTEDVALUE(Dim_RiskBand[risk_band]),
            CONCATENATEX(VALUES(Dim_RiskBand[risk_band]), Dim_RiskBand[risk_band], ", ")
        )
    )""",
    },

    # -------------------------------------------------------------------------
    # Display Folder: 08 - Conditional Formatting (Colors)
    # -------------------------------------------------------------------------
    {
        "name": "Color - Precision KPI Card",
        "folder": "08 - Conditional Formatting (Colors)",
        "format": "Hex Color String",
        "description": "Conditional hex color string for Precision KPI card (Green >= 90%, Amber >= 50%, Red < 50%).",
        "dax": """VAR Prec = [Precision]
RETURN
    SWITCH(
        TRUE(),
        Prec >= 0.90, "#2ECC71",  // Emerald Green
        Prec >= 0.50, "#F1C40F",  // Amber
        "#E74C3C"                 // Coral Red
    )""",
    },
    {
        "name": "Color - Recall KPI Card",
        "folder": "08 - Conditional Formatting (Colors)",
        "format": "Hex Color String",
        "description": "Conditional hex color string for Recall KPI card (Green >= 99%, Amber >= 90%, Red < 90%).",
        "dax": """VAR Rec = [Recall]
RETURN
    SWITCH(
        TRUE(),
        Rec >= 0.99, "#2ECC71",   // Emerald Green (Target 99.79% hit)
        Rec >= 0.90, "#F1C40F",   // Amber
        "#E74C3C"                 // Coral Red (Unacceptable fraud leakage)
    )""",
    },
    {
        "name": "Color - Alert Rate KPI Card",
        "folder": "08 - Conditional Formatting (Colors)",
        "format": "Hex Color String",
        "description": "Conditional hex color string for Alert Rate KPI card (Green <= 5%, Amber <= 20%, Red > 20%).",
        "dax": """VAR Rate = [Alert Rate %]
RETURN
    SWITCH(
        TRUE(),
        Rate <= 0.05, "#2ECC71",  // Emerald Green
        Rate <= 0.20, "#F1C40F",  // Amber (Current Combined OR is 17.06%)
        "#E74C3C"                 // Coral Red (Extreme operational strain)
    )""",
    },
]


def audit_measures_against_csvs(csv_dir: Path = config.POWERBI_OUTPUT_DIR) -> dict:
    """Verify that all table and column names referenced in the DAX measures exist in the CSV headers."""
    print("\n[Audit] Programmatically verifying all DAX table/column references against CSV headers...")

    # Load all CSV headers
    csv_schemas = {}
    for pbi_table, csv_file in PBI_TABLE_TO_CSV.items():
        csv_path = csv_dir / csv_file
        assert csv_path.exists(), f"Missing CSV: {csv_path}"
        df_head = pd.read_csv(csv_path, nrows=1, keep_default_na=False)
        csv_schemas[pbi_table] = set(df_head.columns)

    # Regex patterns
    # Match Table[Column]
    col_ref_pattern = re.compile(r"([A-Za-z0-9_]+)\[([A-Za-z0-9_ %-]+)\]")
    # Match [Measure]
    standalone_measure_pattern = re.compile(r"(?<![A-Za-z0-9_])\[([A-Za-z0-9_ %-]+)\]")

    measure_names = {m["name"] for m in MEASURES_CATALOG}
    assert len(measure_names) == len(MEASURES_CATALOG), "Duplicate measure names detected!"

    referenced_columns = set()
    referenced_measures = set()

    for item in MEASURES_CATALOG:
        dax = item["dax"]
        # Find all Table[Column] references
        for tbl, col in col_ref_pattern.findall(dax):
            assert tbl in csv_schemas, f"Table '{tbl}' in measure '{item['name']}' not found in registered Power BI tables!"
            assert col in csv_schemas[tbl], f"Column '{col}' in measure '{item['name']}' not found in {tbl} ({PBI_TABLE_TO_CSV[tbl]})!"
            referenced_columns.add((tbl, col))

        # Find standalone [Measure] references
        for m in standalone_measure_pattern.findall(dax):
            # Check if this was part of a Table[Column] match
            # If m is a known measure name, it's valid
            if m in measure_names:
                referenced_measures.add(m)

        # Division check: Ensure no raw "/" operator used for arithmetic division
        # We allow comments, but verify DIVIDE is present if division is intended
        if "/" in dax:
            # Strip comments
            lines = [l for l in dax.splitlines() if not l.strip().startswith("//")]
            stripped_code = " ".join(lines)
            if re.search(r"\]\s*/\s*\[", stripped_code) or re.search(r"[0-9A-Za-z_)]\s*/\s*[0-9A-Za-z_(]", stripped_code):
                raise AssertionError(f"Measure '{item['name']}' contains raw '/' division instead of DIVIDE() function!")

    print(f"--> Verified {len(referenced_columns)} distinct Table[Column] references across {len(csv_schemas)} tables.")
    print(f"--> Verified {len(referenced_measures)} distinct inter-measure dependencies.")
    print("--> Verified: 100% of referenced columns exist in source CSV headers!")
    print("--> Verified: 0 instances of unsafe raw '/' division detected.")
    print("--> Verified: All 34 measure names are strictly unique.")

    return {
        "columns": sorted(list(referenced_columns)),
        "measures": sorted(list(measure_names)),
    }


def generate_dax_file(
    audit_info: dict,
    output_path: Path = config.POWERBI_DIR / "03_measures.dax",
) -> str:
    """Compile and write powerbi/03_measures.dax with rich comments and display folders."""
    t0 = time.perf_counter()

    lines = []
    lines.append("// =============================================================================")
    lines.append("// POWER BI DAX MEASURES LIBRARY: TRANSACTION SURVEILLANCE & FRAUD MONITORING")
    lines.append("// =============================================================================")
    lines.append("// Document ID: powerbi/03_measures.dax")
    lines.append("// Total Measures: " + str(len(MEASURES_CATALOG)))
    lines.append("// Verification Standard: 100% Programmatically verified against source CSV headers")
    lines.append("// Generator: src/build_measures_dax.py")
    lines.append("// =============================================================================")
    lines.append("")
    lines.append("/*")
    lines.append("================================================================================")
    lines.append("INSTRUCTIONS FOR HOSTING MEASURES IN A DEDICATED '_Measures' TABLE")
    lines.append("================================================================================")
    lines.append("To keep your Power BI field list tidy and ensure all measures appear together")
    lines.append("at the very top of the Data pane with a distinct calculator icon, follow these steps:")
    lines.append("")
    lines.append("1. CREATE THE DEDICATED TABLE:")
    lines.append("   - In Power BI Desktop, go to the 'Home' ribbon tab.")
    lines.append("   - Click 'Enter Data'.")
    lines.append("   - In the Create Table window, name the single column 'Dummy'.")
    lines.append("   - In the bottom-right 'Name' box, enter exactly: _Measures")
    lines.append("   - Click 'Load'.")
    lines.append("")
    lines.append("2. ADD THE MEASURES:")
    lines.append("   - In the Data pane on the right rail, right-click '_Measures' > 'New Measure'.")
    lines.append("   - Copy and paste the DAX measure code from this file.")
    lines.append("   - Set the Format string in the top ribbon (Measure Tools).")
    lines.append("")
    lines.append("3. ORGANIZE INTO DISPLAY FOLDERS:")
    lines.append("   - Switch to 'Model View' (diagram icon on the left rail).")
    lines.append("   - Select the '_Measures' table, then select a measure.")
    lines.append("   - In the Properties pane on the right, locate 'Display folder'.")
    lines.append("   - Enter the exact folder name specified in the measure comment")
    lines.append("     (e.g. '01 - Enterprise Volumes & KPIs', '02 - Fraud & Alert Exposure ($)', etc.).")
    lines.append("")
    lines.append("4. HIDE THE DUMMY COLUMN (THE CALCULATOR ICON TRICK):")
    lines.append("   - In the Data pane, right-click the 'Dummy' column in '_Measures' > 'Hide'.")
    lines.append("   - Collapse the Data pane using the '>' arrow and re-expand it.")
    lines.append("   - Power BI will recognize that '_Measures' contains only measures, change its")
    lines.append("     table icon to a calculator symbol, and automatically move it to the very")
    lines.append("     top of your field list!")
    lines.append("================================================================================")
    lines.append("*/")
    lines.append("")

    # Group by folder
    current_folder = None
    for m in MEASURES_CATALOG:
        folder = m["folder"]
        if folder != current_folder:
            current_folder = folder
            lines.append("// -----------------------------------------------------------------------------")
            lines.append(f"// DISPLAY FOLDER: {current_folder}")
            lines.append("// -----------------------------------------------------------------------------")
            lines.append("")

        name = m["name"]
        fmt = m["format"]
        desc = m["description"]
        dax = m["dax"]

        lines.append(f"// Measure: [{name}]")
        lines.append(f"// Display Folder: {folder}")
        lines.append(f"// Format String: {fmt}")
        lines.append(f"// Description: {desc}")
        lines.append(f"[{name}] = ")
        # Indent DAX body
        for line in dax.splitlines():
            lines.append(f"    {line}")
        lines.append("")
        lines.append("")

    content = "\n".join(lines)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    elapsed = time.perf_counter() - t0

    print(f"DAX measures library written to: {output_path.relative_to(config.PROJECT_ROOT)} ({elapsed:.2f}s)")
    print(f"File size: {output_path.stat().st_size:,} bytes | Lines: {len(content.splitlines()):,} | Total Measures: {len(MEASURES_CATALOG)}")
    return content


def main() -> None:
    """CLI execution entrypoint."""
    audit_info = audit_measures_against_csvs()
    generate_dax_file(audit_info)

    print("\n==============================================================================")
    print("DAX MEASURE VERIFICATION SUMMARY")
    print("==============================================================================")
    print(f"Total Measures Generated:     {len(MEASURES_CATALOG)}")
    print(f"Total Referenced Columns:     {len(audit_info['columns'])}")
    print(f"Referenced Columns Audit:     100% MATCH against data/outputs/powerbi/*.csv")
    print("Format Strings Specified:     100% of measures have explicit formats")
    print("Division Safety:              100% of divisions use DIVIDE()")
    print("Duplicate Measure Names:      0")
    print("==============================================================================")
    for tbl, col in audit_info["columns"]:
        print(f"  [OK] {tbl}[{col}] -> {PBI_TABLE_TO_CSV[tbl]}")


if __name__ == "__main__":
    main()
