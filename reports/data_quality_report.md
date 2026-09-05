# Data Quality Report

Generated: 2026-09-05 06:03 UTC

## Result

**15/15 checks passed.**

## Dataset volumes

| Dataset | Raw rows | Clean rows |
| --- | ---: | ---: |
| customers | 4 | 4 |
| sales_orders | 4 | 4 |
| gl_controls | 3 | 3 |

## Control results

| Check | Status | Observed | Expected | Detail |
| --- | --- | --- | --- | --- |
| REQ_CUSTOMERS | PASS | customer_id, customer_name, segment, status, created_date | all required columns present | Validated at ingestion |
| NULL_CUSTOMERS | PASS | 0 | <= 0 | Required-field null values |
| REQ_SALES_ORDERS | PASS | order_id, customer_id, order_date, order_amount, currency, category | all required columns present | Validated at ingestion |
| NULL_SALES_ORDERS | PASS | 0 | <= 0 | Required-field null values |
| REQ_GL_CONTROLS | PASS | control_date, source_system, order_count, order_amount, currency | all required columns present | Validated at ingestion |
| NULL_GL_CONTROLS | PASS | 0 | <= 0 | Required-field null values |
| DUP_CUSTOMERS | PASS | 0 | 0 | Duplicate customer_id values |
| DUP_SALES_ORDERS | PASS | 0 | 0 | Duplicate order_id values |
| RANGE_ORDER_AMOUNT | PASS | 0 | 0 | Amount must be > 0 and <= 1,000,000 |
| VALID_ENUMS | PASS | 0 | 0 | Approved segment, status, category, and currency values |
| FK_ORDER_CUSTOMER | PASS | 0 | 0 | Every order customer exists in customer master |
| FRESH_RAW_EXTRACTS | PASS | 2 days | <= 7 days | [["customers.csv", 2], ["sales_orders.csv", 2], ["gl_controls.csv", 2]] |
| RECON_ROW_COUNT | PASS | 4 | 4 | Raw-to-clean sales order count |
| RECON_ORDER_COUNT | PASS | 4 | 4 | Sales orders versus GL control count |
| RECON_ORDER_VALUE | PASS | 2550.49 | 2550.49 | Sales orders versus GL control amount |

## Notes

All samples use synthetic, non-sensitive records. Freshness is evaluated from raw-file modification time and requires files no more than seven calendar days old.
