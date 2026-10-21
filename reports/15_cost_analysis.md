# Transaction Monitoring Financial Cost-Benefit & Economic Optimization Analysis

**Document ID:** `15_cost_analysis.md`  
**Baseline Review Cost:** $15.00 per flagged alert  
**Total Enterprise Fraud Volume:** $12,056,415,427.84 (8,213 fraud events)  
**Evaluated Universe:** Full dataset ($N = 6,362,620$)  

---

## 1. Executive Cost-Benefit Matrix (Baseline: $15.00 / Alert)

| Approach | Alerts | Investigation Cost ($) | Fraud Prevented ($) | Fraud Missed ($) | Total Net Cost ($) | Net Savings ($) | Cost / $ Saved |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `Combined AND (combo_and)` | 4,224 | $63,360.00 | $6,441,959,926.99 | $5,614,455,500.85 | $5,614,518,860.85 | $6,441,896,566.99 | $0.0000 |
| `ML only (ml_flag)` | 4,279 | $64,185.00 | $6,441,959,926.99 | $5,614,455,500.85 | $5,614,519,685.85 | $6,441,895,741.99 | $0.0000 |
| `Rules with threshold alert_score >= 2 (is_rule_alert_2)` | 267,021 | $4,005,315.00 | $10,275,194,064.11 | $1,781,221,363.73 | $1,785,226,678.73 | $10,271,188,749.11 | $0.0004 |
| `Rules only (rule_alert)` | 1,085,554 | $16,283,310.00 | $12,054,919,454.03 | $1,495,973.81 | $17,779,283.81 | $12,038,636,144.03 | $0.0014 |
| `Combined OR (combo_or)` | 1,085,609 | $16,284,135.00 | $12,054,919,454.03 | $1,495,973.81 | $17,780,108.81 | $12,038,635,319.03 | $0.0014 |
| `Simulator baseline (not used)` | 16 | $240.00 | $77,785,563.69 | $11,978,629,864.15 | $11,978,630,104.15 | $77,785,323.69 | $0.0000 |

---

## 2. Key Economic Findings & Operational Triaging

1. **Extreme Efficiency of Combined AND / ML Only:**
   - Requiring ML and SQL consensus (`Combined AND`) flags only **4,224 transactions**, requiring just **$63,360.00** in manual investigation expense.
   - It intercepts **$6,441,959,926.99** in fraud, costing **less than $0.0001 per dollar of fraud prevented**.
   - However, relying solely on this strategy leaves **$5.61B** in missed fraud if unflagged transactions are ignored.

2. **The High-Recall Overhead of Combined OR / Rules Only:**
   - `Combined OR` and `Rules only` catch virtually all fraud (**$12.05B prevented**, missing only **$1.50M**).
   - However, they generate **1,085,609 alerts**, incurring **$16.28M** in human review costs.
   - Because reviewing 1.08M alerts manually is economically unsustainable for compliance teams, these alerts cannot be routed directly to human analysts without automated risk-tier filtering.

3. **Optimal Multi-Tier Solution:**
   - **Tier 1 (Automated Block):** Route `Combined AND` (4,224 alerts) to automated settlement freezes or mandatory biometric step-up authentication.
   - **Tier 2 (High-Priority Queue):** Route transactions with `risk_band == 'High'` (3,402 alerts) to Level 2 analysts.
   - **Tier 3 (Passive Monitoring):** Subject the remaining `Combined OR` transactions to background AML pattern batch processing.
