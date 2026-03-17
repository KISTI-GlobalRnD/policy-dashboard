#!/usr/bin/env python3
"""Extract structured content from a DOCX document.

This is a text-first OOXML parser for converted Word documents. It preserves:
- body paragraph order
- table cell structure
- embedded image assets

Provenance is section-order based because page numbers are not reliably
recoverable from converted DOCX files.
"""

from __future__ import annotations

import argparse
import json
import shutil
from collections import defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
V_NS = "urn:schemas-microsoft-com:vml"

W = f"{{{W_NS}}}"
R = f"{{{R_NS}}}"
REL = f"{{{REL_NS}}}"
A = f"{{{A_NS}}}"
V = f"{{{V_NS}}}"


def clean_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = text.replace("\r", "\n")
    text = text.replace("\t", " ")
    text = text.replace("\u00ad", "")
    text = text.replace("\u2011", "-")
    text = text.replace("\u2028", "\n")
    text = text.replace("\u2029", "\n")
    text = "\n".join(line.strip() for line in text.splitlines())
    text = text.replace("\n\n\n", "\n\n")
    text = " ".join(text.split())
    return text.strip()


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


def cleanup_outputs(document_id: str, text_dir: Path, table_dir: Path, figure_dir: Path, layout_dir: Path, manifest_dir: Path) -> None:
    for target_dir in [text_dir, table_dir, layout_dir, manifest_dir]:
        for path in target_dir.glob(f"{document_id}*"):
            if path.is_file():
                path.unlink()
    figure_assets_dir = figure_dir / "assets" / document_id
    if figure_assets_dir.exists():
        shutil.rmtree(figure_assets_dir)


def load_relationships(docx_zip: ZipFile) -> dict[str, str]:
    rels_path = "word/_rels/document.xml.rels"
    if rels_path not in docx_zip.namelist():
        return {}
    root = ET.fromstring(docx_zip.read(rels_path))
    mapping: dict[str, str] = {}
    for rel in root.findall(f"{REL}Relationship"):
        rel_id = rel.attrib.get("Id", "")
        target = rel.attrib.get("Target", "")
        if rel_id and target:
            mapping[rel_id] = target
    return mapping


def paragraph_text(paragraph: ET.Element) -> str:
    parts: list[str] = []
    for node in paragraph.iter():
        if node.tag == f"{W}t" and node.text:
            parts.append(node.text)
        elif node.tag == f"{W}tab":
            parts.append(" ")
        elif node.tag in {f"{W}br", f"{W}cr"}:
            parts.append("\n")
        elif node.tag == f"{W}noBreakHyphen":
            parts.append("-")
    return clean_text("".join(parts))


def extract_table(tbl: ET.Element) -> dict:
    rows = tbl.findall(f"{W}tr")
    matrix: list[list[str]] = []
    merged_cell_info: list[dict] = []
    max_cols = 0

    for row_index, row in enumerate(rows):
        row_values: list[str] = []
        col_index = 0
        for cell in row.findall(f"{W}tc"):
            cell_text_parts = []
            for paragraph in cell.findall(f".//{W}p"):
                value = paragraph_text(paragraph)
                if value:
                    cell_text_parts.append(value)
            cell_text = "\n".join(cell_text_parts)
            row_values.append(cell_text)

            tc_pr = cell.find(f"{W}tcPr")
            grid_span = 1
            row_span = 1
            if tc_pr is not None:
                grid_span_node = tc_pr.find(f"{W}gridSpan")
                if grid_span_node is not None:
                    grid_span = int(grid_span_node.attrib.get(f"{W}val", "1"))
                vmerge_node = tc_pr.find(f"{W}vMerge")
                if vmerge_node is not None:
                    row_span = 2
            if grid_span > 1 or row_span > 1:
                merged_cell_info.append(
                    {
                        "row_index": row_index,
                        "col_index": col_index,
                        "row_span": row_span,
                        "col_span": grid_span,
                    }
                )
            col_index += 1

        max_cols = max(max_cols, len(row_values))
        matrix.append(row_values)

    normalized_matrix = [row + [""] * (max_cols - len(row)) for row in matrix]
    return {
        "row_count": len(normalized_matrix),
        "col_count": max_cols,
        "cell_matrix": normalized_matrix,
        "merged_cell_info": merged_cell_info,
        "repeat_header": "",
        "treat_as_char": "",
        "text_wrap": "",
    }


