-- Operational reconciliation queries. Tolerances are documented in docs/kpi_catalog.md.

-- 1. Daily proof: curated reporting totals must equal source controls (USD tolerance = 0.00).
SELECT *
FROM vw_reconciliation_daily
ORDER BY calendar_date, currency_code;

-- 2. Exception queue: expected to return zero records before dashboard publication.
SELECT *
FROM vw_reconciliation_exceptions;

-- 3. Aggregate close control: source and curated totals across the reporting period.
SELECT
  SUM(source_order_count) AS source_order_count,
  SUM(curated_order_count) AS curated_order_count,
  SUM(order_count_variance) AS count_variance,
  ROUND(SUM(source_order_amount), 2) AS source_order_amount,
  ROUND(SUM(curated_order_amount), 2) AS curated_order_amount,
  ROUND(SUM(amount_variance_usd), 2) AS amount_variance_usd,
  CASE WHEN SUM(order_count_variance) = 0 AND ABS(SUM(amount_variance_usd)) <= 0.00 THEN 'PASS' ELSE 'FAIL' END AS close_status
FROM vw_reconciliation_daily;
