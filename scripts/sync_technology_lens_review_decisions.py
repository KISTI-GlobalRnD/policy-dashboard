#!/usr/bin/env python3
"""Sync technology lens review queue items into a durable decision CSV."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from technology_lens_review_utils import build_decision_key, normalize_source_policy_item_ids


DECISION_FIELDS = [
    "decision_key",
    "active_in_queue",
    "tech_domain_id",
    "tech_domain_label",
    "policy_item_group_id",
    "policy_id",
    "policy_name",
    "resource_category_id",
    "resource_category_label",
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
    "decision_status",
    "reviewed_group_label",
    "reviewed_group_summary",
    "reviewed_group_description",
    "reviewer_name",
    "reviewer_notes",
]


EDITABLE_FIELDS = {
    "decision_status",
    "reviewed_group_label",
    "reviewed_group_summary",
    "reviewed_group_description",
    "reviewer_name",
    "reviewer_notes",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
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


def has_review_override(existing_row: dict[str, str]) -> bool:
    decision_status = (existing_row.get("decision_status") or "").strip()
    if decision_status and decision_status != "pending":
        return True
    for field in EDITABLE_FIELDS - {"decision_status"}:
        if (existing_row.get(field) or "").strip():
            return True
    return False


def build_decision_row(queue_row: dict[str, str], existing_row: dict[str, str] | None = None) -> dict[str, str]:
    existing_row = existing_row or {}
    source_policy_item_ids = normalize_source_policy_item_ids(queue_row.get("source_policy_item_ids", ""))
    row = {
        "decision_key": build_decision_key(
            queue_row.get("tech_domain_id", ""),
            queue_row.get("policy_id", ""),
            queue_row.get("resource_category_id", ""),
            source_policy_item_ids,
        ),
        "active_in_queue": "yes",
        "tech_domain_id": queue_row.get("tech_domain_id", ""),
        "tech_domain_label": queue_row.get("tech_domain_label", ""),
        "policy_item_group_id": queue_row.get("policy_item_group_id", ""),
        "policy_id": queue_row.get("policy_id", ""),
        "policy_name": queue_row.get("policy_name", ""),
        "resource_category_id": queue_row.get("resource_category_id", ""),
        "resource_category_label": queue_row.get("resource_category_label", ""),
        "group_label": queue_row.get("group_label", ""),
        "group_summary": queue_row.get("group_summary", ""),
        "group_status": queue_row.get("group_status", ""),
        "source_basis_type": queue_row.get("source_basis_type", ""),
        "content_count": queue_row.get("content_count", ""),
        "evidence_count": queue_row.get("evidence_count", ""),
        "member_item_count": queue_row.get("member_item_count", ""),
        "source_policy_item_ids": source_policy_item_ids,
        "primary_strategy_id": queue_row.get("primary_strategy_id", ""),
        "primary_strategy_label": queue_row.get("primary_strategy_label", ""),
        "primary_tech_subdomain_id": queue_row.get("primary_tech_subdomain_id", ""),
        "primary_tech_subdomain_label": queue_row.get("primary_tech_subdomain_label", ""),
        "primary_document_id": queue_row.get("primary_document_id", ""),
        "primary_location_value": queue_row.get("primary_location_value", ""),
        "decision_status": "pending",
        "reviewed_group_label": "",
        "reviewed_group_summary": "",
        "reviewed_group_description": "",
        "reviewer_name": "",
        "reviewer_notes": "",
    }
    for field in EDITABLE_FIELDS:
        if existing_row.get(field):
            row[field] = existing_row[field]
    return row


def summarize(rows: list[dict[str, str]]) -> dict[str, object]:
    status_counts: dict[str, int] = {}
    active_counts: dict[str, int] = {"yes": 0, "no": 0}
    for row in rows:
        status = row["decision_status"] or "pending"
        status_counts[status] = status_counts.get(status, 0) + 1
        active = row["active_in_queue"] or "no"
        active_counts[active] = active_counts.get(active, 0) + 1
    return {
        "decision_item_count": len(rows),
        "active_in_queue_count": active_counts.get("yes", 0),
        "inactive_preserved_count": active_counts.get("no", 0),
        "status_counts": status_counts,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue-csv", required=True)
    parser.add_argument("--out-decision-csv", required=True)
    parser.add_argument("--out-summary-json", required=True)
    args = parser.parse_args()

    queue_rows = read_csv(Path(args.queue_csv))
    decision_path = Path(args.out_decision_csv)
    existing_rows = read_csv(decision_path)
    existing_by_key = {row["decision_key"]: row for row in existing_rows if row.get("decision_key")}

    output_rows: list[dict[str, str]] = []
    seen_keys: set[str] = set()

    for queue_row in queue_rows:
        row = build_decision_row(queue_row, None)
        decision_key = row["decision_key"]
        seen_keys.add(decision_key)
        output_rows.append(build_decision_row(queue_row, existing_by_key.get(decision_key)))

    preserved_statuses = {"approved", "revised", "rejected", "deferred"}
    for existing_row in existing_rows:
        decision_key = existing_row.get("decision_key", "")
        if not decision_key or decision_key in seen_keys:
            continue
        if (existing_row.get("decision_status") or "pending") not in preserved_statuses and not has_review_override(existing_row):
            continue
        preserved = {field: existing_row.get(field, "") for field in DECISION_FIELDS}
        preserved["active_in_queue"] = "no"
        output_rows.append(preserved)

    write_csv(decision_path, output_rows, DECISION_FIELDS)
    write_json(Path(args.out_summary_json), summarize(output_rows))
    print(f"Technology lens decision rows synced: {len(output_rows)}")


if __name__ == "__main__":
    main()
