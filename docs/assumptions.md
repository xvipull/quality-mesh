# Assumptions Register

| ID | Assumption | Validation / trigger | Owner | Impact if false |
| --- | --- | --- | --- | --- |
| A-01 | Pilot source systems can provide stable daily extracts and metadata | Confirm in discovery and access design | Technical Custodians | Re-plan ingestion and freshness targets |
| A-02 | Data Owners can approve CDEs and thresholds within five business days | Measure onboarding lead time | Data Governance Lead | Delay rule implementation |
| A-03 | Finance will approve authoritative reconciliation control totals and tolerances | Controller sign-off before GL pilot | Corporate Controller | Financial reconciliation cannot enter production |
| A-04 | Enterprise identity platform supports required group-based access | Security design review | Security Architect | Use interim restricted pilot access |
| A-05 | Source-to-target lineage is sufficiently known for pilot feeds | Mapping workshop | Analytics Engineering Lead | Limit controls to documented pathways |
| A-06 | Daily batch latency is acceptable for release 1 | Sponsor confirmation | CDAO Sponsor | Re-scope platform for streaming needs |
| A-07 | Exception workflow can integrate with the approved ticketing process or be managed in a governed register | Operations design review | Data Governance Lead | Reduce automation and revise SLAs |
