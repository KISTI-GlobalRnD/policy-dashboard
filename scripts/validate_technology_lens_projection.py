#!/usr/bin/env python3
"""Validate the exported technology lens projection."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--projection-json", required=True)
    parser.add_argument("--out-report", required=True)
    args = parser.parse_args()

    payload = json.loads(Path(args.projection_json).read_text(encoding="utf-8"))
    issues: list[dict[str, object]] = []

    tech_domains = payload.get("tech_domains", [])
    unassigned_groups = payload.get("unassigned_groups", [])
    assigned_group_ids: set[str] = set()

    for domain in tech_domains:
        domain_id = domain.get("tech_domain_id")
        groups = domain.get("groups", [])
        if domain.get("group_count") != len(groups):
            issues.append(
                {
                    "code": "domain_group_count_mismatch",
                    "tech_domain_id": domain_id,
                    "declared_group_count": domain.get("group_count"),
                    "actual_group_count": len(groups),
                }
            )
        actual_content_count = sum(len(group.get("contents", [])) for group in groups)
        if domain.get("content_count") != actual_content_count:
            issues.append(
                {
                    "code": "domain_content_count_mismatch",
                    "tech_domain_id": domain_id,
                    "declared_content_count": domain.get("content_count"),
                    "actual_content_count": actual_content_count,
                }
            )

        for group in groups:
            group_id = group.get("policy_item_group_id")
            if group_id in assigned_group_ids:
                issues.append(
                    {
                        "code": "duplicate_group_assignment",
                        "policy_item_group_id": group_id,
                        "tech_domain_id": domain_id,
                    }
                )
            assigned_group_ids.add(group_id)

            primary_domain = ((group.get("taxonomy") or {}).get("primary_tech_domain")) or {}
            if primary_domain.get("term_id") != domain_id:
                issues.append(
                    {
                        "code": "primary_domain_root_mismatch",
                        "policy_item_group_id": group_id,
                        "expected_tech_domain_id": domain_id,
                        "actual_primary_tech_domain_id": primary_domain.get("term_id"),
                    }
                )

            contents = group.get("contents", [])
            if not contents:
                issues.append(
                    {
                        "code": "group_without_contents",
                        "policy_item_group_id": group_id,
                    }
                )

            if group.get("content_count") != len(contents):
                issues.append(
                    {
                        "code": "group_content_count_mismatch",
                        "policy_item_group_id": group_id,
                        "declared_content_count": group.get("content_count"),
                        "actual_content_count": len(contents),
                    }
                )

            for content in contents:
                content_id = content.get("policy_item_content_id")
                evidence = content.get("evidence", [])
                if content.get("evidence_count") != len(evidence):
                    issues.append(
                        {
                            "code": "content_evidence_count_mismatch",
                            "policy_item_content_id": content_id,
                            "declared_evidence_count": content.get("evidence_count"),
                            "actual_evidence_count": len(evidence),
                        }
                    )
                if not evidence:
                    issues.append(
                        {
                            "code": "content_without_evidence",
                            "policy_item_content_id": content_id,
                        }
                    )
                    continue

                primary_policy_evidence = content.get("primary_policy_evidence")
                if not primary_policy_evidence:
                    issues.append(
                        {
                            "code": "missing_primary_policy_evidence",
                            "policy_item_content_id": content_id,
                        }
                    )
                elif ((primary_policy_evidence.get("document") or {}).get("doc_role")) != "policy_source":
                    issues.append(
                        {
                            "code": "non_policy_primary_evidence",
                            "policy_item_content_id": content_id,
                            "document_id": (primary_policy_evidence.get("document") or {}).get("document_id"),
                        }
                    )

    unassigned_ids = {group.get("policy_item_group_id") for group in unassigned_groups}
    overlap = sorted(group_id for group_id in unassigned_ids if group_id in assigned_group_ids)
    for group_id in overlap:
        issues.append(
            {
                "code": "assigned_and_unassigned_overlap",
                "policy_item_group_id": group_id,
            }
        )

    stats = ((payload.get("meta") or {}).get("stats")) or {}
    if stats.get("assigned_group_count") != len(assigned_group_ids):
        issues.append(
            {
                "code": "meta_assigned_group_count_mismatch",
                "declared_assigned_group_count": stats.get("assigned_group_count"),
                "actual_assigned_group_count": len(assigned_group_ids),
            }
        )
    if stats.get("unassigned_group_count") != len(unassigned_groups):
        issues.append(
            {
                "code": "meta_unassigned_group_count_mismatch",
                "declared_unassigned_group_count": stats.get("unassigned_group_count"),
                "actual_unassigned_group_count": len(unassigned_groups),
            }
        )

    report = {
        "status": "pass" if not issues else "fail",
        "projection_json": args.projection_json,
        "issue_count": len(issues),
        "assigned_group_count": len(assigned_group_ids),
        "unassigned_group_count": len(unassigned_groups),
        "issues": issues,
    }
    write_json(Path(args.out_report), report)
    print(report["status"])
    print(f"issues={report['issue_count']}")
    if issues:
        sys.exit(1)


if __name__ == "__main__":
    main()
