#!/usr/bin/env python3
"""Load curated content-evidence sample CSVs into the ontology store."""

from __future__ import annotations

import argparse
import csv
import sqlite3
from pathlib import Path


LOAD_ORDER = [
    ("policy_item_groups_sample.csv", "policy_item_groups"),
    ("policy_item_group_members_sample.csv", "policy_item_group_members"),
    ("policy_item_contents_sample.csv", "policy_item_contents"),
    ("policy_item_content_evidence_links_sample.csv", "policy_item_content_evidence_links"),
    ("policy_item_group_taxonomy_map_sample.csv", "policy_item_group_taxonomy_map"),
    ("display_texts_curated_sample.csv", "display_texts"),
]


def table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    row = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def load_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", required=True)
    parser.add_argument("--sample-dir", required=True)
    args = parser.parse_args()

    sample_dir = Path(args.sample_dir)
    connection = sqlite3.connect(args.db_path)
    try:
        for _, table_name in LOAD_ORDER:
            if not table_exists(connection, table_name):
                raise RuntimeError(f"Missing table in ontology store: {table_name}")

        for filename, table_name in LOAD_ORDER:
            csv_path = sample_dir / filename
            if not csv_path.exists():
                raise FileNotFoundError(csv_path)
            fieldnames, rows = load_csv(csv_path)
            if not fieldnames or not rows:
                continue
            placeholders = ", ".join("?" for _ in fieldnames)
            columns = ", ".join(fieldnames)
            sql = f"INSERT OR REPLACE INTO {table_name} ({columns}) VALUES ({placeholders})"
            payload = [tuple(row[name] for name in fieldnames) for row in rows]
            connection.executemany(sql, payload)
        connection.commit()
    finally:
        connection.close()

    print("curated_content_sample_loaded")


if __name__ == "__main__":
    main()
