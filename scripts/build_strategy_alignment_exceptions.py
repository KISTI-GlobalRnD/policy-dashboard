#!/usr/bin/env python3
"""Materialize known strategy/reference alignment exceptions."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path


EXCEPTION_ID = "STX-STR-010-001"
STRATEGY_ID = "STR-010"
STRATEGY_LABEL = "디지털 헬스케어 서비스 혁신"
REFERENCE_DOCUMENT_ID = "DOC-REF-002"
REFERENCE_TABLE_ID = "CTBL-DOC-REF-002-001"
REFERENCE_SEQUENCE_NO = "10"
RECOMMENDED_SOURCE_BASIS = "DOC-POL-006; POL-012 reviewed healthcare cluster; STX-STR-010-001"
DECISION_KEY_PATTERN = re.compile(r"decision_key=([A-Za-z0-9-]+)")


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def load_reference_row(reference_table_csv: Path) -> dict[str, str]:
    for row in read_csv_rows(reference_table_csv):
        if row.get("sequence_no") == REFERENCE_SEQUENCE_NO:
            return row
    raise ValueError(
        f"Reference row {REFERENCE_SEQUENCE_NO} not found in {reference_table_csv}"
    )


def load_reviewed_evidence(
    reviewed_map_csv: Path,
    review_decisions_csv: Path,
) -> list[dict[str, str]]:
    decision_keys: list[str] = []
    for row in read_csv_rows(reviewed_map_csv):
        if row.get("term_id") != STRATEGY_ID:
            continue
        notes = row.get("notes", "")
        match = DECISION_KEY_PATTERN.search(notes)
        if match:
            decision_keys.append(match.group(1))

    if not decision_keys:
        return []

    decisions_by_key = {
        row["decision_key"]: row for row in read_csv_rows(review_decisions_csv)
    }

    evidence_rows = []
    for decision_key in decision_keys:
        row = decisions_by_key.get(decision_key)
        if row is None:
            raise ValueError(f"Missing review decision for {decision_key}")
        evidence_rows.append(row)

    return evidence_rows


def build_exception_payload(
    reference_row: dict[str, str],
    evidence_rows: list[dict[str, str]],
) -> tuple[dict[str, object], dict[str, object]]:
    policy_ids = sorted({row["policy_id"] for row in evidence_rows if row.get("policy_id")})
    policy_item_ids = [row["policy_item_id"] for row in evidence_rows if row.get("policy_item_id")]
    decision_keys = [row["decision_key"] for row in evidence_rows if row.get("decision_key")]
    evidence_ids = [row["primary_evidence_id"] for row in evidence_rows if row.get("primary_evidence_id")]

    csv_row = {
        "exception_id": EXCEPTION_ID,
        "strategy_id": STRATEGY_ID,
        "strategy_label": STRATEGY_LABEL,
        "reference_document_id": REFERENCE_DOCUMENT_ID,
        "reference_table_id": REFERENCE_TABLE_ID,
        "reference_sequence_no": REFERENCE_SEQUENCE_NO,
        "reference_strategy_label": reference_row["strategy_label"],
        "reference_content_summary": reference_row["content_summary"],
        "alignment_status": "not_aligned",
        "resolution_status": "keep_strategy_and_reference_separate",
        "reviewed_policy_ids": " | ".join(policy_ids),
        "reviewed_policy_item_ids": " | ".join(policy_item_ids),
        "reviewed_decision_keys": " | ".join(decision_keys),
        "reviewed_primary_evidence_ids": " | ".join(evidence_ids),
        "reviewed_evidence_count": len(evidence_rows),
        "recommended_source_basis": RECOMMENDED_SOURCE_BASIS,
        "notes": (
            "DOC-REF-002 technology row 10 is cyber-focused, but reviewed manual strategy "
            "mappings for STR-010 are healthcare-focused items from POL-012/DOC-POL-006."
        ),
    }

    json_payload = {
        "exception_id": EXCEPTION_ID,
        "strategy": {
            "strategy_id": STRATEGY_ID,
            "strategy_label": STRATEGY_LABEL,
            "recommended_source_basis": RECOMMENDED_SOURCE_BASIS,
        },
        "reference": {
            "document_id": REFERENCE_DOCUMENT_ID,
            "canonical_table_id": REFERENCE_TABLE_ID,
            "sequence_no": int(REFERENCE_SEQUENCE_NO),
            "strategy_label": reference_row["strategy_label"],
            "content_summary": reference_row["content_summary"],
        },
        "alignment_status": "not_aligned",
        "resolution_status": "keep_strategy_and_reference_separate",
        "reviewed_evidence_count": len(evidence_rows),
        "reviewed_policy_ids": policy_ids,
        "reviewed_policy_item_ids": policy_item_ids,
        "reviewed_decision_keys": decision_keys,
        "reviewed_primary_evidence_ids": evidence_ids,
        "evidence_records": [
            {
                "decision_key": row["decision_key"],
                "policy_id": row["policy_id"],
                "policy_name": row["policy_name"],
                "policy_item_id": row["policy_item_id"],
                "bucket_label": row["bucket_label"],
                "item_label": row["item_label"],
                "primary_evidence_id": row["primary_evidence_id"],
                "evidence_preview": row["evidence_preview"],
            }
            for row in evidence_rows
        ],
        "notes": [
            "Reviewed STR-010 mappings currently originate from healthcare-specific items in POL-012.",
            "DOC-REF-002 row 10 should remain a reference-only cyber strategy row until a separate taxonomy change is approved.",
        ],
    }

    return csv_row, json_payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", required=True)
    parser.add_argument(
        "--reviewed-map-csv",
        default="work/04_ontology/instances/policy_item_strategy_map_reviewed.csv",
    )
    parser.add_argument(
        "--review-decisions-csv",
        default="qa/ontology/review_queues/policy-item-strategy-review-decisions.csv",
    )
    parser.add_argument(
        "--reference-table-csv",
        default="work/04_ontology/instances/derived_tables/CTBL-DOC-REF-002-001__strategy-reference.csv",
    )
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    reference_row = load_reference_row(Path(args.reference_table_csv))
    evidence_rows = load_reviewed_evidence(
        Path(args.reviewed_map_csv),
        Path(args.review_decisions_csv),
    )
    csv_fieldnames = [
        "exception_id",
        "strategy_id",
        "strategy_label",
        "reference_document_id",
        "reference_table_id",
        "reference_sequence_no",
        "reference_strategy_label",
        "reference_content_summary",
        "alignment_status",
        "resolution_status",
        "reviewed_policy_ids",
        "reviewed_policy_item_ids",
        "reviewed_decision_keys",
        "reviewed_primary_evidence_ids",
        "reviewed_evidence_count",
        "recommended_source_basis",
        "notes",
    ]
    if not evidence_rows:
        write_csv(out_dir / "strategy_alignment_exceptions.csv", [], csv_fieldnames)
        (out_dir / "strategy_alignment_exceptions.json").write_text("[]\n", encoding="utf-8")
        print("Strategy alignment exceptions written: 0")
        return

    csv_row, json_payload = build_exception_payload(reference_row, evidence_rows)
    write_csv(out_dir / "strategy_alignment_exceptions.csv", [csv_row], csv_fieldnames)
    (out_dir / "strategy_alignment_exceptions.json").write_text(
        json.dumps([json_payload], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print("Strategy alignment exceptions written: 1")


if __name__ == "__main__":
    main()
