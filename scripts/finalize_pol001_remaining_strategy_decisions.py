#!/usr/bin/env python3
"""Finalize the last POL-001 strategy review decisions."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


REVIEWER_NAME = "codex_manual_pol001_final"


FINAL_DECISIONS = {
    "SRD-POL-001-ab1c14a81c40": {
        "decision_status": "reviewed",
        "reviewed_primary_strategy_id": "STR-005",
        "reviewed_secondary_strategy_ids": "",
        "reviewed_confidence": "medium",
        "reviewer_notes": "국가 해상수송력 확충과 쇄빙 컨테이너선 등 해양 선박 신기술 확보가 함께 적시되어 해양 기술주권 축으로 본다.",
    },
    "SRD-POL-001-436176f287ab": {
        "decision_status": "no_strategy",
        "reviewed_primary_strategy_id": "",
        "reviewed_secondary_strategy_ids": "",
        "reviewed_confidence": "high",
        "reviewer_notes": "초격차기술 개발과 국내생산 확대를 묶은 산업 총론으로 특정 15대 전략 하나에 단일 귀속하기 어렵다.",
    },
    "SRD-POL-001-5ac8d236b66a": {
        "decision_status": "no_strategy",
        "reviewed_primary_strategy_id": "",
        "reviewed_secondary_strategy_ids": "",
        "reviewed_confidence": "high",
        "reviewer_notes": "단기·중장기 로드맵 총괄 문장으로 여러 전략을 동시에 포괄해 단일 primary를 두지 않는다.",
    },
    "SRD-POL-001-b658acfefab4": {
        "decision_status": "no_strategy",
        "reviewed_primary_strategy_id": "",
        "reviewed_secondary_strategy_ids": "",
        "reviewed_confidence": "high",
        "reviewer_notes": "전략기술 육성의 추진방식과 관리체계 설명으로 특정 기술전략의 직접 실행 항목은 아니다.",
    },
    "SRD-POL-001-8f7f69aff899": {
        "decision_status": "no_strategy",
        "reviewed_primary_strategy_id": "",
        "reviewed_secondary_strategy_ids": "",
        "reviewed_confidence": "high",
        "reviewer_notes": "북극항로 선박과 초격차 디스플레이를 한 문장에 묶은 복합 과제로 단일 primary를 고정하지 않는다.",
    },
    "SRD-POL-001-07b2894d6a17": {
        "decision_status": "no_strategy",
        "reviewed_primary_strategy_id": "",
        "reviewed_secondary_strategy_ids": "",
        "reviewed_confidence": "high",
        "reviewer_notes": "유무인복합체계 고도화는 국방 전력 과제 성격이 강하며 현재 15대 전략 taxonomy에 직접 대응 축이 없다.",
    },
    "SRD-POL-001-c339787f762d": {
        "decision_status": "no_strategy",
        "reviewed_primary_strategy_id": "",
        "reviewed_secondary_strategy_ids": "",
        "reviewed_confidence": "high",
        "reviewer_notes": "첨단기술 분야 국제협력의 법적 기반과 연구안보 체계 정비는 거버넌스 과제로 특정 전략 primary를 두지 않는다.",
    },
    "SRD-POL-001-21516e5f7e06": {
        "decision_status": "no_strategy",
        "reviewed_primary_strategy_id": "",
        "reviewed_secondary_strategy_ids": "",
        "reviewed_confidence": "high",
        "reviewer_notes": "전력시장 제도 개편은 에너지 전환의 기반 정책이지만 수소·SMR·전력망 기술 자체의 직접 실행 항목은 아니다.",
    },
    "SRD-POL-001-b4ae20fe8655": {
        "decision_status": "no_strategy",
        "reviewed_primary_strategy_id": "",
        "reviewed_secondary_strategy_ids": "",
        "reviewed_confidence": "high",
        "reviewer_notes": "특허 빅데이터 기반 R&D 기획 지원은 범용 연구지원 기능으로 특정 전략기술 primary를 두기 어렵다.",
    },
    "SRD-POL-001-0b8be7b63563": {
        "decision_status": "reviewed",
        "reviewed_primary_strategy_id": "STR-005",
        "reviewed_secondary_strategy_ids": "",
        "reviewed_confidence": "medium",
        "reviewer_notes": "친환경 선박 중심 국가수송력 확충과 선박 경쟁력 제고는 해양 산업·선박 기술 축과 직접 연결된다.",
    },
    "SRD-POL-001-0625b3b4d848": {
        "decision_status": "no_strategy",
        "reviewed_primary_strategy_id": "",
        "reviewed_secondary_strategy_ids": "",
        "reviewed_confidence": "high",
        "reviewer_notes": "거점항만 육성과 스마트항만 조성은 해양 물류 인프라 정책으로, 현재 15대 전략 중 단일 primary로 고정하기는 어렵다.",
    },
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


def apply_updates(master_rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]], int]:
    updated = 0
    output_rows: list[dict[str, str]] = []
    for row in master_rows:
        final = FINAL_DECISIONS.get(row.get("decision_key", ""))
        if not final:
            continue
        if (row.get("decision_status") or "pending") != "pending":
            continue

        row["decision_status"] = final["decision_status"]
        row["reviewed_primary_strategy_id"] = final["reviewed_primary_strategy_id"]
        row["reviewed_secondary_strategy_ids"] = final["reviewed_secondary_strategy_ids"]
        row["reviewed_confidence"] = final["reviewed_confidence"]
        row["reviewer_name"] = REVIEWER_NAME
        row["reviewer_notes"] = final["reviewer_notes"]
        updated += 1

        output_rows.append(
            {
                "decision_key": row["decision_key"],
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

    return master_rows, output_rows, updated


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--master-decision-csv", required=True)
    parser.add_argument("--out-csv", required=True)
    parser.add_argument("--out-summary-json", required=True)
    args = parser.parse_args()

    master_path = Path(args.master_decision_csv)
    master_rows = read_csv(master_path)
    updated_rows, output_rows, updated_count = apply_updates(master_rows)
    if updated_count != len(FINAL_DECISIONS):
        missing = sorted(set(FINAL_DECISIONS) - {row["decision_key"] for row in output_rows})
        raise RuntimeError(f"Did not update all expected decision keys: {missing}")

    write_csv(master_path, updated_rows, MASTER_DECISION_FIELDS)
    write_csv(Path(args.out_csv), output_rows, OUTPUT_FIELDS)
    write_json(
        Path(args.out_summary_json),
        {
            "reviewer_name": REVIEWER_NAME,
            "decision_count": len(output_rows),
            "status_counts": dict(Counter(row["final_decision_status"] for row in output_rows)),
            "confidence_counts": dict(Counter(row["final_confidence"] for row in output_rows)),
        },
    )
    print(f"Finalized remaining POL-001 decisions: {updated_count}")


if __name__ == "__main__":
    main()
