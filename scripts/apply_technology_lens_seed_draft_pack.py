#!/usr/bin/env python3
"""Apply a generated technology lens draft pack into the ontology store."""

from __future__ import annotations

import argparse
import csv
import json
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


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


AUTO_CURATED_GROUP_STATUSES = ("auto_seed_curated", "auto_expand_curated")
AUTO_CURATED_CONTENT_STATUSES = ("auto_seed_curated", "auto_expand_curated")


def query_auto_curated_stats(connection: sqlite3.Connection) -> dict[str, object]:
    group_rows = connection.execute(
        """
        SELECT group_status, COUNT(*)
        FROM policy_item_groups
        WHERE group_status IN (?, ?)
        GROUP BY group_status
        ORDER BY group_status
        """,
        AUTO_CURATED_GROUP_STATUSES,
    ).fetchall()
    content_rows = connection.execute(
        """
        SELECT content_status, COUNT(*)
        FROM policy_item_contents
        WHERE content_status IN (?, ?)
        GROUP BY content_status
        ORDER BY content_status
        """,
        AUTO_CURATED_CONTENT_STATUSES,
    ).fetchall()
    domain_rows = connection.execute(
        """
        SELECT DISTINCT pitm.term_id, td.tech_domain_label
        FROM policy_item_group_taxonomy_map pitm
        JOIN policy_item_groups pig
          ON pig.policy_item_group_id = pitm.policy_item_group_id
        LEFT JOIN tech_domains td
          ON td.tech_domain_id = pitm.term_id
        WHERE pig.group_status IN (?, ?)
          AND pitm.taxonomy_type = 'tech_domain'
          AND pitm.is_primary = 1
          AND pitm.review_status = 'reviewed'
        ORDER BY pitm.term_id
        """
        ,
        AUTO_CURATED_GROUP_STATUSES,
    ).fetchall()
    group_counts = {row[0]: row[1] for row in group_rows}
    content_counts = {row[0]: row[1] for row in content_rows}
    return {
        "auto_curated_group_counts": group_counts,
        "auto_curated_group_count": sum(group_counts.values()),
        "auto_curated_content_counts": content_counts,
        "auto_curated_content_count": sum(content_counts.values()),
        "auto_curated_domains": [
            {
                "tech_domain_id": row[0],
                "tech_domain_label": row[1] or "",
            }
            for row in domain_rows
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", required=True)
    parser.add_argument("--draft-pack-dir", required=True)
    parser.add_argument("--out-summary-json", required=True)
    args = parser.parse_args()

    draft_pack_dir = Path(args.draft_pack_dir)
    connection = sqlite3.connect(args.db_path)
    try:
        for _, table_name in LOAD_ORDER:
            if not table_exists(connection, table_name):
                raise RuntimeError(f"Missing table in ontology store: {table_name}")

        before_stats = query_auto_curated_stats(connection)
        loaded_row_counts: dict[str, int] = {}
        loaded_file_counts: dict[str, int] = {}

        for filename, table_name in LOAD_ORDER:
            csv_path = draft_pack_dir / filename
            if not csv_path.exists():
                raise FileNotFoundError(csv_path)
            fieldnames, rows = load_csv(csv_path)
            loaded_file_counts[filename] = len(rows)
            if not fieldnames or not rows:
                loaded_row_counts[table_name] = 0
                continue
            placeholders = ", ".join("?" for _ in fieldnames)
            columns = ", ".join(fieldnames)
            sql = f"INSERT OR REPLACE INTO {table_name} ({columns}) VALUES ({placeholders})"
            payload = [tuple(row[name] for name in fieldnames) for row in rows]
            connection.executemany(sql, payload)
            loaded_row_counts[table_name] = len(payload)
        connection.commit()

        after_stats = query_auto_curated_stats(connection)
    finally:
        connection.close()

    summary = {
        "status": "applied",
        "db_path": args.db_path,
        "draft_pack_dir": str(draft_pack_dir),
        "loaded_file_counts": loaded_file_counts,
        "loaded_row_counts": loaded_row_counts,
        "auto_curated_group_counts_before": before_stats["auto_curated_group_counts"],
        "auto_curated_group_counts_after": after_stats["auto_curated_group_counts"],
        "auto_curated_group_count_before": before_stats["auto_curated_group_count"],
        "auto_curated_group_count_after": after_stats["auto_curated_group_count"],
        "auto_curated_group_count_delta": after_stats["auto_curated_group_count"] - before_stats["auto_curated_group_count"],
        "auto_curated_content_counts_before": before_stats["auto_curated_content_counts"],
        "auto_curated_content_counts_after": after_stats["auto_curated_content_counts"],
        "auto_curated_content_count_before": before_stats["auto_curated_content_count"],
        "auto_curated_content_count_after": after_stats["auto_curated_content_count"],
        "auto_curated_content_count_delta": after_stats["auto_curated_content_count"] - before_stats["auto_curated_content_count"],
        "auto_curated_domain_count_after": len(after_stats["auto_curated_domains"]),
        "auto_curated_domains_after": after_stats["auto_curated_domains"],
    }
    write_json(Path(args.out_summary_json), summary)
    print("technology_lens_draft_pack_applied")


if __name__ == "__main__":
    main()
