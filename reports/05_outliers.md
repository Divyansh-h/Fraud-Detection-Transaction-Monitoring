# Outlier and Skewness Analysis Report

## 1. Executive Summary & Outlier Policy

> **Core Analytical Finding:** **"removing outliers would remove 33.00% of fraud, so outliers are kept"**.

In conventional tabular workflows, extreme numerical values above Q3 + 1.5*IQR are routinely trimmed or imputed. In transaction monitoring and financial fraud detection, however, **fraud IS the outlier**. Dropping outliers would discard roughly one-third of the target positive class, fundamentally crippling detection models.

## 2. Amount Distribution Skewness & Percentile Profile

| Scope | Skewness (Raw) | Kurtosis (Raw) | Skewness (log1p) | 50% (Median) | 90% | 95% | 99% | 99.9% |
|---|---|---|---|---|---|---|---|---|
| **Overall Dataset** | 30.99 | 1797.96 | -0.5550 | $74,871.94 | $365,423.31 | $518,634.20 | $1,615,979.47 | $8,956,797.68 |
| **TRANSFER** | 10.98 | 207.77 | -0.7104 | $486,308.39 | $1,782,296.64 | $2,674,586.94 | $10,000,000.00 | $24,840,512.47 |
| **CASH_OUT** | 19.94 | 957.89 | -1.5228 | $147,072.18 | $355,191.98 | $427,877.16 | $579,654.07 | $864,676.45 |

- **Log1p Normalisation Effect:** Applying `np.log1p` contracts the raw skewness from **+30.99** down to **-0.56**, producing a well-behaved distribution suitable for linear models and neural networks.

## 3. IQR Outlier Thresholds & Target Class Overlap

| Metric | TRANSFER | CASH_OUT | Combined (TRANSFER & CASH_OUT) |
|---|---|---|---|
| **Q1 (25th Percentile)** | $215,905.35 | $72,669.65 | - |
| **Q3 (75th Percentile)** | $974,958.00 | $246,539.48 | - |
| **IQR** | $759,052.65 | $173,869.83 | - |
| **Outlier Threshold (Q3 + 1.5*IQR)** | **$2,113,536.98** | **$507,344.22** | - |
| **Total Outlier Rows** | 39,793 (7.47%) | 49,220 (2.20%) | 89,013 |
| **Fraud Cases in Outliers** | 803 | 1,907 | **2,710** |
| **Share of Outliers that are Fraud** | 2.02% | 3.87% | 3.04% |
| **Share of Fraud Caught in Outliers** | **19.60%** | **46.33%** | **33.00%** |


## 4. Visualizations

1. **Histogram of log1p(Amount) by Fraud vs Legitimate:** `/Users/divyansh/code/Development/DataScience/Fraud Detection & Transaction Monitoring/reports/figures/01_amount_distribution_by_fraud.png`

2. **Boxplot of log1p(Amount) by Transaction Type:** `/Users/divyansh/code/Development/DataScience/Fraud Detection & Transaction Monitoring/reports/figures/02_amount_boxplot_by_type.png`

3. **Bar Chart of Fraud Rate (%) by Transaction Type:** `/Users/divyansh/code/Development/DataScience/Fraud Detection & Transaction Monitoring/reports/figures/03_fraud_rate_by_type.png`

## 5. Feature Engineering Actions

- Added `isAmountOutlierIQR` (`int8`): Per-type IQR outlier flag.
- Added `isTop1PctAmount` (`int8`): Indicator for transactions at or above the 99th percentile within each type.
- **Zero rows were removed.** Both flags will serve as informative features for tree-based models and rule engines.
