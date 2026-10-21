# Transaction Monitoring Heuristic Rule Engine Evaluation

**Document ID:** `08_rule_evaluation.md`  
**Data Sources:** DuckDB tables `rule_flags` (SCOPED: 2,770,409 rows) and `transactions` (FULL: 6,362,620 rows)  
**Total Fraud Events:** 8,213 (100% contained in `TRANSFER` and `CASH_OUT`)  

---

## 1. Executive Summary & Comparative Matrix (SCOPED Universe)

Evaluation strictly within the modeling scope (`TRANSFER` and `CASH_OUT`, $N = 2,770,409$, Fraud = $8,213$). Table sorted by **F1 Score descending**:

| Rule ID | Rule Name | Alerts | TP | FP | FN | Precision (%) | Recall (%) | FPR (%) | F1 Score | Flagged Value ($) | Share of Value (%) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `rule_emptied` | Rule 1: Account Emptied | 8,008 | 8,008 | 0 | 205 | 100.00% | 97.50% | 0.0000% | **0.9874** | $10,547,398,416.82 | 1.20% |
| `rule_dest_unchanged` | Rule 6: Destination Balance Unchanged | 4,042 | 3,940 | 102 | 4,273 | 97.48% | 47.97% | 0.0037% | **0.6430** | $6,078,483,439.62 | 0.69% |
| `rule_large_amount` | Rule 2: Large Amount Outlier | 24,818 | 1,806 | 23,012 | 6,407 | 7.28% | 21.99% | 0.8331% | **0.1094** | $67,410,813,776.79 | 7.66% |
| `is_rule_alert_2` | Composite Alert: Score >= 2 | 267,021 | 5,908 | 261,113 | 2,305 | 2.21% | 71.93% | 9.4531% | **0.0429** | $140,840,275,000.38 | 16.01% |
| `is_rule_alert_1` | Composite Alert: Score >= 1 | 1,085,554 | 8,190 | 1,077,364 | 23 | 0.75% | 99.72% | 39.0039% | **0.0150** | $407,883,157,529.56 | 46.37% |
| `rule_mule_dest` | Rule 5: Mule Destination (Day) | 748,575 | 647 | 747,928 | 7,566 | 0.09% | 7.88% | 27.0773% | **0.0017** | $273,322,873,217.94 | 31.07% |
| `rule_balance_error` | Rule 7: Balance Inconsistency | 570,732 | 26 | 570,706 | 8,187 | 0.00% | 0.32% | 20.6613% | **0.0001** | $199,218,661,068.58 | 22.65% |
| `rule_velocity` | Rule 3: Originator Velocity (6h) | 0 | 0 | 0 | 8,213 | 0.00% | 0.00% | 0.0000% | **0.0000** | $0.00 | 0.00% |
| `rule_transfer_then_cashout` | Rule 4: Transfer Then Cash-Out (24h) | 0 | 0 | 0 | 8,213 | 0.00% | 0.00% | 0.0000% | **0.0000** | $0.00 | 0.00% |

---

## 2. Global Enterprise Matrix (FULL Dataset Universe)

Evaluation across all 6,362,620 transactions (including `CASH_IN`, `PAYMENT`, and `DEBIT` as automatically unflagged legitimate rows). Table sorted by **F1 Score descending**:

| Rule ID | Rule Name | Alerts | TP | FP | FN | Precision (%) | Recall (%) | FPR (%) | F1 Score | Flagged Value ($) | Share of Value (%) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `rule_emptied` | Rule 1: Account Emptied | 8,008 | 8,008 | 0 | 205 | 100.00% | 97.50% | 0.0000% | **0.9874** | $10,547,398,416.82 | 0.92% |
| `rule_dest_unchanged` | Rule 6: Destination Balance Unchanged | 4,042 | 3,940 | 102 | 4,273 | 97.48% | 47.97% | 0.0016% | **0.6430** | $6,078,483,439.62 | 0.53% |
| `rule_large_amount` | Rule 2: Large Amount Outlier | 24,818 | 1,806 | 23,012 | 6,407 | 7.28% | 21.99% | 0.3621% | **0.1094** | $67,410,813,776.79 | 5.89% |
| `is_rule_alert_2` | Composite Alert: Score >= 2 | 267,021 | 5,908 | 261,113 | 2,305 | 2.21% | 71.93% | 4.1092% | **0.0429** | $140,840,275,000.38 | 12.31% |
| `is_rule_alert_1` | Composite Alert: Score >= 1 | 1,085,554 | 8,190 | 1,077,364 | 23 | 0.75% | 99.72% | 16.9546% | **0.0150** | $407,883,157,529.56 | 35.64% |
| `rule_mule_dest` | Rule 5: Mule Destination (Day) | 748,575 | 647 | 747,928 | 7,566 | 0.09% | 7.88% | 11.7702% | **0.0017** | $273,322,873,217.94 | 23.88% |
| `rule_balance_error` | Rule 7: Balance Inconsistency | 570,732 | 26 | 570,706 | 8,187 | 0.00% | 0.32% | 8.9813% | **0.0001** | $199,218,661,068.58 | 17.41% |
| `rule_velocity` | Rule 3: Originator Velocity (6h) | 0 | 0 | 0 | 8,213 | 0.00% | 0.00% | 0.0000% | **0.0000** | $0.00 | 0.00% |
| `rule_transfer_then_cashout` | Rule 4: Transfer Then Cash-Out (24h) | 0 | 0 | 0 | 8,213 | 0.00% | 0.00% | 0.0000% | **0.0000** | $0.00 | 0.00% |

