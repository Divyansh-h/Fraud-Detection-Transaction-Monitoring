# Machine Learning Diagnostics & Anomaly Score Distribution Analysis

**Document ID:** `12_ml_diagnostics.md`  
**Scoped Transactions Analyzed:** 2,770,409  
**Total Alerted Transactions (`ml_flag=1`):** 4,279 (0.1545%)  

---

## 1. Normalized Anomaly Score Percentile Distribution (0 - 100 Scale)

Normalized anomaly scores (`anomaly_score_pct`) are calibrated against the training set bounds ($[0.0, 100.0]$):

- **50th Percentile (Median):** 11.77
- **90th Percentile:** 35.05
- **99th Percentile:** 58.07
- **99.9th Percentile:** 92.05
- **Max Score:** 100.00

---

## 2. Partition-Level Triage Distribution

| Partition Split | Total Scoped Rows | ML Flagged Alerts | Alert Rate | Mean Anomaly Score |
| :--- | :---: | :---: | :---: | :---: |
| **Train (60%)** | 1,662,245 | 2,540 | 0.1528% | 15.60 |
| **Validation (20%)** | 554,082 | 863 | 0.1558% | 15.61 |
| **Test (20%)** | 554,082 | 876 | 0.1581% | 15.64 |
| **Total Scoped** | **2,770,409** | **4,279** | **0.1545%** | **15.61** |
