#!/usr/bin/env python3
"""Build a review queue for policy items missing a primary strategy mapping."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sqlite3
from pathlib import Path

from strategy_alignment_exception_utils import (
    load_strategy_alignment_exceptions,
    summarize_exception_ids,
    summarize_exception_notes,
)
from strategy_scoring import normalize_text, score_strategy


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


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


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


def compress_text(value: str, limit: int = 220) -> str:
    compact = re.sub(r"\s+", " ", (value or "").strip())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3] + "..."


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", required=True)
    parser.add_argument("--keyword-json", required=True)
    parser.add_argument("--out-csv", required=True)
    parser.add_argument("--out-summary-json", required=True)
    parser.add_argument(
        "--alignment-exceptions-csv",
        default="work/04_ontology/instances/strategy_alignment_exceptions.csv",
    )
    args = parser.parse_args()

    vocabulary = load_json(Path(args.keyword_json))
    alignment_exceptions = load_strategy_alignment_exceptions(Path(args.alignment_exceptions_csv))
    connection = sqlite3.connect(args.db_path)
    connection.row_factory = sqlite3.Row
    try:
        strategy_rows = connection.execute("SELECT * FROM strategies ORDER BY display_order").fetchall()
        item_rows = connection.execute(
            """
            SELECT
                pi.policy_item_id,
                p.policy_id,
                p.policy_name,
                rc.display_label AS bucket_label,
                pi.item_label,
                pi.item_statement,
                pi.item_description,
                piel.derived_representation_id AS primary_evidence_id,
                dr.plain_text AS evidence_text
            FROM policy_items pi
            JOIN policy_buckets pb ON pb.policy_bucket_id = pi.policy_bucket_id
            JOIN policies p ON p.policy_id = pb.policy_id
            JOIN resource_categories rc ON rc.resource_category_id = pb.resource_category_id
            LEFT JOIN policy_item_taxonomy_map pitm
              ON pitm.policy_item_id = pi.policy_item_id
             AND pitm.taxonomy_type = 'strategy'
             AND pitm.is_primary = 1
            LEFT JOIN curation_assertions ca
              ON ca.target_object_type = 'policy_item'
             AND ca.target_object_id = pi.policy_item_id
             AND ca.assertion_type = 'primary_strategy'
             AND ca.asserted_value = 'NO_STRATEGY'
             AND ca.review_status = 'reviewed'
            LEFT JOIN policy_item_evidence_links piel
              ON piel.policy_item_id = pi.policy_item_id
             AND piel.is_primary = 1
            LEFT JOIN derived_representations dr
              ON dr.derived_representation_id = piel.derived_representation_id
            WHERE pitm.policy_item_taxonomy_map_id IS NULL
              AND ca.assertion_id IS NULL
            ORDER BY p.policy_order, pi.policy_item_id
            """
        ).fetchall()

        tech_domain_map: dict[str, list[str]] = {}
        primary_tech_domain_map: dict[str, str] = {}
        for row in connection.execute(
            """
            SELECT pitm.policy_item_id, td.tech_domain_label, pitm.is_primary
            FROM policy_item_taxonomy_map pitm
            JOIN tech_domains td
              ON pitm.taxonomy_type = 'tech_domain'
             AND td.tech_domain_id = pitm.term_id
            ORDER BY pitm.policy_item_id, pitm.is_primary DESC, td.display_order
            """
        ):
            tech_domain_map.setdefault(row["policy_item_id"], []).append(row["tech_domain_label"])
            if row["is_primary"] and row["policy_item_id"] not in primary_tech_domain_map:
                primary_tech_domain_map[row["policy_item_id"]] = row["tech_domain_label"]

        rows: list[dict[str, object]] = []
        for index, item in enumerate(item_rows, start=1):
            text_bundle = " ".join(
                [
                    item["item_label"],
                    item["item_statement"],
                    item["item_description"],
                    item["policy_name"],
                    item["evidence_text"] or "",
                ]
            )
            ranked: list[tuple[sqlite3.Row, int]] = []
            for strategy in strategy_rows:
                vocab_entry = vocabulary.get(strategy["strategy_label"], {})
                score = score_strategy(
                    text_bundle,
                    item["policy_name"],
                    strategy["strategy_id"],
                    strategy["strategy_label"],
                    vocab_entry,
                    focus_text=item["item_label"],
                    primary_tech_domain=primary_tech_domain_map.get(item["policy_item_id"], ""),
                )
                if score > 0:
                    ranked.append((strategy, score))
            ranked.sort(key=lambda pair: (-pair[1], pair[0]["display_order"]))

            suggested = ranked[:3]
            primary_strategy_id = suggested[0][0]["strategy_id"] if suggested else ""
            primary_exception_rows = alignment_exceptions.get(primary_strategy_id, [])
            rows.append(
                {
                    "review_item_id": f"SRV-{index:04d}",
                    "decision_key": build_decision_key(
                        item["policy_id"],
                        item["bucket_label"],
                        item["item_label"],
                        item["primary_evidence_id"] or "",
                    ),
                    "policy_item_id": item["policy_item_id"],
                    "policy_id": item["policy_id"],
                    "policy_name": item["policy_name"],
                    "bucket_label": item["bucket_label"],
                    "item_label": item["item_label"],
                    "item_statement": item["item_statement"],
                    "item_description": item["item_description"],
                    "primary_evidence_id": item["primary_evidence_id"] or "",
                    "evidence_preview": compress_text(item["evidence_text"] or item["item_description"] or item["item_statement"]),
                    "tech_domains": " | ".join(tech_domain_map.get(item["policy_item_id"], [])),
                    "suggested_strategy_id": suggested[0][0]["strategy_id"] if suggested else "",
                    "suggested_strategy_label": suggested[0][0]["strategy_label"] if suggested else "",
                    "suggested_strategy_score": suggested[0][1] if suggested else "",
                    "alternate_strategy_ids": " | ".join(entry[0]["strategy_id"] for entry in suggested[1:]),
                    "alternate_strategy_labels": " | ".join(entry[0]["strategy_label"] for entry in suggested[1:]),
                    "alignment_exception_ids": summarize_exception_ids(primary_exception_rows),
                    "alignment_exception_notes": summarize_exception_notes(primary_exception_rows),
                    "auto_seed_blocked": "yes" if primary_exception_rows else "no",
                    "review_status": "review_required",
                    "reviewer_notes": "",
                }
            )

        summary = {
            "review_item_count": len(rows),
            "policy_counts": {},
            "bucket_counts": {},
            "suggested_strategy_counts": {},
            "auto_seed_blocked_count": 0,
            "auto_seed_blocked_strategies": {},
        }
        for row in rows:
            summary["policy_counts"][row["policy_name"]] = summary["policy_counts"].get(row["policy_name"], 0) + 1
            summary["bucket_counts"][row["bucket_label"]] = summary["bucket_counts"].get(row["bucket_label"], 0) + 1
            if row["suggested_strategy_id"]:
                key = f"{row['suggested_strategy_id']} {row['suggested_strategy_label']}"
                summary["suggested_strategy_counts"][key] = summary["suggested_strategy_counts"].get(key, 0) + 1
                if row["auto_seed_blocked"] == "yes":
                    summary["auto_seed_blocked_count"] += 1
                    summary["auto_seed_blocked_strategies"][key] = (
                        summary["auto_seed_blocked_strategies"].get(key, 0) + 1
                    )
    finally:
        connection.close()

    write_csv(
        Path(args.out_csv),
        rows,
        [
            "review_item_id",
            "decision_key",
            "policy_item_id",
            "policy_id",
            "policy_name",
            "bucket_label",
            "item_label",
            "item_statement",
            "item_description",
            "primary_evidence_id",
            "evidence_preview",
            "tech_domains",
            "suggested_strategy_id",
            "suggested_strategy_label",
            "suggested_strategy_score",
            "alternate_strategy_ids",
            "alternate_strategy_labels",
            "alignment_exception_ids",
            "alignment_exception_notes",
            "auto_seed_blocked",
            "review_status",
            "reviewer_notes",
        ],
    )
    write_json(Path(args.out_summary_json), summary)

    print(f"Strategy review items: {len(rows)}")


if __name__ == "__main__":
    main()
