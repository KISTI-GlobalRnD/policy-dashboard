#!/usr/bin/env python3
"""Run text-first extraction for phase1 policy documents.

Priority order:
1. Pure text extraction for the policy corpus
2. Keep tables / figures only when the format extractor already exposes them
3. Defer table / figure QA to a later pass
"""

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


def resolve_source_file(out_root: Path, row: dict) -> Path | None:
    source_rel_path = row.get("source_rel_path", "")
    internal_path = row.get("internal_path", "")
    if not source_rel_path:
        return None

    source_path = out_root / source_rel_path
    if internal_path:
        if source_path.suffix.lower() == ".zip":
            extracted_dir = source_path.with_suffix("")
            candidate = extracted_dir / internal_path
            if candidate.exists():
                return candidate
        candidate = source_path.parent / internal_path
        if candidate.exists():
            return candidate

    return source_path if source_path.exists() else None


def build_command(out_root: Path, row: dict, source_file: Path) -> list[str]:
    scripts_dir = out_root / "scripts"
    document_id = row["registry_id"]
    source_format = row["source_format"].lower()

    if source_format == "pdf":
        return [
            sys.executable,
            str(scripts_dir / "extract_pdf_text_from_zip.py"),
            "--source-pdf",
            str(source_file),
            "--document-id",
            document_id,
            "--registry-id",
            document_id,
            "--out-root",
            str(out_root),
        ]
    if source_format == "hwpx":
        return [
            sys.executable,
            str(scripts_dir / "extract_hwpx_from_zip.py"),
            "--source-hwpx",
            str(source_file),
            "--document-id",
            document_id,
            "--registry-id",
            document_id,
            "--out-root",
            str(out_root),
        ]
    if source_format == "docx":
        return [
            sys.executable,
            str(scripts_dir / "extract_docx_text.py"),
            "--source-docx",
            str(source_file),
            "--document-id",
            document_id,
            "--registry-id",
            document_id,
            "--out-root",
            str(out_root),
        ]
    if source_format == "hwp":
        return [
            sys.executable,
            str(scripts_dir / "extract_hwp_text.py"),
            "--source-hwp",
            str(source_file),
            "--document-id",
            document_id,
            "--registry-id",
            document_id,
            "--out-root",
            str(out_root),
        ]
    raise ValueError(f"Unsupported source format: {source_format}")


def load_manifest(out_root: Path, document_id: str) -> dict | None:
    manifest_path = out_root / "work/02_structured-extraction/manifests" / f"{document_id}_manifest.json"
    if not manifest_path.exists():
        return None
    return json.loads(manifest_path.read_text(encoding="utf-8"))


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
        if row.get("doc_role") == "policy_source" and row.get("scope_track") == "phase1"
    ]

    summary_rows = []
    for row in target_rows:
        document_id = row["registry_id"]
        include_status = row.get("include_status", "")
        source_format = row.get("source_format", "")
        source_file = resolve_source_file(out_root, row)

        summary = {
            "document_id": document_id,
            "title": row.get("normalized_title", ""),
            "include_status": include_status,
            "source_format": source_format,
            "source_file": str(source_file.relative_to(out_root)) if source_file and source_file.is_relative_to(out_root) else str(source_file or ""),
            "run_status": "",
            "evidence_units": "",
            "tables": "",
            "figures": "",
            "notes": row.get("notes", ""),
        }

        if include_status != "include":
            summary["run_status"] = "not_runnable"
            if include_status == "missing":
                summary["notes"] = f"{summary['notes']} | 원문 미확보"
            summary_rows.append(summary)
            continue

        if source_file is None or not source_file.exists():
            summary["run_status"] = "missing_source"
            summary["notes"] = f"{summary['notes']} | 풀린 원문 파일 없음"
            summary_rows.append(summary)
            continue

        command = build_command(out_root, row, source_file)
        return_code, output = run_command(command, out_root)
        if return_code != 0:
            summary["run_status"] = "failed"
            summary["notes"] = f"{summary['notes']} | {output[:500]}"
            summary_rows.append(summary)
            continue

        manifest = load_manifest(out_root, document_id)
        if manifest is None:
            summary["run_status"] = "manifest_missing"
            summary_rows.append(summary)
            continue

        summary["run_status"] = manifest.get("processing_status", "completed")
        counts = manifest.get("counts", {})
        summary["evidence_units"] = counts.get("evidence_units", "")
        summary["tables"] = counts.get("tables", counts.get("pages_with_tables_markdown", ""))
        summary["figures"] = counts.get("figures", counts.get("pages_with_images_markdown", ""))
        summary_rows.append(summary)

    run_date = date.today().isoformat()
    batch_dir = out_root / "work/02_structured-extraction/manifests/batch_runs"
    csv_path = batch_dir / f"{run_date}_phase1-policy-text-first-batch.csv"
    json_path = batch_dir / f"{run_date}_phase1-policy-text-first-batch.json"

    summary_payload = {
        "run_date": run_date,
        "registry_path": str(registry_path.relative_to(out_root)),
        "total_phase1_policy_rows": len(target_rows),
        "completed_count": sum(1 for row in summary_rows if row["run_status"] == "completed"),
        "failed_count": sum(1 for row in summary_rows if row["run_status"] == "failed"),
        "missing_source_count": sum(1 for row in summary_rows if row["run_status"] == "missing_source"),
        "not_runnable_count": sum(1 for row in summary_rows if row["run_status"] == "not_runnable"),
        "documents": summary_rows,
    }

    fieldnames = [
        "document_id",
        "title",
        "include_status",
        "source_format",
        "source_file",
        "run_status",
        "evidence_units",
        "tables",
        "figures",
        "notes",
    ]
    write_csv(csv_path, summary_rows, fieldnames)
    write_json(json_path, summary_payload)


if __name__ == "__main__":
    main()
