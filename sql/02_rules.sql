-- ==============================================================================
-- 02_rules.sql: Transaction Monitoring Rule Engine Foundation & Implementations
-- ==============================================================================
-- ARCHITECTURAL OVERVIEW & RULE ROADMAP:
-- Centralized SQL repository for heuristic and expert business rules in DuckDB.
--
-- SCOPING POLICY:
-- All rules are evaluated strictly within the `base_scope` view (TRANSFER & CASH_OUT).
-- Transactions outside this scope (CASH_IN, DEBIT, PAYMENT) automatically receive
-- flag 0 during downstream global alert consolidation.
--
-- TARGET LEAKAGE & REFERENCE RESTRICTIONS:
-- `isFlaggedFraud` is strictly excluded from `base_scope` and all rule logic.
-- `isFraud` is retained solely for offline auditing and metric calculation.
--
-- RULE IMPLEMENTATION TRACKER:
-- 1. Rule 1 (Account Emptied - rule1_emptied): Flags complete sender balance drainage.
-- 2. Rule 2 (High Amount Outlier - rule2_large_amount): Flags top 1% amount by type.
-- 3. Rule 3 (Velocity - rule3_velocity): Flags 3+ transactions in 6-hour window by nameOrig.
-- 4. Rule 4 (Transfer then Cash-Out - rule4_transfer_then_cashout): Flags rapid mule cash-out flow.
-- 5. Rule 5 (Mule Destination - rule5_mule_dest): Flags destinations with 3+ distinct senders per day.
-- 6. Rule 6 (Destination Unchanged - rule6_dest_unchanged): Flags large transfers where dest balance is unchanged.
-- 7. Rule 7 (Balance Inconsistency - rule7_balance_error): Flags simultaneous origin and destination balance errors.
-- 8. Composite Alert Engine (rule_flags table): Multi-rule consolidation, alert_score, is_rule_alert_1/2.
-- ==============================================================================

-- 1. Create base_scope view restricted to TRANSFER and CASH_OUT
CREATE OR REPLACE VIEW base_scope AS
SELECT 
    txn_id,
    step,
    day,
    hour,
    type,
    amount,
    nameOrig,
    nameDest,
    oldbalanceOrg,
    newbalanceOrig,
    oldbalanceDest,
    newbalanceDest,
    errOrig,
    errDest,
    destIsMerchant,
    origEmptied,
    destBalanceUnchanged,
    isFraud
FROM transactions
WHERE type IN ('TRANSFER', 'CASH_OUT');

-- ------------------------------------------------------------------------------
-- Rule 1: Account Emptied (rule1_emptied)
-- Flags transactions where oldbalanceOrg > 0, newbalanceOrig == 0,
-- and abs(amount - oldbalanceOrg) < 0.01.
-- ------------------------------------------------------------------------------
CREATE OR REPLACE VIEW rule1_emptied AS
WITH scoped AS (
    SELECT 
        txn_id,
        oldbalanceOrg,
        newbalanceOrig,
        amount
    FROM base_scope
)
SELECT 
    txn_id,
    CASE 
        WHEN oldbalanceOrg > 0 
         AND newbalanceOrig = 0 
         AND abs(amount - oldbalanceOrg) < 0.01 
        THEN 1 
        ELSE 0 
    END AS rule_emptied
FROM scoped;

-- Verification Query 1: Performance metrics for Rule 1 (rule_emptied)
SELECT 
    r.rule_emptied,
    count(*) AS total_rows,
    sum(b.isFraud) AS fraud_rows,
    count(*) - sum(b.isFraud) AS non_fraud_rows,
    round(100.0 * sum(b.isFraud) / count(*), 4) AS precision_pct,
    round(100.0 * sum(b.isFraud) / (SELECT sum(isFraud) FROM base_scope), 4) AS recall_pct
FROM rule1_emptied r
JOIN base_scope b ON r.txn_id = b.txn_id
GROUP BY r.rule_emptied
ORDER BY r.rule_emptied DESC;

