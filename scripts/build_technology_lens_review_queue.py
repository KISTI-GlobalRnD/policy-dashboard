#!/usr/bin/env python3
"""Build a manual review queue for auto-curated technology lens groups."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path


OUTPUT_FIELDS = [
    "priority_rank",
    "review_priority_tier",
    "tech_domain_id",
    "tech_domain_label",
    "tech_domain_display_order",
    "policy_id",
    "policy_name",
    "policy_order",
    "resource_category_id",
    "resource_category_label",
    "policy_item_group_id",
    "group_label",
    "group_summary",
    "group_status",
    "source_basis_type",
    "content_count",
    "evidence_count",
    "member_item_count",
    "source_policy_item_ids",
    "primary_strategy_id",
    "primary_strategy_label",
    "primary_tech_subdomain_id",
    "primary_tech_subdomain_label",
    "primary_document_id",
    "primary_location_value",
    "review_reason",
]

REVIEW_PRIORITY_ORDER = {
    "auto_expand_review": 0,
    "auto_seed_review": 1,
}

RESOURCE_CATEGORY_ORDER = {
    "technology": 0,
    "infrastructure_institutional": 1,
    "talent": 2,
}


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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--projection-json", required=True)
    parser.add_argument("--out-csv", required=True)
    parser.add_argument("--out-summary-json", required=True)
    args = parser.parse_args()

    payload = load_json(Path(args.projection_json))
    queue_rows: list[dict[str, object]] = []
    domain_counts: dict[str, int] = {}
    policy_counts: dict[str, int] = {}

    for domain in payload.get("tech_domains", []):
        tech_domain_id = domain.get("tech_domain_id", "")
        tech_domain_label = domain.get("tech_domain_label", "")
        display_order = int(domain.get("display_order", 999))
        for group in domain.get("groups", []):
            group_status = group.get("group_status", "")
            if group_status not in {"auto_seed_curated", "auto_expand_curated"}:
                continue

            policy = group.get("policy") or {}
            bucket = group.get("bucket") or {}
            member_item_ids = [member.get("policy_item_id", "") for member in group.get("member_items", []) if member.get("policy_item_id")]
            primary_strategy_id, primary_strategy_label = get_primary_strategy(group)
            primary_subdomain_id, primary_subdomain_label = get_primary_subdomain(group)
            primary_document_id, primary_location_value = get_primary_evidence_meta(group)
            review_priority_tier = "auto_expand_review" if group_status == "auto_expand_curated" else "auto_seed_review"
            review_reason = (
                "auto-expanded group: verify representative label, grouping boundary, and evidence fit"
                if group_status == "auto_expand_curated"
                else "auto-seeded group: verify first curated seed for this technology domain"
            )

            queue_rows.append(
                {
                    "priority_rank": 0,
                    "review_priority_tier": review_priority_tier,
                    "tech_domain_id": tech_domain_id,
                    "tech_domain_label": tech_domain_label,
                    "tech_domain_display_order": display_order,
                    "policy_id": policy.get("policy_id", ""),
                    "policy_name": policy.get("policy_name", ""),
                    "policy_order": policy.get("policy_order", ""),
                    "resource_category_id": bucket.get("resource_category_id", ""),
                    "resource_category_label": bucket.get("resource_category_label", ""),
                    "policy_item_group_id": group.get("policy_item_group_id", ""),
                    "group_label": group.get("group_label", ""),
                    "group_summary": compress_text(group.get("group_summary", "")),
                    "group_status": group_status,
                    "source_basis_type": group.get("source_basis_type", ""),
                    "content_count": len(group.get("contents", [])),
                    "evidence_count": count_group_evidence(group),
                    "member_item_count": len(group.get("member_items", [])),
                    "source_policy_item_ids": "|".join(member_item_ids),
                    "primary_strategy_id": primary_strategy_id,
                    "primary_strategy_label": primary_strategy_label,
                    "primary_tech_subdomain_id": primary_subdomain_id,
                    "primary_tech_subdomain_label": primary_subdomain_label,
                    "primary_document_id": primary_document_id,
                    "primary_location_value": primary_location_value,
                    "review_reason": review_reason,
                }
            )
            domain_counts[tech_domain_id] = domain_counts.get(tech_domain_id, 0) + 1
            policy_key = f"{policy.get('policy_id', '')} {policy.get('policy_name', '')}".strip()
            policy_counts[policy_key] = policy_counts.get(policy_key, 0) + 1

    queue_rows.sort(
        key=lambda row: (
            REVIEW_PRIORITY_ORDER.get(str(row["review_priority_tier"]), 9),
            int(row["tech_domain_display_order"]),
            RESOURCE_CATEGORY_ORDER.get(str(row["resource_category_id"]), 9),
            int(row["policy_order"]) if str(row["policy_order"]).isdigit() else 999,
            str(row["policy_item_group_id"]),
        )
    )
    for index, row in enumerate(queue_rows, start=1):
        row["priority_rank"] = index

    summary = {
        "projection_json": args.projection_json,
        "review_item_count": len(queue_rows),
        "auto_seed_group_count": sum(1 for row in queue_rows if row["group_status"] == "auto_seed_curated"),
        "auto_expand_group_count": sum(1 for row in queue_rows if row["group_status"] == "auto_expand_curated"),
        "tech_domain_counts": domain_counts,
        "policy_counts": policy_counts,
    }

    write_csv(Path(args.out_csv), queue_rows, OUTPUT_FIELDS)
    write_json(Path(args.out_summary_json), summary)
    print(f"Technology lens review items: {len(queue_rows)}")


if __name__ == "__main__":
    main()
