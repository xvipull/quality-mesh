"""Purposeful exploratory analysis for the Sales Orders pilot.

Run after the data pipeline: PYTHONPATH=src python3 -m quality_mesh.eda
The script uses Pandas/NumPy for analysis and Matplotlib for two report-ready charts.
"""
from __future__ import annotations

import sqlite3
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).resolve().parents[2] / ".cache" / "matplotlib"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def run_eda(root: Path) -> dict[str, float]:
    db_path = root / "data/quality_mesh.db"
    report_dir = root / "reports"
    figure_dir = report_dir / "figures"
    figure_dir.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as connection:
        orders = pd.read_sql_query("""
            SELECT f.order_id, d.calendar_date AS order_date, c.segment, g.category_code AS category,
                   f.order_amount, f.currency_code
            FROM fact_sales_order f
            JOIN dim_date d ON d.date_key = f.order_date_key
            JOIN dim_customer c ON c.customer_key = f.customer_key
            JOIN dim_category g ON g.category_key = f.category_key
        """, connection)
        quality = pd.read_sql_query("SELECT * FROM dq_check_result", connection)

    numeric = orders[["order_amount"]]
    missing = orders.isna().sum()
    q1, q3 = np.percentile(orders["order_amount"], [25, 75])
    iqr = q3 - q1
    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    outlier_count = int(((orders["order_amount"] < lower) | (orders["order_amount"] > upper)).sum())
    correlations = numeric.corr(numeric_only=True).round(3)
    by_category = orders.groupby("category", as_index=False).agg(revenue_usd=("order_amount", "sum"), orders=("order_id", "count")).sort_values("revenue_usd", ascending=False)
    by_segment = orders.groupby("segment", as_index=False).agg(revenue_usd=("order_amount", "sum"), orders=("order_id", "count")).sort_values("revenue_usd", ascending=False)

    plt.style.use("seaborn-v0_8-whitegrid")
    fig, axis = plt.subplots(figsize=(7, 4.25))
    axis.bar(by_category["category"], by_category["revenue_usd"], color="#177E89")
    axis.set(title="Revenue by Sales Category", xlabel="Category", ylabel="Revenue (USD)")
    for index, value in enumerate(by_category["revenue_usd"]):
        axis.text(index, value, f"${value:,.0f}", ha="center", va="bottom")
    fig.tight_layout()
    fig.savefig(figure_dir / "revenue_by_category.png", dpi=160)
    plt.close(fig)

    fig, axis = plt.subplots(figsize=(7, 4.25))
    axis.hist(orders["order_amount"], bins=min(6, len(orders)), color="#D1495B", edgecolor="white")
    axis.axvline(orders["order_amount"].median(), color="#1D3557", linestyle="--", label=f"Median ${orders['order_amount'].median():,.2f}")
    axis.set(title="Sales Order Value Distribution", xlabel="Order amount (USD)", ylabel="Number of orders")
    axis.legend()
    fig.tight_layout()
    fig.savefig(figure_dir / "order_value_distribution.png", dpi=160)
    plt.close(fig)

    summary = [
        "# Exploratory Data Analysis", "",
        "## Scope", "", "Analysis uses the cleaned Sales Orders star schema and synthetic pilot data. Two charts are retained because they directly support category prioritization and order-value monitoring.", "",
        "## Findings", "",
        f"- **Volume and value:** {len(orders)} orders total **${orders['order_amount'].sum():,.2f}**; median order value is **${orders['order_amount'].median():,.2f}**.",
        f"- **Missingness:** {int(missing.sum())} missing values across {len(orders.columns)} analyzed fields.",
        f"- **Outliers:** {outlier_count} IQR outliers; calculated boundaries are ${lower:,.2f} to ${upper:,.2f}.",
        f"- **Quality controls:** {(quality['status'] == 'PASS').sum()}/{len(quality)} persisted controls pass.",
        "- **Correlation:** Only one numeric analytical measure exists in this pilot, so a correlation matrix would be non-informative; it is calculated programmatically but not charted.", "",
        "## Business drivers", "",
        "| Segment | Orders | Revenue (USD) |", "| --- | ---: | ---: |",
    ]
    summary.extend(f"| {row.segment} | {row.orders} | ${row.revenue_usd:,.2f} |" for row in by_segment.itertuples(index=False))
    summary.extend(["", "## Generated figures", "", "- `reports/figures/revenue_by_category.png` — directs category-level commercial investigation.", "- `reports/figures/order_value_distribution.png` — exposes value concentration and potential outliers.", "", "## Reproducibility", "", "`PYTHONPATH=src python3 -m quality_mesh.eda`"])
    (report_dir / "eda_summary.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    return {"orders": float(len(orders)), "outliers": float(outlier_count), "correlation_dimensions": float(correlations.shape[0])}


if __name__ == "__main__":
    repository_root = Path(__file__).resolve().parents[2]
    print(run_eda(repository_root))
