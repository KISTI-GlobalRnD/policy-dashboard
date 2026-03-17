#!/usr/bin/env python3
"""Generate paragraph classification templates for the phase1 policy set."""

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
    parser.add_argument("--normalization-batch-json")
    args = parser.parse_args()

    out_root = Path(args.out_root)
    normalization_batch_path = (
        Path(args.normalization_batch_json)
        if args.normalization_batch_json
        else out_root / "work/03_processing/normalized/batch_runs/2026-03-14_phase1-policy-normalization-batch.json"
    )
    batch_payload = json.loads(normalization_batch_path.read_text(encoding="utf-8"))
    builder_path = out_root / "scripts/build_paragraph_classification_template.py"

    rows = []
    failed_rows = []

    for document in batch_payload["documents"]:
        if document["run_status"] != "completed":
            continue

        command = [
            sys.executable,
            str(builder_path),
            "--document-id",
            document["document_id"],
            "--document-title",
            document.get("title", ""),
            "--out-root",
            str(out_root),
        ]
        result = subprocess.run(command, capture_output=True, text=True)

        summary_path = out_root / "work/04_ontology/instances" / f"{document['document_id']}__classification-template-summary.json"
        if result.returncode == 0 and summary_path.exists():
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            rows.append(
                {
                    "document_id": document["document_id"],
                    "title": document.get("title", ""),
                    "source_format": document.get("source_format", ""),
                    "paragraph_count": summary["paragraph_count"],
                    "policy_item_yes_count": summary["policy_item_yes_count"],
                    "policy_item_review_count": summary["policy_item_review_count"],
                    "policy_item_no_count": summary["policy_item_no_count"],
                    "resource_type_suggested_count": summary["resource_type_suggested_count"],
                    "strategy_suggested_count": summary["strategy_suggested_count"],
                    "tech_domain_suggested_count": summary["tech_domain_suggested_count"],
                    "tech_subdomain_suggested_count": summary["tech_subdomain_suggested_count"],
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
                    "paragraph_count": document.get("paragraph_count", 0),
                    "policy_item_yes_count": 0,
                    "policy_item_review_count": 0,
                    "policy_item_no_count": 0,
                    "resource_type_suggested_count": 0,
                    "strategy_suggested_count": 0,
                    "tech_domain_suggested_count": 0,
                    "tech_subdomain_suggested_count": 0,
                    "run_status": "failed",
                    "notes": (result.stderr or result.stdout).strip(),
                }
            )

    all_rows = rows + failed_rows
    summary = {
        "run_date": batch_payload["run_date"],
        "normalization_batch_path": str(normalization_batch_path.relative_to(out_root)),
        "completed_count": len(rows),
        "failed_count": len(failed_rows),
        "documents": all_rows,
    }

    out_dir = out_root / "work/04_ontology/instances/batch_runs"
    json_path = out_dir / "2026-03-14_phase1-paragraph-classification-batch.json"
    csv_path = out_dir / "2026-03-14_phase1-paragraph-classification-batch.csv"

    write_json(json_path, summary)
    write_csv(
        csv_path,
        all_rows,
        [
            "document_id",
            "title",
            "source_format",
            "paragraph_count",
            "policy_item_yes_count",
            "policy_item_review_count",
            "policy_item_no_count",
            "resource_type_suggested_count",
            "strategy_suggested_count",
            "tech_domain_suggested_count",
            "tech_subdomain_suggested_count",
            "run_status",
            "notes",
        ],
    )


if __name__ == "__main__":
    main()
