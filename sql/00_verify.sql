-- 00_verify.sql: Verification queries for transactions table in DuckDB

-- 1. Total row count, fraud count, and txn_id uniqueness assertion
SELECT 
    count(*) AS total_rows,
    sum(isFraud) AS fraud_count,
    round(100.0 * sum(isFraud) / count(*), 4) AS fraud_rate_pct,
    count(*) - count(DISTINCT txn_id) AS duplicate_txn_id_count
FROM transactions;

-- 2. Range of simulation step (hourly progression)
SELECT 
    min(step) AS min_step,
    max(step) AS max_step,
    count(DISTINCT step) AS distinct_steps,
    round((max(step) - min(step) + 1) / 24.0, 1) AS total_days
FROM transactions;

-- 3. Volume and fraud distribution by transaction type
SELECT 
    type,
    count(*) AS count,
    round(100.0 * count(*) / sum(count(*)) OVER (), 2) AS share_pct,
    sum(isFraud) AS fraud_count,
    round(100.0 * sum(isFraud) / count(*), 4) AS fraud_rate_pct
FROM transactions
GROUP BY type
ORDER BY count DESC;
