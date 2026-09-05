# Advanced Decision-Support Analytics Report

Generated: 2026-09-05 06:03 UTC

**6/6 configured Spark rules passed; 0 incidents generated.**

## Rule outcomes

| Rule | Severity | Owner | Status | Failed rows |
| --- | --- | --- | --- | ---: |
| SO_REQUIRED_CUSTOMER | CRITICAL | VP, Sales Operations | PASS | 0 |
| SO_POSITIVE_AMOUNT | HIGH | VP, Sales Operations | PASS | 0 |
| SO_CONFORMED_CATEGORY | MEDIUM | BI Data Owner | PASS | 0 |
| SO_CONFORMED_CURRENCY | HIGH | Corporate Controller | PASS | 0 |
| SO_CUSTOMER_REFERENCE | CRITICAL | VP, Customer Operations | PASS | 0 |
| SO_FRESHNESS | HIGH | Commerce Data Engineering | PASS | 0 |

## Governed outputs

- SQLite tables: `governed_column_profile`, `governed_rule_result`, and `governed_incident` in `data/quality_mesh.db`.
- SQLite views: `vw_governed_rule_status` and `vw_open_data_incidents`.
- Parquet publication: `data/governed/{column_profile,rule_result,incident}`.

## Operational interpretation

A failed rule opens one incident per rule, dataset, and evaluation date. The configured deduplication key prevents duplicate alerts within that cycle. Incidents are published as open records for stewardship workflow integration.
