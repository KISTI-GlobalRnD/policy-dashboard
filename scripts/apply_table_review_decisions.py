#!/usr/bin/env python3
"""Apply manual table review decisions to a review queue."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--document-id", required=True)
    parser.add_argument("--out-root", required=True)
    parser.add_argument("--queue-csv", required=True)
    parser.add_argument("--decision-json", required=True)
    args = parser.parse_args()

    out_root = Path(args.out_root)
    queue_path = Path(args.queue_csv)
    decision_path = Path(args.decision_json)

    rows = read_csv(queue_path)
    decisions = json.loads(decision_path.read_text(encoding="utf-8"))
    review_item_updates = decisions.get("review_item_updates", {})
    canonical_tables = decisions.get("canonical_tables", [])

    updated_rows = []
    for row in rows:
        update = review_item_updates.get(row["review_item_id"], {})
        merged = row.copy()
        for key, value in update.items():
            merged[key] = value
        updated_rows.append(merged)

    reviewed_queue_dir = out_root / "qa/extraction/reviewed_queues"
    reviewed_queue_path = reviewed_queue_dir / f"{args.document_id}__table-review-reviewed.csv"
    summary_path = reviewed_queue_dir / f"{args.document_id}__table-review-reviewed-summary.json"

    write_csv(reviewed_queue_path, updated_rows, list(updated_rows[0].keys()))

    summary = {
        "document_id": args.document_id,
        "review_item_count": len(updated_rows),
        "reviewed_count": sum(1 for row in updated_rows if row["review_status"] == "reviewed"),
        "review_required_count": sum(1 for row in updated_rows if row["review_status"] != "reviewed"),
        "keep_yes_count": sum(1 for row in updated_rows if row["keep_for_dashboard"] == "yes"),
        "keep_after_merge_count": sum(1 for row in updated_rows if row["keep_for_dashboard"] == "after_merge"),
        "keep_no_count": sum(1 for row in updated_rows if row["keep_for_dashboard"] == "no"),
        "canonical_table_count": len(canonical_tables),
    }
    write_json(summary_path, summary)

    canonical_dir = out_root / "work/04_ontology/instances"
    canonical_csv_path = canonical_dir / f"{args.document_id}__canonical-tables.csv"
    canonical_json_path = canonical_dir / f"{args.document_id}__canonical-tables.json"

    if canonical_tables:
        write_csv(
            canonical_csv_path,
            canonical_tables,
            [
                "canonical_table_id",
                "document_id",
                "title_hint",
                "page_start",
                "page_end",
                "preferred_candidate_source",
                "preferred_candidate_id",
                "canonical_status",
                "dashboard_ready",
                "source_review_item_ids",
                "notes",
            ],
        )
        write_json(canonical_json_path, canonical_tables)
    else:
        write_csv(
            canonical_csv_path,
            [],
            [
                "canonical_table_id",
                "document_id",
                "title_hint",
                "page_start",
                "page_end",
                "preferred_candidate_source",
                "preferred_candidate_id",
                "canonical_status",
                "dashboard_ready",
                "source_review_item_ids",
                "notes",
            ],
        )
        write_json(canonical_json_path, [])


if __name__ == "__main__":
    main()
