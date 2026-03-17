#!/usr/bin/env python3
"""Build tech-domain review packets from the technology lens decision CSV."""

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
    "primary_document_id",
    "primary_location_value",
    "reviewed_group_label",
    "reviewed_group_summary",
    "reviewed_group_description",
    "reviewer_name",
    "reviewer_notes",
]


INDEX_FIELDS = [
    "tech_domain_id",
    "tech_domain_label",
    "output_csv",
    "active_item_count",
    "pending_count",
    "approved_count",
    "revised_count",
    "rejected_count",
    "deferred_count",
    "inactive_count",
]


STATUS_ORDER = {
    "pending": 0,
    "deferred": 1,
    "approved": 2,
    "revised": 3,
    "rejected": 4,
}


RESOURCE_CATEGORY_ORDER = {
    "technology": 0,
    "infrastructure_institutional": 1,
    "talent": 2,
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
    return value or "tech-domain"


def row_sort_key(row: dict[str, str]) -> tuple[int, int, str, str]:
    return (
        STATUS_ORDER.get(row.get("decision_status", ""), 9),
        RESOURCE_CATEGORY_ORDER.get(row.get("resource_category_id", ""), 9),
        row.get("group_label", ""),
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
        key = (row["tech_domain_id"], row["tech_domain_label"])
        grouped.setdefault(key, []).append(row)

    index_rows: list[dict[str, object]] = []
    summary: dict[str, object] = {
        "tech_domain_packet_count": 0,
        "tech_domain_packets": [],
        "total_item_count": len(decision_rows),
        "active_item_count": 0,
        "pending_count": 0,
        "approved_count": 0,
        "revised_count": 0,
        "rejected_count": 0,
        "deferred_count": 0,
    }

    for (tech_domain_id, tech_domain_label), rows in sorted(grouped.items()):
        sorted_rows = sorted(rows, key=row_sort_key)
        relative_path = Path(f"{tech_domain_id}__{slugify(tech_domain_label)}__technology-lens-review.csv")
        output_path = packet_root / relative_path
        packet_rows = [{field: row.get(field, "") for field in PACKET_FIELDS} for row in sorted_rows]
        write_csv(output_path, packet_rows, PACKET_FIELDS)

        status_counts: dict[str, int] = {"pending": 0, "approved": 0, "revised": 0, "rejected": 0, "deferred": 0}
        active_item_count = 0
        inactive_count = 0
        for row in sorted_rows:
            status = row.get("decision_status", "") or "pending"
            if status in status_counts:
                status_counts[status] += 1
            if row.get("active_in_queue", "no") == "yes":
                active_item_count += 1
            else:
                inactive_count += 1

        index_row = {
            "tech_domain_id": tech_domain_id,
            "tech_domain_label": tech_domain_label,
            "output_csv": str(relative_path).replace("\\", "/"),
            "active_item_count": active_item_count,
            "pending_count": status_counts["pending"],
            "approved_count": status_counts["approved"],
            "revised_count": status_counts["revised"],
            "rejected_count": status_counts["rejected"],
            "deferred_count": status_counts["deferred"],
            "inactive_count": inactive_count,
        }
        index_rows.append(index_row)
        summary["tech_domain_packets"].append(index_row)
        summary["tech_domain_packet_count"] += 1
        summary["active_item_count"] += active_item_count
        summary["pending_count"] += status_counts["pending"]
        summary["approved_count"] += status_counts["approved"]
        summary["revised_count"] += status_counts["revised"]
        summary["rejected_count"] += status_counts["rejected"]
        summary["deferred_count"] += status_counts["deferred"]

    index_rows.sort(key=lambda row: (-int(row["active_item_count"]), row["tech_domain_id"]))
    summary["tech_domain_packets"] = index_rows

    write_csv(Path(args.out_index_csv), index_rows, INDEX_FIELDS)
    write_json(Path(args.out_summary_json), summary)
    print(f"Technology lens review packets: {len(index_rows)}")


if __name__ == "__main__":
    main()
