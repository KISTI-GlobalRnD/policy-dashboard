#!/usr/bin/env python3
"""Build a frozen extraction completion snapshot for handoff."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import date
from pathlib import Path

from table_artifact_quality_utils import classify_table_payload


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


def count_figures(manifest: dict) -> int:
    figures = manifest.get("figures")
    if isinstance(figures, list):
        return len(figures)
    figure_paths = manifest.get("figure_output_paths")
    if isinstance(figure_paths, list):
        return len(figure_paths)
    counts = manifest.get("counts", {})
    if isinstance(counts, dict):
        value = counts.get("figures") or counts.get("pages_with_images_markdown")
        if isinstance(value, int):
            return value
    return 0


def count_tables(manifest: dict) -> int:
    tables = manifest.get("tables")
    if isinstance(tables, list):
        return len(tables)
    counts = manifest.get("counts", {})
    if isinstance(counts, dict):
        value = counts.get("tables") or counts.get("pages_with_tables_markdown")
        if isinstance(value, int):
            return value
    return 0


def is_proxy_manifest(manifest: dict) -> bool:
    extraction_run_id = str(manifest.get("extraction_run_id", ""))
    if extraction_run_id.startswith("derived-context-proxy-"):
        return True
    counts = manifest.get("counts", {})
    if isinstance(counts, dict) and counts.get("proxy_note") is True:
        return True
    return False


def summarize_table_artifacts(manifest: dict, out_root: Path, source_format: str) -> dict[str, object]:
    tables = manifest.get("tables")
    class_counts: dict[str, int] = {}
    raw_count = count_tables(manifest)
    counts = manifest.get("counts", {})
    if not isinstance(tables, list):
        markdown_only_count = 0
        if isinstance(counts, dict):
            value = counts.get("pages_with_tables_markdown")
            if isinstance(value, int):
                markdown_only_count = value
        if markdown_only_count:
            class_counts["markdown_only_candidate"] = markdown_only_count
        return {
            "artifact_count": raw_count,
            "substantive_count": 0,
            "class_counts": class_counts,
            "classified_count": markdown_only_count,
            "unclassified_count": max(raw_count - markdown_only_count, 0),
        }

    classified_count = 0
    unclassified_count = 0
    substantive_count = 0
    for entry in tables:
        table_path_value = entry.get("path")
        if not table_path_value:
            unclassified_count += 1
            continue
        table_path = out_root / table_path_value
        if not table_path.exists():
            unclassified_count += 1
            continue
        payload = load_json(table_path)
        suggested_class, _ = classify_table_payload(payload, source_format.lower())
        class_counts[suggested_class] = class_counts.get(suggested_class, 0) + 1
        classified_count += 1
        if suggested_class == "structured_table":
            substantive_count += 1

    return {
        "artifact_count": raw_count,
        "substantive_count": substantive_count,
        "class_counts": class_counts,
        "classified_count": classified_count,
        "unclassified_count": unclassified_count,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-root", required=True)
    parser.add_argument("--run-date", default=date.today().isoformat())
    args = parser.parse_args()

    out_root = Path(args.out_root)
    run_date = args.run_date

    seed_path = out_root / "work/04_ontology/instances/documents_seed.csv"
    manifest_dir = out_root / "work/02_structured-extraction/manifests"
    batch_dir = out_root / "work/02_structured-extraction/manifests/batch_runs"
    qa_dir = out_root / "qa/extraction"

    rows = list(csv.DictReader(seed_path.open(encoding="utf-8-sig", newline="")))

    status_counts: dict[str, int] = {}
    source_format_counts: dict[str, int] = {}
    extraction_run_counts: dict[str, int] = {}
    proxy_docs: list[str] = []
    ocr_curated_docs: list[str] = []
    source_backed_docs = 0
    source_backed_completed_docs = 0
    total_tables = 0
    total_substantive_tables = 0
    total_figures = 0
    total_classified_tables = 0
    total_unclassified_tables = 0
    table_class_counts: dict[str, int] = {}
    docs = []

    for row in rows:
        document_id = row["document_id"]
        manifest = load_json(manifest_dir / f"{document_id}_manifest.json")
        processing_status = manifest.get("processing_status", "unknown")
        extraction_run_id = manifest.get("extraction_run_id", "")
        source_format = manifest.get("source_format") or row.get("source_format", "")

        status_counts[processing_status] = status_counts.get(processing_status, 0) + 1
        source_format_counts[source_format] = source_format_counts.get(source_format, 0) + 1
        extraction_run_counts[extraction_run_id] = extraction_run_counts.get(extraction_run_id, 0) + 1

        table_summary = summarize_table_artifacts(manifest, out_root, source_format)
        table_count = int(table_summary["artifact_count"])
        figure_count = count_figures(manifest)
        total_tables += table_count
        total_substantive_tables += int(table_summary["substantive_count"])
        total_figures += figure_count
        total_classified_tables += int(table_summary["classified_count"])
        total_unclassified_tables += int(table_summary["unclassified_count"])
        for suggested_class, count in dict(table_summary["class_counts"]).items():
            table_class_counts[suggested_class] = table_class_counts.get(suggested_class, 0) + int(count)

        if row.get("source_rel_path"):
            source_backed_docs += 1
            if processing_status == "completed":
                source_backed_completed_docs += 1

        proxy_note = is_proxy_manifest(manifest)
        if proxy_note:
            proxy_docs.append(document_id)

        quality_notes = manifest.get("quality_notes", [])
        joined_notes = " ".join(quality_notes) if isinstance(quality_notes, list) else str(quality_notes)
        if "manually normalized" in joined_notes or "page-wise draft tables" in joined_notes:
            ocr_curated_docs.append(document_id)

        docs.append(
            {
                "document_id": document_id,
                "title": row.get("normalized_title", ""),
                "doc_role": row.get("doc_role", ""),
                "scope_track": row.get("scope_track", ""),
                "include_status": row.get("include_status", ""),
                "source_format": source_format,
                "processing_status": processing_status,
                "extraction_run_id": extraction_run_id,
                "table_count": table_count,
                "substantive_table_count": table_summary["substantive_count"],
                "table_class_counts": table_summary["class_counts"],
                "figure_count": figure_count,
                "proxy_note": proxy_note,
            }
        )

    summary = {
        "run_date": run_date,
        "document_count": len(rows),
        "completed_count": status_counts.get("completed", 0),
        "status_counts": status_counts,
        "source_backed_document_count": source_backed_docs,
        "source_backed_completed_count": source_backed_completed_docs,
        "proxy_document_count": len(proxy_docs),
        "proxy_documents": proxy_docs,
        "ocr_curated_document_count": len(ocr_curated_docs),
        "ocr_curated_documents": sorted(ocr_curated_docs),
        "source_format_counts": source_format_counts,
        "extraction_run_counts": extraction_run_counts,
        "total_table_artifact_count": total_tables,
        "total_substantive_table_artifact_count": total_substantive_tables,
        "table_artifact_class_counts": table_class_counts,
        "table_artifact_classified_count": total_classified_tables,
        "table_artifact_unclassified_count": total_unclassified_tables,
        "total_figure_artifact_count": total_figures,
        "documents": docs,
    }

    summary_json_path = batch_dir / f"{run_date}_extraction-completion-snapshot.json"
    qa_md_path = qa_dir / f"{run_date}_extraction-completion-snapshot.md"
    write_json(summary_json_path, summary)

    lines = [
        f"# {run_date} Extraction Completion Snapshot",
        "",
        "## Status",
        f"- document_count: `{len(rows)}`",
        f"- completed_count: `{status_counts.get('completed', 0)}`",
        f"- source_backed_completed_count: `{source_backed_completed_docs}` / `{source_backed_docs}`",
        f"- proxy_document_count: `{len(proxy_docs)}`",
        f"- ocr_curated_document_count: `{len(ocr_curated_docs)}`",
        f"- total_table_artifact_count: `{total_tables}`",
        f"- total_substantive_table_artifact_count: `{total_substantive_tables}`",
        f"- total_figure_artifact_count: `{total_figures}`",
        "",
        "## Notes",
        "- Extraction layer is frozen at this snapshot for downstream ontology/dashboard work.",
        "- Table artifact counts now distinguish raw extracted boxes from heuristic substantive tables.",
        "- `DOC-POL-013` uses the companion HWPX source to recover structured tables and figures.",
        "- `DOC-REF-001`, `DOC-REF-002`, `DOC-CTX-002`, `DOC-CTX-003`, `DOC-CTX-004` are OCR-derived and were finalized into curated tables.",
        "- `DOC-CTX-012`, `DOC-CTX-013`, `DOC-CTX-014` remain proxy context notes until raw PDFs are obtained.",
        "",
        "## Table Artifact Classes",
    ]
    for suggested_class, count in sorted(table_class_counts.items()):
        lines.append(f"- `{suggested_class}`: `{count}`")
    lines.extend(
        [
            f"- `unclassified`: `{total_unclassified_tables}`",
            "",
        "## Proxy Documents",
        ]
    )
    for document_id in proxy_docs:
        lines.append(f"- `{document_id}`")
    lines.extend(["", "## OCR-Curated Documents"])
    for document_id in sorted(ocr_curated_docs):
        lines.append(f"- `{document_id}`")
    lines.append("")

    write_text(qa_md_path, "\n".join(lines))
    print(summary_json_path)
    print(qa_md_path)


if __name__ == "__main__":
    main()