-- ------------------------------------------------------------------------------
-- Rule 2: High Amount Outlier (rule2_large_amount)
-- Flags transactions at or above the 99th percentile of amount within its type
-- computed via PERCENT_RANK() OVER (PARTITION BY type ORDER BY amount).
-- ------------------------------------------------------------------------------
CREATE OR REPLACE VIEW rule2_large_amount AS
WITH ranked AS (
    SELECT 
        txn_id,
        percent_rank() OVER (PARTITION BY type ORDER BY amount) AS amt_pctile
    FROM base_scope
)
SELECT 
    txn_id,
    amt_pctile,
    CASE 
        WHEN amt_pctile >= 0.99 THEN 1 
        ELSE 0 
    END AS rule_large_amount
FROM ranked;

-- Verification Query 2A: Performance metrics for Rule 2 (rule_large_amount: 1 vs 0)
SELECT 
    r.rule_large_amount,
    count(*) AS total_rows,
    round(100.0 * count(*) / (SELECT count(*) FROM base_scope), 4) AS share_of_scope_pct,
    sum(b.isFraud) AS fraud_rows,
    count(*) - sum(b.isFraud) AS non_fraud_rows,
    round(100.0 * sum(b.isFraud) / count(*), 4) AS precision_pct,
    round(100.0 * sum(b.isFraud) / (SELECT sum(isFraud) FROM base_scope), 4) AS recall_pct
FROM rule2_large_amount r
JOIN base_scope b ON r.txn_id = b.txn_id
GROUP BY r.rule_large_amount
ORDER BY r.rule_large_amount DESC;

-- Verification Query 2B: Implied amount thresholds by transaction type for Rule 2
SELECT 
    b.type,
    min(b.amount) AS min_amount_threshold,
    max(b.amount) AS max_amount,
    count(*) AS flagged_count,
    sum(b.isFraud) AS fraud_count,
    round(100.0 * sum(b.isFraud) / count(*), 4) AS precision_pct
FROM rule2_large_amount r
JOIN base_scope b ON r.txn_id = b.txn_id
WHERE r.rule_large_amount = 1
GROUP BY b.type
ORDER BY b.type;

-- ------------------------------------------------------------------------------
-- Rule 3: Velocity / Rapid Burst Activity (rule3_velocity)
-- Counts how many scoped transactions the same nameOrig made in the window
-- of the current step and the 5 steps before (6-hour rolling window).
-- Uses numeric RANGE frame:
--   COUNT(*) OVER (PARTITION BY nameOrig ORDER BY step RANGE BETWEEN 5 PRECEDING AND CURRENT ROW)
-- Flags rule_velocity = 1 when txns_last_6h >= 3.
-- ------------------------------------------------------------------------------
CREATE OR REPLACE VIEW rule3_velocity AS
WITH windowed AS (
    SELECT 
        txn_id,
        count(*) OVER (
            PARTITION BY nameOrig 
            ORDER BY step 
            RANGE BETWEEN 5 PRECEDING AND CURRENT ROW
        ) AS txns_last_6h
    FROM base_scope
)
SELECT 
    txn_id,
    txns_last_6h,
    CASE 
        WHEN txns_last_6h >= 3 THEN 1 
        ELSE 0 
    END AS rule_velocity
FROM windowed;

-- Diagnostic Query 3A: Distribution of txns_last_6h and fraud counts by frequency
-- Shows counts for values 1, 2, 3, 4, and 5+ to evaluate potential thresholds
WITH bucketed AS (
    SELECT 
        r.txn_id,
        r.txns_last_6h,
        b.isFraud,
        CASE 
            WHEN r.txns_last_6h = 1 THEN '1'
            WHEN r.txns_last_6h = 2 THEN '2'
            WHEN r.txns_last_6h = 3 THEN '3'
            WHEN r.txns_last_6h = 4 THEN '4'
            ELSE '5+'
        END AS bucket
    FROM rule3_velocity r
    JOIN base_scope b ON r.txn_id = b.txn_id
),
all_buckets AS (
    SELECT * FROM (VALUES ('1', 1), ('2', 2), ('3', 3), ('4', 4), ('5+', 5)) AS v(bucket, sort_order)
),
agg AS (
    SELECT 
        bucket,
        count(*) AS total_rows,
        sum(isFraud) AS fraud_rows,
        count(*) - sum(isFraud) AS non_fraud_rows
    FROM bucketed
    GROUP BY bucket
)
SELECT 
    ab.bucket AS txns_last_6h,
    coalesce(agg.total_rows, 0) AS total_rows,
    round(100.0 * coalesce(agg.total_rows, 0) / (SELECT count(*) FROM base_scope), 4) AS share_of_scope_pct,
    coalesce(agg.fraud_rows, 0) AS fraud_rows,
    coalesce(agg.non_fraud_rows, 0) AS non_fraud_rows,
    round(coalesce(100.0 * agg.fraud_rows / nullif(agg.total_rows, 0), 0.0), 4) AS fraud_rate_pct
