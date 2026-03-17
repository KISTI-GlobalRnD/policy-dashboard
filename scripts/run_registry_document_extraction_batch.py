#!/usr/bin/env python3
"""Run extraction for source-backed registry documents across the corpus."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import date
from pathlib import Path

from run_support_document_extraction_batch import (
    build_commands,
    detect_pdf_mode,
    load_manifest,
    manifest_counts,
    read_registry,
    relative_path_text,
    resolve_source_file,
    run_command,
    slugify_label,
    write_csv,
    write_json,
)


SUPPORTED_FORMATS = {"pdf", "hwpx", "docx", "hwp", "xlsx"}


def include_row(
    row: dict,
    selected_ids: set[str],
    include_statuses: set[str],
    scope_tracks: set[str],
    doc_roles: set[str],
) -> bool:
    if row.get("source_format", "").lower() not in SUPPORTED_FORMATS:
        return False
    if selected_ids and row.get("registry_id") not in selected_ids:
        return False
    if include_statuses and row.get("include_status") not in include_statuses:
        return False
    if scope_tracks and row.get("scope_track") not in scope_tracks:
        return False
    if doc_roles and row.get("doc_role") not in doc_roles:
        return False
    return True


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-root", required=True)
    parser.add_argument(
        "--registry-csv",
        default="work/01_scope-and-ia/requirements/04_document-registry.csv",
    )
    parser.add_argument("--documents", nargs="*")
    parser.add_argument("--include-statuses", nargs="*")
    parser.add_argument("--scope-tracks", nargs="*")
    parser.add_argument("--doc-roles", nargs="*")
    parser.add_argument("--rerun-existing", action="store_true")
    parser.add_argument("--batch-label")
    args = parser.parse_args()

    out_root = Path(args.out_root)
    registry_path = out_root / args.registry_csv
    rows = read_registry(registry_path)

    selected_ids = set(args.documents or [])
    include_statuses = set(args.include_statuses or [])
    scope_tracks = set(args.scope_tracks or [])
    doc_roles = set(args.doc_roles or [])

    target_rows = [
        row
        for row in rows
        if include_row(row, selected_ids, include_statuses, scope_tracks, doc_roles)
    ]

    summary_rows = []
    for row in target_rows:
        document_id = row["registry_id"]
        source_format = row.get("source_format", "")
        source_file = resolve_source_file(out_root, row)
        existing_manifest = load_manifest(out_root, document_id)
        summary = {
            "document_id": document_id,
            "title": row.get("normalized_title", ""),
            "doc_role": row.get("doc_role", ""),
            "scope_track": row.get("scope_track", ""),
            "include_status": row.get("include_status", ""),
            "source_format": source_format,
            "source_file": relative_path_text(source_file, out_root),
            "extraction_mode": "",
            "run_status": "",
            "page_count": "",
            "text_layer_pages": "",
            "evidence_units": "",
            "tables": "",
            "figures": "",
            "notes": row.get("notes", ""),
        }

        if source_file is None or not source_file.exists():
            summary["run_status"] = "missing_source"
            summary["notes"] = f"{summary['notes']} | resolved source missing"
            summary_rows.append(summary)
            continue

        if existing_manifest is not None and not args.rerun_existing:
            summary["run_status"] = "skipped_existing"
            summary["extraction_mode"] = "existing"
            page_count, evidence_units, tables, figures = manifest_counts(existing_manifest)
            summary["page_count"] = page_count
            summary["evidence_units"] = evidence_units
            summary["tables"] = tables
            summary["figures"] = figures
            summary_rows.append(summary)
            continue

        pdf_mode = None
        if source_format.lower() == "pdf":
            pdf_mode, page_count, text_layer_pages = detect_pdf_mode(out_root, source_file)
            summary["page_count"] = page_count
            summary["text_layer_pages"] = text_layer_pages

        commands, extraction_mode = build_commands(out_root, row, source_file, pdf_mode)
        summary["extraction_mode"] = extraction_mode

        command_failed = False
        for command in commands:
            return_code, output = run_command(command, out_root)
            if return_code != 0:
                summary["run_status"] = "failed"
                summary["notes"] = f"{summary['notes']} | {output[:500]}"
                command_failed = True
                break

        if command_failed:
            summary_rows.append(summary)
            continue

        manifest = load_manifest(out_root, document_id)
        if manifest is None:
            summary["run_status"] = "manifest_missing"
            summary_rows.append(summary)
            continue

        summary["run_status"] = manifest.get("processing_status", "completed")
        page_count, evidence_units, tables, figures = manifest_counts(manifest)
        if not summary["page_count"]:
            summary["page_count"] = page_count
        summary["evidence_units"] = evidence_units
        summary["tables"] = tables
        summary["figures"] = figures
        summary_rows.append(summary)

    run_date = date.today().isoformat()
    batch_dir = out_root / "work/02_structured-extraction/manifests/batch_runs"
    base_name = f"{run_date}_registry-document-extraction-batch"
    if args.batch_label:
        base_name = f"{base_name}__{slugify_label(args.batch_label)}"
    elif selected_ids:
        base_name = f"{base_name}__selected-{len(selected_ids):02d}"

    csv_path = batch_dir / f"{base_name}.csv"
    json_path = batch_dir / f"{base_name}.json"

    summary_payload = {
        "run_date": run_date,
        "registry_path": str(registry_path.relative_to(out_root)),
        "target_count": len(target_rows),
        "completed_like_count": sum(
            1 for row in summary_rows if row["run_status"] in {"completed", "partial_table_pending"}
        ),
        "skipped_existing_count": sum(1 for row in summary_rows if row["run_status"] == "skipped_existing"),
        "failed_count": sum(1 for row in summary_rows if row["run_status"] == "failed"),
        "missing_source_count": sum(1 for row in summary_rows if row["run_status"] == "missing_source"),
        "documents": summary_rows,
    }

    fieldnames = [
        "document_id",
        "title",
        "doc_role",
        "scope_track",
        "include_status",
        "source_format",
        "source_file",
        "extraction_mode",
        "run_status",
        "page_count",
        "text_layer_pages",
        "evidence_units",
        "tables",
        "figures",
        "notes",
    ]
    write_csv(csv_path, summary_rows, fieldnames)
    write_json(json_path, summary_payload)


if __name__ == "__main__":
    main()
