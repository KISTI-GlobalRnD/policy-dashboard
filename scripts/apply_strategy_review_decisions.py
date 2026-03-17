#!/usr/bin/env python3
"""Apply reviewed strategy decisions to the ontology store."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sqlite3
import unicodedata
from pathlib import Path


APPLIABLE_STATUSES = {"reviewed", "no_strategy"}


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value or "").lower()
    return re.sub(r"\s+", "", normalized)


def build_decision_key(policy_id: str, bucket_label: str, item_label: str, primary_evidence_id: str) -> str:
    source = "|".join(
        [
            policy_id or "",
            bucket_label or "",
            primary_evidence_id or "",
            normalize_text(item_label),
        ]
    )
    digest = hashlib.sha1(source.encode("utf-8")).hexdigest()[:12]
    return f"SRD-{policy_id}-{digest}"


def parse_ids(value: str) -> list[str]:
    tokens: list[str] = []
    for token in re.split(r"\s*\|\s*|\s*,\s*", value or ""):
        cleaned = token.strip()
        if cleaned:
            tokens.append(cleaned)
    return tokens


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
    parser.add_argument("--out-reviewed-map-csv", required=True)
    parser.add_argument("--out-reviewed-queue-csv", required=True)
    parser.add_argument("--out-summary-json", required=True)
    parser.add_argument("--asserted-at", default="")
    args = parser.parse_args()

    decision_rows = read_csv(Path(args.decision_csv))
    if not decision_rows:
        write_csv(Path(args.out_reviewed_map_csv), [], [
            "policy_item_taxonomy_map_id",
            "policy_item_id",
            "taxonomy_type",
            "term_id",
            "is_primary",
            "confidence",
            "review_status",
            "notes",
        ])
        write_csv(Path(args.out_reviewed_queue_csv), [], [
            "decision_key",
            "decision_status",
            "resolved_policy_item_id",
            "applied_status",
            "applied_primary_strategy_id",
            "applied_secondary_strategy_ids",
            "reviewer_name",
            "reviewer_notes",
        ])
        write_json(Path(args.out_summary_json), {"decision_item_count": 0, "applied_item_count": 0})
        print("Applied reviewed strategy decisions: 0")
        return

    connection = sqlite3.connect(args.db_path)
    connection.row_factory = sqlite3.Row
    try:
        strategy_labels = {
            row["strategy_id"]: row["strategy_label"]
            for row in connection.execute("SELECT strategy_id, strategy_label FROM strategies")
        }
        current_item_rows = connection.execute(
            """
            SELECT
                pi.policy_item_id,
                p.policy_id,
                rc.display_label AS bucket_label,
                pi.item_label,
                piel.derived_representation_id AS primary_evidence_id
            FROM policy_items pi
            JOIN policy_buckets pb ON pb.policy_bucket_id = pi.policy_bucket_id
            JOIN policies p ON p.policy_id = pb.policy_id
            JOIN resource_categories rc ON rc.resource_category_id = pb.resource_category_id
            LEFT JOIN policy_item_evidence_links piel
              ON piel.policy_item_id = pi.policy_item_id
             AND piel.is_primary = 1
            ORDER BY pi.policy_item_id
            """
        ).fetchall()

        current_items_by_key = {
            build_decision_key(
                row["policy_id"],
                row["bucket_label"],
                row["item_label"],
                row["primary_evidence_id"] or "",
            ): dict(row)
            for row in current_item_rows
        }

        mapping_rows: list[dict[str, object]] = []
        assertion_rows: list[dict[str, object]] = []
        reviewed_rows: list[dict[str, object]] = []
        target_policy_item_ids: set[str] = set()
        unresolved_keys: list[str] = []
        invalid_rows: list[dict[str, str]] = []

        for row in decision_rows:
            decision_status = (row.get("decision_status") or "pending").strip()
            if decision_status not in APPLIABLE_STATUSES:
                continue

            decision_key = row["decision_key"]
            current_item = current_items_by_key.get(decision_key)
            if not current_item:
                if (row.get("active_in_queue") or "yes").strip().lower() == "no":
                    reviewed_rows.append(
                        {
                            "decision_key": decision_key,
                            "decision_status": decision_status,
                            "resolved_policy_item_id": "",
                            "applied_status": "inactive_missing_target",
                            "applied_primary_strategy_id": "",
                            "applied_secondary_strategy_ids": "",
                            "reviewer_name": row.get("reviewer_name", ""),
                            "reviewer_notes": row.get("reviewer_notes", ""),
                        }
                    )
                    continue
                unresolved_keys.append(decision_key)
                reviewed_rows.append(
                    {
                        "decision_key": decision_key,
                        "decision_status": decision_status,
                        "resolved_policy_item_id": "",
                        "applied_status": "missing_target",
                        "applied_primary_strategy_id": "",
                        "applied_secondary_strategy_ids": "",
                        "reviewer_name": row.get("reviewer_name", ""),
                        "reviewer_notes": row.get("reviewer_notes", ""),
                    }
                )
                continue

            policy_item_id = current_item["policy_item_id"]

            primary_strategy_id = (row.get("reviewed_primary_strategy_id") or row.get("suggested_primary_strategy_id") or "").strip()
            secondary_strategy_ids = []
            seen_ids = set()
            for strategy_id in parse_ids(row.get("reviewed_secondary_strategy_ids", "")):
                if strategy_id != primary_strategy_id and strategy_id not in seen_ids:
                    secondary_strategy_ids.append(strategy_id)
                    seen_ids.add(strategy_id)

            if decision_status == "reviewed":
                invalid = not primary_strategy_id or primary_strategy_id not in strategy_labels
                invalid = invalid or any(strategy_id not in strategy_labels for strategy_id in secondary_strategy_ids)
                if invalid:
                    invalid_rows.append(row)
                    reviewed_rows.append(
                        {
                            "decision_key": decision_key,
                            "decision_status": decision_status,
                            "resolved_policy_item_id": policy_item_id,
                            "applied_status": "invalid_decision",
                            "applied_primary_strategy_id": primary_strategy_id,
                            "applied_secondary_strategy_ids": " | ".join(secondary_strategy_ids),
                            "reviewer_name": row.get("reviewer_name", ""),
                            "reviewer_notes": row.get("reviewer_notes", ""),
                        }
                    )
                    continue

                target_policy_item_ids.add(policy_item_id)
                confidence = (row.get("reviewed_confidence") or "high").strip() or "high"
                all_strategy_ids = [primary_strategy_id] + secondary_strategy_ids
                for rank, strategy_id in enumerate(all_strategy_ids, start=1):
                    mapping_rows.append(
                        {
                            "policy_item_taxonomy_map_id": f"PIT-{policy_item_id}-{strategy_id}-R{rank:02d}",
                            "policy_item_id": policy_item_id,
                            "taxonomy_type": "strategy",
                            "term_id": strategy_id,
                            "is_primary": 1 if rank == 1 else 0,
                            "confidence": confidence,
                            "review_status": "reviewed_manual",
                            "notes": f"decision_key={decision_key}",
                        }
                    )
            else:
                target_policy_item_ids.add(policy_item_id)

            assertion_rows.append(
                {
                    "assertion_id": f"AST-{policy_item_id}-STR-PRIMARY",
                    "target_object_type": "policy_item",
                    "target_object_id": policy_item_id,
                    "assertion_type": "primary_strategy",
                    "asserted_value": primary_strategy_id if decision_status == "reviewed" else "NO_STRATEGY",
                    "confidence": (row.get("reviewed_confidence") or "high").strip() or "high",
                    "asserted_by": row.get("reviewer_name", "") or "manual",
                    "asserted_at": args.asserted_at,
                    "review_status": "reviewed",
                    "source_note": row.get("reviewer_notes", ""),
                }
            )
            if decision_status == "reviewed" and secondary_strategy_ids:
                assertion_rows.append(
                    {
                        "assertion_id": f"AST-{policy_item_id}-STR-SECONDARY",
                        "target_object_type": "policy_item",
                        "target_object_id": policy_item_id,
                        "assertion_type": "secondary_strategies",
                        "asserted_value": " | ".join(secondary_strategy_ids),
                        "confidence": (row.get("reviewed_confidence") or "high").strip() or "high",
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
                    "resolved_policy_item_id": policy_item_id,
                    "applied_status": "applied",
                    "applied_primary_strategy_id": primary_strategy_id if decision_status == "reviewed" else "NO_STRATEGY",
                    "applied_secondary_strategy_ids": " | ".join(secondary_strategy_ids),
                    "reviewer_name": row.get("reviewer_name", ""),
                    "reviewer_notes": row.get("reviewer_notes", ""),
                }
            )

        if target_policy_item_ids:
            placeholders = ", ".join("?" for _ in target_policy_item_ids)
            connection.execute(
                f"""
                DELETE FROM policy_item_taxonomy_map
                WHERE taxonomy_type = 'strategy'
                  AND policy_item_id IN ({placeholders})
                """,
                tuple(target_policy_item_ids),
            )
            connection.execute(
                f"""
                DELETE FROM curation_assertions
                WHERE target_object_type = 'policy_item'
                  AND assertion_type IN ('primary_strategy', 'secondary_strategies')
                  AND target_object_id IN ({placeholders})
                """,
                tuple(target_policy_item_ids),
            )

        if mapping_rows:
            connection.executemany(
                """
                INSERT OR REPLACE INTO policy_item_taxonomy_map (
                    policy_item_taxonomy_map_id,
                    policy_item_id,
                    taxonomy_type,
                    term_id,
                    is_primary,
                    confidence,
                    review_status,
                    notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        row["policy_item_taxonomy_map_id"],
                        row["policy_item_id"],
                        row["taxonomy_type"],
                        row["term_id"],
                        row["is_primary"],
                        row["confidence"],
                        row["review_status"],
                        row["notes"],
                    )
                    for row in mapping_rows
                ],
            )

        if assertion_rows:
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

    write_csv(
        Path(args.out_reviewed_map_csv),
        mapping_rows,
        [
            "policy_item_taxonomy_map_id",
            "policy_item_id",
            "taxonomy_type",
            "term_id",
            "is_primary",
            "confidence",
            "review_status",
            "notes",
        ],
    )
    write_csv(
        Path(args.out_reviewed_queue_csv),
        reviewed_rows,
        [
            "decision_key",
            "decision_status",
            "resolved_policy_item_id",
            "applied_status",
            "applied_primary_strategy_id",
            "applied_secondary_strategy_ids",
            "reviewer_name",
            "reviewer_notes",
        ],
    )
    write_json(
        Path(args.out_summary_json),
        {
            "decision_item_count": len(decision_rows),
            "applicable_decision_count": sum(
                1 for row in decision_rows if (row.get("decision_status") or "pending").strip() in APPLIABLE_STATUSES
            ),
            "applied_item_count": sum(1 for row in reviewed_rows if row["applied_status"] == "applied"),
            "inactive_missing_target_count": sum(1 for row in reviewed_rows if row["applied_status"] == "inactive_missing_target"),
            "applied_mapping_row_count": len(mapping_rows),
            "no_strategy_item_count": sum(1 for row in reviewed_rows if row["applied_primary_strategy_id"] == "NO_STRATEGY"),
            "unresolved_decision_keys": unresolved_keys,
            "invalid_decision_count": len(invalid_rows),
        },
    )
    print(f"Applied reviewed strategy decisions: {sum(1 for row in reviewed_rows if row['applied_status'] == 'applied')}")


if __name__ == "__main__":
    main()