---

## 3. Mathematical & Empirical Spot-Check Verification

Verification confirms that metrics computed in Python match earlier SQL verification queries:

1. **Spot-Check 1 (`rule_emptied`):**
   - Flagged: **8,008** (Matches Verification Query 1: 8,008 rows)
   - TP: **8,008**, FP: **0**
   - Precision: **100.0000%** (Matches SQL: 100.0000%)
   - Recall: **97.5040%** (Matches SQL: 97.5040%)

2. **Spot-Check 2 (`rule_dest_unchanged`):**
   - Flagged: **4,042** (Matches Verification Query 6A: 4,042 rows)
   - TP: **3,940**, FP: **102**
   - Precision: **97.4765%** (Matches SQL: 97.4765%)
   - Recall: **47.9727%** (Matches SQL: 47.9727%)

3. **Universe Invariance:**
   - Because all 8,213 frauds belong strictly to `TRANSFER` and `CASH_OUT`, and rules are evaluated only on scoped rows, TP, FP, FN, Precision, Recall, and F1 are mathematically invariant between SCOPED and FULL universes.
   - FPR decreases by a factor of ~2.3 in the FULL universe because the non-fraud denominator expands from 2,762,196 to 6,354,407 ($TN_{full} = TN_{scoped} + 3,592,211$).

---

## 4. Analytical Conclusions & Operational Guidance

Generated directly from empirical evaluation:

1. **Strongest Individual Rule:**
   - **`Rule 1: Account Emptied` (`rule_emptied`)** is by far the single most effective rule, achieving an exceptional **F1 score of 0.9874**, a flawless **100.00% precision** (0 false positives), and **97.50% recall** (capturing 8,008 of 8,213 frauds). This directly mirrors the PaySim simulator's core synthetic generation mechanism where fraudsters drain the entirety of the victim's account balance in a single execution.
   - Secondary high-precision anchor: **`Rule 6: Destination Balance Unchanged`** achieves **97.48% precision** and **47.97% recall** ($F_1 = 0.6430$).

2. **Weakest Operational Rules:**
   - **`Rule 3: Originator Velocity (6h)`** and **`Rule 4: Transfer Then Cash-Out (24h)`** generate **0 alerts** on PaySim ($F_1 = 0.0000$). While multi-step originator velocity and rapid mule account turnarounds represent critical real-world anti-money-laundering controls, PaySim's synthetic agent simulator generates disposable victim accounts that are drained once and never reused, rendering originator velocity and destination-to-origin chaining inert on this specific dataset.
   - Among rules that actively trigger alerts, **`Rule 7: Balance Inconsistency` (`rule_balance_error`)** is the poorest discriminator ($F_1 = 0.0001$), triggering 570,732 alerts (20.60% of scope) while catching only 26 frauds, yielding a near-zero precision of 0.0046%.

3. **Composite Policy Comparison (Threshold $\ge 1$ vs $\ge 2$):**
   - **`is_rule_alert_1` (Alert Score $\ge 1$):** Maximizes safety coverage with **99.72% recall** (missing only 23 fraud cases out of 8,213), but creates an unsustainable alert volume of **1,085,554 transactions** (39.18% of scope) with a precision of just **0.75%**.
   - **`is_rule_alert_2` (Alert Score $\ge 2$):** **Best operational balance for compliance investigators.** It suppresses over 75% of the alert workload (267,021 alerts vs 1,085,554), triples precision to **2.21%**, and still captures **71.93% of all fraud** (5,908 frauds caught). For production transaction monitoring pipelines with fixed headcount, `is_rule_alert_2` is the recommended operating threshold.
