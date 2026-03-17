#!/usr/bin/env python3
"""Export a JSON dataset for the sample dashboard."""

from __future__ import annotations

import argparse
import json
import sqlite3
from collections import defaultdict
from pathlib import Path


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", required=True)
    parser.add_argument("--out-json", required=True)
    args = parser.parse_args()

    connection = sqlite3.connect(args.db_path)
    connection.row_factory = sqlite3.Row
    try:
        policies = connection.execute(
            """
            SELECT policy_id, policy_name, policy_order, policy_status, primary_document_id
            FROM policies
            ORDER BY policy_order
            """
        ).fetchall()
        categories = {
            row["resource_category_id"]: dict(row)
            for row in connection.execute("SELECT * FROM resource_categories ORDER BY display_order")
        }
        bucket_rows = connection.execute(
            """
            SELECT pb.policy_bucket_id, pb.policy_id, pb.resource_category_id, pb.bucket_status, rc.display_label
            FROM policy_buckets pb
            JOIN resource_categories rc ON rc.resource_category_id = pb.resource_category_id
            ORDER BY pb.policy_id, pb.display_order
            """
        ).fetchall()
        items = connection.execute(
            """
            SELECT
                pi.policy_item_id,
                pi.policy_bucket_id,
                pi.item_label,
                pi.item_statement,
                pi.item_description,
                dt.title_text,
                dt.summary_text,
                dt.description_text
            FROM policy_items pi
            LEFT JOIN display_texts dt
              ON dt.target_object_type = 'policy_item'
             AND dt.target_object_id = pi.policy_item_id
             AND dt.display_role = 'policy_item_summary'
            ORDER BY pi.policy_item_id
            """
        ).fetchall()
        taxonomy_rows = connection.execute(
            """
            SELECT
                pitm.policy_item_id,
                pitm.taxonomy_type,
                pitm.term_id,
                pitm.is_primary,
                td.tech_domain_label,
                ts.tech_subdomain_label
            FROM policy_item_taxonomy_map pitm
            LEFT JOIN tech_domains td
              ON pitm.taxonomy_type = 'tech_domain'
             AND td.tech_domain_id = pitm.term_id
            LEFT JOIN tech_subdomains ts
              ON pitm.taxonomy_type = 'tech_subdomain'
             AND ts.tech_subdomain_id = pitm.term_id
            ORDER BY pitm.policy_item_id, pitm.taxonomy_type, pitm.is_primary DESC
            """
        ).fetchall()
        evidence_rows = connection.execute(
            """
            SELECT
                link.policy_item_id,
                dr.derived_representation_id,
                dr.representation_type,
                dr.location_type,
                dr.location_value,
                dr.plain_text,
                d.normalized_title AS document_title,
                d.issuing_org,
                d.issued_date,
                sa.asset_path_or_url,
                sa.asset_type
            FROM policy_item_evidence_links link
            JOIN derived_representations dr ON dr.derived_representation_id = link.derived_representation_id
            JOIN documents d ON d.document_id = dr.document_id
            LEFT JOIN derived_to_source_asset_map dsa
              ON dsa.derived_representation_id = dr.derived_representation_id
             AND dsa.is_primary = 1
            LEFT JOIN source_assets sa ON sa.source_asset_id = dsa.source_asset_id
            ORDER BY link.policy_item_id, link.sort_order, dr.derived_representation_id
            """
        ).fetchall()

        evidence_by_item: dict[str, list[dict[str, str]]] = defaultdict(list)
        for row in evidence_rows:
            evidence_by_item[row["policy_item_id"]].append(
                {
                    "derived_representation_id": row["derived_representation_id"],
                    "representation_type": row["representation_type"],
                    "location_type": row["location_type"],
                    "location_value": row["location_value"],
                    "plain_text": row["plain_text"],
                    "document_title": row["document_title"],
                    "issuing_org": row["issuing_org"],
                    "issued_date": row["issued_date"],
                    "asset_path_or_url": row["asset_path_or_url"] or "",
                    "asset_type": row["asset_type"] or "",
                }
            )

        tech_domain_map_by_item: dict[str, list[dict[str, object]]] = defaultdict(list)
        tech_subdomain_map_by_item: dict[str, list[dict[str, object]]] = defaultdict(list)
        for row in taxonomy_rows:
            if row["taxonomy_type"] == "tech_domain" and row["tech_domain_label"]:
                tech_domain_map_by_item[row["policy_item_id"]].append(
                    {
                        "tech_domain_id": row["term_id"],
                        "tech_domain_label": row["tech_domain_label"],
                        "is_primary": bool(row["is_primary"]),
                    }
                )
            elif row["taxonomy_type"] == "tech_subdomain" and row["tech_subdomain_label"]:
                tech_subdomain_map_by_item[row["policy_item_id"]].append(
                    {
                        "tech_subdomain_id": row["term_id"],
                        "tech_subdomain_label": row["tech_subdomain_label"],
                        "is_primary": bool(row["is_primary"]),
                    }
                )

        items_by_bucket: dict[str, list[dict[str, object]]] = defaultdict(list)
        tech_domain_counts: dict[str, int] = defaultdict(int)
        for row in items:
            for domain in tech_domain_map_by_item[row["policy_item_id"]]:
                tech_domain_counts[domain["tech_domain_id"]] += 1
            items_by_bucket[row["policy_bucket_id"]].append(
                {
                    "policy_item_id": row["policy_item_id"],
                    "item_label": row["item_label"],
                    "item_statement": row["item_statement"],
                    "item_description": row["item_description"],
                    "title_text": row["title_text"] or row["item_label"],
                    "summary_text": row["summary_text"] or row["item_statement"],
                    "description_text": row["description_text"] or "",
                    "tech_domains": tech_domain_map_by_item[row["policy_item_id"]],
                    "tech_subdomains": tech_subdomain_map_by_item[row["policy_item_id"]],
                    "evidence": evidence_by_item[row["policy_item_id"]],
                }
            )

        buckets_by_policy: dict[str, list[dict[str, object]]] = defaultdict(list)
        for row in bucket_rows:
            bucket_items = items_by_bucket[row["policy_bucket_id"]]
            buckets_by_policy[row["policy_id"]].append(
                {
                    "policy_bucket_id": row["policy_bucket_id"],
                    "resource_category_id": row["resource_category_id"],
                    "display_label": row["display_label"],
                    "bucket_status": row["bucket_status"],
                    "item_count": len(bucket_items),
                    "items": bucket_items,
                }
            )

        payload = {
            "stats": {
                "policy_count": len(policies),
                "policy_item_count": len(items),
                "evidence_linked_item_count": len(evidence_by_item),
            },
            "policies": [
                {
                    "policy_id": row["policy_id"],
                    "policy_name": row["policy_name"],
                    "policy_order": row["policy_order"],
                    "policy_status": row["policy_status"],
                    "primary_document_id": row["primary_document_id"],
                    "buckets": buckets_by_policy[row["policy_id"]],
                }
                for row in policies
            ],
            "resource_categories": list(categories.values()),
            "tech_domain_filters": [
                {
                    "tech_domain_id": row["tech_domain_id"],
                    "tech_domain_label": row["tech_domain_label"],
                    "item_count": tech_domain_counts.get(row["tech_domain_id"], 0),
                }
                for row in connection.execute("SELECT tech_domain_id, tech_domain_label FROM tech_domains ORDER BY display_order")
            ],
        }
    finally:
        connection.close()

    write_json(Path(args.out_json), payload)
    print(f"Exported policies: {len(payload['policies'])}")
    print(f"Exported policy items: {payload['stats']['policy_item_count']}")


if __name__ == "__main__":
    main()
