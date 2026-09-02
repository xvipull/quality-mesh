# Quality Mesh

**Enterprise Data Quality Observability & Reconciliation Hub**

Quality Mesh gives data governance, business intelligence, and domain teams a shared view of data reliability. It monitors critical-data-element quality, reconciles source-to-target balances, and creates accountable remediation workflows before unreliable data reaches business decisions.

## Project charter

The approved business charter, operating model, scope, risk register, and acceptance criteria are in [docs/requirements.md](docs/requirements.md). Supporting reference material includes the [KPI catalog](docs/kpi_catalog.md), [data dictionary](docs/data_dictionary.md), and [assumptions register](docs/assumptions.md).

## Architecture

```text
Operational sources / SaaS exports / Warehouse tables
                         |
                         v
                    data/raw
                         |
                         v
     Profiling + validation + reconciliation rules (src/, sql/)
                         |
                         v
                  data/staging
                         |
          +--------------+--------------+
          v                             v
   Quality scorecards              Exception register
          |                             |
          +-------------+---------------+
                        v
         Power BI dashboards / Excel packs / reports
```

## Repository layout

| Path | Purpose |
| --- | --- |
| `docs/` | Product charter, requirements, KPI definitions, and metadata |
| `data/raw/` | Immutable landing area for approved source extracts |
| `data/staging/` | Standardized, validation-ready datasets |
| `sql/` | Profiling, reconciliation, and mart queries |
| `src/` | Reusable quality checks and orchestration code |
| `notebooks/` | Controlled exploratory analysis |
| `tests/` | Automated rule and reconciliation tests |
| `powerbi/` | Power BI semantic model and report assets |
| `excel/` | Exception-review and offline stakeholder packs |
| `reports/` | Published, non-sensitive report exports |

## Screenshot placeholders

| Executive quality scorecard | Reconciliation exception drill-through |
| --- | --- |
| `![Placeholder — scorecard](docs/images/quality-scorecard-placeholder.png)` | `![Placeholder — exception drill-through](docs/images/reconciliation-drillthrough-placeholder.png)` |

_Add approved, sanitized screenshots to `docs/images/` before replacing these placeholders._

## Working agreement

Raw data and report exports must not contain production personal data. Rule changes require a named Data Owner, a test, and a documented KPI impact. See the security and privacy requirements in the charter.

## Git workflow

The repository uses a local `post-commit` hook to push successful commits to `origin` automatically. It is enabled with `git config core.hooksPath .githooks`; network or authentication failures leave the commit intact and print a warning.
