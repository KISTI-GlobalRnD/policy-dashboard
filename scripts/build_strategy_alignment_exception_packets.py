#!/usr/bin/env python3
"""Build focused review packets for strategy alignment exceptions."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path

from generated_artifact_utils import cleanup_stale_files


PACKET_FIELDS = [
    "exception_id",
    "strategy_id",
    "strategy_label",
    "reference_document_id",
    "reference_table_id",
    "reference_sequence_no",
    "reference_strategy_label",
    "reference_content_summary",
    "alignment_status",
    "resolution_status",
    "decision_key",
    "active_in_queue",
    "decision_status",
    "policy_item_id",
    "policy_id",
    "policy_name",
    "bucket_label",
    "item_label",
    "primary_evidence_id",
    "evidence_preview",
    "tech_domains",
    "suggested_primary_strategy_id",
    "suggested_primary_strategy_label",
    "suggested_primary_strategy_score",
    "alternate_strategy_ids",
    "alternate_strategy_labels",
    "auto_seed_blocked",
    "reviewed_primary_strategy_id",
    "reviewed_secondary_strategy_ids",
    "reviewed_confidence",
    "reviewer_name",
    "reviewer_notes",
    "alignment_exception_notes",
]


INDEX_FIELDS = [
    "exception_id",
    "strategy_id",
    "strategy_label",
    "output_csv",
    "output_md",
    "item_count",
    "active_item_count",
    "pending_count",
    "reviewed_count",
    "no_strategy_count",
    "deferred_count",
    "policy_count",
    "bucket_technology_count",
    "bucket_infra_system_count",
    "bucket_talent_count",
]


BUCKET_ORDER = {
    "기술": 0,
    "인프라·제도": 1,
    "인재": 2,
}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^0-9a-zA-Z가-힣]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "exception"


def parse_ids(value: str) -> list[str]:
    return [token.strip() for token in (value or "").split("|") if token.strip()]


def extract_exception_ids(decision_row: dict[str, str], known_exception_ids: set[str]) -> list[str]:
    explicit_ids = parse_ids(decision_row.get("alignment_exception_ids", ""))
    if explicit_ids:
        return explicit_ids
    notes = decision_row.get("reviewer_notes", "")
    return [exception_id for exception_id in sorted(known_exception_ids) if exception_id in notes]


def build_fallback_exception(decision_row: dict[str, str], exception_id: str) -> dict[str, str]:
    return {
        "exception_id": exception_id,
        "strategy_id": decision_row.get("reviewed_primary_strategy_id", "") or decision_row.get("suggested_primary_strategy_id", ""),
        "strategy_label": decision_row.get("suggested_primary_strategy_label", ""),
        "reference_document_id": "",
        "reference_table_id": "",
        "reference_sequence_no": "",
        "reference_strategy_label": "",
        "reference_content_summary": decision_row.get("alignment_exception_notes", ""),
        "alignment_status": "manual_preserved",
        "resolution_status": "manual_resolved",
    }


def parse_score(value: str) -> int:
    try:
        return int((value or "").strip())
    except ValueError:
        return 0


def row_sort_key(row: dict[str, str]) -> tuple[int, int, int, str]:
    active_rank = 0 if row.get("active_in_queue") == "yes" else 1
    bucket_rank = BUCKET_ORDER.get(row.get("bucket_label", ""), 9)
    score_rank = -parse_score(row.get("suggested_primary_strategy_score", ""))
    return (active_rank, bucket_rank, score_rank, row.get("decision_key", ""))


def build_brief(index_row: dict[str, object], rows: list[dict[str, str]]) -> str:
    top_policy_counter = Counter(f"{row['policy_id']} {row['policy_name']}" for row in rows)
    top_bucket_counter = Counter(row["bucket_label"] for row in rows)
    sample_rows = rows[:8]
    top_policy_lines = [f"- `{label}`: {count}" for label, count in top_policy_counter.most_common()] or ["- 없음"]
    top_bucket_lines = [f"- `{label}`: {count}" for label, count in top_bucket_counter.most_common()] or ["- 없음"]

    lines = [
        f"# {index_row['exception_id']} Alignment Review Packet",
        "",
        f"- 전략: `{index_row['strategy_id']}` {index_row['strategy_label']}",
        f"- 항목 수: `{index_row['item_count']}`",
        f"- active item: `{index_row['active_item_count']}`",
        f"- 상태: `pending {index_row['pending_count']}` / `reviewed {index_row['reviewed_count']}` / `no_strategy {index_row['no_strategy_count']}` / `deferred {index_row['deferred_count']}`",
        f"- reference row: `{rows[0]['reference_document_id']}` / `{rows[0]['reference_table_id']}` / row `{rows[0]['reference_sequence_no']}`",
        f"- reference label: `{rows[0]['reference_strategy_label']}`",
        f"- resolution status: `{rows[0]['resolution_status']}`",
        "",
        "## 검토 포인트",
        "",
        "- 이 packet은 `DOC-REF-002` row reference와 현재 taxonomy strategy가 어긋나는 항목만 모은다.",
        "- 각 항목은 `STR-010` healthcare cluster를 유지할지, 보조 전략으로만 둘지, 또는 taxonomy 분할 요청 대상으로 올릴지 검토한다.",
        "- reference row 10 `사이버 보안 및 AI 신뢰성 검증 기술 확보`와 직접 연결하려고 하지 않는다.",
        "",
        "## 상위 정책",
        "",
        *top_policy_lines,
        "",
        "## bucket 분포",
        "",
        *top_bucket_lines,
        "",
        "## 샘플 항목",
        "",
    ]

    for row in sample_rows:
        lines.append(
            f"- `{row['decision_key']}` `{row['bucket_label']}` `{row['item_label']}`"
            f" -> suggested `{row['suggested_primary_strategy_id']}` score={row['suggested_primary_strategy_score']}"
        )
    if not sample_rows:
        lines.append("- 없음")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exception-csv", required=True)
    parser.add_argument("--queue-csv", required=True)
    parser.add_argument("--decision-csv", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--out-index-csv", required=True)
    parser.add_argument("--out-summary-json", required=True)
    args = parser.parse_args()

    exception_rows = read_csv(Path(args.exception_csv))
    queue_rows = read_csv(Path(args.queue_csv))
    decision_rows = read_csv(Path(args.decision_csv))

    queue_by_key = {row["decision_key"]: row for row in queue_rows if row.get("decision_key")}
    decision_by_key = {row["decision_key"]: row for row in decision_rows if row.get("decision_key")}

    grouped_rows: dict[str, list[dict[str, str]]] = {}
    exception_lookup = {row["exception_id"]: row for row in exception_rows if row.get("exception_id")}
    known_exception_ids = set(exception_lookup)

    for decision_row in decision_rows:
        queue_row = queue_by_key.get(decision_row.get("decision_key", ""), {})
        for exception_id in extract_exception_ids(decision_row, known_exception_ids):
            exception = exception_lookup.get(exception_id) or build_fallback_exception(decision_row, exception_id)
            merged = {
                "exception_id": exception["exception_id"],
                "strategy_id": exception["strategy_id"],
                "strategy_label": exception["strategy_label"],
                "reference_document_id": exception["reference_document_id"],
                "reference_table_id": exception["reference_table_id"],
                "reference_sequence_no": exception["reference_sequence_no"],
                "reference_strategy_label": exception["reference_strategy_label"],
                "reference_content_summary": exception["reference_content_summary"],
                "alignment_status": exception["alignment_status"],
                "resolution_status": exception["resolution_status"],
                "decision_key": decision_row.get("decision_key", ""),
                "active_in_queue": decision_row.get("active_in_queue", ""),
                "decision_status": decision_row.get("decision_status", ""),
                "policy_item_id": decision_row.get("policy_item_id", ""),
                "policy_id": decision_row.get("policy_id", ""),
                "policy_name": decision_row.get("policy_name", ""),
                "bucket_label": decision_row.get("bucket_label", ""),
                "item_label": decision_row.get("item_label", ""),
                "primary_evidence_id": decision_row.get("primary_evidence_id", ""),
                "evidence_preview": decision_row.get("evidence_preview", ""),
                "tech_domains": decision_row.get("tech_domains", "") or queue_row.get("tech_domains", ""),
                "suggested_primary_strategy_id": decision_row.get("suggested_primary_strategy_id", ""),
                "suggested_primary_strategy_label": decision_row.get("suggested_primary_strategy_label", ""),
                "suggested_primary_strategy_score": decision_row.get("suggested_primary_strategy_score", "") or queue_row.get("suggested_strategy_score", ""),
                "alternate_strategy_ids": decision_row.get("alternate_strategy_ids", ""),
                "alternate_strategy_labels": decision_row.get("alternate_strategy_labels", ""),
                "auto_seed_blocked": decision_row.get("auto_seed_blocked", "") or queue_row.get("auto_seed_blocked", ""),
                "reviewed_primary_strategy_id": decision_row.get("reviewed_primary_strategy_id", ""),
                "reviewed_secondary_strategy_ids": decision_row.get("reviewed_secondary_strategy_ids", ""),
                "reviewed_confidence": decision_row.get("reviewed_confidence", ""),
                "reviewer_name": decision_row.get("reviewer_name", ""),
                "reviewer_notes": decision_row.get("reviewer_notes", ""),
                "alignment_exception_notes": decision_row.get("alignment_exception_notes", "") or queue_row.get("alignment_exception_notes", ""),
            }
            grouped_rows.setdefault(exception_id, []).append(merged)

    out_dir = Path(args.out_dir)
    index_rows: list[dict[str, object]] = []
    keep_names: set[str] = set()

    for exception_id, rows in sorted(grouped_rows.items()):
        exception = exception_lookup.get(exception_id) or build_fallback_exception(rows[0], exception_id)
        sorted_rows = sorted(rows, key=row_sort_key)
        basename = f"{exception_id}__{slugify(exception['strategy_label'])}__alignment-review"
        csv_name = f"{basename}.csv"
        md_name = f"{basename}.md"
        keep_names.update({csv_name, md_name})

        write_csv(out_dir / csv_name, sorted_rows, PACKET_FIELDS)

        status_counter = Counter(row.get("decision_status", "") or "pending" for row in sorted_rows)
        policy_counter = Counter(row["policy_id"] for row in sorted_rows if row.get("policy_id"))
        bucket_counter = Counter(row["bucket_label"] for row in sorted_rows if row.get("bucket_label"))
        active_item_count = sum(1 for row in sorted_rows if row.get("active_in_queue") == "yes")

        index_row = {
            "exception_id": exception_id,
            "strategy_id": exception["strategy_id"],
            "strategy_label": exception["strategy_label"],
            "output_csv": csv_name,
            "output_md": md_name,
            "item_count": len(sorted_rows),
            "active_item_count": active_item_count,
            "pending_count": status_counter.get("pending", 0),
            "reviewed_count": status_counter.get("reviewed", 0),
            "no_strategy_count": status_counter.get("no_strategy", 0),
            "deferred_count": status_counter.get("deferred", 0),
            "policy_count": len(policy_counter),
            "bucket_technology_count": bucket_counter.get("기술", 0),
            "bucket_infra_system_count": bucket_counter.get("인프라·제도", 0),
            "bucket_talent_count": bucket_counter.get("인재", 0),
        }
        index_rows.append(index_row)
        write_text(out_dir / md_name, build_brief(index_row, sorted_rows))

    index_rows.sort(key=lambda row: (-int(row["item_count"]), row["exception_id"]))
    summary = {
        "exception_packet_count": len(index_rows),
        "total_item_count": sum(int(row["item_count"]) for row in index_rows),
        "packets": index_rows,
    }

    removed_files = cleanup_stale_files(
        out_dir,
        keep_names,
        ["*__alignment-review.csv", "*__alignment-review.md"],
    )
    summary["removed_stale_files"] = removed_files

    write_csv(Path(args.out_index_csv), index_rows, INDEX_FIELDS)
    write_json(Path(args.out_summary_json), summary)
    print(f"Strategy alignment exception packets: {len(index_rows)}")


if __name__ == "__main__":
    main()
