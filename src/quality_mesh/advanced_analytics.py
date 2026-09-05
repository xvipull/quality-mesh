"""PySpark profiling and configurable data-quality rule engine.

Run after the base pipeline:
  PYTHONPATH=src python3 -m quality_mesh.advanced_analytics

The Spark workload reads clean CSVs, profiles columns distributively, evaluates
JSON-defined controls, writes governed Parquet outputs, and publishes concise
SQLite tables/views for BI consumption.
"""
from __future__ import annotations

import json
import os
import shutil
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

try:
    from pyspark.sql import DataFrame, SparkSession, functions as F
except ImportError:  # pragma: no cover - supports documentation-only environments
    DataFrame = Any  # type: ignore[misc,assignment]
    SparkSession = Any  # type: ignore[misc,assignment]
    F = None  # type: ignore[assignment]


def configure_java() -> None:
    """Use Homebrew's JDK when available without overriding a supplied JAVA_HOME."""
    if os.environ.get("JAVA_HOME"):
        return
    for candidate in (Path("/opt/homebrew/opt/openjdk@17"), Path("/usr/local/opt/openjdk@17")):
        if candidate.exists():
            os.environ["JAVA_HOME"] = str(candidate)
            os.environ["PATH"] = f"{candidate / 'bin'}:{os.environ.get('PATH', '')}"
            return


def spark_session() -> SparkSession:
    if F is None:
        raise RuntimeError("PySpark is required. Install dependencies with: python3 -m pip install -r requirements.txt")
    configure_java()
    return (SparkSession.builder.master("local[2]").appName("quality-mesh-advanced-analytics")
            .config("spark.ui.enabled", "false").config("spark.sql.session.timeZone", "UTC").getOrCreate())


def load_rules(path: Path) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding="utf-8"))
    required = {"rule_id", "dataset", "kind", "severity", "owner", "description"}
    rule_ids: set[str] = set()
    for rule in config["rules"]:
        absent = required - set(rule)
        if absent:
            raise ValueError(f"Rule missing fields {sorted(absent)}: {rule}")
        if rule["rule_id"] in rule_ids:
            raise ValueError(f"Duplicate rule ID: {rule['rule_id']}")
        if rule["severity"] not in {"CRITICAL", "HIGH", "MEDIUM", "LOW"}:
            raise ValueError(f"Invalid severity: {rule['severity']}")
        rule_ids.add(rule["rule_id"])
    return config


def profile_dataframe(dataframe: DataFrame, dataset: str, evaluated_at_utc: str) -> list[dict[str, Any]]:
    """Profile nulls, cardinality, and lexical bounds using distributed aggregations."""
    total_rows = dataframe.count()
    output: list[dict[str, Any]] = []
    for column in dataframe.columns:
        aggregate = dataframe.agg(
            F.sum(F.when(F.col(column).isNull() | (F.trim(F.col(column)) == ""), 1).otherwise(0)).alias("null_count"),
            F.countDistinct(F.col(column)).alias("distinct_count"),
            F.min(F.col(column)).alias("min_value"),
            F.max(F.col(column)).alias("max_value"),
        ).first()
        null_count = int(aggregate["null_count"] or 0)
        output.append({
            "dataset": dataset, "column_name": column, "row_count": total_rows,
            "null_count": null_count, "null_rate_pct": round(100 * null_count / total_rows, 4) if total_rows else 0.0,
            "distinct_count": int(aggregate["distinct_count"] or 0), "min_value": str(aggregate["min_value"] or ""),
            "max_value": str(aggregate["max_value"] or ""), "evaluated_at_utc": evaluated_at_utc,
        })
    return output


def evaluate_rule(rule: dict[str, Any], frames: dict[str, DataFrame], evaluation_day: date, evaluated_at_utc: str) -> dict[str, Any]:
    dataframe = frames[rule["dataset"]]
    total_rows = dataframe.count()
    if rule["kind"] == "expression":
        failed_rows = dataframe.where(~F.expr(rule["condition"])).count()
    elif rule["kind"] == "foreign_key":
        reference = frames[rule["reference_dataset"]].select(F.col(rule["reference_column"]).alias("reference_key")).distinct()
        failed_rows = dataframe.join(reference, dataframe[rule["column"]] == reference["reference_key"], "left_anti").count()
    elif rule["kind"] == "freshness":
        most_recent = dataframe.select(F.max(F.to_date(F.col(rule["column"]))).alias("maximum_date")).first()["maximum_date"]
        failed_rows = total_rows if most_recent is None or (evaluation_day - most_recent).days > int(rule["max_age_days"]) else 0
    else:
        raise ValueError(f"Unsupported rule kind: {rule['kind']}")
    failed_rate = round(100 * failed_rows / total_rows, 4) if total_rows else 100.0
    return {
        "rule_id": rule["rule_id"], "dataset": rule["dataset"], "severity": rule["severity"], "owner": rule["owner"],
        "description": rule["description"], "status": "PASS" if failed_rows == 0 else "FAIL", "evaluated_rows": total_rows,
        "failed_rows": failed_rows, "failed_rate_pct": failed_rate, "evaluated_at_utc": evaluated_at_utc,
    }


