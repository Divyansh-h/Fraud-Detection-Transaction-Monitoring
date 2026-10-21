# Logical Validity and Simulation Anomaly Report

## 1. Overview

This report examines logical domain constraints, simulation quirks, and accounting validity across all 6,362,620 transactions. 
**Standing Rule Compliance:** No rows were removed or altered during this analysis. All quirks are documented for model feature engineering.

## 2. Logical Validity Check Results

| Check Name | Count | % of Rows | Count in Fraud | Analytical Finding & Quirk Explanation |
|---|---|---|---|---|
| **1. Negative amounts or balances in any column** | 0 | 0.0000% | 0 | No negative monetary amounts or balances exist; dataset respects non-negative domain rules. |
| **2. Transactions with amount == 0** | 16 | 0.0003% | 16 | Exactly 16 zero-amount rows exist, and 100% are fraudulent CASH_OUT attempts on drained accounts. |
| **3. Sender oldbalanceOrg == 0 while amount > 0** | 2,102,433 | 33.0435% | 25 | Over 2.1M transactions have zero sender balance; frequent in legitimate cash-ins/payments, rare in fraud (25 cases). |
| **4. Overdraft: newbalanceOrig < 0 or amount > oldbalanceOrg** | 4,079,080 | 64.1101% | 29 | Simulator clamps newbalanceOrig at 0 without negative balances; 64.1% of transactions show amount > old balance, but only 29 frauds exhibit this. |
| **5. Receiver old & new balance both 0 (non-merchant, amount > 0)** | 165,781 | 2.6055% | 4,070 | Recipient balances remain 0.0 despite funds sent; strong fraud indicator (captures 4,070 fraud cases, 49.56% of total fraud). |
| **6. TRANSFER or CASH_OUT with amount > oldbalanceOrg** | 2,488,634 | 39.1134% | 29 | Common in legitimate activity (39.1%) due to missing initial balances; rare in fraud (only 29 fraud cases) where exact balance is drained. |
| **7. Simulator rule flag: isFlaggedFraud == 1** | 16 | 0.0003% | 16 | Extremely weak heuristic: fires on only 16 rows (100% precision, but 0.19% recall; misses 99.81% of fraud); only triggers on TRANSFER >= $353,874.22. |
| **8. Fraud in CASH_IN, DEBIT, or PAYMENT (expected 0)** | 0 | 0.0000% | 0 | Zero fraud instances exist in CASH_IN, DEBIT, or PAYMENT; confirms fraud is strictly confined to TRANSFER and CASH_OUT. |


## 3. Deep-Dive: Check 4 (Overdraft by Transaction Type)

The PaySim simulator does not permit negative balances; instead, whenever `amount > oldbalanceOrg`, `newbalanceOrig` is clamped at `0.0`.

| Transaction Type | Total Transactions | Overdraft Count | Overdraft Rate (%) | Overdraft in Fraud |
|---|---|---|---|---|
| **CASH_IN** | 1,399,284 | 477,536 | 34.13% | 0 |
| **CASH_OUT** | 2,237,500 | 1,981,122 | 88.54% | 24 |
| **DEBIT** | 41,432 | 11,786 | 28.45% | 0 |
| **PAYMENT** | 2,151,495 | 1,101,124 | 51.18% | 0 |
| **TRANSFER** | 532,909 | 507,512 | 95.23% | 5 |


## 4. Deep-Dive: Check 7 (`isFlaggedFraud` Weakness Analysis)

- **Total Flagged Rows:** 16
- **Flagged Rows that are Actually Fraud:** 16 (100.00% precision)
- **Total Actual Fraud in Dataset:** 8,213
- **Empirical Recall of Rule:** **0.19%** (Misses 8,197 frauds or 99.81%)
- **Minimum Transaction Amount Among Flagged Rows:** **$353,874.22**
- **Transaction Types Flagged:** Exclusively `TRANSFER`

### Crucial Architectural Decision:
> `isFlaggedFraud` represents a naive static rule baked into the PaySim simulator (flagging single transfer attempts > $200,000 under specific circumstances). Because it has near-zero recall (0.19%) and introduces severe target leakage / simulator bias, **it must NEVER be used as a model feature, nor as a benchmark for production detection systems**.
