# KPI Catalog

All rates are shown as percentages unless otherwise stated. A failed freshness SLA is reported independently and is not hidden by a high content-quality score.

| KPI | Definition / formula | Grain | Target | Owner | Decision enabled |
| --- | --- | --- | --- | --- | --- |
| Overall Data Quality Score | Weighted mean of approved dimension scores; weights are set per data product | Product, daily | >= 98.0% | Data Governance Lead | Is the data product fit for use? |
| Completeness Rate | Populated required values / records expected to have a value × 100 | CDE, run | >= 99.5% | Domain Data Owner | Can required business attributes be trusted? |
| Validity Rate | Values matching approved domain/range/pattern / values assessed × 100 | CDE, run | >= 99.0% | Domain Data Owner | Are values usable under business rules? |
| Uniqueness Rate | 1 − duplicate business keys / keys assessed | Entity, run | >= 99.9% | Domain Data Owner | Is double-counting risk acceptable? |
| Timeliness Compliance | Loads received by committed SLA / scheduled loads × 100 | Product, month | >= 95.0% | Technical Custodian | Can reporting be released on time? |
| Reconciliation Variance | Absolute(source control total − target control total) / max(abs(source control total), 1) × 100 | Control, run | <= approved tolerance | Controller / Data Owner | Do source and target agree? |
| Reconciliation Coverage | Target keys matched to eligible source keys / eligible source keys × 100 | Control, run | >= 99.5% | Domain Data Owner | Are populations carried through? |
| Critical Exception SLA Compliance | Critical exceptions assigned within one business day / critical exceptions raised × 100 | Domain, month | >= 90.0% | Data Governance Lead | Is accountability working? |
| Mean Time to Resolve | Sum(resolved time − opened time) / number resolved | Severity, month | Baseline then improve 15% quarter-over-quarter | Domain Data Owner | Where should remediation capacity be focused? |
| Recurrence Rate | Exceptions repeating the same rule and root cause within 30 days / resolved exceptions × 100 | Rule, month | <= 10.0% | Domain Data Owner | Did remediation fix the cause? |

## Score interpretation

Green: meets target. Amber: within 2 percentage points of a rate target or within 25% of a variance tolerance. Red: below target or above tolerance. Any unresolved critical exception overrides an overall green product status to amber until governance disposition is recorded.
