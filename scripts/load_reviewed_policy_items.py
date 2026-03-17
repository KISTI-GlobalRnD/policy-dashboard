#!/usr/bin/env python3
"""Load reviewed policy-item CSVs into the ontology store."""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from pathlib import Path


CSV_TABLE_ORDER = [
    ("policy-items-reviewed.csv", "policy_items"),
    ("display-texts-reviewed.csv", "display_texts"),
    ("policy-item-evidence-links-reviewed.csv", "policy_item_evidence_links"),
    ("policy-item-taxonomy-map-reviewed.csv", "policy_item_taxonomy_map"),
    ("derived-to-display-map-reviewed.csv", "derived_to_display_map"),
]


def read_csv_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def placeholders(values: list[str]) -> str:
    return ", ".join("?" for _ in values)


def existing_policy_items_for_document(connection: sqlite3.Connection, document_id: str) -> list[str]:
    rows = connection.execute(
        """
        SELECT DISTINCT pi.policy_item_id
        FROM policy_items pi
        JOIN policy_item_evidence_links piel
          ON piel.policy_item_id = pi.policy_item_id
        JOIN derived_representations dr
          ON dr.derived_representation_id = piel.derived_representation_id
        WHERE dr.document_id = ?
        ORDER BY pi.policy_item_id
        """,
        (document_id,),
    ).fetchall()
    return [row[0] for row in rows]


def referenced_group_member_ids(connection: sqlite3.Connection, policy_item_ids: list[str]) -> list[str]:
    if not policy_item_ids:
        return []
    rows = connection.execute(
        f"""
        SELECT DISTINCT policy_item_id
        FROM policy_item_group_members
        WHERE policy_item_id IN ({placeholders(policy_item_ids)})
        ORDER BY policy_item_id
        """,
        tuple(policy_item_ids),
    ).fetchall()
    return [row[0] for row in rows]


def delete_policy_item_slice(connection: sqlite3.Connection, policy_item_ids: list[str]) -> dict[str, int]:
    if not policy_item_ids:
        return {
            "deleted_policy_item_count": 0,
            "deleted_display_text_count": 0,
            "deleted_evidence_link_count": 0,
            "deleted_taxonomy_row_count": 0,
            "deleted_assertion_count": 0,
            "deleted_data_quality_flag_count": 0,
            "deleted_derived_to_display_count": 0,
        }

    display_text_rows = connection.execute(
        f"""
        SELECT display_text_id
        FROM display_texts
        WHERE target_object_type = 'policy_item'
          AND target_object_id IN ({placeholders(policy_item_ids)})
        ORDER BY display_text_id
        """,
        tuple(policy_item_ids),
    ).fetchall()
    display_text_ids = [row[0] for row in display_text_rows]

    deleted_derived_to_display_count = 0
    if display_text_ids:
        cursor = connection.execute(
            f"""
            DELETE FROM derived_to_display_map
            WHERE display_text_id IN ({placeholders(display_text_ids)})
            """,
            tuple(display_text_ids),
        )
        deleted_derived_to_display_count = cursor.rowcount

    deleted_display_text_count = connection.execute(
        f"""
        DELETE FROM display_texts
        WHERE target_object_type = 'policy_item'
          AND target_object_id IN ({placeholders(policy_item_ids)})
        """,
        tuple(policy_item_ids),
    ).rowcount
    deleted_taxonomy_row_count = connection.execute(
        f"""
        DELETE FROM policy_item_taxonomy_map
        WHERE policy_item_id IN ({placeholders(policy_item_ids)})
        """,
        tuple(policy_item_ids),
    ).rowcount
    deleted_assertion_count = connection.execute(
        f"""
        DELETE FROM curation_assertions
        WHERE target_object_type = 'policy_item'
          AND target_object_id IN ({placeholders(policy_item_ids)})
        """,
        tuple(policy_item_ids),
    ).rowcount
    deleted_data_quality_flag_count = connection.execute(
        f"""
        DELETE FROM data_quality_flags
        WHERE target_object_type = 'policy_item'
          AND target_object_id IN ({placeholders(policy_item_ids)})
        """,
        tuple(policy_item_ids),
    ).rowcount
    deleted_evidence_link_count = connection.execute(
        f"""
        DELETE FROM policy_item_evidence_links
        WHERE policy_item_id IN ({placeholders(policy_item_ids)})
        """,
        tuple(policy_item_ids),
    ).rowcount
    deleted_policy_item_count = connection.execute(
        f"""
        DELETE FROM policy_items
        WHERE policy_item_id IN ({placeholders(policy_item_ids)})
        """,
        tuple(policy_item_ids),
    ).rowcount

    return {
        "deleted_policy_item_count": deleted_policy_item_count,
        "deleted_display_text_count": deleted_display_text_count,
        "deleted_evidence_link_count": deleted_evidence_link_count,
        "deleted_taxonomy_row_count": deleted_taxonomy_row_count,
        "deleted_assertion_count": deleted_assertion_count,
        "deleted_data_quality_flag_count": deleted_data_quality_flag_count,
        "deleted_derived_to_display_count": deleted_derived_to_display_count,
    }


