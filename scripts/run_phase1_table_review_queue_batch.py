#!/usr/bin/env python3
"""Build table review queues for phase1 policy documents."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from datetime import date
from pathlib import Path


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def read_registry(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def run_command(command: list[str], cwd: Path) -> tuple[int, str]:
    completed = subprocess.run(
        command,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return completed.returncode, completed.stdout.strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-root", required=True)
    parser.add_argument(
        "--registry-csv",
        default="work/01_scope-and-ia/requirements/04_document-registry.csv",
    )
    args = parser.parse_args()

    out_root = Path(args.out_root)
    registry_path = out_root / args.registry_csv
    rows = read_registry(registry_path)
    target_rows = [
        row
        for row in rows
        if row.get("doc_role") == "policy_source"
        and row.get("scope_track") == "phase1"
        and row.get("include_status") == "include"
    ]

    queue_summaries = []
    for row in target_rows:
        document_id = row["registry_id"]
        command = [
            sys.executable,
            str(out_root / "scripts/build_table_review_queue.py"),
            "--document-id",
            document_id,
            "--out-root",
            str(out_root),
        ]
        return_code, output = run_command(command, out_root)
        summary = {
            "document_id": document_id,
            "title": row.get("normalized_title", ""),
            "run_status": "completed" if return_code == 0 else "failed",
            "review_item_count": "",
            "markdown_candidate_count": "",
            "json_candidate_count": "",
            "structured_table_count": "",
            "layout_false_positive_count": "",
            "review_required_count": "",
            "notes": output[:500] if return_code != 0 else "",
        }
        if return_code == 0:
            summary_path = out_root / "qa/extraction/review_queues" / f"{document_id}__table-review-queue-summary.json"
            if summary_path.exists():
                payload = json.loads(summary_path.read_text(encoding="utf-8"))
                counts = payload.get("suggested_class_counts", {})
                summary["review_item_count"] = payload.get("review_item_count", "")
                summary["markdown_candidate_count"] = payload.get("markdown_candidate_count", "")
                summary["json_candidate_count"] = payload.get("json_candidate_count", "")
                summary["structured_table_count"] = counts.get("structured_table", 0)
                summary["layout_false_positive_count"] = counts.get("layout_false_positive", 0)
                summary["review_required_count"] = counts.get("review_required", 0)
        queue_summaries.append(summary)

    run_date = date.today().isoformat()
    batch_dir = out_root / "qa/extraction/review_queues/batch_runs"
    csv_path = batch_dir / f"{run_date}_phase1-table-review-queue-batch.csv"
    json_path = batch_dir / f"{run_date}_phase1-table-review-queue-batch.json"

    payload = {
        "run_date": run_date,
        "registry_path": str(registry_path.relative_to(out_root)),
        "completed_count": sum(1 for row in queue_summaries if row["run_status"] == "completed"),
        "failed_count": sum(1 for row in queue_summaries if row["run_status"] == "failed"),
        "documents": queue_summaries,
    }

    write_csv(
        csv_path,
        queue_summaries,
        [
            "document_id",
            "title",
            "run_status",
            "review_item_count",
            "markdown_candidate_count",
            "json_candidate_count",
            "structured_table_count",
            "layout_false_positive_count",
            "review_required_count",
            "notes",
        ],
    )
    write_json(json_path, payload)


if __name__ == "__main__":
    main()
