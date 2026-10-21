# Balance Consistency and Anomaly Feature Report

## 1. Feature Definitions & Arithmetic Rules

- **`errOrig`**: `oldbalanceOrg - amount - newbalanceOrig`. Mathematical balance error on originator side.
- **`errDest`**: `oldbalanceDest + amount - newbalanceDest`. Mathematical balance error on recipient side.
- **`origInconsistent`**: `abs(errOrig) > 0.01` (`int8`). Sender-side accounting mismatch.
- **`destInconsistent`**: `abs(errDest) > 0.01` (`int8`). Receiver-side accounting mismatch. Explicitly forced to `0` for merchant destinations (`nameDest` starting with 'M') because merchant balances are unrecorded by simulator design.
- **`origEmptied`**: `(oldbalanceOrg > 0) & (newbalanceOrig == 0) & (amount == oldbalanceOrg)` (`int8`). Total balance drainage.
- **`destBalanceUnchanged`**: `(oldbalanceDest == newbalanceDest) & (amount > 0)` (`int8`). Zero destination credit anomaly.

## 2. Consistency Metrics by Transaction Type

| Transaction Type | Total Transactions | `origInconsistent` (%) | `destInconsistent` (%) | `origEmptied` (%) | `destBalanceUnchanged` (%) |
|---|---|---|---|---|---|
| **CASH_IN** | 1,399,284 | 100.00% | 100.00% | 0.0000% | 11.43% |
| **CASH_OUT** | 2,237,500 | 89.00% | 22.68% | 0.1821% | 0.07% |
| **DEBIT** | 41,432 | 30.08% | 23.25% | 0.0000% | 0.00% |
| **PAYMENT** | 2,151,495 | 54.19% | 0.00% | 0.0000% | 100.00% |
| **TRANSFER** | 532,909 | 95.47% | 22.67% | 0.7380% | 0.78% |

> **Note:** For `PAYMENT` transactions, `destInconsistent` is exactly 0.00% because 100% of payment destinations are merchants where destination error checks are not meaningful.

## 3. Consistency Metrics: Fraud vs Non-Fraud

| Class | Total Records | `origInconsistent` (%) | `destInconsistent` (%) | `origEmptied` (%) | `destBalanceUnchanged` (%) |
|---|---|---|---|---|---|
| **Legitimate (0)** | 6,354,407 | 79.91% | 31.99% | 0.0000% | 36.40% |
| **Fraud (1)** | 8,213 | 0.55% | 56.50% | 97.5040% | 49.56% |


## 4. Deep-Dive: Fraud vs Non-Fraud within TRANSFER and CASH_OUT

| Transaction Type | Fraud? | Transaction Count | `origInconsistent` (%) | `destInconsistent` (%) | `origEmptied` (%) | `destBalanceUnchanged` (%) |
|---|---|---|---|---|---|---|
| **CASH_OUT** | Legitimate (0) | 2,233,384 | 89.16% | 22.70% | 0.00% | 0.07% |
| **CASH_OUT** | Fraud (1) | 4,116 | 0.58% | 13.24% | 99.00% | 0.05% |
| **TRANSFER** | Legitimate (0) | 528,812 | 96.21% | 22.07% | 0.00% | 0.02% |
| **TRANSFER** | Fraud (1) | 4,097 | 0.51% | 99.95% | 96.00% | 99.29% |


## 5. Feature Separability Takeaway

> **Key Finding:** origEmptied separates fraud best overall by identifying 97.50% of all fraud cases with 0.00% legitimate false positives, while destBalanceUnchanged provides an extraordinarily stark signal for TRANSFER fraud (99.29% in fraud transfers vs 0.02% in legitimate transfers).
