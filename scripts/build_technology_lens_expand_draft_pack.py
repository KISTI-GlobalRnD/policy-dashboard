#!/usr/bin/env python3
"""Build a bulk expansion draft pack for already-seeded technology lens domains."""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

from build_technology_lens_seed_draft_pack import (
    build_taxonomy_terms,
    load_csv,
    load_json,
    write_csv,
    write_json,
)


GROUP_STATUS = "auto_expand_curated"
CONTENT_STATUS = "auto_expand_curated"
SOURCE_BASIS_TYPE = "technology_lens_expand_batch"
GENERATED_BY = "build_technology_lens_expand_draft_pack.py"
PACK_ID = "technology-lens-expand-draft-pack-v1"


def build_pack_json(selected_groups: list[dict[str, object]]) -> dict[str, object]:
    policy_map: dict[str, dict[str, object]] = {}
    for selected in selected_groups:
        policy = selected["policy"]
        bucket = selected["bucket"]
        group_payload = selected["group_payload"]
        policy_node = policy_map.setdefault(
            policy["policy_id"],
            {
                "policy_id": policy["policy_id"],
                "policy_name": policy["policy_name"],
                "buckets": {},
            },
        )
        bucket_node = policy_node["buckets"].setdefault(
            bucket["policy_bucket_id"],
            {
                "policy_bucket_id": bucket["policy_bucket_id"],
                "resource_category_id": bucket["resource_category_id"],
                "resource_category_label": bucket["resource_category_label"],
                "groups": [],
            },
        )
        bucket_node["groups"].append(group_payload)

    return {
        "sample_scope": {
            "pack_id": PACK_ID,
            "generated_from": "post-seed technology-lens projection + curation queue",
            "purpose": "Bulk expansion draft pack for technology domains that already have at least one curated seed group.",
            "policy_count": len(policy_map),
            "group_count": len(selected_groups),
            "content_count": sum(len(group["group_payload"]["contents"]) for group in selected_groups),
        },
        "policies": [
            {
                "policy_id": policy["policy_id"],
                "policy_name": policy["policy_name"],
                "buckets": list(policy["buckets"].values()),
            }
            for policy in policy_map.values()
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--projection-json", required=True)
    parser.add_argument("--queue-csv", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--out-summary-json", required=True)
    parser.add_argument("--max-domains", type=int, default=20)
    parser.add_argument("--groups-per-domain", type=int, default=3)
    args = parser.parse_args()

    projection = load_json(Path(args.projection_json))
    queue_rows = load_csv(Path(args.queue_csv))
    out_dir = Path(args.out_dir)

    groups_by_key = {
        (domain["tech_domain_id"], group["policy_item_group_id"]): group
        for domain in projection.get("tech_domains", [])
        for group in domain.get("groups", [])
    }

    selected_queue_rows: list[dict[str, str]] = []
    domain_counts: dict[str, int] = defaultdict(int)
    selected_domain_ids: list[str] = []

    for row in queue_rows:
        if row.get("domain_priority_tier") != "expand_curated":
            continue
        tech_domain_id = row.get("tech_domain_id", "")
        if not tech_domain_id:
            continue
        if tech_domain_id not in selected_domain_ids:
            if len(selected_domain_ids) >= args.max_domains:
                continue
            selected_domain_ids.append(tech_domain_id)
        if domain_counts[tech_domain_id] >= args.groups_per_domain:
            continue
        selected_queue_rows.append(row)
        domain_counts[tech_domain_id] += 1

    group_rows: list[dict[str, object]] = []
    member_rows: list[dict[str, object]] = []
    content_rows: list[dict[str, object]] = []
    evidence_rows: list[dict[str, object]] = []
    taxonomy_rows: list[dict[str, object]] = []
    display_rows: list[dict[str, object]] = []
    selection_rows: list[dict[str, object]] = []
    selected_groups: list[dict[str, object]] = []

    for selection_rank, queue_row in enumerate(selected_queue_rows, start=1):
        tech_domain_id = queue_row["tech_domain_id"]
        group = groups_by_key[(tech_domain_id, queue_row["policy_item_group_id"])]
        group_id = f"PIG-EXP-{tech_domain_id}-{selection_rank:02d}"
        group_payload = {
            "policy_item_group_id": group_id,
            "group_label": group["group_label"],
            "group_summary": group["group_summary"],
            "group_description": group["group_description"],
            "taxonomies": [],
            "member_items": [],
            "contents": [],
        }

        group_rows.append(
            {
                "policy_item_group_id": group_id,
                "policy_bucket_id": group["bucket"]["policy_bucket_id"],
                "group_label": group["group_label"],
                "group_summary": group["group_summary"],
                "group_description": group["group_description"],
                "group_status": GROUP_STATUS,
                "source_basis_type": SOURCE_BASIS_TYPE,
                "display_order": selection_rank,
                "notes": f"expand draft from {group['policy_item_group_id']} / {group.get('source_policy_item_id', '')}",
            }
        )
        display_rows.append(
            {
                "display_text_id": f"DSP-GRP-EXP-{tech_domain_id}-{selection_rank:02d}",
                "target_object_type": "policy_item_group",
                "target_object_id": group_id,
                "display_role": "policy_item_group_card",
                "title_text": group["display"]["title_text"],
                "summary_text": group["display"]["summary_text"],
                "description_text": group["display"]["description_text"],
                "generated_by": GENERATED_BY,
                "review_status": "reviewed",
                "source_basis_type": SOURCE_BASIS_TYPE,
                "notes": f"expand draft from {group['policy_item_group_id']}",
            }
        )

        for member_index, member in enumerate(group.get("member_items", []), start=1):
            member_rows.append(
                {
                    "policy_item_group_member_id": f"PGM-EXP-{tech_domain_id}-{selection_rank:02d}-{member_index:02d}",
                    "policy_item_group_id": group_id,
                    "policy_item_id": member["policy_item_id"],
                    "member_role": member.get("member_role", "representative_item"),
                    "is_representative": 1 if member.get("is_representative") else 0,
                    "confidence": member.get("confidence", "medium"),
                    "notes": f"expand draft from {group['policy_item_group_id']}",
                }
            )
            group_payload["member_items"].append(
                {
                    "policy_item_id": member["policy_item_id"],
                    "item_label": member.get("item_label", ""),
                    "item_statement": member.get("item_statement", ""),
                    "member_role": member.get("member_role", "representative_item"),
                    "is_representative": bool(member.get("is_representative")),
                    "derived_representation_id": (group.get("contents", [{}])[0].get("primary_policy_evidence") or {}).get(
                        "derived_representation_id",
                        "",
                    ),
                }
            )

        taxonomy_terms = []
        for taxonomy_index, (taxonomy_type, term, is_primary) in enumerate(build_taxonomy_terms(group), start=1):
            taxonomy_rows.append(
                {
                    "policy_item_group_taxonomy_map_id": f"PGTM-EXP-{tech_domain_id}-{selection_rank:02d}-{taxonomy_index:02d}",
                    "policy_item_group_id": group_id,
                    "taxonomy_type": taxonomy_type,
                    "term_id": term["term_id"],
                    "is_primary": 1 if is_primary else 0,
                    "confidence": term.get("confidence", "medium"),
                    "review_status": "reviewed",
                    "notes": f"expand draft from {group['policy_item_group_id']} ({term.get('review_status', '')})",
                }
            )
            taxonomy_terms.append(
                {
                    "taxonomy_type": taxonomy_type,
                    "term_id": term["term_id"],
                    "label": term["label"],
                    "is_primary": is_primary,
                }
            )
        group_payload["taxonomies"] = taxonomy_terms

        for content_index, content in enumerate(group.get("contents", []), start=1):
            content_id = f"PIC-EXP-{tech_domain_id}-{selection_rank:02d}-{content_index:02d}"
            content_rows.append(
                {
                    "policy_item_content_id": content_id,
                    "policy_item_group_id": group_id,
                    "content_label": content["content_label"],
                    "content_statement": content["content_statement"],
                    "content_summary": content["content_summary"],
                    "content_type": content["content_type"],
                    "content_status": CONTENT_STATUS,
                    "display_order": content_index,
                    "notes": f"expand draft from {content['policy_item_content_id']}",
                }
            )
            display_rows.append(
                {
                    "display_text_id": f"DSP-CNT-EXP-{tech_domain_id}-{selection_rank:02d}-{content_index:02d}",
                    "target_object_type": "policy_item_content",
                    "target_object_id": content_id,
                    "display_role": "policy_item_content_card",
                    "title_text": content["display"]["title_text"],
                    "summary_text": content["display"]["summary_text"],
                    "description_text": content["display"]["description_text"],
                    "generated_by": GENERATED_BY,
                    "review_status": "reviewed",
                    "source_basis_type": SOURCE_BASIS_TYPE,
                    "notes": f"expand draft from {content['policy_item_content_id']}",
                }
            )
            content_payload = {
                "policy_item_content_id": content_id,
                "content_label": content["content_label"],
                "content_statement": content["content_statement"],
                "content_summary": content["content_summary"],
                "content_type": content["content_type"],
                "display_order": content_index,
                "evidence": [],
            }
            for evidence_index, evidence in enumerate(content.get("evidence", []), start=1):
                evidence_rows.append(
                    {
                        "policy_item_content_evidence_link_id": f"PCEL-EXP-{tech_domain_id}-{selection_rank:02d}-{content_index:02d}-{evidence_index:02d}",
                        "policy_item_content_id": content_id,
                        "derived_representation_id": evidence["derived_representation_id"],
                        "link_role": evidence.get("link_role", "primary_support"),
                        "evidence_strength": evidence.get("evidence_strength", "medium"),
                        "is_primary": 1 if evidence.get("is_primary") else 0,
                        "sort_order": evidence.get("sort_order", evidence_index),
                        "notes": f"expand draft from {content['policy_item_content_id']}",
                    }
                )
                content_payload["evidence"].append(
                    {
                        "source_policy_item_id": content.get("source_policy_item_id", group.get("source_policy_item_id", "")),
                        "source_policy_item_label": group["member_items"][0]["item_label"] if group.get("member_items") else "",
                        "derived_representation_id": evidence["derived_representation_id"],
                        "source_object_type": evidence.get("source_object_type", ""),
                        "source_object_id": evidence.get("source_object_id", ""),
                        "representation_type": evidence.get("representation_type", ""),
                        "document_id": (evidence.get("document") or {}).get("document_id", ""),
                        "location_type": evidence.get("location_type", ""),
                        "location_value": evidence.get("location_value", ""),
                        "evidence_text": evidence.get("plain_text", ""),
                        "evidence_label": evidence.get("link_role", ""),
                        "structured_payload_path": "",
                        "table_json_path": "",
                        "source_assets": [
                            {
                                "derived_representation_id": evidence["derived_representation_id"],
                                "source_asset_id": asset["source_asset_id"],
                                "asset_type": asset["asset_type"],
                                "asset_path_or_url": asset["asset_path_or_url"],
                                "page_no": asset.get("page_no", ""),
                                "section_id": asset.get("section_id", ""),
                            }
                            for asset in evidence.get("source_assets", [])
                        ],
                    }
                )
            group_payload["contents"].append(content_payload)

        selection_rows.append(
            {
                "selection_rank": selection_rank,
                "tech_domain_id": queue_row["tech_domain_id"],
                "tech_domain_label": queue_row["tech_domain_label"],
                "policy_id": queue_row["policy_id"],
                "policy_name": queue_row["policy_name"],
                "source_group_id": queue_row["policy_item_group_id"],
                "proposed_group_id": group_id,
                "source_policy_item_id": queue_row["source_policy_item_id"],
                "primary_strategy_id": queue_row["primary_strategy_id"],
                "primary_strategy_label": queue_row["primary_strategy_label"],
                "primary_document_id": queue_row["primary_document_id"],
                "primary_location_value": queue_row["primary_location_value"],
                "recommendation_reason": queue_row["recommendation_reason"],
            }
        )

        selected_groups.append(
            {
                "tech_domain_id": tech_domain_id,
                "policy": group["policy"],
                "bucket": group["bucket"],
                "group_payload": group_payload,
            }
        )

    pack_json = build_pack_json(selected_groups)

    write_csv(
        out_dir / "policy_item_groups_sample.csv",
        group_rows,
        [
            "policy_item_group_id",
            "policy_bucket_id",
            "group_label",
            "group_summary",
            "group_description",
            "group_status",
            "source_basis_type",
            "display_order",
            "notes",
        ],
    )
    write_csv(
        out_dir / "policy_item_group_members_sample.csv",
        member_rows,
        [
            "policy_item_group_member_id",
            "policy_item_group_id",
            "policy_item_id",
            "member_role",
            "is_representative",
            "confidence",
            "notes",
        ],
    )
    write_csv(
        out_dir / "policy_item_contents_sample.csv",
        content_rows,
        [
            "policy_item_content_id",
            "policy_item_group_id",
            "content_label",
            "content_statement",
            "content_summary",
            "content_type",
            "content_status",
            "display_order",
            "notes",
        ],
    )
    write_csv(
        out_dir / "policy_item_content_evidence_links_sample.csv",
        evidence_rows,
        [
            "policy_item_content_evidence_link_id",
            "policy_item_content_id",
            "derived_representation_id",
            "link_role",
            "evidence_strength",
            "is_primary",
            "sort_order",
            "notes",
        ],
    )
    write_csv(
        out_dir / "policy_item_group_taxonomy_map_sample.csv",
        taxonomy_rows,
        [
            "policy_item_group_taxonomy_map_id",
            "policy_item_group_id",
            "taxonomy_type",
            "term_id",
            "is_primary",
            "confidence",
            "review_status",
            "notes",
        ],
    )
    write_csv(
        out_dir / "display_texts_curated_sample.csv",
        display_rows,
        [
            "display_text_id",
            "target_object_type",
            "target_object_id",
            "display_role",
            "title_text",
            "summary_text",
            "description_text",
            "generated_by",
            "review_status",
            "source_basis_type",
            "notes",
        ],
    )
    write_csv(
        out_dir / "expand_group_selection.csv",
        selection_rows,
        [
            "selection_rank",
            "tech_domain_id",
            "tech_domain_label",
            "policy_id",
            "policy_name",
            "source_group_id",
            "proposed_group_id",
            "source_policy_item_id",
            "primary_strategy_id",
            "primary_strategy_label",
            "primary_document_id",
            "primary_location_value",
            "recommendation_reason",
        ],
    )
    write_json(out_dir / "technology-lens-expand-draft-pack.json", pack_json)

    summary = {
        "projection_json": args.projection_json,
        "queue_csv": args.queue_csv,
        "selected_domain_count": len({row["tech_domain_id"] for row in selection_rows}),
        "selected_group_count": len(group_rows),
        "selected_content_count": len(content_rows),
        "selected_evidence_link_count": len(evidence_rows),
        "selected_policy_count": len({row["policy_id"] for row in selection_rows}),
        "max_domains": args.max_domains,
        "groups_per_domain": args.groups_per_domain,
        "selected_groups": selection_rows,
        "out_dir": str(out_dir),
    }
    write_json(Path(args.out_summary_json), summary)
    print(f"Technology lens expand draft groups: {len(group_rows)}")


if __name__ == "__main__":
    main()
