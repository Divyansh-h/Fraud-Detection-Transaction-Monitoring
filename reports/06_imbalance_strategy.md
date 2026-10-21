# Class Imbalance and Data Splitting Strategy Report

## 1. Modeling Scope Definition

Machine learning and detection algorithms are strictly confined to transaction types where fraud exists:
- **In-Scope Types:** `TRANSFER` and `CASH_OUT`
- **In-Scope Transactions:** 2,770,409 (43.54% of the total dataset)
- **In-Scope Fraud Cases:** 8,213 (100.00% of all fraud in the dataset)
- **In-Scope Fraud Prevalence:** **0.2965%** (~0.30%)

> **Architectural Justification:** In previous profiling, `CASH_IN`, `DEBIT`, and `PAYMENT` showed **exactly 0** fraud cases across 3,592,211 rows. Training models on 0% fraud types introduces unnecessary computational overhead and distorts decision boundaries. These non-scoped transactions remain fully available for portfolio-level analytics and executive dashboard totals, while ML models focus on fraud-active channels.

## 2. Stratified Data Split

To prevent data leakage while preserving class distribution across train, validation, and test partitions, stratified sampling was applied on `isFraud` with `random_state=42`:

| Split | Rows | % of Scope | Fraud Rows | Fraud Rate (%) |
|---|---|---|---|---|
| **train** | 1,662,245 | 60.0% | 4,928 | 0.2965% |
| **val** | 554,082 | 20.0% | 1,643 | 0.2965% |
| **test** | 554,082 | 20.0% | 1,642 | 0.2963% |

- **Stratification Quality:** Maximum difference in fraud rate across splits is **0.000180 percentage points**, well within the 0.02 percentage point tolerance.

## 3. Why Accuracy is a Misleading Metric

In highly imbalanced datasets, raw classification accuracy is fundamentally deceptive. A trivial dummy model that predicts "no fraud" for every transaction achieves:
- **99.87% accuracy** on the full dataset (99.8709%)
- **99.70% accuracy** on the scoped dataset (99.7035%)

Such a model catches 0 fraud events (0% recall) yet appears virtually flawless under accuracy. Consequently, **accuracy is strictly banned as an evaluation metric** in this project.

## 4. Imbalance-Aware Evaluation Metrics

All rule-based and machine-learning models will be evaluated strictly using:
1. **Precision (Positive Predictive Value):** Avoid wasting compliance officer time on false alerts.
2. **Recall (Sensitivity / Detection Rate):** Maximize recovery of fraudulent funds.
3. **False Positive Rate (FPR):** Monitor operational impact on legitimate customers.
4. **F1-Score / PR-AUC (Precision-Recall Area Under Curve):** Benchmark overall detection tradeoff without distortion from majority negatives.

## 5. Handling Imbalance Without Synthetic Oversampling (No SMOTE)

- **No SMOTE or Synthetic Oversampling:** SMOTE synthesizes artificial minority points via nearest neighbors, which distorts boundary distributions and risks generating unrealistic financial account states. Furthermore, unsupervised anomaly detectors like **Isolation Forest** learn density topology on uncontaminated empirical distributions.

## 6. Single Source of Truth for Identifiers (`txn_id`)

- **Identifier (`txn_id`):** Defined as the 0-based original row position in the raw CSV (`int32`).
- **Artifact Generated:** `split_assignment.parquet` containing exactly `3` partitions across `2,770,409` transactions with **0 duplicate IDs**.