FROM all_buckets ab
LEFT JOIN agg ON ab.bucket = agg.bucket
ORDER BY ab.sort_order;

-- Verification Query 3B: Performance metrics for Rule 3 (rule_velocity: 1 vs 0)
WITH flags AS (
    SELECT * FROM (VALUES (1), (0)) AS f(flag)
),
agg AS (
    SELECT 
        r.rule_velocity,
        count(*) AS total_rows,
        sum(b.isFraud) AS fraud_rows,
        count(*) - sum(b.isFraud) AS non_fraud_rows
    FROM rule3_velocity r
    JOIN base_scope b ON r.txn_id = b.txn_id
    GROUP BY r.rule_velocity
)
SELECT 
    f.flag AS rule_velocity,
    coalesce(agg.total_rows, 0) AS total_rows,
    round(100.0 * coalesce(agg.total_rows, 0) / (SELECT count(*) FROM base_scope), 4) AS share_of_scope_pct,
    coalesce(agg.fraud_rows, 0) AS fraud_rows,
    coalesce(agg.non_fraud_rows, 0) AS non_fraud_rows,
    round(coalesce(100.0 * agg.fraud_rows / nullif(agg.total_rows, 0), 0.0), 4) AS precision_pct,
    round(coalesce(100.0 * agg.fraud_rows / (SELECT sum(isFraud) FROM base_scope), 0.0), 4) AS recall_pct
FROM flags f
LEFT JOIN agg ON f.flag = agg.rule_velocity
ORDER BY f.flag DESC;

-- ------------------------------------------------------------------------------
-- Rule 4: Transfer Followed by Cash-Out (rule4_transfer_then_cashout)
-- Flags cash-out transactions where funds were transferred into the account
-- within the preceding 24 hours (24 steps) and cashed out within +/- 10% amount.
-- Returns exactly one row per scoped transaction (LEFT JOIN with base_scope).
-- ------------------------------------------------------------------------------
CREATE OR REPLACE VIEW rule4_transfer_then_cashout AS
WITH transfers_in AS (
    SELECT 
        txn_id,
        nameDest AS account,
        step AS t_step,
        amount
    FROM base_scope
    WHERE type = 'TRANSFER'
),
cashouts AS (
    SELECT 
        txn_id,
        nameOrig AS account,
        step AS c_step,
        amount
    FROM base_scope
    WHERE type = 'CASH_OUT'
),
matched_cashouts AS (
    SELECT DISTINCT 
        c.txn_id
    FROM cashouts c
    JOIN transfers_in t ON c.account = t.account
    WHERE c.c_step BETWEEN t.t_step AND t.t_step + 24
      AND abs(c.amount - t.amount) <= 0.10 * t.amount
)
SELECT 
    b.txn_id,
    CASE 
        WHEN m.txn_id IS NOT NULL THEN 1 
        ELSE 0 
    END AS rule_transfer_then_cashout
FROM base_scope b
LEFT JOIN matched_cashouts m ON b.txn_id = m.txn_id;

-- Diagnostic Query 4A: Matched cash-outs (transfer followed by cash-out within 24h & 10% amount)
WITH transfers_in AS (
    SELECT 
        txn_id,
        nameDest AS account,
        step AS t_step,
        amount
    FROM base_scope
    WHERE type = 'TRANSFER'
),
cashouts AS (
    SELECT 
        txn_id,
        nameOrig AS account,
        step AS c_step,
        amount,
        isFraud
    FROM base_scope
    WHERE type = 'CASH_OUT'
),
matches AS (
    SELECT 
        c.txn_id,
        c.isFraud
    FROM cashouts c
    JOIN transfers_in t ON c.account = t.account
    WHERE c.c_step BETWEEN t.t_step AND t.t_step + 24
      AND abs(c.amount - t.amount) <= 0.10 * t.amount
    GROUP BY c.txn_id, c.isFraud
)
SELECT 
    (SELECT count(*) FROM cashouts) AS total_cashout_txns,
    count(m.txn_id) AS matched_cashouts,
    coalesce(sum(m.isFraud), 0) AS fraud_among_matches,
    count(m.txn_id) - coalesce(sum(m.isFraud), 0) AS non_fraud_among_matches,
    round(coalesce(100.0 * sum(m.isFraud) / nullif(count(m.txn_id), 0), 0.0), 4) AS precision_pct
