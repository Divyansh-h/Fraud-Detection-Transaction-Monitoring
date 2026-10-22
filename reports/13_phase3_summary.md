# Phase 3 Machine Learning Summary: Anomaly Detection Architecture & Evaluation

**Document ID:** `13_phase3_summary.md`  
**Execution Timestamp:** 2026-10-22 16:59:00 UTC  
**Model Family:** Unsupervised Isolation Forest (`sklearn.ensemble.IsolationForest`)  
**Scope of Application:** `TRANSFER` and `CASH_OUT` transactions only ($N = 2,770,409$)  
**Evaluation Principle:** Model selection and operating threshold calibration performed strictly on Validation ($N = 554,082$); Test set ($N = 554,082$) evaluated strictly once.

---

## 1. Final Model Architecture & Hyperparameter Configuration

The winning configuration was determined via systematic grid sweep over tree depth, sample density, and feature sets (documented in `10_if_sweep.csv`). Selection was guided by **Validation PR-AUC**, with training time serving as tie-breaker:

| Configuration Parameter | Value Selected | Design Justification |
| :--- | :--- | :--- |
| **Model Type** | `IsolationForest` | Unsupervised recursive partitioning suited for unlabeled anomaly vectors |
| **Number of Estimators (`n_estimators`)** | **100** | Optimal balance between variance stabilization and sub-second inference latency |
| **Subsample Size (`max_samples`)** | **1024** | Outperformed default 256; deeper subsample captures multi-attribute joint balance shifts |
| **Nominal Contamination (`contamination`)** | **0.003** | Calibrated to expected domain fraud prevalence (~0.30%) |
| **Feature Set** | **Set A** (13 features) | Delivered +40.09% PR-AUC improvement over rule-free baseline (Set B) |
| **Training Dataset Size** | **1,662,245 rows** | Trained on the FULL training partition without subsampling |
| **Training Duration** | **1.38 seconds** | High computational throughput suitable for high-frequency deployment |

---

## 2. Generalization Performance: Validation vs. Test Out-of-Sample

To strictly audit against test-set overfitting or leakage, the table below compares performance metrics across the **Validation** and **Test** sets at the selected operating threshold (`best_f1` = 0.704009):

| Evaluation Metric | Validation Set ($N = 554,082$) | Held-Out Test Set ($N = 554,082$) | Variance ($\Delta$) | Status |
| :--- | :---: | :---: | :---: | :---: |
| **Area Under PR Curve (PR-AUC)** | **0.7620** | **0.7565** | -0.0054 | Stable Generalization |
| **Area Under ROC Curve (ROC-AUC)** | **0.9960** | **0.9972** | +0.0013 | Exceptional Separation |
| **Precision (PPV)** | **98.45%** | **96.58%** | -1.87% | High Alert Fidelity |
| **Recall (Sensitivity)** | **50.40%** | **51.52%** | +1.12% | Consistent Capture |
| **False Positive Rate (FPR)** | **0.0024%** | **0.0054%** | +0.0030% | Near-Zero False Alarms |
| **F1 Score** | **0.6667** | **0.6720** | +0.0053 | Optimal Operating Balance |
| **Total Alerts Generated** | **841** | **876** | +35 | Operationally Manageable |
| **Alerts per 100,000 Transactions** | **151.8** | **158.1** | +6.3 | Scalable Workload |

> **Audit Observation:** Out-of-sample performance on the test set closely mirrors the validation set across all indicators. The model maintains **96.58% precision** and **51.52% recall** on unseen test data, verifying that decision boundaries are robust and free from tuning leakage.

---

## 3. Test Partition Operating Condition Comparison

Performance across all evaluated test operating conditions (exported to `reports/11_ml_test_results.csv`):

| Operating Condition | Decision Threshold | TP | FP | Precision | Recall | FPR | F1 Score | Alerts / 100k |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`best_f1` (Selected)** | **0.704009** | **846** | **30** | **96.58%** | **51.52%** | **0.0054%** | **0.6720** | **158.1** |
| `high_recall_p50` | 0.662667 | 1,064 | 456 | 70.00% | 64.80% | 0.0825% | 0.6730 | 274.3 |
| `default_contamination` | Model Default | 1,112 | 607 | 64.69% | 67.72% | 0.1099% | 0.6617 | 310.2 |
| `high_precision_r80` | 0.592857 | 1,568 | 7,807 | 16.73% | 95.49% | 1.4132% | 0.2847 | 1692.0 |

---

## 4. Production Artifacts Delivered

1. **`models/isolation_forest.joblib`**: Serialized production estimator (2.64 MB).
2. **`models/model_metadata.json`**: Complete lineage tracking scikit-learn version, seed, hyperparameters, and feature order.
3. **`data/outputs/ml_scores.parquet`**: Full scoped universe (2,770,409 transactions) scored with raw anomaly score, 0-100 normalized score, binary alert flag, and split identifier.
4. **`src/predict.py`**: Production inference function `score_dataframe(df)` verified by deterministic reproducibility testing.

---

## 5. Limitations

When interpreting these results and deploying this model into live transaction monitoring environments, the following five fundamental limitations must be explicitly recognized:

1. **Synthetic Nature of PaySim:**  
   PaySim is an agent-based simulation calibrated on aggregated mobile money logs from a single African financial service provider. While realistic in scale, synthetic data cannot replicate the full messiness, human behavioral quirks, seasonal shopping dynamics, or evolving adversarial evasion techniques seen in real-world retail banking networks.

2. **Extreme Predictive Power of Hand-Crafted Features (`origEmptied`):**  
   Features such as `origEmptied` and `destBalanceUnchanged` exhibit disproportionately strong predictive power in PaySim because the underlying simulation script encoded fraud primarily as complete balance depletion. In commercial banking, sophisticated money launderers and account takeover fraudsters deliberately leave residual balances or execute multi-stage micro-transfers to blend into legitimate consumer behavior. Real-world performance on these specific features would be noticeably lower.

3. **Unsupervised Isolation Forest vs. Supervised Models:**  
   Isolation Forest operates in a purely unsupervised capacity, identifying topological isolation depth rather than directly optimizing a labeled fraud objective. Consequently, it achieves a recall ceiling (~51-68% at acceptable precision), whereas supervised gradient boosted decision trees (such as LightGBM or XGBoost) trained on historical dispute labels typically achieve higher recall and sharper discrimination.

4. **Absence of Longitudinal Customer History:**  
   The dataset contains no persistent customer profiles, long-term historical velocity baselines, device fingerprints, IP reputations, or account tenure. Each transaction is judged strictly on instantaneous row-level accounting discrepancies, preventing the model from recognizing behavioral anomalies (e.g., a customer suddenly sending 10x their typical monthly volume).

5. **Operational Trade-Offs: Fraud Caught vs. Customer Friction:**  
   Calibrating decision thresholds involves an unavoidable business tension between financial crime loss mitigation and customer friction. While increasing recall to 95.5% (`high_precision_r80`) catches nearly all fraud, it inflates alert volumes from **158 to 1,692 alerts per 100,000 transactions**, causing overwhelming alert queues for human compliance investigators and inadvertently freezing legitimate customer transactions.
