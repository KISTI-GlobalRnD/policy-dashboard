#!/usr/bin/env python3
"""Finalize cropped raw context-note PDFs into plain-text page outputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


TARGET_DOCUMENT_IDS = ["DOC-CTX-012", "DOC-CTX-013", "DOC-CTX-014"]


def clean_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = "\n".join(line.rstrip() for line in text.splitlines())
    return text.strip()


def build_markdown(page_records: list[dict]) -> str:
    chunks = []
    for page in page_records:
        chunks.append(f"<!-- page: {page['page_no']} -->\n{clean_text(page.get('text', ''))}\n")
    return "\n".join(chunks).strip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-root", required=True)
    parser.add_argument("--documents", nargs="*", default=TARGET_DOCUMENT_IDS)
    args = parser.parse_args()

    out_root = Path(args.out_root)
    text_dir = out_root / "work/02_structured-extraction/text"
    manifest_dir = out_root / "work/02_structured-extraction/manifests"
    table_dir = out_root / "work/02_structured-extraction/tables"

    for document_id in args.documents:
        blocks_path = text_dir / f"{document_id}_blocks.json"
        pages_path = text_dir / f"{document_id}_pages.json"
        markdown_path = text_dir / f"{document_id}.md"
        manifest_path = manifest_dir / f"{document_id}_manifest.json"
        if not (blocks_path.exists() and pages_path.exists() and manifest_path.exists()):
            continue

        block_payload = json.loads(blocks_path.read_text(encoding="utf-8"))
        blocks = block_payload if isinstance(block_payload, list) else block_payload.get("blocks", [])
        pages = json.loads(pages_path.read_text(encoding="utf-8"))
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        blocks_by_page: dict[int, list[str]] = {}
        for block in blocks:
            page_no = int(block.get("page_no") or block.get("page_no_or_sheet_name") or 0)
            if page_no <= 0:
                continue
            text = clean_text(block.get("text", ""))
            if not text:
                continue
            blocks_by_page.setdefault(page_no, []).append(text)

        for page in pages:
            page_no = int(page["page_no"])
            fallback_text = clean_text("\n\n".join(blocks_by_page.get(page_no, [])))
            if not fallback_text:
                continue
            page["primary_text"] = page.get("text", "")
            page["text"] = fallback_text
            page["tables"] = []
            page["text_fallback_applied"] = True
            page["text_fallback_source"] = "pymupdf-text-dict-sort"
            page["text_fallback_reason"] = "cropped_context_section_placeholder_markdown"

        pages_path.write_text(json.dumps(pages, ensure_ascii=False, indent=2), encoding="utf-8")
        markdown_path.write_text(build_markdown(pages), encoding="utf-8")

        counts = manifest.setdefault("counts", {})
        counts["pages_with_tables_markdown"] = 0
        counts["page_text_fallback_pages"] = len(pages)
        quality_notes = manifest.setdefault("quality_notes", [])
        note = (
            "Cropped PACST section pages were post-processed from PyMuPDF block text to remove "
            "placeholder 2-column markdown table artifacts."
        )
        if note not in quality_notes:
            quality_notes.append(note)
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

        for path in table_dir.glob(f"TBL-{document_id}-PROXY-*"):
            if path.is_file():
                path.unlink()


if __name__ == "__main__":
    main()
