#!/usr/bin/env python3
"""Build conservative draft recommendations for a strategy review batch."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path


OUTPUT_FIELDS = [
    "decision_key",
    "review_item_id",
    "policy_item_id",
    "policy_id",
    "policy_name",
    "bucket_label",
    "item_label",
    "primary_evidence_id",
    "tech_domains",
    "evidence_preview",
    "suggested_primary_strategy_id",
    "suggested_primary_strategy_label",
    "suggested_primary_strategy_score",
    "alternate_strategy_ids",
    "alternate_strategy_labels",
    "alignment_exception_ids",
    "alignment_exception_notes",
    "auto_seed_blocked",
    "recommended_decision_status",
    "recommended_primary_strategy_id",
    "recommended_secondary_strategy_ids",
    "recommended_confidence",
    "manual_attention",
    "recommendation_reason",
]


STRATEGY_LABELS = {
    "STR-001": "AI G3 도약 및 전 산업 AX 확산",
    "STR-003": "바이오·헬스 글로벌 중심국가 도약",
    "STR-006": "탄소중립 및 에너지 안보 (수소·SMR)",
    "STR-007": "양자 정보통신 및 미래소재 선점",
    "STR-008": "피지컬 AI 및 지능형 로봇 산업 육성",
    "STR-010": "디지털 헬스케어 서비스 혁신",
    "STR-011": "디지털 콘텐츠 및 K-컬처 혁신",
}


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


def recommend(row: dict[str, str]) -> dict[str, str]:
    text = " ".join(
        [
            normalize_text(row.get("item_label", "")),
            normalize_text(row.get("evidence_preview", "")),
            normalize_text(row.get("tech_domains", "")),
        ]
    )
    text_lower = text.lower()

    def result(
        status: str,
        primary: str = "",
        secondary: str = "",
        confidence: str = "",
        attention: str = "medium",
        reason: str = "",
    ) -> dict[str, str]:
        return {
            "recommended_decision_status": status,
            "recommended_primary_strategy_id": primary,
            "recommended_secondary_strategy_ids": secondary,
            "recommended_confidence": confidence,
            "manual_attention": attention,
            "recommendation_reason": reason,
        }

    if (row.get("auto_seed_blocked") or "").strip().lower() == "yes":
        suggested_id = row.get("suggested_primary_strategy_id", "")
        return result(
            "deferred",
            suggested_id,
            "",
            "",
            "high",
            f"alignment exception {row.get('alignment_exception_ids', '')} 때문에 자동 확정을 막고 수동 검토로 남긴다.",
        )

    if contains_any(text, ["초전도", "초전도자석", "선재", "도체", "핵융합", "CERN", "극저온", "고자장"]):
        return result(
            "reviewed",
            "STR-007",
            "",
            "high",
            "low",
            "초전도·선재·핵융합 등 미래소재/초전도 축이 직접 드러난다.",
        )

    content_keywords = ["웹툰", "만화", "판호", "영화", "음원", "뮤직비디오", "음악영상물", "방송영상", "문화산업진흥법"]
    is_game_content = contains_any(text, content_keywords)
    is_game_content = is_game_content or ("게임" in text and "게임체인저" not in text)
    is_game_content = is_game_content or ("영상" in text and not contains_any(text, ["의료영상", "영상의학", "의료시스템"]))

    if is_game_content:
        secondary = "STR-001" if "AI" in text or "ai" in text_lower else ""
        reason = "게임/웹툰/만화/판호 등 K-콘텐츠 수출·제작 지원 항목이다."
        if secondary:
            reason += " AI는 도구 성격이므로 보조 축으로만 둔다."
        return result("reviewed", "STR-011", secondary, "high", "low", reason)

    if contains_any(text, ["AI 영화", "ai 영화", "영화제작"]):
        return result(
            "reviewed",
            "STR-011",
            "STR-001",
            "high",
            "low",
            "영화 제작지원이 본체이고 AI는 제작도구 성격이라 콘텐츠 전략을 우선한다.",
        )

    has_health_service = contains_any(
        text,
        [
            "Medical Korea",
            "의료시스템",
            "보험등재",
            "의료기술평가",
            "의료기기",
            "비대면",
            "원격",
            "원격협진",
            "의료기관",
            "사용적합성평가",
        ],
    )
    has_health_service = has_health_service or ("의료" in text and contains_any(text, ["인허가", "실증", "임상", "시장", "평가", "보험"]))

    if has_health_service:
        secondary = "STR-001" if contains_any(text, ["AI", "ai", "ICT", "디지털"]) else ""
        return result(
            "reviewed",
            "STR-010",
            secondary,
            "high" if contains_any(text, ["Medical Korea", "의료시스템", "보험등재", "의료기술평가"]) else "medium",
            "low" if contains_any(text, ["Medical Korea", "의료시스템", "보험등재", "의료기술평가"]) else "medium",
            "의료 해외진출·보험등재·디지털헬스 서비스 확산 맥락으로 디지털 헬스케어 축이 명확하다.",
        )

    has_bio = contains_any(
        text,
        ["신약", "제약", "바이오", "CDMO", "임상 3상", "의약품", "바이오의약", "글로벌제약펀드", "제약사", "보건계정펀드"],
    )
    has_bio = has_bio or ("펀드" in text and contains_any(text, ["임상", "바이오", "제약", "의약"]))

    if has_bio:
        secondary = "STR-015" if contains_any(text, ["백신", "감염병"]) else ""
        attention = "low" if contains_any(text, ["신약", "제약", "바이오", "CDMO", "임상 3상", "의약품"]) else "medium"
        confidence = "high" if attention == "low" else "medium"
        return result(
            "reviewed",
            "STR-003",
            secondary,
            confidence,
            attention,
            "신약·제약·바이오 상업화/생산/펀드/임상 지원 항목으로 바이오·헬스 축이 직접적이다.",
        )

    if contains_any(text, ["백신", "mRNA", "감염병", "공중보건"]):
        return result(
            "reviewed",
            "STR-015",
            "STR-003" if contains_any(text, ["바이오", "신약", "제약"]) else "",
            "high",
            "low",
            "백신·감염병·공중보건 대응이 직접 드러난다.",
        )

    if "첨단로봇제조" in text:
        return result(
            "reviewed",
            "STR-008",
            "",
            "medium",
            "high",
            "기술분야 태그가 첨단로봇제조이나 본문 직접 단서가 약해 로봇 전략 초안으로만 둔다.",
        )

    if contains_any(text, ["수소", "SMR", "전력망", "HVDC", "해상풍력", "태양광"]):
        return result(
            "reviewed",
            "STR-006",
            "",
            "high",
            "low",
            "에너지 전환/전력망/수소/SMR 등 에너지 전략 단서가 명확하다.",
        )

    if contains_any(text, ["초혁신경제", "선도형경제", "글로벌 시장진출", "미래대응"]) and not contains_any(
        text,
        ["바이오", "초전도", "게임", "웹툰", "의료", "에너지"],
    ):
        return result(
            "no_strategy",
            "",
            "",
            "",
            "low",
            "정책 총론 또는 범분야 비전 서술로 특정 15대 전략 하나에 귀속하기 어렵다.",
        )

    if contains_any(text, ["첨단소재", "소재․부품", "첨단소재․부품"]) and "초전도" not in text:
        return result(
            "deferred",
            "",
            "",
            "",
            "high",
            "소재 프로젝트 맥락은 보이나 현재 문장만으로는 미래소재/전략기술 자립 중 어느 축인지 추가 문맥 확인이 필요하다.",
        )

    if contains_any(text, ["기술·에너지·식량"]) or contains_any(text, ["추격형경제", "선도형경제"]):
        return result(
            "no_strategy",
            "",
            "",
            "",
            "medium",
            "여러 전략을 포괄하는 거시 서술이라 단일 전략으로 고정하지 않는다.",
        )

    if contains_any(text, ["투자 실적", "구체적인 프로젝트", "문제해결형지원체계", "재정·세제·금융지원"]) and not contains_any(
        text,
        ["의료", "바이오", "제약", "초전도", "게임", "웹툰", "영화", "음악"],
    ):
        return result(
            "no_strategy",
            "",
            "",
            "",
            "medium",
            "범용 투자·지원체계 설명으로 특정 전략 귀속 근거가 약하다.",
        )

    suggested_id = row.get("suggested_primary_strategy_id", "")
    if suggested_id in STRATEGY_LABELS:
        return result(
            "deferred",
            suggested_id,
            "",
            "low",
            "high",
            "직접 단서가 부족해 자동 제안은 참고만 하고 사람 검토를 남긴다.",
        )

    return result(
        "deferred",
        "",
        "",
        "",
        "high",
        "직접 단서가 부족하여 수동 검토가 필요하다.",
    )


def build_summary(rows: list[dict[str, str]]) -> dict[str, object]:
    status_counter = Counter(row["recommended_decision_status"] for row in rows)
    primary_counter = Counter(
        f"{row['recommended_primary_strategy_id']} {STRATEGY_LABELS.get(row['recommended_primary_strategy_id'], '')}".strip()
        for row in rows
        if row["recommended_primary_strategy_id"]
    )
    attention_counter = Counter(row["manual_attention"] for row in rows)
    return {
        "draft_item_count": len(rows),
        "status_counts": dict(status_counter),
        "primary_strategy_counts": dict(primary_counter),
        "attention_counts": dict(attention_counter),
    }


def build_markdown(summary: dict[str, object], rows: list[dict[str, str]], batch_name: str) -> str:
    strategy_lines = [f"- `{key}`: {value}" for key, value in summary["primary_strategy_counts"].items()]
    if not strategy_lines:
        strategy_lines = ["- 없음"]
    lines = [
        f"# {batch_name} 드래프트 추천",
        "",
        "이 문서는 규칙 기반 초안이며, ontology에 자동 반영되지 않는다.",
        "",
        "## 요약",
        "",
        *[f"- `{key}`: {value}" for key, value in summary["status_counts"].items()],
        "",
        "## 추천 전략 분포",
        "",
        *strategy_lines,
        "",
        "## 수동 주의 항목",
        "",
    ]

    high_attention = [row for row in rows if row["manual_attention"] == "high"][:12]
    if high_attention:
        for row in high_attention:
            lines.append(
                f"- `{row['decision_key']}` `{row['recommended_decision_status']}` `{row['recommended_primary_strategy_id']}` {row['item_label']} : {row['recommendation_reason']}"
            )
    else:
        lines.append("- 없음")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-csv", required=True)
    parser.add_argument("--out-csv", required=True)
    parser.add_argument("--out-summary-json", required=True)
    parser.add_argument("--out-brief-md", required=True)
    args = parser.parse_args()

    rows = read_csv(Path(args.batch_csv))
    output_rows: list[dict[str, str]] = []
    for row in rows:
        merged = {field: row.get(field, "") for field in OUTPUT_FIELDS if field in row}
        merged.update(recommend(row))
        output_rows.append(merged)

    summary = build_summary(output_rows)
    batch_name = Path(args.batch_csv).stem
    write_csv(Path(args.out_csv), output_rows, OUTPUT_FIELDS)
    write_json(Path(args.out_summary_json), summary)
    write_text(Path(args.out_brief_md), build_markdown(summary, output_rows, batch_name))
    print(f"Draft recommendations: {len(output_rows)}")


if __name__ == "__main__":
    main()