def publish_sqlite(db_path: Path, profiles: list[dict[str, Any]], results: list[dict[str, Any]], incidents: list[dict[str, Any]]) -> None:
    connection = sqlite3.connect(db_path)
    with connection:
        connection.executescript("""
          DROP TABLE IF EXISTS governed_column_profile;
          DROP TABLE IF EXISTS governed_rule_result;
          DROP TABLE IF EXISTS governed_incident;
          CREATE TABLE governed_column_profile (dataset TEXT, column_name TEXT, row_count INTEGER, null_count INTEGER, null_rate_pct REAL, distinct_count INTEGER, min_value TEXT, max_value TEXT, evaluated_at_utc TEXT);
          CREATE TABLE governed_rule_result (rule_id TEXT, dataset TEXT, severity TEXT, owner TEXT, description TEXT, status TEXT, evaluated_rows INTEGER, failed_rows INTEGER, failed_rate_pct REAL, evaluated_at_utc TEXT);
          CREATE TABLE governed_incident (incident_id TEXT PRIMARY KEY, rule_id TEXT, dataset TEXT, severity TEXT, owner TEXT, status TEXT, failed_rows INTEGER, opened_at_utc TEXT, deduplication_key TEXT UNIQUE);
          DROP VIEW IF EXISTS vw_governed_rule_status;
          CREATE VIEW vw_governed_rule_status AS SELECT severity, owner, status, COUNT(*) AS rule_count, SUM(failed_rows) AS failed_rows FROM governed_rule_result GROUP BY severity, owner, status;
          DROP VIEW IF EXISTS vw_open_data_incidents;
          CREATE VIEW vw_open_data_incidents AS SELECT * FROM governed_incident WHERE status = 'OPEN';
        """)
        connection.executemany("INSERT INTO governed_column_profile VALUES (:dataset, :column_name, :row_count, :null_count, :null_rate_pct, :distinct_count, :min_value, :max_value, :evaluated_at_utc)", profiles)
        connection.executemany("INSERT INTO governed_rule_result VALUES (:rule_id, :dataset, :severity, :owner, :description, :status, :evaluated_rows, :failed_rows, :failed_rate_pct, :evaluated_at_utc)", results)
        connection.executemany("INSERT INTO governed_incident VALUES (:incident_id, :rule_id, :dataset, :severity, :owner, :status, :failed_rows, :opened_at_utc, :deduplication_key)", incidents)
    connection.close()


def write_governed_parquet(spark: SparkSession, destination: Path, name: str, rows: list[dict[str, Any]]) -> None:
    output = destination / name
    shutil.rmtree(output, ignore_errors=True)
    spark.createDataFrame(rows).write.mode("overwrite").parquet(str(output))


def write_report(path: Path, profiles: list[dict[str, Any]], results: list[dict[str, Any]], incidents: list[dict[str, Any]]) -> None:
    passes = sum(result["status"] == "PASS" for result in results)
    lines = ["# Advanced Decision-Support Analytics Report", "", f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}", "", f"**{passes}/{len(results)} configured Spark rules passed; {len(incidents)} incidents generated.**", "", "## Rule outcomes", "", "| Rule | Severity | Owner | Status | Failed rows |", "| --- | --- | --- | --- | ---: |"]
    lines.extend(f"| {row['rule_id']} | {row['severity']} | {row['owner']} | {row['status']} | {row['failed_rows']} |" for row in results)
    lines.extend(["", "## Governed outputs", "", "- SQLite tables: `governed_column_profile`, `governed_rule_result`, and `governed_incident` in `data/quality_mesh.db`.", "- SQLite views: `vw_governed_rule_status` and `vw_open_data_incidents`.", "- Parquet publication: `data/governed/{column_profile,rule_result,incident}`.", "", "## Operational interpretation", "", "A failed rule opens one incident per rule, dataset, and evaluation date. The configured deduplication key prevents duplicate alerts within that cycle. Incidents are published as open records for stewardship workflow integration."])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_advanced_analytics(root: Path, evaluation_day: date | None = None) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    evaluation_day = evaluation_day or date.today()
    evaluated_at = datetime.now(timezone.utc).isoformat()
    config = load_rules(root / "config/quality_rules.json")
    spark = spark_session()
    try:
        frames = {name: spark.read.option("header", True).csv(str(root / "data/staging" / f"{name}_clean.csv")) for name in ("customers", "sales_orders", "gl_controls")}
        profiles = [item for name, frame in frames.items() for item in profile_dataframe(frame, name, evaluated_at)]
        results = [evaluate_rule(rule, frames, evaluation_day, evaluated_at) for rule in config["rules"]]
        incidents = []
        for result in results:
            if result["status"] in config["incident_policy"]["open_on_status"]:
                key = f"{result['rule_id']}|{result['dataset']}|{evaluation_day.isoformat()}"
                incidents.append({"incident_id": f"INC-{result['rule_id']}-{evaluation_day.strftime('%Y%m%d')}", "rule_id": result["rule_id"], "dataset": result["dataset"], "severity": result["severity"], "owner": result["owner"], "status": "OPEN", "failed_rows": result["failed_rows"], "opened_at_utc": evaluated_at, "deduplication_key": key})
        governed = root / "data/governed"
        write_governed_parquet(spark, governed, "column_profile", profiles)
        write_governed_parquet(spark, governed, "rule_result", results)
        if incidents:
            write_governed_parquet(spark, governed, "incident", incidents)
        else:
            shutil.rmtree(governed / "incident", ignore_errors=True)
        publish_sqlite(root / "data/quality_mesh.db", profiles, results, incidents)
        write_report(root / "reports/advanced_analytics_report.md", profiles, results, incidents)
        return profiles, results, incidents
    finally:
        spark.stop()


if __name__ == "__main__":
    repository_root = Path(__file__).resolve().parents[2]
    profile_rows, rule_rows, incident_rows = run_advanced_analytics(repository_root)
    print(f"Advanced analytics complete: {len(profile_rows)} column profiles, {len(rule_rows)} rules, {len(incident_rows)} incidents")
