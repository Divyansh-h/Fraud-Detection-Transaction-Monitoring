# Duplicates and Entity ID Integrity Report

## 1. Full-Row Duplicates (Exact 11-Column Match)

- **Total Rows:** 6,362,620
- **Exact Duplicate Rows:** 0
- **Duplicate Share:** 0.000000%

> **Recommendation:** 0 full-row duplicates were identified. The raw dataset contains no redundant transaction rows; no deduplication is needed.

## 2. Repeated Originator Analysis (`nameOrig`)

In financial systems, repeated `nameOrig` accounts represent authentic customer activity rather than data duplication. A single customer often conducts multiple transactions over a 30-day monitoring window (e.g., routine payments, recurring transfers, cash withdrawals).

- **Accounts with > 1 Transaction:** 9,298
- **Maximum Transactions by a Single Account:** 3

### Top 10 Most Frequent Originator Accounts

| Rank | Originator Account (`nameOrig`) | Transaction Count |
|---|---|---|
| 1 | `C2098525306` | 3 |
| 2 | `C400299098` | 3 |
| 3 | `C1999539787` | 3 |
| 4 | `C1065307291` | 3 |
| 5 | `C545315117` | 3 |
| 6 | `C1976208114` | 3 |
| 7 | `C1784010646` | 3 |
| 8 | `C1530544995` | 3 |
| 9 | `C1902386530` | 3 |
| 10 | `C1677795071` | 3 |


## 3. Originator ID Prefix Verification (`nameOrig`)

| Prefix Type | Account Type | Count | Share (%) |
|---|---|---|---|
| `C` | Customer Account | 6,362,620 | 100.0000% |
| `M` | Merchant Account | 0 | 0.0000% |

> **Finding:** 100% of originator IDs begin with `'C'`. No merchants initiate transactions as originators in this dataset.

## 4. Destination ID Prefix & Merchant Routing (`nameDest`)

| Prefix Type | Entity Type | Count | Share (%) |
|---|---|---|---|
| `C` | Customer Destination | 4,211,125 | 66.1854% |
| `M` | Merchant Destination | 2,151,495 | 33.8146% |


- **Transaction Types Directed to Merchants (`M`):** `PAYMENT`
- **Verification:** Merchant destinations receive strictly `PAYMENT` transactions (100% alignment). No `TRANSFER`, `CASH_OUT`, `CASH_IN`, or `DEBIT` transactions are routed to merchant entities.

## 5. Temporal Step Ordering

- **Is File Monotonically Sorted by `step` Ascending?:** **True**
- **Verification:** Transactions are chronologically ordered from step 1 through step 743, ensuring that historical features and cumulative metrics can be computed without global resorting.

## 6. Fraud Entity Analysis (`isFraud == 1`)

- **Total Fraud Records:** 8,213
- **Distinct Originators in Fraud:** 8,213
- **Distinct Destinations in Fraud:** 8,169
- **Originators Appearing in > 1 Fraud Event:** 0
- **Destinations Appearing in > 1 Fraud Event:** 44

### Key Fraud Topology Insights

1. **One-Time Drained Victims:** Every single fraudulent transaction originates from a unique `nameOrig` (`8,213` distinct victim accounts). Attackers compromise and completely drain victim accounts in a single pass without reusing the same originator for secondary fraud.

2. **Destination Re-Use:** While originators are never reused for fraud, `44` destination accounts receive exactly `2` fraudulent transactions each (`88` fraud events channeled through repeated mule/drop accounts).

| Top Re-used Fraud Destination (`nameDest`) | Fraud Inflow Count |
|---|---|
| `C410033330` | 2 |
| `C803116137` | 2 |
| `C904300960` | 2 |
| `C1013511446` | 2 |
| `C2020337583` | 2 |

