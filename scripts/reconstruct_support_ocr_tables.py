#!/usr/bin/env python3
"""Reconstruct coarse table candidates from OCR line blocks for support PDFs."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path


PROFILES = {
    "DOC-REF-002": {
        "column_boundaries": [550.0, 1350.0],
        "header_tokens": ["과학기술정책", "내용"],
    },
    "DOC-CTX-002": {
        "column_boundaries": [360.0],
        "header_tokens": ["기술개요", "중분류"],
    },
    "DOC-CTX-003": {
        "column_boundaries": [395.0],
        "header_tokens": ["기술개요", "중분류"],
    },
    "DOC-CTX-004": {
        "column_boundaries": [370.0],
        "header_tokens": ["기술개요", "중분류"],
    },
}

DEFAULT_DOCUMENTS = list(PROFILES.keys())
HANGUL_OR_ALNUM_RE = re.compile(r"[가-힣A-Za-z0-9]")


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(path: Path, rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        for row in rows:
            writer.writerow(row)


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


def block_sort_key(block: dict) -> tuple[float, float]:
    x0, y0, _x1, _y1 = bbox_bounds(block["bbox"])
    return y0, x0


def looks_like_noise(text: str, score: float) -> bool:
    compact = text.replace(" ", "")
    if not compact:
        return True
    if score < 0.65:
        return True
    signal = len(HANGUL_OR_ALNUM_RE.findall(compact))
    ratio = signal / max(len(compact), 1)
    if len(compact) <= 4 and score < 0.85:
        return True
    if ratio < 0.45 and score < 0.9:
        return True
    if re.fullmatch(r"[\W_]+", compact):
        return True
    return False


def filter_blocks(blocks: list[dict]) -> list[dict]:
    kept = []
    for block in blocks:
        text = clean_text(block.get("text", ""))
        score = float(block.get("extraction_confidence", 0.0) or 0.0)
        if not text:
            continue
        if looks_like_noise(text, score):
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
        threshold = max(18.0, min(32.0, (current_h + block["height"]) * 0.45))
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


def find_header_index(rows: list[list[dict]], header_tokens: list[str]) -> int:
    normalized_tokens = [normalize_token_text(token) for token in header_tokens]
    for index, row in enumerate(rows):
        text = normalize_token_text(row_text(row))
        if all(token in text for token in normalized_tokens):
            return index
    return 0


def assign_column(x0: float, boundaries: list[float]) -> int:
    for index, boundary in enumerate(boundaries):
        if x0 < boundary:
            return index
    return len(boundaries)


def row_to_cells(row: list[dict], boundaries: list[float]) -> list[str]:
    cells = ["" for _ in range(len(boundaries) + 1)]
    for block in row:
        column = assign_column(block["x0"], boundaries)
        cells[column] = cell_join(cells[column], block["text"])
    return [clean_text(cell) for cell in cells]


def merge_continuations(rows: list[list[str]], header_rows: int = 1) -> list[list[str]]:
    if not rows:
        return []
    merged = [rows[0]]
    col_count = len(rows[0])

    for row_index, row in enumerate(rows[1:], start=1):
        current = merged[-1]
        filled = [index for index, value in enumerate(row) if value]
        if not filled:
            continue
        if row_index <= header_rows:
            merged.append(row)
            continue
        if len(filled) == 1:
            index = filled[0]
            if index == col_count - 1 and any(current[col] for col in range(col_count - 1)):
                current[index] = cell_join(current[index], row[index])
                continue
            if current[index] and not any(row[col] for col in range(index + 1, col_count)):
                current[index] = cell_join(current[index], row[index])
                continue
        merged.append(row)
    return merged


def table_bbox(rows: list[list[dict]]) -> list[float] | None:
    if not rows:
        return None
    xs0 = []
    ys0 = []
    xs1 = []
    ys1 = []
    for row in rows:
        for block in row:
            x0, y0, x1, y1 = bbox_bounds(block["bbox"])
            xs0.append(x0)
            ys0.append(y0)
            xs1.append(x1)
            ys1.append(y1)
    if not xs0:
        return None
    return [min(xs0), min(ys0), max(xs1), max(ys1)]


def build_table_candidate(document_id: str, blocks: list[dict]) -> tuple[dict, list[list[str]]] | None:
    profile = PROFILES.get(document_id)
    if profile is None:
        raise ValueError(f"No OCR table profile configured for {document_id}")

    filtered = filter_blocks(blocks)
    if not filtered:
        return None

    rows = group_rows(filtered)
    header_index = find_header_index(rows, profile["header_tokens"])
    title_rows = rows[:header_index]
    table_rows = rows[header_index:]
    if not table_rows:
        return None

    cell_rows = [row_to_cells(row, profile["column_boundaries"]) for row in table_rows]
    cell_rows = merge_continuations(cell_rows, header_rows=1)
    if len(cell_rows) < 2:
        return None

    title_parts = []
    for row in title_rows:
        text = clean_text(row_text(row))
        if not text:
            continue
        if len(text.replace(" ", "")) < 4:
            continue
        title_parts.append(text)

    page_no = table_rows[0][0]["page_no"]
    table_id = f"TBL-{document_id}-OCR-001"
    table_payload = {
        "table_id": table_id,
        "document_id": document_id,
        "page_no_or_sheet_name": page_no,
        "block_order": 1,
        "table_title": " / ".join(title_parts[:3]),
        "header_rows": [1],
        "table_shape": {
            "rows": len(cell_rows),
            "cols": len(cell_rows[0]),
        },
        "cell_matrix": cell_rows,
        "merged_cell_info": [],
        "source_bbox": table_bbox(table_rows),
        "extraction_confidence": "medium",
        "extraction_method": "rapidocr-line-table-heuristic-v1",
        "candidate_source": "rapidocr_line_reconstruction",
        "source_line_count": len(filtered),
        "review_required": True,
    }
    return table_payload, cell_rows


def update_manifest(out_root: Path, document_id: str, table_payload: dict, csv_path: Path, json_path: Path) -> None:
    manifest_path = out_root / "work/02_structured-extraction/manifests" / f"{document_id}_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    tables = manifest.get("tables")
    table_entry = {
        "table_id": table_payload["table_id"],
        "path": str(json_path.relative_to(out_root)),
        "csv_path": str(csv_path.relative_to(out_root)),
        "page_no": table_payload["page_no_or_sheet_name"],
        "rows": table_payload["table_shape"]["rows"],
        "cols": table_payload["table_shape"]["cols"],
        "candidate_source": table_payload["candidate_source"],
    }
    if isinstance(tables, list):
        tables = [row for row in tables if row.get("table_id") != table_payload["table_id"]]
        tables.append(table_entry)
    else:
        tables = [table_entry]
    manifest["tables"] = tables

    counts = manifest.get("counts", {})
    if isinstance(counts, dict):
        counts["tables"] = len(tables)
        manifest["counts"] = counts

    quality_notes = manifest.get("quality_notes", [])
    note = "OCR line blocks were grouped into a coarse table candidate for manual review."
    if note not in quality_notes:
        quality_notes.append(note)
    manifest["quality_notes"] = quality_notes
    write_json(manifest_path, manifest)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-root", required=True)
    parser.add_argument("--documents", nargs="*", default=DEFAULT_DOCUMENTS)
    args = parser.parse_args()

    out_root = Path(args.out_root)
    tables_dir = out_root / "work/02_structured-extraction/tables"

    for document_id in args.documents:
        blocks_path = out_root / "work/02_structured-extraction/text" / f"{document_id}_blocks.json"
        if not blocks_path.exists():
            raise FileNotFoundError(f"Missing OCR blocks for {document_id}: {blocks_path}")
        blocks = json.loads(blocks_path.read_text(encoding="utf-8"))
        if isinstance(blocks, dict):
            blocks = blocks.get("blocks", [])

        candidate = build_table_candidate(document_id, blocks)
        if candidate is None:
            continue
        table_payload, cell_rows = candidate

        json_path = tables_dir / f"{table_payload['table_id']}.json"
        csv_path = tables_dir / f"{table_payload['table_id']}.csv"
        write_json(json_path, table_payload)
        write_csv(csv_path, cell_rows)
        update_manifest(out_root, document_id, table_payload, csv_path, json_path)


if __name__ == "__main__":
    main()