FROM matches m;

-- Verification Query 4B: Performance metrics for Rule 4 (rule_transfer_then_cashout: 1 vs 0)
WITH flags AS (
    SELECT * FROM (VALUES (1), (0)) AS f(flag)
),
agg AS (
    SELECT 
        r.rule_transfer_then_cashout,
        count(*) AS total_rows,
        sum(b.isFraud) AS fraud_rows,
        count(*) - sum(b.isFraud) AS non_fraud_rows
    FROM rule4_transfer_then_cashout r
    JOIN base_scope b ON r.txn_id = b.txn_id
    GROUP BY r.rule_transfer_then_cashout
)
SELECT 
    f.flag AS rule_transfer_then_cashout,
    coalesce(agg.total_rows, 0) AS total_rows,
    round(100.0 * coalesce(agg.total_rows, 0) / (SELECT count(*) FROM base_scope), 4) AS share_of_scope_pct,
    coalesce(agg.fraud_rows, 0) AS fraud_rows,
    coalesce(agg.non_fraud_rows, 0) AS non_fraud_rows,
    round(coalesce(100.0 * agg.fraud_rows / nullif(agg.total_rows, 0), 0.0), 4) AS precision_pct,
    round(coalesce(100.0 * agg.fraud_rows / (SELECT sum(isFraud) FROM base_scope), 0.0), 4) AS recall_pct
FROM flags f
LEFT JOIN agg ON f.flag = agg.rule_transfer_then_cashout
ORDER BY f.flag DESC;

-- Verification Query 4C: Integrity assertion for rule4_transfer_then_cashout view
-- Asserts that count(*) = count(DISTINCT txn_id) = base_scope row count (2,770,409)
SELECT 
    count(*) AS total_rows,
    count(DISTINCT txn_id) AS distinct_txn_ids,
    (SELECT count(*) FROM base_scope) AS base_scope_rows,
    CASE 
        WHEN count(*) = count(DISTINCT txn_id) 
         AND count(*) = (SELECT count(*) FROM base_scope) 
        THEN 'PASSED' 
        ELSE 'FAILED' 
    END AS assertion_status
FROM rule4_transfer_then_cashout;

-- ------------------------------------------------------------------------------
-- Rule 5: Mule Destination / High Inbound Fan-in (rule5_mule_dest)
-- For each non-merchant destination (nameDest), counts distinct nameOrig senders
-- that sent to it in the same day using:
--   COUNT(DISTINCT nameOrig) OVER (PARTITION BY nameDest, day)
-- Flags rule_mule_dest = 1 when distinct senders per destination per day >= 3.
-- Returns every scoped txn_id exactly once.
-- ------------------------------------------------------------------------------
CREATE OR REPLACE VIEW rule5_mule_dest AS
WITH distinct_counts AS (
    SELECT 
        txn_id,
        count(DISTINCT nameOrig) OVER (PARTITION BY nameDest, day) AS distinct_senders
    FROM base_scope
    WHERE destIsMerchant = 0
)
SELECT 
    b.txn_id,
    CASE 
        WHEN dc.distinct_senders >= 3 THEN 1 
        ELSE 0 
    END AS rule_mule_dest
FROM base_scope b
LEFT JOIN distinct_counts dc ON b.txn_id = dc.txn_id;

-- Verification Query 5A: Performance metrics for Rule 5 (rule_mule_dest: 1 vs 0)
WITH flags AS (
    SELECT * FROM (VALUES (1), (0)) AS f(flag)
),
agg AS (
    SELECT 
        r.rule_mule_dest,
        count(*) AS total_rows,
        sum(b.isFraud) AS fraud_rows,
        count(*) - sum(b.isFraud) AS non_fraud_rows
    FROM rule5_mule_dest r
    JOIN base_scope b ON r.txn_id = b.txn_id
    GROUP BY r.rule_mule_dest
)
SELECT 
    f.flag AS rule_mule_dest,
    coalesce(agg.total_rows, 0) AS total_rows,
    round(100.0 * coalesce(agg.total_rows, 0) / (SELECT count(*) FROM base_scope), 4) AS share_of_scope_pct,
    coalesce(agg.fraud_rows, 0) AS fraud_rows,
    coalesce(agg.non_fraud_rows, 0) AS non_fraud_rows,
    round(coalesce(100.0 * agg.fraud_rows / nullif(agg.total_rows, 0), 0.0), 4) AS precision_pct,
    round(coalesce(100.0 * agg.fraud_rows / (SELECT sum(isFraud) FROM base_scope), 0.0), 4) AS recall_pct
