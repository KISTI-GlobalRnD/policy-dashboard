#!/usr/bin/env python3
"""Apply a curated review decision manifest to a policy-item review workbench."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


REVIEW_FIELDS = [
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
]

EXPECTED_MATCH_FIELDS = [
    "candidate_role_draft",
    "item_label_draft",
    "item_statement_draft",
    "primary_text",
]


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def clean_text(value: str) -> str:
    return " ".join((value or "").split()).strip()


def row_has_review_content(row: dict[str, str]) -> bool:
    review_status = clean_text(row.get("review_status", ""))
    if review_status in {"reviewed", "reviewed_manual"}:
        return True
    non_status_fields = [field for field in REVIEW_FIELDS if field != "review_status"]
    return any(clean_text(row.get(field, "")) for field in non_status_fields)


def mismatch_details(
    decision_row: dict[str, str],
    target_row: dict[str, str],
) -> dict[str, dict[str, str]]:
    mismatches: dict[str, dict[str, str]] = {}
    for field in EXPECTED_MATCH_FIELDS:
        expected_value = clean_text(decision_row.get(field, ""))
        if not expected_value:
            continue
        actual_value = clean_text(target_row.get(field, ""))
        if expected_value != actual_value:
            mismatches[field] = {
                "expected": decision_row.get(field, ""),
                "actual": target_row.get(field, ""),
            }
    return mismatches


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--decision-csv", required=True)
    parser.add_argument("--target-workbench", required=True)
    parser.add_argument("--out-summary-json", required=True)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    decision_path = Path(args.decision_csv)
    target_path = Path(args.target_workbench)

    decision_rows = read_csv_rows(decision_path)
    target_rows = read_csv_rows(target_path)
    target_by_id = {row["merge_candidate_id"]: row for row in target_rows if row.get("merge_candidate_id")}

    applied_count = 0
    skipped_existing_count = 0
    missing_target_ids: list[str] = []
    skipped_existing_ids: list[str] = []
    mismatched_rows: list[dict[str, object]] = []
    decision_counts: Counter[str] = Counter()

    for decision_row in decision_rows:
        merge_candidate_id = clean_text(decision_row.get("merge_candidate_id", ""))
        if not merge_candidate_id:
            continue

        target_row = target_by_id.get(merge_candidate_id)
        if not target_row:
            missing_target_ids.append(merge_candidate_id)
            continue

        mismatches = mismatch_details(decision_row, target_row)
        if mismatches:
            mismatched_rows.append(
                {
                    "merge_candidate_id": merge_candidate_id,
                    "mismatches": mismatches,
                }
            )
            continue

        if row_has_review_content(target_row) and not args.force:
            skipped_existing_count += 1
            skipped_existing_ids.append(merge_candidate_id)
            continue

        for field in REVIEW_FIELDS:
            target_row[field] = decision_row.get(field, "")

        applied_count += 1
        decision_counts[clean_text(decision_row.get("reviewer_decision", "")) or "<blank>"] += 1

    fieldnames = list(target_rows[0].keys()) if target_rows else []
    write_csv(target_path, target_rows, fieldnames)

    summary = {
        "decision_csv": str(decision_path),
        "target_workbench": str(target_path),
        "decision_row_count": len(decision_rows),
        "applied_count": applied_count,
        "skipped_existing_count": skipped_existing_count,
        "missing_target_count": len(missing_target_ids),
        "mismatched_count": len(mismatched_rows),
        "applied_decision_counts": dict(decision_counts),
        "skipped_existing_ids": skipped_existing_ids,
        "missing_target_ids": missing_target_ids,
        "mismatched_rows": mismatched_rows,
        "force": args.force,
    }
    write_json(Path(args.out_summary_json), summary)
    print(f"Applied manual review decisions: {applied_count}")


if __name__ == "__main__":
    main()
