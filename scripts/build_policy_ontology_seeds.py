#!/usr/bin/env python3
"""Build initial ontology seed CSVs from the document registry."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


POLICY_ORDER = [
    ("POL-001", "123대 국정과제"),
    ("POL-002", "AI-바이오 국가전략"),
    ("POL-003", "과학기술xAI 국가전략"),
    ("POL-004", "AI시대 대한민국 네트워크 전략"),
    ("POL-005", "AI반도체 산업 도약 전략"),
    ("POL-006", "제조AX 추진방향"),
    ("POL-007", "기초연구 생태계 육성 방안"),
    ("POL-008", "민간투자연계, 팁스 R&D 확산방안"),
    ("POL-009", "과학기술분야 출연(연) 정책방향"),
    ("POL-010", "연구개발 생태계 혁신방안"),
    ("POL-011", "정부 AX사업 전주기 원스톱 지원방안"),
    ("POL-012", "초혁신경제 15대 프로젝트 추진계획"),
]

RESOURCE_CATEGORIES = [
    ("technology", "기술", "기술 개발, 상용화, 실증, 제품화, 핵심 기술 확보 관련 항목", 1),
    (
        "infrastructure_institutional",
        "인프라·제도",
        "플랫폼, 데이터, 장비, 실증환경, 거버넌스, 제도 개선, 재정·금융 지원 관련 항목",
        2,
    ),
    ("talent", "인재", "인력양성, 교육, 연구인력 확보, 전문인력 유치 관련 항목", 3),
]


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


def infer_location_granularity(source_format: str) -> str:
    source_format = source_format.lower()
    if source_format == "pdf":
        return "page"
    if source_format in {"hwp", "hwpx"}:
        return "section"
    if source_format == "xlsx":
        return "sheet"
    return "unknown"


def build_policy_rows(registry_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    policy_documents = {
        row["registry_id"]: row
        for row in registry_rows
        if row["doc_role"] == "policy_source" and row["scope_track"] == "phase1"
    }
    rows: list[dict[str, object]] = []

    for policy_order, (policy_id, policy_name) in enumerate(POLICY_ORDER, start=1):
        matching_docs = [
            row
            for row in policy_documents.values()
            if row["normalized_title"] == policy_name
        ]
        primary_document = matching_docs[0]["registry_id"] if matching_docs else ""
        has_source_document = 1 if any(row["include_status"] == "include" for row in matching_docs) else 0
        policy_status = "active" if has_source_document else "missing_source"
        notes = ""
        if matching_docs and matching_docs[0]["include_status"] == "missing":
            notes = "문서 레지스트리 기준 원문 미확보"
        rows.append(
            {
                "policy_id": policy_id,
                "policy_name": policy_name,
                "policy_order": policy_order,
                "policy_status": policy_status,
                "primary_document_id": primary_document,
                "has_source_document": has_source_document,
                "source_document_count": len(matching_docs),
                "notes": notes,
            }
        )
    return rows


def build_document_rows(registry_rows: list[dict[str, str]], policy_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    title_to_policy_id = {row["policy_name"]: row["policy_id"] for row in policy_rows}
    rows: list[dict[str, object]] = []
    for registry_row in registry_rows:
        policy_id = title_to_policy_id.get(registry_row["normalized_title"], "")
        if not policy_id:
            policy_id = None
        rows.append(
            {
                "document_id": registry_row["registry_id"],
                "registry_id": registry_row["registry_id"],
                "policy_id": policy_id,
                "doc_role": registry_row["doc_role"],
                "scope_track": registry_row["scope_track"],
                "include_status": registry_row["include_status"],
                "normalized_title": registry_row["normalized_title"],
                "source_rel_path": registry_row["source_rel_path"],
                "internal_path": registry_row["internal_path"],
                "source_format": registry_row["source_format"],
                "issuing_org": registry_row["issuing_org"],
                "issued_date": registry_row["issued_date"],
                "region": registry_row["region"],
                "location_granularity": infer_location_granularity(registry_row["source_format"]),
                "notes": registry_row["notes"],
            }
        )
    return rows


def build_resource_rows() -> list[dict[str, object]]:
    return [
        {
            "resource_category_id": resource_category_id,
            "display_label": display_label,
            "description": description,
            "display_order": display_order,
            "is_active": 1,
        }
        for resource_category_id, display_label, description, display_order in RESOURCE_CATEGORIES
    ]


def build_policy_bucket_rows(policy_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for policy_row in policy_rows:
        for display_order, (resource_category_id, _, _, _) in enumerate(RESOURCE_CATEGORIES, start=1):
            rows.append(
                {
                    "policy_bucket_id": f"PBK-{policy_row['policy_id']}-{display_order:02d}",
                    "policy_id": policy_row["policy_id"],
                    "resource_category_id": resource_category_id,
                    "display_order": display_order,
                    "bucket_summary": "",
                    "bucket_status": "ready" if policy_row["has_source_document"] else "source_missing",
                }
            )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry-path", required=True)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()

    registry_path = Path(args.registry_path)
    out_dir = Path(args.out_dir)

    registry_rows = read_csv_rows(registry_path)
    policy_rows = build_policy_rows(registry_rows)
    document_rows = build_document_rows(registry_rows, policy_rows)
    resource_rows = build_resource_rows()
    policy_bucket_rows = build_policy_bucket_rows(policy_rows)

    write_csv(
        out_dir / "resource_categories.csv",
        resource_rows,
        ["resource_category_id", "display_label", "description", "display_order", "is_active"],
    )
    write_csv(
        out_dir / "policy_master.csv",
        policy_rows,
        [
            "policy_id",
            "policy_name",
            "policy_order",
            "policy_status",
            "primary_document_id",
            "has_source_document",
            "source_document_count",
            "notes",
        ],
    )
    write_csv(
        out_dir / "documents_seed.csv",
        document_rows,
        [
            "document_id",
            "registry_id",
            "policy_id",
            "doc_role",
            "scope_track",
            "include_status",
            "normalized_title",
            "source_rel_path",
            "internal_path",
            "source_format",
            "issuing_org",
            "issued_date",
            "region",
            "location_granularity",
            "notes",
        ],
    )
    write_csv(
        out_dir / "policy_bucket_master.csv",
        policy_bucket_rows,
        [
            "policy_bucket_id",
            "policy_id",
            "resource_category_id",
            "display_order",
            "bucket_summary",
            "bucket_status",
        ],
    )


if __name__ == "__main__":
    main()
