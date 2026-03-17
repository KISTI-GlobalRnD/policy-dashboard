#!/usr/bin/env python3
"""Extract a simple structured representation from the taxonomy XLSX source.

This script intentionally uses only the Python standard library so it can run
in the current environment without extra dependencies.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple
from xml.etree import ElementTree as ET
from zipfile import ZipFile


NS = {
    "a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}


def col_to_index(col_name: str) -> int:
    value = 0
    for char in col_name:
        value = value * 26 + (ord(char.upper()) - ord("A") + 1)
    return value


def split_ref(ref: str) -> Tuple[str, int]:
    match = re.fullmatch(r"([A-Z]+)(\d+)", ref)
    if not match:
        raise ValueError(f"Unsupported cell reference: {ref}")
    col_name, row_no = match.groups()
    return col_name, int(row_no)


def range_to_bounds(range_ref: str) -> Tuple[int, int, int, int]:
    start, end = range_ref.split(":")
    start_col, start_row = split_ref(start)
    end_col, end_row = split_ref(end)
    return start_row, col_to_index(start_col), end_row, col_to_index(end_col)


def read_shared_strings(zf: ZipFile) -> List[str]:
    if "xl/sharedStrings.xml" not in zf.namelist():
        return []
    root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
    values: List[str] = []
    for item in root.findall("a:si", NS):
        text = "".join(node.text or "" for node in item.iterfind(".//a:t", NS))
        values.append(text)
    return values


def read_sheet_targets(zf: ZipFile) -> List[Tuple[str, str]]:
    workbook = ET.fromstring(zf.read("xl/workbook.xml"))
    rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
    rel_map = {rel.attrib["Id"]: rel.attrib["Target"] for rel in rels.findall("rel:Relationship", NS)}
    sheets = []
    for sheet in workbook.find("a:sheets", NS):
        rid = sheet.attrib["{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"]
        sheets.append((sheet.attrib["name"], "xl/" + rel_map[rid]))
    return sheets


@dataclass
class WorksheetTable:
    sheet_name: str
    max_row: int
    max_col: int
    merged_ranges: List[dict]
    rows: List[List[str]]


def parse_worksheet(zf: ZipFile, worksheet_path: str, shared_strings: List[str]) -> WorksheetTable:
    root = ET.fromstring(zf.read(worksheet_path))
    sheet_data = root.find("a:sheetData", NS)
    raw_cells: Dict[Tuple[int, int], str] = {}
    max_row = 0
    max_col = 0

    for row in sheet_data.findall("a:row", NS):
        for cell in row.findall("a:c", NS):
            ref = cell.attrib["r"]
            col_name, row_no = split_ref(ref)
            col_no = col_to_index(col_name)
            cell_type = cell.attrib.get("t")
            value_node = cell.find("a:v", NS)
            value = value_node.text if value_node is not None else ""
            if cell_type == "s" and value != "":
                value = shared_strings[int(value)]
            elif cell_type == "inlineStr":
                value = "".join(node.text or "" for node in cell.iterfind(".//a:t", NS))
            raw_cells[(row_no, col_no)] = value
            max_row = max(max_row, row_no)
            max_col = max(max_col, col_no)

    merged_ranges = []
    merge_cells = root.find("a:mergeCells", NS)
    if merge_cells is not None:
        for merge_cell in merge_cells.findall("a:mergeCell", NS):
            start_row, start_col, end_row, end_col = range_to_bounds(merge_cell.attrib["ref"])
            merged_ranges.append(
                {
                    "range_ref": merge_cell.attrib["ref"],
                    "start_row": start_row,
                    "start_col": start_col,
                    "end_row": end_row,
                    "end_col": end_col,
                }
            )

    rows: List[List[str]] = []
    for row_no in range(1, max_row + 1):
        row_values = []
        for col_no in range(1, max_col + 1):
            row_values.append(raw_cells.get((row_no, col_no), ""))
        rows.append(row_values)

    return WorksheetTable(
        sheet_name=Path(worksheet_path).stem,
        max_row=max_row,
        max_col=max_col,
        merged_ranges=merged_ranges,
        rows=rows,
    )


def write_csv(path: Path, rows: List[List[str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, help="Path to the XLSX source file")
    parser.add_argument("--document-id", required=True)
    parser.add_argument("--registry-id", required=True)
    parser.add_argument("--out-root", required=True, help="Project root output directory")
    args = parser.parse_args()

    source = Path(args.source)
    out_root = Path(args.out_root)
    manifests_dir = out_root / "work/02_structured-extraction/manifests"
    tables_dir = out_root / "work/02_structured-extraction/tables"
    normalized_dir = out_root / "work/03_processing/normalized"
    manifests_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)
    normalized_dir.mkdir(parents=True, exist_ok=True)

    with ZipFile(source) as zf:
        shared_strings = read_shared_strings(zf)
        sheet_targets = read_sheet_targets(zf)
        extracted_sheets = []
        domain_rows: List[List[str]] = [["tech_domain", "tech_subdomain"]]

        for sheet_name, worksheet_path in sheet_targets:
            worksheet = parse_worksheet(zf, worksheet_path, shared_strings)
            table_id = f"TBL-{args.document_id}-001"
            table_json_path = tables_dir / f"{args.document_id}__{sheet_name}.json"
            table_csv_path = tables_dir / f"{args.document_id}__{sheet_name}.csv"
            write_csv(table_csv_path, worksheet.rows)

            table_payload = {
                "table_id": table_id,
                "document_id": args.document_id,
                "page_no_or_sheet_name": sheet_name,
                "table_title": f"{sheet_name} worksheet export",
                "header_rows": [1, 2],
                "table_shape": {"rows": worksheet.max_row, "cols": worksheet.max_col},
                "cell_matrix": worksheet.rows,
                "merged_cell_info": worksheet.merged_ranges,
                "source_bbox": None,
                "extraction_confidence": "high",
                "extraction_method": "xlsx-zip-xml-parser",
                "table_csv_path": str(table_csv_path.relative_to(out_root)),
            }
            table_json_path.write_text(json.dumps(table_payload, ensure_ascii=False, indent=2), encoding="utf-8")

            extracted_sheets.append(
                {
                    "sheet_name": sheet_name,
                    "worksheet_path": worksheet_path,
                    "table_id": table_id,
                    "table_json_path": str(table_json_path.relative_to(out_root)),
                    "table_csv_path": str(table_csv_path.relative_to(out_root)),
                    "rows": worksheet.max_row,
                    "cols": worksheet.max_col,
                    "merged_ranges": len(worksheet.merged_ranges),
                }
            )

            if sheet_name == "Sheet1":
                for row in worksheet.rows[2:]:
                    tech_domain = row[0].strip()
                    for value in row[1:]:
                        tech_subdomain = value.strip()
                        if tech_domain and tech_subdomain:
                            domain_rows.append([tech_domain, tech_subdomain])

        manifest_path = manifests_dir / f"{args.document_id}_manifest.json"
        manifest = {
            "document_id": args.document_id,
            "registry_id": args.registry_id,
            "source_rel_path": str(source),
            "internal_path": "",
            "source_format": "xlsx",
            "extraction_run_id": "pilot-gs-004-v1",
            "page_count_or_sheet_count": len(extracted_sheets),
            "processing_status": "completed",
            "quality_notes": [
                "Workbook extracted via ZIP/XML parser.",
                "Merged-cell metadata preserved separately.",
                "Domain-subdomain pairs flattened for downstream processing.",
            ],
            "sheets": extracted_sheets,
        }
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

        normalized_csv = normalized_dir / f"{args.document_id}__tech-domain-subdomain.csv"
        write_csv(normalized_csv, domain_rows)


if __name__ == "__main__":
    main()
