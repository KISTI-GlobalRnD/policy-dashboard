#!/usr/bin/env python3
"""Finalize explicit manual decisions for selected strategy review draft rows."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


REVIEWER_NAME = "codex_manual_strategy_review"


FINAL_DECISIONS = {
    "SRD-POL-001-3d500d3e4f44": {
        "decision_status": "reviewed",
        "reviewed_primary_strategy_id": "STR-006",
        "reviewed_secondary_strategy_ids": "",
        "reviewed_confidence": "high",
        "reviewer_notes": "서남해·제주 해상풍력단지 구축을 위한 계획입지 발굴·인허가 특례는 STR-006의 직접 실행 과제다.",
    },
    "SRD-POL-001-fa0676e55344": {
        "decision_status": "reviewed",
        "reviewed_primary_strategy_id": "STR-015",
        "reviewed_secondary_strategy_ids": "",
        "reviewed_confidence": "high",
        "reviewer_notes": "영양·백신·보건 지원은 감염병 대응 및 공중보건 축과 직접 연결된다.",
    },
    "SRD-POL-001-b72144647fc9": {
        "decision_status": "no_strategy",
        "reviewed_primary_strategy_id": "",
        "reviewed_secondary_strategy_ids": "",
        "reviewed_confidence": "high",
        "reviewer_notes": "기후변화 대응, 식량안보, 반도체 초순수 공급이 결합된 복합 회복력 과제로 단일 15대 전략 primary를 두기 어렵다.",
    },
    "SRD-POL-001-f37a87b79bb6": {
        "decision_status": "reviewed",
        "reviewed_primary_strategy_id": "STR-002",
        "reviewed_secondary_strategy_ids": "",
        "reviewed_confidence": "high",
        "reviewer_notes": "반도체 실증팹 구축은 초격차 전략기술 확보 축의 직접 근거다.",
    },
    "SRD-POL-001-7e8e706ea712": {
        "decision_status": "no_strategy",
        "reviewed_primary_strategy_id": "",
        "reviewed_secondary_strategy_ids": "",
        "reviewed_confidence": "high",
        "reviewer_notes": "반도체·RE100 산단 대상 안정적 물공급은 범용 산업 인프라 과제로 단일 전략 primary를 두기 어렵다.",
    },
    "SRD-POL-001-11edb9c9fdaf": {
        "decision_status": "no_strategy",
        "reviewed_primary_strategy_id": "",
        "reviewed_secondary_strategy_ids": "",
        "reviewed_confidence": "high",
        "reviewer_notes": "조선·방산·반도체를 함께 묶는 규제혁신 총론으로 특정 15대 전략에 단일 귀속하기 어렵다.",
    },
    "SRD-POL-001-9d9ac7b2b560": {
        "decision_status": "no_strategy",
        "reviewed_primary_strategy_id": "",
        "reviewed_secondary_strategy_ids": "",
        "reviewed_confidence": "high",
        "reviewer_notes": "가속기·핵융합·연구로·첨단장비를 포괄하는 범분야 연구인프라 확충 과제로 단일 전략 primary를 두기 어렵다.",
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


def apply_to_master(
    master_rows: list[dict[str, str]],
    final_rows: list[dict[str, str]],
    draft_lookup: dict[str, dict[str, str]],
) -> tuple[list[dict[str, str]], int]:
    final_by_key = {row["decision_key"]: row for row in final_rows}
    updated_count = 0
    for row in master_rows:
        final = final_by_key.get(row.get("decision_key", ""))
        if not final:
            continue
        draft = draft_lookup[row["decision_key"]]
        next_values = {
            "policy_item_id": draft.get("policy_item_id", row.get("policy_item_id", "")),
            "policy_id": draft.get("policy_id", row.get("policy_id", "")),
            "policy_name": draft.get("policy_name", row.get("policy_name", "")),
            "bucket_label": draft.get("bucket_label", row.get("bucket_label", "")),
            "item_label": draft.get("item_label", row.get("item_label", "")),
            "primary_evidence_id": draft.get("primary_evidence_id", row.get("primary_evidence_id", "")),
            "evidence_preview": draft.get("evidence_preview", row.get("evidence_preview", "")),
            "tech_domains": draft.get("tech_domains", row.get("tech_domains", "")),
            "suggested_primary_strategy_id": draft.get("suggested_primary_strategy_id", row.get("suggested_primary_strategy_id", "")),
            "suggested_primary_strategy_label": draft.get("suggested_primary_strategy_label", row.get("suggested_primary_strategy_label", "")),
            "suggested_primary_strategy_score": draft.get("suggested_primary_strategy_score", row.get("suggested_primary_strategy_score", "")),
            "alternate_strategy_ids": draft.get("alternate_strategy_ids", row.get("alternate_strategy_ids", "")),
            "alternate_strategy_labels": draft.get("alternate_strategy_labels", row.get("alternate_strategy_labels", "")),
            "decision_status": final["final_decision_status"],
            "reviewed_primary_strategy_id": final["final_primary_strategy_id"],
            "reviewed_secondary_strategy_ids": final["final_secondary_strategy_ids"],
            "reviewed_confidence": final["final_confidence"],
            "reviewer_name": final["reviewer_name"],
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
    parser.add_argument("--draft-csv", action="append", required=True)
    parser.add_argument("--out-csv", required=True)
    parser.add_argument("--out-summary-json", required=True)
    parser.add_argument("--master-decision-csv", required=True)
    args = parser.parse_args()

    draft_rows: list[dict[str, str]] = []
    for draft_csv in args.draft_csv:
        draft_rows.extend(read_csv(Path(draft_csv)))

    draft_lookup = {row["decision_key"]: row for row in draft_rows}
    missing_keys = sorted(key for key in FINAL_DECISIONS if key not in draft_lookup)
    if missing_keys:
        raise KeyError(f"Missing draft rows for manual decisions: {missing_keys}")

    final_rows = []
    for decision_key, final in FINAL_DECISIONS.items():
        draft = draft_lookup[decision_key]
        final_rows.append(
            {
                "decision_key": decision_key,
                "policy_item_id": draft["policy_item_id"],
                "policy_id": draft["policy_id"],
                "policy_name": draft["policy_name"],
                "bucket_label": draft["bucket_label"],
                "item_label": draft["item_label"],
                "final_decision_status": final["decision_status"],
                "final_primary_strategy_id": final["reviewed_primary_strategy_id"],
                "final_secondary_strategy_ids": final["reviewed_secondary_strategy_ids"],
                "final_confidence": final["reviewed_confidence"],
                "reviewer_name": REVIEWER_NAME,
                "reviewer_notes": final["reviewer_notes"],
            }
        )

    master_path = Path(args.master_decision_csv)
    master_rows = read_csv(master_path)
    updated_rows, updated_count = apply_to_master(master_rows, final_rows, draft_lookup)
    write_csv(master_path, updated_rows, MASTER_DECISION_FIELDS if not master_rows else list(updated_rows[0].keys()))
    write_csv(Path(args.out_csv), final_rows, OUTPUT_FIELDS)

    summary = {
        "decision_count": len(final_rows),
        "status_counts": dict(Counter(row["final_decision_status"] for row in final_rows)),
        "confidence_counts": dict(Counter(row["final_confidence"] for row in final_rows)),
        "updated_master_rows": updated_count,
    }
    write_json(Path(args.out_summary_json), summary)
    print(f"Finalized strategy manual decisions: {len(final_rows)}")


if __name__ == "__main__":
    main()
