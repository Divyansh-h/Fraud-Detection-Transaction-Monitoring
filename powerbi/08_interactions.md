# Power BI Interaction, Slicer Synchronization & Navigation Architecture

**Document ID:** `powerbi/08_interactions.md`  
**Report Scope:** Cross-Page Interactivity, Visual Decoupling, State Management & Custom Tooltips  
**Target Audience:** Power BI Developers, BI Architects, Lead Analytics Engineers  
**Standard Canvas Size:** 1280 x 720 px (16:9 HD) | Tooltip Canvas: 320 x 220 px  

---

## Table of Contents
1. [Slicer Synchronization Architecture](#1-slicer-synchronization-architecture)
   - [Sync Rationale & Global vs. Local Scope](#sync-rationale--global-vs-local-scope)
   - [Master Slicer Synchronization Matrix](#master-slicer-synchronization-matrix)
   - [Numbered Configuration Steps (View > Sync Slicers)](#numbered-configuration-steps-view--sync-slicers)
2. [Edit-Interactions Matrices per Page](#2-edit-interactions-matrices-per-page)
   - [Core Visual Interaction Principles](#core-visual-interaction-principles)
   - [Page 1 (Executive Overview) Interaction Matrix](#page-1-executive-overview-interaction-matrix)
   - [Page 2 (Rules vs ML) Interaction Matrix](#page-2-rules-vs-ml-interaction-matrix)
   - [Page 3 (Investigation) Interaction Matrix](#page-3-investigation-interaction-matrix)
   - [Numbered Steps to Configure Edit Interactions](#numbered-steps-to-configure-edit-interactions)
3. [Bookmark & State Management Architecture](#3-bookmark--state-management-architecture)
   - [Bookmark 1: All Transactions (Default State)](#bookmark-1-all-transactions-default-state)
   - [Bookmark 2: Fraud-Prone Types Only (TRANSFER + CASH_OUT)](#bookmark-2-fraud-prone-types-only-transfer--cash_out)
   - [Bookmark 3: High & Critical Risk Only](#bookmark-3-high--critical-risk-only)
   - [Bookmark 4: Reset Filters Action](#bookmark-4-reset-filters-action)
4. [Report Navigation Systems & Info (i) Tooltip Button](#4-report-navigation-systems--info-i-tooltip-button)
   - [Global Page Navigator Bar](#global-page-navigator-bar)
   - [Information (i) Tooltip Button on Executive Overview](#information-i-tooltip-button-on-executive-overview)
   - [Tooltip Page Spec: 'Tooltip - Alert Definition'](#tooltip-page-spec-tooltip---alert-definition)
5. [Custom Tooltip Page Spec: Fraud Rate Bar Chart (`VIS-04`)](#5-custom-tooltip-page-spec-fraud-rate-bar-chart-vis-04)
   - [Tooltip Page Layout & Wireframe](#tooltip-page-layout--wireframe)
   - [Tooltip Master Visual Specification Table](#tooltip-master-visual-specification-table)
   - [Step-by-Step Binding Guide to VIS-04](#step-by-step-binding-guide-to-vis-04)

---

## 1. Slicer Synchronization Architecture

### Sync Rationale & Global vs. Local Scope
In a multi-page financial crime monitoring solution, uncontrolled slicer propagation can produce catastrophic metric distortion. Therefore, slicer synchronization is partitioned into two distinct operational scopes:
1. **Global Domain Slicers (Synchronized across Pages 1, 2, and 3):**
   - `Payment Method` (`Dim_Type[type]`): When an executive or investigator filters to `TRANSFER` or `CASH_OUT`, that categorical scope MUST persist across Executive Overview, Model Diagnostics, and Transaction Investigation.
   - `Simulation Day Range` (`Dim_Day[day]`): A temporal zoom (e.g., investigating Days 10 to 15 spike) must remain synchronized to preserve chronological context across all three analytical views.
2. **Local Page-Specific Slicers (Isolated to individual pages):**
   - `Alert Source` (`Dim_AlertSource[alert_source]`): Local to Page 1. Triage source attribution is an executive exploration angle; synchronizing it to Page 3 would accidentally pre-filter the raw investigation ledger.
   - `Amount Magnitude Band` (`Dim_AmountBand[amount_band]`): Local to Page 1. Slices executive prevalence; Page 3 uses interactive log-scale scatter filtering instead.
   - `Risk Band` (`Dim_RiskBand[risk_band]`): Local to Page 3. Drives tactical alert queue triage.
   - `Surveillance Outcome` (`Fact_Transactions[outcome]`): Local to Page 3. Used exclusively for case ledger categorization (TP vs FP audit).

### Master Slicer Synchronization Matrix

| Slicer Name | Underlying Field | Sync Group Name | Page 1: Sync | Page 1: Visible | Page 2: Sync | Page 2: Visible | Page 3: Sync | Page 3: Visible | Query Pass-Through |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Payment Method** | `Dim_Type[type]` | `Sync_PaymentType` | **YES** | **YES** | **YES** | NO (Hidden) | **YES** | **YES** | Active 1-to-many relationship |
| **Simulation Day Range** | `Dim_Day[day]` | `Sync_DayRange` | **YES** | **YES** | **YES** | NO (Hidden) | **YES** | NO (Hidden) | Active 1-to-many relationship |
| **Alert Source** | `Dim_AlertSource[alert_source]` | `Local_P1_Source` | **NO** | **YES** | **NO** | NO | **NO** | NO | Scoped to Page 1 only |
| **Amount Magnitude Band** | `Dim_AmountBand[amount_band]` | `Local_P1_Amount` | **NO** | **YES** | **NO** | NO | **NO** | NO | Scoped to Page 1 only |
| **Risk Band** | `Dim_RiskBand[risk_band]` | `Local_P3_Risk` | **NO** | NO | **NO** | NO | **NO** | **YES** | Scoped to Page 3 only |
| **Surveillance Outcome** | `Fact_Transactions[outcome]` | `Local_P3_Outcome` | **NO** | NO | **NO** | NO | **NO** | **YES** | Scoped to Page 3 only |

> [!IMPORTANT]  
> On Page 2 (*Rules vs ML*), `Payment Method` and `Simulation Day Range` are configured with **Sync = YES** but **Visible = NO**. This allows filters selected on Page 1 or Page 3 to silently govern the daily stacked column chart (`VIS-12`) without cluttering Page 2's diagnostic canvas.
### Numbered Configuration Steps (View > Sync slicers)
Follow these exact numbered instructions in Power BI Desktop to configure slicer synchronization via **View > Sync slicers**:
1. On the top ribbon, navigate to **View > Sync slicers** (check the **Sync slicers** box) to open the configuration pane on the right.
2. Navigate to **Page 1 (Executive Overview)** and click visual **`VIS-03A` (Payment Method Slicer)**.
3. In the **Sync slicers** pane, under the table of page names:
   - Check the **Sync** checkbox for `Executive Overview`, `Rules vs ML`, and `Investigation`.
   - Check the **Visible** checkbox ONLY for `Executive Overview` and `Investigation`.
   - Expand **Advanced options**, and enter group name: `Sync_PaymentType`.
4. Click visual **`VIS-03B` (Simulation Day Slider)**:
   - Check the **Sync** checkbox for `Executive Overview`, `Rules vs ML`, and `Investigation`.
   - Check the **Visible** checkbox ONLY for `Executive Overview`.
   - In Advanced options, set group name: `Sync_DayRange`.
5. Click visual **`VIS-03C` (Alert Source Slicer)**:
   - Ensure all Sync checkboxes are **UNCHECKED** for other pages. Visible is checked ONLY for `Executive Overview`.
6. Click visual **`VIS-03D` (Amount Magnitude Band Slicer)**:
   - Ensure all Sync checkboxes are **UNCHECKED** for other pages. Visible is checked ONLY for `Executive Overview`.
7. Navigate to **Page 3 (Investigation)**, select **`VIS-13B` (Risk Band Slicer)** and **`VIS-13C` (Outcome Slicer)**:
   - Ensure both slicers have Sync unchecked for all other pages, and Visible checked ONLY for `Investigation`.
8. Click **File > Save** to persist synchronization groups.

---

## 2. Edit-Interactions Matrices per Page

### Core Visual Interaction Principles
Power BI visuals default to bidirectional cross-filtering, which causes metric inaccuracies if unmanaged. The following core architectural rules are strictly enforced:
1. **Total Transactions Isolation:** Slicers for `Alert Source` and `Risk Band` MUST NOT filter the `Total Transactions` KPI card (`VIS-01A`). Because `Agg_ByType[total_txns]` represents the entire enterprise census (6,362,620 transactions) and unalerted normal transactions do not possess an alert source or risk band, applying these slicers would blank or corrupt the baseline denominator.
2. **Bar Click Decoupling:** Clicking a bar on `VIS-04` (Fraud Rate by Payment Type) MUST cross-filter the temporal line chart (`VIS-05`), hourly column (`VIS-06`), and donut (`VIS-07`), but MUST NOT filter the top-level KPI cards (`VIS-01A` to `VIS-01F`). The executive KPI row must reflect the primary page slicers rather than transient visual highlights.
3. **Static Benchmark Protection:** Static evaluation tables on Page 2 (`Metrics_Approach`, `Metrics_Rules`, `Confusion_Matrix`) must ignore intra-page visual selections to prevent inconsistent diagnostic reporting.

### Page 1 (Executive Overview) Interaction Matrix

The table below specifies the target visual behavior (`Filter`, `Highlight`, or `None`) when interacting with source slicers or visual selections on Page 1:

| Source Visual / Slicer | VIS-01A (Txns) | VIS-01B (Alerts) | VIS-01C (Flagged $) | VIS-01D (Fraud Rate) | VIS-01E (Precision) | VIS-01F (Recall) | VIS-02 (Brief) | VIS-04 (Bar) | VIS-05 (Line) | VIS-06 (Hour) | VIS-07 (Donut) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`VIS-03A` (Type Slicer)** | **Filter** | **Filter** | **Filter** | **Filter** | **Filter** | **Filter** | None | **Filter** | **Filter** | **Filter** | **Filter** |
| **`VIS-03B` (Day Slider)** | **Filter** | **Filter** | **Filter** | **Filter** | **Filter** | **Filter** | None | **Filter** | **Filter** | **Filter** | **Filter** |
| **`VIS-03C` (Alert Source Sl.)** | **NONE** | **Filter** | **Filter** | **Filter** | **Filter** | **Filter** | None | **NONE** | **Filter** | **Filter** | **Filter** |
| **`VIS-03D` (Amount Band Sl.)** | **Filter** | **Filter** | **Filter** | **Filter** | **Filter** | **Filter** | None | **Filter** | **Filter** | **Filter** | **Filter** |
| **`VIS-04` (Fraud Rate Bar)** | **NONE** | **NONE** | **NONE** | **NONE** | **NONE** | **NONE** | None | — | **Filter** | **Filter** | **Filter** |
| **`VIS-05` (Daily Trend Line)** | **NONE** | **NONE** | **NONE** | **NONE** | **NONE** | **NONE** | None | **Filter** | — | **Filter** | **Filter** |
| **`VIS-06` (Hourly Column)** | **NONE** | **NONE** | **NONE** | **NONE** | **NONE** | **NONE** | None | **Filter** | **Filter** | — | **Filter** |
| **`VIS-07` (Donut Attribution)** | **NONE** | **NONE** | **NONE** | **NONE** | **NONE** | **NONE** | None | **NONE** | **Filter** | **Filter** | — |

> [!CAUTION]  
> Pay special attention to the row **`VIS-04` (Fraud Rate Bar)**: its interaction to all 6 KPI cards is set to **NONE**, while its interaction to `VIS-05` (Line Chart), `VIS-06` (Column Chart), and `VIS-07` (Donut) is set to **Filter**.

### Page 2 (Rules vs ML) Interaction Matrix

| Source Visual | VIS-08 (Brief Banner) | VIS-09 (Strategy Bar) | VIS-10 (Rules Table) | VIS-11 (Confusion Matrix) | VIS-12 (Daily Alerts Column) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **`VIS-09` (Strategy Bar Click)** | None | — | **Highlight** | **Highlight** | **Filter** |
| **`VIS-10` (Rule Table Selection)** | None | **None** | — | **None** | **Filter** |
| **`VIS-11` (Confusion Matrix Cell)** | None | **None** | **None** | — | **Filter** |
| **`VIS-12` (Daily Column Click)** | None | **None** | **None** | **None** | — |

### Page 3 (Investigation) Interaction Matrix

| Source Visual / Slicer | VIS-13A (Type) | VIS-13B (Risk Band) | VIS-13C (Outcome) | VIS-14 (Risk Bar) | VIS-15 (Top 20 Table) | VIS-16 (Scatter Plot) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **`VIS-13A` (Type Slicer)** | — | **Filter** | **Filter** | **Filter** | **Filter** | **Filter** |
| **`VIS-13B` (Risk Band Slicer)** | **Filter** | — | **Filter** | **Highlight** | **Filter** | **Filter** |
| **`VIS-13C` (Outcome Slicer)** | **Filter** | **Filter** | — | **Filter** | **Filter** | **Filter** |
| **`VIS-14` (Risk-Band Bar)** | **None** | **None** | **None** | — | **Filter** | **Filter** |
| **`VIS-15` (Top 20 Row Click)** | **None** | **None** | **None** | **None** | — | **Highlight** |
| **`VIS-16` (Scatter Point Click)** | **None** | **None** | **None** | **None** | **Filter** | — |

### Numbered Steps to Configure Edit Interactions
1. On Page 1, select visual **`VIS-03C` (Alert Source Slicer)**.
2. On the top menu ribbon, navigate to **Format > Edit interactions** (small filter/highlight/none icons will appear above every visual).
3. Locate visual **`VIS-01A` (`Total Transactions`)** and click the **None** icon (circle with diagonal slash).
4. Locate visual **`VIS-04` (`Fraud Rate % by Type`)** and click the **None** icon.
5. Now select visual **`VIS-04` (Fraud Rate Bar Chart)**:
   - Click the **None** icon above **all 6 KPI cards** (`VIS-01A` through `VIS-01F`).
   - Ensure the **Filter** icon is active above `VIS-05` (Line Chart), `VIS-06` (Column Chart), and `VIS-07` (Donut Chart).
6. Select visual **`VIS-07` (Donut Chart)**:
   - Click the **None** icon above `VIS-01A` (Total Transactions) and `VIS-04`.
7. Click **Format > Edit interactions** on the ribbon again to turn off edit mode and save.

---

## 3. Bookmark & State Management Architecture

Four executive bookmarks provide one-click investigation scenarios and filter resets:

### Bookmark 1: 'All Transactions' (Default State)
- **Purpose:** Restores report to full 6.36M transaction universe with no filters applied.
- **Exact Configuration Steps:**
  1. Open the **Bookmarks** pane (**View > Bookmarks**) and **Selection** pane (**View > Selection**).
  2. In `VIS-03A` (Payment Method), select **(Select All)**.
  3. In `VIS-03B` (Simulation Day Slider), set range to full: `1` to `31`.
  4. In `VIS-03C` (Alert Source), select **(All)**.
  5. In `VIS-03D` (Amount Band), select **(All)**.
  6. Ensure no visual chart elements are selected or highlighted.
  7. In the Bookmarks pane, click **Add** and rename the bookmark to: `All transactions`.
  8. Click the ellipsis (**...**) next to `All transactions` and configure:
     - **Data:** Checked (ON)
     - **Display:** Checked (ON)
     - **Current page:** Checked (ON)
     - **All visuals:** Checked (ON)
  9. Click **Update** to save the state.

### Bookmark 2: 'Fraud-Prone Types Only (TRANSFER + CASH_OUT)'
- **Purpose:** Focuses surveillance specifically on the active modeling scope (2,770,409 transactions) where 100% of fraud occurs.
- **Exact Configuration Steps:**
  1. In `VIS-03A` (Payment Method Slicer), uncheck all types and check ONLY: `TRANSFER` and `CASH_OUT`.
  2. In `VIS-03B`, ensure range is set to `1` to `31`.
  3. Verify `VIS-01A` updates to 2,770,409 transactions and `VIS-01D` displays 0.296% fraud rate.
  4. In the Bookmarks pane, click **Add** and rename to: `Fraud-prone types only (TRANSFER + CASH_OUT)`.
  5. Click the ellipsis (**...**) and configure:
     - **Data:** Checked (ON)
     - **Display:** Checked (ON)
     - **Current page:** Checked (ON)
     - **All visuals:** Checked (ON)
  6. Click **Update** to save.

### Bookmark 3: 'Critical Risk Only'
- **Purpose:** Isolates high-urgency triage cases. In the underlying data model, `Critical` has 0 cases and `High` contains 3,402 alerts with 3,397 confirmed frauds (99.85% precision). To deliver actionable operational triage, this bookmark filters to `High` and `Critical` risk bands.
- **Exact Configuration Steps:**
  1. Navigate to **Page 3 (Investigation)**.
  2. In `VIS-13B` (Risk Band Slicer), check `High` and `Critical`.
  3. In `VIS-13C` (Outcome Slicer), select `(All)`.
  4. In the Bookmarks pane, click **Add** and rename to: `Critical risk only`.
  5. Click the ellipsis (**...**) and configure:
     - **Data:** Checked (ON)
     - **Display:** Checked (ON)
     - **Current page:** Checked (ON)
     - **All visuals:** Checked (ON)
  6. Click **Update** to save.

### Bookmark 4: 'Reset Filters Action'
- **Purpose:** Universal reset button that clears transient slicer selections on the active page without forcing page transitions.
- **Exact Configuration Steps:**
  1. Set all slicers on the current page to their default clear states.
  2. In the Bookmarks pane, click **Add** and rename to: `Reset filters`.
  3. Click the ellipsis (**...**) and configure:
     - **Data:** Checked (ON)
     - **Display:** UNCHECKED (OFF)
     - **Current page:** Checked (ON)
     - **All visuals:** Checked (ON)
  4. Click **Update**.
  5. To wire to the UI: On Page 1, click **Insert > Buttons > Reset**.
  6. Position the button at: `X = 186`, `Y = 282`, `Width = 50`, `Height = 24` (adjacent to Payment Method header).
  7. In **Format > Action**, toggle **On**, set **Type = Bookmark**, and select **Bookmark = Reset filters**.

---

## 4. Report Navigation Systems & Info (i) Tooltip Button

### Global Page Navigator Bar
To ensure seamless cross-page movement, every page includes a standardized, non-overlapping Page Navigator bar positioned along the top right of the canvas:
- **Component Type:** Native Page Navigator (`Insert > Buttons > Navigator > Page navigator`)
- **Geometry:** `X = 766`, `Y = 16`, `Width = 498`, `Height = 32` (on Pages 2 & 3), or integrated into custom header tabs.
- **Page Display Names:**
  1. `1. Executive Overview` (Routes to `powerbi/05_page1_overview.md`)
  2. `2. Rules vs ML` (Routes to `powerbi/06_page2_detection.md`)
  3. `3. Investigation` (Routes to `powerbi/07_page3_investigation.md`)
- **Hidden Pages:** The `Account Detail` sub-page and all tooltip pages (`Tooltip - Alert Definition`, `Tooltip - Type Details`) are configured with **Hide in report** = ON, so they never appear in the Page Navigator.
- **Navigator Styling:**
  - Default Fill: `#F1F5F9` (Slate light), Border: 1px `#CBD5E1`, Text: 11 pt Semibold `#334155`.
  - Selected Fill: `#1E3A8A` (Deep Navy), Text: 11 pt Bold `#FFFFFF`.
  - Hover Fill: `#E2E8F0`, Text: 11 pt Bold `#1E293B`.

### Information (i) Tooltip Button on Executive Overview
To explain the official alert triage logic to executives without cluttering the canvas, an information icon is embedded inside `VIS-02` (Surveillance Intelligence Brief):
- **Button Type:** Icon Button (Type: Information `i`)
- **Coordinates:** `X = 206`, `Y = 132`, `Width = 24`, `Height = 24` (nested inside top-right corner of `VIS-02`)
- **Action Settings:**
  - Action: **ON**
  - Type: **Tooltip**
  - Tooltip Type: **Report Page**
  - Page: **`Tooltip - Alert Definition`**

### Tooltip Page Spec: 'Tooltip - Alert Definition'
- **Page Name:** `Tooltip - Alert Definition`
- **Page Configuration:**
  - Page Type: **Tooltip** (In Format pane > Page Information > Allow use as tooltip = ON)
  - Canvas Size: **Custom: 320 x 180 px**
  - Visibility: **Hidden in report tabs**
- **Visual Containers on Canvas (320 x 180 px):**
  1. **Title Header (`x = 12, y = 10, w = 296, h = 30`):**
     - Text: **OFFICIAL SURVEILLANCE ALERT DEFINITION**
     - Font: 11 pt Bold `#1E3A8A`, 1px bottom accent border `#3B82F6`.
  2. **Alert Logic Narrative Box (`x = 12, y = 46, w = 296, h = 124`):**
     - Background: `#F8FAFC`, Border: 1px `#E2E8F0`, Radius: 4px.
     - Exact Static Text:
       > **Alert Definition (Combined OR): An alert is triggered when a transaction is flagged by ANY of the 7 heuristic SQL rules (e.g. Account Emptied, Mule Destination) OR by the Calibrated Isolation Forest ML model (Threshold >= 0.704 on TRANSFER & CASH_OUT).**  
       > **Surveillance Performance: Captures 99.79% of all fraud (8,196 of 8,213 events), securing $407.88B in monitored flow and preventing $12.06B in criminal theft.**

---

## 5. Custom Tooltip Page Spec: Fraud Rate Bar Chart (`VIS-04`)

When a user hovers over any payment type bar on `VIS-04` (e.g., `TRANSFER`, `CASH_OUT`, or `PAYMENT`), a rich micro-dashboard appears displaying exact counts and triage precision.

### Tooltip Page Layout & Wireframe
- **Report Page Name:** `Tooltip - Type Details`
- **Canvas Dimensions:** 320 x 220 pixels
- **Allow use as tooltip:** **ON**

```text
+------------------------------------------------------------------+
|                     CANVAS: 320 x 220 PIXELS                     |
+------------------------------------------------------------------+
| [TT-01: Header Card - Selected Payment Type: Dim_Type[type]]     | (y=10..44)
| (x=12, y=10, w=296, h=34)                                        |
+-----------------------+------------------+-----------------------+
| [TT-02: Fraud Count]  | [TT-03: Alerts]  | [TT-04: Precision]    | (y=50..110)
| Agg_ByType[fraud_cnt] | Agg_ByType[alert]| TP / Total Alerts     |
| (x=12, w=92, h=60)    | (x=114, w=92, h) | (x=216, w=92, h=60)   |
+-----------------------+------------------+-----------------------+
| [TT-05: Mini Metrics Breakdown Table]                            | (y=118..210)
| Total Transactions, Total Flagged Value ($), Fraud Rate %        |
| (x=12, y=118, w=296, h=92)                                       |
+------------------------------------------------------------------+
```

### Tooltip Master Visual Specification Table

| Visual ID | Type | Title | Data Fields (Axis / Values) | Source Column / Measure | X | Y | W | H | Formatting Notes |
| :--- | :--- | :--- | :--- | :--- | --: | --: | --: | --: | :--- |
| **`TT-01`** | `Card` | **Payment Type** | `Values: Dim_Type[type]` | `Dim_Type[type]` | `12` | `10` | `296` | `34` | Callout: 14 pt Bold Accent Navy `#1E3A8A`. Background: `#F1F5F9`, Border: 1px `#CBD5E1`. |
| **`TT-02`** | `Card` | **Fraud Count** | `Values: Agg_ByType[fraud_count]` | `Agg_ByType[fraud_count]` | `12` | `50` | `92` | `60` | Callout: 16 pt Bold `#E74C3C` (Crimson), Label: 9 pt Semibold `#64748B`. Format: `#,##0`. |
| **`TT-03`** | `Card` | **Alert Count** | `Values: Agg_ByType[alert_count]` | `Agg_ByType[alert_count]` | `114` | `50` | `92` | `60` | Callout: 16 pt Bold `#1E3A8A` (Navy), Label: 9 pt Semibold `#64748B`. Format: `#,##0`. |
| **`TT-04`** | `Card` | **Alert Precision** | `Values: DIVIDE(tp, alert_count)` | `_Measures[Precision by Type]` | `216` | `50` | `92` | `60` | Callout: 16 pt Bold `#10B981` (Green), Label: 9 pt Semibold `#64748B`. Format: `0.00%`. |
| **`TT-05`** | `Table` | **Volume & Prevalence** | `Total Txns, Flagged $, Fraud Rate %` | `Agg_ByType[total_txns], flagged_value, fraud_rate_pct` | `12` | `118` | `296` | `92` | Compact table showing: Total Txns (`#,##0`), Flagged Value (`$0.00B`), Fraud Rate (`0.000%`). Alternating rows `#F8FAFC`. |

### Step-by-Step Binding Guide to VIS-04
Follow these exact numbered steps to link `Tooltip - Type Details` to `VIS-04`:
1. Create a new report page, name it `Tooltip - Type Details`.
2. In the **Format page** pane on the right:
   - Expand **Page information** > Toggle **Allow use as tooltip** to **ON**.
   - Expand **Canvas settings** > Set **Type** to **Custom** > Width: `320 px`, Height: `220 px`.
3. Right-click the page tab at the bottom and select **Hide page**.
4. Place visual containers `TT-01` through `TT-05` at the exact coordinates defined in the table above.
5. Navigate back to **Page 1 (Executive Overview)** and click visual **`VIS-04` (Fraud Rate % by Transaction Type)**.
6. In the **Format visual** pane:
   - Click the **General** tab.
   - Expand the **Tooltips** card (ensure it is toggled **ON**).
   - Under **Type**, select **Report page**.
   - Under **Page**, select **`Tooltip - Type Details`**.
7. Hover over `TRANSFER` and `CASH_OUT` bars on `VIS-04` to verify the micro-dashboard activates with type-specific metrics.

---
*Interaction and navigation specification compiled programmatically by `src/build_interactions_doc.py`.*