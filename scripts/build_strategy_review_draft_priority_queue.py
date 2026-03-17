#!/usr/bin/env python3
"""Aggregate high-attention strategy draft items into a priority review queue."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


OUTPUT_FIELDS = [
    "priority_rank",
    "batch_name",
    "decision_key",
    "review_item_id",
    "policy_id",
    "policy_name",
    "bucket_label",
    "item_label",
    "recommended_decision_status",
    "recommended_primary_strategy_id",
    "recommended_secondary_strategy_ids",
    "recommended_confidence",
    "manual_attention",
    "recommendation_reason",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
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


def sort_key(row: dict[str, str]) -> tuple[int, int, str, str]:
    attention_order = {"high": 0, "medium": 1, "low": 2}
    status_order = {"deferred": 0, "no_strategy": 1, "reviewed": 2}
    return (
        attention_order.get(row.get("manual_attention", ""), 9),
        status_order.get(row.get("recommended_decision_status", ""), 9),
        row.get("policy_id", ""),
        row.get("decision_key", ""),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--drafts-dir", required=True)
    parser.add_argument("--out-csv", required=True)
    parser.add_argument("--out-summary-json", required=True)
    parser.add_argument("--batch-index-csv")
    args = parser.parse_args()

    drafts_dir = Path(args.drafts_dir)
    if args.batch_index_csv:
        batch_index_rows = read_csv(Path(args.batch_index_csv))
        draft_paths = [
            drafts_dir / f"{Path(row['output_csv']).stem}__draft.csv"
            for row in batch_index_rows
            if row.get("output_csv")
        ]
    else:
        draft_paths = sorted(drafts_dir.glob("*__draft.csv"))
    rows: list[dict[str, str]] = []

    for draft_path in draft_paths:
        batch_name = draft_path.name.replace("__draft.csv", "")
        for row in read_csv(draft_path):
            if row.get("manual_attention") not in {"high", "medium"}:
                continue
            rows.append(
                {
                    "batch_name": batch_name,
                    "decision_key": row.get("decision_key", ""),
                    "review_item_id": row.get("review_item_id", ""),
                    "policy_id": row.get("policy_id", ""),
                    "policy_name": row.get("policy_name", ""),
                    "bucket_label": row.get("bucket_label", ""),
                    "item_label": row.get("item_label", ""),
                    "recommended_decision_status": row.get("recommended_decision_status", ""),
                    "recommended_primary_strategy_id": row.get("recommended_primary_strategy_id", ""),
                    "recommended_secondary_strategy_ids": row.get("recommended_secondary_strategy_ids", ""),
                    "recommended_confidence": row.get("recommended_confidence", ""),
                    "manual_attention": row.get("manual_attention", ""),
                    "recommendation_reason": row.get("recommendation_reason", ""),
                }
            )

    rows.sort(key=sort_key)
    ranked_rows: list[dict[str, object]] = []
    for rank, row in enumerate(rows, start=1):
        ranked = row.copy()
        ranked["priority_rank"] = rank
        ranked_rows.append(ranked)

    summary = {
        "priority_item_count": len(ranked_rows),
        "attention_counts": {},
        "status_counts": {},
        "policy_counts": {},
    }
    for row in ranked_rows:
        attention = row["manual_attention"]
        status = row["recommended_decision_status"]
        policy = f"{row['policy_id']} {row['policy_name']}"
        summary["attention_counts"][attention] = summary["attention_counts"].get(attention, 0) + 1
        summary["status_counts"][status] = summary["status_counts"].get(status, 0) + 1
        summary["policy_counts"][policy] = summary["policy_counts"].get(policy, 0) + 1

    write_csv(Path(args.out_csv), ranked_rows, OUTPUT_FIELDS)
    write_json(Path(args.out_summary_json), summary)
    print(f"Strategy draft priority items: {len(ranked_rows)}")


if __name__ == "__main__":
    main()
