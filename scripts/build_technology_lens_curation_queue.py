#!/usr/bin/env python3
"""Build a curation priority queue from the technology lens projection."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path


OUTPUT_FIELDS = [
    "priority_rank",
    "domain_priority_tier",
    "tech_domain_id",
    "tech_domain_label",
    "tech_domain_display_order",
    "within_domain_rank",
    "domain_group_count",
    "domain_curated_group_count",
    "domain_provisional_group_count",
    "domain_policy_count",
    "policy_id",
    "policy_name",
    "policy_order",
    "resource_category_id",
    "resource_category_label",
    "policy_item_group_id",
    "group_label",
    "group_summary",
    "projection_source",
    "group_status",
    "content_count",
    "evidence_count",
    "source_policy_item_id",
    "primary_strategy_id",
    "primary_strategy_label",
    "primary_tech_subdomain_id",
    "primary_tech_subdomain_label",
    "primary_document_id",
    "primary_location_value",
    "recommendation_reason",
]

RESOURCE_CATEGORY_ORDER = {
    "technology": 0,
    "infrastructure_institutional": 1,
    "talent": 2,
}

DOMAIN_PRIORITY_ORDER = {
    "seed_curated": 0,
    "expand_curated": 1,
}

CURATED_GROUP_STATUSES = {"sample_curated", "auto_seed_curated", "auto_expand_curated", "reviewed_curated"}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def compress_text(value: str, limit: int = 180) -> str:
    compact = re.sub(r"\s+", " ", (value or "").strip())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3] + "..."


def count_group_evidence(group: dict[str, object]) -> int:
    return sum(
        int(content.get("evidence_count", len(content.get("evidence", []))))
        for content in group.get("contents", [])
    )


def get_primary_strategy(group: dict[str, object]) -> tuple[str, str]:
    for strategy in ((group.get("taxonomy") or {}).get("strategies") or []):
        if strategy.get("is_primary"):
            return strategy.get("term_id", ""), strategy.get("label", "")
    strategies = ((group.get("taxonomy") or {}).get("strategies") or [])
    if not strategies:
        return "", ""
    return strategies[0].get("term_id", ""), strategies[0].get("label", "")


def get_primary_subdomain(group: dict[str, object]) -> tuple[str, str]:
    primary_subdomain = ((group.get("taxonomy") or {}).get("primary_tech_subdomain")) or {}
    return primary_subdomain.get("term_id", ""), primary_subdomain.get("label", "")


def get_primary_evidence_meta(group: dict[str, object]) -> tuple[str, str]:
    for content in group.get("contents", []):
        primary_evidence = content.get("primary_policy_evidence") or {}
        document = primary_evidence.get("document") or {}
        if document.get("document_id"):
            return document.get("document_id", ""), primary_evidence.get("location_value", "")
        evidence = content.get("evidence") or []
        if evidence:
            first = evidence[0]
            first_document = first.get("document") or {}
            return first_document.get("document_id", ""), first.get("location_value", "")
    return "", ""


def sort_provisional_group(
    group: dict[str, object],
    domain_priority_tier: str,
    tech_domain_display_order: int,
) -> tuple[int, int, int, int, int, str]:
    policy = group.get("policy") or {}
    bucket = group.get("bucket") or {}
    primary_strategy_id, _ = get_primary_strategy(group)
    return (
        DOMAIN_PRIORITY_ORDER.get(domain_priority_tier, 9),
        tech_domain_display_order,
        RESOURCE_CATEGORY_ORDER.get(bucket.get("resource_category_id", ""), 9),
        0 if primary_strategy_id else 1,
        -count_group_evidence(group),
        f"{policy.get('policy_order', 999):04d}:{group.get('policy_item_group_id', '')}",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--projection-json", required=True)
    parser.add_argument("--out-csv", required=True)
    parser.add_argument("--out-summary-json", required=True)
    args = parser.parse_args()

    payload = load_json(Path(args.projection_json))
    projected_domains = {
        domain.get("tech_domain_id", ""): domain
        for domain in payload.get("tech_domains", [])
        if domain.get("tech_domain_id")
    }
    domain_index = {
        entry.get("tech_domain_id", ""): {
            "tech_domain_id": entry.get("tech_domain_id", ""),
            "tech_domain_label": entry.get("tech_domain_label", ""),
            "display_order": int(entry.get("display_order", 999)),
        }
        for entry in payload.get("tech_domain_filters", [])
        if entry.get("tech_domain_id")
    }
    for tech_domain_id, domain in projected_domains.items():
        if tech_domain_id not in domain_index:
            domain_index[tech_domain_id] = {
                "tech_domain_id": tech_domain_id,
                "tech_domain_label": domain.get("tech_domain_label", ""),
                "display_order": int(domain.get("display_order", 999)),
            }

    domain_summaries: list[dict[str, object]] = []
    queue_rows: list[dict[str, object]] = []
    empty_domains: list[dict[str, object]] = []

    for domain_meta in sorted(domain_index.values(), key=lambda row: int(row["display_order"])):
        tech_domain_id = domain_meta.get("tech_domain_id", "")
        tech_domain_label = domain_meta.get("tech_domain_label", "")
        display_order = int(domain_meta.get("display_order", 999))
        domain = projected_domains.get(tech_domain_id, {})
        groups = domain.get("groups", [])
        curated_groups = [group for group in groups if group.get("group_status") in CURATED_GROUP_STATUSES]
        provisional_groups = [group for group in groups if group.get("group_status") not in CURATED_GROUP_STATUSES]
        policy_ids = sorted(
            {
                (group.get("policy") or {}).get("policy_id")
                for group in groups
                if (group.get("policy") or {}).get("policy_id")
            }
        )

        if not groups:
            empty_domains.append(
                {
                    "tech_domain_id": tech_domain_id,
                    "tech_domain_label": tech_domain_label,
                    "display_order": display_order,
                    "reason": "no_projected_groups",
                }
            )
            domain_summaries.append(
                {
                    "tech_domain_id": tech_domain_id,
                    "tech_domain_label": tech_domain_label,
                    "display_order": display_order,
                    "policy_count": 0,
                    "group_count": 0,
                    "curated_group_count": 0,
                    "provisional_group_count": 0,
                    "content_count": 0,
                    "curated_content_count": 0,
                    "provisional_content_count": 0,
                    "queue_item_count": 0,
                    "curation_stage": "empty",
                }
            )
            continue

        if provisional_groups and not curated_groups:
            curation_stage = "seed_curated"
        elif provisional_groups:
            curation_stage = "expand_curated"
        else:
            curation_stage = "covered"

        domain_summary = {
            "tech_domain_id": tech_domain_id,
            "tech_domain_label": tech_domain_label,
            "display_order": display_order,
            "policy_count": len(policy_ids),
            "group_count": len(groups),
            "curated_group_count": len(curated_groups),
            "provisional_group_count": len(provisional_groups),
            "content_count": sum(len(group.get("contents", [])) for group in groups),
            "curated_content_count": sum(len(group.get("contents", [])) for group in curated_groups),
            "provisional_content_count": sum(len(group.get("contents", [])) for group in provisional_groups),
            "queue_item_count": len(provisional_groups),
            "curation_stage": curation_stage,
        }
        domain_summaries.append(domain_summary)

        provisional_groups.sort(
            key=lambda group: sort_provisional_group(
                group,
                curation_stage,
                display_order,
            )
        )

        for within_domain_rank, group in enumerate(provisional_groups, start=1):
            policy = group.get("policy") or {}
            bucket = group.get("bucket") or {}
            primary_strategy_id, primary_strategy_label = get_primary_strategy(group)
            primary_subdomain_id, primary_subdomain_label = get_primary_subdomain(group)
            primary_document_id, primary_location_value = get_primary_evidence_meta(group)
            evidence_count = count_group_evidence(group)
            recommendation_reason = (
                "domain has no curated seed yet; promote one representative provisional group first"
                if curation_stage == "seed_curated"
                else "domain already has curated seed; expand curated breadth with remaining provisional groups"
            )

            queue_rows.append(
                {
                    "priority_rank": 0,
                    "domain_priority_tier": curation_stage,
                    "tech_domain_id": tech_domain_id,
                    "tech_domain_label": tech_domain_label,
                    "tech_domain_display_order": display_order,
                    "within_domain_rank": within_domain_rank,
                    "domain_group_count": domain_summary["group_count"],
                    "domain_curated_group_count": domain_summary["curated_group_count"],
                    "domain_provisional_group_count": domain_summary["provisional_group_count"],
                    "domain_policy_count": domain_summary["policy_count"],
                    "policy_id": policy.get("policy_id", ""),
                    "policy_name": policy.get("policy_name", ""),
                    "policy_order": policy.get("policy_order", ""),
                    "resource_category_id": bucket.get("resource_category_id", ""),
                    "resource_category_label": bucket.get("resource_category_label", ""),
                    "policy_item_group_id": group.get("policy_item_group_id", ""),
                    "group_label": group.get("group_label", ""),
                    "group_summary": compress_text(group.get("group_summary", "")),
                    "projection_source": group.get("projection_source", ""),
                    "group_status": group.get("group_status", ""),
                    "content_count": len(group.get("contents", [])),
                    "evidence_count": evidence_count,
                    "source_policy_item_id": group.get("source_policy_item_id", ""),
                    "primary_strategy_id": primary_strategy_id,
                    "primary_strategy_label": primary_strategy_label,
                    "primary_tech_subdomain_id": primary_subdomain_id,
                    "primary_tech_subdomain_label": primary_subdomain_label,
                    "primary_document_id": primary_document_id,
                    "primary_location_value": primary_location_value,
                    "recommendation_reason": recommendation_reason,
                }
            )

    queue_rows.sort(
        key=lambda row: (
            DOMAIN_PRIORITY_ORDER.get(str(row["domain_priority_tier"]), 9),
            int(row["tech_domain_display_order"]),
            int(row["within_domain_rank"]),
            RESOURCE_CATEGORY_ORDER.get(str(row["resource_category_id"]), 9),
            int(row["policy_order"]) if str(row["policy_order"]).isdigit() else 999,
            str(row["policy_item_group_id"]),
        )
    )
    for index, row in enumerate(queue_rows, start=1):
        row["priority_rank"] = index

    policy_counts: dict[str, int] = {}
    for row in queue_rows:
        policy_key = f"{row['policy_id']} {row['policy_name']}".strip()
        policy_counts[policy_key] = policy_counts.get(policy_key, 0) + 1

    computed_empty_domains = [
        {
            "tech_domain_id": domain["tech_domain_id"],
            "tech_domain_label": domain["tech_domain_label"],
            "display_order": domain["display_order"],
            "reason": "no_projected_groups",
        }
        for domain in domain_summaries
        if domain["curation_stage"] == "empty"
    ]

    summary = {
        "projection_json": args.projection_json,
        "queue_item_count": len(queue_rows),
        "projected_tech_domain_count": sum(1 for domain in domain_summaries if domain["group_count"] > 0),
        "empty_tech_domain_count": len(computed_empty_domains),
        "seed_curated_domain_count": sum(1 for domain in domain_summaries if domain["curation_stage"] == "seed_curated"),
        "expand_curated_domain_count": sum(1 for domain in domain_summaries if domain["curation_stage"] == "expand_curated"),
        "covered_domain_count": sum(1 for domain in domain_summaries if domain["curation_stage"] == "covered"),
        "curated_group_count": sum(int(domain["curated_group_count"]) for domain in domain_summaries),
        "provisional_group_count": sum(int(domain["provisional_group_count"]) for domain in domain_summaries),
        "policy_counts": policy_counts,
        "empty_domains": computed_empty_domains,
        "domain_summaries": sorted(domain_summaries, key=lambda row: int(row["display_order"])),
    }

    write_csv(Path(args.out_csv), queue_rows, OUTPUT_FIELDS)
    write_json(Path(args.out_summary_json), summary)
    print(f"Technology lens curation queue items: {len(queue_rows)}")


if __name__ == "__main__":
    main()
