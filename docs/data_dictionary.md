# Data Dictionary

This logical model is the minimum shared schema for the observability hub. Physical schemas and types will be finalized in design.

| Entity | Field | Definition | Classification | Steward / source |
| --- | --- | --- | --- | --- |
| `data_product` | `data_product_id` | Stable identifier for an onboarded data product | Internal | Data Governance |
| `data_product` | `domain_name` | Business domain responsible for the product | Internal | Data Governance |
| `critical_data_element` | `cde_id` | Stable identifier for a governed critical data element | Internal | Domain Data Owner |
| `critical_data_element` | `business_definition` | Approved meaning and intended use of the CDE | Internal | Domain Data Owner |
| `quality_rule` | `rule_id` | Versioned identifier for a data-quality control | Internal | Analytics Engineering |
| `quality_rule` | `quality_dimension` | Completeness, validity, uniqueness, conformity, timeliness, or referential integrity | Internal | Data Governance |
| `quality_rule` | `threshold_value` | Approved pass threshold or tolerance | Internal | Domain Data Owner |
| `quality_run` | `run_id` | Immutable evaluation execution identifier | Internal | Platform |
| `quality_run` | `evaluated_at_utc` | UTC timestamp the rule evaluation completed | Internal | Platform |
| `quality_result` | `observed_value` | Measured score, count, or variance from a rule run | Internal | Platform |
| `quality_result` | `status` | PASS, WARN, FAIL, or ERROR outcome | Internal | Platform |
| `reconciliation_control` | `control_id` | Identifier for source-to-target comparison | Internal | Finance / Domain Owner |
| `reconciliation_control` | `control_type` | Count, amount, or key-coverage comparison | Internal | Finance / Domain Owner |
| `reconciliation_result` | `source_value` | Aggregated source-side control value | Confidential | Technical Custodian |
| `reconciliation_result` | `target_value` | Aggregated target-side control value | Confidential | Technical Custodian |
| `exception` | `exception_id` | Unique actionable quality incident | Internal | Data Governance |
| `exception` | `severity` | Critical, high, medium, or low impact classification | Internal | Data Governance |
| `exception` | `assigned_owner` | Accountable business owner role or identifier | Internal | Data Governance |
| `exception_sample` | `masked_record_reference` | Non-identifying pointer or masked evidence sample; never raw PII | Restricted | Domain Data Owner |

## Handling rules

No raw customer identifiers, contact details, payment data, or credentials may be committed. Where operational investigation needs row-level evidence, retain a masked reference in the approved platform and expose it only to authorized roles. Definitions and ownership must be reviewed quarterly or on material source change.
