#!/usr/bin/env python3
"""Run extraction for support documents registered in the document registry.

Current targets are registry rows with include_status=support. PDF sources are
dispatched by text-layer detection:

1. text-layer PDF -> extract_pdf_text_from_zip.py
2. scanned/image PDF -> extract_scanned_pdf_pages.py + ocr_page_images_rapidocr.py

Other supported formats reuse the existing phase1 extractors.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
import urllib.request
import zipfile
from datetime import date
from pathlib import Path


OCR_TABLE_RECONSTRUCTION_DOCS = {
    "DOC-REF-002",
    "DOC-CTX-002",
    "DOC-CTX-003",
    "DOC-CTX-004",
}


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


def ensure_pymupdf(loader_root: Path) -> None:
    lib_dir = loader_root / "lib"
    if (lib_dir / "fitz").exists():
        if str(lib_dir) not in sys.path:
            sys.path.insert(0, str(lib_dir))
        return

    loader_root.mkdir(parents=True, exist_ok=True)
    metadata = json.load(urllib.request.urlopen("https://pypi.org/pypi/PyMuPDF/json"))
    wheel_url = None
    wheel_name = None
    for item in metadata["urls"]:
        filename = item["filename"]
        if "cp310-abi3-manylinux_2_28_x86_64.whl" in filename:
            wheel_url = item["url"]
            wheel_name = filename
            break
    if wheel_url is None or wheel_name is None:
        raise RuntimeError("Unable to resolve a compatible PyMuPDF wheel.")

    wheel_path = loader_root / wheel_name
    if not wheel_path.exists():
        urllib.request.urlretrieve(wheel_url, wheel_path)

    with zipfile.ZipFile(wheel_path) as archive:
        archive.extractall(lib_dir)

    if str(lib_dir) not in sys.path:
        sys.path.insert(0, str(lib_dir))


def detect_pdf_mode(out_root: Path, source_file: Path) -> tuple[str, int, int]:
    loader_root = out_root / "tmp" / "pymupdf_loader"
    ensure_pymupdf(loader_root)

    import fitz  # type: ignore

    doc = fitz.open(source_file)
    try:
        page_count = len(doc)
        text_layer_pages = 0
        for page in doc:
            if page.get_text("words"):
                text_layer_pages += 1
        mode = "text_pdf" if text_layer_pages > 0 else "ocr_pdf"
        return mode, page_count, text_layer_pages
    finally:
        doc.close()


def build_commands(out_root: Path, row: dict, source_file: Path, pdf_mode: str | None) -> tuple[list[list[str]], str]:
    scripts_dir = out_root / "scripts"
    document_id = row["registry_id"]
    source_format = row["source_format"].lower()

    if source_format == "pdf":
        if pdf_mode == "ocr_pdf":
            commands = [
                [
                    sys.executable,
                    str(scripts_dir / "extract_scanned_pdf_pages.py"),
                    "--source",
                    str(source_file),
                    "--document-id",
                    document_id,
                    "--registry-id",
                    document_id,
                    "--out-root",
                    str(out_root),
                ],
                [
                    sys.executable,
                    str(scripts_dir / "ocr_page_images_rapidocr.py"),
                    "--document-id",
                    document_id,
                    "--registry-id",
                    document_id,
                    "--out-root",
                    str(out_root),
                ],
            ]
            if document_id in OCR_TABLE_RECONSTRUCTION_DOCS:
                commands.append(
                    [
                        sys.executable,
                        str(scripts_dir / "reconstruct_support_ocr_tables.py"),
                        "--out-root",
                        str(out_root),
                        "--documents",
                        document_id,
                    ]
                )
            return (commands, "ocr_pdf")
        return (
            [
                [
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
            ],
            "text_pdf",
        )

    if source_format == "hwpx":
        return (
            [
                [
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
            ],
            "hwpx",
        )

    if source_format == "docx":
        return (
            [
                [
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
            ],
            "docx",
        )

    if source_format == "hwp":
        return (
            [
                [
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
            ],
            "hwp",
        )

    if source_format == "xlsx":
        return (
            [
                [
                    sys.executable,
                    str(scripts_dir / "extract_xlsx_taxonomy.py"),
                    "--source",
                    str(source_file),
                    "--document-id",
                    document_id,
                    "--registry-id",
                    document_id,
                    "--out-root",
                    str(out_root),
                ]
            ],
            "xlsx",
        )

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


def relative_path_text(path: Path | None, root: Path) -> str:
    if path is None:
        return ""
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def manifest_counts(manifest: dict) -> tuple[object, object, object, object]:
    counts = manifest.get("counts", {})
    evidence_units = counts.get("evidence_units")
    if evidence_units in (None, ""):
        evidence_units = manifest.get("text_block_count", "")

    tables = counts.get("tables")
    if tables in (None, ""):
        tables = counts.get("pages_with_tables_markdown", "")

    figures = counts.get("figures")
    if figures in (None, ""):
        figure_paths = manifest.get("figure_output_paths")
        if isinstance(figure_paths, list):
            figures = len(figure_paths)
        else:
            figures = len(manifest.get("figures", [])) if isinstance(manifest.get("figures"), list) else ""

    page_count = manifest.get("page_count_or_sheet_count", "")
    return page_count, evidence_units, tables, figures


def slugify_label(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = value.strip("-")
    return value or "batch"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-root", required=True)
    parser.add_argument(
        "--registry-csv",
        default="work/01_scope-and-ia/requirements/04_document-registry.csv",
    )
    parser.add_argument("--rerun-existing", action="store_true")
    parser.add_argument("--documents", nargs="*")
    parser.add_argument("--batch-label")
    args = parser.parse_args()

    out_root = Path(args.out_root)
    registry_path = out_root / args.registry_csv
    rows = read_registry(registry_path)
    selected_ids = set(args.documents or [])

    target_rows = [
        row
        for row in rows
        if row.get("include_status") == "support"
        and row.get("source_format", "").lower() in {"pdf", "hwpx", "docx", "hwp", "xlsx"}
        and (not selected_ids or row.get("registry_id") in selected_ids)
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
    base_name = f"{run_date}_support-document-extraction-batch"
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
        "completed_like_count": sum(1 for row in summary_rows if row["run_status"] in {"completed", "partial_table_pending"}),
        "skipped_existing_count": sum(1 for row in summary_rows if row["run_status"] == "skipped_existing"),
        "failed_count": sum(1 for row in summary_rows if row["run_status"] == "failed"),
        "missing_source_count": sum(1 for row in summary_rows if row["run_status"] == "missing_source"),
        "documents": summary_rows,
    }

    fieldnames = [
        "document_id",
        "title",
        "doc_role",
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
