#!/usr/bin/env python3
"""Extract pure text and supporting layout metadata from a text-based PDF.

Primary text extraction uses PyMuPDF4LLM page chunks for better reading order.
Auxiliary block extraction uses PyMuPDF to preserve bounding boxes for later
layout-aware processing.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
import zipfile
from pathlib import Path


RUNTIME_PACKAGES = [
    ("numpy", "cp312-cp312-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl"),
    ("PyMuPDF", "cp310-abi3-manylinux_2_28_x86_64.whl"),
    ("pymupdf4llm", ".whl"),
    ("tabulate", ".whl"),
]


def ensure_runtime(loader_root: Path) -> None:
    lib_dir = loader_root / "lib"
    if (lib_dir / "pymupdf4llm").exists() and (lib_dir / "pymupdf").exists():
        sys.path.insert(0, str(lib_dir))
        return

    loader_root.mkdir(parents=True, exist_ok=True)
    lib_dir.mkdir(parents=True, exist_ok=True)

    for package_name, filename_marker in RUNTIME_PACKAGES:
        metadata = json.load(urllib.request.urlopen(f"https://pypi.org/pypi/{package_name}/json"))
        wheel_url = None
        wheel_name = None
        for item in metadata["urls"]:
            filename = item["filename"]
            if not filename.endswith(".whl"):
                continue
            if filename_marker == ".whl" or filename_marker in filename:
                wheel_url = item["url"]
                wheel_name = filename
                break
        if wheel_url is None or wheel_name is None:
            raise RuntimeError(f"Unable to resolve a compatible wheel for {package_name}.")

        wheel_path = loader_root / wheel_name
        if not wheel_path.exists():
            urllib.request.urlretrieve(wheel_url, wheel_path)

        with zipfile.ZipFile(wheel_path) as archive:
            archive.extractall(lib_dir)

    sys.path.insert(0, str(lib_dir))


def clean_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = "\n".join(line.rstrip() for line in text.splitlines())
    return text.strip()


def to_jsonable(value: object) -> object:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(item) for item in value]
    if hasattr(value, "tolist"):
        return to_jsonable(value.tolist())
    if hasattr(value, "__iter__") and not isinstance(value, (bytes, bytearray)):
        try:
            return [to_jsonable(item) for item in list(value)]
        except TypeError:
            pass
    return str(value)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(to_jsonable(payload), ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


def relative_or_absolute(path_str: str | None, root: Path) -> str:
    if not path_str:
        return ""
    path = Path(path_str)
    try:
        return str(path.relative_to(root))
    except ValueError:
        return path_str


def extract_pdf_bytes(source_pdf: str | None, source_zip: str | None, internal_path: str | None) -> bytes:
    if source_pdf:
        return Path(source_pdf).read_bytes()
    if source_zip and internal_path:
        with zipfile.ZipFile(source_zip) as outer_zip:
            return outer_zip.read(internal_path)
    raise ValueError("Either --source-pdf or --source-zip with --internal-path is required.")


def build_page_chunks(document_id: str, page_chunks: list[dict]) -> tuple[list[dict], str]:
    records = []
    markdown_parts = []

    for page_no, chunk in enumerate(page_chunks, start=1):
        text = clean_text(chunk.get("text", ""))
        record = {
            "document_id": document_id,
            "page_no": page_no,
            "metadata": chunk.get("metadata", {}),
            "toc_items": chunk.get("toc_items", []),
            "tables": chunk.get("tables", []),
            "images": chunk.get("images", []),
            "graphics": chunk.get("graphics", []),
            "words": chunk.get("words", []),
            "text": text,
            "extraction_method": "pymupdf4llm-to_markdown-page_chunks",
            "extraction_confidence": "high",
        }
        records.append(record)
        markdown_parts.append(f"<!-- page: {page_no} -->\n{text}\n")

    return records, "\n".join(markdown_parts).strip() + "\n"


def build_markdown_text(page_records: list[dict]) -> str:
    markdown_parts = []
    for page in page_records:
        page_no = page["page_no"]
        text = clean_text(page.get("text", ""))
        markdown_parts.append(f"<!-- page: {page_no} -->\n{text}\n")
    return "\n".join(markdown_parts).strip() + "\n"


def build_bbox_blocks(document_id: str, doc: object) -> tuple[list[dict], list[dict]]:
    import pymupdf  # type: ignore

    evidence_blocks = []
    layout_pages = []
    block_order = 0

    for page_no, page in enumerate(doc, start=1):
        page_dict = page.get_text("dict", sort=True)
        page_blocks = []

        for raw_block in page_dict.get("blocks", []):
            bbox = raw_block.get("bbox")
            block_type = raw_block.get("type")
            if block_type != 0:
                page_blocks.append(
                    {
                        "bbox": bbox,
                        "type": "non_text",
                    }
                )
                continue

            lines = []
            for line in raw_block.get("lines", []):
                line_text = "".join(span.get("text", "") for span in line.get("spans", []))
                if line_text:
                    lines.append(line_text)
            text = clean_text("\n".join(lines))
            if not text:
                continue

            block_order += 1
            evidence_id = f"EVD-{document_id}-{block_order:05d}"
            evidence_blocks.append(
                {
                    "evidence_id": evidence_id,
                    "document_id": document_id,
                    "page_no_or_sheet_name": page_no,
                    "block_order": block_order,
                    "block_type": "text_block",
                    "text": text,
                    "bbox": bbox,
                    "extraction_method": "pymupdf-text-dict-sort",
                    "extraction_confidence": "high",
                    "page_no": page_no,
                }
            )
            page_blocks.append(
                {
                    "bbox": bbox,
                    "type": "text",
                    "evidence_id": evidence_id,
                }
            )

        layout_pages.append(
            {
                "document_id": document_id,
                "page_no": page_no,
                "page_width": page.rect.width,
                "page_height": page.rect.height,
                "blocks": page_blocks,
            }
        )

    return evidence_blocks, layout_pages


def apply_page_text_fallback(page_records: list[dict], evidence_blocks: list[dict]) -> list[int]:
    blocks_by_page: dict[int, list[str]] = {}
    for block in evidence_blocks:
        page_no = int(block.get("page_no") or block.get("page_no_or_sheet_name") or 0)
        if page_no <= 0:
            continue
        text = clean_text(block.get("text", ""))
        if not text:
            continue
        blocks_by_page.setdefault(page_no, []).append(text)

    fallback_pages = []
    for record in page_records:
        page_no = int(record["page_no"])
        primary_text = clean_text(record.get("text", ""))
        fallback_text = clean_text("\n\n".join(blocks_by_page.get(page_no, [])))
        if not fallback_text:
            continue

        # Some Hancom-exported PDFs expose usable text blocks while the
        # pymupdf4llm page-chunk text is empty or only keeps the title line.
        use_fallback = not primary_text
        if primary_text and len(primary_text) < max(80, int(len(fallback_text) * 0.25)):
            use_fallback = True

        if not use_fallback:
            continue

        record["primary_text"] = primary_text
        record["text"] = fallback_text
        record["text_fallback_applied"] = True
        record["text_fallback_source"] = "pymupdf-text-dict-sort"
        record["text_fallback_reason"] = "empty_primary_text" if not primary_text else "sparse_primary_text"
        fallback_pages.append(page_no)

    return fallback_pages


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--document-id", required=True)
    parser.add_argument("--registry-id", required=True)
    parser.add_argument("--out-root", required=True)
    parser.add_argument("--source-pdf")
    parser.add_argument("--source-zip")
    parser.add_argument("--internal-path")
    args = parser.parse_args()

    out_root = Path(args.out_root)
    loader_root = out_root / "tmp" / "pymupdf4llm_loader"
    ensure_runtime(loader_root)

    import pymupdf  # type: ignore
    import pymupdf4llm  # type: ignore

    pdf_bytes = extract_pdf_bytes(args.source_pdf, args.source_zip, args.internal_path)
    temp_pdf = out_root / "tmp" / f"{args.document_id}.pdf"
    temp_pdf.parent.mkdir(parents=True, exist_ok=True)
    temp_pdf.write_bytes(pdf_bytes)

    text_dir = out_root / "work/02_structured-extraction/text"
    layout_dir = out_root / "work/02_structured-extraction/layout"
    manifest_dir = out_root / "work/02_structured-extraction/manifests"
    text_dir.mkdir(parents=True, exist_ok=True)
    layout_dir.mkdir(parents=True, exist_ok=True)
    manifest_dir.mkdir(parents=True, exist_ok=True)

    page_chunks = pymupdf4llm.to_markdown(
        str(temp_pdf),
        page_chunks=True,
        force_text=True,
        use_ocr=False,
    )
    page_records, markdown_text = build_page_chunks(args.document_id, page_chunks)

    doc = pymupdf.open(temp_pdf)
    evidence_blocks, layout_pages = build_bbox_blocks(args.document_id, doc)
    fallback_pages = apply_page_text_fallback(page_records, evidence_blocks)
    if fallback_pages:
        markdown_text = build_markdown_text(page_records)

    blocks_path = text_dir / f"{args.document_id}_blocks.json"
    pages_path = text_dir / f"{args.document_id}_pages.json"
    markdown_path = text_dir / f"{args.document_id}.md"
    layout_path = layout_dir / f"{args.document_id}_layout.json"

    write_json(blocks_path, evidence_blocks)
    write_json(pages_path, page_records)
    write_text(markdown_path, markdown_text)
    write_json(layout_path, layout_pages)

    manifest = {
        "document_id": args.document_id,
        "registry_id": args.registry_id,
        "source_rel_path": relative_or_absolute(args.source_pdf or args.source_zip, out_root),
        "internal_path": args.internal_path or "",
        "source_format": "pdf",
        "extraction_run_id": "pilot-gs-002-v3",
        "page_count_or_sheet_count": len(doc),
        "processing_status": "completed",
        "quality_notes": [
            "Primary pure-text path uses PyMuPDF4LLM page chunks in reading order.",
            "Auxiliary PyMuPDF text blocks preserve bounding boxes for later layout-aware processing.",
            "OCR disabled because the document exposes an embedded text layer.",
            "PyMuPDF4LLM layout ONNX stack was not enabled in this phase because pure-text extraction is the current priority.",
        ],
        "text_path": str(blocks_path.relative_to(out_root)),
        "page_text_path": str(pages_path.relative_to(out_root)),
        "markdown_path": str(markdown_path.relative_to(out_root)),
        "layout_path": str(layout_path.relative_to(out_root)),
        "counts": {
            "page_chunks": len(page_records),
            "evidence_units": len(evidence_blocks),
            "pages_with_tables_markdown": sum(1 for page in page_records if page["tables"]),
            "pages_with_images_markdown": sum(1 for page in page_records if page["images"]),
            "page_text_fallback_pages": len(fallback_pages),
        },
    }
    if fallback_pages:
        manifest["quality_notes"].append(
            "PyMuPDF4LLM page text was replaced with PyMuPDF block-order fallback on sparse/empty pages: "
            + ", ".join(str(page_no) for page_no in fallback_pages)
        )
    manifest_path = manifest_dir / f"{args.document_id}_manifest.json"
    write_json(manifest_path, manifest)


if __name__ == "__main__":
    main()
