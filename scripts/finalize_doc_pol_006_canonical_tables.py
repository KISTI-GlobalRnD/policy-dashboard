#!/usr/bin/env python3
"""Finalize the two unresolved canonical tables for DOC-POL-006.

This script materializes:
- a normalized support-history table for page 25
- a merged multi-page schedule table for pages 36-38

It also upgrades the related canonical table records from
`needs_normalization` / `needs_merge` to `ready`.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


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


def build_support_history_rows() -> list[dict]:
    columns = ["2016", "2017", "2018", "2019", "2020", "2021", "2022", "2023", "2024", "2025", "총"]
    values = {
        "예산": ["900", "1,400", "1,815", "2,265", "2,500", "3,300", "2,554", "2,554", "2,525", "2,550", "22,363"],
        "대상": ["2", "4", "6", "9", "9", "8", "8", "5", "7", "9", "67"],
    }
    rows: list[dict] = []
    for label, data in values.items():
        row = {"구분": label}
        row.update(dict(zip(columns, data, strict=True)))
        rows.append(row)
    return rows


def build_schedule_rows() -> list[dict]:
    grouped_rows = {
        "25년 12월": [
            "[초전도체] 고온초전도자석 실용화 기술개발 성과 목표 마련",
            "[글로벌 상업화 지원] 펀드 및 글로벌 진출 지원 ’26년 예산 확정",
            "[K-디지털헬스케어] 민-관 합동 얼라이언스 구성 및 추진단 2차 회의",
            "[K-콘텐츠] 문화산업보증계정 운용계획 확정",
            "[K-콘텐츠] 신규 해외거점 5개소 설립",
            "[K-콘텐츠] ｢영화비디오법｣ 일부개정안 발의",
        ],
        "26년 상반기": [
            "[초전도체] 고온초전도자석 원천기술 검증",
            "[초전도체] 초전도 도체 시험설비 실험동 건설",
            "[글로벌 상업화 지원] K-바이오 백신 펀드 결성(5, 6호 각 5백억)",
            "[글로벌 상업화 지원] 임상3상 특화펀드 조성 협의(금융위, 국책은행)",
            "[글로벌 상업화 지원] K-바이오 백신 3호 펀드 결성 완료",
            "[글로벌 상업화 지원] 글로벌 진출, 수출 지원 프로그램 사업계획 수립 및 운영",
            "[K-디지털헬스케어] 추진단 3차·4차 회의",
            "[K-디지털헬스케어] 민-관 합동 얼라이언스를 통한 정책 패키지 과제화 도출",
            "[K-디지털헬스케어] 해외 규제, 인허가 등 컨설팅 지원, 성공사례 정보 공유",
            "[K-콘텐츠] AI 콘텐츠 제작지원 사업 공고",
            "[K-콘텐츠] 국제공동제작 영화 지원사업 공고",
            "[K-콘텐츠] AI 영화 제작 실습 워크숍 실시",
            "[K-콘텐츠] 영화 ODA 글로벌 파트너십 구축 관련 사전타당성 연구",
        ],
        "26년 하반기": [
            "[K-콘텐츠] 웹툰 제작비 세액공제 신규 추진",
            "[K-콘텐츠] AI 융합 OTT 글로벌 진출 확산 지원 사업 공고",
            "[초전도체] 고온초전도자석 실용화기술개발 착수",
            "[초전도체] 초전도 도체 시험용 프로토타입 자석 제작",
            "[초전도체] 국제공동연구를 통한 핵융합로용 자석 선재 개발",
            "[글로벌 상업화 지원] 글로벌 오픈이노베이션 워크숍(11월)",
            "[글로벌 상업화 지원] 임상3상 특화펀드 운용사 선정 공고",
            "[글로벌 상업화 지원] 임상3상 특화펀드 결성(15백억)",
            "[K-디지털헬스케어] 추진단 5차·6차 회의",
            "[K-디지털헬스케어] 디지털헬스 의료기기 수출모델 구축사업 구체화",
            "[K-콘텐츠] 콘텐츠 미래전략펀드 조성 완료",
            "[K-콘텐츠] 해외거점 전체 운영성과평가",
            "[K-콘텐츠] 게임콘텐츠 제작비용 세액공제 관련 「조세특례제한법」 개정",
            "[K-콘텐츠] AI 융합 OTT 글로벌 진출 확산 지원 사업 K-채널(3개) 송출",
        ],
        "27년": [
            "[초전도체] 고성능 고온초전도 솔레노이드자석 설계 및 제작 기술개발",
            "[초전도체] 초전도자석 헬륨냉동기 구축",
            "[초전도체] 초전도 도체 시험용 초전도자석 제작",
            "[글로벌 상업화 지원] K-바이오 백신 펀드 1조원 조성",
            "[글로벌 상업화 지원] 글로벌 진출 및 수출 지원 프로그램 운영(계속)",
            "[K-콘텐츠] 게임콘텐츠 제작비 세액공제 시행",
            "[K-콘텐츠] 해외 기업지원센터 1개소 신설",
        ],
        "28년": [
            "[초전도체] 고온초전도자석 공정 통합·반자동화와 실규모 성능·신뢰성 검증",
            "[초전도체] 초전도 도체 시험설비 구축 및 종합시운전",
            "[글로벌 상업화 지원] 글로벌 진출 및 수출 지원 프로그램 운영(계속)",
            "[글로벌 상업화 지원] 제4차 제약바이오산업 육성·지원 종합계획(’28~’32)",
            "[글로벌 상업화 지원] 제2차 바이오헬스 인재양성방안(’28~’32)",
            "[K-디지털헬스케어] 해외 허브·국내 생태계(기업·의료기관 등) 통합 플랫폼 구축 및 운영",
        ],
        "29년": [
            "[초전도체] 고온초전도자석 제작 및 운용의 표준화",
            "[글로벌 상업화 지원] 글로벌 진출 및 수출 지원 프로그램 운영(계속)",
        ],
        "30년": [
            "[초전도체] 응용분야별 고온초전도자석 프로토타입 제작",
            "[글로벌 상업화 지원] 글로벌 진출 및 수출 지원 프로그램 운영(계속)",
            "[K-디지털헬스케어] 새로운 한국 의료 수출 성공모델 확보·확산",
        ],
    }

    rows: list[dict] = []
    sequence_no = 0
    for period, items in grouped_rows.items():
        for item in items:
            sequence_no += 1
            rows.append(
                {
                    "sequence_no": sequence_no,
                    "시기": period,
                    "세부 일정": item,
                }
            )
    return rows


def build_support_history_json(rows: list[dict]) -> dict:
    fieldnames = list(rows[0].keys())
    return {
        "canonical_table_id": "CTBL-DOC-POL-006-006",
        "document_id": "DOC-POL-006",
        "title": "ICT 기반 해외진출 지원사업 지원 현황",
        "columns": fieldnames,
        "table_shape": {"rows": len(rows), "cols": len(fieldnames)},
        "cell_matrix": [[row[field] for field in fieldnames] for row in rows],
        "records": rows,
        "provenance": {
            "source_candidate_ids": ["TBL-DOC-POL-006-TBLTMP-015", "PAR-DOC-POL-006-00343"],
            "source_review_item_ids": ["TRV-DOC-POL-006-MD-007", "TRV-DOC-POL-006-JS-015"],
            "normalization_method": "manual_visual_review_from_pdf_page_25",
            "source_pages": [25],
        },
    }


def build_schedule_json(rows: list[dict]) -> dict:
    fieldnames = list(rows[0].keys())
    return {
        "canonical_table_id": "CTBL-DOC-POL-006-007",
        "document_id": "DOC-POL-006",
        "title": "초혁신경제 15대 프로젝트 세부 일정",
        "columns": fieldnames,
        "table_shape": {"rows": len(rows), "cols": len(fieldnames)},
        "cell_matrix": [[str(row[field]) for field in fieldnames] for row in rows],
        "records": rows,
        "provenance": {
            "source_candidate_ids": [
                "TBL-DOC-POL-006-TBLTMP-018",
                "TBL-DOC-POL-006-TBLTMP-019",
                "TBL-DOC-POL-006-TBLTMP-020",
                "PAR-DOC-POL-006-00493",
                "PAR-DOC-POL-006-00495",
                "PAR-DOC-POL-006-00496",
            ],
            "source_review_item_ids": [
                "TRV-DOC-POL-006-MD-008",
                "TRV-DOC-POL-006-JS-018",
                "TRV-DOC-POL-006-MD-009",
                "TRV-DOC-POL-006-JS-019",
                "TRV-DOC-POL-006-MD-010",
                "TRV-DOC-POL-006-JS-020",
            ],
            "merge_method": "manual_visual_review_from_pdf_pages_36_38",
            "source_pages": [36, 37, 38],
        },
    }


def update_review_decisions(decision_path: Path) -> None:
    payload = json.loads(decision_path.read_text(encoding="utf-8"))
    review_updates = payload.get("review_item_updates", {})
    for review_item_id in ["TRV-DOC-POL-006-MD-007", "TRV-DOC-POL-006-JS-015"]:
        review_updates[review_item_id] = {
            "keep_for_dashboard": "yes",
            "review_status": "reviewed",
            "canonical_table_id": "CTBL-DOC-POL-006-006",
            "reviewer_notes": "PDF 원본 page 25 시각 검토 후 연도/수치 셀을 정규화한 canonical table로 승격.",
        }
    for review_item_id in [
        "TRV-DOC-POL-006-MD-008",
        "TRV-DOC-POL-006-JS-018",
        "TRV-DOC-POL-006-MD-009",
        "TRV-DOC-POL-006-JS-019",
        "TRV-DOC-POL-006-MD-010",
        "TRV-DOC-POL-006-JS-020",
    ]:
        review_updates[review_item_id] = {
            "keep_for_dashboard": "yes",
            "review_status": "reviewed",
            "canonical_table_id": "CTBL-DOC-POL-006-007",
            "reviewer_notes": "PDF 원본 pages 36-38 시각 검토 후 다중 페이지 일정표를 병합한 canonical table로 승격.",
        }

    updated_canonical_tables = []
    for table in payload.get("canonical_tables", []):
        if table["canonical_table_id"] == "CTBL-DOC-POL-006-006":
            table = {
                **table,
                "title_hint": "ICT 기반 해외진출 지원사업 지원 현황",
                "preferred_candidate_source": "manual_normalized",
                "preferred_candidate_id": "CTBL-DOC-POL-006-006__normalized",
                "canonical_status": "ready",
                "dashboard_ready": "yes",
                "notes": "PDF 원본 page 25 시각 검토를 바탕으로 연도/수치 셀을 정규화한 표.",
            }
        if table["canonical_table_id"] == "CTBL-DOC-POL-006-007":
            table = {
                **table,
                "title_hint": "초혁신경제 15대 프로젝트 세부 일정",
                "preferred_candidate_source": "manual_merged",
                "preferred_candidate_id": "CTBL-DOC-POL-006-007__merged",
                "canonical_status": "ready",
                "dashboard_ready": "yes",
                "notes": "PDF 원본 pages 36-38 시각 검토를 바탕으로 다중 페이지 일정표를 병합한 표.",
            }
        updated_canonical_tables.append(table)

    payload["review_item_updates"] = review_updates
    payload["canonical_tables"] = updated_canonical_tables
    write_json(decision_path, payload)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-root", required=True)
    args = parser.parse_args()

    out_root = Path(args.out_root)
    derived_dir = out_root / "work/04_ontology/instances/derived_tables"
    qa_dir = out_root / "qa/extraction"

    support_rows = build_support_history_rows()
    support_json = build_support_history_json(support_rows)
    schedule_rows = build_schedule_rows()
    schedule_json = build_schedule_json(schedule_rows)

    write_csv(
        derived_dir / "CTBL-DOC-POL-006-006__normalized.csv",
        support_rows,
        list(support_rows[0].keys()),
    )
    write_json(derived_dir / "CTBL-DOC-POL-006-006__normalized.json", support_json)

    write_csv(
        derived_dir / "CTBL-DOC-POL-006-007__merged.csv",
        schedule_rows,
        list(schedule_rows[0].keys()),
    )
    write_json(derived_dir / "CTBL-DOC-POL-006-007__merged.json", schedule_json)

    decision_path = qa_dir / "review_decisions" / "DOC-POL-006__table-review-decisions.json"
    update_review_decisions(decision_path)


if __name__ == "__main__":
    main()
