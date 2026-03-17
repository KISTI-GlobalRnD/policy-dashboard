#!/usr/bin/env python3
"""Export a technology-centric read model from the ontology store."""

from __future__ import annotations

import argparse
import json
import sqlite3
from collections import defaultdict
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path


RESOURCE_CATEGORY_PRIORITY = {
    "technology": 0,
    "infrastructure_institutional": 1,
    "talent": 2,
}

AUTO_CURATED_GROUP_STATUSES = {"auto_seed_curated", "auto_expand_curated"}
EXCLUDED_GROUP_STATUSES = {"review_rejected"}


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def classify_source_tier(doc_role: str, include_status: str) -> str:
    if doc_role == "policy_source":
        return "authoritative_policy"
    if include_status == "support":
        return "supporting_context"
    if include_status == "hold":
        return "reference_only"
    if include_status == "missing":
        return "missing_source"
    return "supplementary"


def first_or_none(rows: list[sqlite3.Row]) -> sqlite3.Row | None:
    return rows[0] if rows else None


def build_taxonomy_payload(row: sqlite3.Row, label_key: str) -> dict[str, object]:
    return {
        "term_id": row["term_id"],
        "label": row[label_key],
        "is_primary": bool(row["is_primary"]),
        "confidence": row["confidence"],
        "review_status": row["review_status"],
    }


def build_group_summary(group_payload: dict[str, object]) -> dict[str, object]:
    return {
        "policy_item_group_id": group_payload["policy_item_group_id"],
        "group_label": group_payload["group_label"],
        "group_summary": group_payload["group_summary"],
        "policy": deepcopy(group_payload["policy"]),
        "bucket": deepcopy(group_payload["bucket"]),
        "taxonomy": deepcopy(group_payload["taxonomy"]),
        "content_count": group_payload["content_count"],
        "member_item_count": group_payload["member_item_count"],
    }


def build_taxonomy_projection(taxonomies: dict[str, list[sqlite3.Row]]) -> tuple[list[dict[str, object]], dict[str, object]]:
    primary_domains = [
        build_taxonomy_payload(tax_row, "tech_domain_label")
        for tax_row in taxonomies.get("tech_domain", [])
        if tax_row["is_primary"] and tax_row["tech_domain_label"]
    ]
    secondary_domains = [
        build_taxonomy_payload(tax_row, "tech_domain_label")
        for tax_row in taxonomies.get("tech_domain", [])
        if (not tax_row["is_primary"]) and tax_row["tech_domain_label"]
    ]
    primary_subdomains = [
        build_taxonomy_payload(tax_row, "tech_subdomain_label")
        for tax_row in taxonomies.get("tech_subdomain", [])
        if tax_row["is_primary"] and tax_row["tech_subdomain_label"]
    ]
    secondary_subdomains = [
        build_taxonomy_payload(tax_row, "tech_subdomain_label")
        for tax_row in taxonomies.get("tech_subdomain", [])
        if (not tax_row["is_primary"]) and tax_row["tech_subdomain_label"]
    ]
    strategies = [
        build_taxonomy_payload(tax_row, "strategy_label")
        for tax_row in taxonomies.get("strategy", [])
        if tax_row["strategy_label"]
    ]
    return primary_domains, {
        "primary_tech_domain": primary_domains[0] if len(primary_domains) == 1 else None,
        "secondary_tech_domains": secondary_domains,
        "primary_tech_subdomain": primary_subdomains[0] if primary_subdomains else None,
        "secondary_tech_subdomains": secondary_subdomains,
        "strategies": strategies,
    }


