#!/usr/bin/env python3
"""Sync unresolved strategy review queue items into a durable decision CSV."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path


DECISION_FIELDS = [
    "decision_key",
    "active_in_queue",
    "policy_item_id",
    "policy_id",
    "policy_name",
    "bucket_label",
    "item_label",
    "primary_evidence_id",
    "evidence_preview",
    "tech_domains",
    "suggested_primary_strategy_id",
    "suggested_primary_strategy_label",
    "suggested_primary_strategy_score",
    "alternate_strategy_ids",
    "alternate_strategy_labels",
    "alignment_exception_ids",
    "alignment_exception_notes",
    "auto_seed_blocked",
    "decision_status",
    "reviewed_primary_strategy_id",
    "reviewed_secondary_strategy_ids",
    "reviewed_confidence",
    "reviewer_name",
    "reviewer_notes",
]


EDITABLE_FIELDS = {
    "decision_status",
    "reviewed_primary_strategy_id",
    "reviewed_secondary_strategy_ids",
    "reviewed_confidence",
    "reviewer_name",
    "reviewer_notes",
}


def has_review_override(existing_row: dict[str, str]) -> bool:
    decision_status = (existing_row.get("decision_status") or "").strip()
    if decision_status and decision_status != "pending":
        return True
    for field in EDITABLE_FIELDS - {"decision_status"}:
        if (existing_row.get(field) or "").strip():
            return True
    return False


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


def parse_ids(value: str) -> list[str]:
    tokens: list[str] = []
    for token in re.split(r"\s*\|\s*|\s*,\s*", value or ""):
        cleaned = token.strip()
        if cleaned:
            tokens.append(cleaned)
    return tokens


def parse_score(value: str) -> int:
    try:
        return int((value or "").strip())
    except ValueError:
        return 0


def build_decision_row(
    queue_row: dict[str, str],
    existing_row: dict[str, str] | None = None,
    *,
    auto_seed_policy_ids: set[str],
    require_tech_domains_for_auto_review_policy_ids: set[str],
    auto_review_min_score: int,
) -> dict[str, str]:
    existing_row = existing_row or {}
    row = {
        "decision_key": queue_row["decision_key"],
        "active_in_queue": "yes",
        "policy_item_id": queue_row["policy_item_id"],
        "policy_id": queue_row["policy_id"],
        "policy_name": queue_row["policy_name"],
        "bucket_label": queue_row["bucket_label"],
        "item_label": queue_row["item_label"],
        "primary_evidence_id": queue_row["primary_evidence_id"],
        "evidence_preview": queue_row["evidence_preview"],
        "tech_domains": queue_row.get("tech_domains", ""),
        "suggested_primary_strategy_id": queue_row["suggested_strategy_id"],
        "suggested_primary_strategy_label": queue_row["suggested_strategy_label"],
        "suggested_primary_strategy_score": queue_row.get("suggested_strategy_score", ""),
        "alternate_strategy_ids": queue_row["alternate_strategy_ids"],
        "alternate_strategy_labels": queue_row["alternate_strategy_labels"],
        "alignment_exception_ids": queue_row.get("alignment_exception_ids", ""),
        "alignment_exception_notes": queue_row.get("alignment_exception_notes", ""),
        "auto_seed_blocked": queue_row.get("auto_seed_blocked", ""),
        "decision_status": "pending",
        "reviewed_primary_strategy_id": "",
        "reviewed_secondary_strategy_ids": "",
        "reviewed_confidence": "",
        "reviewer_name": "",
        "reviewer_notes": "",
    }

    preserve_existing_override = not (
        (queue_row.get("auto_seed_blocked") or "").strip().lower() == "yes"
        and (existing_row.get("reviewer_name") or "").strip() == "auto_seed"
        and (existing_row.get("decision_status") or "").strip() == "reviewed"
        and (existing_row.get("reviewed_primary_strategy_id") or "").strip()
        == (queue_row.get("suggested_strategy_id") or "").strip()
    )

    if preserve_existing_override:
        for field in EDITABLE_FIELDS:
            if existing_row.get(field):
                row[field] = existing_row[field]

    if preserve_existing_override and has_review_override(existing_row):
        return row

    policy_id = queue_row["policy_id"]
    if policy_id not in auto_seed_policy_ids:
        return row

    if (queue_row.get("auto_seed_blocked") or "").strip().lower() == "yes":
        return row

    has_tech_domains = bool((queue_row.get("tech_domains") or "").strip())
    suggested_primary = (queue_row.get("suggested_strategy_id") or "").strip()
    if suggested_primary:
        if policy_id in require_tech_domains_for_auto_review_policy_ids and not has_tech_domains:
            return row
        score = parse_score(queue_row.get("suggested_strategy_score", ""))
        if score >= auto_review_min_score:
            secondary_ids = parse_ids(queue_row.get("alternate_strategy_ids", ""))[:2]
            row["decision_status"] = "reviewed"
            row["reviewed_primary_strategy_id"] = suggested_primary
            row["reviewed_secondary_strategy_ids"] = " | ".join(
                strategy_id for strategy_id in secondary_ids if strategy_id != suggested_primary
            )
            row["reviewed_confidence"] = "high" if score >= 3 else "medium"
            row["reviewer_name"] = "auto_seed"
            row["reviewer_notes"] = f"provisional_auto_seed_from_queue(score={score})"
            return row

    row["decision_status"] = "no_strategy"
    row["reviewed_confidence"] = "medium"
    row["reviewer_name"] = "auto_seed"
    row["reviewer_notes"] = "provisional_auto_seed_no_strategy(no_queue_suggestion)"
    return row


def summarize(rows: list[dict[str, str]]) -> dict[str, object]:
    status_counts: dict[str, int] = {}
    active_counts: dict[str, int] = {"yes": 0, "no": 0}
    auto_seeded_count = 0
    for row in rows:
        status = row["decision_status"] or "pending"
        status_counts[status] = status_counts.get(status, 0) + 1
        active = row["active_in_queue"] or "no"
        active_counts[active] = active_counts.get(active, 0) + 1
        if (row.get("reviewer_name") or "").strip() == "auto_seed":
            auto_seeded_count += 1
    return {
        "decision_item_count": len(rows),
        "active_in_queue_count": active_counts.get("yes", 0),
        "inactive_preserved_count": active_counts.get("no", 0),
        "status_counts": status_counts,
        "auto_seeded_count": auto_seeded_count,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue-csv", required=True)
    parser.add_argument("--out-decision-csv", required=True)
    parser.add_argument("--out-summary-json", required=True)
    parser.add_argument("--auto-seed-policy-ids", default="")
    parser.add_argument("--require-tech-domains-for-auto-review-policy-ids", default="")
    parser.add_argument("--auto-review-min-score", type=int, default=2)
    args = parser.parse_args()

    queue_rows = read_csv(Path(args.queue_csv))
    decision_path = Path(args.out_decision_csv)
    existing_rows = read_csv(decision_path)
    existing_by_key = {row["decision_key"]: row for row in existing_rows if row.get("decision_key")}
    auto_seed_policy_ids = {token.strip() for token in args.auto_seed_policy_ids.split(",") if token.strip()}
    require_tech_domains_for_auto_review_policy_ids = {
        token.strip() for token in args.require_tech_domains_for_auto_review_policy_ids.split(",") if token.strip()
    }

    output_rows: list[dict[str, str]] = []
    seen_keys: set[str] = set()

    for queue_row in queue_rows:
        decision_key = queue_row["decision_key"]
        seen_keys.add(decision_key)
        output_rows.append(
            build_decision_row(
                queue_row,
                existing_by_key.get(decision_key),
                auto_seed_policy_ids=auto_seed_policy_ids,
                require_tech_domains_for_auto_review_policy_ids=require_tech_domains_for_auto_review_policy_ids,
                auto_review_min_score=args.auto_review_min_score,
            )
        )

    preserved_statuses = {"reviewed", "no_strategy", "deferred"}
    for existing_row in existing_rows:
        decision_key = existing_row.get("decision_key", "")
        if not decision_key or decision_key in seen_keys:
            continue
        if (existing_row.get("decision_status") or "pending") not in preserved_statuses:
            continue
        preserved = {field: existing_row.get(field, "") for field in DECISION_FIELDS}
        preserved["active_in_queue"] = "no"
        output_rows.append(preserved)

    write_csv(decision_path, output_rows, DECISION_FIELDS)
    write_json(Path(args.out_summary_json), summarize(output_rows))
    print(f"Decision rows synced: {len(output_rows)}")


if __name__ == "__main__":
    main()
