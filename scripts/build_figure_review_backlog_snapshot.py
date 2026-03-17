#!/usr/bin/env python3
"""Summarize actual figure review backlog and optionally build ready queues."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from datetime import date
from pathlib import Path


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


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


def write_text(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


def run_build_queue(out_root: Path, document_id: str) -> tuple[str, str]:
    command = [
        sys.executable,
        str(out_root / "scripts/build_figure_review_queue.py"),
        "--document-id",
        document_id,
        "--out-root",
        str(out_root),
    ]
    completed = subprocess.run(
        command,
        cwd=out_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return ("completed" if completed.returncode == 0 else "failed"), completed.stdout.strip()[:500]


def classify_status(doc_role: str, include_status: str, figure_type_counts: dict[str, int], queue_summary_path: Path) -> str:
    page_render_count = int(figure_type_counts.get("pdf_page_image", 0))
    total_count = sum(int(value) for value in figure_type_counts.values())
    all_page_renders = total_count > 0 and page_render_count == total_count
    queue_exists = queue_summary_path.exists()

    if all_page_renders and (include_status == "support" or doc_role in {"working_note", "context_note"}):
        return "support_render_only"
    if include_status == "hold":
        return "deferred_hold_queue_built" if queue_exists else "deferred_hold_pending"
    if doc_role == "policy_source" and include_status == "include":
        return "queue_built" if queue_exists else "review_pending"
    if include_status == "support":
        return "support_embedded_images"
    return "review_pending"


def priority_for(doc_role: str, include_status: str, status: str) -> str:
    if status in {
        "manual_review_complete",
        "support_render_only",
        "deferred_hold_queue_built",
        "deferred_hold_pending",
    }:
        return "none"
    if doc_role == "policy_source" and include_status == "include":
        return "high"
    return "medium"


def recommended_action(status: str) -> str:
    actions = {
        "support_render_only": "none",
        "manual_review_complete": "none",
        "manual_review_pending": "finish_figure_review_decisions",
        "deferred_hold_queue_built": "optional_benchmark_or_hold_review_only_if_scope_changes",
        "deferred_hold_pending": "optional_benchmark_or_hold_review_only_if_scope_changes",
        "queue_built": "review_figure_assets_and_set_quality_status",
        "review_pending": "build_figure_review_queue",
        "support_embedded_images": "review_support_figures_if_needed_for_dashboard",
    }
    return actions.get(status, "inspect_manually")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-root", required=True)
    parser.add_argument("--run-date", default=date.today().isoformat())
    parser.add_argument("--build-ready-queues", action="store_true")
    args = parser.parse_args()

    out_root = Path(args.out_root)
    run_date = args.run_date
    seed_rows = list(csv.DictReader((out_root / "work/04_ontology/instances/documents_seed.csv").open(encoding="utf-8-sig", newline="")))
    seed_by_id = {row["document_id"]: row for row in seed_rows}

    figure_dir = out_root / "work/02_structured-extraction/figures"
    queue_dir = out_root / "qa/extraction/review_queues"
    reviewed_dir = out_root / "qa/extraction/reviewed_queues"
    qa_dir = out_root / "qa/extraction"

    figure_paths = sorted(figure_dir.glob("FIG-*.json"))
    figure_docs: dict[str, list[Path]] = {}
    for path in figure_paths:
        document_id = path.stem.split("-")[1:4]
        if len(document_id) < 3:
            continue
        doc_id = "-".join(document_id)
        figure_docs.setdefault(doc_id, []).append(path)

    summary_rows = []
    status_counts: dict[str, int] = {}
    priority_counts: dict[str, int] = {}

    for document_id, paths in sorted(figure_docs.items()):
        seed_row = seed_by_id.get(document_id, {})
        figure_type_counts: dict[str, int] = {}
        extraction_method_counts: dict[str, int] = {}
        generic_caption_count = 0
        missing_bbox_count = 0

        for path in paths:
            payload = load_json(path)
            figure_type = str(payload.get("figure_type", ""))
            extraction_method = str(payload.get("extraction_method", ""))
            figure_type_counts[figure_type] = figure_type_counts.get(figure_type, 0) + 1
            extraction_method_counts[extraction_method] = extraction_method_counts.get(extraction_method, 0) + 1
            caption = str(payload.get("caption", ""))
            if caption.startswith("그림입니다.") or caption.startswith("Rendered page"):
                generic_caption_count += 1
            if payload.get("source_bbox") in (None, "", []):
                missing_bbox_count += 1

        queue_summary_path = queue_dir / f"{document_id}__figure-review-queue-summary.json"
        reviewed_summary_path = reviewed_dir / f"{document_id}__figure-review-reviewed-summary.json"
        queue_build_status = ""
        queue_build_notes = ""
        if args.build_ready_queues and not reviewed_summary_path.exists():
            queue_build_status, queue_build_notes = run_build_queue(out_root, document_id)

        queue_summary = load_json(queue_summary_path) if queue_summary_path.exists() else {}
        reviewed_summary = load_json(reviewed_summary_path) if reviewed_summary_path.exists() else {}
        if reviewed_summary_path.exists():
            status = "manual_review_complete" if reviewed_summary.get("review_required_count", 0) == 0 else "manual_review_pending"
        else:
            status = classify_status(
                seed_row.get("doc_role", ""),
                seed_row.get("include_status", ""),
                figure_type_counts,
                queue_summary_path,
            )
        priority = priority_for(seed_row.get("doc_role", ""), seed_row.get("include_status", ""), status)
        status_counts[status] = status_counts.get(status, 0) + 1
        priority_counts[priority] = priority_counts.get(priority, 0) + 1

        suggested_counts = queue_summary.get("suggested_class_counts", {})
        summary_rows.append(
            {
                "document_id": document_id,
                "title": seed_row.get("normalized_title", ""),
                "doc_role": seed_row.get("doc_role", ""),
                "include_status": seed_row.get("include_status", ""),
                "source_format": seed_row.get("source_format", ""),
                "raw_figure_count": len(paths),
                "page_render_count": figure_type_counts.get("pdf_page_image", 0),
                "embedded_image_count": figure_type_counts.get("image", 0),
                "missing_bbox_count": missing_bbox_count,
                "generic_caption_count": generic_caption_count,
                "status": status,
                "priority": priority,
                "recommended_action": recommended_action(status),
                "queue_build_status": queue_build_status,
                "queue_review_item_count": queue_summary.get("review_item_count", ""),
                "queue_review_required_count": suggested_counts.get("review_required", 0),
                "queue_support_render_count": suggested_counts.get("support_render", 0),
                "queue_deferred_hold_count": suggested_counts.get("deferred_hold_image", 0)
                + suggested_counts.get("deferred_hold_render", 0),
                "reviewed_count": reviewed_summary.get("reviewed_count", ""),
                "review_pending_count": reviewed_summary.get("review_required_count", ""),
                "dashboard_keep_count": reviewed_summary.get("keep_yes_count", ""),
                "notes": queue_build_notes,
            }
        )

    summary_rows.sort(
        key=lambda item: (
            {"high": 0, "medium": 1, "none": 2}.get(item["priority"], 3),
            item["status"],
            -int(item["raw_figure_count"]),
            item["document_id"],
        )
    )

    top_backlog = [
        row
        for row in summary_rows
        if row["priority"] in {"high", "medium"}
        and row["status"] not in {"manual_review_complete", "support_render_only", "deferred_hold_queue_built", "deferred_hold_pending"}
    ]

    payload = {
        "run_date": run_date,
        "document_count_with_figure_artifacts": len(summary_rows),
        "status_counts": status_counts,
        "priority_counts": priority_counts,
        "top_backlog_count": len(top_backlog),
        "documents": summary_rows,
    }

    json_path = queue_dir / f"{run_date}_figure-review-backlog-snapshot.json"
    csv_path = queue_dir / f"{run_date}_figure-review-backlog-snapshot.csv"
    md_path = qa_dir / f"{run_date}_figure-review-backlog-snapshot.md"

    write_json(json_path, payload)
    write_csv(
        csv_path,
        summary_rows,
        [
            "document_id",
            "title",
            "doc_role",
            "include_status",
            "source_format",
            "raw_figure_count",
            "page_render_count",
            "embedded_image_count",
            "missing_bbox_count",
            "generic_caption_count",
            "status",
            "priority",
            "recommended_action",
            "queue_build_status",
            "queue_review_item_count",
            "queue_review_required_count",
            "queue_support_render_count",
            "queue_deferred_hold_count",
            "reviewed_count",
            "review_pending_count",
            "dashboard_keep_count",
            "notes",
        ],
    )

    lines = [
        f"# {run_date} Figure Review Backlog Snapshot",
        "",
        "## Status Counts",
    ]
    for key, value in sorted(status_counts.items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Priority Counts"])
    for key, value in sorted(priority_counts.items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Top Backlog"])
    for row in top_backlog[:10]:
        lines.append(
            f"- `{row['document_id']}` `{row['status']}` priority=`{row['priority']}` raw_figures=`{row['raw_figure_count']}` "
            f"embedded=`{row['embedded_image_count']}` missing_bbox=`{row['missing_bbox_count']}`"
        )
    lines.extend(["", "## Deferred Hold Items"])
    for row in summary_rows:
        if row["status"] == "deferred_hold_queue_built":
            lines.append(
                f"- `{row['document_id']}` raw_figures=`{row['raw_figure_count']}` "
                f"review_items=`{row['queue_review_item_count']}`"
            )
    lines.append("")
    write_text(md_path, "\n".join(lines))

    print(json_path)
    print(csv_path)
    print(md_path)


if __name__ == "__main__":
    main()
