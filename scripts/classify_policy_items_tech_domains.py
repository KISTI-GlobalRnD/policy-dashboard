#!/usr/bin/env python3
"""Classify auto policy items into tech domains using keyword heuristics."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sqlite3
import unicodedata
from pathlib import Path


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value or "").lower()
    return re.sub(r"\s+", "", normalized)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def score_domain(text_bundle: str, policy_name: str, domain_label: str, vocab_entry: dict) -> int:
    score = 0
    normalized_bundle = normalize_text(text_bundle)
    normalized_policy = normalize_text(policy_name)
    if normalize_text(domain_label) in normalized_bundle:
        score += 8
    for alias in vocab_entry.get("aliases", []):
        normalized_alias = normalize_text(alias)
        if normalized_alias and normalized_alias in normalized_bundle:
            score += 3
    for alias in vocab_entry.get("policy_aliases", []):
        normalized_alias = normalize_text(alias)
        if normalized_alias and normalized_alias in normalized_policy:
            score += 4
    return score


def infer_subdomain_id(text_bundle: str, domain_id: str, subdomains: list[sqlite3.Row]) -> str:
    normalized_bundle = normalize_text(text_bundle)
    best_subdomain_id = ""
    best_score = 0
    for subdomain in subdomains:
        label = subdomain["tech_subdomain_label"]
        score = 0
        normalized_label = normalize_text(label)
        if normalized_label in normalized_bundle:
            score += 6
        split_tokens = [normalize_text(token) for token in re.split(r"[·/() ]+", label) if token.strip()]
        for token in split_tokens:
            if token and token in normalized_bundle:
                score += 2
        if score > best_score:
            best_score = score
            best_subdomain_id = subdomain["tech_subdomain_id"]
    return best_subdomain_id if best_score > 0 else ""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", required=True)
    parser.add_argument("--keyword-json", required=True)
    parser.add_argument("--out-csv", required=True)
    args = parser.parse_args()

    vocabulary = load_json(Path(args.keyword_json))
    connection = sqlite3.connect(args.db_path)
    connection.row_factory = sqlite3.Row
    try:
        domain_rows = connection.execute("SELECT * FROM tech_domains ORDER BY display_order").fetchall()
        subdomain_rows = connection.execute("SELECT * FROM tech_subdomains ORDER BY tech_domain_id, display_order").fetchall()
        preserved_item_ids = {
            row["policy_item_id"]
            for row in connection.execute(
                """
                SELECT DISTINCT policy_item_id
                FROM policy_item_taxonomy_map
                WHERE taxonomy_type IN ('tech_domain', 'tech_subdomain')
                  AND review_status != 'auto_mapped'
                """
            ).fetchall()
        }
        subdomains_by_domain: dict[str, list[sqlite3.Row]] = {}
        for row in subdomain_rows:
            subdomains_by_domain.setdefault(row["tech_domain_id"], []).append(row)

        item_rows = connection.execute(
            """
            SELECT
                pi.policy_item_id,
                pi.item_label,
                pi.item_statement,
                pi.item_description,
                p.policy_name
            FROM policy_items pi
            JOIN policy_buckets pb ON pb.policy_bucket_id = pi.policy_bucket_id
            JOIN policies p ON p.policy_id = pb.policy_id
            ORDER BY pi.policy_item_id
            """
        ).fetchall()

        mapping_rows: list[dict[str, object]] = []
        for item in item_rows:
            if item["policy_item_id"] in preserved_item_ids:
                continue
            text_bundle = " ".join(
                [
                    item["item_label"],
                    item["item_statement"],
                    item["item_description"],
                    item["policy_name"],
                ]
            )
            scores = []
            for domain in domain_rows:
                vocab_entry = vocabulary.get(domain["tech_domain_label"], {})
                score = score_domain(text_bundle, item["policy_name"], domain["tech_domain_label"], vocab_entry)
                if score > 0:
                    scores.append((domain, score))
            if not scores:
                continue

            scores.sort(key=lambda pair: (-pair[1], pair[0]["display_order"]))
            top_score = scores[0][1]
            selected = [pair for pair in scores if pair[1] >= max(4, top_score - 2)][:2]

            for rank, (domain, score) in enumerate(selected, start=1):
                subdomain_id = infer_subdomain_id(text_bundle, domain["tech_domain_id"], subdomains_by_domain.get(domain["tech_domain_id"], []))
                confidence = "high" if score >= 10 else "medium"
                mapping_rows.append(
                    {
                        "policy_item_taxonomy_map_id": f"PIT-{item['policy_item_id']}-{rank:02d}",
                        "policy_item_id": item["policy_item_id"],
                        "taxonomy_type": "tech_domain",
                        "term_id": domain["tech_domain_id"],
                        "is_primary": 1 if rank == 1 else 0,
                        "confidence": confidence,
                        "review_status": "auto_mapped",
                        "notes": f"score={score}; subdomain={subdomain_id}",
                    }
                )
                if subdomain_id:
                    mapping_rows.append(
                        {
                            "policy_item_taxonomy_map_id": f"PIT-{item['policy_item_id']}-SUB-{rank:02d}",
                            "policy_item_id": item["policy_item_id"],
                            "taxonomy_type": "tech_subdomain",
                            "term_id": subdomain_id,
                            "is_primary": 1 if rank == 1 else 0,
                            "confidence": confidence,
                            "review_status": "auto_mapped",
                            "notes": f"derived_from={domain['tech_domain_id']}",
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
            WHERE taxonomy_type IN ('tech_domain', 'tech_subdomain')
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

    print(f"Taxonomy mappings: {len(mapping_rows)}")


if __name__ == "__main__":
    main()
