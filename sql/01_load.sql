-- 01_load.sql: Create transactions table in DuckDB from cleaned Parquet
CREATE OR REPLACE TABLE transactions AS 
SELECT * 
FROM read_parquet('data/processed/transactions_clean.parquet');