def drawing_relationship_ids(paragraph: ET.Element) -> list[str]:
    ids: list[str] = []
    for node in paragraph.findall(f".//{A}blip"):
        rel_id = node.attrib.get(f"{R}embed") or node.attrib.get(f"{R}link")
        if rel_id:
            ids.append(rel_id)
    for node in paragraph.findall(f".//{V}imagedata"):
        rel_id = node.attrib.get(f"{R}id")
        if rel_id:
            ids.append(rel_id)
    return ids


def resolve_internal_asset_path(target: str) -> str:
    if target.startswith("/"):
        return target.lstrip("/")
    if target.startswith("word/"):
        return target
    return f"word/{target}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-docx", required=True)
    parser.add_argument("--document-id", required=True)
    parser.add_argument("--registry-id", required=True)
    parser.add_argument("--out-root", required=True)
    args = parser.parse_args()

    out_root = Path(args.out_root)
    text_dir = out_root / "work/02_structured-extraction/text"
    table_dir = out_root / "work/02_structured-extraction/tables"
    figure_dir = out_root / "work/02_structured-extraction/figures"
    layout_dir = out_root / "work/02_structured-extraction/layout"
    manifest_dir = out_root / "work/02_structured-extraction/manifests"
    figure_assets_dir = figure_dir / "assets" / args.document_id

    text_dir.mkdir(parents=True, exist_ok=True)
    table_dir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)
    layout_dir.mkdir(parents=True, exist_ok=True)
    manifest_dir.mkdir(parents=True, exist_ok=True)
    figure_assets_dir.mkdir(parents=True, exist_ok=True)
    cleanup_outputs(args.document_id, text_dir, table_dir, figure_dir, layout_dir, manifest_dir)
    figure_assets_dir.mkdir(parents=True, exist_ok=True)

    with ZipFile(args.source_docx) as docx_zip:
        relationships = load_relationships(docx_zip)
        root = ET.fromstring(docx_zip.read("word/document.xml"))
        body = root.find(f"{W}body")
        if body is None:
            raise ValueError("DOCX body was not found.")

        text_blocks = []
        tables = []
        figures = []
        section_summaries: dict[str, dict[str, int]] = defaultdict(lambda: {"text_blocks": 0, "tables": 0, "figures": 0})
        copied_assets: dict[str, str] = {}

        block_order = 0
        table_order = 0
        figure_order = 0
        section_index = 0

        def current_section_name() -> str:
            return f"section{section_index}"

        for child in list(body):
            tag = child.tag
            section_name = current_section_name()

            if tag == f"{W}p":
                text = paragraph_text(child)
                if text:
                    block_order += 1
                    text_blocks.append(
                        {
                            "evidence_id": f"EVD-{args.document_id}-{block_order:05d}",
                            "document_id": args.document_id,
                            "page_no_or_sheet_name": section_name,
                            "block_order": block_order,
                            "block_type": "paragraph",
                            "text": text,
                            "bbox": None,
                            "extraction_method": "docx-xml-parser",
                            "extraction_confidence": "medium",
                            "paragraph_id": child.attrib.get(f"{W}rsidR", ""),
                        }
                    )
                    section_summaries[section_name]["text_blocks"] += 1

                for rel_id in drawing_relationship_ids(child):
                    target = relationships.get(rel_id, "")
                    if not target:
                        continue
                    internal_asset_path = resolve_internal_asset_path(target)
                    if internal_asset_path not in docx_zip.namelist():
                        continue
                    asset_name = Path(internal_asset_path).name
                    asset_path = figure_assets_dir / asset_name
                    if internal_asset_path not in copied_assets:
                        asset_path.write_bytes(docx_zip.read(internal_asset_path))
                        copied_assets[internal_asset_path] = str(asset_path)
                    figure_order += 1
                    figure_id = f"FIG-{args.document_id}-{figure_order:03d}"
                    figure_rel_path = figure_dir / f"{figure_id}.json"
                    figure_payload = {
                        "figure_id": figure_id,
                        "document_id": args.document_id,
                        "section_name": section_name,
                        "source_block_order": block_order,
                        "relationship_id": rel_id,
                        "internal_asset_path": internal_asset_path,
                        "asset_path": relative_or_absolute(copied_assets[internal_asset_path], out_root),
                        "shape_comment": "",
                        "source_bbox": None,
                        "extraction_method": "docx-xml-parser",
                    }
                    write_json(figure_rel_path, figure_payload)
                    figures.append(
                        {
                            "figure_id": figure_id,
                            "path": relative_or_absolute(str(figure_rel_path), out_root),
                            "asset_path": relative_or_absolute(copied_assets[internal_asset_path], out_root),
                            "section_name": section_name,
                        }
                    )
                    section_summaries[section_name]["figures"] += 1

                if child.find(f".//{W}sectPr") is not None:
                    section_index += 1
                continue

            if tag == f"{W}tbl":
                table_order += 1
                table_id = f"TBL-{args.document_id}-{table_order:03d}"
                table_payload = {
                    "table_id": table_id,
                    "document_id": args.document_id,
                    "page_no_or_sheet_name": section_name,
                    "source_bbox": None,
                    "extraction_method": "docx-xml-parser",
                    **extract_table(child),
                }
                table_path = table_dir / f"{table_id}.json"
                write_json(table_path, table_payload)
                tables.append(
                    {
                        "table_id": table_id,
                        "path": relative_or_absolute(str(table_path), out_root),
                        "section_name": section_name,
                        "rows": table_payload["row_count"],
                        "cols": table_payload["col_count"],
                    }
                )
                section_summaries[section_name]["tables"] += 1
                continue

            if tag == f"{W}sectPr":
                section_index += 1

        layout_sections = [
            {
                "section_name": section_name,
                "text_block_count": summary["text_blocks"],
                "table_count": summary["tables"],
                "figure_count": summary["figures"],
            }
            for section_name, summary in sorted(section_summaries.items(), key=lambda item: int(item[0].replace("section", "")))
        ]

        text_path = text_dir / f"{args.document_id}_blocks.json"
        layout_path = layout_dir / f"{args.document_id}_layout.json"
        manifest_path = manifest_dir / f"{args.document_id}_manifest.json"

        write_json(text_path, text_blocks)
        write_json(layout_path, {"document_id": args.document_id, "sections": layout_sections})
        write_json(
            manifest_path,
            {
                "document_id": args.document_id,
                "registry_id": args.registry_id,
                "source_rel_path": relative_or_absolute(args.source_docx, out_root),
                "internal_path": "",
                "source_format": "docx",
                "extraction_run_id": "docx-pilot-v1",
                "page_count_or_sheet_count": len(layout_sections),
                "processing_status": "completed",
                "quality_notes": [
                    "DOCX parsed directly from OOXML package.",
                    "Section order is used as provenance because page numbers are not reliable in converted DOCX files.",
                    "Tables and embedded media are preserved separately from pure text blocks.",
                ],
                "text_path": relative_or_absolute(str(text_path), out_root),
                "layout_path": relative_or_absolute(str(layout_path), out_root),
                "tables": tables,
                "figures": figures,
                "counts": {
                    "evidence_units": len(text_blocks),
                    "tables": len(tables),
                    "figures": len(figures),
                },
            },
        )


if __name__ == "__main__":
    main()
