#!/usr/bin/env python3
"""Finalize explicit manual decisions for selected technology lens review rows."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


REVIEWER_NAME = "codex_manual_technology_lens_review"


FINAL_DECISIONS = {
    "TLR-TD-002-4ce18cf6e771": {
        "decision_status": "revised",
        "reviewed_group_label": "기후테크 육성",
        "reviewed_group_summary": "기후대응 에너지 산업을 육성해 그린 강국 도약을 추진하는 과제.",
        "reviewed_group_description": "",
        "reviewer_notes": "에너지 기술축의 대표 근거로 유지하되 raw 접두 표기와 압축 문장을 정리한다.",
    },
    "TLR-TD-002-a67a4179bb8e": {
        "decision_status": "revised",
        "reviewed_group_label": "미래전략산업·에너지 인프라 성장펀드",
        "reviewed_group_summary": "AI 등 미래전략산업과 에너지 인프라에 투자하는 민관 합동 대규모 성장펀드 조성 과제.",
        "reviewed_group_description": "",
        "reviewer_notes": "범용 펀드지만 에너지 인프라 투자가 명시되어 infra/institution 그룹으로 유지한다.",
    },
    "TLR-TD-002-32f58df085a6": {
        "decision_status": "rejected",
        "reviewed_group_label": "",
        "reviewed_group_summary": "",
        "reviewed_group_description": "",
        "reviewer_notes": "초전도체는 에너지 응용이 포함되지만 소재·양자 성격이 더 강해 에너지 대표 그룹으로 확정하지 않는다.",
    },
    "TLR-TD-003-ce55f5599417": {
        "decision_status": "revised",
        "reviewed_group_label": "동남권 항공·이차전지 국가산단 조성",
        "reviewed_group_summary": "동남권에 항공·이차전지 국가산단을 조성하는 지역 산업기반 확충 과제.",
        "reviewed_group_description": "",
        "reviewer_notes": "이차전지 지역 거점 조성 근거가 직접적이라 유지하되 카드 라벨을 정리한다.",
    },
    "TLR-TD-003-3ef8a03e8dca": {
        "decision_status": "revised",
        "reviewed_group_label": "이차전지 위기산업 특단대책",
        "reviewed_group_summary": "이차전지를 포함한 위기업종 특단대책과 산업위기지역 패키지 지원을 추진하는 과제.",
        "reviewed_group_description": "",
        "reviewer_notes": "이차전지를 명시한 산업 지원 정책이어서 유지하되 요약을 정제한다.",
    },
    "TLR-TD-004-bd6fea254f33": {
        "decision_status": "revised",
        "reviewed_group_label": "AI·첨단과학 기반 국방개혁 로드맵",
        "reviewed_group_summary": "AI·첨단과학기술 기반 스마트강군 육성을 위한 국방개혁 로드맵 마련 및 추진 과제.",
        "reviewed_group_description": "",
        "reviewer_notes": "국방 기술 전환의 직접 근거이므로 유지하되 카드 문구를 명시적으로 다듬는다.",
    },
    "TLR-TD-004-bdd639ad4cd4": {
        "decision_status": "rejected",
        "reviewed_group_label": "",
        "reviewed_group_summary": "",
        "reviewed_group_description": "",
        "reviewer_notes": "군사법개혁은 국방 기술축이 아니라 사법·거버넌스 개편 과제다.",
    },
    "TLR-TD-004-cc9d6e3bfe9c": {
        "decision_status": "revised",
        "reviewed_group_label": "국방 AI 신속개발·활용",
        "reviewed_group_summary": "국방 데이터·보안 체계 개선과 맞춤형 획득 프로세스 마련으로 국방 AI 활용을 가속하는 과제.",
        "reviewed_group_description": "",
        "reviewer_notes": "국방 AI 활용 기반을 직접 설명하는 항목으로 유지한다.",
    },
    "TLR-TD-005-f653497af274": {
        "decision_status": "revised",
        "reviewed_group_label": "바이오파운드리 기반 첨단바이오소재 구축",
        "reviewed_group_summary": "첨단 바이오소재 후보물질의 개발·생산이 가능한 바이오파운드리를 구축하는 과제.",
        "reviewed_group_description": "",
        "reviewer_notes": "소재 기술축에서 바이오소재 생산 기반을 직접 설명하는 항목이다.",
    },
    "TLR-TD-005-cb9b63d36b6e": {
        "decision_status": "approved",
        "reviewed_group_label": "",
        "reviewed_group_summary": "",
        "reviewed_group_description": "",
        "reviewer_notes": "지역특화 고부가가치 소재 연구·활용과 인프라 구축이 명시되어 소재 그룹으로 유지한다.",
    },
    "TLR-TD-005-05e9dec21247": {
        "decision_status": "revised",
        "reviewed_group_label": "수소환원제철·스페셜티소재 전환",
        "reviewed_group_summary": "수소환원제철과 스페셜티 소재 중심으로 탄소감축과 고부가가치화를 추진하는 과제.",
        "reviewed_group_description": "",
        "reviewer_notes": "철강·화학 소재 고도화 맥락이 분명해 소재 기술축에 유지한다.",
    },
    "TLR-TD-006-edab63e76ef2": {
        "decision_status": "revised",
        "reviewed_group_label": "보안 사각지대 지원 강화",
        "reviewed_group_summary": "지역·중소기업 등 보안 취약 영역 지원과 디지털 역기능 해소, 정보보호산업 육성을 함께 추진하는 과제.",
        "reviewed_group_description": "",
        "reviewer_notes": "사이버보안 기술·산업 지원이 직접 드러나므로 유지하되 카드 문구를 정리한다.",
    },
    "TLR-TD-006-ad0e627cbfd6": {
        "decision_status": "approved",
        "reviewed_group_label": "",
        "reviewed_group_summary": "",
        "reviewed_group_description": "",
        "reviewer_notes": "AI 기반 사이버위협 대응과 정보보호 제도 개편이 직접 연결돼 있어 그대로 승인한다.",
    },
    "TLR-TD-007-d0feb1b8ba17": {
        "decision_status": "revised",
        "reviewed_group_label": "6G·AI 네트워크 선도국 도약",
        "reviewed_group_summary": "6G와 AI 네트워크 초격차 기술개발 및 융합서비스 조기 실증에 선제 투자하는 과제.",
        "reviewed_group_description": "",
        "reviewer_notes": "차세대 통신 핵심 정책 문구이므로 유지하되 과도한 원문 수식을 압축한다.",
    },
    "TLR-TD-007-ef19533c64dd": {
        "decision_status": "approved",
        "reviewed_group_label": "",
        "reviewed_group_summary": "",
        "reviewed_group_description": "",
        "reviewer_notes": "기지국 효율화와 저전력 통신망 구축은 차세대 통신 인프라 정책으로 타당하다.",
    },
    "TLR-TD-007-966edd842344": {
        "decision_status": "revised",
        "reviewed_group_label": "초지능 네트워크 구축",
        "reviewed_group_summary": "AI에 최적화된 6G 상용화와 초지능 네트워크 인프라 구축을 추진하는 과제.",
        "reviewed_group_description": "",
        "reviewer_notes": "원문이 잘린 카드라서 대표 라벨과 요약을 복원한다.",
    },
    "TLR-TD-008-50137b46d117": {
        "decision_status": "revised",
        "reviewed_group_label": "산업 AI 전환 촉진",
        "reviewed_group_summary": "제조기업 AI 팩토리 전환과 중소기업 AI 바우처 지원으로 산업 현장 AI 도입을 확산하는 과제.",
        "reviewed_group_description": "",
        "reviewer_notes": "첨단제조 축에서 가장 직접적인 산업 AI 전환 과제라 유지한다.",
    },
    "TLR-TD-008-b0a7199c166f": {
        "decision_status": "rejected",
        "reviewed_group_label": "",
        "reviewed_group_summary": "",
        "reviewed_group_description": "",
        "reviewer_notes": "자율운항 선박 실증은 첨단로봇제조보다 해양·모빌리티 성격이 강하다.",
    },
    "TLR-TD-008-3a9a03ff49e9": {
        "decision_status": "rejected",
        "reviewed_group_label": "",
        "reviewed_group_summary": "",
        "reviewed_group_description": "",
        "reviewer_notes": "교통·물류·안전 서비스 생산성 제고는 범용 AI 서비스 과제로 첨단로봇제조 대표 그룹으로는 범위가 너무 넓다.",
    },
    "TLR-TD-010-3ec90a2c74f3": {
        "decision_status": "revised",
        "reviewed_group_label": "양자과학기술 전략 중추기관 육성",
        "reviewed_group_summary": "양자과학기술 등 첨단 기초과학 분야의 전략·도전 연구 중추기관을 육성하는 과제.",
        "reviewed_group_description": "",
        "reviewer_notes": "양자 역량 확충 근거가 분명하지만 범주를 더 분명하게 보이도록 카드 문구를 조정한다.",
    },
    "TLR-TD-010-ffc2d71e979f": {
        "decision_status": "revised",
        "reviewed_group_label": "양자컴퓨터 하이브리드 활용",
        "reviewed_group_summary": "양자컴퓨터-슈퍼컴퓨터 하이브리드 시스템을 구축해 신약 개발 등 난제 해결을 지원하는 과제.",
        "reviewed_group_description": "",
        "reviewer_notes": "바이오 응용 사례를 담고 있지만 양자컴 활용 인프라 자체가 핵심이라 양자 축에 유지한다.",
    },
    "TLR-TD-012-76d0998377d3": {
        "decision_status": "revised",
        "reviewed_group_label": "위성 기반 광역감시 정보체계 구축",
        "reviewed_group_summary": "위성 등 첨단기술을 활용한 광역 감시·정보체계를 구축하는 과제.",
        "reviewed_group_description": "",
        "reviewer_notes": "우주항공 축에서 위성 기반 감시 체계 근거로 직접 읽힌다.",
    },
    "TLR-TD-012-4a0f70917b9b": {
        "decision_status": "approved",
        "reviewed_group_label": "",
        "reviewed_group_summary": "",
        "reviewed_group_description": "",
        "reviewer_notes": "K-Space 클러스터와 재사용발사체 개발을 직접 다루는 대표 항목이라 그대로 승인한다.",
    },
    "TLR-TD-012-4881777fc9c4": {
        "decision_status": "rejected",
        "reviewed_group_label": "",
        "reviewed_group_summary": "",
        "reviewed_group_description": "",
        "reviewer_notes": "AI·항공엔진·반도체·우주·드론·로봇이 결합된 범분야 산업 총론이라 우주항공 대표 그룹으로 확정하지 않는다.",
    },
    "TLR-TD-013-d937ad4b82ee": {
        "decision_status": "revised",
        "reviewed_group_label": "관할해역 감시체계 강화",
        "reviewed_group_summary": "관할해역 감시 역량을 강화해 해양안보를 고도화하고 해양생태계 보전을 병행하는 과제.",
        "reviewed_group_description": "",
        "reviewer_notes": "해양 안보·감시 인프라 축으로 직접 연결되지만 원문 문장을 카드형으로 정리한다.",
    },
    "TLR-TD-013-d5154b106a4e": {
        "decision_status": "revised",
        "reviewed_group_label": "국가해상수송력·허브항만 확충",
        "reviewed_group_summary": "국가 해상수송력 확충과 글로벌 허브항만 완성으로 해양 물류 기반을 강화하는 과제.",
        "reviewed_group_description": "",
        "reviewer_notes": "해양 물류·항만 기반을 직접 다루므로 해양 축에 유지한다.",
    },
    "TLR-TD-013-08a589cbabe1": {
        "decision_status": "revised",
        "reviewed_group_label": "해상풍력 설치선·전용항만 기반 강화",
        "reviewed_group_summary": "해상풍력 기자재 기술개발과 설치선 건조, 전용항만 설치를 추진하는 과제.",
        "reviewed_group_description": "",
        "reviewer_notes": "복합 문장 중 해상풍력 설치선·전용항만 부분을 해양 산업기반 대표 근거로 남긴다.",
    },
    "TLR-TD-014-4c38ed4205e2": {
        "decision_status": "revised",
        "reviewed_group_label": "미래차 혁신 생태계 조성",
        "reviewed_group_summary": "친환경차, SDV, AI 자율주행차 중심의 미래차 혁신 생태계를 조성하는 과제.",
        "reviewed_group_description": "",
        "reviewer_notes": "첨단모빌리티 핵심 키워드가 직접 모여 있어 대표 그룹으로 유지한다.",
    },
    "TLR-TD-014-8192cc2ff85b": {
        "decision_status": "revised",
        "reviewed_group_label": "전기차·PM 안전대책 및 자율주행 질서 정비",
        "reviewed_group_summary": "전기차·이륜차·개인이동수단 안전대책과 자율주행 법·질서 정비를 추진하는 과제.",
        "reviewed_group_description": "",
        "reviewer_notes": "첨단모빌리티의 제도·안전 축을 대표하는 인프라·제도 그룹으로 유지한다.",
    },
    "TLR-TD-014-34e8cd14b230": {
        "decision_status": "approved",
        "reviewed_group_label": "",
        "reviewed_group_summary": "",
        "reviewed_group_description": "",
        "reviewer_notes": "레벨4 자율차 출시와 자율주행 AI 인프라 구축을 직접 설명하는 대표 정책이어서 그대로 승인한다.",
    },
}


OUTPUT_FIELDS = [
    "decision_key",
    "tech_domain_id",
    "tech_domain_label",
    "policy_item_group_id",
    "policy_id",
    "policy_name",
    "group_label",
    "final_decision_status",
    "final_group_label",
    "final_group_summary",
    "final_group_description",
    "reviewer_name",
    "reviewer_notes",
]


MASTER_DECISION_FIELDS = [
    "decision_key",
    "active_in_queue",
    "tech_domain_id",
    "tech_domain_label",
    "policy_item_group_id",
    "policy_id",
    "policy_name",
    "resource_category_id",
    "resource_category_label",
    "group_label",
    "group_summary",
    "group_status",
    "source_basis_type",
    "content_count",
    "evidence_count",
    "member_item_count",
    "source_policy_item_ids",
    "primary_strategy_id",
    "primary_strategy_label",
    "primary_tech_subdomain_id",
    "primary_tech_subdomain_label",
    "primary_document_id",
    "primary_location_value",
    "decision_status",
    "reviewed_group_label",
    "reviewed_group_summary",
    "reviewed_group_description",
    "reviewer_name",
    "reviewer_notes",
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


def apply_to_master(master_rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], int]:
    updated_count = 0
    for row in master_rows:
        final = FINAL_DECISIONS.get(row.get("decision_key", ""))
        if not final:
            continue
        next_values = {
            "decision_status": final["decision_status"],
            "reviewed_group_label": final["reviewed_group_label"],
            "reviewed_group_summary": final["reviewed_group_summary"],
            "reviewed_group_description": final["reviewed_group_description"],
            "reviewer_name": REVIEWER_NAME,
            "reviewer_notes": final["reviewer_notes"],
        }
        changed = any(row.get(field, "") != value for field, value in next_values.items())
        for field, value in next_values.items():
            row[field] = value
        if changed:
            updated_count += 1
    return master_rows, updated_count


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--decision-csv", required=True)
    parser.add_argument("--out-csv", required=True)
    parser.add_argument("--out-summary-json", required=True)
    args = parser.parse_args()

    decision_path = Path(args.decision_csv)
    master_rows = read_csv(decision_path)
    master_lookup = {row["decision_key"]: row for row in master_rows if row.get("decision_key")}

    missing_keys = sorted(key for key in FINAL_DECISIONS if key not in master_lookup)
    if missing_keys:
        raise KeyError(f"Missing technology lens review rows for manual decisions: {missing_keys}")

    updated_rows, updated_count = apply_to_master(master_rows)
    write_csv(
        decision_path,
        updated_rows,
        MASTER_DECISION_FIELDS if not updated_rows else list(updated_rows[0].keys()),
    )

    final_rows = []
    for decision_key, final in FINAL_DECISIONS.items():
        source_row = master_lookup[decision_key]
        final_rows.append(
            {
                "decision_key": decision_key,
                "tech_domain_id": source_row.get("tech_domain_id", ""),
                "tech_domain_label": source_row.get("tech_domain_label", ""),
                "policy_item_group_id": source_row.get("policy_item_group_id", ""),
                "policy_id": source_row.get("policy_id", ""),
                "policy_name": source_row.get("policy_name", ""),
                "group_label": source_row.get("group_label", ""),
                "final_decision_status": final["decision_status"],
                "final_group_label": final["reviewed_group_label"],
                "final_group_summary": final["reviewed_group_summary"],
                "final_group_description": final["reviewed_group_description"],
                "reviewer_name": REVIEWER_NAME,
                "reviewer_notes": final["reviewer_notes"],
            }
        )

    write_csv(Path(args.out_csv), final_rows, OUTPUT_FIELDS)
    write_json(
        Path(args.out_summary_json),
        {
            "decision_count": len(final_rows),
            "status_counts": dict(Counter(row["final_decision_status"] for row in final_rows)),
            "updated_master_rows": updated_count,
            "reviewer_name": REVIEWER_NAME,
            "decision_csv": args.decision_csv,
        },
    )
    print(f"Technology lens manual decisions finalized: {len(final_rows)}")


if __name__ == "__main__":
    main()
