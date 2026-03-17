#!/usr/bin/env python3
"""Summarize actual table review backlog and optionally build ready queues."""

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
    return isinstance(counts, dict) and counts.get("proxy_note") is True


def is_curated_complete(manifest: dict) -> bool:
    quality_notes = manifest.get("quality_notes", [])
    joined_notes = " ".join(quality_notes) if isinstance(quality_notes, list) else str(quality_notes)
    return "manually normalized" in joined_notes or "page-wise draft tables" in joined_notes


def is_deferred_hold_scope(doc_role: str, include_status: str) -> bool:
    return doc_role == "benchmark_source" and include_status == "hold"


def priority_for(doc_role: str, include_status: str, status: str) -> str:
    if status in {
        "manual_review_complete",
        "curated_complete",
        "proxy_complete",
        "deferred_hold_markdown_candidate",
        "deferred_hold_queue_ready",
        "deferred_hold_queue_built",
    }:
        return "none"
    if doc_role == "policy_source" and include_status == "include":
        return "high"
    if doc_role in {"working_note", "taxonomy_source"} or include_status == "support":
        return "low"
    if doc_role == "benchmark_source":
        return "low"
    return "medium"


def recommended_action(status: str) -> str:
    actions = {
        "manual_review_complete": "none",
        "curated_complete": "none",
        "proxy_complete": "replace_with_raw_source_when_available",
        "manual_review_pending": "finish_table_review_decisions",
        "queue_built": "review_queue_items_and_apply_decisions",
        "queue_ready_not_started": "build_table_review_queue",
        "normalization_missing": "normalize_text_blocks_then_build_queue",
        "markdown_only_candidate": "decide_whether_markdown_tables_need_manual_review",
        "deferred_hold_markdown_candidate": "optional_benchmark_review_only_if_scope_changes",
        "deferred_hold_queue_ready": "optional_benchmark_review_only_if_scope_changes",
        "deferred_hold_queue_built": "optional_benchmark_review_only_if_scope_changes",
    }
    return actions.get(status, "inspect_manually")


