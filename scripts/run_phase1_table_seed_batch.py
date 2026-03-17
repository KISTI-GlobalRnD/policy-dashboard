#!/usr/bin/env python3
"""Seed and apply obvious table review decisions for phase1 policy documents."""

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

    summaries = []
    for row in target_rows:
        document_id = row["registry_id"]
        decision_path = out_root / "qa/extraction/review_decisions" / f"{document_id}__table-review-decisions.json"

        if decision_path.exists():
            summaries.append(
                {
                    "document_id": document_id,
                    "title": row.get("normalized_title", ""),
                    "run_status": "skipped_existing",
                    "reviewed_count": "",
                    "review_required_count": "",
                    "keep_yes_count": "",
                    "keep_no_count": "",
                    "canonical_table_count": "",
                    "notes": "existing_decision_file",
                }
            )
            continue

        seed_command = [
            sys.executable,
            str(out_root / "scripts/seed_table_review_decisions.py"),
            "--document-id",
            document_id,
            "--out-root",
            str(out_root),
        ]
        rc_seed, out_seed = run_command(seed_command, out_root)
        if rc_seed != 0:
            summaries.append(
                {
                    "document_id": document_id,
                    "title": row.get("normalized_title", ""),
                    "run_status": "seed_failed",
                    "reviewed_count": "",
                    "review_required_count": "",
                    "keep_yes_count": "",
                    "keep_no_count": "",
                    "canonical_table_count": "",
                    "notes": out_seed[:500],
                }
            )
            continue

        apply_command = [
            sys.executable,
            str(out_root / "scripts/apply_table_review_decisions.py"),
            "--document-id",
            document_id,
            "--out-root",
            str(out_root),
            "--queue-csv",
            str(out_root / "qa/extraction/review_queues" / f"{document_id}__table-review-queue.csv"),
            "--decision-json",
            str(decision_path),
        ]
        rc_apply, out_apply = run_command(apply_command, out_root)
        if rc_apply != 0:
            summaries.append(
                {
                    "document_id": document_id,
                    "title": row.get("normalized_title", ""),
                    "run_status": "apply_failed",
                    "reviewed_count": "",
                    "review_required_count": "",
                    "keep_yes_count": "",
                    "keep_no_count": "",
                    "canonical_table_count": "",
                    "notes": out_apply[:500],
                }
            )
            continue

        summary_path = out_root / "qa/extraction/reviewed_queues" / f"{document_id}__table-review-reviewed-summary.json"
        payload = json.loads(summary_path.read_text(encoding="utf-8"))
        summaries.append(
            {
                "document_id": document_id,
                "title": row.get("normalized_title", ""),
                "run_status": "completed",
                "reviewed_count": payload.get("reviewed_count", ""),
                "review_required_count": payload.get("review_required_count", ""),
                "keep_yes_count": payload.get("keep_yes_count", ""),
                "keep_no_count": payload.get("keep_no_count", ""),
                "canonical_table_count": payload.get("canonical_table_count", ""),
                "notes": "",
            }
        )

    run_date = date.today().isoformat()
    batch_dir = out_root / "qa/extraction/reviewed_queues/batch_runs"
    csv_path = batch_dir / f"{run_date}_phase1-table-seed-batch.csv"
    json_path = batch_dir / f"{run_date}_phase1-table-seed-batch.json"
    payload = {
        "run_date": run_date,
        "registry_path": str(registry_path.relative_to(out_root)),
        "completed_count": sum(1 for row in summaries if row["run_status"] == "completed"),
        "skipped_existing_count": sum(1 for row in summaries if row["run_status"] == "skipped_existing"),
        "failed_count": sum(1 for row in summaries if row["run_status"] not in {"completed", "skipped_existing"}),
        "documents": summaries,
    }
    write_csv(
        csv_path,
        summaries,
        [
            "document_id",
            "title",
            "run_status",
            "reviewed_count",
            "review_required_count",
            "keep_yes_count",
            "keep_no_count",
            "canonical_table_count",
            "notes",
        ],
    )
    write_json(json_path, payload)


if __name__ == "__main__":
    main()