FROM flags f
LEFT JOIN agg ON f.flag = agg.rule_mule_dest
ORDER BY f.flag DESC;

-- Verification Query 5B: Integrity assertion for rule5_mule_dest view
SELECT 
    count(*) AS total_rows,
    count(DISTINCT txn_id) AS distinct_txn_ids,
    (SELECT count(*) FROM base_scope) AS base_scope_rows,
    CASE 
        WHEN count(*) = count(DISTINCT txn_id) 
         AND count(*) = (SELECT count(*) FROM base_scope) 
        THEN 'PASSED' 
        ELSE 'FAILED' 
    END AS assertion_status
FROM rule5_mule_dest;

-- ------------------------------------------------------------------------------
-- Rule 6: Destination Balance Unchanged (rule6_dest_unchanged)
-- Flags TRANSFER transactions where amount >= 10,000, oldbalanceDest = newbalanceDest,
-- and destIsMerchant = 0 (captures funds that vanished at the non-merchant destination).
-- Returns every scoped txn_id exactly once.
-- ------------------------------------------------------------------------------
CREATE OR REPLACE VIEW rule6_dest_unchanged AS
SELECT 
    txn_id,
    CASE 
        WHEN type = 'TRANSFER' 
         AND amount >= 10000 
         AND oldbalanceDest = newbalanceDest 
         AND destIsMerchant = 0 
        THEN 1 
        ELSE 0 
    END AS rule_dest_unchanged
FROM base_scope;

-- Verification Query 6A: Performance metrics for Rule 6 (rule_dest_unchanged: 1 vs 0)
WITH flags AS (
    SELECT * FROM (VALUES (1), (0)) AS f(flag)
),
agg AS (
    SELECT 
        r.rule_dest_unchanged,
        count(*) AS total_rows,
        sum(b.isFraud) AS fraud_rows,
        count(*) - sum(b.isFraud) AS non_fraud_rows
    FROM rule6_dest_unchanged r
    JOIN base_scope b ON r.txn_id = b.txn_id
    GROUP BY r.rule_dest_unchanged
)
SELECT 
    f.flag AS rule_dest_unchanged,
    coalesce(agg.total_rows, 0) AS total_rows,
    round(100.0 * coalesce(agg.total_rows, 0) / (SELECT count(*) FROM base_scope), 4) AS share_of_scope_pct,
    coalesce(agg.fraud_rows, 0) AS fraud_rows,
    coalesce(agg.non_fraud_rows, 0) AS non_fraud_rows,
    round(coalesce(100.0 * agg.fraud_rows / nullif(agg.total_rows, 0), 0.0), 4) AS precision_pct,
    round(coalesce(100.0 * agg.fraud_rows / (SELECT sum(isFraud) FROM base_scope), 0.0), 4) AS recall_pct
FROM flags f
LEFT JOIN agg ON f.flag = agg.rule_dest_unchanged
ORDER BY f.flag DESC;

-- Verification Query 6B: Integrity assertion for rule6_dest_unchanged view
SELECT 
    count(*) AS total_rows,
    count(DISTINCT txn_id) AS distinct_txn_ids,
    (SELECT count(*) FROM base_scope) AS base_scope_rows,
    CASE 
        WHEN count(*) = count(DISTINCT txn_id) 
         AND count(*) = (SELECT count(*) FROM base_scope) 
        THEN 'PASSED' 
        ELSE 'FAILED' 
    END AS assertion_status
FROM rule6_dest_unchanged;

-- ------------------------------------------------------------------------------
-- Rule 7: Simultaneous Balance Inconsistency (rule7_balance_error)
-- Flags transactions where both sender and destination accounts display balance
-- anomalies: ABS(errOrig) > 0.01 AND ABS(errDest) > 0.01 AND destIsMerchant = 0.
-- Returns every scoped txn_id exactly once.
-- ------------------------------------------------------------------------------
CREATE OR REPLACE VIEW rule7_balance_error AS
SELECT 
    txn_id,
    CASE 
        WHEN abs(errOrig) > 0.01 
         AND abs(errDest) > 0.01 
         AND destIsMerchant = 0 
        THEN 1 
        ELSE 0 
    END AS rule_balance_error
