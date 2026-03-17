#!/usr/bin/env python3
"""Build a per-document review queue for extracted figure artifacts."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def read_seed_row(seed_csv: Path, document_id: str) -> dict:
    with seed_csv.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("document_id") == document_id:
                return row
    return {}


def read_figure_payloads(figure_dir: Path, document_id: str) -> list[dict]:
    payloads = []
    for path in sorted(figure_dir.glob(f"FIG-{document_id}-*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["_path"] = str(path)
        payloads.append(payload)
    return payloads


def stringify_location(payload: dict) -> str:
    page_no = payload.get("page_no")
    if page_no not in (None, ""):
        return str(page_no)
    page_or_section = payload.get("page_no_or_sheet_name")
    return str(page_or_section or "")


def is_generic_caption(caption: str) -> bool:
    value = (caption or "").strip()
    return value.startswith("그림입니다.") or value.startswith("Rendered page")


def keep_decision_for_class(class_name: str) -> str:
    if class_name in {"support_render", "deferred_hold_render", "deferred_hold_image"}:
        return "no"
    return "review"


def default_quality_status(class_name: str) -> str:
    if class_name == "support_render":
        return "support_render"
    if class_name in {"deferred_hold_render", "deferred_hold_image"}:
        return "deferred_hold"
    return "review_required"


def suggested_class(payload: dict, seed_row: dict) -> tuple[str, str]:
    figure_type = payload.get("figure_type", "")
    include_status = seed_row.get("include_status", "")
    doc_role = seed_row.get("doc_role", "")

    if figure_type == "pdf_page_image":
        if include_status == "support" or doc_role in {"working_note", "context_note"}:
            return ("support_render", "ocr/manual review support page render")
        if include_status == "hold":
            return ("deferred_hold_render", "hold-scope page render")
        return ("review_required", "page render in in-scope document")

    if include_status == "hold":
        return ("deferred_hold_image", "embedded image in hold-scope document")

    return ("review_required", "embedded image requires semantic figure review")


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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--document-id", required=True)
    parser.add_argument("--out-root", required=True)
    args = parser.parse_args()

    out_root = Path(args.out_root)
    document_id = args.document_id
    seed_row = read_seed_row(out_root / "work/04_ontology/instances/documents_seed.csv", document_id)
    payloads = read_figure_payloads(out_root / "work/02_structured-extraction/figures", document_id)

    queue_rows = []
    class_counts: dict[str, int] = {}
    figure_type_counts: dict[str, int] = {}
    generic_caption_count = 0
    missing_bbox_count = 0

    for index, payload in enumerate(payloads, start=1):
        caption = payload.get("caption", "") or ""
        if is_generic_caption(caption):
            generic_caption_count += 1
        if payload.get("source_bbox") in (None, "", []):
            missing_bbox_count += 1
        figure_type = payload.get("figure_type", "") or ""
        figure_type_counts[figure_type] = figure_type_counts.get(figure_type, 0) + 1

        suggested, rationale = suggested_class(payload, seed_row)
        class_counts[suggested] = class_counts.get(suggested, 0) + 1
        queue_rows.append(
            {
                "review_item_id": f"FRV-{document_id}-{index:03d}",
                "figure_id": payload.get("figure_id", ""),
                "document_id": document_id,
                "title": seed_row.get("normalized_title", ""),
                "doc_role": seed_row.get("doc_role", ""),
                "include_status": seed_row.get("include_status", ""),
                "location": stringify_location(payload),
                "figure_type": figure_type,
                "extraction_method": payload.get("extraction_method", ""),
                "extraction_confidence": payload.get("extraction_confidence", ""),
                "has_source_bbox": 0 if payload.get("source_bbox") in (None, "", []) else 1,
                "generic_caption": 1 if is_generic_caption(caption) else 0,
                "caption": caption,
                "summary": payload.get("summary", "") or "",
                "asset_path": payload.get("asset_path", "") or "",
                "suggested_class": suggested,
                "rationale": rationale,
                "keep_for_dashboard": keep_decision_for_class(suggested),
                "review_status": "review_required",
                "quality_status": default_quality_status(suggested),
                "reviewer_notes": "",
            }
        )

    summary = {
        "document_id": document_id,
        "review_item_count": len(queue_rows),
        "figure_type_counts": figure_type_counts,
        "suggested_class_counts": class_counts,
        "generic_caption_count": generic_caption_count,
        "missing_bbox_count": missing_bbox_count,
    }

    queue_dir = out_root / "qa/extraction/review_queues"
    write_csv(
        queue_dir / f"{document_id}__figure-review-queue.csv",
        queue_rows,
        [
            "review_item_id",
            "figure_id",
            "document_id",
            "title",
            "doc_role",
            "include_status",
            "location",
            "figure_type",
            "extraction_method",
            "extraction_confidence",
            "has_source_bbox",
            "generic_caption",
            "caption",
            "summary",
            "asset_path",
            "suggested_class",
            "rationale",
            "keep_for_dashboard",
            "review_status",
            "quality_status",
            "reviewer_notes",
        ],
    )
    write_json(queue_dir / f"{document_id}__figure-review-queue-summary.json", summary)


if __name__ == "__main__":
    main()
