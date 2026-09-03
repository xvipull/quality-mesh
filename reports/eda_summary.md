# Exploratory Data Analysis

## Scope

Analysis uses the cleaned Sales Orders star schema and synthetic pilot data. Two charts are retained because they directly support category prioritization and order-value monitoring.

## Findings

- **Volume and value:** 4 orders total **$2,550.49**; median order value is **$625.25**.
- **Missingness:** 0 missing values across 6 analyzed fields.
- **Outliers:** 0 IQR outliers; calculated boundaries are $-1,042.82 to $2,305.69.
- **Quality controls:** 15/15 persisted controls pass.
- **Correlation:** Only one numeric analytical measure exists in this pilot, so a correlation matrix would be non-informative; it is calculated programmatically but not charted.

## Business drivers

| Segment | Orders | Revenue (USD) |
| --- | ---: | ---: |
| MID_MARKET | 1 | $1,200.00 |
| ENTERPRISE | 2 | $1,099.99 |
| SMB | 1 | $250.50 |

## Generated figures

- `reports/figures/revenue_by_category.png` — directs category-level commercial investigation.
- `reports/figures/order_value_distribution.png` — exposes value concentration and potential outliers.

## Reproducibility

`PYTHONPATH=src python3 -m quality_mesh.eda`
