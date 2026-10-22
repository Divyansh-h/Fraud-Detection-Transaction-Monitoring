# Power BI Design System, Palette & Accessibility Specification

**Document ID:** `powerbi/09_design.md`  
**Theme Name:** `Fraud Monitor` (`powerbi/fraud_theme.json`)  
**Design Philosophy:** High-Density Analytical Clarity, Dark-Navy Neutral Foundation, WCAG AA Accessibility  
**Canvas Architecture:** 1280 x 720 Standard HD (16:9) | 16 px Unified Layout Gutter  

---

## Table of Contents
1. [Theme Overview & Palette Table](#1-theme-overview--palette-table)
2. [Color Blind Safety & Semantic Color Rules](#2-color-blind-safety--semantic-color-rules)
3. [Typography Hierarchy & Font Specifications](#3-typography-hierarchy--font-specifications)
4. [Layout Spacing, Margins & 16 px Gutter Grid](#4-layout-spacing-margins--16-px-gutter-grid)
5. [Single Alert Accent Color per Page Rule](#5-single-alert-accent-color-per-page-rule)
6. [Consistent Number & Currency Formatting](#6-consistent-number--currency-formatting)
7. [WCAG AA Accessibility Audit & Contrast Ratio Table](#7-wcag-aa-accessibility-audit--contrast-ratio-table)
8. [Power BI Theme Installation Guide](#8-power-bi-theme-installation-guide)

---

## 1. Theme Overview & Palette Table

The **Fraud Monitor** theme utilizes a dark-navy neutral palette engineered specifically for financial crime surveillance. Instead of generic primary colors, every hue is balanced for readability, low eye strain, and clear visual hierarchy:

| Swatch | Color Name | Hex Code | System Role | Analytical Usage & Context |
| :---: | :--- | :---: | :--- | :--- |
| `#1E3A8A` | **Brand Navy (Primary Dark)** | `#1E3A8A` | `dataColors #1, Titles, KPI Accents` | Primary corporate accent, provides commanding authority without harsh black glare. |
| `#2563EB` | **Royal Blue (Secondary Data)** | `#2563EB` | `dataColors #2, Hourly Columns, Rule Only` | High-contrast blue for time-series bars and broad heuristic rule alerts. |
| `#B45309` | **Warning Amber (Medium Alert)** | `#B45309` | `dataColors #3, CASH_OUT Highlight, High Risk` | Accessible warm amber, alerts analysts to elevated risk without red alarm fatigue. |
| `#047857` | **Consensus Teal / Emerald (Safe / Good)** | `#047857` | `dataColors #4, Both (Consensus), Recall KPI` | High-contrast deep emerald/teal representing consensus alerts and high recall. |
| `#7C3AED` | **Surveillance Purple (ML Isolation)** | `#7C3AED` | `dataColors #5, ML Only Slices, Outliers` | Distinct violet hue for machine learning anomalies and false negatives. |
| `#B91C1C` | **Alert Red (Critical / Bad)** | `#B91C1C` | `dataColors #6, TRANSFER Highlight, TP Flag` | High-urgency crimson red reserved exclusively for confirmed fraud and critical risk. |
| `#64748B` | **Neutral Slate (Inactive / Normal)** | `#64748B` | `dataColors #7, Non-fraud types, Gridlines` | Muted slate grey for zero-fraud categories (PAYMENT, CASH_IN, DEBIT). |
| `#EA580C` | **Burnt Orange (Tertiary Highlight)** | `#EA580C` | `dataColors #8, High Risk Band Bar` | Warm orange providing distinct chromatic separation from amber and red. |

### Foundational Structural Colors
- **Canvas Background (`background`):** `#FFFFFF` (Pure Crisp White) — Provides maximum luminescent contrast against dark visual cards.
- **Primary Foreground (`foreground`):** `#0F172A` (Slate 900) — Deep slate-navy replaces harsh `#000000` for soft, elegant typography.
- **Card & Table Fill (`cardBackground`):** `#F8FAFC` (Slate 50) — Subtle cool neutral container separating visuals from the white canvas.
- **Container Border (`border`):** `#E2E8F0` (Slate 200) — 1px crisp outline providing structural boundaries without visual clutter.
- **Table Header Fill (`tableAccent`):** `#1E3A8A` (Deep Navy) — Anchor color for column headers and data bar gradients.

---

## 2. Color Blind Safety & Semantic Color Rules

### Color-Blind Safe Architecture
A common anti-pattern in surveillance dashboards is relying exclusively on red vs. green to signify bad vs. good. Individuals with Deuteranopia or Protanopia (red-green blindness) perceive both colors as muddy brownish-yellows. This theme eliminates red-green dependency through four design safeguards:
1. **Multi-Channel Distinction:** Every critical metric pairs color with **explicit text labels**, **symbols**, and **positional hierarchy**. Red is never the sole carrier of meaning.
2. **Dual-Hue Blue/Amber Dominance:** Primary visual comparisons use Navy/Blue (`#1E3A8A` / `#2563EB`) against Amber/Orange (`#B45309` / `#EA580C`), which are completely distinct across all color vision types.
3. **Teal Replacement for Pure Green:** Positive consensus outcomes utilize Deep Teal (`#047857`), which maintains high blue-channel luminance, preventing confusion with alert red.
4. **Crimson Red Isolation:** Red (`#B91C1C`) is strictly reserved for high-urgency confirmed fraud (`TRANSFER` rate, True Positives, Critical Risk). Normal transactions utilize neutral slate (`#64748B`).

---

## 3. Typography Hierarchy & Font Specifications

All typography follows Microsoft Power BI native Segoe UI font families, ensuring 100% rendering fidelity across Desktop and Power BI Service:
- **Body & Metric Values:** `Segoe UI` (Clean, highly legible geometric sans-serif).
- **Titles & Headers:** `Segoe UI Semibold` (Provides crisp optical weight without muddy bold distortion).

### Typography Hierarchy Specification

| Hierarchy Level | Font Family | Size (pt) | Weight | Color | Usage Context |
| :--- | :--- | --: | :--- | :---: | :--- |
| **KPI Callout Big Number** | `Segoe UI` | **24 pt** | Bold / Semibold | `#0F172A` | Top 6 KPI card primary metrics |
| **Card Label / Subtitle** | `Segoe UI` | **10 pt** | Semibold | `#475569` | Metric descriptors below callout values |
| **Visual Title** | `Segoe UI Semibold` | **12 pt** | Semibold | `#0F172A` | Primary visual container header |
| **Slicer Header** | `Segoe UI Semibold` | **11 pt** | Semibold | `#0F172A` | Dropdown & vertical slicer titles |
| **Slicer Items** | `Segoe UI` | **10 pt** | Regular | `#334155` | Checkbox and list values |
| **Table Column Headers** | `Segoe UI Semibold` | **10 pt** | Semibold | `#0F172A` | Table grid column headers |
| **Table Cell Values** | `Segoe UI` | **9 pt** | Regular | `#1E293B` | Data grid numerical & text cells |
| **Axis Title** | `Segoe UI Semibold` | **10 pt** | Semibold | `#475569` | X/Y Axis descriptive titles |
| **Axis Labels** | `Segoe UI` | **9 pt** | Regular | `#475569` | Numeric ticks and categorical labels |
| **Data Labels** | `Segoe UI Semibold` | **9 pt** | Semibold | `#0F172A` | Bar chart outside-end labels |

---

## 4. Layout Spacing, Margins & 16 px Gutter Grid

All report pages are built on a mathematical **1280 x 720 Standard HD Canvas** with strict **16 px unified spacing**:
- **Outer Canvas Margins:** 16 px padding on Left, Top, Right, and Bottom bounds (`X=16..1264`, `Y=16..704`).
- **Horizontal Gutters:** Exactly **16 px** between adjacent visual columns (e.g., `236 px` to `252 px` on Page 1; `750 px` to `766 px` on Page 1).
- **Vertical Gutters:** Exactly **16 px** between major content rows (e.g., `116 px` to `128 px`; `404 px` to `420 px`).
- **Sub-item Gutter (Left Slicer Rail):** Compact **12 px** vertical gutter between slicers to maximize vertical data capacity.
- **Zero Overlap Guarantee:** Bounding boxes are audited programmatically by `powerbi/check_layout.py` to assert $(r_1 \le x_2) \lor (r_2 \le x_1) \lor (b_1 \le y_2) \lor (b_2 \le y_1)$.

---

## 5. Single Alert Accent Color per Page Rule

To prevent 'dashboard carnival syndrome' and alarm fatigue, the design system enforces the **Single Alert Accent Rule**:
> **Each report page is permitted AT MOST ONE chromatic accent color for urgent alerts.**  
> **All surrounding context MUST remain in neutral slate, navy, or muted tones.**

### Page-by-Page Enforcement:
1. **Page 1 (Executive Overview):**
   - Primary Canvas: Navy (`#1E3A8A`) and Neutral Slate (`#CBD5E1`).
   - **Sole Alert Accent:** Crimson Red (`#B91C1C`) applied exclusively to `TRANSFER` fraud rate and Confirmed Fraud line in `VIS-05`.
2. **Page 2 (Rules vs ML):**
   - Primary Canvas: Deep Navy (`#1E3A8A`) and Blue (`#3B82F6`).
   - **Sole Alert Accent:** Soft Crimson (`#B91C1C`) applied exclusively to False Negatives (escaped fraud) in `VIS-11`.
3. **Page 3 (Investigation):**
   - Primary Canvas: Slate (`#94A3B8`) and Blue (`#2563EB`).
   - **Sole Alert Accent:** High-urgency Red (`#B91C1C` / `#EF4444`) applied exclusively to True Positive fraud points and Critical Risk band.

---

## 6. Consistent Number & Currency Formatting

Every numeric field across the data model is formatted with deterministic standard formats:

| Metric Category | DAX / Power BI Format String | Output Example | Plain-English Rule |
| :--- | :--- | :--- | :--- |
| **Transaction Counts** | `#,##0` | `6,362,620` | Always include commas; zero decimal places |
| **Alert Counts** | `#,##0` | `1,085,609` | Integer with thousand separators |
| **Currency (Billions)** | `$#,##0.00"B"` (or `$0.00B`) | `$407.88B` | Formatted in Billions with 2 decimals |
| **Currency (Ledger)** | `$#,##0` | `$181,924` | Exact integer currency in tables |
| **General Percentages** | `0.0%` (or `0.00%`) | `17.1%` (or `98.65%`) | 1 or 2 decimals for alert rate / precision |
| **Prevalence / Fraud Rate** | `0.000%` | `0.129%` | **Mandatory 3 decimals** to reflect 0.129% baseline |
| **Type-Specific Rates** | `0.000%` | `0.769%` (TRANSFER) | 3 decimals (TRANSFER=0.769%, CASH_OUT=0.184%) |
| **Anomaly Scores** | `0.0%` | `70.4%` | Isolation Forest percentile (0.0% to 100.0%) |
| **Combo Risk Score** | `0.000` | `1.428` | Composite score (0.000 to 2.000) |

---

## 7. WCAG AA Accessibility Audit & Contrast Ratio Table

### Accessibility Requirements:
- **WCAG 2.1 Level AA Standard:** Minimum contrast ratio of **4.5:1** for normal text (< 18 pt), and **3.0:1** for large text (>= 18 pt or >= 14 pt bold).
- **Our Standard:** **EVERY text and background combination exceeds 4.5:1**, providing universal accessibility across all display environments.

### Contrast Ratio Audit Matrix (Computed Programmatically via Python)

| Visual Interface Element | Foreground (Text) | Background (Fill) | Contrast Ratio | WCAG AA Status | Luminescence Analysis |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Primary Headings & Card Values** | `#0F172A` | `#FFFFFF` | **`17.85:1`** | **`PASS`** | Main canvas titles and KPI numbers |
| **Primary Text in Callout Cards** | `#0F172A` | `#F8FAFC` | **`17.06:1`** | **`PASS`** | Executive briefing card & table headers |
| **Secondary Labels & Axis Text** | `#475569` | `#FFFFFF` | **`7.58:1`** | **`PASS`** | Slicer items, chart axis labels, tooltips |
| **Secondary Labels on Card Fills** | `#475569` | `#F8FAFC` | **`7.24:1`** | **`PASS`** | KPI card category subtitles |
| **Brand Navy Text / Badges** | `#1E3A8A` | `#FFFFFF` | **`10.36:1`** | **`PASS`** | Total Alerts KPI callout & table title |
| **Brand Navy on Light Slate Fill** | `#1E3A8A` | `#F1F5F9` | **`9.45:1`** | **`PASS`** | Navigator button unselected state |
| **Dark Alert Red Text** | `#B91C1C` | `#FFFFFF` | **`6.47:1`** | **`PASS`** | High-risk fraud numbers & warning callouts |
| **Dark Alert Red on Light Tint** | `#991B1B` | `#FEE2E2` | **`6.80:1`** | **`PASS`** | Confusion Matrix False Positive callout |
| **Warning Amber Text** | `#B45309` | `#FFFFFF` | **`5.02:1`** | **`PASS`** | CASH_OUT rate & medium risk callout |
| **Warning Amber on Light Tint** | `#92400E` | `#FEF3C7` | **`6.37:1`** | **`PASS`** | Medium risk badge background |
| **Success Teal / Green Text** | `#047857` | `#FFFFFF` | **`5.48:1`** | **`PASS`** | Recall 99.79% KPI & Consensus metrics |
| **Success Green on Light Tint** | `#065F46` | `#D1FAE5` | **`6.78:1`** | **`PASS`** | Confusion Matrix True Positive cell |
| **White Button Text on Navy Fill** | `#FFFFFF` | `#1E3A8A` | **`10.36:1`** | **`PASS`** | Page navigator active selected tab |
| **White Button Text on Red Fill** | `#FFFFFF` | `#B91C1C` | **`6.47:1`** | **`PASS`** | High-urgency investigation pill |

> [!TIP]  
> **Verification Result:** All 14 evaluated text/background pairings meet or exceed the **4.5:1** contrast threshold. Highest contrast: Primary headings on canvas (**17.85:1**). Lowest contrast: Warning Amber text on canvas (**5.02:1**).

---

## 8. Power BI Theme Installation Guide

To import `powerbi/fraud_theme.json` into Power BI Desktop:
1. Open your Power BI report file (`.pbix`).
2. On the ribbon, navigate to the **View** tab.
3. In the **Themes** gallery dropdown, click the downward arrow and select **Browse for themes**.
4. In the file explorer, navigate to the report directory and select:  
   `powerbi/fraud_theme.json`
5. Click **Open**. Power BI Desktop will display a success prompt:  
   *'Theme imported successfully'*. All default visual titles, font sizes, data colors, and transparent borders will automatically align.

---
*Design system and theme specification compiled programmatically by `src/build_design_theme.py`.*