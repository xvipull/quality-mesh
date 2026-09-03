# Transformation Log

The pipeline is implemented in `src/quality_mesh/pipeline.py` and can be reproduced with `PYTHONPATH=src python -m quality_mesh.pipeline`.

| Dataset | Source field | Transformation | Rationale |
| --- | --- | --- | --- |
| Customer Master | `customer_id` | Trim, uppercase, remove separators (`c-001` → `C001`) | Canonical business key for joins |
| Customer Master | `segment`, `status` | Trim, uppercase, replace spaces/hyphens with underscores | Match governed category values |
| Customer Master | `created_date` | Parse `YYYY/MM/DD`, `DD-MM-YYYY`, or ISO date to ISO-8601 | One unambiguous date type |
| Sales Orders | `order_id`, `customer_id` | Canonical key normalization | Stable business keys and referential joins |
| Sales Orders | `order_date` | Parse allowed formats to ISO-8601 | Date dimension conformance |
| Sales Orders | `order_amount` | Remove thousands separators, parse decimal, round to two decimals | Currency-safe numeric measure |
| Sales Orders | `currency` | Trim and uppercase | ISO currency-code conformance |
| Sales Orders | `category` | Trim, uppercase, normalize separator | Conformed category dimension |
| GL Controls | Counts, amounts, dates, currency | Parse to integer, two-decimal numeric, ISO date, uppercase | Comparable reconciliation control values |

Raw files are immutable pipeline inputs. Cleaned CSVs are reproducible derivatives in `data/staging/`; the SQLite database is rebuilt from those transformations on every successful run.