def build_evidence_payload(
    row: sqlite3.Row,
    assets_by_derived: dict[str, list[dict[str, object]]],
) -> tuple[dict[str, object], str]:
    source_tier = classify_source_tier(row["doc_role"], row["include_status"])
    return (
        {
            "derived_representation_id": row["derived_representation_id"],
            "representation_type": row["representation_type"],
            "source_object_type": row["source_object_type"],
            "source_object_id": row["source_object_id"],
            "location_type": row["location_type"],
            "location_value": row["location_value"],
            "plain_text": row["plain_text"] or "",
            "quality_status": row["quality_status"],
            "review_status": row["review_status"],
            "link_role": row["link_role"],
            "evidence_strength": row["evidence_strength"],
            "is_primary": bool(row["is_primary"]),
            "sort_order": row["sort_order"],
            "source_tier": source_tier,
            "document": {
                "document_id": row["document_id"],
                "policy_id": row["document_policy_id"],
                "doc_role": row["doc_role"],
                "include_status": row["include_status"],
                "normalized_title": row["normalized_title"],
                "issuing_org": row["issuing_org"],
                "issued_date": row["issued_date"],
                "location_granularity": row["location_granularity"],
            },
            "source_assets": assets_by_derived.get(row["derived_representation_id"], []),
        },
        source_tier,
    )


def provisional_item_sort_key(item_payload: dict[str, object]) -> tuple[int, int, int, int, str]:
    strategy_rows = item_payload["taxonomy_rows"].get("strategy", [])
    has_reviewed_strategy = any(
        row["is_primary"] and row["review_status"] != "auto_mapped"
        for row in strategy_rows
    )
    has_primary_strategy = any(row["is_primary"] for row in strategy_rows)
    strategy_rank = 0 if has_reviewed_strategy else 1 if has_primary_strategy else 2
    bucket_rank = RESOURCE_CATEGORY_PRIORITY.get(
        item_payload["bucket"]["resource_category_id"],
        9,
    )
    curation_rank = -int(item_payload["curation_priority"])
    return (
        strategy_rank,
        bucket_rank,
        int(item_payload["policy"]["policy_order"]),
        curation_rank,
        item_payload["policy_item_id"],
    )


def select_provisional_items(
    item_payloads: list[dict[str, object]],
    max_groups_per_domain: int,
) -> list[dict[str, object]]:
    if max_groups_per_domain <= 0:
        return []

    sorted_items = sorted(item_payloads, key=provisional_item_sort_key)
    selected: list[dict[str, object]] = []
    selected_ids: set[str] = set()
    used_policy_bucket_pairs: set[tuple[str, str]] = set()

    for item in sorted_items:
        pair = (
            item["policy"]["policy_id"],
            item["bucket"]["resource_category_id"],
        )
        if pair in used_policy_bucket_pairs:
            continue
        selected.append(item)
        selected_ids.add(item["policy_item_id"])
        used_policy_bucket_pairs.add(pair)
        if len(selected) >= max_groups_per_domain:
            return selected

    for item in sorted_items:
        if item["policy_item_id"] in selected_ids:
            continue
        selected.append(item)
        if len(selected) >= max_groups_per_domain:
            break

    return selected


