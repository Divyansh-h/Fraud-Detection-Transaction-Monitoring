"""Unified Power BI Report Layout & Collision Verification Suite.

File: powerbi/check_layout.py
Purpose: Parses markdown position tables from all 3 Power BI page specifications:
  - powerbi/05_page1_overview.md ("Executive Overview")
  - powerbi/06_page2_detection.md ("Rules vs ML")
  - powerbi/07_page3_investigation.md ("Investigation" + "Account Detail" sub-page)

Asserts:
  1. Every visual fits completely within the standard 1280 x 720 px canvas (0 <= x, 0 <= y, x+w <= 1280, y+h <= 720).
  2. Zero pairwise visual bounding-box overlaps/collisions on every page canvas.
  3. Referential integrity: Every referenced table column exists in data/outputs/powerbi CSVs.

Prints 'PASS' upon complete validation.
"""

from pathlib import Path
import re
import sys
import pandas as pd

# Resolve repository root
POWERBI_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = POWERBI_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config

CANVAS_WIDTH = 1280
CANVAS_HEIGHT = 720

TABLE_TO_CSV = {
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


def load_csv_schemas() -> dict[str, set[str]]:
    """Load column schemas from all exported Power BI CSVs."""
    csv_schemas = {}
    for tbl, csv_name in TABLE_TO_CSV.items():
        csv_path = config.POWERBI_OUTPUT_DIR / csv_name
        assert csv_path.exists(), f"Missing CSV data file: {csv_path}"
        df = pd.read_csv(csv_path, nrows=1)
        csv_schemas[tbl] = set(df.columns)
    return csv_schemas


def parse_markdown_tables(doc_path: Path) -> list[tuple[str, list[dict]]]:
    """Parse one or more visual specification markdown tables from a document."""
    text = doc_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    tables = []
    current_table_name = doc_path.name
    current_lines = []
    in_table = False

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("### Master Visual Table:"):
            current_table_name = stripped.replace("### Master Visual Table:", "").strip()
        elif stripped.startswith("## 2. Master Visual Specification Table"):
            current_table_name = doc_path.name

        if stripped.startswith("| Visual ID") or stripped.startswith("| **`VIS-") or stripped.startswith("| **`DT-"):
            if not in_table:
                in_table = True
                current_lines = [line]
            else:
                current_lines.append(line)
        elif in_table:
            if stripped.startswith("|"):
                current_lines.append(line)
            else:
                in_table = False
                if len(current_lines) > 2:
                    tables.append((current_table_name, current_lines))
                current_lines = []

    if in_table and len(current_lines) > 2:
        tables.append((current_table_name, current_lines))

    parsed_result = []
    for t_name, t_lines in tables:
        # Find header
        header_idx = 0
        for idx, l in enumerate(t_lines):
            if "Visual ID" in l:
                header_idx = idx
                break

        header = [c.strip() for c in t_lines[header_idx].split("|")[1:-1]]
        visuals = []

        for l in t_lines[header_idx + 1:]:
            s = l.strip()
            if not s.startswith("|") or ":---" in s or "---:" in s:
                continue
            cells = [c.strip() for c in s.split("|")[1:-1]]
            if len(cells) < len(header):
                continue
            row = dict(zip(header, cells))
            clean_id = row["Visual ID"].replace("**`", "").replace("`**", "").replace("`", "")
            row["clean_id"] = clean_id
            row["x_int"] = int(row["X"].replace("`", "").strip())
            row["y_int"] = int(row["Y"].replace("`", "").strip())
            row["w_int"] = int(row["W"].replace("`", "").strip())
            row["h_int"] = int(row["H"].replace("`", "").strip())
            visuals.append(row)

        parsed_result.append((t_name, visuals))

    return parsed_result


def audit_table_geometry(table_name: str, visuals: list[dict]) -> None:
    """Verify bounds containment and zero collisions."""
    assert len(visuals) > 0, f"Table '{table_name}' has zero parsed visuals!"
    n = len(visuals)

    # 1. Bounds audit
    for v in visuals:
        x, y, w, h = v["x_int"], v["y_int"], v["w_int"], v["h_int"]
        r, b = x + w, y + h
        vid = v["clean_id"]

        assert 0 <= x, f"Canvas [{table_name}] Visual {vid}: x < 0 ({x})"
        assert 0 <= y, f"Canvas [{table_name}] Visual {vid}: y < 0 ({y})"
        assert r <= CANVAS_WIDTH, (
            f"Canvas [{table_name}] Visual {vid}: Right boundary {r} exceeds canvas width {CANVAS_WIDTH} (w={w}, x={x})"
        )
        assert b <= CANVAS_HEIGHT, (
            f"Canvas [{table_name}] Visual {vid}: Bottom boundary {b} exceeds canvas height {CANVAS_HEIGHT} (h={h}, y={y})"
        )

    # 2. Collision audit
    collisions = []
    for i in range(n):
        v1 = visuals[i]
        x1, y1, w1, h1 = v1["x_int"], v1["y_int"], v1["w_int"], v1["h_int"]
        r1, b1 = x1 + w1, y1 + h1

        for j in range(i + 1, n):
            v2 = visuals[j]
            x2, y2, w2, h2 = v2["x_int"], v2["y_int"], v2["w_int"], v2["h_int"]
            r2, b2 = x2 + w2, y2 + h2

            separated = (r1 <= x2) or (r2 <= x1) or (b1 <= y2) or (b2 <= y1)
            if not separated:
                collisions.append(
                    f"Canvas [{table_name}]: Collision between {v1['clean_id']} ({v1.get('Title', '')}) and "
                    f"{v2['clean_id']} ({v2.get('Title', '')})! Bounding box overlap."
                )

    assert not collisions, "\n".join(collisions)


def audit_table_fields(table_name: str, visuals: list[dict], csv_schemas: dict[str, set[str]]) -> None:
    """Verify that all referenced fields and tables exist in exported CSVs."""
    col_pattern = re.compile(r"([A-Za-z0-9_]+)\[([A-Za-z0-9_]+)\]")
    missing_fields = []

    for v in visuals:
        text = " ".join([str(val) for val in v.values()])
        matches = col_pattern.findall(text)
        for tbl, col in matches:
            if tbl in ["_Measures", "Navigation"]:
                continue
            if tbl in csv_schemas:
                if col not in csv_schemas[tbl]:
                    missing_fields.append(f"Visual {v['clean_id']} in [{table_name}]: Field {tbl}[{col}] not in CSV!")
            else:
                missing_fields.append(f"Visual {v['clean_id']} in [{table_name}]: Unknown table {tbl}!")

    assert not missing_fields, "Missing field references:\n" + "\n".join(missing_fields)


def verify_page(doc_path: Path, csv_schemas: dict[str, set[str]]) -> int:
    """Audit a single markdown page specification file."""
    assert doc_path.exists(), f"Page spec file not found: {doc_path}"
    parsed_tables = parse_markdown_tables(doc_path)
    assert len(parsed_tables) >= 1, f"No visual tables found in {doc_path.name}"

    total_visuals_in_page = 0
    for t_name, visuals in parsed_tables:
        audit_table_geometry(t_name, visuals)
        audit_table_fields(t_name, visuals, csv_schemas)
        total_visuals_in_page += len(visuals)
        print(f"  * Canvas '{t_name}': {len(visuals)} visuals verified (bounds: 1280x720, collisions: 0, fields: valid).")

    return total_visuals_in_page


def main() -> None:
    """Entrypoint to verify all three Power BI report pages."""
    print("=" * 70)
    print("AUDITING POWER BI REPORT LAYOUT SPECIFICATIONS (PAGES 1, 2, 3)")
    print("=" * 70)

    csv_schemas = load_csv_schemas()
    print(f"Loaded column schemas for {len(csv_schemas)} Power BI tables from CSV.\n")

    pages = [
        ("Page 1: Executive Overview", POWERBI_DIR / "05_page1_overview.md"),
        ("Page 2: Rules vs ML", POWERBI_DIR / "06_page2_detection.md"),
        ("Page 3: Investigation", POWERBI_DIR / "07_page3_investigation.md"),
    ]

    total_audited_visuals = 0
    for page_title, page_path in pages:
        print(f"Auditing {page_title} ({page_path.name})...")
        count = verify_page(page_path, csv_schemas)
        total_audited_visuals += count
        print(f"  -> {page_title}: PASS ({count} visuals audited)\n")

    print("-" * 70)
    print(f"TOTAL VISUAL CONTAINERS AUDITED ACROSS REPORT: {total_audited_visuals}")
    print("CANVAS BOUNDS PER PAGE:                        1280 x 720 px")
    print("OUT-OF-BOUNDS ERRORS:                          0")
    print("VISUAL OVERLAPS / COLLISIONS:                  0")
    print("REFERENTIAL SCHEMA ERRORS:                     0")
    print("AUDIT RESULT:                                  PASS")
    print("=" * 70)


if __name__ == "__main__":
    main()
