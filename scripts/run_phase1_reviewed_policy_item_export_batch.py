#!/usr/bin/env python3
"""Export reviewed policy items for phase1 documents that have review workbenches."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
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


def reviewed_workbench_stats(path: Path) -> tuple[int, dict[str, int]]:
    reviewed_rows = [
        row
        for row in read_csv_rows(path)
        if (row.get("review_status") or "").strip() in {"reviewed", "reviewed_manual"}
    ]
    decision_counts = Counter((row.get("reviewer_decision") or "").strip() or "<blank>" for row in reviewed_rows)
    return len(reviewed_rows), dict(decision_counts)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-root", required=True)
    parser.add_argument("--documents", nargs="*")
    parser.add_argument("--run-date", default="2026-03-16")
    args = parser.parse_args()

    out_root = Path(args.out_root)
    builder_path = out_root / "scripts/build_reviewed_policy_items_from_workbench.py"
    review_workbench_dir = out_root / "work/04_ontology/review_workbenches"

    if args.documents:
        target_documents = args.documents
    else:
        target_documents = sorted(
            path.name.replace("__policy-item-review-workbench.csv", "")
            for path in review_workbench_dir.glob("*__policy-item-review-workbench.csv")
        )

    rows: list[dict[str, object]] = []
    failed_rows: list[dict[str, object]] = []

    for document_id in target_documents:
        workbench_path = review_workbench_dir / f"{document_id}__policy-item-review-workbench.csv"
        if not workbench_path.exists():
            rows.append(
                {
                    "document_id": document_id,
                    "reviewed_source_row_count": 0,
                    "reviewed_item_count": 0,
                    "evidence_link_count": 0,
                    "taxonomy_row_count": 0,
                    "issue_count": 0,
                    "run_status": "skipped_missing_workbench",
                    "notes": "missing review workbench",
                }
            )
            continue

        reviewed_source_row_count, reviewed_decision_counts = reviewed_workbench_stats(workbench_path)
        if reviewed_source_row_count == 0:
            rows.append(
                {
                    "document_id": document_id,
                    "reviewed_source_row_count": 0,
                    "reviewed_item_count": 0,
                    "evidence_link_count": 0,
                    "taxonomy_row_count": 0,
                    "issue_count": 0,
                    "run_status": "skipped_unreviewed_workbench",
                    "notes": f"reviewed rows absent; decision_counts={reviewed_decision_counts}",
                }
            )
            continue

        command = [
            sys.executable,
            str(builder_path),
            "--document-id",
            document_id,
            "--out-root",
            str(out_root),
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        summary_path = out_root / "work/04_ontology/reviewed_items" / f"{document_id}__reviewed-items-summary.json"
        if result.returncode == 0 and summary_path.exists():
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            rows.append(
                {
                    "document_id": document_id,
                    "reviewed_source_row_count": summary.get("reviewed_source_row_count", reviewed_source_row_count),
                    "reviewed_item_count": summary["reviewed_item_count"],
                    "evidence_link_count": summary["evidence_link_count"],
                    "taxonomy_row_count": summary["taxonomy_row_count"],
                    "issue_count": summary.get("issue_count", 0),
                    "run_status": "completed_with_issues" if summary.get("issue_count", 0) else "completed",
                    "notes": "" if not summary.get("issue_count", 0) else f"issue_counts={summary.get('issue_counts', {})}",
                }
            )
        else:
            failed_rows.append(
                {
                    "document_id": document_id,
                    "reviewed_source_row_count": reviewed_source_row_count,
                    "reviewed_item_count": 0,
                    "evidence_link_count": 0,
                    "taxonomy_row_count": 0,
                    "issue_count": 0,
                    "run_status": "failed",
                    "notes": (result.stderr or result.stdout).strip(),
                }
            )

    all_rows = rows + failed_rows
    summary = {
        "document_count": len(target_documents),
        "completed_count": sum(1 for row in all_rows if row["run_status"] == "completed"),
        "completed_with_issues_count": sum(1 for row in all_rows if row["run_status"] == "completed_with_issues"),
        "skipped_missing_workbench_count": sum(1 for row in all_rows if row["run_status"] == "skipped_missing_workbench"),
        "skipped_unreviewed_workbench_count": sum(1 for row in all_rows if row["run_status"] == "skipped_unreviewed_workbench"),
        "failed_count": sum(1 for row in all_rows if row["run_status"] == "failed"),
        "reviewed_source_row_count_total": sum(int(row["reviewed_source_row_count"]) for row in all_rows),
        "reviewed_item_count_total": sum(
            int(row["reviewed_item_count"])
            for row in all_rows
            if row["run_status"] in {"completed", "completed_with_issues"}
        ),
        "issue_count_total": sum(int(row["issue_count"]) for row in all_rows if row["run_status"] in {"completed", "completed_with_issues"}),
        "documents": all_rows,
    }

    out_dir = out_root / "work/04_ontology/reviewed_items/batch_runs"
    write_json(out_dir / f"{args.run_date}_phase1-reviewed-policy-item-export-batch.json", summary)
    write_csv(
        out_dir / f"{args.run_date}_phase1-reviewed-policy-item-export-batch.csv",
        all_rows,
        [
            "document_id",
            "reviewed_source_row_count",
            "reviewed_item_count",
            "evidence_link_count",
            "taxonomy_row_count",
            "issue_count",
            "run_status",
            "notes",
        ],
    )


if __name__ == "__main__":
    main()
