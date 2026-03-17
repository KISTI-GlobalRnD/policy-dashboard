#!/usr/bin/env python3
"""Extract structured content from an HWPX document stored inside a ZIP archive.

The environment is minimal, so this implementation uses only the Python
standard library and stores provenance using section/block order when page
numbers are not available.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from xml.etree import ElementTree as ET
from zipfile import ZipFile


HP_NS = "http://www.hancom.co.kr/hwpml/2011/paragraph"
HC_NS = "http://www.hancom.co.kr/hwpml/2011/core"
HS_NS = "http://www.hancom.co.kr/hwpml/2011/section"

HP = f"{{{HP_NS}}}"
HC = f"{{{HC_NS}}}"
HS = f"{{{HS_NS}}}"


def local_name(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[1]
    return tag


def clean_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def collect_text_excluding(node: ET.Element, excluded_tags: set[str]) -> str:
    if node.tag in excluded_tags:
        return ""
    parts: List[str] = []
    if node.tag == f"{HP}t" and node.text:
        parts.append(node.text)
    for child in list(node):
        if child.tag == f"{HP}fwSpace":
            parts.append(" ")
        elif child.tag == f"{HP}lineBreak":
            parts.append("\n")
        elif child.tag == f"{HP}tab":
            parts.append("\t")
        value = collect_text_excluding(child, excluded_tags)
        if value:
            parts.append(value)
        if child.tail:
            parts.append(child.tail)
    return "".join(parts)


def collect_cell_text(cell: ET.Element) -> str:
    paragraphs = []
    for paragraph in cell.iterfind(f".//{HP}p"):
        value = collect_text_excluding(paragraph, {f"{HP}tbl", f"{HP}pic", f"{HP}rect"})
        value = clean_text(value)
        if value:
            paragraphs.append(value)
    return "\n".join(paragraphs)


def find_binary_path(hwpx_zip: ZipFile, binary_id: str) -> Optional[str]:
    prefix = f"BinData/{binary_id}."
    for name in hwpx_zip.namelist():
        if name.startswith(prefix):
            return name
    return None


def extract_picture_info(pic: ET.Element, hwpx_zip: ZipFile, figures_assets_dir: Path) -> Tuple[dict, Optional[Path]]:
    img = pic.find(f"{HC}img")
    binary_id = img.attrib.get("binaryItemIDRef") if img is not None else None
    shape_comment = ""
    for node in pic.iter():
        if local_name(node.tag) == "shapeComment" and node.text:
            shape_comment = node.text
            break
    if binary_id:
        internal_path = find_binary_path(hwpx_zip, binary_id)
    else:
        internal_path = None

    asset_rel_path = None
    if internal_path is not None:
        asset_name = Path(internal_path).name
        asset_path = figures_assets_dir / asset_name
        asset_path.write_bytes(hwpx_zip.read(internal_path))
        asset_rel_path = asset_path

    figure_info = {
        "binary_item_id": binary_id,
        "internal_asset_path": internal_path or "",
        "shape_comment": clean_text(shape_comment),
        "original_name": "",
        "asset_path": "",
    }

    if shape_comment:
        for line in shape_comment.splitlines():
            if "원본 그림의 이름:" in line:
                figure_info["original_name"] = line.split(":", 1)[1].strip()
                break

    if asset_rel_path is not None:
        figure_info["asset_path"] = str(asset_rel_path)

    return figure_info, asset_rel_path


def parse_table(tbl: ET.Element) -> dict:
    row_cnt = int(tbl.attrib.get("rowCnt", "0"))
    col_cnt = int(tbl.attrib.get("colCnt", "0"))
    matrix = [["" for _ in range(col_cnt)] for _ in range(row_cnt)]
    merged_cell_info = []

    for cell in tbl.iterfind(f".//{HP}tc"):
        addr = cell.find(f"{HP}cellAddr")
        span = cell.find(f"{HP}cellSpan")
        if addr is None:
            continue
        row_idx = int(addr.attrib.get("rowAddr", "0"))
        col_idx = int(addr.attrib.get("colAddr", "0"))
        row_span = int(span.attrib.get("rowSpan", "1")) if span is not None else 1
        col_span = int(span.attrib.get("colSpan", "1")) if span is not None else 1
        cell_text = collect_cell_text(cell)
        if 0 <= row_idx < row_cnt and 0 <= col_idx < col_cnt:
            matrix[row_idx][col_idx] = cell_text
        if row_span > 1 or col_span > 1:
            merged_cell_info.append(
                {
                    "row_index": row_idx,
                    "col_index": col_idx,
                    "row_span": row_span,
                    "col_span": col_span,
                }
            )

    return {
        "row_count": row_cnt,
        "col_count": col_cnt,
        "cell_matrix": matrix,
        "merged_cell_info": merged_cell_info,
        "repeat_header": tbl.attrib.get("repeatHeader"),
        "treat_as_char": tbl.find(f"{HP}pos").attrib.get("treatAsChar") if tbl.find(f"{HP}pos") is not None else "",
        "text_wrap": tbl.attrib.get("textWrap", ""),
    }


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def relative_or_absolute(path_str: str | None, root: Path) -> str:
    if not path_str:
        return ""
    path = Path(path_str)
    try:
        return str(path.relative_to(root))
    except ValueError:
        return path_str


def extract_shape_text(rect: ET.Element) -> str:
    return clean_text(collect_text_excluding(rect, set()))


def extract_hwpx_bytes(source_hwpx: str | None, source_zip: str | None, internal_path: str | None) -> bytes:
    if source_hwpx:
        return Path(source_hwpx).read_bytes()
    if source_zip and internal_path:
        with ZipFile(source_zip) as outer_zip:
            return outer_zip.read(internal_path)
    raise ValueError("Either --source-hwpx or --source-zip with --internal-path is required.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--document-id", required=True)
    parser.add_argument("--registry-id", required=True)
    parser.add_argument("--out-root", required=True)
    parser.add_argument("--source-hwpx")
    parser.add_argument("--source-zip")
    parser.add_argument("--internal-path")
    args = parser.parse_args()

    out_root = Path(args.out_root)
    text_dir = out_root / "work/02_structured-extraction/text"
    table_dir = out_root / "work/02_structured-extraction/tables"
    figure_dir = out_root / "work/02_structured-extraction/figures"
    figure_assets_dir = figure_dir / "assets" / args.document_id
    layout_dir = out_root / "work/02_structured-extraction/layout"
    manifest_dir = out_root / "work/02_structured-extraction/manifests"

    text_dir.mkdir(parents=True, exist_ok=True)
    table_dir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)
    figure_assets_dir.mkdir(parents=True, exist_ok=True)
    layout_dir.mkdir(parents=True, exist_ok=True)
    manifest_dir.mkdir(parents=True, exist_ok=True)

    for path in text_dir.glob(f"{args.document_id}*"):
        if path.is_file():
            path.unlink()
    for path in layout_dir.glob(f"{args.document_id}*"):
        if path.is_file():
            path.unlink()
    for path in manifest_dir.glob(f"{args.document_id}*"):
        if path.is_file():
            path.unlink()
    for path in table_dir.glob(f"TBL-{args.document_id}-*.json"):
        path.unlink()
    for path in figure_dir.glob(f"FIG-{args.document_id}-*.json"):
        path.unlink()
    if figure_assets_dir.exists():
        shutil.rmtree(figure_assets_dir)
    figure_assets_dir.mkdir(parents=True, exist_ok=True)

    text_blocks = []
    tables_written = []
    figures_written = []
    layout_sections = []

    hwpx_bytes = extract_hwpx_bytes(args.source_hwpx, args.source_zip, args.internal_path)
    temp_hwpx = out_root / "tmp" / f"{args.document_id}.hwpx"
    temp_hwpx.parent.mkdir(parents=True, exist_ok=True)
    temp_hwpx.write_bytes(hwpx_bytes)

    with ZipFile(temp_hwpx) as hwpx_zip:
        section_names = sorted(
            name
            for name in hwpx_zip.namelist()
            if name.startswith("Contents/section") and name.endswith(".xml")
        )

        block_order = 0
        table_count = 0
        figure_count = 0

        for section_name in section_names:
            section_xml = hwpx_zip.read(section_name)
            root = ET.fromstring(section_xml)
            section_label = Path(section_name).stem
            page_pr = root.find(f".//{HP}pagePr")
            layout_sections.append(
                {
                    "section_name": section_label,
                    "source_path": section_name,
                    "page_width": page_pr.attrib.get("width", "") if page_pr is not None else "",
                    "page_height": page_pr.attrib.get("height", "") if page_pr is not None else "",
                }
            )

            for paragraph in root.findall(f"{HP}p"):
                paragraph_text = clean_text(
                    collect_text_excluding(paragraph, {f"{HP}tbl", f"{HP}pic", f"{HP}rect"})
                )
                if paragraph_text:
                    block_order += 1
                    text_blocks.append(
                        {
                            "evidence_id": f"EVD-{args.document_id}-{block_order:05d}",
                            "document_id": args.document_id,
                            "page_no_or_sheet_name": section_label,
                            "block_order": block_order,
                            "block_type": "paragraph",
                            "text": paragraph_text,
                            "bbox": None,
                            "extraction_method": "hwpx-xml-parser",
                            "extraction_confidence": "high",
                            "paragraph_id": paragraph.attrib.get("id", ""),
                        }
                    )

                for run in paragraph.findall(f"{HP}run"):
                    for child in list(run):
                        if child.tag == f"{HP}rect":
                            shape_text = extract_shape_text(child)
                            if shape_text:
                                block_order += 1
                                text_blocks.append(
                                    {
                                        "evidence_id": f"EVD-{args.document_id}-{block_order:05d}",
                                        "document_id": args.document_id,
                                        "page_no_or_sheet_name": section_label,
                                        "block_order": block_order,
                                        "block_type": "shape_text",
                                        "text": shape_text,
                                        "bbox": None,
                                        "extraction_method": "hwpx-xml-parser",
                                        "extraction_confidence": "medium",
                                        "paragraph_id": paragraph.attrib.get("id", ""),
                                    }
                                )
                        elif child.tag == f"{HP}tbl":
                            block_order += 1
                            table_count += 1
                            table_id = f"TBL-{args.document_id}-{table_count:03d}"
                            parsed = parse_table(child)
                            table_payload = {
                                "table_id": table_id,
                                "document_id": args.document_id,
                                "page_no_or_sheet_name": section_label,
                                "block_order": block_order,
                                "table_title": "",
                                "header_rows": [1] if parsed["row_count"] else [],
                                "table_shape": {
                                    "rows": parsed["row_count"],
                                    "cols": parsed["col_count"],
                                },
                                "cell_matrix": parsed["cell_matrix"],
                                "merged_cell_info": parsed["merged_cell_info"],
                                "source_bbox": None,
                                "extraction_confidence": "high",
                                "extraction_method": "hwpx-xml-parser",
                                "paragraph_id": paragraph.attrib.get("id", ""),
                                "source_table_id": child.attrib.get("id", ""),
                                "repeat_header": parsed["repeat_header"],
                                "treat_as_char": parsed["treat_as_char"],
                                "text_wrap": parsed["text_wrap"],
                            }
                            table_path = table_dir / f"{table_id}.json"
                            write_json(table_path, table_payload)
                            tables_written.append(
                                {
                                    "table_id": table_id,
                                    "path": str(table_path.relative_to(out_root)),
                                    "section_name": section_label,
                                    "rows": parsed["row_count"],
                                    "cols": parsed["col_count"],
                                }
                            )
                            for picture in child.findall(f".//{HP}pic"):
                                block_order += 1
                                figure_count += 1
                                figure_id = f"FIG-{args.document_id}-{figure_count:03d}"
                                figure_info, asset_path = extract_picture_info(picture, hwpx_zip, figure_assets_dir)
                                figure_payload = {
                                    "figure_id": figure_id,
                                    "document_id": args.document_id,
                                    "page_no": None,
                                    "page_no_or_sheet_name": section_label,
                                    "block_order": block_order,
                                    "figure_type": "image",
                                    "caption": figure_info["shape_comment"],
                                    "legend_text": "",
                                    "summary": figure_info["original_name"] or figure_info["shape_comment"],
                                    "asset_path": str(asset_path.relative_to(out_root)) if asset_path is not None else "",
                                    "source_bbox": None,
                                    "extraction_confidence": "medium",
                                    "extraction_method": "hwpx-xml-parser",
                                    "paragraph_id": paragraph.attrib.get("id", ""),
                                    "parent_table_id": table_id,
                                    "binary_item_id": figure_info["binary_item_id"],
                                    "internal_asset_path": figure_info["internal_asset_path"],
                                }
                                figure_path = figure_dir / f"{figure_id}.json"
                                write_json(figure_path, figure_payload)
                                figures_written.append(
                                    {
                                        "figure_id": figure_id,
                                        "path": str(figure_path.relative_to(out_root)),
                                        "asset_path": str(asset_path.relative_to(out_root)) if asset_path is not None else "",
                                        "section_name": section_label,
                                    }
                                )
                        elif child.tag == f"{HP}pic":
                            block_order += 1
                            figure_count += 1
                            figure_id = f"FIG-{args.document_id}-{figure_count:03d}"
                            figure_info, asset_path = extract_picture_info(child, hwpx_zip, figure_assets_dir)
                            figure_payload = {
                                "figure_id": figure_id,
                                "document_id": args.document_id,
                                "page_no": None,
                                "page_no_or_sheet_name": section_label,
                                "block_order": block_order,
                                "figure_type": "image",
                                "caption": figure_info["shape_comment"],
                                "legend_text": "",
                                "summary": figure_info["original_name"] or figure_info["shape_comment"],
                                "asset_path": str(asset_path.relative_to(out_root)) if asset_path is not None else "",
                                "source_bbox": None,
                                "extraction_confidence": "medium",
                                "extraction_method": "hwpx-xml-parser",
                                "paragraph_id": paragraph.attrib.get("id", ""),
                                "binary_item_id": figure_info["binary_item_id"],
                                "internal_asset_path": figure_info["internal_asset_path"],
                            }
                            figure_path = figure_dir / f"{figure_id}.json"
                            write_json(figure_path, figure_payload)
                            figures_written.append(
                                {
                                    "figure_id": figure_id,
                                    "path": str(figure_path.relative_to(out_root)),
                                    "asset_path": str(asset_path.relative_to(out_root)) if asset_path is not None else "",
                                    "section_name": section_label,
                                }
                            )

    text_path = text_dir / f"{args.document_id}_blocks.json"
    write_json(text_path, text_blocks)
    layout_path = layout_dir / f"{args.document_id}_layout.json"
    write_json(
        layout_path,
        {
            "document_id": args.document_id,
            "sections": layout_sections,
        },
    )

    manifest = {
        "document_id": args.document_id,
        "registry_id": args.registry_id,
        "source_rel_path": relative_or_absolute(args.source_hwpx or args.source_zip, out_root),
        "internal_path": args.internal_path or "",
        "source_format": "hwpx",
        "extraction_run_id": "pilot-gs-003-v1",
        "page_count_or_sheet_count": len(layout_sections),
        "processing_status": "completed",
        "quality_notes": [
            "HWPX extracted from the outer ZIP archive.",
            "Only top-level paragraphs were treated as body blocks to avoid nested table duplication.",
            "Page numbers were not reconstructed; section and block order are used as provenance.",
        ],
        "text_path": str(text_path.relative_to(out_root)),
        "layout_path": str(layout_path.relative_to(out_root)),
        "tables": tables_written,
        "figures": figures_written,
        "counts": {
            "evidence_units": len(text_blocks),
            "tables": len(tables_written),
            "figures": len(figures_written),
        },
    }
    manifest_path = manifest_dir / f"{args.document_id}_manifest.json"
    write_json(manifest_path, manifest)


if __name__ == "__main__":
    main()
