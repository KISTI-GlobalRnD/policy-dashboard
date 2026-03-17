#!/usr/bin/env python3
"""Build manual review drafts for strategy alignment exception packets."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path

from generated_artifact_utils import cleanup_stale_files


OUTPUT_FIELDS = [
    "exception_id",
    "decision_key",
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
    "alignment_exception_notes",
    "draft_resolution_category",
    "proposed_primary_strategy_id",
    "proposed_secondary_strategy_ids",
    "proposed_taxonomy_request",
    "manual_attention",
    "draft_reason",
]


INDEX_FIELDS = [
    "exception_id",
    "output_csv",
    "output_summary_json",
    "output_brief_md",
    "item_count",
    "keep_primary_count",
    "demote_from_primary_count",
    "taxonomy_split_review_count",
    "high_attention_count",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
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


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())


def contains_any(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def dedupe_ids(*groups: str) -> str:
    seen: list[str] = []
    for group in groups:
        for token in (group or "").split("|"):
            cleaned = token.strip()
            if cleaned and cleaned not in seen:
                seen.append(cleaned)
    return " | ".join(seen)


def recommend(row: dict[str, str]) -> dict[str, str]:
    text = " ".join(
        [
            normalize_text(row.get("item_label", "")),
            normalize_text(row.get("evidence_preview", "")),
            normalize_text(row.get("tech_domains", "")),
        ]
    )
    health_keywords = [
        "디지털헬스",
        "디지털 헬스",
        "비대면진료",
        "원격협진",
        "원격진료",
        "의료데이터",
        "의료기기",
        "의료 AI",
        "AI 의료",
        "병원",
        "Medical Korea",
    ]

    def result(
        category: str,
        primary: str,
        secondary: str,
        taxonomy_request: str,
        attention: str,
        reason: str,
    ) -> dict[str, str]:
        return {
            "draft_resolution_category": category,
            "proposed_primary_strategy_id": primary,
            "proposed_secondary_strategy_ids": secondary,
            "proposed_taxonomy_request": taxonomy_request,
            "manual_attention": attention,
            "draft_reason": reason,
        }

    if contains_any(text, ["디지털자산", "블록체인", "현물ETF", "토큰증권"]):
        return result(
            "demote_from_primary",
            "",
            "",
            "",
            "high",
            "디지털자산·블록체인 규율은 금융·시장 제도 과제로 현재 15대 전략 중 STR-010에 두기 어렵다.",
        )

    if contains_any(
        text,
        [
            "디지털성범죄",
            "딥페이크",
            "정보주체",
            "개인정보",
            "불법정보",
            "도박",
            "마약",
            "온라인안전",
            "디지털시민성",
            "스미싱",
            "피싱",
            "사이버",
            "보안사각지대",
        ],
    ):
        return result(
            "demote_from_primary",
            "",
            "",
            "",
            "high",
            "디지털 안전·권리·사이버보안 규율 과제로 STR-010 healthcare service cluster와는 직접 연결되지 않는다.",
        )

    if contains_any(text, ["K-팝", "웹툰", "콘텐츠", "미디어"]) and not contains_any(text, health_keywords):
        return result(
            "demote_from_primary",
            "STR-011",
            "",
            "",
            "medium",
            "콘텐츠·미디어 산업 진흥 맥락이 강해 STR-010보다 STR-011 또는 no_strategy 검토가 우선이다.",
        )

    if contains_any(text, ["탄소배출", "디지털제품여권", "해상풍력", "RE100"]) and not contains_any(text, health_keywords):
        return result(
            "demote_from_primary",
            "STR-006",
            "",
            "",
            "medium",
            "탄소중립 공급망·에너지 전환 대응 성격이 강해 STR-010보다 STR-006 검토가 우선이다.",
        )

    if contains_any(text, ["세부 일정", "참 고 초혁신경제"]) and contains_any(
        text,
        ["K-콘텐츠", "웹툰", "초전도", "글로벌 오픈이노베이션", "임상 3상 특화펀드"],
    ):
        return result(
            "demote_from_primary",
            "",
            dedupe_ids("STR-010", row.get("alternate_strategy_ids", "")),
            "",
            "high",
            "여러 프로젝트 일정이 섞인 composite row라서 STR-010을 primary로 확정하면 과적합 위험이 크다.",
        )

    if contains_any(
        text,
        ["데이터기반", "빅데이터", "테스트 데이터", "비식별", "다인종", "다인구", "기술경쟁력"],
    ) and contains_any(text, ["의료기기", "디지털헬스", "AI 의료", "의료 AI", "의료기기 S/W", "의료데이터", "병원"]):
        return result(
            "taxonomy_split_review",
            "STR-010",
            dedupe_ids("STR-003", row.get("alternate_strategy_ids", "")),
            "consider_split_digital_health_rnd_or_data_from_service_export_cluster",
            "high",
            "서비스·수출 지원보다는 디지털헬스 R&D/데이터 기반 구축 성격이 강해 별도 taxonomy 분할 검토가 필요하다.",
        )

    if contains_any(text, ["비대면진료", "원격협진", "Medical Korea"]) or (
        contains_any(text, health_keywords)
        and contains_any(text, ["해외진출", "플랫폼", "거점", "제도화", "실증", "홍보"])
    ):
        return result(
            "keep_primary",
            "STR-010",
            "",
            "",
            "medium",
            "비대면진료·원격협진 또는 디지털헬스 서비스 확산/수출 지원 문맥이 직접 드러난다.",
        )

    return result(
        "demote_from_primary",
        "",
        "",
        "",
        "high",
        "현재 문장만으로는 STR-010 healthcare service/export cluster와 직접 연결하기 어려워 수동 재판정이 필요하다.",
    )


def build_summary(rows: list[dict[str, str]]) -> dict[str, object]:
    category_counter = Counter(row["draft_resolution_category"] for row in rows)
    attention_counter = Counter(row["manual_attention"] for row in rows)
    policy_counter = Counter(f"{row['policy_id']} {row['policy_name']}" for row in rows)
    return {
        "draft_item_count": len(rows),
        "category_counts": dict(category_counter),
        "attention_counts": dict(attention_counter),
        "policy_counts": dict(policy_counter),
    }


def build_markdown(exception_id: str, summary: dict[str, object], rows: list[dict[str, str]]) -> str:
    category_lines = [f"- `{key}`: {value}" for key, value in summary["category_counts"].items()] or ["- 없음"]
    high_attention = [row for row in rows if row["manual_attention"] == "high"][:12]

    lines = [
        f"# {exception_id} Draft Resolution",
        "",
        "이 문서는 alignment exception packet에 대한 규칙 기반 수동 검토 초안이다.",
        "",
        "## 분류 요약",
        "",
        *category_lines,
        "",
        "## High Attention",
        "",
    ]
    if high_attention:
        for row in high_attention:
            lines.append(
                f"- `{row['decision_key']}` `{row['draft_resolution_category']}` `{row['item_label']}`"
                f" -> `{row['proposed_primary_strategy_id']}` / `{row['proposed_secondary_strategy_ids']}`"
                f" : {row['draft_reason']}"
            )
    else:
        lines.append("- 없음")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet-index-csv", required=True)
    parser.add_argument("--packets-dir", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--out-index-csv", required=True)
    parser.add_argument("--out-summary-json", required=True)
    args = parser.parse_args()

    packet_index_rows = read_csv(Path(args.packet_index_csv))
    packets_dir = Path(args.packets_dir)
    out_dir = Path(args.out_dir)

    index_rows: list[dict[str, object]] = []
    overall_category_counter = Counter()
    keep_names: set[str] = set()

    for index_row in packet_index_rows:
        if int(index_row.get("active_item_count", 0) or 0) == 0:
            continue
        packet_csv = packets_dir / index_row["output_csv"]
        packet_rows = read_csv(packet_csv)
        output_rows: list[dict[str, str]] = []
        for row in packet_rows:
            merged = {field: row.get(field, "") for field in OUTPUT_FIELDS if field in row}
            merged.update(recommend(row))
            output_rows.append(merged)

        exception_id = index_row["exception_id"]
        summary = build_summary(output_rows)
        overall_category_counter.update(summary["category_counts"])
        base_stem = packet_csv.stem

        out_csv = out_dir / f"{base_stem}__draft.csv"
        out_summary = out_dir / f"{base_stem}__draft-summary.json"
        out_brief = out_dir / f"{base_stem}__draft-brief.md"
        keep_names.update({out_csv.name, out_summary.name, out_brief.name})
        write_csv(out_csv, output_rows, OUTPUT_FIELDS)
        write_json(out_summary, summary)
        write_text(out_brief, build_markdown(exception_id, summary, output_rows))

        index_rows.append(
            {
                "exception_id": exception_id,
                "output_csv": out_csv.name,
                "output_summary_json": out_summary.name,
                "output_brief_md": out_brief.name,
                "item_count": len(output_rows),
                "keep_primary_count": summary["category_counts"].get("keep_primary", 0),
                "demote_from_primary_count": summary["category_counts"].get("demote_from_primary", 0),
                "taxonomy_split_review_count": summary["category_counts"].get("taxonomy_split_review", 0),
                "high_attention_count": summary["attention_counts"].get("high", 0),
            }
        )

    summary_payload = {
        "exception_draft_count": len(index_rows),
        "category_counts": dict(overall_category_counter),
        "drafts": index_rows,
    }
    summary_payload["removed_stale_files"] = cleanup_stale_files(
        out_dir,
        keep_names,
        [
            "*__alignment-review__draft.csv",
            "*__alignment-review__draft-summary.json",
            "*__alignment-review__draft-brief.md",
        ],
    )

    write_csv(Path(args.out_index_csv), index_rows, INDEX_FIELDS)
    write_json(Path(args.out_summary_json), summary_payload)
    print(f"Strategy alignment exception drafts: {len(index_rows)}")


if __name__ == "__main__":
    main()
