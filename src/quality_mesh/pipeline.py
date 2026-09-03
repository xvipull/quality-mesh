"""Clean, validate, model, and report the Sales Orders pilot dataset.

Run from the repository root with: PYTHONPATH=src python -m quality_mesh.pipeline
Only Python's standard library is used so the sample is portable.
"""
from __future__ import annotations

import csv
import json
import sqlite3
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

REQUIRED = {
    "customers": ["customer_id", "customer_name", "segment", "status", "created_date"],
    "sales_orders": ["order_id", "customer_id", "order_date", "order_amount", "currency", "category"],
    "gl_controls": ["control_date", "source_system", "order_count", "order_amount", "currency"],
}
NULL_THRESHOLDS = {"customers": 0.0, "sales_orders": 0.0, "gl_controls": 0.0}
VALID_SEGMENTS = {"ENTERPRISE", "SMB", "MID_MARKET"}
VALID_CATEGORIES = {"ONLINE", "WHOLESALE", "RETAIL"}
VALID_STATUS = {"ACTIVE", "INACTIVE"}
VALID_CURRENCIES = {"USD"}


def normalize_key(value: str) -> str:
    """Create canonical business keys: uppercase alphanumeric with no separators."""
    return "".join(character for character in value.strip().upper() if character.isalnum())


def normalize_enum(value: str) -> str:
    return value.strip().upper().replace("-", "_").replace(" ", "_")


def parse_date(value: str) -> str:
    for pattern in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(value.strip(), pattern).date().isoformat()
        except ValueError:
            pass
    raise ValueError(f"Unsupported date: {value!r}")


def parse_amount(value: str) -> Decimal:
    try:
        return Decimal(value.strip().replace(",", "")).quantize(Decimal("0.01"))
    except (InvalidOperation, AttributeError) as error:
        raise ValueError(f"Invalid amount: {value!r}") from error


def read_csv(path: Path, dataset: str) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or set(REQUIRED[dataset]) - set(reader.fieldnames):
            missing = sorted(set(REQUIRED[dataset]) - set(reader.fieldnames or []))
            raise ValueError(f"{dataset} missing required columns: {missing}")
        return list(reader)


