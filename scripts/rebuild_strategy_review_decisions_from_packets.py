#!/usr/bin/env python3
"""Rebuild strategy review decision CSV from clean by-policy packet exports."""

from __future__ import annotations

import argparse
import csv
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


def load_exception_drafts(paths: list[Path]) -> dict[str, dict[str, str]]:
    lookup: dict[str, dict[str, str]] = {}
    for path in paths:
        for row in read_csv(path):
            if row.get("decision_key"):
                lookup[row["decision_key"]] = row
    return lookup


def packet_sort_key(row: dict[str, str]) -> tuple[str, str, str]:
    return (
        row.get("policy_id", ""),
        row.get("bucket_label", ""),
        row.get("decision_key", ""),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packets-dir", required=True)
    parser.add_argument("--out-csv", required=True)
    parser.add_argument("--exception-draft-csv", action="append", default=[])
    args = parser.parse_args()

    packets_dir = Path(args.packets_dir)
    packet_rows: list[dict[str, str]] = []
    for packet_csv in sorted(packets_dir.glob("*.csv")):
        packet_rows.extend(read_csv(packet_csv))

    exception_lookup = load_exception_drafts([Path(path) for path in args.exception_draft_csv])

    output_rows: list[dict[str, str]] = []
    for row in sorted(packet_rows, key=packet_sort_key):
        exception_row = exception_lookup.get(row["decision_key"], {})
        output_rows.append(
            {
                "decision_key": row.get("decision_key", ""),
                "active_in_queue": row.get("active_in_queue", ""),
                "policy_item_id": row.get("policy_item_id", ""),
                "policy_id": row.get("policy_id", ""),
                "policy_name": row.get("policy_name", ""),
                "bucket_label": row.get("bucket_label", ""),
                "item_label": row.get("item_label", ""),
                "primary_evidence_id": row.get("primary_evidence_id", ""),
                "evidence_preview": row.get("evidence_preview", ""),
                "tech_domains": exception_row.get("tech_domains", ""),
                "suggested_primary_strategy_id": row.get("suggested_primary_strategy_id", ""),
                "suggested_primary_strategy_label": row.get("suggested_primary_strategy_label", ""),
                "suggested_primary_strategy_score": exception_row.get("suggested_primary_strategy_score", ""),
                "alternate_strategy_ids": row.get("alternate_strategy_ids", ""),
                "alternate_strategy_labels": row.get("alternate_strategy_labels", ""),
                "alignment_exception_ids": exception_row.get("exception_id", ""),
                "alignment_exception_notes": exception_row.get("alignment_exception_notes", ""),
                "auto_seed_blocked": exception_row.get("auto_seed_blocked", ""),
                "decision_status": row.get("decision_status", ""),
                "reviewed_primary_strategy_id": row.get("reviewed_primary_strategy_id", ""),
                "reviewed_secondary_strategy_ids": row.get("reviewed_secondary_strategy_ids", ""),
                "reviewed_confidence": row.get("reviewed_confidence", ""),
                "reviewer_name": row.get("reviewer_name", ""),
                "reviewer_notes": row.get("reviewer_notes", ""),
            }
        )

    write_csv(Path(args.out_csv), output_rows, DECISION_FIELDS)
    print(f"Rebuilt decision rows from packets: {len(output_rows)}")


if __name__ == "__main__":
    main()
