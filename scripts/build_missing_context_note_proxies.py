#!/usr/bin/env python3
"""Build derived proxy context notes for missing support-domain documents.

These artifacts are intentionally marked as proxy notes because the original
source PDFs are not present in the repository. The content is limited to the
registered tech-domain taxonomy plus the set of relevant policy documents
already present in the corpus.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path


PROXY_CONFIGS = [
    {
        "document_id": "DOC-CTX-012",
        "title": "기술분야 개요 인공지능",
        "tech_domain": "인공지능",
        "source_documents": ["DOC-POL-001", "DOC-POL-002", "DOC-POL-004", "DOC-POL-012"],
        "extra_keywords": ["AI", "LLM", "GPU", "데이터", "AX"],
    },
    {
        "document_id": "DOC-CTX-013",
        "title": "기술분야 개요 첨단로봇제조",
        "tech_domain": "첨단로봇제조",
        "source_documents": ["DOC-POL-003", "DOC-POL-006", "DOC-POL-012"],
        "extra_keywords": ["로봇", "스마트팩토리", "AI팩토리", "제조데이터", "자율화"],
    },
    {
        "document_id": "DOC-CTX-014",
        "title": "기술분야 개요 반도체디스플레이",
        "tech_domain": "반도체디스플레이",
        "source_documents": ["DOC-POL-001", "DOC-POL-006", "DOC-POL-007"],
        "extra_keywords": ["반도체", "디스플레이", "패키징", "NPU", "PIM", "소부장"],
    },
]

TOKEN_SPLIT_RE = re.compile(r"[·/(),\-\s]+")
NON_ALNUM_RE = re.compile(r"[^가-힣A-Za-z0-9]+")


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


def write_csv(path: Path, rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerows(rows)


def load_document_titles(seed_csv: Path) -> dict[str, str]:
    with seed_csv.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return {
        row["document_id"]: row.get("normalized_title", row["document_id"])
        for row in rows
        if row.get("document_id")
    }


def load_seed_rows(seed_csv: Path) -> dict[str, dict]:
    with seed_csv.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return {row["document_id"]: row for row in rows if row.get("document_id")}


def load_taxonomy_rows(path: Path) -> dict[str, list[str]]:
    domain_rows: dict[str, list[str]] = {}
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            domain = row["tech_domain"].strip()
            subdomain = row["tech_subdomain"].strip()
            if not domain or not subdomain:
                continue
            domain_rows.setdefault(domain, []).append(subdomain)
    return domain_rows


def normalize_text(text: str) -> str:
    return NON_ALNUM_RE.sub("", text).lower()


def build_keyword_set(tech_domain: str, subdomains: list[str], extra_keywords: list[str]) -> list[str]:
    keywords = {tech_domain, *subdomains, *extra_keywords}
    expanded = set(keywords)
    for value in list(keywords):
        for token in TOKEN_SPLIT_RE.split(value):
            token = token.strip()
            if len(token) >= 2:
                expanded.add(token)
    normalized = sorted({normalize_text(value) for value in expanded if normalize_text(value)})
    return normalized


def load_source_blocks(text_dir: Path, document_id: str) -> list[dict]:
    path = text_dir / f"{document_id}_blocks.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        return payload.get("blocks", [])
    return payload


def block_locator(block: dict) -> str:
    page_no = block.get("page_no")
    if page_no not in (None, ""):
        return f"page {page_no}"
    section = block.get("page_no_or_sheet_name")
    if section:
        return str(section)
    return "source"


def compact_text(text: str, limit: int = 180) -> str:
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def select_supporting_evidence(
    text_dir: Path,
    document_titles: dict[str, str],
    source_documents: list[str],
    keywords: list[str],
    per_document_limit: int = 2,
) -> list[dict]:
    selected: list[dict] = []
    for document_id in source_documents:
        blocks = load_source_blocks(text_dir, document_id)
        scored = []
        for block in blocks:
            text = (block.get("text") or "").strip()
            if len(text) < 20:
                continue
            normalized = normalize_text(text)
            if not normalized:
                continue
            matched = [keyword for keyword in keywords if keyword and keyword in normalized]
            if not matched:
                continue
            score = len(set(matched))
            if any(keyword == normalize_text(document_titles.get(document_id, "")) for keyword in matched):
                score -= 1
            scored.append(
                {
                    "document_id": document_id,
                    "document_title": document_titles.get(document_id, document_id),
                    "evidence_id": block.get("evidence_id", ""),
                    "locator": block_locator(block),
                    "score": score,
                    "text": compact_text(text),
                }
            )
        scored.sort(key=lambda item: (-item["score"], item["evidence_id"]))
        selected.extend(scored[:per_document_limit])
    return selected


def build_markdown(
    title: str,
    tech_domain: str,
    subdomains: list[str],
    source_lines: list[str],
    supporting_evidence: list[dict],
) -> str:
    lines = [
        f"# {title}",
        "",
        "> 원문 미확보 상태에서 기존 코퍼스와 기술분류표를 바탕으로 생성한 proxy context note.",
        "",
        f"- 대분류: {tech_domain}",
        f"- 중분류 수: {len(subdomains)}",
        "",
        "## 중분류",
    ]
    for item in subdomains:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## 관련 정책 문서",
        ]
    )
    for line in source_lines:
        lines.append(f"- {line}")
    lines.extend(["", "## 대표 근거 문단"])
    for item in supporting_evidence:
        lines.append(
            f"- {item['document_id']} {item['document_title']} [{item['locator']}, {item['evidence_id']}]: {item['text']}"
        )
    lines.extend(
        [
            "",
            "## 메모",
            f"- {tech_domain} 분야의 세부 범위는 DOC-TAX-001 기술분류표 기준이다.",
            "- 원본 기술분야 개요 PDF가 확보되면 이 proxy note는 교체 대상이다.",
            "",
        ]
    )
    return "\n".join(lines)


def build_plain_text(
    title: str,
    tech_domain: str,
    subdomains: list[str],
    source_lines: list[str],
    supporting_evidence: list[dict],
) -> str:
    lines = [
        title,
        "",
        "원문 미확보 상태에서 기존 코퍼스와 기술분류표를 바탕으로 생성한 proxy context note.",
        "",
        f"대분류: {tech_domain}",
        f"중분류 수: {len(subdomains)}",
        "",
        "중분류",
    ]
    for item in subdomains:
        lines.append(f"- {item}")
    lines.extend(["", "관련 정책 문서"])
    for line in source_lines:
        lines.append(f"- {line}")
    lines.extend(["", "대표 근거 문단"])
    for item in supporting_evidence:
        lines.append(
            f"- {item['document_id']} {item['document_title']} [{item['locator']}, {item['evidence_id']}]: {item['text']}"
        )
    lines.extend(
        [
            "",
            "메모",
            f"- {tech_domain} 분야의 세부 범위는 DOC-TAX-001 기술분류표 기준이다.",
            "- 원본 기술분야 개요 PDF가 확보되면 이 proxy note는 교체 대상이다.",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def build_proxy_taxonomy_table_payload(
    document_id: str,
    tech_domain: str,
    subdomains: list[str],
) -> tuple[dict, list[list[str]]]:
    table_id = f"TBL-{document_id}-PROXY-001"
    cell_matrix = [["중분류", "source_basis"]]
    cell_matrix.extend([[subdomain, "DOC-TAX-001 (proxy-derived)"] for subdomain in subdomains])
    payload = {
        "table_id": table_id,
        "document_id": document_id,
        "page_no_or_sheet_name": 1,
        "block_order": 1,
        "table_title": f"{tech_domain} 분야 proxy 중분류 목록",
        "header_rows": [1],
        "table_shape": {
            "rows": len(cell_matrix),
            "cols": 2,
        },
        "cell_matrix": cell_matrix,
        "merged_cell_info": [],
        "source_bbox": None,
        "extraction_confidence": "medium",
        "extraction_method": "derived-context-proxy-taxonomy-table-v1",
        "candidate_source": "proxy_taxonomy_summary",
        "review_required": True,
        "source_candidate_ids": ["DOC-TAX-001"],
        "tech_domain": tech_domain,
    }
    return payload, cell_matrix


def build_proxy_evidence_table_payload(
    document_id: str,
    tech_domain: str,
    supporting_evidence: list[dict],
) -> tuple[dict, list[list[str]]]:
    table_id = f"TBL-{document_id}-PROXY-002"
    cell_matrix = [["source_document_id", "locator", "evidence_id", "evidence_text"]]
    for item in supporting_evidence:
        cell_matrix.append(
            [
                item["document_id"],
                item["locator"],
                item["evidence_id"],
                item["text"],
            ]
        )
    payload = {
        "table_id": table_id,
        "document_id": document_id,
        "page_no_or_sheet_name": 1,
        "block_order": 2,
        "table_title": f"{tech_domain} 분야 proxy 근거 문단 매트릭스",
        "header_rows": [1],
        "table_shape": {
            "rows": len(cell_matrix),
            "cols": 4,
        },
        "cell_matrix": cell_matrix,
        "merged_cell_info": [],
        "source_bbox": None,
        "extraction_confidence": "medium",
        "extraction_method": "derived-context-proxy-evidence-matrix-v1",
        "candidate_source": "proxy_supporting_evidence_matrix",
        "review_required": True,
        "source_candidate_ids": sorted({item["document_id"] for item in supporting_evidence}),
        "tech_domain": tech_domain,
    }
    return payload, cell_matrix


def cleanup_outputs(document_id: str, text_dir: Path, manifest_dir: Path, table_dir: Path) -> None:
    for path in text_dir.glob(f"{document_id}*"):
        if path.is_file():
            path.unlink()
    for path in manifest_dir.glob(f"{document_id}*"):
        if path.is_file():
            path.unlink()
    for path in table_dir.glob(f"TBL-{document_id}-PROXY-*"):
        if path.is_file():
            path.unlink()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-root", required=True)
    args = parser.parse_args()

    out_root = Path(args.out_root)
    text_dir = out_root / "work/02_structured-extraction/text"
    manifest_dir = out_root / "work/02_structured-extraction/manifests"
    table_dir = out_root / "work/02_structured-extraction/tables"
    text_dir.mkdir(parents=True, exist_ok=True)
    manifest_dir.mkdir(parents=True, exist_ok=True)
    table_dir.mkdir(parents=True, exist_ok=True)

    seed_csv = out_root / "work/04_ontology/instances/documents_seed.csv"
    titles = load_document_titles(seed_csv)
    seed_rows = load_seed_rows(seed_csv)
    taxonomy_rows = load_taxonomy_rows(out_root / "work/03_processing/normalized/DOC-TAX-001__tech-domain-subdomain.csv")

    for config in PROXY_CONFIGS:
        document_id = config["document_id"]
        seed_row = seed_rows.get(document_id, {})
        if seed_row.get("source_rel_path") or seed_row.get("include_status") != "missing":
            continue
        tech_domain = config["tech_domain"]
        subdomains = taxonomy_rows.get(tech_domain, [])
        source_lines = [
            f"{source_doc} {titles.get(source_doc, source_doc)}"
            for source_doc in config["source_documents"]
        ]
        keywords = build_keyword_set(tech_domain, subdomains, config.get("extra_keywords", []))
        supporting_evidence = select_supporting_evidence(
            text_dir,
            titles,
            config["source_documents"],
            keywords,
        )

        cleanup_outputs(document_id, text_dir, manifest_dir, table_dir)

        markdown = build_markdown(config["title"], tech_domain, subdomains, source_lines, supporting_evidence)
        plain_text = build_plain_text(config["title"], tech_domain, subdomains, source_lines, supporting_evidence)
        taxonomy_table_payload, taxonomy_table_matrix = build_proxy_taxonomy_table_payload(
            document_id,
            tech_domain,
            subdomains,
        )
        evidence_table_payload, evidence_table_matrix = build_proxy_evidence_table_payload(
            document_id,
            tech_domain,
            supporting_evidence,
        )
        table_payloads = [
            (taxonomy_table_payload, taxonomy_table_matrix),
            (evidence_table_payload, evidence_table_matrix),
        ]
        table_entries = []
        for table_payload, table_matrix in table_payloads:
            table_id = table_payload["table_id"]
            table_json_path = table_dir / f"{table_id}.json"
            table_csv_path = table_dir / f"{table_id}.csv"
            write_json(table_json_path, table_payload)
            write_csv(table_csv_path, table_matrix)
            table_entries.append(
                {
                    "table_id": table_id,
                    "path": f"work/02_structured-extraction/tables/{table_json_path.name}",
                    "csv_path": f"work/02_structured-extraction/tables/{table_csv_path.name}",
                    "page_no": 1,
                    "rows": len(table_matrix),
                    "cols": len(table_matrix[0]) if table_matrix else 0,
                    "candidate_source": table_payload["candidate_source"],
                }
            )

        blocks = []
        block_order = 0
        for text in [
            config["title"],
            "원문 미확보 상태에서 기존 코퍼스와 기술분류표를 바탕으로 생성한 proxy context note.",
            f"대분류: {tech_domain}",
            "중분류",
            *[f"- {item}" for item in subdomains],
            "관련 정책 문서",
            *[f"- {line}" for line in source_lines],
            "대표 근거 문단",
            *[
                f"- {item['document_id']} {item['document_title']} [{item['locator']}, {item['evidence_id']}]: {item['text']}"
                for item in supporting_evidence
            ],
            "메모",
            f"- {tech_domain} 분야의 세부 범위는 DOC-TAX-001 기술분류표 기준이다.",
            "- 원본 기술분야 개요 PDF가 확보되면 이 proxy note는 교체 대상이다.",
        ]:
            block_order += 1
            blocks.append(
                {
                    "evidence_id": f"EVD-{document_id}-{block_order:05d}",
                    "document_id": document_id,
                    "page_no_or_sheet_name": 1,
                    "block_order": block_order,
                    "block_type": "derived_proxy_note",
                    "text": text,
                    "bbox": None,
                    "source_document_ids": config["source_documents"],
                    "extraction_method": "derived-context-proxy-from-taxonomy-and-corpus",
                    "extraction_confidence": "medium",
                    "page_no": 1,
                }
            )

        pages = [
            {
                "document_id": document_id,
                "page_no": 1,
                "metadata": {
                    "proxy_note": True,
                    "tech_domain": tech_domain,
                    "source_document_ids": config["source_documents"],
                },
                "toc_items": [],
                "tables": table_entries,
                "images": [],
                "graphics": [],
                "words": [],
                "text": plain_text.strip(),
                "extraction_method": "derived-context-proxy-from-taxonomy-and-corpus",
                "extraction_confidence": "medium",
            }
        ]

        write_text(text_dir / f"{document_id}.md", markdown)
        write_json(text_dir / f"{document_id}_pages.json", pages)
        write_json(text_dir / f"{document_id}_blocks.json", blocks)
        write_json(
            manifest_dir / f"{document_id}_manifest.json",
            {
                "document_id": document_id,
                "registry_id": document_id,
                "source_rel_path": "",
                "internal_path": "",
                "source_format": "pdf",
                "extraction_run_id": "derived-context-proxy-v2",
                "page_count_or_sheet_count": 1,
                "processing_status": "completed",
                "quality_notes": [
                    "Original source PDF is missing from the repository.",
                    "This artifact is a proxy note generated from DOC-TAX-001 plus related policy documents already present in the corpus.",
                    "Representative evidence snippets were pulled from relevant source documents to make the proxy note more usable.",
                    "Proxy taxonomy and evidence tables were materialized so downstream loaders can treat the missing context note like other extracted documents.",
                    "Replace this proxy with the original source extraction when the raw PDF is obtained.",
                ],
                "text_path": f"work/02_structured-extraction/text/{document_id}.md",
                "pages_path": f"work/02_structured-extraction/text/{document_id}_pages.json",
                "blocks_path": f"work/02_structured-extraction/text/{document_id}_blocks.json",
                "tables": table_entries,
                "counts": {
                    "page_chunks": 1,
                    "evidence_units": len(blocks),
                    "tables": len(table_entries),
                    "pages_with_tables_markdown": 0,
                    "pages_with_images_markdown": 0,
                    "proxy_note": True,
                    "supporting_evidence_snippets": len(supporting_evidence),
                },
                "source_document_ids": config["source_documents"],
                "supporting_evidence": supporting_evidence,
                "tech_domain": tech_domain,
            },
        )


if __name__ == "__main__":
    main()
