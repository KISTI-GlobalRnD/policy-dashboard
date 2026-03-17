#!/usr/bin/env python3
"""Build a hybrid table review queue for a document."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from table_artifact_quality_utils import classify_json_table, extract_preview_from_cell_matrix


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


def parse_markdown_table(markdown: str) -> tuple[int, int, str]:
    lines = [line.strip() for line in markdown.splitlines() if line.strip()]
    header = lines[0] if lines else ""
    rows = 0
    cols = 0
    if len(lines) >= 2 and lines[0].startswith("|") and lines[1].startswith("|"):
        rows = max(len(lines) - 1, 0)
        cols = max(lines[0].count("|") - 1, 0)
    return rows, cols, header


def keep_decision_for_class(suggested_class: str) -> str:
    if suggested_class == "structured_table":
        return "yes"
    if suggested_class == "layout_false_positive":
        return "no"
    return "review"


def classify_markdown_table(rows: int, cols: int, header: str) -> tuple[str, str]:
    compact_header = header.replace(" ", "")
    if any(token in compact_header for token in ["시기", "상반기", "하반기"]) and rows <= 5:
        return "multi_page_fragment", "timeline_fragment"
    if rows >= 3 and cols >= 2:
        return "structured_table", "markdown_table_detected"
    return "review_required", "needs_manual_review"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--document-id", required=True)
    parser.add_argument("--out-root", required=True)
    args = parser.parse_args()

    out_root = Path(args.out_root)
    paragraphs_path = out_root / "work/03_processing/normalized" / f"{args.document_id}__paragraphs.json"
    tables_dir = out_root / "work/02_structured-extraction/tables"
    manifest_path = out_root / "work/02_structured-extraction/manifests" / f"{args.document_id}_manifest.json"
    if not paragraphs_path.exists():
        raise FileNotFoundError(f"Missing paragraph file: {paragraphs_path}")
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing manifest file: {manifest_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    source_format = manifest.get("source_format", "").lower()

    rows = []

    paragraphs = json.loads(paragraphs_path.read_text(encoding="utf-8"))
    markdown_index = 0
    for paragraph in paragraphs:
        if paragraph["block_type"] != "table_markdown":
            continue
        markdown_index += 1
        parsed_rows, parsed_cols, header = parse_markdown_table(paragraph["text"])
        suggested_class, heuristic_reason = classify_markdown_table(parsed_rows, parsed_cols, header)
        rows.append(
            {
                "review_item_id": f"TRV-{args.document_id}-MD-{markdown_index:03d}",
                "document_id": args.document_id,
                "source_format": source_format,
                "page_no": paragraph["page_no"],
                "candidate_source": "pymupdf4llm_markdown",
                "candidate_id": paragraph["paragraph_id"],
                "rows": parsed_rows,
                "cols": parsed_cols,
                "preview_text": header,
                "suggested_class": suggested_class,
                "heuristic_reason": heuristic_reason,
                "keep_for_dashboard": keep_decision_for_class(suggested_class),
                "merge_group_hint": f"PAGE-{paragraph['page_no']:02d}",
                "canonical_table_id": "",
                "review_status": "review_required",
                "reviewer_notes": "",
                "treat_as_char": "",
                "text_wrap": "",
            }
        )

    json_index = 0
    for table_path in sorted(tables_dir.glob(f"TBL-{args.document_id}-*.json")):
        json_index += 1
        table = json.loads(table_path.read_text(encoding="utf-8"))
        shape = table.get("table_shape", {})
        cell_matrix = table.get("cell_matrix") or []
        preview = extract_preview_from_cell_matrix(cell_matrix)
        treat_as_char = table.get("treat_as_char", "")
        text_wrap = table.get("text_wrap", "")
        suggested_class, heuristic_reason = classify_json_table(
            shape.get("rows", 0),
            shape.get("cols", 0),
            preview,
            source_format,
            treat_as_char,
            text_wrap,
        )
        page_no = table.get("page_no_or_sheet_name", "")
        merge_group_hint = f"PAGE-{int(page_no):02d}" if str(page_no).isdigit() else ""
        candidate_source = table.get("candidate_source", "pymupdf_find_tables")
        rows.append(
            {
                "review_item_id": f"TRV-{args.document_id}-JS-{json_index:03d}",
                "document_id": args.document_id,
                "source_format": source_format,
                "page_no": page_no,
                "candidate_source": candidate_source,
                "candidate_id": table.get("table_id", table_path.stem),
                "rows": shape.get("rows", 0),
                "cols": shape.get("cols", 0),
                "preview_text": preview,
                "suggested_class": suggested_class,
                "heuristic_reason": heuristic_reason,
                "keep_for_dashboard": keep_decision_for_class(suggested_class),
                "merge_group_hint": merge_group_hint,
                "canonical_table_id": "",
                "review_status": "review_required",
                "reviewer_notes": "",
                "treat_as_char": treat_as_char,
                "text_wrap": text_wrap,
            }
        )

    rows.sort(key=lambda row: (int(row["page_no"]) if str(row["page_no"]).isdigit() else 10**9, row["candidate_source"], row["candidate_id"]))

    summary = {
        "document_id": args.document_id,
        "review_item_count": len(rows),
        "markdown_candidate_count": sum(1 for row in rows if row["candidate_source"] == "pymupdf4llm_markdown"),
        "json_candidate_count": sum(1 for row in rows if row["candidate_source"] == "pymupdf_find_tables"),
        "suggested_class_counts": {
            label: sum(1 for row in rows if row["suggested_class"] == label)
            for label in sorted({row["suggested_class"] for row in rows})
        },
    }

    queue_dir = out_root / "qa/extraction/review_queues"
    csv_path = queue_dir / f"{args.document_id}__table-review-queue.csv"
    summary_path = queue_dir / f"{args.document_id}__table-review-queue-summary.json"

    write_csv(
        csv_path,
        rows,
        [
            "review_item_id",
            "document_id",
            "source_format",
            "page_no",
            "candidate_source",
            "candidate_id",
            "rows",
            "cols",
            "preview_text",
            "suggested_class",
            "heuristic_reason",
            "keep_for_dashboard",
            "merge_group_hint",
            "canonical_table_id",
            "review_status",
            "reviewer_notes",
            "treat_as_char",
            "text_wrap",
        ],
    )
    write_json(summary_path, summary)


if __name__ == "__main__":
    main()
