# PaySim Dataset Profiling Report

## 1. Executive Summary

- **Total Transactions:** 6,362,620
- **Total Columns:** 11
- **Memory Footprint:** 497.35 MB
- **Total Null Values:** 0
- **Total Fraudulent Transactions:** 8,213
- **Overall Fraud Rate:** 0.1291% (~0.129%)
- **Imbalance Ratio:** 773.70 : 1 (6,354,407 legit to 8,213 fraud)

## 2. Missing Value Analysis

| Column | Data Type | Null Count | Null % |
|---|---|---|---|
| `step` | `int16` | 0 | 0.00% |
| `type` | `category` | 0 | 0.00% |
| `amount` | `float64` | 0 | 0.00% |
| `nameOrig` | `string` | 0 | 0.00% |
| `oldbalanceOrg` | `float64` | 0 | 0.00% |
| `newbalanceOrig` | `float64` | 0 | 0.00% |
| `nameDest` | `string` | 0 | 0.00% |
| `oldbalanceDest` | `float64` | 0 | 0.00% |
| `newbalanceDest` | `float64` | 0 | 0.00% |
| `isFraud` | `int8` | 0 | 0.00% |
| `isFlaggedFraud` | `int8` | 0 | 0.00% |

**Total Nulls Across Dataset:** 0

## 3. Numeric Column Descriptive Statistics

| Column | Mean | Std | Min | 1% | 25% | Median (50%) | 75% | 99% | 99.9% | Max |
|---|---|---|---|---|---|---|---|---|---|---|
| `amount` | 179,861.90 | 603,858.23 | 0.00 | 449.47 | 13,389.57 | 74,871.94 | 208,721.48 | 1,615,979.47 | 8,956,797.68 | 92,445,516.64 |
| `oldbalanceOrg` | 833,883.10 | 2,888,242.67 | 0.00 | 0.00 | 0.00 | 14,208.00 | 107,315.18 | 16,027,256.13 | 26,825,930.20 | 59,585,040.37 |
| `newbalanceOrig` | 855,113.67 | 2,924,048.50 | 0.00 | 0.00 | 0.00 | 0.00 | 144,258.41 | 16,176,160.56 | 26,971,658.93 | 49,585,040.37 |
| `oldbalanceDest` | 1,100,701.67 | 3,399,180.11 | 0.00 | 0.00 | 0.00 | 132,705.66 | 943,036.71 | 12,371,819.15 | 34,392,786.79 | 356,015,889.35 |
| `newbalanceDest` | 1,224,996.40 | 3,674,128.94 | 0.00 | 0.00 | 0.00 | 214,661.44 | 1,111,909.25 | 13,137,866.94 | 39,531,571.97 | 356,179,278.92 |


## 4. Transaction Breakdown by Type

| Transaction Type | Count | Share (%) |
|---|---|---|
| **CASH_IN** | 1,399,284 | 21.99% |
| **CASH_OUT** | 2,237,500 | 35.17% |
| **DEBIT** | 41,432 | 0.65% |
| **PAYMENT** | 2,151,495 | 33.81% |
| **TRANSFER** | 532,909 | 8.38% |


## 5. Fraud Statistics by Transaction Type

| Transaction Type | Total Count | Fraud Count | Fraud Rate (%) | Mean Amount | Median Amount |
|---|---|---|---|---|---|
| **CASH_IN** | 1,399,284 | 0 | 0.0000% | 168,920.24 | 143,427.71 |
| **CASH_OUT** | 2,237,500 | 4,116 | 0.1840% | 176,273.96 | 147,072.18 |
| **DEBIT** | 41,432 | 0 | 0.0000% | 5,483.67 | 3,048.99 |
| **PAYMENT** | 2,151,495 | 0 | 0.0000% | 13,057.60 | 9,482.19 |
| **TRANSFER** | 532,909 | 4,097 | 0.7688% | 910,647.01 | 486,308.39 |

> **Key Verification:** Fraud cases occur exclusively in `TRANSFER` (4,097) and `CASH_OUT` (4,116). `CASH_IN`, `DEBIT`, and `PAYMENT` contain exactly 0 fraud occurrences.

## 6. Entity Cardinality & Merchant Analysis

- **Unique Originator Accounts (`nameOrig`):** 6,353,307 (99.8536% unique)
- **Unique Destination Accounts (`nameDest`):** 2,722,362
- **Merchant Destinations (Starting with 'M'):** 2,151,495 (33.81% of all transactions)
- **Note:** Merchant accounts have 0 initial and final destination balances by design in the PaySim simulator.

## 7. Temporal Distribution (Hourly Step to Daily Aggregations)

- **Simulation Step Range:** 1 to 743 (1 step = 1 hour, span of 31 days)

| Day | Total Transactions | Fraud Transactions | Fraud Rate (%) |
|---|---|---|---|
| Day 01 | 574,255 | 271 | 0.0472% |
| Day 02 | 455,238 | 309 | 0.0679% |
| Day 03 | 1,070 | 310 | 28.9720% |
| Day 04 | 28,240 | 262 | 0.9278% |
| Day 05 | 9,789 | 252 | 2.5743% |
| Day 06 | 441,005 | 228 | 0.0517% |
| Day 07 | 420,583 | 272 | 0.0647% |
| Day 08 | 449,637 | 278 | 0.0618% |
| Day 09 | 417,919 | 255 | 0.0610% |
| Day 10 | 392,945 | 282 | 0.0718% |
| Day 11 | 417,859 | 262 | 0.0627% |
| Day 12 | 349,776 | 298 | 0.0852% |
| Day 13 | 428,583 | 242 | 0.0565% |
| Day 14 | 397,876 | 246 | 0.0618% |
| Day 15 | 401,282 | 250 | 0.0623% |
| Day 16 | 375,594 | 252 | 0.0671% |
| Day 17 | 425,766 | 320 | 0.0752% |
| Day 18 | 20,999 | 268 | 1.2763% |
| Day 19 | 11,300 | 256 | 2.2655% |
| Day 20 | 19,727 | 236 | 1.1963% |
| Day 21 | 24,593 | 272 | 1.1060% |
| Day 22 | 53,437 | 256 | 0.4791% |
| Day 23 | 51,012 | 216 | 0.4234% |
| Day 24 | 32,709 | 280 | 0.8560% |
| Day 25 | 57,853 | 240 | 0.4148% |
| Day 26 | 13,885 | 272 | 1.9589% |
| Day 27 | 8,578 | 280 | 3.2642% |
| Day 28 | 14,661 | 248 | 1.6916% |
| Day 29 | 54,890 | 260 | 0.4737% |
| Day 30 | 11,287 | 268 | 2.3744% |
| Day 31 | 272 | 272 | 100.0000% |

