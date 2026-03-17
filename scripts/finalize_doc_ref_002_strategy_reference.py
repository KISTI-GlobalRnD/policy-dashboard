#!/usr/bin/env python3
"""Materialize manual canonical references for DOC-REF-002.

DOC-REF-002 is a one-page board that groups source policy documents into
"기술 / 인프라·제도 / 인재·제도" bands.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


SOURCE_POLICY_DOCUMENTS = [
    {
        "display_order": 1,
        "document_id": "DOC-POL-001",
        "policy_id": "POL-001",
        "board_label": "123대 국정과제",
        "board_citation": "국정과제 ('25.8)",
    },
    {
        "display_order": 2,
        "document_id": "DOC-POL-002",
        "policy_id": "POL-002",
        "board_label": "AI·바이오 국가전략",
        "board_citation": "과기정통부, '25.12.18",
    },
    {
        "display_order": 3,
        "document_id": "DOC-POL-004",
        "policy_id": "POL-003",
        "board_label": "과학기술xAI 국가전략",
        "board_citation": "과기정통부, '25.11.22",
    },
    {
        "display_order": 4,
        "document_id": "DOC-POL-011",
        "policy_id": "POL-004",
        "board_label": "AI시대 대한민국 네트워크 전략",
        "board_citation": "과기정통부, '25.12.18",
    },
    {
        "display_order": 5,
        "document_id": "DOC-POL-007",
        "policy_id": "POL-005",
        "board_label": "AI반도체 산업 도약전략",
        "board_citation": "산업통상부, '25.12.18",
    },
    {
        "display_order": 6,
        "document_id": "DOC-POL-003",
        "policy_id": "POL-006",
        "board_label": "제조AX 추진방향",
        "board_citation": "산업통상부, '25.12.22",
    },
    {
        "display_order": 7,
        "document_id": "DOC-POL-009",
        "policy_id": "POL-007",
        "board_label": "기초연구 생태계 육성방안",
        "board_citation": "과기정통부, '25.12.18",
    },
    {
        "display_order": 8,
        "document_id": "DOC-POL-008",
        "policy_id": "POL-008",
        "board_label": "민간투자·팁스 R&D 확산방안",
        "board_citation": "중소벤처기업부, '25.12.18",
    },
    {
        "display_order": 9,
        "document_id": "DOC-POL-010",
        "policy_id": "POL-009",
        "board_label": "과학기술분야 출연(연) 정책방향",
        "board_citation": "과기정통부, '25.12.18",
    },
    {
        "display_order": 10,
        "document_id": "DOC-POL-005",
        "policy_id": "POL-010",
        "board_label": "연구개발 생태계 혁신방안",
        "board_citation": "과기정통부, '25.11.22",
    },
    {
        "display_order": 11,
        "document_id": "DOC-POL-012",
        "policy_id": "POL-011",
        "board_label": "정부 AX사업 전주기 원스톱 지원방안",
        "board_citation": "과기정통부·행정안전부, '26.1.28",
    },
    {
        "display_order": 12,
        "document_id": "DOC-POL-006",
        "policy_id": "POL-012",
        "board_label": "초혁신경제 15대 프로젝트 추진계획",
        "board_citation": "기획재정부, '25.12.16",
    },
]


TECH_STRATEGY_ROWS = [
    {
        "sequence_no": 1,
        "strategy_label": "AI G3 도약 및 전 산업 AX 확산",
        "content_summary": "AI 파운데이션 모델 개발 및 전 산업 인공지능 전환(AX) 가속화",
    },
    {
        "sequence_no": 2,
        "strategy_label": "초격차 전략기술 확보 (반도체·이차전지)",
        "content_summary": "차세대 AI 반도체(NPU, PIM) 및 고성능 이차전지 초격차 기술 확보",
    },
    {
        "sequence_no": 3,
        "strategy_label": "바이오·헬스 글로벌 중심국가 도약",
        "content_summary": "AI 기반 차세대 바이오의료·헬스 시스템 글로벌 혁신",
    },
    {
        "sequence_no": 4,
        "strategy_label": "차세대 네트워크(6G) 및 지능형 인프라",
        "content_summary": "6G 상용화 기술 확보 및 저궤도 위성통신 기반 초연결망 구축",
    },
    {
        "sequence_no": 5,
        "strategy_label": "우주항공 및 해양 기술주권 확보",
        "content_summary": "독자적 항공엔진 개발 및 완전 자율운항 선박 핵심기술 확보",
    },
    {
        "sequence_no": 6,
        "strategy_label": "탄소중립 및 에너지 안보 (수소·SMR)",
        "content_summary": "그린수소 생산 및 소형모듈원자로(SMR) 상용화 기술 개발",
    },
    {
        "sequence_no": 7,
        "strategy_label": "양자 정보통신 및 미래소재 선점",
        "content_summary": "양자 컴퓨팅 원천기술 및 초전도체, 그래핀 등 게임체인저 소재 개발",
    },
    {
        "sequence_no": 8,
        "strategy_label": "피지컬 AI 및 지능형 로봇 산업 육성",
        "content_summary": "인간 공존형 로봇 및 산업 현장 자율화 로봇 기술 고도화",
    },
    {
        "sequence_no": 9,
        "strategy_label": "미래 모빌리티(자율주행·UAM)",
        "content_summary": "자율주행 소프트웨어(SDV) 및 도심항공교통(UAM) 상용화",
    },
    {
        "sequence_no": 10,
        "strategy_label": "사이버 보안 및 AI 신뢰성 검증 기술 확보",
        "content_summary": "데이터 중심 정보보호 및 AI 신뢰성 검증 기술 확보",
    },
    {
        "sequence_no": 11,
        "strategy_label": "디지털 콘텐츠 및 K-컬처 혁신",
        "content_summary": "AI 기반 콘텐츠 제작과 K-콘텐츠 경쟁력 고도화",
    },
    {
        "sequence_no": 12,
        "strategy_label": "스마트 농업 및 수산업 기술",
        "content_summary": "스마트 농업·수산업 생산 고도화와 식량안보 대응",
    },
    {
        "sequence_no": 13,
        "strategy_label": "디지털 트윈 및 가상화 공정 혁신",
        "content_summary": "산업 생산성 향상을 위한 가상 모형 및 시뮬레이션 기술",
    },
    {
        "sequence_no": 14,
        "strategy_label": "핵심 전략기술 자립 (LNG화물창·특수강)",
        "content_summary": "에너지 및 주력 산업의 소재·부품·장비 자립화",
    },
    {
        "sequence_no": 15,
        "strategy_label": "감염병 대응 및 공중보건 기술 자립",
        "content_summary": "mRNA 백신 플랫폼 및 정밀 의료 기술 국산화",
    },
]


TECH_ROW_LEVEL_NOTES = {
    "11": "우측 보드 텍스트가 부분 훼손되어 라벨과 가독 가능한 키워드를 기준으로 summary를 정규화했다.",
    "12": "우측 보드 텍스트가 부분 훼손되어 라벨과 가독 가능한 키워드를 기준으로 summary를 정규화했다.",
    "14": "우측 보드 텍스트가 부분 훼손되어 라벨과 가독 가능한 키워드를 기준으로 summary를 정규화했다.",
}


INFRA_POLICY_ROWS = [
    {
        "sequence_no": 1,
        "factor_label": "국가 AI 컴퓨팅 인프라(GPU) 확충",
        "content_summary": "정부 보유 첨단 GPU 확충과 공동활용 체계로 범부처 AI 인프라 접근성 강화",
    },
    {
        "sequence_no": 2,
        "factor_label": "R&D 예비타당성 조사 폐지 및 신속 지원",
        "content_summary": "당락형 예타 대신 기획보완형 사전점검으로 연구개발 추진 속도 제고",
    },
    {
        "sequence_no": 3,
        "factor_label": "대학 단위 연구혁신 기반 구축",
        "content_summary": "대학 단위 연구시설·장비·연구지원인력을 블록펀딩 방식으로 지원",
    },
    {
        "sequence_no": 4,
        "factor_label": "정부 AX 원스톱 지원 및 공공 지능화",
        "content_summary": "부처별 AX 사업의 기획·수행·평가 전주기를 원스톱으로 지원",
    },
    {
        "sequence_no": 5,
        "factor_label": "데이터 기반 연구 생태계 구축",
        "content_summary": "국가연구데이터플랫폼(DataON) 고도화 및 데이터 공유 체계",
    },
    {
        "sequence_no": 6,
        "factor_label": "출연연 임무중심 체계 및 PBS 폐지",
        "content_summary": "출연연을 임무 중심으로 개편하고 PBS를 폐지해 장기 연구 기반 강화",
    },
    {
        "sequence_no": 7,
        "factor_label": "민간 주도 벤처투자(TIPS) 확산",
        "content_summary": "민간 주도 투자와 팁스 확산으로 기술창업·스케일업 지원",
    },
    {
        "sequence_no": 8,
        "factor_label": "규제 샌드박스 및 실증 특례 확대",
        "content_summary": "신기술 도입의 시장 진입을 위한 실증·특례 지원 확대",
    },
    {
        "sequence_no": 9,
        "factor_label": "연구개발 평가제도 혁신(등급 폐지)",
        "content_summary": "실패를 걱정하지 않는 도전형 연구평가 체계 전환",
    },
    {
        "sequence_no": 10,
        "factor_label": "과학기술 국제협력 및 글로벌 허브 구축",
        "content_summary": "해외 우수 기관과의 공동 연구 및 글로벌 오픈이노베이션 확대",
    },
    {
        "sequence_no": 11,
        "factor_label": "전략기술 세제 혜택 및 금융 지원 확대",
        "content_summary": "전략기술 분야의 투자·금융·세제 지원 확대",
    },
    {
        "sequence_no": 12,
        "factor_label": "기술사업화 및 기술이전 선순환 체계",
        "content_summary": "R&D 성과가 시장으로 이어지도록 기술료 및 지분 분배 제도 개선",
    },
    {
        "sequence_no": 13,
        "factor_label": "지역 주도 혁신 클러스터 및 특구 조성",
        "content_summary": "기회발전특구 등 전략 거점을 육성해 지역 혁신성과 확산",
    },
    {
        "sequence_no": 14,
        "factor_label": "국가 전략기술 보호 및 연구보안 강화",
        "content_summary": "핵심 기술 유출 방지를 위한 연구보안 체계와 거버넌스 확립",
    },
    {
        "sequence_no": 15,
        "factor_label": "IRIS 통합 연구지원 시스템 고도화",
        "content_summary": "범부처 디지털 플랫폼 고도화로 연구행정 부담 경감",
    },
]


INFRA_ROW_LEVEL_NOTES = {
    "1": "우측 보드 문구가 손상돼 DOC-POL-004, DOC-POL-012의 GPU 공통 인프라 문장을 기준으로 summary를 정규화했다.",
    "2": "우측 보드 문구가 손상돼 DOC-POL-005의 예타 폐지·사전점검 문장을 기준으로 summary를 정규화했다.",
    "3": "중앙 보드 라벨 OCR이 누락돼 DOC-POL-005, DOC-POL-009의 대학 블록펀딩 문장을 기준으로 factor_label을 보강했다.",
    "4": "우측 보드 문구가 손상돼 DOC-POL-012의 전주기 원스톱 지원 취지를 반영해 summary를 정규화했다.",
    "8": "우측 보드 문구 일부만 읽혀 시장 진입 실증 지원 취지로 summary를 정규화했다.",
    "9": "우측 보드 문구 일부만 읽혀 도전형 평가 전환 취지로 summary를 정규화했다.",
    "11": "우측 보드 문구가 흐려 라벨 중심의 concise summary로 정규화했다.",
    "15": "우측 보드에는 '범부처 디지털 플랫폼 고도화'만 가독 가능해 연구행정 부담 경감 취지로 summary를 정규화했다.",
}


TALENT_POLICY_ROWS = [
    {
        "sequence_no": 1,
        "factor_label": "AI·소프트웨어 전문인력 양성",
        "content_summary": "AI 대학원 등을 중심으로 전주기 성장 지원 체계 구축",
    },
    {
        "sequence_no": 2,
        "factor_label": "석·박사급 고급 연구인재 사다리 구축",
        "content_summary": "고급 연구인재의 전주기 성장 지원 체계 구축",
    },
    {
        "sequence_no": 3,
        "factor_label": "글로벌 우수 연구자 유치 및 정주 지원",
        "content_summary": "해외 우수 연구자에게 파격적 정주 지원 제공",
    },
    {
        "sequence_no": 4,
        "factor_label": "Staff Scientist 및 전임연구원 제도",
        "content_summary": "전문 전임연구 인력을 통해 연구 몰입 환경 조성",
    },
    {
        "sequence_no": 5,
        "factor_label": "신진연구자(Post-Doc) 정착 지원",
        "content_summary": "신진 연구자에게 안정적 법적 지위와 정착 기반 제공",
    },
    {
        "sequence_no": 6,
        "factor_label": "과학기술 영재학교 및 조기 인재 발굴",
        "content_summary": "과학영재 특화를 통한 조기 육성",
    },
    {
        "sequence_no": 7,
        "factor_label": "여성 및 은퇴 과학기술인 경력 활용",
        "content_summary": "경력보유 과학기술인의 경험 전수 지원",
    },
    {
        "sequence_no": 8,
        "factor_label": "도메인 지식+AI 융합 양손잡이 인재",
        "content_summary": "전공 지식과 AI를 겸비한 실전형 융합 전문가 육성",
    },
    {
        "sequence_no": 9,
        "factor_label": "의사과학자(MD-Ph.D.) 양성",
        "content_summary": "바이오 중심의 의사·과학 융합형 전문인력 양성",
    },
    {
        "sequence_no": 10,
        "factor_label": "산업 밀착형 계약학과 및 실무 인력",
        "content_summary": "산업 수요 기반 커리큘럼으로 즉시 투입 가능한 인재 육성",
    },
    {
        "sequence_no": 11,
        "factor_label": "전문연구요원 우대 및 제도 개선",
        "content_summary": "AI 분야 우수 인재의 전문연구요원 우선 배정과 지속성 확보",
    },
    {
        "sequence_no": 12,
        "factor_label": "과학기술인 보상체계 및 성과급 확대",
        "content_summary": "성과에 걸맞은 파격적 보상으로 연구 의욕 고취",
    },
    {
        "sequence_no": 13,
        "factor_label": "재직자 AX 전환 교육 및 리스킬링",
        "content_summary": "숙련 노동자의 AI 도구 융합 역량을 높이는 전환 교육",
    },
    {
        "sequence_no": 14,
        "factor_label": "연구지원인력 전문화 및 행정 부담 경감",
        "content_summary": "기술직과 행정직의 잡무를 분리해 연구지원 체계 전문화",
    },
    {
        "sequence_no": 15,
        "factor_label": "글로벌 파트너십 기반 해외 연수 지원",
        "content_summary": "해외 유수 대학·연구소와의 공동 연수 및 파견 기회 확대",
    },
]


TALENT_ROW_LEVEL_NOTES = {
    "1": "우측 보드에는 'AI 대학원' 조각만 남아 있어 전주기 성장 지원 체계로 summary를 정규화했다.",
    "3": "중앙 보드 라벨 OCR이 누락돼 우측 보드의 '파격적 정주 지원' 문구를 기준으로 factor_label을 보강했다.",
    "4": "우측 보드 문구가 부분 훼손돼 '몰입 환경 조성' 키워드 기준으로 summary를 정규화했다.",
    "6": "우측 보드 문구가 부분 훼손돼 조기 육성 취지로 summary를 정규화했다.",
    "8": "DOC-POL-004의 '양손잡이 인재' 표현과 우측 보드의 '실전형 융합 전문가 육성' 문구를 함께 반영했다.",
    "9": "우측 보드 문구가 부분 훼손돼 바이오 중심 전문인력 양성 취지로 summary를 정규화했다.",
    "11": "중앙 보드 라벨 OCR이 부분 누락돼 DOC-POL-004의 전문연구요원 우선 배정 문장을 기준으로 factor_label과 summary를 보강했다.",
    "13": "우측 보드에는 '숙련 노동자 AI 도구 융'만 남아 있어 전환 교육·리스킬링 취지로 summary를 정규화했다.",
    "14": "우측 보드의 '기술직 행정직을 잡무 분리' 문구를 기반으로 summary를 정규화했다.",
}


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


def build_canonical_table_json(
    *,
    canonical_table_id: str,
    title: str,
    rows: list[dict],
    normalization_method: str,
    row_level_notes: dict[str, str],
) -> dict:
    fieldnames = list(rows[0].keys())
    return {
        "canonical_table_id": canonical_table_id,
        "document_id": "DOC-REF-002",
        "title": title,
        "columns": fieldnames,
        "table_shape": {"rows": len(rows), "cols": len(fieldnames)},
        "cell_matrix": [[row[field] for field in fieldnames] for row in rows],
        "records": rows,
        "provenance": {
            "source_candidate_ids": ["TBL-DOC-REF-002-OCR-001"],
            "normalization_method": normalization_method,
            "source_pages": [1],
            "source_asset_path": "work/02_structured-extraction/figures/assets/DOC-REF-002/page_001.png",
            "source_policy_documents": SOURCE_POLICY_DOCUMENTS,
            "row_level_notes": row_level_notes,
        },
    }


def build_canonical_table_metadata(
    *,
    canonical_table_id: str,
    title_hint: str,
    preferred_candidate_id: str,
    notes: str,
) -> dict[str, object]:
    return {
        "canonical_table_id": canonical_table_id,
        "document_id": "DOC-REF-002",
        "title_hint": title_hint,
        "page_start": 1,
        "page_end": 1,
        "preferred_candidate_source": "manual_normalized",
        "preferred_candidate_id": preferred_candidate_id,
        "canonical_status": "ready",
        "dashboard_ready": "yes",
        "source_review_item_ids": "",
        "notes": notes,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-root", required=True)
    args = parser.parse_args()

    out_root = Path(args.out_root)
    instances_dir = out_root / "work/04_ontology/instances"
    derived_dir = instances_dir / "derived_tables"

    table_specs = [
        {
            "table_id": "CTBL-DOC-REF-002-001",
            "basename": "CTBL-DOC-REF-002-001__strategy-reference",
            "title": "정책·기술분야별 재구성(안) - 기술 전략 reference",
            "rows": TECH_STRATEGY_ROWS,
            "normalization_method": "manual_visual_review_from_doc_ref_002_page_1_technology_band",
            "row_level_notes": TECH_ROW_LEVEL_NOTES,
            "notes": "DOC-REF-002 page 1 상단 기술 밴드를 시각 검토해 15개 전략 reference로 정규화한 표.",
        },
        {
            "table_id": "CTBL-DOC-REF-002-002",
            "basename": "CTBL-DOC-REF-002-002__infrastructure-reference",
            "title": "정책·기술분야별 재구성(안) - 인프라·제도 common factors",
            "rows": INFRA_POLICY_ROWS,
            "normalization_method": "manual_visual_review_from_doc_ref_002_page_1_infrastructure_band",
            "row_level_notes": INFRA_ROW_LEVEL_NOTES,
            "notes": "DOC-REF-002 page 1 중단 인프라·제도 밴드를 시각 검토해 15개 공통 요소 reference로 정규화한 표.",
        },
        {
            "table_id": "CTBL-DOC-REF-002-003",
            "basename": "CTBL-DOC-REF-002-003__talent-reference",
            "title": "정책·기술분야별 재구성(안) - 인재·제도 common factors",
            "rows": TALENT_POLICY_ROWS,
            "normalization_method": "manual_visual_review_from_doc_ref_002_page_1_talent_band",
            "row_level_notes": TALENT_ROW_LEVEL_NOTES,
            "notes": "DOC-REF-002 page 1 하단 인재·제도 밴드를 시각 검토해 15개 공통 요소 reference로 정규화한 표.",
        },
    ]

    metadata_rows: list[dict[str, object]] = []
    for spec in table_specs:
        canonical_json = build_canonical_table_json(
            canonical_table_id=spec["table_id"],
            title=spec["title"],
            rows=spec["rows"],
            normalization_method=spec["normalization_method"],
            row_level_notes=spec["row_level_notes"],
        )
        fieldnames = list(spec["rows"][0].keys())
        write_csv(
            derived_dir / f"{spec['basename']}.csv",
            spec["rows"],
            fieldnames,
        )
        write_json(
            derived_dir / f"{spec['basename']}.json",
            canonical_json,
        )
        metadata_rows.append(
            build_canonical_table_metadata(
                canonical_table_id=spec["table_id"],
                title_hint=spec["title"],
                preferred_candidate_id=spec["basename"],
                notes=spec["notes"],
            )
        )

    write_csv(
        instances_dir / "DOC-REF-002__canonical-tables.csv",
        metadata_rows,
        list(metadata_rows[0].keys()),
    )
    write_json(
        instances_dir / "DOC-REF-002__canonical-tables.json",
        metadata_rows,
    )

    print(f"Canonical tables written: {len(metadata_rows)}")


if __name__ == "__main__":
    main()
