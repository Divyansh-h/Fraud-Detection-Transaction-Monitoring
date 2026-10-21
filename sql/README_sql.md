# SQL Transaction Monitoring Architecture & Execution Guide

**Directory:** `sql/`  
**Database Engine:** DuckDB (`data/processed/fraud.duckdb`)  
**Data Universe:** 6,362,620 total transactions; 2,770,409 scoped transactions (`TRANSFER`, `CASH_OUT`)  

---

## 1. SQL File Directory & Script Catalog

| Script File | Purpose | Key Artifacts Created |
| :--- | :--- | :--- |
| [`01_load.sql`](file:///Users/divyansh/code/Development/DataScience/Fraud%20Detection%20&%20Transaction%20Monitoring/sql/01_load.sql) | Loads cleaned Parquet data directly into DuckDB using native columnar vectorization. | Table: `transactions` (6,362,620 rows, 24 columns) |
| [`00_verify.sql`](file:///Users/divyansh/code/Development/DataScience/Fraud%20Detection%20&%20Transaction%20Monitoring/sql/00_verify.sql) | Sanity-checks loaded table integrity: row counts, fraud totals, type distribution, step boundaries, and primary key uniqueness. | Diagnostic result tables |
| [`02_rules.sql`](file:///Users/divyansh/code/Development/DataScience/Fraud%20Detection%20&%20Transaction%20Monitoring/sql/02_rules.sql) | Core transaction monitoring heuristic rule engine and multi-rule alert aggregation engine. | View: `base_scope`<br>Views: `rule1_emptied` through `rule7_balance_error`<br>Table: `rule_flags` |

---

## 2. Recommended Execution Sequence

Run the scripts in the following order using `src/run_sql.py` or the Phase 2 orchestrator `src/run_phase2.py`:

```bash
# Step 1: Ingest clean Parquet master table into DuckDB
python src/run_sql.py sql/01_load.sql

# Step 2: (Optional verification) Audit database table integrity
python src/run_sql.py sql/00_verify.sql

# Step 3: Execute full transaction monitoring rule engine
python src/run_sql.py sql/02_rules.sql
```

---

## 3. Rule Architecture Overview (`02_rules.sql`)

All heuristic rules evaluate within the `base_scope` view (`TRANSFER` and `CASH_OUT` only):
1. **Rule 1 (`rule1_emptied`):** Flags transactions where sender balance is drained to zero (`oldbalanceOrg > 0 AND newbalanceOrig = 0 AND ABS(amount - oldbalanceOrg) < 0.01`).
2. **Rule 2 (`rule2_large_amount`):** Flags transactions in the top 1% by amount within each transaction type (`PERCENT_RANK() >= 0.99`).
3. **Rule 3 (`rule3_velocity`):** Flags senders conducting $\ge 3$ transactions in a rolling 6-hour window (`COUNT(*) OVER (PARTITION BY nameOrig ORDER BY step RANGE BETWEEN 5 PRECEDING AND CURRENT ROW) >= 3`).
4. **Rule 4 (`rule4_transfer_then_cashout`):** Flags accounts receiving a transfer and subsequent cash-out within 24 hours with $\pm 10\%$ amount matching.
5. **Rule 5 (`rule5_mule_dest`):** Flags non-merchant destination accounts receiving funds from $\ge 3$ distinct senders in the same calendar day.
6. **Rule 6 (`rule6_dest_unchanged`):** Flags transfers $\ge \$10,000$ where destination balance is unchanged (`oldbalanceDest = newbalanceDest`).
7. **Rule 7 (`rule7_balance_error`):** Flags simultaneous origin and destination book-balance errors (`ABS(errOrig) > 0.01 AND ABS(errDest) > 0.01`).
8. **Consolidated Table (`rule_flags`):** Multi-rule join table storing individual flags, `alert_score` (sum of 7 rule flags), and tiered alert flags (`is_rule_alert_1`, `is_rule_alert_2`).

---

## 4. Porting to PostgreSQL

DuckDB SQL syntax in this repository is ANSI-compliant where possible. When deploying these rules to an enterprise PostgreSQL instance, check the following syntax items (the DuckDB scripts in this repo remain unchanged):

### A. Data Ingestion (`read_parquet` to `COPY`)
- **DuckDB:** `CREATE OR REPLACE TABLE transactions AS SELECT * FROM read_parquet('path/to/file.parquet');`
- **PostgreSQL:** Native PostgreSQL does not read Parquet files directly out of the box. Use either:
  1. Standard CSV copy: `\COPY transactions FROM 'transactions_clean.csv' WITH (FORMAT csv, HEADER true);`
  2. Foreign Data Wrapper (`pg_parquet` / `parquet_fdw`):
     ```sql
     CREATE FOREIGN TABLE transactions_fdw (...) 
     SERVER parquet_server 
     OPTIONS (filename '/path/to/file.parquet');
     ```

### B. Window Numeric `RANGE` Frame Syntax
- **DuckDB:** Supports integer offsets directly:
  ```sql
  COUNT(*) OVER (PARTITION BY nameOrig ORDER BY step RANGE BETWEEN 5 PRECEDING AND CURRENT ROW)
  ```
- **PostgreSQL:**
  - Supported for numeric/integer types in PostgreSQL 11+: `RANGE BETWEEN 5 PRECEDING AND CURRENT ROW` works as long as `step` is `integer` or `numeric`.
  - In temporal production systems using timestamps, convert to interval syntax:
    ```sql
    COUNT(*) OVER (
        PARTITION BY nameOrig 
        ORDER BY txn_timestamp 
        RANGE BETWEEN INTERVAL '5 hours' PRECEDING AND CURRENT ROW
    )
    ```

### C. Percentile Ranking (`PERCENT_RANK()`)
- **DuckDB & PostgreSQL:** Both engines natively support the standard ANSI window function:
  ```sql
  PERCENT_RANK() OVER (PARTITION BY type ORDER BY amount)
  ```
- **PostgreSQL Performance Optimization:** For tables with $>2.7$ million rows, create a composite index on `(type, amount)` before executing this rule in PostgreSQL to avoid disk-spilled external merge sorts:
  ```sql
  CREATE INDEX idx_transactions_type_amount ON transactions (type, amount);
  ```

### D. Filter Clause (`FILTER (WHERE ...)`)
- Both DuckDB and PostgreSQL natively support SQL:2003 aggregate filtering:
  ```sql
  COUNT(*) FILTER (WHERE is_rule_alert_1 = 1)
  ```
  No syntax changes are required.
