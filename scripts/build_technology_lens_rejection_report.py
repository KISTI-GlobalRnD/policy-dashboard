#!/usr/bin/env python3
"""Build a rejection/review follow-up report for technology lens manual decisions."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict, Counter
from pathlib import Path


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
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_markdown(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    lines.append("# Technology Lens Rejection Follow-up")
    lines.append("")
    lines.append(f"- total_items: {len(rows)}")
    lines.append("")

    by_domain = defaultdict(list)
    for row in rows:
        by_domain[row["tech_domain_label"] or row["tech_domain_id"]].append(row)

    for domain_label in sorted(by_domain):
        lines.append(f"## {domain_label}")
        lines.append("")
        for row in by_domain[domain_label]:
            lines.append(f"- `{row['decision_key']}`")
            lines.append(f"  - policy: {row['policy_name']} ({row['policy_id']})")
            lines.append(f"  - group: {row['group_label']}")
            lines.append(f"  - note: {row['reviewer_notes']}")
            rowsource = row.get("source_policy_item_ids", "")
            if rowsource:
                lines.append(f"  - source_policy_item_ids: {rowsource}")
            lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--decision-csv", required=True)
    parser.add_argument("--out-summary-json", required=True)
    parser.add_argument("--out-rejected-csv", required=True)
    parser.add_argument("--out-rejected-md", required=True)
    args = parser.parse_args()

    rows = read_csv(Path(args.decision_csv))
    status_rows = rows
    status_counts = Counter(row.get("final_decision_status", row.get("decision_status", "pending")) for row in status_rows)
    rejected_rows = [
        row
        for row in status_rows
        if (row.get("final_decision_status") or row.get("decision_status", "")).strip().lower() == "rejected"
    ]

    rejected_counts = Counter(row.get("tech_domain_label", row.get("tech_domain_id", "")) for row in rejected_rows)
    rejected_csv_fields = [
        "decision_key",
        "tech_domain_id",
        "tech_domain_label",
        "policy_id",
        "policy_name",
        "policy_item_group_id",
        "group_label",
        "reviewer_name",
        "reviewer_notes",
        "source_policy_item_ids",
    ]

    write_csv(Path(args.out_rejected_csv), rejected_rows, rejected_csv_fields)
    write_markdown(Path(args.out_rejected_md), rejected_rows)
    summary = {
        "decision_csv": args.decision_csv,
        "total_count": len(status_rows),
        "status_counts": dict(status_counts),
        "rejected_count": len(rejected_rows),
        "rejected_by_tech_domain": dict(rejected_counts),
        "rejected_csv": args.out_rejected_csv,
        "rejected_markdown": args.out_rejected_md,
    }
    write_json(Path(args.out_summary_json), summary)
    print(f"Technology lens rejection report written: rejected={len(rejected_rows)}")


if __name__ == "__main__":
    main()
