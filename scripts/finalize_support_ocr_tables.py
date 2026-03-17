#!/usr/bin/env python3
"""Finalize support OCR tables into curated structured extraction artifacts."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


MANUAL_TABLE_CONFIGS = {
    "DOC-CTX-002": {
        "table_id": "TBL-DOC-CTX-002-CURATED-001",
        "title": "사이버보안 분야 세부기술 분류체계",
        "columns": ["중분류", "기술 개요"],
        "rows": [
            [
                "공통기반",
                "양자 내성 암호(PQC), 동형 암호, DID/FIDO 등 차세대 암호·인증과 데이터 비식별화, 프라이버시 강화기술(PET), 데이터 무결성 검증 기술",
            ],
            [
                "클라우드·플랫폼 보안",
                "5G/6G 통신망 보안, 클라우드 네이티브 보안(CNAPP), 서버·PC·모바일·IoT 엣지 디바이스와 운영체제·펌웨어 보안",
            ],
            [
                "신기술 융합보안",
                "AI 모델 보호와 AI 활용 탐지, 학습데이터 보호, 블록체인·스마트 컨트랙트 보안, 디지털 자산 및 탈중앙화 서비스 보안",
            ],
            [
                "물리·현장보안",
                "지능형 CCTV, 생체인식 출입통제, 무인 경비 시스템 등 현장·물리 보안 기술",
            ],
            [
                "위협·정책 대응",
                "제로트러스트, SW 공급망 보안, 사이버 회복력, 국제협력, 디지털 포렌식·수사 지원 등 위협 대응·정책 기반 기술",
            ],
        ],
        "source_candidate_ids": ["TBL-DOC-CTX-002-OCR-001"],
        "tech_domain": "사이버보안",
        "page_no": 1,
    },
    "DOC-CTX-003": {
        "table_id": "TBL-DOC-CTX-003-CURATED-001",
        "title": "소재 분야 세부기술 분류체계",
        "columns": ["중분류", "기술 개요"],
        "rows": [
            [
                "금속소재",
                "우수한 전기·열전도성과 높은 인장강도를 바탕으로 자동차, 조선, 에너지, 항공·방산, IT 등 핵심 산업에 활용되는 소재",
            ],
            [
                "세라믹소재",
                "산화물·질화물·탄화물·붕화물 등으로 구성되며 높은 경도, 내열성, 내식성, 전기절연성을 바탕으로 전자, 에너지, 건축, 의료 분야에 활용되는 소재",
            ],
            [
                "화학소재",
                "분자 구조와 조성에 따라 물성을 조절할 수 있으며 내열성, 내화학성, 절연성, 기능성을 기반으로 전자, 에너지, 바이오, 환경 분야에 활용되는 소재",
            ],
            [
                "섬유소재",
                "의류용 섬유 외에도 고강도, 내열성, 내화학성을 토대로 자동차, 토목·건축, 의료, 환경 분야에 활용되는 소재",
            ],
            [
                "탄소소재",
                "탄소를 주성분으로 하며 고강도, 내열성, 내화학성, 높은 전기전도성 등 물성을 바탕으로 첨단 산업 전반에 활용되는 소재",
            ],
            [
                "나노소재",
                "나노미터 수준에서 제어되는 구조를 바탕으로 전기·광학·기계적 특성을 고도화하는 소재",
            ],
            [
                "첨단미래소재",
                "미래 전략산업 수요에 대응하는 차세대 기능성·고성능 소재군",
            ],
        ],
        "source_candidate_ids": ["TBL-DOC-CTX-003-OCR-001"],
        "tech_domain": "소재",
        "page_no": 1,
    },
    "DOC-CTX-004": {
        "table_id": "TBL-DOC-CTX-004-CURATED-001",
        "title": "양자 분야 세부기술 분류체계",
        "columns": ["중분류", "기술 개요"],
        "rows": [
            [
                "양자컴퓨팅",
                "중첩·얽힘 등 양자역학적 특성을 활용해 고전 컴퓨터를 능가하는 초고속 연산 성능을 구현하는 기술",
            ],
            [
                "양자통신",
                "양자 상태의 민감성과 비복제성을 활용해 고신뢰·고보안 통신을 구현하는 기술",
            ],
            [
                "양자센서",
                "양자의 초고감도 특성을 기반으로 기존 센서의 측정 한계를 넘어서는 초정밀 계측 기술",
            ],
            [
                "공통기반",
                "핵심 소재·부품·장비와 기초 원천기술 연구, 양자팹, 양자컴퓨팅 클라우드, 지역별 연구거점 등 양자기술 개발 인프라",
            ],
            [
                "국제협력",
                "국제 공동연구와 기술교류 활동",
            ],
        ],
        "source_candidate_ids": ["TBL-DOC-CTX-004-OCR-001"],
        "tech_domain": "양자",
        "page_no": 1,
    },
}


DOC_REF_002_CURATION = [
    {
        "source_path": "work/04_ontology/instances/derived_tables/CTBL-DOC-REF-002-001__strategy-reference.json",
        "table_id": "TBL-DOC-REF-002-CURATED-001",
        "page_no": 1,
    },
    {
        "source_path": "work/04_ontology/instances/derived_tables/CTBL-DOC-REF-002-002__infrastructure-reference.json",
        "table_id": "TBL-DOC-REF-002-CURATED-002",
        "page_no": 1,
    },
    {
        "source_path": "work/04_ontology/instances/derived_tables/CTBL-DOC-REF-002-003__talent-reference.json",
        "table_id": "TBL-DOC-REF-002-CURATED-003",
        "page_no": 1,
    },
]


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(path: Path, rows: list[list[object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerows(rows)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def manual_payload(document_id: str, config: dict) -> tuple[dict, list[list[object]]]:
    cell_matrix = [config["columns"], *config["rows"]]
    payload = {
        "table_id": config["table_id"],
        "document_id": document_id,
        "page_no_or_sheet_name": config["page_no"],
        "block_order": 1,
        "table_title": config["title"],
        "header_rows": [1],
        "table_shape": {
            "rows": len(cell_matrix),
            "cols": len(config["columns"]),
        },
        "cell_matrix": cell_matrix,
        "merged_cell_info": [],
        "source_bbox": None,
        "extraction_confidence": "medium",
        "extraction_method": "manual-curated-from-ocr-review-v1",
        "candidate_source": "finalized_from_ocr_review",
        "review_required": False,
        "source_candidate_ids": config["source_candidate_ids"],
        "tech_domain": config["tech_domain"],
    }
    return payload, cell_matrix


def doc_ref_payload(out_root: Path, config: dict) -> tuple[dict, list[list[object]]]:
    source = load_json(out_root / config["source_path"])
    cell_matrix = [source["columns"], *source["cell_matrix"]]
    payload = {
        "table_id": config["table_id"],
        "document_id": source["document_id"],
        "page_no_or_sheet_name": config["page_no"],
        "block_order": 1,
        "table_title": source["title"],
        "header_rows": [1],
        "table_shape": {
            "rows": len(cell_matrix),
            "cols": len(source["columns"]),
        },
        "cell_matrix": cell_matrix,
        "merged_cell_info": [],
        "source_bbox": None,
        "extraction_confidence": "medium",
        "extraction_method": "manual-curated-from-doc-ref-002-canonical-reference-v1",
        "candidate_source": "finalized_from_canonical_reference",
        "review_required": False,
        "source_candidate_ids": source["provenance"]["source_candidate_ids"],
        "source_asset_path": source["provenance"].get("source_asset_path"),
    }
    return payload, cell_matrix


def table_entry(table_payload: dict, json_path: Path, csv_path: Path, out_root: Path) -> dict:
    return {
        "table_id": table_payload["table_id"],
        "path": str(json_path.relative_to(out_root)),
        "csv_path": str(csv_path.relative_to(out_root)),
        "page_no": table_payload["page_no_or_sheet_name"],
        "rows": table_payload["table_shape"]["rows"],
        "cols": table_payload["table_shape"]["cols"],
        "candidate_source": table_payload["candidate_source"],
    }


def replace_manifest_tables(out_root: Path, document_id: str, table_entries: list[dict], note: str) -> None:
    manifest_path = out_root / "work/02_structured-extraction/manifests" / f"{document_id}_manifest.json"
    manifest = load_json(manifest_path)
    manifest["processing_status"] = "completed"
    manifest["tables"] = table_entries

    counts = manifest.get("counts", {})
    if not isinstance(counts, dict):
        counts = {}
    counts["tables"] = len(table_entries)
    manifest["counts"] = counts

    quality_notes = [
        item
        for item in manifest.get("quality_notes", [])
        if item != "Table structure is not yet reconstructed; further table parsing is still required."
    ]
    if note not in quality_notes:
        quality_notes.append(note)
    manifest["quality_notes"] = quality_notes
    write_json(manifest_path, manifest)


def finalize_manual_docs(out_root: Path) -> None:
    tables_dir = out_root / "work/02_structured-extraction/tables"
    for document_id, config in MANUAL_TABLE_CONFIGS.items():
        payload, cell_matrix = manual_payload(document_id, config)
        json_path = tables_dir / f"{payload['table_id']}.json"
        csv_path = tables_dir / f"{payload['table_id']}.csv"
        write_json(json_path, payload)
        write_csv(csv_path, cell_matrix)
        replace_manifest_tables(
            out_root,
            document_id,
            [table_entry(payload, json_path, csv_path, out_root)],
            "OCR line candidates were manually normalized into a finalized structured table.",
        )


def finalize_doc_ref_002(out_root: Path) -> None:
    tables_dir = out_root / "work/02_structured-extraction/tables"
    table_entries = []
    for config in DOC_REF_002_CURATION:
        payload, cell_matrix = doc_ref_payload(out_root, config)
        json_path = tables_dir / f"{payload['table_id']}.json"
        csv_path = tables_dir / f"{payload['table_id']}.csv"
        write_json(json_path, payload)
        write_csv(csv_path, cell_matrix)
        table_entries.append(table_entry(payload, json_path, csv_path, out_root))

    replace_manifest_tables(
        out_root,
        "DOC-REF-002",
        table_entries,
        "OCR board candidate was manually normalized into curated structured tables aligned with canonical reference rows.",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-root", required=True)
    args = parser.parse_args()

    out_root = Path(args.out_root)
    finalize_manual_docs(out_root)
    finalize_doc_ref_002(out_root)


if __name__ == "__main__":
    main()