def run_build_queue(out_root: Path, document_id: str) -> tuple[str, str]:
    command = [
        sys.executable,
        str(out_root / "scripts/build_table_review_queue.py"),
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-root", required=True)
    parser.add_argument("--run-date", default=date.today().isoformat())
    parser.add_argument("--build-ready-queues", action="store_true")
    args = parser.parse_args()

    out_root = Path(args.out_root)
    run_date = args.run_date

    seed_path = out_root / "work/04_ontology/instances/documents_seed.csv"
    manifest_dir = out_root / "work/02_structured-extraction/manifests"
    normalized_dir = out_root / "work/03_processing/normalized"
    queue_dir = out_root / "qa/extraction/review_queues"
    reviewed_dir = out_root / "qa/extraction/reviewed_queues"
    qa_dir = out_root / "qa/extraction"

    rows = list(csv.DictReader(seed_path.open(encoding="utf-8-sig", newline="")))
    summary_rows = []
    status_counts: dict[str, int] = {}
    priority_counts: dict[str, int] = {}

    for row in rows:
        document_id = row["document_id"]
        manifest_path = manifest_dir / f"{document_id}_manifest.json"
        if not manifest_path.exists():
            continue
        manifest = load_json(manifest_path)
        raw_table_count = count_tables(manifest)
        if raw_table_count <= 0:
            continue

        doc_role = row.get("doc_role", "")
        include_status = row.get("include_status", "")
        source_format = manifest.get("source_format") or row.get("source_format", "")
        queue_summary_path = queue_dir / f"{document_id}__table-review-queue-summary.json"
        reviewed_summary_path = reviewed_dir / f"{document_id}__table-review-reviewed-summary.json"
        paragraphs_path = normalized_dir / f"{document_id}__paragraphs.json"
        deferred_hold_scope = is_deferred_hold_scope(doc_role, include_status)
        markdown_only = 0
        counts = manifest.get("counts", {})
        if isinstance(counts, dict):
            value = counts.get("pages_with_tables_markdown")
            if isinstance(value, int):
                markdown_only = value

        queue_build_status = ""
        queue_build_notes = ""
        if reviewed_summary_path.exists():
            reviewed_summary = load_json(reviewed_summary_path)
            status = "manual_review_complete" if reviewed_summary.get("review_required_count", 0) == 0 else "manual_review_pending"
            queue_summary = load_json(queue_summary_path) if queue_summary_path.exists() else {}
        elif is_proxy_manifest(manifest):
            reviewed_summary = {}
            queue_summary = {}
            status = "proxy_complete"
        elif is_curated_complete(manifest):
            reviewed_summary = {}
            queue_summary = {}
            status = "curated_complete"
        elif paragraphs_path.exists():
            if args.build_ready_queues:
                queue_build_status, queue_build_notes = run_build_queue(out_root, document_id)
            queue_summary = load_json(queue_summary_path) if queue_summary_path.exists() else {}
            reviewed_summary = {}
            if deferred_hold_scope:
                status = "deferred_hold_queue_built" if queue_summary_path.exists() else "deferred_hold_queue_ready"
            else:
                status = "queue_built" if queue_summary_path.exists() else "queue_ready_not_started"
        elif markdown_only:
            reviewed_summary = {}
            queue_summary = {}
            status = "deferred_hold_markdown_candidate" if deferred_hold_scope else "markdown_only_candidate"
        else:
            reviewed_summary = {}
            queue_summary = {}
            status = "normalization_missing"

        priority = priority_for(doc_role, include_status, status)
        status_counts[status] = status_counts.get(status, 0) + 1
        priority_counts[priority] = priority_counts.get(priority, 0) + 1

        suggested_counts = queue_summary.get("suggested_class_counts", {})
        summary_rows.append(
            {
                "document_id": document_id,
                "title": row.get("normalized_title", ""),
                "doc_role": doc_role,
                "include_status": include_status,
                "source_format": source_format,
                "raw_table_count": raw_table_count,
                "status": status,
                "priority": priority,
                "recommended_action": recommended_action(status),
                "queue_build_status": queue_build_status,
                "queue_review_item_count": queue_summary.get("review_item_count", ""),
                "queue_structured_table_count": suggested_counts.get("structured_table", 0),
                "queue_review_required_count": suggested_counts.get("review_required", 0),
                "queue_layout_false_positive_count": suggested_counts.get("layout_false_positive", 0),
                "reviewed_count": reviewed_summary.get("reviewed_count", ""),
                "review_pending_count": reviewed_summary.get("review_required_count", ""),
                "canonical_table_count": reviewed_summary.get("canonical_table_count", ""),
                "notes": queue_build_notes,
            }
        )

    summary_rows.sort(
        key=lambda item: (
            {"high": 0, "medium": 1, "low": 2, "none": 3}.get(item["priority"], 4),
            item["status"],
            -int(item["raw_table_count"]),
            item["document_id"],
        )
    )

    top_backlog = [
        row
        for row in summary_rows
        if row["priority"] in {"high", "medium"} and row["status"] not in {"manual_review_complete", "curated_complete", "proxy_complete"}
    ]

    payload = {
        "run_date": run_date,
        "document_count_with_table_artifacts": len(summary_rows),
        "status_counts": status_counts,
        "priority_counts": priority_counts,
        "top_backlog_count": len(top_backlog),
        "documents": summary_rows,
    }

    json_path = queue_dir / f"{run_date}_table-review-backlog-snapshot.json"
    csv_path = queue_dir / f"{run_date}_table-review-backlog-snapshot.csv"
    md_path = qa_dir / f"{run_date}_table-review-backlog-snapshot.md"

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
            "raw_table_count",
            "status",
            "priority",
            "recommended_action",
            "queue_build_status",
            "queue_review_item_count",
            "queue_structured_table_count",
            "queue_review_required_count",
            "queue_layout_false_positive_count",
            "reviewed_count",
            "review_pending_count",
            "canonical_table_count",
            "notes",
        ],
    )

    lines = [
        f"# {run_date} Table Review Backlog Snapshot",
        "",
        "## Status Counts",
    ]
    for key, value in sorted(status_counts.items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Priority Counts",
        ]
    )
    for key, value in sorted(priority_counts.items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Top Backlog",
        ]
    )
    for row in top_backlog[:10]:
        lines.append(
            f"- `{row['document_id']}` `{row['status']}` priority=`{row['priority']}` raw_tables=`{row['raw_table_count']}` "
            f"structured=`{row['queue_structured_table_count']}` review_required=`{row['queue_review_required_count']}`"
        )
    deferred_rows = [row for row in summary_rows if row["status"].startswith("deferred_hold_")]
    lines.extend(
        [
            "",
            "## Deferred Hold Items",
        ]
    )
    for row in deferred_rows[:10]:
        lines.append(
            f"- `{row['document_id']}` `{row['status']}` raw_tables=`{row['raw_table_count']}` "
            f"review_items=`{row['queue_review_item_count']}` structured=`{row['queue_structured_table_count']}` "
            f"review_required=`{row['queue_review_required_count']}`"
        )
    lines.append("")

    write_text(md_path, "\n".join(lines))
    print(json_path)
    print(csv_path)
    print(md_path)


if __name__ == "__main__":
    main()