FROM base_scope;

-- Verification Query 7A: Performance metrics for Rule 7 (rule_balance_error: 1 vs 0)
WITH flags AS (
    SELECT * FROM (VALUES (1), (0)) AS f(flag)
),
agg AS (
    SELECT 
        r.rule_balance_error,
        count(*) AS total_rows,
        sum(b.isFraud) AS fraud_rows,
        count(*) - sum(b.isFraud) AS non_fraud_rows
    FROM rule7_balance_error r
    JOIN base_scope b ON r.txn_id = b.txn_id
    GROUP BY r.rule_balance_error
)
SELECT 
    f.flag AS rule_balance_error,
    coalesce(agg.total_rows, 0) AS total_rows,
    round(100.0 * coalesce(agg.total_rows, 0) / (SELECT count(*) FROM base_scope), 4) AS share_of_scope_pct,
    coalesce(agg.fraud_rows, 0) AS fraud_rows,
    coalesce(agg.non_fraud_rows, 0) AS non_fraud_rows,
    round(coalesce(100.0 * agg.fraud_rows / nullif(agg.total_rows, 0), 0.0), 4) AS precision_pct,
    round(coalesce(100.0 * agg.fraud_rows / (SELECT sum(isFraud) FROM base_scope), 0.0), 4) AS recall_pct
FROM flags f
LEFT JOIN agg ON f.flag = agg.rule_balance_error
ORDER BY f.flag DESC;

-- Verification Query 7B: Integrity assertion for rule7_balance_error view
SELECT 
    count(*) AS total_rows,
    count(DISTINCT txn_id) AS distinct_txn_ids,
    (SELECT count(*) FROM base_scope) AS base_scope_rows,
    CASE 
        WHEN count(*) = count(DISTINCT txn_id) 
         AND count(*) = (SELECT count(*) FROM base_scope) 
        THEN 'PASSED' 
        ELSE 'FAILED' 
    END AS assertion_status
FROM rule7_balance_error;

-- ==============================================================================
-- Combined Rules Comparison Table (Rules 1 to 7)
-- Cross-rule evaluation of flagged volume, fraud capture, precision, and recall
-- evaluated against the entire base_scope population (2,770,409 rows, 8,213 frauds).
-- ==============================================================================
WITH base_counts AS (
    SELECT 
        count(*) AS total_scope,
        sum(isFraud) AS total_fraud
    FROM base_scope
),
all_rules AS (
    SELECT 'Rule 1: Account Emptied' AS rule_name, 1 AS rule_order, r.rule_emptied AS flag, b.isFraud
    FROM rule1_emptied r JOIN base_scope b ON r.txn_id = b.txn_id
    UNION ALL
    SELECT 'Rule 2: Large Amount Outlier', 2, r.rule_large_amount, b.isFraud
    FROM rule2_large_amount r JOIN base_scope b ON r.txn_id = b.txn_id
    UNION ALL
    SELECT 'Rule 3: Originator Velocity (6h)', 3, r.rule_velocity, b.isFraud
    FROM rule3_velocity r JOIN base_scope b ON r.txn_id = b.txn_id
    UNION ALL
    SELECT 'Rule 4: Transfer Then Cash-Out (24h)', 4, r.rule_transfer_then_cashout, b.isFraud
    FROM rule4_transfer_then_cashout r JOIN base_scope b ON r.txn_id = b.txn_id
    UNION ALL
    SELECT 'Rule 5: Mule Destination (Day)', 5, r.rule_mule_dest, b.isFraud
    FROM rule5_mule_dest r JOIN base_scope b ON r.txn_id = b.txn_id
    UNION ALL
    SELECT 'Rule 6: Destination Balance Unchanged', 6, r.rule_dest_unchanged, b.isFraud
    FROM rule6_dest_unchanged r JOIN base_scope b ON r.txn_id = b.txn_id
    UNION ALL
    SELECT 'Rule 7: Balance Inconsistency', 7, r.rule_balance_error, b.isFraud
    FROM rule7_balance_error r JOIN base_scope b ON r.txn_id = b.txn_id
)
SELECT 
    ar.rule_name,
    cast(sum(ar.flag) AS BIGINT) AS flagged_rows,
    round(100.0 * sum(ar.flag) / max(bc.total_scope), 4) AS share_of_scope_pct,
    cast(sum(CASE WHEN ar.flag = 1 THEN ar.isFraud ELSE 0 END) AS BIGINT) AS fraud_caught,
    round(coalesce(100.0 * sum(CASE WHEN ar.flag = 1 THEN ar.isFraud ELSE 0 END) / nullif(sum(ar.flag), 0), 0.0), 4) AS precision_pct,
    round(coalesce(100.0 * sum(CASE WHEN ar.flag = 1 THEN ar.isFraud ELSE 0 END) / max(bc.total_fraud), 0.0), 4) AS recall_pct
