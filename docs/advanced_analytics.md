# Advanced Decision-Support Analytics

## Operating design

`src/quality_mesh/advanced_analytics.py` uses PySpark to profile clean staged datasets and evaluate rules in `config/quality_rules.json`. The rules are configuration, not hard-coded policy: each supplies a stable ID, dataset, condition type, severity, accountable owner, and plain-language description. Supported controls are Spark SQL expressions, foreign-key checks, and freshness checks.

Failures create a governed incident with a deterministic key: `rule_id|dataset|evaluation_date`. That key is the handoff contract for an external ticketing or incident-management system. The sample run has no failures; the incident table remains intentionally empty.

## Governed publication contract

| Output | Grain | Storage | Primary consumers |
| --- | --- | --- | --- |
| `governed_column_profile` | Dataset × column × evaluation | SQLite and Parquet | Data Governance, engineering |
| `governed_rule_result` | Rule × evaluation | SQLite and Parquet | BI and Data Owners |
| `governed_incident` | Failed rule × dataset × evaluation date | SQLite and Parquet when incidents exist | Stewardship workflow |
| `vw_governed_rule_status` | Severity × owner × status | SQLite view | Governance scorecards |
| `vw_open_data_incidents` | Open incident | SQLite view | Data Owners |

## Assumptions and limitations

- The pilot uses batch CSV inputs and Spark local mode. Production must run on a managed Spark platform, read governed lakehouse tables, and use a durable metastore/catalog.
- The profiler treats staged values as strings for universal CSV compatibility; profile min/max values are lexical. Numeric distribution profiling should be added through typed contracts for each CDE.
- Rule evaluation currently creates one incident per failed rule/dataset/day, not one incident per failed record. Record samples should remain in an access-controlled platform, not in Git.
- Freshness uses the supplied evaluation date (or local calendar date). Production should use an agreed business-calendar cutoff and source watermark.
- Parquet output folders are regenerated and ignored by Git; the SQLite governed tables and report provide a committed sample run for review.
- The small synthetic pilot is not statistically representative. Thresholds, ownership, and severity must be reapproved when production domains onboard.
