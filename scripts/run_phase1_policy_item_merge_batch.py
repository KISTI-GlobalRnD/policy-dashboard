#!/usr/bin/env python3
"""Generate policy-item merge drafts for the phase1 policy set."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path


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
    parser.add_argument("--out-root", required=True)
    parser.add_argument("--classification-batch-json")
    args = parser.parse_args()

    out_root = Path(args.out_root)
    classification_batch_path = (
        Path(args.classification_batch_json)
        if args.classification_batch_json
        else out_root / "work/04_ontology/instances/batch_runs/2026-03-14_phase1-paragraph-classification-batch.json"
    )
    batch_payload = json.loads(classification_batch_path.read_text(encoding="utf-8"))
    builder_path = out_root / "scripts/build_policy_item_merge_draft.py"

    rows: list[dict[str, object]] = []
    failed_rows: list[dict[str, object]] = []

    for document in batch_payload["documents"]:
        if document["run_status"] != "completed":
            continue

        command = [
            sys.executable,
            str(builder_path),
            "--document-id",
            document["document_id"],
            "--out-root",
            str(out_root),
        ]
        result = subprocess.run(command, capture_output=True, text=True)

        summary_path = out_root / "work/04_ontology/merge_drafts" / f"{document['document_id']}__policy-item-merge-draft-summary.json"
        if result.returncode == 0 and summary_path.exists():
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            rows.append(
                {
                    "document_id": document["document_id"],
                    "title": document.get("title", ""),
                    "source_format": document.get("source_format", ""),
                    "classification_row_count": summary["classification_row_count"],
                    "merge_candidate_count": summary["merge_candidate_count"],
                    "skipped_primary_count": summary.get("skipped_primary_count", 0),
                    "attached_continuation_group_count": summary["attached_continuation_group_count"],
                    "attached_review_group_count": summary["attached_review_group_count"],
                    "resource_type_guess_count": summary["resource_type_guess_count"],
                    "strategy_candidate_count": summary["strategy_candidate_count"],
                    "tech_domain_candidate_count": summary["tech_domain_candidate_count"],
                    "run_status": "completed",
                    "notes": "",
                }
            )
        else:
            failed_rows.append(
                {
                    "document_id": document["document_id"],
                    "title": document.get("title", ""),
                    "source_format": document.get("source_format", ""),
                    "classification_row_count": document.get("paragraph_count", 0),
                    "merge_candidate_count": 0,
                    "skipped_primary_count": 0,
                    "attached_continuation_group_count": 0,
                    "attached_review_group_count": 0,
                    "resource_type_guess_count": 0,
                    "strategy_candidate_count": 0,
                    "tech_domain_candidate_count": 0,
                    "run_status": "failed",
                    "notes": (result.stderr or result.stdout).strip(),
                }
            )

    all_rows = rows + failed_rows
    summary = {
        "run_date": batch_payload["run_date"],
        "classification_batch_path": str(classification_batch_path.relative_to(out_root)),
        "completed_count": len(rows),
        "failed_count": len(failed_rows),
        "merge_candidate_count_total": sum(int(row["merge_candidate_count"]) for row in rows),
        "skipped_primary_count_total": sum(int(row["skipped_primary_count"]) for row in rows),
        "documents": all_rows,
    }

    out_dir = out_root / "work/04_ontology/merge_drafts/batch_runs"
    json_path = out_dir / "2026-03-14_phase1-policy-item-merge-batch.json"
    csv_path = out_dir / "2026-03-14_phase1-policy-item-merge-batch.csv"

    write_json(json_path, summary)
    write_csv(
        csv_path,
        all_rows,
        [
            "document_id",
            "title",
            "source_format",
            "classification_row_count",
            "merge_candidate_count",
            "skipped_primary_count",
            "attached_continuation_group_count",
            "attached_review_group_count",
            "resource_type_guess_count",
            "strategy_candidate_count",
            "tech_domain_candidate_count",
            "run_status",
            "notes",
        ],
    )


if __name__ == "__main__":
    main()
