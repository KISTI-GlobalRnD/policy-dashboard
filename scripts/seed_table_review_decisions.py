#!/usr/bin/env python3
"""Seed obvious table review decisions from heuristic queue output."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def summarize_title_hint(preview_text: str) -> str:
    text = " ".join(preview_text.replace("\n", " ").split()).strip()
    if not text:
        return "표 후보"
    if "|" in text:
        parts = [part.strip() for part in text.split("|") if part.strip()]
        if parts:
            text = " / ".join(parts[:3])
    return text[:80]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--document-id", required=True)
    parser.add_argument("--out-root", required=True)
    parser.add_argument("--queue-csv")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    out_root = Path(args.out_root)
    queue_path = Path(args.queue_csv) if args.queue_csv else out_root / "qa/extraction/review_queues" / f"{args.document_id}__table-review-queue.csv"
    decision_path = out_root / "qa/extraction/review_decisions" / f"{args.document_id}__table-review-decisions.json"

    if decision_path.exists() and not args.overwrite:
        raise FileExistsError(f"Decision file already exists: {decision_path}")

    rows = read_csv(queue_path)
    review_item_updates: dict[str, dict] = {}
    canonical_tables: list[dict] = []
    canonical_index = 0

    for row in rows:
        suggested_class = row["suggested_class"]
        review_item_id = row["review_item_id"]

        if suggested_class == "layout_false_positive":
            review_item_updates[review_item_id] = {
                "keep_for_dashboard": "no",
                "review_status": "reviewed",
                "reviewer_notes": "1차 heuristic seed. 레이아웃 박스/표 도구 기반 제목 요소로 판단해 제외.",
            }
            continue

        if suggested_class != "structured_table":
            continue

        canonical_index += 1
        canonical_table_id = f"CTBL-{args.document_id}-{canonical_index:03d}"
        review_item_updates[review_item_id] = {
            "keep_for_dashboard": "yes",
            "review_status": "reviewed",
            "canonical_table_id": canonical_table_id,
            "reviewer_notes": "1차 heuristic seed. 구조표 후보로 유지.",
        }
        canonical_tables.append(
            {
                "canonical_table_id": canonical_table_id,
                "document_id": args.document_id,
                "title_hint": summarize_title_hint(row.get("preview_text", "")),
                "page_start": row.get("page_no", ""),
                "page_end": row.get("page_no", ""),
                "preferred_candidate_source": row.get("candidate_source", ""),
                "preferred_candidate_id": row.get("candidate_id", ""),
                "canonical_status": "ready",
                "dashboard_ready": "yes",
                "source_review_item_ids": review_item_id,
                "notes": "1차 heuristic seed로 생성된 canonical table.",
            }
        )

    payload = {
        "review_item_updates": review_item_updates,
        "canonical_tables": canonical_tables,
    }
    write_json(decision_path, payload)


if __name__ == "__main__":
    main()
