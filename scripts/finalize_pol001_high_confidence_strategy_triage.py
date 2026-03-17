#!/usr/bin/env python3
"""Apply high-confidence manual strategy triage for POL-001 pending items."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path


REVIEWER_NAME = "codex_manual_pol001_high_confidence"


REVIEW_OVERRIDES = {
    "SRD-POL-001-fb119c3ac91e": {
        "decision_status": "reviewed",
        "reviewed_primary_strategy_id": "STR-005",
        "reviewed_secondary_strategy_ids": "",
        "reviewed_confidence": "high",
        "reviewer_notes": "기후감시위성(천리안5호) 개발·발사가 직접 적시되어 우주항공 기술주권 축으로 본다.",
    },
    "SRD-POL-001-1fb46ae11cea": {
        "decision_status": "reviewed",
        "reviewed_primary_strategy_id": "STR-002",
        "reviewed_secondary_strategy_ids": "",
        "reviewed_confidence": "high",
        "reviewer_notes": "차세대 배터리 기술개발과 배터리 삼각벨트 구축은 초격차 전략기술 확보 축의 직접 과제다.",
    },
    "SRD-POL-001-a5b1ef39bab1": {
        "decision_status": "reviewed",
        "reviewed_primary_strategy_id": "STR-012",
        "reviewed_secondary_strategy_ids": "",
        "reviewed_confidence": "high",
        "reviewer_notes": "스마트APC 확대는 스마트 농업·유통 기술 확산 과제로 STR-012에 직접 대응한다.",
    },
    "SRD-POL-001-1efa43c3fb24": {
        "decision_status": "reviewed",
        "reviewed_primary_strategy_id": "STR-001",
        "reviewed_secondary_strategy_ids": "",
        "reviewed_confidence": "high",
        "reviewer_notes": "이노베이션 아카데미 확대와 AX대학원 설립은 AI·AX 인재 기반 확충 과제로 STR-001에 직접 연결된다.",
    },
}


KEEP_PENDING_KEYS = {
    "SRD-POL-001-ab1c14a81c40",  # 국가해상수송력20% 확충
    "SRD-POL-001-436176f287ab",  # 기술혁신·생산기반확대
    "SRD-POL-001-5ac8d236b66a",  # 단기
    "SRD-POL-001-b658acfefab4",  # 민관협업전략기술육성
    "SRD-POL-001-8f7f69aff899",  # 북극항로선박·초격차디스플레이
    "SRD-POL-001-07b2894d6a17",  # 유무인복합체계고도화
    "SRD-POL-001-c339787f762d",  # 전략적국제협력강화
    "SRD-POL-001-21516e5f7e06",  # 전력시장혁신
    "SRD-POL-001-b4ae20fe8655",  # 특허정보연계R&D
    "SRD-POL-001-0b8be7b63563",  # 해운경쟁력제고
    "SRD-POL-001-0625b3b4d848",  # 거점항만조성
}


OUTPUT_FIELDS = [
    "decision_key",
    "policy_item_id",
    "policy_id",
    "policy_name",
    "bucket_label",
    "item_label",
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


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", "", (value or "").strip().lower())


def contains_any(text: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, text) for pattern in patterns)


def build_no_strategy_reason(row: dict[str, str]) -> str:
    text = normalize_text(" ".join([row.get("item_label", ""), row.get("evidence_preview", "")]))

    if contains_any(
        text,
        [
            r"경제안보",
            r"외교",
            r"공급망",
            r"동맹",
            r"수출통제",
            r"영사서비스",
        ],
    ):
        return "경제안보·외교·공급망 거버넌스 성격으로 15대 전략 primary에 직접 귀속하지 않는다."

    if contains_any(
        text,
        [
            r"건강보험",
            r"필수의료",
            r"진료권",
            r"소아환자",
            r"의료보상",
            r"공공의료",
            r"건강권",
        ],
    ):
        return "보건의료 서비스·보상·전달체계 정비 성격으로 디지털헬스 기술전략의 직접 과제는 아니다."

    if contains_any(
        text,
        [
            r"공정거래",
            r"분쟁조정",
            r"민사적구제",
            r"불공정",
            r"권익",
            r"시장질서",
            r"몰수",
            r"조달시장",
            r"임금체계",
        ],
    ):
        return "시장질서·법집행·제도정비 과제로서 15대 기술전략 primary를 두기 어렵다."

    if contains_any(
        text,
        [
            r"사회적고립",
            r"고독사",
            r"인권",
            r"교권",
            r"아동학대",
            r"재난",
            r"안전사고",
            r"정신건강",
            r"청년정책",
            r"기초학력",
        ],
    ):
        return "복지·교육·안전망 강화 성격의 일반 정책으로 특정 전략기술 primary를 두지 않는다."

    if contains_any(
        text,
        [
            r"관광",
            r"문화국가",
            r"미디어사회적책임",
            r"예술인",
            r"전통·유산",
            r"스포츠인프라",
            r"지역창업",
            r"창업국가",
            r"지방소멸",
            r"메가특구",
            r"교통인프라",
        ],
    ):
        return "지역·문화·생활 인프라 확충 과제로 15대 전략기술과 직접 대응하지 않는다."

    if contains_any(text, [r"디지털자산", r"분산원장", r"토큰증권", r"블록체인"]):
        return "디지털자산·블록체인 제도화 과제이나 현재 15대 전략 taxonomy에 대응 축이 없다."

    return "123대 국정과제의 총론·제도·지원 과제로서 15대 전략 primary를 직접 부여하기 어렵다."


def apply_updates(master_rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]], list[str]]:
    final_rows: list[dict[str, str]] = []
    pending_kept: list[str] = []

    for row in master_rows:
        if row.get("policy_id") != "POL-001":
            continue
        if (row.get("active_in_queue") or "yes") != "yes":
            continue
        if (row.get("decision_status") or "pending") != "pending":
            continue

        decision_key = row["decision_key"]
        if decision_key in KEEP_PENDING_KEYS:
            pending_kept.append(decision_key)
            continue

        final = REVIEW_OVERRIDES.get(decision_key)
        if final is None:
            final = {
                "decision_status": "no_strategy",
                "reviewed_primary_strategy_id": "",
                "reviewed_secondary_strategy_ids": "",
                "reviewed_confidence": "high",
                "reviewer_notes": build_no_strategy_reason(row),
            }

        row["decision_status"] = final["decision_status"]
        row["reviewed_primary_strategy_id"] = final["reviewed_primary_strategy_id"]
        row["reviewed_secondary_strategy_ids"] = final["reviewed_secondary_strategy_ids"]
        row["reviewed_confidence"] = final["reviewed_confidence"]
        row["reviewer_name"] = REVIEWER_NAME
        row["reviewer_notes"] = final["reviewer_notes"]

        final_rows.append(
            {
                "decision_key": decision_key,
                "policy_item_id": row["policy_item_id"],
                "policy_id": row["policy_id"],
                "policy_name": row["policy_name"],
                "bucket_label": row["bucket_label"],
                "item_label": row["item_label"],
                "final_decision_status": final["decision_status"],
                "final_primary_strategy_id": final["reviewed_primary_strategy_id"],
                "final_secondary_strategy_ids": final["reviewed_secondary_strategy_ids"],
                "final_confidence": final["reviewed_confidence"],
                "reviewer_name": REVIEWER_NAME,
                "reviewer_notes": final["reviewer_notes"],
            }
        )

    return master_rows, final_rows, pending_kept


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--master-decision-csv", required=True)
    parser.add_argument("--out-csv", required=True)
    parser.add_argument("--out-summary-json", required=True)
    args = parser.parse_args()

    master_path = Path(args.master_decision_csv)
    master_rows = read_csv(master_path)
    updated_rows, final_rows, pending_kept = apply_updates(master_rows)

    if not updated_rows:
        raise SystemExit("No master decision rows found.")

    write_csv(master_path, updated_rows, MASTER_DECISION_FIELDS)
    write_csv(Path(args.out_csv), final_rows, OUTPUT_FIELDS)

    summary = {
        "reviewer_name": REVIEWER_NAME,
        "decision_count": len(final_rows),
        "status_counts": dict(Counter(row["final_decision_status"] for row in final_rows)),
        "confidence_counts": dict(Counter(row["final_confidence"] for row in final_rows)),
        "kept_pending_count": len(pending_kept),
        "kept_pending_keys": sorted(pending_kept),
    }
    write_json(Path(args.out_summary_json), summary)
    print(f"Finalized POL-001 high-confidence decisions: {len(final_rows)}")


if __name__ == "__main__":
    main()