FROM all_rules ar
CROSS JOIN base_counts bc
GROUP BY ar.rule_name, ar.rule_order
ORDER BY ar.rule_order;

-- ==============================================================================
-- Final Combination: Consolidated rule_flags Table & Alert Scoring Engine
-- Joins base_scope to all seven rule views on txn_id.
-- Evaluates alert_score (sum of flags), is_rule_alert_1 (>=1), and is_rule_alert_2 (>=2).
-- Guaranteed zero NULL values via COALESCE(..., 0).
-- ==============================================================================
CREATE OR REPLACE TABLE rule_flags AS
SELECT 
    b.txn_id,
    b.step,
    b.day,
    b.hour,
    b.type,
    b.amount,
    b.nameOrig,
    b.nameDest,
    coalesce(r1.rule_emptied, 0) AS rule_emptied,
    coalesce(r2.rule_large_amount, 0) AS rule_large_amount,
    coalesce(r3.rule_velocity, 0) AS rule_velocity,
    coalesce(r4.rule_transfer_then_cashout, 0) AS rule_transfer_then_cashout,
    coalesce(r5.rule_mule_dest, 0) AS rule_mule_dest,
    coalesce(r6.rule_dest_unchanged, 0) AS rule_dest_unchanged,
    coalesce(r7.rule_balance_error, 0) AS rule_balance_error,
    (
        coalesce(r1.rule_emptied, 0) +
        coalesce(r2.rule_large_amount, 0) +
        coalesce(r3.rule_velocity, 0) +
        coalesce(r4.rule_transfer_then_cashout, 0) +
        coalesce(r5.rule_mule_dest, 0) +
        coalesce(r6.rule_dest_unchanged, 0) +
        coalesce(r7.rule_balance_error, 0)
    ) AS alert_score,
    CASE 
        WHEN (
            coalesce(r1.rule_emptied, 0) +
            coalesce(r2.rule_large_amount, 0) +
            coalesce(r3.rule_velocity, 0) +
            coalesce(r4.rule_transfer_then_cashout, 0) +
            coalesce(r5.rule_mule_dest, 0) +
            coalesce(r6.rule_dest_unchanged, 0) +
            coalesce(r7.rule_balance_error, 0)
        ) >= 1 THEN 1 
        ELSE 0 
    END AS is_rule_alert_1,
    CASE 
        WHEN (
            coalesce(r1.rule_emptied, 0) +
            coalesce(r2.rule_large_amount, 0) +
            coalesce(r3.rule_velocity, 0) +
            coalesce(r4.rule_transfer_then_cashout, 0) +
            coalesce(r5.rule_mule_dest, 0) +
            coalesce(r6.rule_dest_unchanged, 0) +
            coalesce(r7.rule_balance_error, 0)
        ) >= 2 THEN 1 
        ELSE 0 
    END AS is_rule_alert_2,
    b.isFraud
FROM base_scope b
LEFT JOIN rule1_emptied r1 ON b.txn_id = r1.txn_id
LEFT JOIN rule2_large_amount r2 ON b.txn_id = r2.txn_id
LEFT JOIN rule3_velocity r3 ON b.txn_id = r3.txn_id
LEFT JOIN rule4_transfer_then_cashout r4 ON b.txn_id = r4.txn_id
LEFT JOIN rule5_mule_dest r5 ON b.txn_id = r5.txn_id
LEFT JOIN rule6_dest_unchanged r6 ON b.txn_id = r6.txn_id
LEFT JOIN rule7_balance_error r7 ON b.txn_id = r7.txn_id;

