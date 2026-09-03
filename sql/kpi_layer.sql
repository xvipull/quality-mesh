-- Quality Mesh KPI semantic layer (SQLite).
-- Re-run after rebuilding base tables; each view has an explicit, documented grain.

DROP VIEW IF EXISTS vw_daily_sales_kpi;
CREATE VIEW vw_daily_sales_kpi AS
SELECT
  d.calendar_date,
  COUNT(*) AS order_count,
  ROUND(SUM(f.order_amount), 2) AS revenue_usd,
  ROUND(AVG(f.order_amount), 2) AS average_order_value,
  COUNT(DISTINCT f.customer_key) AS active_customers
FROM fact_sales_order AS f
JOIN dim_date AS d ON d.date_key = f.order_date_key
GROUP BY d.calendar_date;

DROP VIEW IF EXISTS vw_monthly_sales_trend;
CREATE VIEW vw_monthly_sales_trend AS
WITH monthly AS (
  SELECT
    SUBSTR(calendar_date, 1, 7) || '-01' AS month_start,
    SUM(revenue_usd) AS revenue_usd,
    SUM(order_count) AS order_count,
    SUM(active_customers) AS active_customer_days
  FROM vw_daily_sales_kpi
  GROUP BY SUBSTR(calendar_date, 1, 7)
), comparison AS (
  SELECT
    month_start,
    revenue_usd,
    order_count,
    active_customer_days,
    LAG(revenue_usd) OVER (ORDER BY month_start) AS prior_period_revenue_usd,
    LAG(order_count) OVER (ORDER BY month_start) AS prior_period_order_count
  FROM monthly
)
SELECT
  month_start,
  ROUND(revenue_usd, 2) AS revenue_usd,
  order_count,
  active_customer_days,
  ROUND(prior_period_revenue_usd, 2) AS prior_period_revenue_usd,
  CASE WHEN prior_period_revenue_usd IS NULL OR prior_period_revenue_usd = 0 THEN NULL
       ELSE ROUND(100.0 * (revenue_usd - prior_period_revenue_usd) / prior_period_revenue_usd, 2) END AS revenue_period_over_period_pct,
  CASE WHEN prior_period_order_count IS NULL OR prior_period_order_count = 0 THEN NULL
       ELSE ROUND(100.0 * (order_count - prior_period_order_count) / prior_period_order_count, 2) END AS order_period_over_period_pct
FROM comparison;

DROP VIEW IF EXISTS vw_customer_segment_kpi;
CREATE VIEW vw_customer_segment_kpi AS
SELECT
  c.segment,
  COUNT(DISTINCT c.customer_key) AS customers_with_orders,
  COUNT(f.order_key) AS order_count,
  ROUND(SUM(f.order_amount), 2) AS revenue_usd,
  ROUND(AVG(f.order_amount), 2) AS average_order_value,
  ROUND(100.0 * SUM(f.order_amount) / SUM(SUM(f.order_amount)) OVER (), 2) AS revenue_share_pct
FROM fact_sales_order AS f
JOIN dim_customer AS c ON c.customer_key = f.customer_key
GROUP BY c.segment;

DROP VIEW IF EXISTS vw_customer_cohort_month;
CREATE VIEW vw_customer_cohort_month AS
WITH order_base AS (
  SELECT
    SUBSTR(c.created_date, 1, 7) || '-01' AS cohort_month,
    SUBSTR(d.calendar_date, 1, 7) || '-01' AS order_month,
    c.customer_key,
    f.order_amount
  FROM fact_sales_order AS f
  JOIN dim_customer AS c ON c.customer_key = f.customer_key
  JOIN dim_date AS d ON d.date_key = f.order_date_key
)
SELECT
  cohort_month,
  order_month,
  COUNT(DISTINCT customer_key) AS active_customers,
  COUNT(*) AS order_count,
  ROUND(SUM(order_amount), 2) AS revenue_usd
FROM order_base
GROUP BY cohort_month, order_month;

DROP VIEW IF EXISTS vw_quality_exceptions;
CREATE VIEW vw_quality_exceptions AS
SELECT check_id, status, observed, expected, detail, evaluated_at_utc
FROM dq_check_result
WHERE status IN ('FAIL', 'WARN');

DROP VIEW IF EXISTS vw_reconciliation_daily;
CREATE VIEW vw_reconciliation_daily AS
WITH curated AS (
  SELECT order_date_key AS date_key, currency_code, COUNT(*) AS curated_order_count, ROUND(SUM(order_amount), 2) AS curated_order_amount
  FROM fact_sales_order
  GROUP BY order_date_key, currency_code
), source_control AS (
  SELECT control_date_key AS date_key, currency_code, SUM(order_count) AS source_order_count, ROUND(SUM(order_amount), 2) AS source_order_amount
  FROM fact_reconciliation_control
  GROUP BY control_date_key, currency_code
), joined AS (
  SELECT
    COALESCE(s.date_key, c.date_key) AS date_key,
    COALESCE(s.currency_code, c.currency_code) AS currency_code,
    COALESCE(s.source_order_count, 0) AS source_order_count,
    COALESCE(c.curated_order_count, 0) AS curated_order_count,
    COALESCE(s.source_order_amount, 0) AS source_order_amount,
    COALESCE(c.curated_order_amount, 0) AS curated_order_amount
  FROM source_control AS s
  FULL OUTER JOIN curated AS c ON c.date_key = s.date_key AND c.currency_code = s.currency_code
)
SELECT
  d.calendar_date,
  currency_code,
  source_order_count,
  curated_order_count,
  source_order_count - curated_order_count AS order_count_variance,
  source_order_amount,
  curated_order_amount,
  ROUND(source_order_amount - curated_order_amount, 2) AS amount_variance_usd,
  0.00 AS documented_amount_tolerance_usd,
  CASE WHEN source_order_count = curated_order_count
         AND ABS(source_order_amount - curated_order_amount) <= 0.00 THEN 'PASS' ELSE 'FAIL' END AS reconciliation_status
FROM joined
JOIN dim_date AS d ON d.date_key = joined.date_key;

DROP VIEW IF EXISTS vw_reconciliation_exceptions;
CREATE VIEW vw_reconciliation_exceptions AS
SELECT *
FROM vw_reconciliation_daily
WHERE reconciliation_status = 'FAIL';

DROP VIEW IF EXISTS vw_enterprise_kpi_summary;
CREATE VIEW vw_enterprise_kpi_summary AS
SELECT
  (SELECT COUNT(*) FROM fact_sales_order) AS sales_order_count,
  (SELECT ROUND(SUM(order_amount), 2) FROM fact_sales_order) AS sales_revenue_usd,
  (SELECT ROUND(100.0 * SUM(CASE WHEN status = 'PASS' THEN 1 ELSE 0 END) / COUNT(*), 2) FROM dq_check_result) AS data_quality_pass_rate_pct,
  (SELECT COUNT(*) FROM vw_quality_exceptions) AS open_quality_exceptions,
  (SELECT COUNT(*) FROM vw_reconciliation_exceptions) AS reconciliation_exceptions;
