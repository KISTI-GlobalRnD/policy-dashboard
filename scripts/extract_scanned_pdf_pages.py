#!/usr/bin/env python3
"""Create page-image assets and a manifest for scanned or image-heavy PDFs.

This is a pre-OCR extraction step. It renders page images and records whether
the source PDF contains a usable text layer.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
import zipfile
from pathlib import Path


def ensure_pymupdf(loader_root: Path) -> None:
    lib_dir = loader_root / "lib"
    if (lib_dir / "fitz").exists():
        sys.path.insert(0, str(lib_dir))
        return

    loader_root.mkdir(parents=True, exist_ok=True)
    metadata = json.load(urllib.request.urlopen("https://pypi.org/pypi/PyMuPDF/json"))
    wheel_url = None
    wheel_name = None
    for item in metadata["urls"]:
        filename = item["filename"]
        if "cp310-abi3-manylinux_2_28_x86_64.whl" in filename:
            wheel_url = item["url"]
            wheel_name = filename
            break
    if wheel_url is None or wheel_name is None:
        raise RuntimeError("Unable to resolve a compatible PyMuPDF wheel.")

    wheel_path = loader_root / wheel_name
    if not wheel_path.exists():
        urllib.request.urlretrieve(wheel_url, wheel_path)

    with zipfile.ZipFile(wheel_path) as archive:
        archive.extractall(lib_dir)

    sys.path.insert(0, str(lib_dir))


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--document-id", required=True)
    parser.add_argument("--registry-id", required=True)
    parser.add_argument("--out-root", required=True)
    args = parser.parse_args()

    out_root = Path(args.out_root)
    loader_root = out_root / "tmp" / "pymupdf_loader"
    ensure_pymupdf(loader_root)

    import fitz  # type: ignore

    source = Path(args.source)
    figures_dir = out_root / "work/02_structured-extraction/figures"
    figures_assets_dir = figures_dir / "assets" / args.document_id
    manifest_dir = out_root / "work/02_structured-extraction/manifests"
    text_dir = out_root / "work/02_structured-extraction/text"

    figures_assets_dir.mkdir(parents=True, exist_ok=True)
    manifest_dir.mkdir(parents=True, exist_ok=True)
    text_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(source)
    figure_outputs = []
    page_records = []
    text_layer_pages = 0

    for page_index, page in enumerate(doc, start=1):
        words = page.get_text("words")
        has_text_layer = bool(words)
        if has_text_layer:
            text_layer_pages += 1

        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
        asset_path = figures_assets_dir / f"page_{page_index:03d}.png"
        pix.save(str(asset_path))

        figure_id = f"FIG-{args.document_id}-{page_index:03d}"
        figure_payload = {
            "figure_id": figure_id,
            "document_id": args.document_id,
            "page_no": page_index,
            "figure_type": "pdf_page_image",
            "caption": f"Rendered page {page_index}",
            "legend_text": "",
            "summary": f"Rendered page image for OCR/manual review. text_layer={has_text_layer}",
            "asset_path": str(asset_path.relative_to(out_root)),
            "source_bbox": None,
            "extraction_confidence": "low",
            "extraction_method": "pymupdf-page-render",
            "text_layer_detected": has_text_layer,
        }
        figure_path = figures_dir / f"{figure_id}.json"
        write_json(figure_path, figure_payload)
        figure_outputs.append(str(figure_path.relative_to(out_root)))
        page_records.append(
            {
                "page_no": page_index,
                "asset_path": str(asset_path.relative_to(out_root)),
                "text_layer_detected": has_text_layer,
            }
        )

    text_stub_path = text_dir / f"{args.document_id}_blocks.json"
    write_json(
        text_stub_path,
        {
            "document_id": args.document_id,
            "status": "ocr_required",
            "blocks": [],
            "notes": [
                "No embedded text layer detected via PyMuPDF." if text_layer_pages == 0 else "Some text layer detected; OCR still recommended for consistency.",
                "Page images were rendered for later OCR/manual extraction.",
            ],
        },
    )

    manifest = {
        "document_id": args.document_id,
        "registry_id": args.registry_id,
        "source_rel_path": str(source),
        "internal_path": "",
        "source_format": "pdf",
        "extraction_run_id": "pilot-gs-001-preocr-v1",
        "page_count_or_sheet_count": len(doc),
        "processing_status": "partial_ocr_pending",
        "quality_notes": [
            f"Rendered {len(doc)} page images using PyMuPDF.",
            f"Text layer detected on {text_layer_pages} / {len(doc)} pages.",
            "OCR or manual table transcription is still required for text/table extraction.",
        ],
        "page_records": page_records,
        "text_output_path": str(text_stub_path.relative_to(out_root)),
        "figure_output_paths": figure_outputs,
    }
    manifest_path = manifest_dir / f"{args.document_id}_manifest.json"
    write_json(manifest_path, manifest)


if __name__ == "__main__":
    main()
