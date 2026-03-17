#!/usr/bin/env python3
"""Build the 15-strategy seed CSV and optionally load it into SQLite."""

from __future__ import annotations

import argparse
import csv
import sqlite3
from pathlib import Path


DOC_REF_002_SOURCE_BASIS = "DOC-REF-002; CTBL-DOC-REF-002-001"
STR_010_SOURCE_BASIS = "DOC-POL-006; POL-012 reviewed healthcare cluster; STX-STR-010-001"


STRATEGIES = [
    {
        "strategy_id": "STR-001",
        "strategy_label": "AI G3 도약 및 전 산업 AX 확산",
        "strategy_description": "독자 AI 모델, 공공·산업 AX, AI 컴퓨팅과 데이터 인프라 확산 전략.",
        "source_basis": DOC_REF_002_SOURCE_BASIS,
        "display_order": 1,
        "is_active": 1,
    },
    {
        "strategy_id": "STR-002",
        "strategy_label": "초격차 전략기술 확보 (반도체·이차전지)",
        "strategy_description": "AI반도체, 첨단 패키징, 차세대 반도체와 이차전지 등 초격차 전략기술 확보 전략.",
        "source_basis": DOC_REF_002_SOURCE_BASIS,
        "display_order": 2,
        "is_active": 1,
    },
    {
        "strategy_id": "STR-003",
        "strategy_label": "바이오·헬스 글로벌 중심국가 도약",
        "strategy_description": "AI 바이오, 신약 개발, 바이오 제조, 글로벌 상업화를 포함하는 바이오·헬스 전략.",
        "source_basis": DOC_REF_002_SOURCE_BASIS,
        "display_order": 3,
        "is_active": 1,
    },
    {
        "strategy_id": "STR-004",
        "strategy_label": "차세대 네트워크(6G) 및 지능형 인프라",
        "strategy_description": "6G, AI 네트워크, 오픈랜, 국가 AI 고속도로와 지능형 네트워크 인프라 전략.",
        "source_basis": DOC_REF_002_SOURCE_BASIS,
        "display_order": 4,
        "is_active": 1,
    },
    {
        "strategy_id": "STR-005",
        "strategy_label": "우주항공 및 해양 기술주권 확보",
        "strategy_description": "초고해상도 위성, 우주항공, 자율운항선박과 해양 분야 기술주권 전략.",
        "source_basis": DOC_REF_002_SOURCE_BASIS,
        "display_order": 5,
        "is_active": 1,
    },
    {
        "strategy_id": "STR-006",
        "strategy_label": "탄소중립 및 에너지 안보 (수소·SMR)",
        "strategy_description": "그린수소, SMR, 해상풍력, HVDC, 태양광, 전력망을 포함하는 에너지 전환 전략.",
        "source_basis": DOC_REF_002_SOURCE_BASIS,
        "display_order": 6,
        "is_active": 1,
    },
    {
        "strategy_id": "STR-007",
        "strategy_label": "양자 정보통신 및 미래소재 선점",
        "strategy_description": "양자 정보통신, 그래핀, 초전도, 차세대 소재 선점 전략.",
        "source_basis": DOC_REF_002_SOURCE_BASIS,
        "display_order": 7,
        "is_active": 1,
    },
    {
        "strategy_id": "STR-008",
        "strategy_label": "피지컬 AI 및 지능형 로봇 산업 육성",
        "strategy_description": "피지컬 AI, 온디바이스 AI, 휴머노이드, 산업·서비스 로봇 생태계 육성 전략.",
        "source_basis": DOC_REF_002_SOURCE_BASIS,
        "display_order": 8,
        "is_active": 1,
    },
    {
        "strategy_id": "STR-009",
        "strategy_label": "미래 모빌리티(자율주행·UAM)",
        "strategy_description": "자율주행, SDV, 차량용 반도체, UAM 등 미래 모빌리티 전환 전략.",
        "source_basis": DOC_REF_002_SOURCE_BASIS,
        "display_order": 9,
        "is_active": 1,
    },
    {
        "strategy_id": "STR-010",
        "strategy_label": "디지털 헬스케어 서비스 혁신",
        "strategy_description": "K-디지털헬스케어, 의료 AI·의료기기, 비대면 진료, 해외 실증·인허가 지원을 묶는 working 전략 라벨.",
        "source_basis": STR_010_SOURCE_BASIS,
        "display_order": 10,
        "is_active": 1,
    },
    {
        "strategy_id": "STR-011",
        "strategy_label": "디지털 콘텐츠 및 K-컬처 혁신",
        "strategy_description": "AI 콘텐츠 제작, 게임·웹툰·영상·음악 등 K-콘텐츠 글로벌 경쟁력 강화 전략.",
        "source_basis": DOC_REF_002_SOURCE_BASIS,
        "display_order": 11,
        "is_active": 1,
    },
    {
        "strategy_id": "STR-012",
        "strategy_label": "스마트 농업 및 수산업 기술",
        "strategy_description": "스마트농업, 스마트양식, 정밀 데이터 기반 농수산 기술과 식량안보 대응 전략.",
        "source_basis": DOC_REF_002_SOURCE_BASIS,
        "display_order": 12,
        "is_active": 1,
    },
    {
        "strategy_id": "STR-013",
        "strategy_label": "디지털 트윈 및 가상화 공정 혁신",
        "strategy_description": "제조AX, AI 팩토리, 공정 혁신, 디지털 트윈과 가상화 기반 산업 혁신 전략.",
        "source_basis": DOC_REF_002_SOURCE_BASIS,
        "display_order": 13,
        "is_active": 1,
    },
    {
        "strategy_id": "STR-014",
        "strategy_label": "핵심 전략기술 자립 (LNG화물창·특수강)",
        "strategy_description": "LNG 화물창, 특수탄소강 등 제조·소재 분야 전략기술 자립화 전략.",
        "source_basis": DOC_REF_002_SOURCE_BASIS,
        "display_order": 14,
        "is_active": 1,
    },
    {
        "strategy_id": "STR-015",
        "strategy_label": "감염병 대응 및 공중보건 기술 자립",
        "strategy_description": "백신, mRNA, 감염병 대응, 공중보건 기술 자립과 보건안보 강화 전략.",
        "source_basis": DOC_REF_002_SOURCE_BASIS,
        "display_order": 15,
        "is_active": 1,
    },
]


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--db-path")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    fieldnames = [
        "strategy_id",
        "strategy_label",
        "strategy_description",
        "source_basis",
        "display_order",
        "is_active",
    ]
    write_csv(out_dir / "strategies_seed.csv", STRATEGIES, fieldnames)

    if args.db_path:
        connection = sqlite3.connect(args.db_path)
        try:
            connection.executemany(
                """
                INSERT OR REPLACE INTO strategies (
                    strategy_id,
                    strategy_label,
                    strategy_description,
                    source_basis,
                    display_order,
                    is_active
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        row["strategy_id"],
                        row["strategy_label"],
                        row["strategy_description"],
                        row["source_basis"],
                        row["display_order"],
                        row["is_active"],
                    )
                    for row in STRATEGIES
                ],
            )
            connection.commit()
        finally:
            connection.close()

    print(f"Strategies: {len(STRATEGIES)}")


if __name__ == "__main__":
    main()
