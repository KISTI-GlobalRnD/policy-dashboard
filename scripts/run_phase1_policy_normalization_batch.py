#!/usr/bin/env python3
"""Normalize ontology source text outputs into paragraph-level working files."""

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


def load_manifest(out_root: Path, document_id: str) -> dict | None:
    manifest_path = out_root / "work/02_structured-extraction/manifests" / f"{document_id}_manifest.json"
    if not manifest_path.exists():
        return None
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def build_command(out_root: Path, document_id: str, source_format: str) -> list[str]:
    scripts_dir = out_root / "scripts"
    if source_format == "pdf":
        script_name = "normalize_pdf_page_text.py"
    else:
        script_name = "normalize_structured_text_blocks.py"
    return [
        sys.executable,
        str(scripts_dir / script_name),
        "--document-id",
        document_id,
        "--out-root",
        str(out_root),
    ]


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

    supported_formats = {"pdf", "hwp", "hwpx", "docx"}
    target_rows = [
        row
        for row in rows
        if row.get("include_status") in {"include", "support"}
        and row.get("source_format", "").lower() in supported_formats
    ]

    summary_rows = []
    for row in target_rows:
        document_id = row["registry_id"]
        manifest = load_manifest(out_root, document_id)
        source_format = manifest.get("source_format", "").lower() if manifest else row.get("source_format", "").lower()
        summary = {
            "document_id": document_id,
            "title": row.get("normalized_title", ""),
            "source_format": source_format,
            "run_status": "",
            "paragraph_count": "",
            "page_count": "",
            "notes": "",
        }

        if manifest is None:
            summary["run_status"] = "missing_manifest"
            summary_rows.append(summary)
            continue

        command = build_command(out_root, document_id, source_format)
        return_code, output = run_command(command, out_root)
        if return_code != 0:
            summary["run_status"] = "failed"
            summary["notes"] = output[:500]
            summary_rows.append(summary)
            continue

        report_path = out_root / "work/03_processing/normalized" / f"{document_id}__text-normalization-report.json"
        if not report_path.exists():
            summary["run_status"] = "missing_report"
            summary_rows.append(summary)
            continue

        report = json.loads(report_path.read_text(encoding="utf-8"))
        summary["run_status"] = "completed"
        summary["paragraph_count"] = report.get("paragraph_count", "")
        summary["page_count"] = report.get("page_count", "")
        summary_rows.append(summary)

    run_date = date.today().isoformat()
    batch_dir = out_root / "work/03_processing/normalized/batch_runs"
    csv_path = batch_dir / f"{run_date}_phase1-policy-normalization-batch.csv"
    json_path = batch_dir / f"{run_date}_phase1-policy-normalization-batch.json"
    summary_payload = {
        "run_date": run_date,
        "registry_path": str(registry_path.relative_to(out_root)),
        "completed_count": sum(1 for row in summary_rows if row["run_status"] == "completed"),
        "failed_count": sum(1 for row in summary_rows if row["run_status"] == "failed"),
        "documents": summary_rows,
    }
    write_csv(csv_path, summary_rows, ["document_id", "title", "source_format", "run_status", "paragraph_count", "page_count", "notes"])
    write_json(json_path, summary_payload)


if __name__ == "__main__":
    main()