-- Verification Query 8A: Integrity assertion for rule_flags table
-- Asserts that count(*) = count(DISTINCT txn_id) = base_scope row count (2,770,409)
SELECT 
    count(*) AS total_rows,
    count(DISTINCT txn_id) AS distinct_txn_ids,
    (SELECT count(*) FROM base_scope) AS base_scope_rows,
    CASE 
        WHEN count(*) = count(DISTINCT txn_id) 
         AND count(*) = (SELECT count(*) FROM base_scope) 
        THEN 'PASSED' 
        ELSE 'FAILED' 
    END AS assertion_status
FROM rule_flags;

-- Verification Query 8B: NULL count check across all rule flag and composite score columns
SELECT 
    count(*) - count(rule_emptied) AS nulls_rule_emptied,
    count(*) - count(rule_large_amount) AS nulls_rule_large_amount,
    count(*) - count(rule_velocity) AS nulls_rule_velocity,
    count(*) - count(rule_transfer_then_cashout) AS nulls_rule_transfer_then_cashout,
    count(*) - count(rule_mule_dest) AS nulls_rule_mule_dest,
    count(*) - count(rule_dest_unchanged) AS nulls_rule_dest_unchanged,
    count(*) - count(rule_balance_error) AS nulls_rule_balance_error,
    count(*) - count(alert_score) AS nulls_alert_score,
    count(*) - count(is_rule_alert_1) AS nulls_is_rule_alert_1,
    count(*) - count(is_rule_alert_2) AS nulls_is_rule_alert_2
FROM rule_flags;

-- Verification Query 8C: Distribution of alert_score (0 to 7)
WITH all_scores AS (
    SELECT score FROM (VALUES (0), (1), (2), (3), (4), (5), (6), (7)) AS s(score)
),
agg AS (
    SELECT 
        alert_score,
        count(*) AS total_rows,
        sum(isFraud) AS fraud_rows,
        count(*) - sum(isFraud) AS non_fraud_rows
    FROM rule_flags
    GROUP BY alert_score
)
SELECT 
    s.score AS alert_score,
    coalesce(agg.total_rows, 0) AS total_rows,
    round(100.0 * coalesce(agg.total_rows, 0) / (SELECT count(*) FROM rule_flags), 4) AS share_of_scope_pct,
    coalesce(agg.fraud_rows, 0) AS fraud_rows,
    coalesce(agg.non_fraud_rows, 0) AS non_fraud_rows,
    round(coalesce(100.0 * agg.fraud_rows / nullif(agg.total_rows, 0), 0.0), 4) AS fraud_rate_pct
FROM all_scores s
LEFT JOIN agg ON s.score = agg.alert_score
ORDER BY s.score;

-- Verification Query 8D: Performance metrics for composite alerts (is_rule_alert_1 and is_rule_alert_2)
SELECT 
    'Alert Score >= 1 (is_rule_alert_1)' AS alert_policy,
    count(*) FILTER (WHERE is_rule_alert_1 = 1) AS flagged_rows,
    round(100.0 * count(*) FILTER (WHERE is_rule_alert_1 = 1) / count(*), 4) AS share_of_scope_pct,
    sum(isFraud) FILTER (WHERE is_rule_alert_1 = 1) AS fraud_caught,
    round(100.0 * sum(isFraud) FILTER (WHERE is_rule_alert_1 = 1) / count(*) FILTER (WHERE is_rule_alert_1 = 1), 4) AS precision_pct,
    round(100.0 * sum(isFraud) FILTER (WHERE is_rule_alert_1 = 1) / sum(isFraud), 4) AS recall_pct
FROM rule_flags
UNION ALL
SELECT 
    'Alert Score >= 2 (is_rule_alert_2)',
    count(*) FILTER (WHERE is_rule_alert_2 = 1),
    round(100.0 * count(*) FILTER (WHERE is_rule_alert_2 = 1) / count(*), 4),
    sum(isFraud) FILTER (WHERE is_rule_alert_2 = 1),
    round(100.0 * sum(isFraud) FILTER (WHERE is_rule_alert_2 = 1) / count(*) FILTER (WHERE is_rule_alert_2 = 1), 4),
    round(100.0 * sum(isFraud) FILTER (WHERE is_rule_alert_2 = 1) / sum(isFraud), 4)
FROM rule_flags;




