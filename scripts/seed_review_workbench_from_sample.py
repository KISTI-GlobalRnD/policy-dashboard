#!/usr/bin/env python3
"""Seed reviewed decisions from a reviewed sample workbench into a real workbench."""

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


def core_text_signature(row: dict[str, str]) -> tuple[str, str, str]:
    return (
        row.get("item_label_draft", ""),
        row.get("item_statement_draft", ""),
        row.get("primary_text", ""),
    )


def row_has_review_content(row: dict[str, str]) -> bool:
    review_status = (row.get("review_status", "") or "").strip()
    if review_status in {"reviewed", "reviewed_manual"}:
        return True
    non_status_fields = [field for field in REVIEW_FIELDS if field != "review_status"]
    return any((row.get(field, "") or "").strip() for field in non_status_fields)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample-workbench", required=True)
    parser.add_argument("--target-workbench", required=True)
    parser.add_argument("--out-summary-json", required=True)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    sample_path = Path(args.sample_workbench)
    target_path = Path(args.target_workbench)

    sample_rows = read_csv_rows(sample_path)
    target_rows = read_csv_rows(target_path)
    target_by_id = {row["merge_candidate_id"]: row for row in target_rows if row.get("merge_candidate_id")}

    applied_count = 0
    skipped_existing_count = 0
    missing_target_ids: list[str] = []
    mismatched_ids: list[str] = []
    seeded_decision_counts: Counter[str] = Counter()

    for sample_row in sample_rows:
        if (sample_row.get("review_status") or "").strip() not in {"reviewed", "reviewed_manual"}:
            continue

        merge_candidate_id = sample_row["merge_candidate_id"]
        target_row = target_by_id.get(merge_candidate_id)
        if not target_row:
            missing_target_ids.append(merge_candidate_id)
            continue

        if core_text_signature(sample_row) != core_text_signature(target_row):
            mismatched_ids.append(merge_candidate_id)
            continue

        if row_has_review_content(target_row) and not args.force:
            skipped_existing_count += 1
            continue

        for field in REVIEW_FIELDS:
            target_row[field] = sample_row.get(field, "")

        applied_count += 1
        seeded_decision_counts[(sample_row.get("reviewer_decision") or "").strip() or "<blank>"] += 1

    fieldnames = list(target_rows[0].keys()) if target_rows else []
    write_csv(target_path, target_rows, fieldnames)

    summary = {
        "sample_workbench": str(sample_path),
        "target_workbench": str(target_path),
        "applied_count": applied_count,
        "skipped_existing_count": skipped_existing_count,
        "missing_target_count": len(missing_target_ids),
        "mismatched_count": len(mismatched_ids),
        "seeded_decision_counts": dict(seeded_decision_counts),
        "missing_target_ids": missing_target_ids,
        "mismatched_ids": mismatched_ids,
        "force": args.force,
    }
    write_json(Path(args.out_summary_json), summary)
    print(f"Seeded reviewed workbench rows: {applied_count}")


if __name__ == "__main__":
    main()
