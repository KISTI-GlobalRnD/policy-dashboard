#!/usr/bin/env python3
"""Finalize explicit manual decisions for strategy alignment exception drafts."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


REVIEWER_NAME = "codex_manual_exception_review"


FINAL_DECISIONS = {
    "SRD-POL-012-3207f0439153": {
        "decision_status": "reviewed",
        "reviewed_primary_strategy_id": "STR-010",
        "reviewed_secondary_strategy_ids": "",
        "reviewed_confidence": "high",
        "reviewer_notes": "STX-STR-010-001 keep_primary: K-디지털헬스 수출전략 패키지로 직접 읽힌다.",
    },
    "SRD-POL-012-48dd2f85b8a3": {
        "decision_status": "reviewed",
        "reviewed_primary_strategy_id": "STR-010",
        "reviewed_secondary_strategy_ids": "",
        "reviewed_confidence": "medium",
        "reviewer_notes": "STX-STR-010-001 keep_primary: 의료 AI·의료기기 해외수요 확대라는 시장 맥락이 STR-010과 직접 연결된다.",
    },
    "SRD-POL-012-dab70a92dcb0": {
        "decision_status": "no_strategy",
        "reviewed_primary_strategy_id": "",
        "reviewed_secondary_strategy_ids": "",
        "reviewed_confidence": "high",
        "reviewer_notes": "STX-STR-010-001 no_strategy: K-콘텐츠·초전도체·글로벌상업화 일정이 섞인 composite schedule row다.",
    },
    "SRD-POL-012-7fcbb7391bfd": {
        "decision_status": "reviewed",
        "reviewed_primary_strategy_id": "STR-010",
        "reviewed_secondary_strategy_ids": "",
        "reviewed_confidence": "medium",
        "reviewer_notes": "STX-STR-010-001 keep_primary: 디지털헬스 해외진출 수요의 배경 설명으로 STR-010 cluster에 남긴다.",
    },
    "SRD-POL-012-bc0be1062e6c": {
        "decision_status": "no_strategy",
        "reviewed_primary_strategy_id": "",
        "reviewed_secondary_strategy_ids": "",
        "reviewed_confidence": "high",
        "reviewer_notes": "STX-STR-010-001 no_strategy: 여러 프로젝트 세부 일정이 결합된 composite reference row다.",
    },
    "SRD-POL-012-05b69825f4ec": {
        "decision_status": "reviewed",
        "reviewed_primary_strategy_id": "STR-010",
        "reviewed_secondary_strategy_ids": "STR-001 | STR-003",
        "reviewed_confidence": "medium",
        "reviewer_notes": "STX-STR-010-001 reviewed_with_split_flag: 해외진출 맥락은 STR-010이 맞지만 AI 의료기기 데이터 확보 이슈가 강해 split candidate로 남긴다.",
    },
    "SRD-POL-012-2b1b525c44f9": {
        "decision_status": "reviewed",
        "reviewed_primary_strategy_id": "STR-010",
        "reviewed_secondary_strategy_ids": "",
        "reviewed_confidence": "medium",
        "reviewer_notes": "STX-STR-010-001 keep_primary: 해외 의료기기 인허가·임상·실증 지원 애로는 STR-010 service/export cluster의 직접 근거다.",
    },
    "SRD-POL-012-0108242d7117": {
        "decision_status": "reviewed",
        "reviewed_primary_strategy_id": "STR-010",
        "reviewed_secondary_strategy_ids": "",
        "reviewed_confidence": "high",
        "reviewer_notes": "STX-STR-010-001 keep_primary: 해외진출 규제·애로 해결 정책지원은 STR-010 institutional support로 본다.",
    },
    "SRD-POL-012-0d300765cab2": {
        "decision_status": "reviewed",
        "reviewed_primary_strategy_id": "STR-010",
        "reviewed_secondary_strategy_ids": "",
        "reviewed_confidence": "high",
        "reviewer_notes": "STX-STR-010-001 keep_primary: K-디지털헬스 쇼케이스·홍보 지원은 service/export cluster의 직접 action이다.",
    },
    "SRD-POL-012-5197d55420de": {
        "decision_status": "reviewed",
        "reviewed_primary_strategy_id": "STR-010",
        "reviewed_secondary_strategy_ids": "",
        "reviewed_confidence": "high",
        "reviewer_notes": "STX-STR-010-001 keep_primary: 해외거점 확보 추진단 구성은 STR-010 거버넌스/거점 구축 action이다.",
    },
    "SRD-POL-012-5f649775733f": {
        "decision_status": "reviewed",
        "reviewed_primary_strategy_id": "STR-010",
        "reviewed_secondary_strategy_ids": "",
        "reviewed_confidence": "medium",
        "reviewer_notes": "STX-STR-010-001 keep_primary: 해외 현지 데이터 접근과 물리적 공간 애로는 디지털헬스 해외진출 인프라 문제다.",
    },
    "SRD-POL-012-9129da9bf238": {
        "decision_status": "reviewed",
        "reviewed_primary_strategy_id": "STR-010",
        "reviewed_secondary_strategy_ids": "",
        "reviewed_confidence": "medium",
        "reviewer_notes": "STX-STR-010-001 keep_primary: 사업화 실증 지원 수요는 STR-010 수출·실증 지원 cluster와 직접 연결된다.",
    },
    "SRD-POL-012-b40fee4789e1": {
        "decision_status": "reviewed",
        "reviewed_primary_strategy_id": "STR-010",
        "reviewed_secondary_strategy_ids": "STR-003",
        "reviewed_confidence": "medium",
        "reviewer_notes": "STX-STR-010-001 reviewed_with_split_flag: 디지털헬스 데이터 구축은 STR-010에 두되 바이오·헬스 R&D 성격이 강해 split candidate로 남긴다.",
    },
    "SRD-POL-012-e6fe05dd5d8b": {
        "decision_status": "reviewed",
        "reviewed_primary_strategy_id": "STR-010",
        "reviewed_secondary_strategy_ids": "STR-001 | STR-003",
        "reviewed_confidence": "medium",
        "reviewer_notes": "STX-STR-010-001 reviewed_with_split_flag: 빅데이터 기반 디지털의료기기 R&D는 STR-010에 두되 AI/바이오 축 보조 매핑과 split candidate 메모를 남긴다.",
    },
    "SRD-POL-012-edf0789d256e": {
        "decision_status": "reviewed",
        "reviewed_primary_strategy_id": "STR-010",
        "reviewed_secondary_strategy_ids": "",
        "reviewed_confidence": "high",
        "reviewer_notes": "STX-STR-010-001 keep_primary: Medical Korea 브랜드 확산은 STR-010 홍보·시장안착 action이다.",
    },
    "SRD-POL-012-17cbdfb5de05": {
        "decision_status": "reviewed",
        "reviewed_primary_strategy_id": "STR-010",
        "reviewed_secondary_strategy_ids": "",
        "reviewed_confidence": "high",
        "reviewer_notes": "STX-STR-010-001 keep_primary: 디지털헬스 제도개선·인프라 확충 서술은 STR-010 인프라·제도 cluster에 해당한다.",
    },
    "SRD-POL-012-27ab71ee96c3": {
        "decision_status": "reviewed",
        "reviewed_primary_strategy_id": "STR-010",
        "reviewed_secondary_strategy_ids": "",
        "reviewed_confidence": "high",
        "reviewer_notes": "STX-STR-010-001 keep_primary: ICT 의료시스템 수출 지원 연차 목표는 STR-010 로드맵 action이다.",
    },
    "SRD-POL-002-7e20c0b580df": {
        "decision_status": "reviewed",
        "reviewed_primary_strategy_id": "STR-010",
        "reviewed_secondary_strategy_ids": "",
        "reviewed_confidence": "high",
        "reviewer_notes": "STX-STR-010-001 keep_primary: 디지털헬스케어법은 STR-010의 제도 기반을 직접 형성한다.",
    },
    "SRD-POL-012-6f87aec3eac5": {
        "decision_status": "reviewed",
        "reviewed_primary_strategy_id": "STR-010",
        "reviewed_secondary_strategy_ids": "",
        "reviewed_confidence": "high",
        "reviewer_notes": "STX-STR-010-001 keep_primary: 원격협진에서 비대면진료 제도화로의 regulatory delta는 STR-010의 핵심 제도 action이다.",
    },
    "SRD-POL-012-bd818983dc30": {
        "decision_status": "reviewed",
        "reviewed_primary_strategy_id": "STR-010",
        "reviewed_secondary_strategy_ids": "",
        "reviewed_confidence": "high",
        "reviewer_notes": "STX-STR-010-001 keep_primary: 비대면진료 통합플랫폼 구축은 STR-010의 직접 실행과제다.",
    },
    "SRD-POL-001-b7c6c2f050b4": {
        "decision_status": "reviewed",
        "reviewed_primary_strategy_id": "STR-010",
        "reviewed_secondary_strategy_ids": "",
        "reviewed_confidence": "high",
        "reviewer_notes": "STX-STR-010-001 keep_primary: 어촌 의료취약지 비대면진료·원격협진 체계 신설은 STR-010의 직접 서비스 확산 과제다.",
    },
    "SRD-POL-001-22f71491bfe3": {
        "decision_status": "no_strategy",
        "reviewed_primary_strategy_id": "",
        "reviewed_secondary_strategy_ids": "",
        "reviewed_confidence": "high",
        "reviewer_notes": "STX-STR-010-001 no_strategy: 소상공인 디지털 경쟁력·상권 육성은 범용 민생/디지털 전환 과제로 STR-010에 두기 어렵다.",
    },
    "SRD-POL-001-2a3f69fff2e3": {
        "decision_status": "no_strategy",
        "reviewed_primary_strategy_id": "",
        "reviewed_secondary_strategy_ids": "",
        "reviewed_confidence": "high",
        "reviewer_notes": "STX-STR-010-001 no_strategy: 디지털 역기능 대응과 이용자 안전 환경 조성은 범용 디지털 안전·규율 과제다.",
    },
    "SRD-POL-001-54fbacb46d29": {
        "decision_status": "no_strategy",
        "reviewed_primary_strategy_id": "",
        "reviewed_secondary_strategy_ids": "",
        "reviewed_confidence": "high",
        "reviewer_notes": "STX-STR-010-001 no_strategy: 디지털 성범죄·교제폭력 대응은 사회안전/피해자 지원 과제로 STR-010과 직접 연결되지 않는다.",
    },
    "SRD-POL-001-57a82223169e": {
        "decision_status": "no_strategy",
        "reviewed_primary_strategy_id": "",
        "reviewed_secondary_strategy_ids": "",
        "reviewed_confidence": "high",
        "reviewer_notes": "STX-STR-010-001 no_strategy: 디지털 시민성·취약 청소년 지원은 청소년 정책 범주로 특정 전략기술 축에 귀속하기 어렵다.",
    },
    "SRD-POL-001-5ec39d2b02ff": {
        "decision_status": "no_strategy",
        "reviewed_primary_strategy_id": "",
        "reviewed_secondary_strategy_ids": "",
        "reviewed_confidence": "high",
        "reviewer_notes": "STX-STR-010-001 no_strategy: 신통상협정 확대는 외교·통상 총론으로 개별 전략기술 축 primary를 두기 어렵다.",
    },
    "SRD-POL-001-accdc13dc39e": {
        "decision_status": "no_strategy",
        "reviewed_primary_strategy_id": "",
        "reviewed_secondary_strategy_ids": "",
        "reviewed_confidence": "high",
        "reviewer_notes": "STX-STR-010-001 no_strategy: 정보주체 권리·딥페이크 삭제요구권은 개인정보·디지털 권리 규율 과제다.",
    },
    "SRD-POL-001-af92cd2c4d79": {
        "decision_status": "no_strategy",
        "reviewed_primary_strategy_id": "",
        "reviewed_secondary_strategy_ids": "",
        "reviewed_confidence": "high",
        "reviewer_notes": "STX-STR-010-001 no_strategy: 사이버보안 사각지대 지원은 중요하지만 현재 15대 전략 체계의 독립 축 밖이다.",
    },
    "SRD-POL-001-5735e9202368": {
        "decision_status": "no_strategy",
        "reviewed_primary_strategy_id": "",
        "reviewed_secondary_strategy_ids": "",
        "reviewed_confidence": "high",
        "reviewer_notes": "STX-STR-010-001 no_strategy: K-팝·디지털헬스·관광-뷰티가 섞인 복합 융합 row라 단일 primary 확정 위험이 크다.",
    },
    "SRD-POL-001-478f225fb7a9": {
        "decision_status": "reviewed",
        "reviewed_primary_strategy_id": "STR-010",
        "reviewed_secondary_strategy_ids": "",
        "reviewed_confidence": "high",
        "reviewer_notes": "STX-STR-010-001 keep_primary: 비대면진료 제도화는 STR-010의 직접 제도·서비스 확산 과제다.",
    },
    "SRD-POL-001-203c558c1073": {
        "decision_status": "no_strategy",
        "reviewed_primary_strategy_id": "",
        "reviewed_secondary_strategy_ids": "",
        "reviewed_confidence": "high",
        "reviewer_notes": "STX-STR-010-001 no_strategy: 디지털자산 상장·공시·영업규제는 금융디지털 규율 과제로 STR-010에 둘 수 없다.",
    },
    "SRD-POL-001-35935eac1406": {
        "decision_status": "no_strategy",
        "reviewed_primary_strategy_id": "",
        "reviewed_secondary_strategy_ids": "",
        "reviewed_confidence": "high",
        "reviewer_notes": "STX-STR-010-001 no_strategy: 디지털성범죄 대응 협력체계는 사회안전/피해구제 과제로 STR-010과 직접 연결되지 않는다.",
    },
    "SRD-POL-001-788b9c70f440": {
        "decision_status": "reviewed",
        "reviewed_primary_strategy_id": "STR-006",
        "reviewed_secondary_strategy_ids": "",
        "reviewed_confidence": "high",
        "reviewer_notes": "STX-STR-010-001 reassign_primary: 탄소배출 데이터플랫폼과 디지털제품여권 대응은 탄소중립 공급망 대응으로 STR-006이 타당하다.",
    },
    "SRD-POL-001-b1843c686758": {
        "decision_status": "no_strategy",
        "reviewed_primary_strategy_id": "",
        "reviewed_secondary_strategy_ids": "",
        "reviewed_confidence": "high",
        "reviewer_notes": "STX-STR-010-001 no_strategy: 디지털자산·블록체인 생태계 조성은 금융·산업 총론으로 현재 전략체계 밖이다.",
    },
    "SRD-POL-001-bcb12bc59597": {
        "decision_status": "no_strategy",
        "reviewed_primary_strategy_id": "",
        "reviewed_secondary_strategy_ids": "",
        "reviewed_confidence": "high",
        "reviewer_notes": "STX-STR-010-001 no_strategy: 통신비 경감은 보편 통신복지 과제로 6G·지능형 인프라 전략과는 결이 다르다.",
    },
    "SRD-POL-001-c0a4730849d5": {
        "decision_status": "reviewed",
        "reviewed_primary_strategy_id": "STR-011",
        "reviewed_secondary_strategy_ids": "",
        "reviewed_confidence": "medium",
        "reviewer_notes": "STX-STR-010-001 reassign_primary: 디지털·미디어 법제 정비와 미디어 미래성장동력 확보는 STR-011 콘텐츠/미디어 산업 진흥에 더 가깝다.",
    },
    "SRD-POL-001-c7d9b12d1800": {
        "decision_status": "no_strategy",
        "reviewed_primary_strategy_id": "",
        "reviewed_secondary_strategy_ids": "",
        "reviewed_confidence": "high",
        "reviewer_notes": "STX-STR-010-001 no_strategy: 불법정보 삭제·차단과 법제 개선은 범용 디지털 규율 과제다.",
    },
    "SRD-POL-001-ca534bc20f2a": {
        "decision_status": "no_strategy",
        "reviewed_primary_strategy_id": "",
        "reviewed_secondary_strategy_ids": "",
        "reviewed_confidence": "high",
        "reviewer_notes": "STX-STR-010-001 no_strategy: 디지털자산 현물 ETF 제도화는 금융규제 과제로 STR-010과 직접 연결되지 않는다.",
    },
    "SRD-POL-001-e95b676ce38b": {
        "decision_status": "reviewed",
        "reviewed_primary_strategy_id": "STR-010",
        "reviewed_secondary_strategy_ids": "STR-003",
        "reviewed_confidence": "medium",
        "reviewer_notes": "STX-STR-010-001 reviewed_with_split_flag: 의료데이터 상호연계와 디지털 기반 병원 연구플랫폼은 primary는 STR-010에 두되 바이오 연구 성격이 있어 STR-003 보조 매핑을 남긴다.",
    },
    "SRD-POL-001-f8114d652c9a": {
        "decision_status": "no_strategy",
        "reviewed_primary_strategy_id": "",
        "reviewed_secondary_strategy_ids": "",
        "reviewed_confidence": "high",
        "reviewer_notes": "STX-STR-010-001 no_strategy: 디지털자산 규율·현물 ETF·토큰증권 제도정비는 금융시장 제도 과제다.",
    },
    "SRD-POL-001-b11f4337f715": {
        "decision_status": "no_strategy",
        "reviewed_primary_strategy_id": "",
        "reviewed_secondary_strategy_ids": "",
        "reviewed_confidence": "high",
        "reviewer_notes": "STX-STR-010-001 no_strategy: 아동·청소년 온라인 안전 강화는 디지털 권익/보호 과제로 전략기술 축 아님.",
    },
    "SRD-POL-001-bb448dc4a9a5": {
        "decision_status": "no_strategy",
        "reviewed_primary_strategy_id": "",
        "reviewed_secondary_strategy_ids": "",
        "reviewed_confidence": "high",
        "reviewer_notes": "STX-STR-010-001 no_strategy: 학교 내 신종 디지털성범죄 예방은 교육·안전 정책으로 15대 전략 primary를 두기 어렵다.",
    },
}


OUTPUT_FIELDS = [
    "exception_id",
    "decision_key",
    "policy_item_id",
    "policy_id",
    "policy_name",
    "bucket_label",
    "item_label",
    "draft_resolution_category",
    "final_decision_status",
    "final_primary_strategy_id",
    "final_secondary_strategy_ids",
    "final_confidence",
    "reviewer_name",
    "reviewer_notes",
]


MASTER_DECISION_FIELDS = [
    "decision_key",
    "active_in_queue",
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
    "alignment_exception_ids",
    "alignment_exception_notes",
    "auto_seed_blocked",
    "decision_status",
    "reviewed_primary_strategy_id",
    "reviewed_secondary_strategy_ids",
    "reviewed_confidence",
    "reviewer_name",
    "reviewer_notes",
]


DECISION_EDIT_FIELDS = [
    "decision_status",
    "reviewed_primary_strategy_id",
    "reviewed_secondary_strategy_ids",
    "reviewed_confidence",
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


def finalize_rows(draft_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    output_rows: list[dict[str, str]] = []
    for row in draft_rows:
        decision_key = row["decision_key"]
        if decision_key not in FINAL_DECISIONS:
            raise KeyError(f"Missing final decision for {decision_key}")
        final = FINAL_DECISIONS[decision_key]
        output_rows.append(
            {
                "exception_id": row["exception_id"],
                "decision_key": decision_key,
                "policy_item_id": row["policy_item_id"],
                "policy_id": row["policy_id"],
                "policy_name": row["policy_name"],
                "bucket_label": row["bucket_label"],
                "item_label": row["item_label"],
                "draft_resolution_category": row["draft_resolution_category"],
                "final_decision_status": final["decision_status"],
                "final_primary_strategy_id": final["reviewed_primary_strategy_id"],
                "final_secondary_strategy_ids": final["reviewed_secondary_strategy_ids"],
                "final_confidence": final["reviewed_confidence"],
                "reviewer_name": REVIEWER_NAME,
                "reviewer_notes": final["reviewer_notes"],
            }
        )
    return output_rows


def apply_to_master(
    master_rows: list[dict[str, str]],
    final_rows: list[dict[str, str]],
    draft_rows: list[dict[str, str]],
) -> tuple[list[dict[str, str]], int, int]:
    final_by_key = {row["decision_key"]: row for row in final_rows}
    draft_by_key = {row["decision_key"]: row for row in draft_rows}
    master_by_key = {row.get("decision_key", ""): row for row in master_rows if row.get("decision_key")}
    updated_count = 0
    appended_count = 0
    for row in master_rows:
        final = final_by_key.get(row.get("decision_key", ""))
        if not final:
            continue
        next_values = {
            "tech_domains": draft_by_key[row["decision_key"]].get("tech_domains", ""),
            "suggested_primary_strategy_score": draft_by_key[row["decision_key"]].get("suggested_primary_strategy_score", ""),
            "alignment_exception_ids": final["exception_id"],
            "alignment_exception_notes": draft_by_key[row["decision_key"]].get("alignment_exception_notes", ""),
            "auto_seed_blocked": draft_by_key[row["decision_key"]].get("auto_seed_blocked", "yes"),
            "decision_status": final["final_decision_status"],
            "reviewed_primary_strategy_id": final["final_primary_strategy_id"],
            "reviewed_secondary_strategy_ids": final["final_secondary_strategy_ids"],
            "reviewed_confidence": final["final_confidence"],
            "reviewer_name": final["reviewer_name"],
            "reviewer_notes": final["reviewer_notes"],
        }
        changed = any((row.get(field, "") != value) for field, value in next_values.items())
        for field, value in next_values.items():
            row[field] = value
        if changed:
            updated_count += 1

    for decision_key, final in final_by_key.items():
        if decision_key in master_by_key:
            continue
        draft = draft_by_key[decision_key]
        master_rows.append(
            {
                "decision_key": decision_key,
                "active_in_queue": "no",
                "policy_item_id": draft["policy_item_id"],
                "policy_id": draft["policy_id"],
                "policy_name": draft["policy_name"],
                "bucket_label": draft["bucket_label"],
                "item_label": draft["item_label"],
                "primary_evidence_id": draft.get("primary_evidence_id", ""),
                "evidence_preview": draft.get("evidence_preview", ""),
                "tech_domains": draft.get("tech_domains", ""),
                "suggested_primary_strategy_id": draft.get("suggested_primary_strategy_id", ""),
                "suggested_primary_strategy_label": draft.get("suggested_primary_strategy_label", ""),
                "suggested_primary_strategy_score": draft.get("suggested_primary_strategy_score", ""),
                "alternate_strategy_ids": draft.get("alternate_strategy_ids", ""),
                "alternate_strategy_labels": draft.get("alternate_strategy_labels", ""),
                "alignment_exception_ids": final["exception_id"],
                "alignment_exception_notes": draft.get("alignment_exception_notes", ""),
                "auto_seed_blocked": draft.get("auto_seed_blocked", "yes"),
                "decision_status": final["final_decision_status"],
                "reviewed_primary_strategy_id": final["final_primary_strategy_id"],
                "reviewed_secondary_strategy_ids": final["final_secondary_strategy_ids"],
                "reviewed_confidence": final["final_confidence"],
                "reviewer_name": final["reviewer_name"],
                "reviewer_notes": final["reviewer_notes"],
            }
        )
        appended_count += 1
    return master_rows, updated_count, appended_count


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--draft-csv", required=True)
    parser.add_argument("--out-csv", required=True)
    parser.add_argument("--out-summary-json", required=True)
    parser.add_argument("--master-decision-csv")
    args = parser.parse_args()

    draft_rows = read_csv(Path(args.draft_csv))
    if len(draft_rows) != len(FINAL_DECISIONS):
        raise ValueError(
            f"Expected {len(FINAL_DECISIONS)} draft rows, found {len(draft_rows)}"
        )

    final_rows = finalize_rows(draft_rows)
    write_csv(Path(args.out_csv), final_rows, OUTPUT_FIELDS)

    summary = {
        "decision_count": len(final_rows),
        "status_counts": dict(Counter(row["final_decision_status"] for row in final_rows)),
        "confidence_counts": dict(Counter(row["final_confidence"] for row in final_rows)),
        "policy_counts": dict(
            Counter(f"{row['policy_id']} {row['policy_name']}" for row in final_rows)
        ),
    }

    if args.master_decision_csv:
        master_path = Path(args.master_decision_csv)
        existing_master_rows = read_csv(master_path)
        if existing_master_rows:
            fieldnames = list(existing_master_rows[0].keys())
            for field in MASTER_DECISION_FIELDS:
                if field not in fieldnames:
                    fieldnames.append(field)
        else:
            fieldnames = MASTER_DECISION_FIELDS
        updated_rows, updated_count, appended_count = apply_to_master(existing_master_rows, final_rows, draft_rows)
        write_csv(master_path, updated_rows, fieldnames)
        summary["master_decision_csv"] = str(master_path)
        summary["updated_master_rows"] = updated_count
        summary["appended_master_rows"] = appended_count

    write_json(Path(args.out_summary_json), summary)
    print(f"Finalized alignment manual decisions: {len(final_rows)}")


if __name__ == "__main__":
    main()
