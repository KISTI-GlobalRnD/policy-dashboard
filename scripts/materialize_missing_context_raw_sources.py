#!/usr/bin/env python3
"""Replace missing context-note proxies with source-backed official PDF crops."""

from __future__ import annotations

import argparse
import csv
import json
import urllib.request
from pathlib import Path

from run_support_document_extraction_batch import ensure_pymupdf


OFFICIAL_SOURCE_URL = (
    "https://www.pacst.go.kr/jsp/common/download.jsp"
    "?param1=GcP08V2DuYJSEFxi1PB%2BJw%3D%3D"
    "&param2=xBT8RH4eVRh7O%2FDTVo1yBG8ojH6mw8v6TbkhoFu891SqjaxhSc23MfDTlR0De8vCuQDd3mbZ2vdb%0A"
    "yrlad1GTDSZpRjHVq7kSbPr%2Bk2ADBn2TBrW4FFpsmZtcLxDUYj0Shp4lLObQXbtZ%2FgI0Pm8ullKi%0A"
    "fZgLWUPVUILqgQzfR3k%3D"
)
OFFICIAL_SOURCE_REL_PATH = "data/2026-03-17_pacst_68-4_2025-implementation-plan.pdf"

SECTION_CONFIGS = [
    {
        "document_id": "DOC-CTX-012",
        "section_title": "인공지능",
        "page_no": 208,
        "clip_rect": [40, 50, 565, 380],
        "source_rel_path": "data/2026-03-17_missing-context-raw-sources/DOC-CTX-012__pacst-68-4-page-208.pdf",
    },
    {
        "document_id": "DOC-CTX-013",
        "section_title": "첨단 로봇·제조",
        "page_no": 235,
        "clip_rect": [40, 338, 565, 460],
        "source_rel_path": "data/2026-03-17_missing-context-raw-sources/DOC-CTX-013__pacst-68-4-page-235.pdf",
    },
    {
        "document_id": "DOC-CTX-014",
        "section_title": "반도체·디스플레이",
        "page_no": 232,
        "clip_rect": [40, 50, 565, 332],
        "source_rel_path": "data/2026-03-17_missing-context-raw-sources/DOC-CTX-014__pacst-68-4-page-232.pdf",
    },
]


def read_csv_rows(path: Path) -> tuple[list[dict], list[str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader), list(reader.fieldnames or [])


def write_csv_rows(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def download_official_pdf(out_root: Path) -> Path:
    target_path = out_root / OFFICIAL_SOURCE_REL_PATH
    target_path.parent.mkdir(parents=True, exist_ok=True)
    if not target_path.exists():
        urllib.request.urlretrieve(OFFICIAL_SOURCE_URL, target_path)
    return target_path


def build_cropped_pdf(out_root: Path, source_pdf: Path, page_no: int, clip_rect: list[float], output_path: Path) -> None:
    loader_root = out_root / "tmp" / "pymupdf_loader"
    ensure_pymupdf(loader_root)

    import fitz  # type: ignore

    output_path.parent.mkdir(parents=True, exist_ok=True)
    src = fitz.open(source_pdf)
    try:
        page_index = page_no - 1
        clip = fitz.Rect(*clip_rect)
        out = fitz.open()
        try:
            new_page = out.new_page(width=clip.width, height=clip.height)
            new_page.show_pdf_page(new_page.rect, src, page_index, clip=clip)
            out.save(output_path)
        finally:
            out.close()
    finally:
        src.close()


def update_registry_csv(path: Path, run_date: str) -> list[dict]:
    rows, fieldnames = read_csv_rows(path)
    updated = []
    for row in rows:
        document_id = row.get("registry_id") or row.get("document_id")
        matched = next((cfg for cfg in SECTION_CONFIGS if cfg["document_id"] == document_id), None)
        if matched is None:
            continue
        row["include_status"] = "support"
        row["source_rel_path"] = matched["source_rel_path"]
        if "internal_path" in row:
            row["internal_path"] = ""
        row["source_format"] = "pdf"
        row["issuing_org"] = "국가과학기술자문회의"
        row["issued_date"] = "2025-03-13"
        row["notes"] = (
            "PACST 68-4 공식 PDF에서 해당 기술분야 섹션을 발췌한 source-backed raw context note; "
            f"{run_date} raw source replacement (page {matched['page_no']}, section {matched['section_title']})"
        )
        updated.append(
            {
                "document_id": matched["document_id"],
                "source_rel_path": matched["source_rel_path"],
                "page_no": matched["page_no"],
                "section_title": matched["section_title"],
            }
        )
    write_csv_rows(path, rows, fieldnames)
    return updated


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-root", required=True)
    parser.add_argument("--run-date", default="2026-03-17")
    args = parser.parse_args()

    out_root = Path(args.out_root)
    run_date = args.run_date
    official_source_path = download_official_pdf(out_root)

    replacements = []
    for config in SECTION_CONFIGS:
        output_path = out_root / config["source_rel_path"]
        build_cropped_pdf(
            out_root,
            official_source_path,
            config["page_no"],
            config["clip_rect"],
            output_path,
        )
        replacements.append(
            {
                "document_id": config["document_id"],
                "section_title": config["section_title"],
                "page_no": config["page_no"],
                "source_rel_path": config["source_rel_path"],
                "official_source_rel_path": OFFICIAL_SOURCE_REL_PATH,
            }
        )

    registry_updates = update_registry_csv(
        out_root / "work/01_scope-and-ia/requirements/04_document-registry.csv",
        run_date,
    )
    seed_updates = update_registry_csv(
        out_root / "work/04_ontology/instances/documents_seed.csv",
        run_date,
    )

    write_json(
        out_root / f"qa/extraction/{run_date}_missing-context-source-replacement.json",
        {
            "run_date": run_date,
            "official_source_url": OFFICIAL_SOURCE_URL,
            "official_source_rel_path": OFFICIAL_SOURCE_REL_PATH,
            "replacement_count": len(replacements),
            "replacements": replacements,
            "registry_updates": registry_updates,
            "seed_updates": seed_updates,
        },
    )


if __name__ == "__main__":
    main()
