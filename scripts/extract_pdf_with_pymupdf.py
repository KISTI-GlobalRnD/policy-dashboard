#!/usr/bin/env python3
"""Extract text blocks, images, optional tables, and layout metadata from a PDF.

PyMuPDF is bootstrapped from a wheel on first run because the base environment
does not provide it.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path


def ensure_pymupdf() -> None:
    try:
        import fitz  # noqa: F401
        return
    except ImportError:
        pass

    base = Path("/tmp/pymupdf_loader")
    base.mkdir(parents=True, exist_ok=True)
    wheel = None
    data = json.load(urllib.request.urlopen("https://pypi.org/pypi/PyMuPDF/json"))
    for item in data["urls"]:
        filename = item["filename"]
        if "cp310-abi3-manylinux_2_28_x86_64.whl" in filename:
            wheel = base / filename
            if not wheel.exists():
                urllib.request.urlretrieve(item["url"], wheel)
            break
    if wheel is None:
        raise RuntimeError("Unable to locate a compatible PyMuPDF wheel.")

    lib_dir = base / "lib"
    if not (lib_dir / "fitz").exists():
        with zipfile.ZipFile(wheel) as zf:
            zf.extractall(lib_dir)
    sys.path.insert(0, str(lib_dir))


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def cleanup_outputs(document_id: str, text_dir: Path, table_dir: Path, figure_dir: Path, layout_dir: Path, manifest_dir: Path) -> None:
    for target_dir in [text_dir, layout_dir, manifest_dir]:
        for path in target_dir.glob(f"{document_id}*"):
            if path.is_file():
                path.unlink()
    for path in table_dir.glob(f"TBL-{document_id}-*.json"):
        path.unlink()
    for path in figure_dir.glob(f"FIG-{document_id}-*.json"):
        path.unlink()
    asset_dir = figure_dir / "assets" / document_id
    if asset_dir.exists():
        shutil.rmtree(asset_dir)
    asset_dir.mkdir(parents=True, exist_ok=True)


def extract_pdf_bytes(source_pdf: str | None, source_zip: str | None, internal_path: str | None) -> bytes:
    if source_pdf:
        return Path(source_pdf).read_bytes()
    if source_zip and internal_path:
        with zipfile.ZipFile(source_zip) as zf:
            return zf.read(internal_path)
    raise ValueError("Either --source-pdf or --source-zip with --internal-path is required.")


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
    text_dir = out_root / "work/02_structured-extraction/text"
    table_dir = out_root / "work/02_structured-extraction/tables"
    figure_dir = out_root / "work/02_structured-extraction/figures"
    layout_dir = out_root / "work/02_structured-extraction/layout"
    manifest_dir = out_root / "work/02_structured-extraction/manifests"
    cleanup_outputs(args.document_id, text_dir, table_dir, figure_dir, layout_dir, manifest_dir)
    asset_dir = figure_dir / "assets" / args.document_id

    ensure_pymupdf()
    import fitz

    pdf_bytes = extract_pdf_bytes(args.source_pdf, args.source_zip, args.internal_path)
    temp_pdf = out_root / "tmp" / f"{args.document_id}.pdf"
    temp_pdf.parent.mkdir(parents=True, exist_ok=True)
    temp_pdf.write_bytes(pdf_bytes)

    doc = fitz.open(temp_pdf)

    evidence_units = []
    tables = []
    figures = []
    layout_pages = []
    block_counter = 0
    table_counter = 0
    figure_counter = 0

    for page_index in range(len(doc)):
        page = doc[page_index]
        page_no = page_index + 1
        layout_pages.append(
            {
                "page_no": page_no,
                "page_width": page.rect.width,
                "page_height": page.rect.height,
            }
        )

        for block in page.get_text("blocks"):
            x0, y0, x1, y1, text, block_no, block_type = block
            text = (text or "").strip()
            if not text:
                continue
            block_counter += 1
            evidence_units.append(
                {
                    "evidence_id": f"EVD-{args.document_id}-{block_counter:05d}",
                    "document_id": args.document_id,
                    "page_no_or_sheet_name": page_no,
                    "block_order": block_counter,
                    "block_type": "text_block" if block_type == 0 else "image_block",
                    "text": text,
                    "bbox": [x0, y0, x1, y1],
                    "extraction_method": "pymupdf-text-blocks",
                    "extraction_confidence": "high",
                    "page_block_no": block_no,
                }
            )

        if hasattr(page, "find_tables"):
            found = page.find_tables()
            for table in found.tables:
                table_counter += 1
                table_id = f"TBL-{args.document_id}-{table_counter:03d}"
                try:
                    cell_matrix = table.extract()
                except Exception:
                    cell_matrix = []
                rows = len(cell_matrix)
                cols = max((len(row) for row in cell_matrix), default=0)
                table_payload = {
                    "table_id": table_id,
                    "document_id": args.document_id,
                    "page_no_or_sheet_name": page_no,
                    "block_order": block_counter + 1,
                    "table_title": "",
                    "header_rows": [1] if rows else [],
                    "table_shape": {"rows": rows, "cols": cols},
                    "cell_matrix": cell_matrix,
                    "merged_cell_info": [],
                    "source_bbox": list(table.bbox) if getattr(table, "bbox", None) else None,
                    "extraction_confidence": "medium",
                    "extraction_method": "pymupdf-find_tables",
                }
                table_path = table_dir / f"{table_id}.json"
                write_json(table_path, table_payload)
                tables.append(
                    {
                        "table_id": table_id,
                        "path": str(table_path.relative_to(out_root)),
                        "page_no": page_no,
                        "rows": rows,
                        "cols": cols,
                    }
                )

        seen_xrefs = set()
        for image_info in page.get_images(full=True):
            xref = image_info[0]
            if xref in seen_xrefs:
                continue
            seen_xrefs.add(xref)
            figure_counter += 1
            figure_id = f"FIG-{args.document_id}-{figure_counter:03d}"
            image_data = doc.extract_image(xref)
            ext = image_data.get("ext", "bin")
            asset_path = asset_dir / f"{figure_id}.{ext}"
            asset_path.write_bytes(image_data["image"])
            figure_payload = {
                "figure_id": figure_id,
                "document_id": args.document_id,
                "page_no": page_no,
                "page_no_or_sheet_name": page_no,
                "block_order": block_counter + 1,
                "figure_type": "image",
                "caption": "",
                "legend_text": "",
                "summary": image_data.get("smask", ""),
                "asset_path": str(asset_path.relative_to(out_root)),
                "source_bbox": None,
                "extraction_confidence": "medium",
                "extraction_method": "pymupdf-images",
                "xref": xref,
                "width": image_data.get("width"),
                "height": image_data.get("height"),
            }
            figure_path = figure_dir / f"{figure_id}.json"
            write_json(figure_path, figure_payload)
            figures.append(
                {
                    "figure_id": figure_id,
                    "path": str(figure_path.relative_to(out_root)),
                    "asset_path": str(asset_path.relative_to(out_root)),
                    "page_no": page_no,
                }
            )

    text_path = text_dir / f"{args.document_id}_blocks.json"
    layout_path = layout_dir / f"{args.document_id}_layout.json"
    write_json(text_path, evidence_units)
    write_json(
        layout_path,
        {
            "document_id": args.document_id,
            "pages": layout_pages,
        },
    )

    manifest = {
        "document_id": args.document_id,
        "registry_id": args.registry_id,
        "source_rel_path": args.source_pdf or args.source_zip,
        "internal_path": args.internal_path or "",
        "source_format": "pdf",
        "extraction_run_id": "pilot-gs-002-v1",
        "page_count_or_sheet_count": len(layout_pages),
        "processing_status": "completed",
        "quality_notes": [
            "PDF extracted with PyMuPDF text blocks.",
            "Table extraction depends on page.find_tables() and may miss visually implied tables.",
            "Image extraction is based on embedded image xrefs.",
        ],
        "text_path": str(text_path.relative_to(out_root)),
        "layout_path": str(layout_path.relative_to(out_root)),
        "tables": tables,
        "figures": figures,
        "counts": {
            "evidence_units": len(evidence_units),
            "tables": len(tables),
            "figures": len(figures),
        },
    }
    manifest_path = manifest_dir / f"{args.document_id}_manifest.json"
    write_json(manifest_path, manifest)


if __name__ == "__main__":
    main()