def load_rows(connection: sqlite3.Connection, csv_path: Path, table_name: str) -> int:
    fieldnames, rows = read_csv_rows(csv_path)
    if not fieldnames or not rows:
        return 0
    sql = f"INSERT OR REPLACE INTO {table_name} ({', '.join(fieldnames)}) VALUES ({', '.join('?' for _ in fieldnames)})"
    connection.executemany(sql, [tuple(row[name] for name in fieldnames) for row in rows])
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", required=True)
    parser.add_argument("--reviewed-items-dir", required=True)
    parser.add_argument("--documents", nargs="*")
    parser.add_argument("--out-summary-json", required=True)
    parser.add_argument("--out-summary-csv")
    args = parser.parse_args()

    reviewed_items_dir = Path(args.reviewed_items_dir)
    if args.documents:
        documents = args.documents
    else:
        documents = sorted(
            path.name.replace("__policy-items-reviewed.csv", "")
            for path in reviewed_items_dir.glob("*__policy-items-reviewed.csv")
        )

    connection = sqlite3.connect(args.db_path)
    try:
        rows: list[dict[str, object]] = []
        for document_id in documents:
            file_paths = {
                suffix: reviewed_items_dir / f"{document_id}__{suffix}"
                for suffix, _ in CSV_TABLE_ORDER
            }
            summary_path = reviewed_items_dir / f"{document_id}__reviewed-items-summary.json"
            summary_payload = {}
            if summary_path.exists():
                summary_payload = json.loads(summary_path.read_text(encoding="utf-8"))

            if not file_paths["policy-items-reviewed.csv"].exists():
                rows.append(
                    {
                        "document_id": document_id,
                        "run_status": "skipped_missing_reviewed_items",
                        "loaded_policy_item_count": 0,
                        "loaded_display_text_count": 0,
                        "loaded_evidence_link_count": 0,
                        "loaded_taxonomy_row_count": 0,
                        "loaded_derived_to_display_count": 0,
                        "deleted_policy_item_count": 0,
                        "deleted_display_text_count": 0,
                        "deleted_evidence_link_count": 0,
                        "deleted_taxonomy_row_count": 0,
                        "deleted_assertion_count": 0,
                        "deleted_data_quality_flag_count": 0,
                        "deleted_derived_to_display_count": 0,
                        "notes": "missing reviewed policy item csv",
                    }
                )
                continue

            if summary_payload and summary_payload.get("run_status") == "no_reviewed_rows":
                rows.append(
                    {
                        "document_id": document_id,
                        "run_status": "skipped_no_reviewed_rows",
                        "loaded_policy_item_count": 0,
                        "loaded_display_text_count": 0,
                        "loaded_evidence_link_count": 0,
                        "loaded_taxonomy_row_count": 0,
                        "loaded_derived_to_display_count": 0,
                        "deleted_policy_item_count": 0,
                        "deleted_display_text_count": 0,
                        "deleted_evidence_link_count": 0,
                        "deleted_taxonomy_row_count": 0,
                        "deleted_assertion_count": 0,
                        "deleted_data_quality_flag_count": 0,
                        "deleted_derived_to_display_count": 0,
                        "notes": "reviewed export summary reports no reviewed rows",
                    }
                )
                continue

            existing_policy_item_ids = existing_policy_items_for_document(connection, document_id)
            referenced_group_ids = referenced_group_member_ids(connection, existing_policy_item_ids)
            if referenced_group_ids:
                rows.append(
                    {
                        "document_id": document_id,
                        "run_status": "failed_group_reference",
                        "loaded_policy_item_count": 0,
                        "loaded_display_text_count": 0,
                        "loaded_evidence_link_count": 0,
                        "loaded_taxonomy_row_count": 0,
                        "loaded_derived_to_display_count": 0,
                        "deleted_policy_item_count": 0,
                        "deleted_display_text_count": 0,
                        "deleted_evidence_link_count": 0,
                        "deleted_taxonomy_row_count": 0,
                        "deleted_assertion_count": 0,
                        "deleted_data_quality_flag_count": 0,
                        "deleted_derived_to_display_count": 0,
                        "notes": f"policy items still referenced by groups: {referenced_group_ids[:10]}",
                    }
                )
                continue

            try:
                delete_counts = delete_policy_item_slice(connection, existing_policy_item_ids)
                loaded_counts = {
                    "loaded_policy_item_count": 0,
                    "loaded_display_text_count": 0,
                    "loaded_evidence_link_count": 0,
                    "loaded_taxonomy_row_count": 0,
                    "loaded_derived_to_display_count": 0,
                }
                for suffix, table_name in CSV_TABLE_ORDER:
                    csv_path = file_paths[suffix]
                    if not csv_path.exists():
                        continue
                    count = load_rows(connection, csv_path, table_name)
                    if suffix == "policy-items-reviewed.csv":
                        loaded_counts["loaded_policy_item_count"] = count
                    elif suffix == "display-texts-reviewed.csv":
                        loaded_counts["loaded_display_text_count"] = count
                    elif suffix == "policy-item-evidence-links-reviewed.csv":
                        loaded_counts["loaded_evidence_link_count"] = count
                    elif suffix == "policy-item-taxonomy-map-reviewed.csv":
                        loaded_counts["loaded_taxonomy_row_count"] = count
                    elif suffix == "derived-to-display-map-reviewed.csv":
                        loaded_counts["loaded_derived_to_display_count"] = count
                connection.commit()
                rows.append(
                    {
                        "document_id": document_id,
                        "run_status": "completed",
                        **loaded_counts,
                        **delete_counts,
                        "notes": "",
                    }
                )
            except Exception as exc:  # pragma: no cover - defensive rollback path
                connection.rollback()
                rows.append(
                    {
                        "document_id": document_id,
                        "run_status": "failed",
                        "loaded_policy_item_count": 0,
                        "loaded_display_text_count": 0,
                        "loaded_evidence_link_count": 0,
                        "loaded_taxonomy_row_count": 0,
                        "loaded_derived_to_display_count": 0,
                        "deleted_policy_item_count": 0,
                        "deleted_display_text_count": 0,
                        "deleted_evidence_link_count": 0,
                        "deleted_taxonomy_row_count": 0,
                        "deleted_assertion_count": 0,
                        "deleted_data_quality_flag_count": 0,
                        "deleted_derived_to_display_count": 0,
                        "notes": str(exc),
                    }
                )
    finally:
        connection.close()

    summary = {
        "document_count": len(documents),
        "completed_count": sum(1 for row in rows if row["run_status"] == "completed"),
        "skipped_missing_reviewed_items_count": sum(1 for row in rows if row["run_status"] == "skipped_missing_reviewed_items"),
        "skipped_no_reviewed_rows_count": sum(1 for row in rows if row["run_status"] == "skipped_no_reviewed_rows"),
        "failed_count": sum(1 for row in rows if row["run_status"] not in {"completed", "skipped_missing_reviewed_items", "skipped_no_reviewed_rows"}),
        "loaded_policy_item_count_total": sum(int(row["loaded_policy_item_count"]) for row in rows if row["run_status"] == "completed"),
        "loaded_display_text_count_total": sum(int(row["loaded_display_text_count"]) for row in rows if row["run_status"] == "completed"),
        "loaded_evidence_link_count_total": sum(int(row["loaded_evidence_link_count"]) for row in rows if row["run_status"] == "completed"),
        "loaded_taxonomy_row_count_total": sum(int(row["loaded_taxonomy_row_count"]) for row in rows if row["run_status"] == "completed"),
        "loaded_derived_to_display_count_total": sum(int(row["loaded_derived_to_display_count"]) for row in rows if row["run_status"] == "completed"),
        "deleted_policy_item_count_total": sum(int(row["deleted_policy_item_count"]) for row in rows if row["run_status"] == "completed"),
        "deleted_display_text_count_total": sum(int(row["deleted_display_text_count"]) for row in rows if row["run_status"] == "completed"),
        "deleted_evidence_link_count_total": sum(int(row["deleted_evidence_link_count"]) for row in rows if row["run_status"] == "completed"),
        "deleted_taxonomy_row_count_total": sum(int(row["deleted_taxonomy_row_count"]) for row in rows if row["run_status"] == "completed"),
        "deleted_assertion_count_total": sum(int(row["deleted_assertion_count"]) for row in rows if row["run_status"] == "completed"),
        "deleted_data_quality_flag_count_total": sum(int(row["deleted_data_quality_flag_count"]) for row in rows if row["run_status"] == "completed"),
        "deleted_derived_to_display_count_total": sum(int(row["deleted_derived_to_display_count"]) for row in rows if row["run_status"] == "completed"),
        "documents": rows,
    }
    write_json(Path(args.out_summary_json), summary)
    if args.out_summary_csv:
        write_csv(
            Path(args.out_summary_csv),
            rows,
            [
                "document_id",
                "run_status",
                "loaded_policy_item_count",
                "loaded_display_text_count",
                "loaded_evidence_link_count",
                "loaded_taxonomy_row_count",
                "loaded_derived_to_display_count",
                "deleted_policy_item_count",
                "deleted_display_text_count",
                "deleted_evidence_link_count",
                "deleted_taxonomy_row_count",
                "deleted_assertion_count",
                "deleted_data_quality_flag_count",
                "deleted_derived_to_display_count",
                "notes",
            ],
        )

    print(f"Reviewed policy items loaded: {summary['completed_count']}")


if __name__ == "__main__":
    main()
