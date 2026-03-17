#!/usr/bin/env python3
"""Build policy/bucket review batches from strategy decisions and queue metadata."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

from generated_artifact_utils import cleanup_stale_files


BATCH_FIELDS = [
    "decision_key",
    "review_item_id",
    "policy_item_id",
    "policy_id",
    "policy_name",
    "bucket_label",
    "item_label",
    "primary_evidence_id",
    "tech_domains",
    "evidence_preview",
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


INDEX_FIELDS = [
    "batch_id",
    "policy_id",
    "policy_name",
    "bucket_label",
    "batch_order",
    "output_csv",
    "item_count",
    "with_suggestion_count",
    "without_suggestion_count",
    "max_suggested_score",
    "min_suggested_score",
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


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^0-9a-zA-Z가-힣]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "value"


def parse_score(value: str) -> int:
    try:
        return int((value or "").strip())
    except ValueError:
        return 0


def batch_sort_key(row: dict[str, str]) -> tuple[int, int, int, str, str]:
    status_order = {"pending": 0, "deferred": 1}
    has_no_suggestion = 1 if not row.get("suggested_primary_strategy_id") else 0
    score = parse_score(row.get("suggested_primary_strategy_score", ""))
    return (
        status_order.get(row.get("decision_status", ""), 9),
        has_no_suggestion,
        -score,
        row.get("item_label", ""),
        row.get("decision_key", ""),
    )


def chunk_rows(rows: list[dict[str, str]], size: int) -> list[list[dict[str, str]]]:
    return [rows[index : index + size] for index in range(0, len(rows), size)]


def merge_row(decision_row: dict[str, str], queue_row: dict[str, str] | None) -> dict[str, str]:
    queue_row = queue_row or {}
    return {
        "decision_key": decision_row.get("decision_key", ""),
        "review_item_id": queue_row.get("review_item_id", ""),
        "policy_item_id": decision_row.get("policy_item_id", ""),
        "policy_id": decision_row.get("policy_id", ""),
        "policy_name": decision_row.get("policy_name", ""),
        "bucket_label": decision_row.get("bucket_label", ""),
        "item_label": decision_row.get("item_label", ""),
        "primary_evidence_id": decision_row.get("primary_evidence_id", ""),
        "tech_domains": queue_row.get("tech_domains", ""),
        "evidence_preview": decision_row.get("evidence_preview", ""),
        "suggested_primary_strategy_id": decision_row.get("suggested_primary_strategy_id", ""),
        "suggested_primary_strategy_label": decision_row.get("suggested_primary_strategy_label", ""),
        "suggested_primary_strategy_score": queue_row.get("suggested_strategy_score", ""),
        "alternate_strategy_ids": decision_row.get("alternate_strategy_ids", ""),
        "alternate_strategy_labels": decision_row.get("alternate_strategy_labels", ""),
        "alignment_exception_ids": queue_row.get("alignment_exception_ids", ""),
        "alignment_exception_notes": queue_row.get("alignment_exception_notes", ""),
        "auto_seed_blocked": queue_row.get("auto_seed_blocked", ""),
        "decision_status": decision_row.get("decision_status", ""),
        "reviewed_primary_strategy_id": decision_row.get("reviewed_primary_strategy_id", ""),
        "reviewed_secondary_strategy_ids": decision_row.get("reviewed_secondary_strategy_ids", ""),
        "reviewed_confidence": decision_row.get("reviewed_confidence", ""),
        "reviewer_name": decision_row.get("reviewer_name", ""),
        "reviewer_notes": decision_row.get("reviewer_notes", ""),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--decision-csv", required=True)
    parser.add_argument("--queue-csv", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--out-index-csv", required=True)
    parser.add_argument("--out-summary-json", required=True)
    parser.add_argument("--batch-size", type=int, default=40)
    args = parser.parse_args()

    decision_rows = read_csv(Path(args.decision_csv))
    queue_rows = read_csv(Path(args.queue_csv))
    queue_by_key = {row["decision_key"]: row for row in queue_rows if row.get("decision_key")}

    active_rows = [
        merge_row(row, queue_by_key.get(row.get("decision_key", "")))
        for row in decision_rows
        if row.get("active_in_queue") == "yes" and (row.get("decision_status") or "pending") in {"pending", "deferred"}
    ]

    grouped: dict[tuple[str, str, str], list[dict[str, str]]] = {}
    for row in active_rows:
        key = (row["policy_id"], row["policy_name"], row["bucket_label"])
        grouped.setdefault(key, []).append(row)

    out_dir = Path(args.out_dir)
    index_rows: list[dict[str, object]] = []
    keep_names: set[str] = set()

    for (policy_id, policy_name, bucket_label), rows in sorted(grouped.items()):
        sorted_rows = sorted(rows, key=batch_sort_key)
        for batch_order, batch_rows in enumerate(chunk_rows(sorted_rows, args.batch_size), start=1):
            filename = (
                f"{policy_id}__{slugify(policy_name)}__{slugify(bucket_label)}__batch-{batch_order:02d}.csv"
            )
            output_path = out_dir / filename
            keep_names.add(filename)
            write_csv(output_path, batch_rows, BATCH_FIELDS)

            scores = [parse_score(row["suggested_primary_strategy_score"]) for row in batch_rows if row["suggested_primary_strategy_score"]]
            index_row = {
                "batch_id": f"{policy_id}-{slugify(bucket_label)}-{batch_order:02d}",
                "policy_id": policy_id,
                "policy_name": policy_name,
                "bucket_label": bucket_label,
                "batch_order": batch_order,
                "output_csv": filename,
                "item_count": len(batch_rows),
                "with_suggestion_count": sum(1 for row in batch_rows if row["suggested_primary_strategy_id"]),
                "without_suggestion_count": sum(1 for row in batch_rows if not row["suggested_primary_strategy_id"]),
                "max_suggested_score": max(scores) if scores else 0,
                "min_suggested_score": min(scores) if scores else 0,
            }
            index_rows.append(index_row)

    index_rows.sort(key=lambda row: (-int(row["item_count"]), row["policy_id"], row["batch_order"]))
    summary = {
        "batch_count": len(index_rows),
        "total_item_count": len(active_rows),
        "batch_size": args.batch_size,
        "batches": index_rows,
    }
    summary["removed_stale_files"] = cleanup_stale_files(out_dir, keep_names, ["*.csv"])

    write_csv(Path(args.out_index_csv), index_rows, INDEX_FIELDS)
    write_json(Path(args.out_summary_json), summary)
    print(f"Strategy review batches: {len(index_rows)}")


if __name__ == "__main__":
    main()
