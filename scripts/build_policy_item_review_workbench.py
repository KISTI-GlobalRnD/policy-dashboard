#!/usr/bin/env python3
"""Build a reviewer workbench CSV from a policy-item merge draft."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def read_csv_rows(path: Path) -> list[dict[str, str]]:
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


def review_priority(row: dict[str, str]) -> str:
    role = row.get("candidate_role_draft", "")
    if role in {"meta_program_frame", "problem_or_requirement", "case_example", "background_context"}:
        return "high"
    if role == "regulatory_delta":
        return "medium"
    if int(row.get("member_count", "0") or 0) > 1:
        return "medium"
    if int(row.get("supporting_review_count", "0") or 0) > 0:
        return "medium"
    if not row.get("primary_strategy_candidates", "") and not row.get("tech_domain_candidates", ""):
        return "medium"
    return "low"


def suggested_reviewer_action(row: dict[str, str]) -> str:
    role = row.get("candidate_role_draft", "")
    if role == "meta_program_frame":
        return "drop_or_attach_background"
    if role == "problem_or_requirement":
        return "recast_or_attach_background"
    if role == "case_example":
        return "attach_as_case_example"
    if role == "background_context":
        return "attach_as_background"
    if role == "regulatory_delta":
        return "keep_as_regulatory_delta"
    return "keep_or_merge"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--document-id", required=True)
    parser.add_argument("--out-root", required=True)
    args = parser.parse_args()

    out_root = Path(args.out_root)
    merge_path = out_root / "work/04_ontology/merge_drafts" / f"{args.document_id}__policy-item-merge-draft.csv"
    if not merge_path.exists():
        raise FileNotFoundError(f"Missing merge draft: {merge_path}")

    merge_rows = read_csv_rows(merge_path)
    workbench_rows: list[dict[str, object]] = []

    for row in merge_rows:
        workbench_rows.append(
            {
                "merge_candidate_id": row["merge_candidate_id"],
                "document_id": row["document_id"],
                "page_no": row["page_no"],
                "review_priority": review_priority(row),
                "suggested_reviewer_action": suggested_reviewer_action(row),
                "review_status": "review_required",
                "reviewer_decision": "",
                "reviewer_role_override": "",
                "reviewer_resource_type_override": "",
                "reviewer_strategy_override": "",
                "reviewer_tech_domain_override": "",
                "reviewer_tech_subdomain_override": "",
                "merge_into_candidate_id": "",
                "split_required": "",
                "final_item_label": "",
                "final_item_statement": "",
                "reviewer_notes": "",
                "candidate_role_draft": row["candidate_role_draft"],
                "candidate_role_notes": row.get("candidate_role_notes", ""),
                "bucket_resource_type_guess": row["bucket_resource_type_guess"],
                "primary_strategy_candidates": row["primary_strategy_candidates"],
                "tech_domain_candidates": row["tech_domain_candidates"],
                "tech_subdomain_candidates": row["tech_subdomain_candidates"],
                "merge_confidence": row["merge_confidence"],
                "item_label_draft": row["item_label_draft"],
                "item_statement_draft": row["item_statement_draft"],
                "primary_seed_id": row["primary_seed_id"],
                "member_seed_ids": row["member_seed_ids"],
                "supporting_review_seed_ids": row["supporting_review_seed_ids"],
                "member_count": row["member_count"],
                "supporting_review_count": row["supporting_review_count"],
                "primary_text": row["primary_text"],
            }
        )

    summary = {
        "document_id": args.document_id,
        "merge_candidate_count": len(merge_rows),
        "high_priority_count": sum(1 for row in workbench_rows if row["review_priority"] == "high"),
        "medium_priority_count": sum(1 for row in workbench_rows if row["review_priority"] == "medium"),
        "low_priority_count": sum(1 for row in workbench_rows if row["review_priority"] == "low"),
        "suggested_action_counts": {
            action: sum(1 for row in workbench_rows if row["suggested_reviewer_action"] == action)
            for action in sorted({row["suggested_reviewer_action"] for row in workbench_rows})
        },
    }

    out_dir = out_root / "work/04_ontology/review_workbenches"
    write_csv(
        out_dir / f"{args.document_id}__policy-item-review-workbench.csv",
        workbench_rows,
        [
            "merge_candidate_id",
            "document_id",
            "page_no",
            "review_priority",
            "suggested_reviewer_action",
            "review_status",
            "reviewer_decision",
            "reviewer_role_override",
            "reviewer_resource_type_override",
            "reviewer_strategy_override",
            "reviewer_tech_domain_override",
            "reviewer_tech_subdomain_override",
            "merge_into_candidate_id",
            "split_required",
            "final_item_label",
            "final_item_statement",
            "reviewer_notes",
            "candidate_role_draft",
            "candidate_role_notes",
            "bucket_resource_type_guess",
            "primary_strategy_candidates",
            "tech_domain_candidates",
            "tech_subdomain_candidates",
            "merge_confidence",
            "item_label_draft",
            "item_statement_draft",
            "primary_seed_id",
            "member_seed_ids",
            "supporting_review_seed_ids",
            "member_count",
            "supporting_review_count",
            "primary_text",
        ],
    )
    write_json(out_dir / f"{args.document_id}__policy-item-review-workbench-summary.json", summary)


if __name__ == "__main__":
    main()
