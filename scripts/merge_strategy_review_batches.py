#!/usr/bin/env python3
"""Merge editable strategy batch CSVs back into the master decision CSV."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


EDITABLE_FIELDS = [
    "decision_status",
    "reviewed_primary_strategy_id",
    "reviewed_secondary_strategy_ids",
    "reviewed_confidence",
    "reviewer_name",
    "reviewer_notes",
]


def has_review_override(row: dict[str, str]) -> bool:
    decision_status = (row.get("decision_status") or "").strip()
    if decision_status and decision_status != "pending":
        return True
    for field in EDITABLE_FIELDS:
        if field == "decision_status":
            continue
        if (row.get(field) or "").strip():
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--decision-csv", required=True)
    parser.add_argument("--batches-dir", required=True)
    parser.add_argument("--out-summary-json", required=True)
    args = parser.parse_args()

    decision_path = Path(args.decision_csv)
    batch_dir = Path(args.batches_dir)

    decision_rows = read_csv(decision_path)
    if not decision_rows:
        write_json(
            Path(args.out_summary_json),
            {
                "decision_item_count": 0,
                "batch_file_count": 0,
                "merged_item_count": 0,
                "updated_item_count": 0,
                "duplicate_decision_keys": [],
                "missing_decision_keys": [],
            },
        )
        print("Merged strategy batch edits: 0")
        return

    fieldnames = list(decision_rows[0].keys())
    decision_by_key = {row["decision_key"]: row for row in decision_rows if row.get("decision_key")}

    merged_item_count = 0
    updated_item_count = 0
    duplicate_decision_keys: list[str] = []
    missing_decision_keys: list[str] = []
    seen_in_batches: set[str] = set()

    batch_files = sorted(batch_dir.glob("*.csv"))
    for batch_path in batch_files:
        for batch_row in read_csv(batch_path):
            decision_key = batch_row.get("decision_key", "")
            if not decision_key:
                continue
            if not has_review_override(batch_row):
                continue
            if decision_key in seen_in_batches:
                duplicate_decision_keys.append(decision_key)
                continue
            seen_in_batches.add(decision_key)
            decision_row = decision_by_key.get(decision_key)
            if decision_row is None:
                missing_decision_keys.append(decision_key)
                continue

            merged_item_count += 1
            before = tuple(decision_row.get(field, "") for field in EDITABLE_FIELDS)
            for field in EDITABLE_FIELDS:
                decision_row[field] = batch_row.get(field, "")
            after = tuple(decision_row.get(field, "") for field in EDITABLE_FIELDS)
            if before != after:
                updated_item_count += 1

    output_rows = [decision_by_key.get(row["decision_key"], row) for row in decision_rows]
    write_csv(decision_path, output_rows, fieldnames)
    write_json(
        Path(args.out_summary_json),
        {
            "decision_item_count": len(decision_rows),
            "batch_file_count": len(batch_files),
            "merged_item_count": merged_item_count,
            "updated_item_count": updated_item_count,
            "duplicate_decision_keys": sorted(set(duplicate_decision_keys)),
            "missing_decision_keys": sorted(set(missing_decision_keys)),
        },
    )
    print(f"Merged strategy batch edits: {updated_item_count}")


if __name__ == "__main__":
    main()
