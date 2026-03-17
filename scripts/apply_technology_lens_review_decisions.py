#!/usr/bin/env python3
"""Apply technology lens group review decisions to the ontology store."""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from collections import defaultdict
from pathlib import Path

from technology_lens_review_utils import build_decision_key, normalize_source_policy_item_ids


APPLIABLE_STATUSES = {"approved", "revised", "rejected"}
AUTO_GROUP_STATUSES = {"auto_seed_curated", "auto_expand_curated"}
REVIEWED_GROUP_STATUS = "reviewed_curated"
REJECTED_GROUP_STATUS = "review_rejected"
REVIEWED_CONTENT_STATUS = "reviewed_curated"
REJECTED_CONTENT_STATUS = "review_rejected"
REVIEWED_SOURCE_BASIS_TYPE = "technology_lens_manual_review"
REJECTED_SOURCE_BASIS_TYPE = "technology_lens_review_rejected"


REVIEWED_QUEUE_FIELDS = [
    "decision_key",
    "decision_status",
    "resolved_group_id",
    "applied_status",
    "applied_group_status",
    "applied_group_label",
    "reviewer_name",
    "reviewer_notes",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", required=True)
    parser.add_argument("--decision-csv", required=True)
    parser.add_argument("--out-reviewed-queue-csv", required=True)
    parser.add_argument("--out-summary-json", required=True)
    parser.add_argument("--asserted-at", default="")
    args = parser.parse_args()

    decision_rows = read_csv(Path(args.decision_csv))
    if not decision_rows:
        write_csv(Path(args.out_reviewed_queue_csv), [], REVIEWED_QUEUE_FIELDS)
        write_json(Path(args.out_summary_json), {"decision_item_count": 0, "applied_item_count": 0})
        print("Applied technology lens review decisions: 0")
        return

    connection = sqlite3.connect(args.db_path)
    connection.row_factory = sqlite3.Row
    try:
        group_rows = connection.execute(
            """
            SELECT
                pig.policy_item_group_id,
                pig.policy_bucket_id,
                pig.group_label,
                pig.group_summary,
                pig.group_description,
                pig.group_status,
                pig.source_basis_type,
                pb.policy_id,
                pb.resource_category_id
            FROM policy_item_groups pig
            JOIN policy_buckets pb ON pb.policy_bucket_id = pig.policy_bucket_id
            ORDER BY pig.policy_item_group_id
            """
        ).fetchall()
        member_rows = connection.execute(
            """
            SELECT policy_item_group_id, policy_item_id
            FROM policy_item_group_members
            ORDER BY policy_item_group_id, policy_item_id
            """
        ).fetchall()
        taxonomy_rows = connection.execute(
            """
            SELECT policy_item_group_id, term_id
            FROM policy_item_group_taxonomy_map
            WHERE taxonomy_type = 'tech_domain'
              AND is_primary = 1
              AND review_status = 'reviewed'
            ORDER BY policy_item_group_id, term_id
            """
        ).fetchall()
        content_rows = connection.execute(
            """
            SELECT policy_item_content_id, policy_item_group_id
            FROM policy_item_contents
            ORDER BY policy_item_group_id, policy_item_content_id
            """
        ).fetchall()
        group_display_rows = connection.execute(
            """
            SELECT display_text_id, target_object_id
            FROM display_texts
            WHERE target_object_type = 'policy_item_group'
              AND display_role = 'policy_item_group_card'
            ORDER BY target_object_id
            """
        ).fetchall()
        content_display_rows = connection.execute(
            """
            SELECT display_text_id, target_object_id
            FROM display_texts
            WHERE target_object_type = 'policy_item_content'
              AND display_role = 'policy_item_content_card'
            ORDER BY target_object_id
            """
        ).fetchall()

        members_by_group: dict[str, list[str]] = defaultdict(list)
        for row in member_rows:
            members_by_group[row["policy_item_group_id"]].append(row["policy_item_id"])

        primary_domain_by_group = {
            row["policy_item_group_id"]: row["term_id"]
            for row in taxonomy_rows
        }
        content_ids_by_group: dict[str, list[str]] = defaultdict(list)
        for row in content_rows:
            content_ids_by_group[row["policy_item_group_id"]].append(row["policy_item_content_id"])
        group_display_id_by_group = {
            row["target_object_id"]: row["display_text_id"]
            for row in group_display_rows
        }
        content_display_ids_by_content = {
            row["target_object_id"]: row["display_text_id"]
            for row in content_display_rows
        }

        current_groups_by_key: dict[str, dict[str, object]] = {}
        for row in group_rows:
            tech_domain_id = primary_domain_by_group.get(row["policy_item_group_id"], "")
            source_policy_item_ids = normalize_source_policy_item_ids(
                " | ".join(members_by_group.get(row["policy_item_group_id"], []))
            )
            if not tech_domain_id or not source_policy_item_ids:
                continue
            decision_key = build_decision_key(
                tech_domain_id,
                row["policy_id"],
                row["resource_category_id"],
                source_policy_item_ids,
            )
            current_groups_by_key[decision_key] = {
                "policy_item_group_id": row["policy_item_group_id"],
                "group_label": row["group_label"],
                "group_summary": row["group_summary"],
                "group_description": row["group_description"],
                "group_status": row["group_status"],
                "group_display_text_id": group_display_id_by_group.get(row["policy_item_group_id"], ""),
                "content_ids": content_ids_by_group.get(row["policy_item_group_id"], []),
                "content_display_text_ids": [
                    content_display_ids_by_content[content_id]
                    for content_id in content_ids_by_group.get(row["policy_item_group_id"], [])
                    if content_id in content_display_ids_by_content
                ],
            }

        reviewed_rows: list[dict[str, object]] = []
        assertion_rows: list[dict[str, object]] = []
        applied_item_count = 0

        for row in decision_rows:
            decision_status = (row.get("decision_status") or "pending").strip()
            if decision_status not in APPLIABLE_STATUSES:
                continue

            decision_key = row["decision_key"]
            current_group = current_groups_by_key.get(decision_key)
            if not current_group:
                applied_status = "inactive_missing_target" if (row.get("active_in_queue") or "yes") == "no" else "missing_target"
                reviewed_rows.append(
                    {
                        "decision_key": decision_key,
                        "decision_status": decision_status,
                        "resolved_group_id": "",
                        "applied_status": applied_status,
                        "applied_group_status": "",
                        "applied_group_label": "",
                        "reviewer_name": row.get("reviewer_name", ""),
                        "reviewer_notes": row.get("reviewer_notes", ""),
                    }
                )
                continue

            group_id = current_group["policy_item_group_id"]
            existing_label = current_group["group_label"]
            existing_summary = current_group["group_summary"]
            existing_description = current_group["group_description"]

            if decision_status == "rejected":
                target_group_status = REJECTED_GROUP_STATUS
                target_content_status = REJECTED_CONTENT_STATUS
                target_source_basis_type = REJECTED_SOURCE_BASIS_TYPE
                applied_group_label = existing_label
                applied_group_summary = existing_summary
                applied_group_description = existing_description
            else:
                target_group_status = REVIEWED_GROUP_STATUS
                target_content_status = REVIEWED_CONTENT_STATUS
                target_source_basis_type = REVIEWED_SOURCE_BASIS_TYPE
                applied_group_label = (row.get("reviewed_group_label") or "").strip() or existing_label
                applied_group_summary = (row.get("reviewed_group_summary") or "").strip() or existing_summary
                applied_group_description = (row.get("reviewed_group_description") or "").strip() or existing_description

            connection.execute(
                """
                UPDATE policy_item_groups
                SET group_label = ?,
                    group_summary = ?,
                    group_description = ?,
                    group_status = ?,
                    source_basis_type = ?
                WHERE policy_item_group_id = ?
                """,
                (
                    applied_group_label,
                    applied_group_summary,
                    applied_group_description,
                    target_group_status,
                    target_source_basis_type,
                    group_id,
                ),
            )
            if current_group["content_ids"]:
                placeholders = ", ".join("?" for _ in current_group["content_ids"])
                connection.execute(
                    f"""
                    UPDATE policy_item_contents
                    SET content_status = ?
                    WHERE policy_item_content_id IN ({placeholders})
                    """,
                    (target_content_status, *current_group["content_ids"]),
                )
            if current_group["group_display_text_id"]:
                connection.execute(
                    """
                    UPDATE display_texts
                    SET title_text = ?,
                        summary_text = ?,
                        description_text = ?,
                        generated_by = 'technology_lens_review',
                        review_status = 'reviewed',
                        source_basis_type = ?
                    WHERE display_text_id = ?
                    """,
                    (
                        applied_group_label,
                        applied_group_summary,
                        applied_group_description,
                        target_source_basis_type,
                        current_group["group_display_text_id"],
                    ),
                )
            if current_group["content_display_text_ids"]:
                placeholders = ", ".join("?" for _ in current_group["content_display_text_ids"])
                connection.execute(
                    f"""
                    UPDATE display_texts
                    SET generated_by = 'technology_lens_review',
                        review_status = 'reviewed',
                        source_basis_type = ?
                    WHERE display_text_id IN ({placeholders})
                    """,
                    (target_source_basis_type, *current_group["content_display_text_ids"]),
                )

            assertion_rows.append(
                {
                    "assertion_id": f"AST-{group_id}-TLR",
                    "target_object_type": "policy_item_group",
                    "target_object_id": group_id,
                    "assertion_type": "technology_lens_review",
                    "asserted_value": decision_status,
                    "confidence": "high",
                    "asserted_by": row.get("reviewer_name", "") or "manual",
                    "asserted_at": args.asserted_at,
                    "review_status": "reviewed",
                    "source_note": row.get("reviewer_notes", ""),
                }
            )
            reviewed_rows.append(
                {
                    "decision_key": decision_key,
                    "decision_status": decision_status,
                    "resolved_group_id": group_id,
                    "applied_status": "applied",
                    "applied_group_status": target_group_status,
                    "applied_group_label": applied_group_label,
                    "reviewer_name": row.get("reviewer_name", ""),
                    "reviewer_notes": row.get("reviewer_notes", ""),
                }
            )
            applied_item_count += 1

        if assertion_rows:
            assertion_ids = tuple(row["assertion_id"] for row in assertion_rows)
            placeholders = ", ".join("?" for _ in assertion_ids)
            connection.execute(
                f"DELETE FROM curation_assertions WHERE assertion_id IN ({placeholders})",
                assertion_ids,
            )
            connection.executemany(
                """
                INSERT OR REPLACE INTO curation_assertions (
                    assertion_id,
                    target_object_type,
                    target_object_id,
                    assertion_type,
                    asserted_value,
                    confidence,
                    asserted_by,
                    asserted_at,
                    review_status,
                    source_note
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        row["assertion_id"],
                        row["target_object_type"],
                        row["target_object_id"],
                        row["assertion_type"],
                        row["asserted_value"],
                        row["confidence"],
                        row["asserted_by"],
                        row["asserted_at"],
                        row["review_status"],
                        row["source_note"],
                    )
                    for row in assertion_rows
                ],
            )

        connection.commit()
    finally:
        connection.close()

    write_csv(Path(args.out_reviewed_queue_csv), reviewed_rows, REVIEWED_QUEUE_FIELDS)
    write_json(
        Path(args.out_summary_json),
        {
            "decision_item_count": len(decision_rows),
            "applied_item_count": applied_item_count,
            "applied_status_counts": {
                status: sum(1 for row in reviewed_rows if row["applied_status"] == status)
                for status in sorted({row["applied_status"] for row in reviewed_rows})
            },
        },
    )
    print(f"Applied technology lens review decisions: {applied_item_count}")


if __name__ == "__main__":
    main()
