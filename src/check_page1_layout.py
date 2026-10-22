"""Verification Script: Parse powerbi/05_page1_overview.md layout and assert zero overlaps.

Reads powerbi/05_page1_overview.md, parses the markdown position table,
asserts no visuals overlap, asserts every visual lies within the 1280x720 canvas,
verifies all referenced field and table names exist in exported CSVs,
and prints PASS.
"""

from pathlib import Path
import re
import sys
import pandas as pd

# Add repo root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
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


def parse_markdown_visuals_table(doc_path: Path) -> list[dict]:
    """Parse the visual specification markdown table from powerbi/05_page1_overview.md."""
    text = doc_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    # Find master table
    table_lines = []
    in_table = False
    for line in lines:
        if line.strip().startswith("| Visual ID"):
            in_table = True
            table_lines.append(line)
        elif in_table:
            if line.strip().startswith("|") and not line.strip().startswith("| :---"):
                table_lines.append(line)
            elif not line.strip().startswith("|"):
                break

    assert len(table_lines) > 1, f"No table found in {doc_path}!"
    header = [c.strip() for c in table_lines[0].split("|")[1:-1]]

    visuals = []
    for line in table_lines[1:]:
        cells = [c.strip() for c in line.split("|")[1:-1]]
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

    return visuals


def verify_layout(visuals: list[dict]) -> None:
    """Assert bounding box containment and zero pairwise collisions."""
    assert len(visuals) >= 15, f"Expected at least 15 visuals, found {len(visuals)}"

    # 1. Bounds check
    for v in visuals:
        x, y, w, h = v["x_int"], v["y_int"], v["w_int"], v["h_int"]
        r, b = x + w, y + h
        vid = v["clean_id"]
        assert 0 <= x, f"Visual {vid} x < 0: {x}"
        assert 0 <= y, f"Visual {vid} y < 0: {y}"
        assert r <= CANVAS_WIDTH, f"Visual {vid} right edge {r} exceeds canvas width {CANVAS_WIDTH}"
        assert b <= CANVAS_HEIGHT, f"Visual {vid} bottom edge {b} exceeds canvas height {CANVAS_HEIGHT}"

    # 2. Collision check
    n = len(visuals)
    collisions = []
    for i in range(n):
        v1 = visuals[i]
        x1, y1, w1, h1 = v1["x_int"], v1["y_int"], v1["w_int"], v1["h_int"]
        r1, b1 = x1 + w1, y1 + h1

        for j in range(i + 1, n):
            v2 = visuals[j]
            x2, y2, w2, h2 = v2["x_int"], v2["y_int"], v2["w_int"], v2["h_int"]
            r2, b2 = x2 + w2, y2 + h2

            # Two non-rotated rectangles do not overlap if one is completely to the left,
            # right, above, or below the other
            separated = (r1 <= x2) or (r2 <= x1) or (b1 <= y2) or (b2 <= y1)
            if not separated:
                collisions.append(
                    f"Collision detected between {v1['clean_id']} ({v1['Title']}) and {v2['clean_id']} ({v2['Title']})!"
                )

    assert not collisions, f"Visual collisions detected:\n" + "\n".join(collisions)


def verify_fields_in_csvs(visuals: list[dict]) -> None:
    """Verify all referenced table columns exist in data/outputs/powerbi CSVs."""
    csv_columns = {}
    for tbl, csv_name in TABLE_TO_CSV.items():
        csv_path = config.POWERBI_OUTPUT_DIR / csv_name
        assert csv_path.exists(), f"Missing CSV: {csv_path}"
        df = pd.read_csv(csv_path, nrows=1)
        csv_columns[tbl] = set(df.columns)

    col_pattern = re.compile(r"([A-Za-z0-9_]+)\[([A-Za-z0-9_]+)\]")
    missing_fields = []

    for v in visuals:
        text = f"{v.get('Fields (Axis, Values, Legend)', '')} {v.get('Tables & Measures Used', '')} {v.get('Sorting', '')}"
        matches = col_pattern.findall(text)
        for tbl, col in matches:
            if tbl == "_Measures":
                continue  # DAX measure
            if tbl in csv_columns:
                if col not in csv_columns[tbl]:
                    missing_fields.append(f"Visual {v['clean_id']}: Field {tbl}[{col}] not found in {TABLE_TO_CSV[tbl]}")
            else:
                missing_fields.append(f"Visual {v['clean_id']}: Unknown table {tbl}")

    assert not missing_fields, "Missing field references:\n" + "\n".join(missing_fields)


def main():
    doc_path = config.POWERBI_DIR / "05_page1_overview.md"
    assert doc_path.exists(), f"Missing {doc_path}"

    visuals = parse_markdown_visuals_table(doc_path)
    verify_layout(visuals)
    verify_fields_in_csvs(visuals)

    print(f"Verified {len(visuals)} visuals in {doc_path.name}:")
    print(f"- Zero canvas collisions detected")
    print(f"- All visuals fit within {CANVAS_WIDTH}x{CANVAS_HEIGHT} canvas bounds")
    print(f"- All referenced fields and tables exist in exported CSVs")
    print("PASS")


if __name__ == "__main__":
    main()
