# Analytics Data Model

## Grain and keys

| Table | Grain | Surrogate key | Business key(s) |
| --- | --- | --- | --- |
| `dim_date` | One calendar date | `date_key` (`YYYYMMDD`) | `calendar_date` |
| `dim_customer` | One current customer | `customer_key` | `customer_id` |
| `dim_category` | One approved sales category | `category_key` | `category_code` |
| `fact_sales_order` | One sales order | `order_key` | `order_id` |
| `fact_reconciliation_control` | One source-system control per date | `control_key` | `control_date_key`, `source_system`, `currency_code` |
| `dq_check_result` | One check outcome per pipeline run | `check_id` for this single-run sample | `check_id`, evaluation timestamp in production |

`fact_sales_order` links to date, customer, and category dimensions using integer surrogate keys. `order_id` and `customer_id` remain durable business keys for reconciliation and drill-through. The control fact is intentionally separate from order facts: it preserves authoritative source totals without inventing row-level transaction detail.

```text
dim_date      dim_customer      dim_category
    |               |                 |
    +---------------+-----------------+
                    |
             fact_sales_order

dim_date ---------------- fact_reconciliation_control
```
