# Machine Learning Data Preparation & Modeling Architecture Notes

**Document ID:** `09_ml_data_notes.md`  
**Modeling Scope:** `TRANSFER` and `CASH_OUT` transactions only ($N = 2,770,409$)  
**Total Target Fraud Events:** 8,213  
**Master Input Source:** `transactions_clean.parquet`  
**Split Assignment Source:** `split_assignment.parquet`  

---

## 1. Partition Distribution & Stratification Audit

The scoped dataset is partitioned into three disjoint sets using row-index stratified splitting (`random_state=42`) on `isFraud`:

| Split Partition | File Artifact | Row Count | Share of Scope | Fraud Count | Fraud Rate |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Train (60%)** | `ml_train.parquet` | 1,662,245 | 60.00% | 4,928 | 0.2965% |
| **Validation (20%)** | `ml_val.parquet` | 554,082 | 20.00% | 1,643 | 0.2965% |
| **Test (20%)** | `ml_test.parquet` | 554,082 | 20.00% | 1,642 | 0.2963% |
| **Total Scope** | **Combined** | **2,770,409** | **100.00%** | **8,213** | **0.2965%** |

---

## 2. Feature Schema & Column Layout

Each partitioned dataset (`ml_train.parquet`, `ml_val.parquet`, `ml_test.parquet`) contains exactly **15 columns**:
1. `txn_id` (`int32`): Global unique transaction identifier (row position in raw dataset).
2. `logAmt` (`float64`): `log1p(amount)`.
3. `isTransfer` (`int8`): Binary indicator (1 for `TRANSFER`, 0 for `CASH_OUT`).
4. `logOldOrg` (`float64`): `log1p(oldbalanceOrg)`.
5. `logNewOrig` (`float64`): `log1p(newbalanceOrig)`.
6. `logOldDest` (`float64`): `log1p(oldbalanceDest)`.
7. `logNewDest` (`float64`): `log1p(newbalanceDest)`.
8. `errOrig_signed` (`float64`): Signed log-magnitude origin accounting discrepancy.
9. `errDest_signed` (`float64`): Signed log-magnitude destination accounting discrepancy.
10. `origEmptied` (`int8`): Balance drained to zero indicator.
11. `destBalanceUnchanged` (`int8`): Destination balance unchanged indicator.
12. `destIsMerchant` (`int8`): Destination merchant indicator.
13. `amtToBalanceRatio` (`float64`): Transaction amount to origin balance ratio (clipped to $[0.0, 1.5]$).
14. `hour` (`int8`): Cyclical time feature ($0 \dots 23$).
15. `isFraud` (`int8`): Ground truth target label (evaluation only).

---

## 3. Modeling Philosophy: Unsupervised Isolation Forest

1. **Unsupervised Training on Train Features Only:**
   - The Isolation Forest anomaly detector is trained **strictly on the feature matrix of `ml_train.parquet` without labels** (`isFraud` is completely withheld during `model.fit()`).
   - In production financial crime systems, newly emerging attack vectors and zero-day fraud rings operate without historical ground-truth annotations. The model learns the multi-dimensional geometric topology of legitimate banking behavior purely through recursive tree isolation depth.

2. **Validation Set for Evaluation and Threshold Calibration:**
   - Ground truth labels (`isFraud`) are introduced **only during validation on `ml_val.parquet`**.
   - Hyperparameter search (number of estimators, max samples) and anomaly score threshold tuning (decision boundary / contamination percentile) are performed **strictly against the Validation set**.

3. **Strict No-Test-Tuning Rule:**
   - **The Test dataset (`ml_test.parquet`) is held out in an isolated evaluation vault and is NEVER used for tuning, contamination calibration, feature selection, or iterative threshold adjustments.**
   - The test set is evaluated exactly once at the conclusion of model selection to provide an uncompromised, unbiased measurement of out-of-sample generalization performance on unseen production data.

---

## 4. Partition Integrity & Leakage Guarantees

- **Disjoint Identifiers:** Pairwise intersection checks confirm that no transaction identifier (`txn_id`) appears in more than one partition:
  $$\text{Train} \cap \text{Val} = \emptyset, \quad \text{Train} \cap \text{Test} = \emptyset, \quad \text{Val} \cap \text{Test} = \emptyset$$
- **Identifier & Target Leakage Prevention:** High-cardinality identity strings (`nameOrig`, `nameDest`), simulation timestamps (`step`, `day`), and synthetic reference flags (`isFlaggedFraud`) are strictly excluded from all training feature vectors.
