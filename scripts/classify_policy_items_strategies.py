#!/usr/bin/env python3
"""Classify policy items into the 15 strategy axis using keyword heuristics."""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from pathlib import Path

from strategy_alignment_exception_utils import load_strategy_alignment_exceptions
from strategy_scoring import score_strategy


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", required=True)
    parser.add_argument("--keyword-json", required=True)
    parser.add_argument("--out-csv", required=True)
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
        preserved_item_ids = {
            row["policy_item_id"]
            for row in connection.execute(
                """
                SELECT DISTINCT policy_item_id
                FROM policy_item_taxonomy_map
                WHERE taxonomy_type = 'strategy'
                  AND review_status != 'auto_mapped'
                """
            ).fetchall()
        }
        preserved_item_ids.update(
            row["target_object_id"]
            for row in connection.execute(
                """
                SELECT DISTINCT target_object_id
                FROM curation_assertions
                WHERE target_object_type = 'policy_item'
                  AND assertion_type = 'primary_strategy'
                  AND review_status = 'reviewed'
                """
            ).fetchall()
        )
        item_rows = connection.execute(
            """
            SELECT
                pi.policy_item_id,
                pi.item_label,
                pi.item_statement,
                pi.item_description,
                p.policy_name,
                dr.plain_text AS evidence_text
            FROM policy_items pi
            JOIN policy_buckets pb ON pb.policy_bucket_id = pi.policy_bucket_id
            JOIN policies p ON p.policy_id = pb.policy_id
            LEFT JOIN policy_item_evidence_links piel
              ON piel.policy_item_id = pi.policy_item_id
             AND piel.is_primary = 1
            LEFT JOIN derived_representations dr
              ON dr.derived_representation_id = piel.derived_representation_id
            ORDER BY pi.policy_item_id
            """
        ).fetchall()
        primary_tech_domain_by_item = {
            row["policy_item_id"]: row["tech_domain_label"]
            for row in connection.execute(
                """
                SELECT pitm.policy_item_id, td.tech_domain_label
                FROM policy_item_taxonomy_map pitm
                JOIN tech_domains td ON td.tech_domain_id = pitm.term_id
                WHERE pitm.taxonomy_type = 'tech_domain'
                  AND pitm.is_primary = 1
                """
            ).fetchall()
        }

        mapping_rows: list[dict[str, object]] = []
        blocked_item_count = 0
        for item in item_rows:
            if item["policy_item_id"] in preserved_item_ids:
                continue
            text_bundle = " ".join(
                [
                    item["item_label"],
                    item["item_statement"],
                    item["item_description"],
                    item["policy_name"],
                    item["evidence_text"] or "",
                ]
            )
            scores = []
            for strategy in strategy_rows:
                vocab_entry = vocabulary.get(strategy["strategy_label"], {})
                score = score_strategy(
                    text_bundle,
                    item["policy_name"],
                    strategy["strategy_id"],
                    strategy["strategy_label"],
                    vocab_entry,
                    focus_text=item["item_label"],
                    primary_tech_domain=primary_tech_domain_by_item.get(item["policy_item_id"], ""),
                )
                if score > 0:
                    scores.append((strategy, score))
            if not scores:
                continue

            scores.sort(key=lambda pair: (-pair[1], pair[0]["display_order"]))
            if scores[0][0]["strategy_id"] in alignment_exceptions:
                blocked_item_count += 1
                continue
            top_score = scores[0][1]
            selected = [pair for pair in scores if pair[1] >= max(4, top_score - 2)][:2]

            for rank, (strategy, score) in enumerate(selected, start=1):
                confidence = "high" if score >= 10 else "medium"
                mapping_rows.append(
                    {
                        "policy_item_taxonomy_map_id": f"PIT-{item['policy_item_id']}-STR-{rank:02d}",
                        "policy_item_id": item["policy_item_id"],
                        "taxonomy_type": "strategy",
                        "term_id": strategy["strategy_id"],
                        "is_primary": 1 if rank == 1 else 0,
                        "confidence": confidence,
                        "review_status": "auto_mapped",
                        "notes": f"score={score}",
                    }
                )

        write_csv(
            Path(args.out_csv),
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

        connection.execute(
            """
            DELETE FROM policy_item_taxonomy_map
            WHERE taxonomy_type = 'strategy'
              AND review_status = 'auto_mapped'
            """
        )
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
        connection.commit()
    finally:
        connection.close()

    print(
        f"Strategy mappings: {len(mapping_rows)} | "
        f"blocked by alignment exception: {blocked_item_count}"
    )


if __name__ == "__main__":
    main()