def build_provisional_group_payload(
    item_payload: dict[str, object],
    display_order: int,
) -> dict[str, object]:
    content_id = f"PIC-PROV-{item_payload['policy_item_id']}"
    content_payload = {
        "policy_item_content_id": content_id,
        "content_label": item_payload["display"]["title_text"],
        "content_statement": item_payload["item_statement"],
        "content_summary": item_payload["display"]["summary_text"] or item_payload["item_statement"],
        "content_type": "policy_action",
        "content_status": "provisional_auto",
        "display_order": 1,
        "display": deepcopy(item_payload["display"]),
        "evidence_count": len(item_payload["evidence"]),
        "primary_policy_evidence": deepcopy(item_payload["primary_policy_evidence"]),
        "evidence": deepcopy(item_payload["evidence"]),
        "projection_source": "provisional_policy_item",
        "source_policy_item_id": item_payload["policy_item_id"],
    }
    return {
        "policy_item_group_id": f"PIG-PROV-{item_payload['policy_item_id']}",
        "group_label": item_payload["display"]["title_text"],
        "group_summary": item_payload["display"]["summary_text"] or item_payload["item_statement"],
        "group_description": item_payload["display"]["description_text"] or item_payload["item_description"],
        "group_status": "provisional_auto",
        "source_basis_type": "provisional_policy_item",
        "display_order": display_order,
        "display": deepcopy(item_payload["display"]),
        "policy": deepcopy(item_payload["policy"]),
        "bucket": deepcopy(item_payload["bucket"]),
        "taxonomy": deepcopy(item_payload["taxonomy"]),
        "member_item_count": 1,
        "member_items": [
            {
                "policy_item_id": item_payload["policy_item_id"],
                "item_label": item_payload["item_label"],
                "item_statement": item_payload["item_statement"],
                "item_description": item_payload["item_description"],
                "member_role": "representative_item",
                "is_representative": True,
                "confidence": item_payload["primary_tech_domain"]["confidence"],
            }
        ],
        "content_count": 1,
        "contents": [content_payload],
        "projection_source": "provisional_policy_item",
        "source_policy_item_id": item_payload["policy_item_id"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--max-provisional-groups-per-domain", type=int, default=3)
    args = parser.parse_args()

    connection = sqlite3.connect(args.db_path)
    connection.row_factory = sqlite3.Row
    try:
        tech_domains = connection.execute(
            """
            SELECT tech_domain_id, tech_domain_label, display_order
            FROM tech_domains
            WHERE is_active = 1
            ORDER BY display_order, tech_domain_id
            """
        ).fetchall()
        groups = connection.execute(
            """
            SELECT
                pig.*,
                pb.policy_id,
                pb.resource_category_id,
                pb.display_order AS bucket_display_order,
                rc.display_label AS resource_category_label,
                p.policy_name,
                p.policy_order,
                p.policy_status,
                p.primary_document_id
            FROM policy_item_groups pig
            JOIN policy_buckets pb ON pb.policy_bucket_id = pig.policy_bucket_id
            JOIN resource_categories rc ON rc.resource_category_id = pb.resource_category_id
            JOIN policies p ON p.policy_id = pb.policy_id
            ORDER BY p.policy_order, pb.display_order, pig.display_order, pig.policy_item_group_id
            """
        ).fetchall()
        contents = connection.execute(
            """
            SELECT
                pic.*,
                dt.title_text AS display_title,
                dt.summary_text AS display_summary,
                dt.description_text AS display_description
            FROM policy_item_contents pic
            LEFT JOIN display_texts dt
              ON dt.target_object_type = 'policy_item_content'
             AND dt.target_object_id = pic.policy_item_content_id
             AND dt.display_role = 'policy_item_content_card'
            ORDER BY pic.policy_item_group_id, pic.display_order, pic.policy_item_content_id
            """
        ).fetchall()
        group_display_rows = connection.execute(
            """
            SELECT
                target_object_id AS policy_item_group_id,
                title_text,
                summary_text,
                description_text
            FROM display_texts
            WHERE target_object_type = 'policy_item_group'
              AND display_role = 'policy_item_group_card'
            ORDER BY target_object_id
            """
        ).fetchall()
        group_member_rows = connection.execute(
            """
            SELECT
                pgm.policy_item_group_id,
                pgm.policy_item_id,
                pgm.member_role,
                pgm.is_representative,
                pgm.confidence,
                pi.item_label,
                pi.item_statement,
                pi.item_description
            FROM policy_item_group_members pgm
            JOIN policy_items pi ON pi.policy_item_id = pgm.policy_item_id
            ORDER BY pgm.policy_item_group_id, pgm.is_representative DESC, pgm.policy_item_id
            """
        ).fetchall()
        group_taxonomy_rows = connection.execute(
            """
            SELECT
                pitm.policy_item_group_id,
                pitm.taxonomy_type,
                pitm.term_id,
                pitm.is_primary,
                pitm.confidence,
                pitm.review_status,
                td.tech_domain_label,
                ts.tech_subdomain_label,
                s.strategy_label
            FROM policy_item_group_taxonomy_map pitm
            LEFT JOIN tech_domains td
              ON pitm.taxonomy_type = 'tech_domain'
             AND td.tech_domain_id = pitm.term_id
            LEFT JOIN tech_subdomains ts
              ON pitm.taxonomy_type = 'tech_subdomain'
             AND ts.tech_subdomain_id = pitm.term_id
            LEFT JOIN strategies s
              ON pitm.taxonomy_type = 'strategy'
             AND s.strategy_id = pitm.term_id
            ORDER BY pitm.policy_item_group_id, pitm.taxonomy_type, pitm.is_primary DESC, pitm.term_id
            """
        ).fetchall()
        content_evidence_rows = connection.execute(
            """
            SELECT
                pcel.policy_item_content_id,
                pcel.derived_representation_id,
                pcel.link_role,
                pcel.evidence_strength,
                pcel.is_primary,
                pcel.sort_order,
                dr.document_id,
                dr.representation_type,
                dr.source_object_type,
                dr.source_object_id,
                dr.location_type,
                dr.location_value,
                dr.plain_text,
                dr.quality_status,
                dr.review_status,
                d.policy_id AS document_policy_id,
                d.doc_role,
                d.include_status,
                d.normalized_title,
                d.issuing_org,
                d.issued_date,
                d.location_granularity
            FROM policy_item_content_evidence_links pcel
            JOIN derived_representations dr
              ON dr.derived_representation_id = pcel.derived_representation_id
            JOIN documents d
              ON d.document_id = dr.document_id
            ORDER BY pcel.policy_item_content_id, pcel.is_primary DESC, pcel.sort_order, pcel.derived_representation_id
            """
        ).fetchall()
        item_rows = connection.execute(
            """
            SELECT
                pi.*,
                pb.policy_id,
                pb.resource_category_id,
                pb.display_order AS bucket_display_order,
                rc.display_label AS resource_category_label,
                p.policy_name,
                p.policy_order,
                p.policy_status,
                p.primary_document_id,
                dt.title_text AS display_title,
                dt.summary_text AS display_summary,
                dt.description_text AS display_description
            FROM policy_items pi
            JOIN policy_buckets pb ON pb.policy_bucket_id = pi.policy_bucket_id
            JOIN resource_categories rc ON rc.resource_category_id = pb.resource_category_id
            JOIN policies p ON p.policy_id = pb.policy_id
            LEFT JOIN display_texts dt
              ON dt.target_object_type = 'policy_item'
             AND dt.target_object_id = pi.policy_item_id
             AND dt.display_role = 'policy_item_summary'
            ORDER BY p.policy_order, pb.display_order, pi.policy_item_id
            """
        ).fetchall()
        item_taxonomy_rows = connection.execute(
            """
            SELECT
                pitm.policy_item_id,
                pitm.taxonomy_type,
                pitm.term_id,
                pitm.is_primary,
                pitm.confidence,
                pitm.review_status,
                td.tech_domain_label,
                ts.tech_subdomain_label,
                s.strategy_label
            FROM policy_item_taxonomy_map pitm
            LEFT JOIN tech_domains td
              ON pitm.taxonomy_type = 'tech_domain'
             AND td.tech_domain_id = pitm.term_id
            LEFT JOIN tech_subdomains ts
              ON pitm.taxonomy_type = 'tech_subdomain'
             AND ts.tech_subdomain_id = pitm.term_id
            LEFT JOIN strategies s
              ON pitm.taxonomy_type = 'strategy'
             AND s.strategy_id = pitm.term_id
            ORDER BY pitm.policy_item_id, pitm.taxonomy_type, pitm.is_primary DESC, pitm.term_id
            """
        ).fetchall()
        item_evidence_rows = connection.execute(
            """
            SELECT
                piel.policy_item_id,
                piel.derived_representation_id,
                piel.link_role,
                piel.evidence_strength,
                piel.is_primary,
                piel.sort_order,
                dr.document_id,
                dr.representation_type,
                dr.source_object_type,
                dr.source_object_id,
                dr.location_type,
                dr.location_value,
                dr.plain_text,
                dr.quality_status,
                dr.review_status,
                d.policy_id AS document_policy_id,
                d.doc_role,
                d.include_status,
                d.normalized_title,
                d.issuing_org,
                d.issued_date,
                d.location_granularity
            FROM policy_item_evidence_links piel
            JOIN derived_representations dr
              ON dr.derived_representation_id = piel.derived_representation_id
            JOIN documents d
              ON d.document_id = dr.document_id
            ORDER BY piel.policy_item_id, piel.is_primary DESC, piel.sort_order, piel.derived_representation_id
            """
        ).fetchall()
        derived_asset_rows = connection.execute(
            """
            SELECT
                dsa.derived_representation_id,
                dsa.mapping_type,
                dsa.is_primary,
                sa.source_asset_id,
                sa.document_id,
                sa.asset_type,
                sa.mime_type,
                sa.asset_path_or_url,
                sa.page_no,
                sa.section_id,
                sa.bbox_json,
                sa.thumbnail_path,
                sa.quality_status
            FROM derived_to_source_asset_map dsa
            JOIN source_assets sa ON sa.source_asset_id = dsa.source_asset_id
            ORDER BY dsa.derived_representation_id, dsa.is_primary DESC, sa.source_asset_id
            """
        ).fetchall()
    finally:
        connection.close()

    group_display_by_id = {row["policy_item_group_id"]: row for row in group_display_rows}

    members_by_group: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in group_member_rows:
        members_by_group[row["policy_item_group_id"]].append(
            {
                "policy_item_id": row["policy_item_id"],
                "item_label": row["item_label"],
                "item_statement": row["item_statement"],
                "item_description": row["item_description"],
                "member_role": row["member_role"],
                "is_representative": bool(row["is_representative"]),
                "confidence": row["confidence"],
            }
        )

    assets_by_derived: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in derived_asset_rows:
        assets_by_derived[row["derived_representation_id"]].append(
            {
                "source_asset_id": row["source_asset_id"],
                "document_id": row["document_id"],
                "asset_type": row["asset_type"],
                "mime_type": row["mime_type"],
                "asset_path_or_url": row["asset_path_or_url"],
                "page_no": row["page_no"] or "",
                "section_id": row["section_id"] or "",
                "bbox_json": row["bbox_json"] or "",
                "thumbnail_path": row["thumbnail_path"] or "",
                "quality_status": row["quality_status"],
                "mapping_type": row["mapping_type"],
                "is_primary": bool(row["is_primary"]),
            }
        )

    reviewed_taxonomy_by_group: dict[str, dict[str, list[sqlite3.Row]]] = defaultdict(lambda: defaultdict(list))
    for row in group_taxonomy_rows:
        if row["review_status"] != "reviewed":
            continue
        reviewed_taxonomy_by_group[row["policy_item_group_id"]][row["taxonomy_type"]].append(row)

    contents_by_group: dict[str, list[dict[str, object]]] = defaultdict(list)
    policy_evidence_count = 0
    support_evidence_count = 0
    for row in content_evidence_rows:
        evidence_payload, source_tier = build_evidence_payload(row, assets_by_derived)
        if source_tier == "authoritative_policy":
            policy_evidence_count += 1
        elif source_tier == "supporting_context":
            support_evidence_count += 1
        contents_by_group[row["policy_item_content_id"]].append(evidence_payload)

    content_payload_by_id: dict[str, dict[str, object]] = {}
    for row in contents:
        evidence_list = contents_by_group[row["policy_item_content_id"]]
        primary_policy_evidence = first_or_none(
            [
                evidence
                for evidence in evidence_list
                if evidence["source_tier"] == "authoritative_policy"
            ]
        )
        content_payload_by_id[row["policy_item_content_id"]] = {
            "policy_item_content_id": row["policy_item_content_id"],
            "content_label": row["content_label"],
            "content_statement": row["content_statement"],
            "content_summary": row["content_summary"],
            "content_type": row["content_type"],
            "content_status": row["content_status"],
            "display_order": row["display_order"],
            "display": {
                "title_text": row["display_title"] or row["content_label"],
                "summary_text": row["display_summary"] or row["content_summary"] or row["content_statement"],
                "description_text": row["display_description"] or "",
            },
            "evidence_count": len(evidence_list),
            "primary_policy_evidence": deepcopy(primary_policy_evidence) if primary_policy_evidence else None,
            "evidence": evidence_list,
        }

    content_lists_by_group: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in contents:
        content_lists_by_group[row["policy_item_group_id"]].append(content_payload_by_id[row["policy_item_content_id"]])

    item_taxonomy_by_id: dict[str, dict[str, list[sqlite3.Row]]] = defaultdict(lambda: defaultdict(list))
    for row in item_taxonomy_rows:
        item_taxonomy_by_id[row["policy_item_id"]][row["taxonomy_type"]].append(row)

    item_evidence_by_id: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in item_evidence_rows:
        evidence_payload, source_tier = build_evidence_payload(row, assets_by_derived)
        item_evidence_by_id[row["policy_item_id"]].append(evidence_payload)

    provisional_candidates_by_domain_id: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in item_rows:
        primary_domains, taxonomy_payload = build_taxonomy_projection(item_taxonomy_by_id[row["policy_item_id"]])
        if len(primary_domains) != 1:
            continue
        evidence_list = item_evidence_by_id.get(row["policy_item_id"], [])
        primary_policy_evidence = first_or_none(
            [
                evidence
                for evidence in evidence_list
                if evidence["source_tier"] == "authoritative_policy"
            ]
        )
        if not primary_policy_evidence:
            continue

        provisional_candidates_by_domain_id[primary_domains[0]["term_id"]].append(
            {
                "policy_item_id": row["policy_item_id"],
                "item_label": row["item_label"],
                "item_statement": row["item_statement"],
                "item_description": row["item_description"],
                "item_status": row["item_status"],
                "source_basis_type": row["source_basis_type"],
                "curation_priority": row["curation_priority"],
                "display": {
                    "title_text": row["display_title"] or row["item_label"],
                    "summary_text": row["display_summary"] or row["item_statement"] or row["item_description"],
                    "description_text": row["display_description"] or row["item_description"],
                },
                "policy": {
                    "policy_id": row["policy_id"],
                    "policy_name": row["policy_name"],
                    "policy_order": row["policy_order"],
                    "policy_status": row["policy_status"],
                    "primary_document_id": row["primary_document_id"],
                },
                "bucket": {
                    "policy_bucket_id": row["policy_bucket_id"],
                    "resource_category_id": row["resource_category_id"],
                    "resource_category_label": row["resource_category_label"],
                    "bucket_display_order": row["bucket_display_order"],
                },
                "primary_tech_domain": primary_domains[0],
                "taxonomy": taxonomy_payload,
                "taxonomy_rows": item_taxonomy_by_id[row["policy_item_id"]],
                "primary_policy_evidence": primary_policy_evidence,
                "evidence": evidence_list,
            }
        )

    domain_payloads: list[dict[str, object]] = []
    filters: list[dict[str, object]] = []
    groups_by_domain_id: dict[str, list[dict[str, object]]] = defaultdict(list)
    unassigned_groups: list[dict[str, object]] = []

    included_curated_group_count = 0
    included_curated_content_count = 0
    for row in groups:
        if row["group_status"] in EXCLUDED_GROUP_STATUSES:
            continue
        group_display = group_display_by_id.get(row["policy_item_group_id"])
        taxonomies = reviewed_taxonomy_by_group[row["policy_item_group_id"]]
        primary_domains, taxonomy_payload = build_taxonomy_projection(taxonomies)

        group_contents = content_lists_by_group[row["policy_item_group_id"]]
        group_payload = {
            "policy_item_group_id": row["policy_item_group_id"],
            "group_label": row["group_label"],
            "group_summary": row["group_summary"],
            "group_description": row["group_description"],
            "group_status": row["group_status"],
            "source_basis_type": row["source_basis_type"],
            "display_order": row["display_order"],
            "display": {
                "title_text": group_display["title_text"] if group_display else row["group_label"],
                "summary_text": group_display["summary_text"] if group_display else row["group_summary"],
                "description_text": group_display["description_text"] if group_display else row["group_description"],
            },
            "policy": {
                "policy_id": row["policy_id"],
                "policy_name": row["policy_name"],
                "policy_order": row["policy_order"],
                "policy_status": row["policy_status"],
                "primary_document_id": row["primary_document_id"],
            },
            "bucket": {
                "policy_bucket_id": row["policy_bucket_id"],
                "resource_category_id": row["resource_category_id"],
                "resource_category_label": row["resource_category_label"],
                "bucket_display_order": row["bucket_display_order"],
            },
            "taxonomy": taxonomy_payload,
            "member_item_count": len(members_by_group[row["policy_item_group_id"]]),
            "member_items": members_by_group[row["policy_item_group_id"]],
            "content_count": len(group_contents),
            "contents": group_contents,
            "projection_source": "reviewed_group" if row["group_status"] == "reviewed_curated" else "curated_group",
        }
        included_curated_group_count += 1
        included_curated_content_count += len(group_contents)

        if len(primary_domains) != 1:
            group_payload["assignment_issue"] = "missing_or_ambiguous_primary_tech_domain"
            unassigned_groups.append(group_payload)
            continue

        groups_by_domain_id[primary_domains[0]["term_id"]].append(group_payload)

    curated_domain_ids = {domain_id for domain_id, domain_groups in groups_by_domain_id.items() if domain_groups}
    seed_expansion_domain_ids = {
        domain_id
        for domain_id, domain_groups in groups_by_domain_id.items()
        if any(group.get("group_status") in AUTO_CURATED_GROUP_STATUSES for group in domain_groups)
    }
    provisional_group_count = 0
    provisional_content_count = 0
    provisional_policy_evidence_count = 0
    provisional_support_evidence_count = 0
    for row in tech_domains:
        existing_groups = groups_by_domain_id.get(row["tech_domain_id"], [])
        if row["tech_domain_id"] in curated_domain_ids and row["tech_domain_id"] not in seed_expansion_domain_ids:
            continue
        represented_policy_item_ids = {
            member["policy_item_id"]
            for group in existing_groups
            for member in group.get("member_items", [])
            if member.get("policy_item_id")
        }
        candidate_items = [
            item_payload
            for item_payload in provisional_candidates_by_domain_id.get(row["tech_domain_id"], [])
            if item_payload["policy_item_id"] not in represented_policy_item_ids
        ]
        remaining_slots = args.max_provisional_groups_per_domain
        if row["tech_domain_id"] in seed_expansion_domain_ids:
            remaining_slots = max(args.max_provisional_groups_per_domain - len(existing_groups), 0)
        selected_items = select_provisional_items(
            candidate_items,
            remaining_slots,
        )
        next_display_order = max((group["display_order"] for group in existing_groups), default=0) + 1
        for offset, item_payload in enumerate(selected_items):
            provisional_policy_evidence_count += sum(
                1 for evidence in item_payload["evidence"] if evidence["source_tier"] == "authoritative_policy"
            )
            provisional_support_evidence_count += sum(
                1 for evidence in item_payload["evidence"] if evidence["source_tier"] == "supporting_context"
            )
            groups_by_domain_id[row["tech_domain_id"]].append(
                build_provisional_group_payload(item_payload, next_display_order + offset)
            )
            provisional_group_count += 1
            provisional_content_count += 1

    for row in tech_domains:
        domain_groups = groups_by_domain_id.get(row["tech_domain_id"], [])
        content_count = sum(group["content_count"] for group in domain_groups)
        policy_ids = sorted({group["policy"]["policy_id"] for group in domain_groups})
        strategy_map: dict[str, dict[str, object]] = {}
        subdomain_map: dict[str, dict[str, object]] = {}
        resource_category_counts: dict[str, int] = defaultdict(int)
        for group in domain_groups:
            resource_category_counts[group["bucket"]["resource_category_id"]] += 1
            for strategy in group["taxonomy"]["strategies"]:
                strategy_map[strategy["term_id"]] = strategy
            primary_subdomain = group["taxonomy"]["primary_tech_subdomain"]
            if primary_subdomain:
                subdomain_entry = subdomain_map.setdefault(
                    primary_subdomain["term_id"],
                    {
                        "tech_subdomain_id": primary_subdomain["term_id"],
                        "tech_subdomain_label": primary_subdomain["label"],
                        "group_count": 0,
                    },
                )
                subdomain_entry["group_count"] += 1

        filters.append(
            {
                "tech_domain_id": row["tech_domain_id"],
                "tech_domain_label": row["tech_domain_label"],
                "display_order": row["display_order"],
                "group_count": len(domain_groups),
                "content_count": content_count,
            }
        )
        if not domain_groups:
            continue

        domain_payloads.append(
            {
                "tech_domain_id": row["tech_domain_id"],
                "tech_domain_label": row["tech_domain_label"],
                "display_order": row["display_order"],
                "group_count": len(domain_groups),
                "content_count": content_count,
                "policy_count": len(policy_ids),
                "resource_category_counts": dict(sorted(resource_category_counts.items())),
                "strategies": sorted(strategy_map.values(), key=lambda item: item["term_id"]),
                "subdomains": sorted(subdomain_map.values(), key=lambda item: item["tech_subdomain_id"]),
                "groups": domain_groups,
            }
        )

    assigned_group_count = sum(len(rows) for rows in groups_by_domain_id.values())
    assigned_content_count = sum(group["content_count"] for rows in groups_by_domain_id.values() for group in rows)
    payload = {
        "meta": {
            "projection_name": "technology_lens_projection",
            "projection_version": "v1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source_db_path": args.db_path,
            "group_scope": "curated policy_item_groups with reviewed primary tech_domain, plus provisional policy_item fallback for uncovered tech domains and residual provisional fallback for auto-curated technology domains",
            "stats": {
                "seed_tech_domain_count": len(tech_domains),
                "projected_tech_domain_count": len(domain_payloads),
                "group_count": included_curated_group_count + provisional_group_count,
                "assigned_group_count": assigned_group_count,
                "unassigned_group_count": len(unassigned_groups),
                "content_count": included_curated_content_count + provisional_content_count,
                "assigned_content_count": assigned_content_count,
                "curated_group_count": included_curated_group_count,
                "curated_content_count": included_curated_content_count,
                "provisional_group_count": provisional_group_count,
                "provisional_content_count": provisional_content_count,
                "authoritative_policy_evidence_count": policy_evidence_count + provisional_policy_evidence_count,
                "supporting_context_evidence_count": support_evidence_count + provisional_support_evidence_count,
                "max_provisional_groups_per_domain": args.max_provisional_groups_per_domain,
            },
        },
        "tech_domain_filters": filters,
        "tech_domains": domain_payloads,
        "unassigned_groups": [build_group_summary(group) | {"assignment_issue": group["assignment_issue"]} for group in unassigned_groups],
    }

    write_json(Path(args.out_json), payload)
    print(f"Projected tech domains: {len(domain_payloads)}")
    print(f"Projected groups: {assigned_group_count}")
    print(f"Projected contents: {assigned_content_count}")


if __name__ == "__main__":
    main()
