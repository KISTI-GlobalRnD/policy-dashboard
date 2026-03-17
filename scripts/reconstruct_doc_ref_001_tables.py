#!/usr/bin/env python3
"""Reconstruct page-wise draft tables for DOC-REF-001 from OCR blocks."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path


BOUNDARIES = [180.0, 430.0]
COLUMN_HEADERS = ["구분", "주요", "내용"]
HEADER_TOKENS = ["구분", "내용"]
HANGUL_OR_ALNUM_RE = re.compile(r"[가-힣A-Za-z0-9]")


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(path: Path, rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerows(rows)


def clean_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = "\n".join(line.strip() for line in text.splitlines())
    return text.strip()


def cell_join(left: str, right: str) -> str:
    if not left:
        return right
    if not right:
        return left
    if left.endswith(("-", "/", "·", "(", "[")):
        return f"{left}{right}"
    return f"{left} {right}"


def bbox_bounds(bbox: list[list[float]]) -> tuple[float, float, float, float]:
    xs = [point[0] for point in bbox]
    ys = [point[1] for point in bbox]
    return min(xs), min(ys), max(xs), max(ys)


def looks_like_noise(text: str, score: float) -> bool:
    compact = text.replace(" ", "")
    if not compact:
        return True
    if score < 0.6:
        return True
    signal = len(HANGUL_OR_ALNUM_RE.findall(compact))
    ratio = signal / max(len(compact), 1)
    if len(compact) <= 2 and score < 0.85:
        return True
    if ratio < 0.4 and score < 0.9:
        return True
    if re.fullmatch(r"[\W_]+", compact):
        return True
    return False


def filter_blocks(blocks: list[dict]) -> list[dict]:
    kept = []
    for block in blocks:
        text = clean_text(block.get("text", ""))
        score = float(block.get("extraction_confidence", 0.0) or 0.0)
        if not text or looks_like_noise(text, score):
            continue
        x0, y0, x1, y1 = bbox_bounds(block["bbox"])
        kept.append(
            {
                "text": text,
                "score": score,
                "bbox": block["bbox"],
                "x0": x0,
                "y0": y0,
                "x1": x1,
                "y1": y1,
                "height": y1 - y0,
                "page_no": int(block.get("page_no") or block.get("page_no_or_sheet_name") or 1),
            }
        )
    kept.sort(key=lambda row: (row["page_no"], row["y0"], row["x0"]))
    return kept


def group_rows(blocks: list[dict]) -> list[list[dict]]:
    if not blocks:
        return []
    rows: list[list[dict]] = []
    current = [blocks[0]]
    current_y = blocks[0]["y0"]
    current_h = blocks[0]["height"]
    for block in blocks[1:]:
        threshold = max(16.0, min(28.0, (current_h + block["height"]) * 0.45))
        if block["page_no"] == current[0]["page_no"] and abs(block["y0"] - current_y) <= threshold:
            current.append(block)
            current_y = (current_y + block["y0"]) / 2
            current_h = max(current_h, block["height"])
            continue
        rows.append(sorted(current, key=lambda row: row["x0"]))
        current = [block]
        current_y = block["y0"]
        current_h = block["height"]
    rows.append(sorted(current, key=lambda row: row["x0"]))
    return rows


def row_text(row: list[dict]) -> str:
    return " ".join(block["text"] for block in row)


def normalize_token_text(text: str) -> str:
    return re.sub(r"\s+", "", text).lower()


def find_header_index(rows: list[list[dict]]) -> int:
    tokens = [normalize_token_text(token) for token in HEADER_TOKENS]
    for index, row in enumerate(rows):
        text = normalize_token_text(row_text(row))
        if all(token in text for token in tokens):
            return index
    return 0


def assign_column(x0: float) -> int:
    for index, boundary in enumerate(BOUNDARIES):
        if x0 < boundary:
            return index
    return len(BOUNDARIES)


def row_to_cells(row: list[dict]) -> list[str]:
    cells = ["" for _ in range(len(BOUNDARIES) + 1)]
    for block in row:
        column = assign_column(block["x0"])
        cells[column] = cell_join(cells[column], block["text"])
    return [clean_text(cell) for cell in cells]


def merge_continuations(rows: list[list[str]]) -> list[list[str]]:
    if not rows:
        return []
    merged = [rows[0]]
    for row in rows[1:]:
        current = merged[-1]
        filled = [index for index, value in enumerate(row) if value]
        if not filled:
            continue
        if filled == [2]:
            current[2] = cell_join(current[2], row[2])
            continue
        if filled == [1] and current[0]:
            current[1] = cell_join(current[1], row[1])
            continue
        if filled == [1, 2] and not row[0] and current[0]:
            current[1] = cell_join(current[1], row[1])
            current[2] = cell_join(current[2], row[2])
            continue
        merged.append(row)
    return merged


def page_title(page_no: int) -> str:
    return f"정책-항목 구성(안) page {page_no:03d} table"


def reconstruct_tables(out_root: Path) -> list[dict]:
    blocks_path = out_root / "work/02_structured-extraction/text/DOC-REF-001_blocks.json"
    raw_blocks = json.loads(blocks_path.read_text(encoding="utf-8"))
    filtered = filter_blocks(raw_blocks)
    by_page: dict[int, list[dict]] = {}
    for block in filtered:
        by_page.setdefault(block["page_no"], []).append(block)

    tables_dir = out_root / "work/02_structured-extraction/tables"
    entries = []
    for page_no in sorted(by_page):
        rows = group_rows(by_page[page_no])
        header_index = find_header_index(rows)
        data_rows = rows[header_index + 1 :]
        cell_rows = [row_to_cells(row) for row in data_rows]
        cell_rows = [row for row in cell_rows if any(row)]
        cell_rows = merge_continuations([COLUMN_HEADERS, *cell_rows])
        if len(cell_rows) <= 1:
            continue

        table_id = f"TBL-DOC-REF-001-{page_no:03d}"
        bbox = None
        if data_rows:
            xs0 = []
            ys0 = []
            xs1 = []
            ys1 = []
            for row in data_rows:
                for block in row:
                    x0, y0, x1, y1 = bbox_bounds(block["bbox"])
                    xs0.append(x0)
                    ys0.append(y0)
                    xs1.append(x1)
                    ys1.append(y1)
            bbox = [min(xs0), min(ys0), max(xs1), max(ys1)]

        payload = {
            "table_id": table_id,
            "document_id": "DOC-REF-001",
            "page_no_or_sheet_name": page_no,
            "block_order": 1,
            "table_title": page_title(page_no),
            "header_rows": [1],
            "table_shape": {
                "rows": len(cell_rows),
                "cols": len(COLUMN_HEADERS),
            },
            "cell_matrix": cell_rows,
            "merged_cell_info": [],
            "source_bbox": bbox,
            "extraction_confidence": "medium",
            "extraction_method": "rapidocr-line-table-heuristic-v2-pagewise",
            "candidate_source": "pagewise_ocr_line_reconstruction",
            "review_required": False,
        }
        json_path = tables_dir / f"{table_id}.json"
        csv_path = tables_dir / f"{table_id}.csv"
        write_json(json_path, payload)
        write_csv(csv_path, cell_rows)
        entries.append(
            {
                "table_id": table_id,
                "path": str(json_path.relative_to(out_root)),
                "csv_path": str(csv_path.relative_to(out_root)),
                "page_no": page_no,
                "rows": len(cell_rows),
                "cols": len(COLUMN_HEADERS),
                "candidate_source": "pagewise_ocr_line_reconstruction",
            }
        )
    return entries


def update_manifest(out_root: Path, table_entries: list[dict]) -> None:
    manifest_path = out_root / "work/02_structured-extraction/manifests/DOC-REF-001_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
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
    note = "OCR line blocks were reconstructed into page-wise draft tables for the board document."
    if note not in quality_notes:
        quality_notes.append(note)
    manifest["quality_notes"] = quality_notes
    write_json(manifest_path, manifest)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-root", required=True)
    args = parser.parse_args()

    out_root = Path(args.out_root)
    table_entries = reconstruct_tables(out_root)
    update_manifest(out_root, table_entries)


if __name__ == "__main__":
    main()
