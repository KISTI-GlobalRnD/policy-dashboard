#!/usr/bin/env python3
"""Initialize the SQLite ontology store and optionally load seed CSVs."""

from __future__ import annotations

import argparse
import csv
import sqlite3
from pathlib import Path


SEED_FILES = {
    "resource_categories.csv": "resource_categories",
    "policy_master.csv": "policies",
    "documents_seed.csv": "documents",
    "policy_bucket_master.csv": "policy_buckets",
    "strategies_seed.csv": "strategies",
}


def load_csv_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def create_database(db_path: Path, schema_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    with schema_path.open(encoding="utf-8") as handle:
        connection.executescript(handle.read())
    return connection


def load_seed_file(connection: sqlite3.Connection, csv_path: Path, table_name: str) -> None:
    fieldnames, rows = load_csv_rows(csv_path)
    if not fieldnames or not rows:
        return
    placeholders = ", ".join("?" for _ in fieldnames)
    columns = ", ".join(fieldnames)
    sql = f"INSERT OR REPLACE INTO {table_name} ({columns}) VALUES ({placeholders})"
    payload = []
    for row in rows:
        values = []
        for name in fieldnames:
            value = row[name]
            if table_name == "documents" and name == "policy_id" and value == "":
                value = None
            values.append(value)
        payload.append(tuple(values))
    connection.executemany(sql, payload)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", required=True)
    parser.add_argument("--schema-path", required=True)
    parser.add_argument("--seed-dir")
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()

    db_path = Path(args.db_path)
    schema_path = Path(args.schema_path)
    if db_path.exists() and not args.replace:
        raise FileExistsError(f"Database already exists: {db_path}")
    if db_path.exists() and args.replace:
        db_path.unlink()

    connection = create_database(db_path, schema_path)
    try:
        if args.seed_dir:
            seed_dir = Path(args.seed_dir)
            for filename, table_name in SEED_FILES.items():
                csv_path = seed_dir / filename
                if csv_path.exists():
                    load_seed_file(connection, csv_path, table_name)
        connection.commit()
    finally:
        connection.close()


if __name__ == "__main__":
    main()