def clean_customers(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    cleaned = []
    for row in rows:
        cleaned.append({
            "customer_id": normalize_key(row["customer_id"]),
            "customer_name": row["customer_name"].strip(),
            "segment": normalize_enum(row["segment"]),
            "status": normalize_enum(row["status"]),
            "created_date": parse_date(row["created_date"]),
        })
    return cleaned


def clean_orders(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    cleaned = []
    for row in rows:
        cleaned.append({
            "order_id": normalize_key(row["order_id"]),
            "customer_id": normalize_key(row["customer_id"]),
            "order_date": parse_date(row["order_date"]),
            "order_amount": f"{parse_amount(row['order_amount']):.2f}",
            "currency": row["currency"].strip().upper(),
            "category": normalize_enum(row["category"]),
        })
    return cleaned


def clean_controls(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    cleaned = []
    for row in rows:
        cleaned.append({
            "control_date": parse_date(row["control_date"]),
            "source_system": row["source_system"].strip().upper(),
            "order_count": str(int(row["order_count"])),
            "order_amount": f"{parse_amount(row['order_amount']):.2f}",
            "currency": row["currency"].strip().upper(),
        })
    return cleaned


def duplicate_count(rows: list[dict[str, str]], key: str) -> int:
    values = [row[key] for row in rows]
    return len(values) - len(set(values))


def validate(clean: dict[str, list[dict[str, str]]], raw: dict[str, list[dict[str, str]]], raw_dir: Path) -> list[dict[str, Any]]:
    """Return an auditable set of automated check outcomes."""
    checks: list[dict[str, Any]] = []

    def add(check_id: str, status: str, observed: Any, expected: str, detail: str) -> None:
        checks.append({"check_id": check_id, "status": status, "observed": str(observed), "expected": expected, "detail": detail})

    for dataset, columns in REQUIRED.items():
        add(f"REQ_{dataset.upper()}", "PASS", ", ".join(columns), "all required columns present", "Validated at ingestion")
        nulls = sum(1 for row in clean[dataset] for column in columns if not row[column])
        limit = NULL_THRESHOLDS[dataset] * len(clean[dataset]) * len(columns)
        add(f"NULL_{dataset.upper()}", "PASS" if nulls <= limit else "FAIL", nulls, f"<= {limit:g}", "Required-field null values")

    for dataset, key in (("customers", "customer_id"), ("sales_orders", "order_id")):
        duplicates = duplicate_count(clean[dataset], key)
        add(f"DUP_{dataset.upper()}", "PASS" if duplicates == 0 else "FAIL", duplicates, "0", f"Duplicate {key} values")

    invalid_orders = sum(1 for row in clean["sales_orders"] if not (Decimal("0") < Decimal(row["order_amount"]) <= Decimal("1000000")))
    add("RANGE_ORDER_AMOUNT", "PASS" if invalid_orders == 0 else "FAIL", invalid_orders, "0", "Amount must be > 0 and <= 1,000,000")
    invalid_enums = sum(row["segment"] not in VALID_SEGMENTS or row["status"] not in VALID_STATUS for row in clean["customers"])
    invalid_enums += sum(row["category"] not in VALID_CATEGORIES or row["currency"] not in VALID_CURRENCIES for row in clean["sales_orders"])
    add("VALID_ENUMS", "PASS" if invalid_enums == 0 else "FAIL", invalid_enums, "0", "Approved segment, status, category, and currency values")

    customer_keys = {row["customer_id"] for row in clean["customers"]}
    orphan_orders = sum(row["customer_id"] not in customer_keys for row in clean["sales_orders"])
    add("FK_ORDER_CUSTOMER", "PASS" if orphan_orders == 0 else "FAIL", orphan_orders, "0", "Every order customer exists in customer master")

    today = date.today()
    stale = []
    for path in raw_dir.glob("*.csv"):
        age_days = (today - datetime.fromtimestamp(path.stat().st_mtime).date()).days
        stale.append((path.name, age_days))
    maximum_age = max(age for _, age in stale)
    add("FRESH_RAW_EXTRACTS", "PASS" if maximum_age <= 7 else "FAIL", f"{maximum_age} days", "<= 7 days", json.dumps(stale))

    raw_order_count, clean_order_count = len(raw["sales_orders"]), len(clean["sales_orders"])
    add("RECON_ROW_COUNT", "PASS" if raw_order_count == clean_order_count else "FAIL", clean_order_count, str(raw_order_count), "Raw-to-clean sales order count")
    fact_count = sum(int(row["order_count"]) for row in clean["gl_controls"])
    fact_value = sum((Decimal(row["order_amount"]) for row in clean["sales_orders"]), Decimal("0"))
    control_value = sum((Decimal(row["order_amount"]) for row in clean["gl_controls"]), Decimal("0"))
    add("RECON_ORDER_COUNT", "PASS" if clean_order_count == fact_count else "FAIL", clean_order_count, str(fact_count), "Sales orders versus GL control count")
    add("RECON_ORDER_VALUE", "PASS" if fact_value == control_value else "FAIL", f"{fact_value:.2f}", f"{control_value:.2f}", "Sales orders versus GL control amount")
    return checks


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def load_model(db_path: Path, clean: dict[str, list[dict[str, str]]], checks: list[dict[str, Any]]) -> None:
    db_path.unlink(missing_ok=True)
    connection = sqlite3.connect(db_path)
    with connection:
        connection.executescript("""
        PRAGMA foreign_keys = ON;
        CREATE TABLE dim_date (date_key INTEGER PRIMARY KEY, calendar_date TEXT NOT NULL UNIQUE, year INTEGER NOT NULL, month INTEGER NOT NULL, day INTEGER NOT NULL);
        CREATE TABLE dim_customer (customer_key INTEGER PRIMARY KEY, customer_id TEXT NOT NULL UNIQUE, customer_name TEXT NOT NULL, segment TEXT NOT NULL, status TEXT NOT NULL, created_date TEXT NOT NULL);
        CREATE TABLE dim_category (category_key INTEGER PRIMARY KEY, category_code TEXT NOT NULL UNIQUE);
        CREATE TABLE fact_sales_order (order_key INTEGER PRIMARY KEY, order_id TEXT NOT NULL UNIQUE, customer_key INTEGER NOT NULL, order_date_key INTEGER NOT NULL, category_key INTEGER NOT NULL, order_amount REAL NOT NULL, currency_code TEXT NOT NULL, FOREIGN KEY(customer_key) REFERENCES dim_customer(customer_key), FOREIGN KEY(order_date_key) REFERENCES dim_date(date_key), FOREIGN KEY(category_key) REFERENCES dim_category(category_key));
        CREATE TABLE fact_reconciliation_control (control_key INTEGER PRIMARY KEY, control_date_key INTEGER NOT NULL, source_system TEXT NOT NULL, order_count INTEGER NOT NULL, order_amount REAL NOT NULL, currency_code TEXT NOT NULL, FOREIGN KEY(control_date_key) REFERENCES dim_date(date_key));
        CREATE TABLE dq_check_result (check_id TEXT PRIMARY KEY, status TEXT NOT NULL, observed TEXT NOT NULL, expected TEXT NOT NULL, detail TEXT NOT NULL, evaluated_at_utc TEXT NOT NULL);
        """)
        dates = sorted({row["order_date"] for row in clean["sales_orders"]} | {row["control_date"] for row in clean["gl_controls"]})
        for calendar_date in dates:
            parsed = date.fromisoformat(calendar_date)
            connection.execute("INSERT INTO dim_date VALUES (?, ?, ?, ?, ?)", (int(parsed.strftime("%Y%m%d")), calendar_date, parsed.year, parsed.month, parsed.day))
        for row in clean["customers"]:
            connection.execute("INSERT INTO dim_customer (customer_id, customer_name, segment, status, created_date) VALUES (?, ?, ?, ?, ?)", tuple(row.values()))
        for category in sorted({row["category"] for row in clean["sales_orders"]}):
            connection.execute("INSERT INTO dim_category (category_code) VALUES (?)", (category,))
        customer_keys = dict(connection.execute("SELECT customer_id, customer_key FROM dim_customer"))
        category_keys = dict(connection.execute("SELECT category_code, category_key FROM dim_category"))
        for row in clean["sales_orders"]:
            connection.execute("INSERT INTO fact_sales_order (order_id, customer_key, order_date_key, category_key, order_amount, currency_code) VALUES (?, ?, ?, ?, ?, ?)", (row["order_id"], customer_keys[row["customer_id"]], int(row["order_date"].replace("-", "")), category_keys[row["category"]], float(row["order_amount"]), row["currency"]))
        for row in clean["gl_controls"]:
            connection.execute("INSERT INTO fact_reconciliation_control (control_date_key, source_system, order_count, order_amount, currency_code) VALUES (?, ?, ?, ?, ?)", (int(row["control_date"].replace("-", "")), row["source_system"], int(row["order_count"]), float(row["order_amount"]), row["currency"]))
        evaluated_at = datetime.now(timezone.utc).isoformat()
        connection.executemany("INSERT INTO dq_check_result VALUES (?, ?, ?, ?, ?, ?)", [(check["check_id"], check["status"], check["observed"], check["expected"], check["detail"], evaluated_at) for check in checks])
    connection.close()


def write_report(path: Path, checks: list[dict[str, Any]], clean: dict[str, list[dict[str, str]]]) -> None:
    passed = sum(check["status"] == "PASS" for check in checks)
    lines = ["# Data Quality Report", "", f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}", "", "## Result", "", f"**{passed}/{len(checks)} checks passed.**", "", "## Dataset volumes", "", "| Dataset | Raw rows | Clean rows |", "| --- | ---: | ---: |"]
    for dataset, rows in clean.items():
        lines.append(f"| {dataset} | {len(rows)} | {len(rows)} |")
    lines.extend(["", "## Control results", "", "| Check | Status | Observed | Expected | Detail |", "| --- | --- | --- | --- | --- |"])
    lines.extend(f"| {check['check_id']} | {check['status']} | {check['observed']} | {check['expected']} | {check['detail']} |" for check in checks)
    lines.extend(["", "## Notes", "", "All samples use synthetic, non-sensitive records. Freshness is evaluated from raw-file modification time and requires files no more than seven calendar days old."])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_pipeline(root: Path) -> list[dict[str, Any]]:
    raw_dir, staging_dir = root / "data/raw", root / "data/staging"
    raw = {name: read_csv(raw_dir / f"{name}.csv", name) for name in REQUIRED}
    clean = {"customers": clean_customers(raw["customers"]), "sales_orders": clean_orders(raw["sales_orders"]), "gl_controls": clean_controls(raw["gl_controls"])}
    checks = validate(clean, raw, raw_dir)
    if any(check["status"] == "FAIL" for check in checks):
        raise ValueError("Data quality controls failed; database was not loaded.")
    for dataset, rows in clean.items():
        write_csv(staging_dir / f"{dataset}_clean.csv", rows)
    load_model(root / "data/quality_mesh.db", clean, checks)
    write_report(root / "reports/data_quality_report.md", checks, clean)
    return checks


if __name__ == "__main__":
    repository_root = Path(__file__).resolve().parents[2]
    results = run_pipeline(repository_root)
    print(f"Pipeline complete: {sum(item['status'] == 'PASS' for item in results)}/{len(results)} checks passed")
