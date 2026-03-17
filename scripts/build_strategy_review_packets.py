#!/usr/bin/env python3
"""Build policy-level review packets from the strategy decision CSV."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path


PACKET_FIELDS = [
    "decision_key",
    "active_in_queue",
    "decision_status",
    "policy_item_id",
    "policy_id",
    "policy_name",
    "bucket_label",
    "item_label",
    "primary_evidence_id",
    "evidence_preview",
    "suggested_primary_strategy_id",
    "suggested_primary_strategy_label",
    "alternate_strategy_ids",
    "alternate_strategy_labels",
    "reviewed_primary_strategy_id",
    "reviewed_secondary_strategy_ids",
    "reviewed_confidence",
    "reviewer_name",
    "reviewer_notes",
]


INDEX_FIELDS = [
    "policy_id",
    "policy_name",
    "output_csv",
    "active_item_count",
    "pending_count",
    "reviewed_count",
    "no_strategy_count",
    "deferred_count",
    "inactive_count",
    "bucket_technology_count",
    "bucket_infra_system_count",
    "bucket_talent_count",
]


BUCKET_COLUMN_MAP = {
    "기술": "bucket_technology_count",
    "인프라·제도": "bucket_infra_system_count",
    "인재": "bucket_talent_count",
}


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
    return value or "policy"


def row_sort_key(row: dict[str, str]) -> tuple[int, int, str, str]:
    status_order = {
        "pending": 0,
        "deferred": 1,
        "reviewed": 2,
        "no_strategy": 3,
    }
    bucket_order = {
        "기술": 0,
        "인프라·제도": 1,
        "인재": 2,
    }
    return (
        status_order.get(row.get("decision_status", ""), 9),
        bucket_order.get(row.get("bucket_label", ""), 9),
        row.get("item_label", ""),
        row.get("decision_key", ""),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--decision-csv", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--out-index-csv", required=True)
    parser.add_argument("--out-summary-json", required=True)
    args = parser.parse_args()

    decision_rows = read_csv(Path(args.decision_csv))
    packet_root = Path(args.out_dir)
    grouped: dict[tuple[str, str], list[dict[str, str]]] = {}

    for row in decision_rows:
        key = (row["policy_id"], row["policy_name"])
        grouped.setdefault(key, []).append(row)

    index_rows: list[dict[str, object]] = []
    summary: dict[str, object] = {
        "policy_packet_count": 0,
        "policy_packets": [],
        "total_item_count": len(decision_rows),
        "active_item_count": 0,
        "pending_count": 0,
        "reviewed_count": 0,
        "no_strategy_count": 0,
        "deferred_count": 0,
    }

    for (policy_id, policy_name), rows in sorted(grouped.items()):
        sorted_rows = sorted(rows, key=row_sort_key)
        relative_path = Path(f"{policy_id}__{slugify(policy_name)}__strategy-review.csv")
        output_path = packet_root / relative_path
        packet_rows = [{field: row.get(field, "") for field in PACKET_FIELDS} for row in sorted_rows]
        write_csv(output_path, packet_rows, PACKET_FIELDS)

        status_counts: dict[str, int] = {"pending": 0, "reviewed": 0, "no_strategy": 0, "deferred": 0}
        bucket_counts: dict[str, int] = {column: 0 for column in BUCKET_COLUMN_MAP.values()}
        active_item_count = 0
        inactive_count = 0
        for row in sorted_rows:
            status = row.get("decision_status", "") or "pending"
            if status in status_counts:
                status_counts[status] += 1
            active = row.get("active_in_queue", "no")
            if active == "yes":
                active_item_count += 1
            else:
                inactive_count += 1
            bucket_key = BUCKET_COLUMN_MAP.get(row.get("bucket_label", ""))
            if bucket_key:
                bucket_counts[bucket_key] += 1

        index_row = {
            "policy_id": policy_id,
            "policy_name": policy_name,
            "output_csv": str(relative_path).replace("\\", "/"),
            "active_item_count": active_item_count,
            "pending_count": status_counts["pending"],
            "reviewed_count": status_counts["reviewed"],
            "no_strategy_count": status_counts["no_strategy"],
            "deferred_count": status_counts["deferred"],
            "inactive_count": inactive_count,
            "bucket_technology_count": bucket_counts["bucket_technology_count"],
            "bucket_infra_system_count": bucket_counts["bucket_infra_system_count"],
            "bucket_talent_count": bucket_counts["bucket_talent_count"],
        }
        index_rows.append(index_row)
        summary["policy_packets"].append(index_row)
        summary["policy_packet_count"] += 1
        summary["active_item_count"] += active_item_count
        summary["pending_count"] += status_counts["pending"]
        summary["reviewed_count"] += status_counts["reviewed"]
        summary["no_strategy_count"] += status_counts["no_strategy"]
        summary["deferred_count"] += status_counts["deferred"]

    index_rows.sort(key=lambda row: (-int(row["active_item_count"]), row["policy_id"]))
    summary["policy_packets"] = index_rows

    write_csv(Path(args.out_index_csv), index_rows, INDEX_FIELDS)
    write_json(Path(args.out_summary_json), summary)
    print(f"Policy review packets: {len(index_rows)}")


if __name__ == "__main__":
    main()
