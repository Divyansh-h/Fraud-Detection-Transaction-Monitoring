# Phase 1: Data Profiling, Validation & Cleaning Executive Summary

## Core Findings & Analytical Highlights

1. **Total Transaction Volume:** Processed **6,362,620** transactions with **0 nulls** and **0 duplicate rows**, maintaining full structural integrity across 31 simulation days.

2. **Extreme Class Imbalance:** Exactly **8,213** fraudulent transactions exist, establishing a baseline fraud rate of **0.1291%** (~0.129%) and an imbalance ratio of **773.70 : 1** (legitimate to fraudulent).

3. **Strict Channel Isolation:** Fraud occurs exclusively in two transaction channels: **TRANSFER** (4,097 fraud cases, 0.7688% fraud rate) and **CASH_OUT** (4,116 fraud cases, 0.1840% fraud rate). In contrast, `CASH_IN`, `DEBIT`, and `PAYMENT` contain **exactly 0** fraud cases across 3,592,211 transactions.

4. **Machine Learning Scoping:** Focusing detection models strictly on `TRANSFER` and `CASH_OUT` isolates **2,770,409** transactions (43.54% of dataset) while capturing **100.00% (8,213)** of all fraud events, lifting within-scope fraud density to **0.2965%**.

5. **Account Drainage Feature (`origEmptied`):** **97.50%** of all fraud transactions (8,008 / 8,213) involve completely draining the sender's account (`oldbalanceOrg > 0 & newbalanceOrig == 0 & amount == oldbalanceOrg`), compared to **0** occurrences in legitimate transactions (0.00% false positive rate).

6. **Originator Balance Consistency Inversion:** **79.91%** of legitimate transactions fail the mathematical balance check (`errOrig > 0.01`) due to simulation balance capping at zero, whereas only **0.55%** of fraud transactions are inconsistent because fraudsters systematically drain the exact available balance.

7. **Recipient Balance Anomaly in Transfers:** **99.29%** of fraudulent `TRANSFER` transactions leave the recipient balance unchanged at zero despite significant funds sent, compared to only **0.02%** in legitimate transfers.

8. **Simulator Rule Weakness (`isFlaggedFraud`):** The simulator's internal heuristic flags only **16** transactions (all `TRANSFER` >= $353,874.22), capturing just **0.19%** of all fraud cases and missing **99.81%** (8,197 fraud cases); it must never be used as a model feature.

9. **Outlier Retention Policy:** Amounts are heavily right-skewed (+30.99 skewness). Conventional IQR trimming would eliminate **33.00%** of all fraud cases in `TRANSFER` and `CASH_OUT` (2,710 cases); therefore, **zero outliers were dropped**, and outlier indicators were preserved as model features.

10. **Entity Topology & Stratified Partitioning:** Evaluated **6,353,307** distinct originators and **2,722,362** destinations (with 2,151,495 merchant destinations). Generated a leak-free 60/20/20 stratified split (`split_assignment.parquet`) where fraud proportions across train, validation, and test partitions differ by less than **0.0002 percentage points**.

## Generated Deliverables

- **Clean Master Parquet:** `/Users/divyansh/code/Development/DataScience/Fraud Detection & Transaction Monitoring/data/processed/transactions_clean.parquet` (353.91 MB, 6,362,620 rows, 24 columns)
- **Stratified Split Assignment:** `/Users/divyansh/code/Development/DataScience/Fraud Detection & Transaction Monitoring/data/processed/split_assignment.parquet` (2,770,409 rows, 0 duplicate IDs)
- **Profiling & Audit Reports:** `reports/01_profile.md`, `reports/02_duplicates_and_ids.md`, `reports/03_balance_consistency.md`, `reports/04_validity.md`, `reports/05_outliers.md`, `reports/06_imbalance_strategy.md`, `reports/07_phase1_summary.md`
- **Visualizations Generated:** 8 publication-grade charts saved in `reports/figures/`
