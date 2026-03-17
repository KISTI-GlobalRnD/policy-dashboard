#!/usr/bin/env python3
"""Build paragraph-to-source-evidence provenance mappings."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sqlite3
import unicodedata
from collections import defaultdict
from pathlib import Path


TRANSLATION_TABLE = str.maketrans(
    {
        "\uf09e": "-",
        "•": "-",
        "◦": "-",
        "▪": "-",
        "▸": "-",
        "▹": "-",
        "►": "-",
        "▻": "-",
        "": "-",
        "󰊱": "-",
        "󰊲": "-",
        "󰊳": "-",
        "󰊴": "-",
        "󰊵": "-",
        "󰊶": "-",
        "–": "-",
        "—": "-",
        "―": "-",
        "−": "-",
        "‐": "-",
        "‑": "-",
        "․": "·",
        "ㆍ": "·",
        "‧": "·",
        "∙": "·",
        "∼": "~",
        "～": "~",
        "〜": "~",
        "“": '"',
        "”": '"',
        "‟": '"',
        "’": "'",
        "‘": "'",
        "‚": "'",
        "‛": "'",
    }
)
ZERO_WIDTH_RE = re.compile(r"[\u200b-\u200d\ufeff]")


def normalize_compare_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text or "").translate(TRANSLATION_TABLE)
    normalized = ZERO_WIDTH_RE.sub("", normalized)
    return "".join(normalized.split())


def read_paragraph_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def load_raw_blocks(path: Path) -> list[dict]:
    raw_blocks = json.loads(path.read_text(encoding="utf-8"))
    expanded_blocks: list[dict] = []
    for block in raw_blocks:
        base_order = int(block.get("block_order", 0))
        text = block.get("text", "")
        lines = [part.strip() for part in re.split(r"\n+", text) if part.strip()]
        if len(lines) <= 1:
            single_block = dict(block)
            single_block["base_block_order"] = base_order
            single_block["line_index"] = 0
            expanded_blocks.append(single_block)
            continue

        for line_index, line in enumerate(lines, start=1):
            expanded_block = dict(block)
            expanded_block["text"] = line
            expanded_block["block_order"] = (base_order * 100) + line_index
            expanded_block["base_block_order"] = base_order
            expanded_block["line_index"] = line_index
            expanded_blocks.append(expanded_block)
    return expanded_blocks


def group_by_page(rows: list[dict], page_key: str) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[str(row[page_key])].append(row)
    return grouped


def raw_block_sort_key(raw_block: dict, page_no: str) -> tuple[int, int] | int:
    if str(page_no).startswith("section"):
        return (
            int(raw_block.get("base_block_order", raw_block.get("block_order", 0))),
            int(raw_block.get("line_index", 0)),
        )
    return int(raw_block.get("block_order", 0))


def find_match(
    raw_blocks: list[dict],
    start_index: int,
    target_text: str,
    merged_block_count: int,
    *,
    max_skip: int = 8,
    max_sequence_floor: int = 8,
    search_from_start: bool = False,
) -> tuple[int, int, str] | None:
    target_compare = normalize_compare_text(target_text)
    if not target_compare:
        return None

    max_sequence = max(merged_block_count + 4, max_sequence_floor)
    if search_from_start:
        candidate_starts = range(len(raw_blocks))
    else:
        candidate_starts = range(start_index, min(len(raw_blocks), start_index + max_skip + 1))

    for candidate_start in candidate_starts:
        built = ""
        for sequence_length in range(1, max_sequence + 1):
            candidate_end = candidate_start + sequence_length
            if candidate_end > len(raw_blocks):
                break
            built += normalize_compare_text(raw_blocks[candidate_end - 1].get("text", ""))
            if not built:
                continue
            if built == target_compare:
                base_note = "exact_match" if sequence_length == merged_block_count else "exact_variable_span"
                note = f"{base_note}_page_fallback" if search_from_start else base_note
                return candidate_start, candidate_end, note

    for candidate_start in candidate_starts:
        candidate_text = normalize_compare_text(raw_blocks[candidate_start].get("text", ""))
        if not candidate_text:
            continue
        if candidate_text in target_compare or target_compare in candidate_text:
            note = "fuzzy_single_block_page_fallback" if search_from_start else "fuzzy_single_block"
            return candidate_start, candidate_start + 1, note
    return None


def build_document_rows(document_id: str, normalized_dir: Path, text_dir: Path) -> tuple[list[dict[str, object]], dict[str, int]]:
    paragraph_csv = normalized_dir / f"{document_id}__paragraphs.csv"
    raw_blocks_json = text_dir / f"{document_id}_blocks.json"
    if not paragraph_csv.exists() or not raw_blocks_json.exists():
        return [], {"paragraph_count": 0, "mapped_count": 0, "unmapped_count": 0}

    paragraphs = read_paragraph_rows(paragraph_csv)
    raw_blocks = load_raw_blocks(raw_blocks_json)

    paragraphs_by_page = group_by_page(paragraphs, "page_no")
    raw_by_page = group_by_page(raw_blocks, "page_no_or_sheet_name")

    mapping_rows: list[dict[str, object]] = []
    mapped_paragraphs = 0
    unmapped_paragraphs = 0

    for page_no, page_paragraphs in paragraphs_by_page.items():
        page_raw = sorted(raw_by_page.get(page_no, []), key=lambda item: raw_block_sort_key(item, page_no))
        raw_pointer = 0
        for paragraph in sorted(page_paragraphs, key=lambda item: int(item["page_block_order"])):
            match = find_match(
                raw_blocks=page_raw,
                start_index=raw_pointer,
                target_text=paragraph["text"],
                merged_block_count=int(paragraph["merged_block_count"]),
            )
            if not match and str(page_no).isdigit():
                match = find_match(
                    raw_blocks=page_raw,
                    start_index=0,
                    target_text=paragraph["text"],
                    merged_block_count=int(paragraph["merged_block_count"]),
                    max_sequence_floor=40,
                    search_from_start=True,
                )
            if not match:
                unmapped_paragraphs += 1
                continue
            start_index, end_index, note = match
            mapped_paragraphs += 1
            for mapping_order, raw_block in enumerate(page_raw[start_index:end_index], start=1):
                bbox = raw_block.get("bbox")
                mapping_rows.append(
                    {
                        "paragraph_source_map_id": f"PSM-{paragraph['paragraph_id']}-{mapping_order:02d}",
                        "paragraph_id": paragraph["paragraph_id"],
                        "source_evidence_id": raw_block["evidence_id"],
                        "document_id": document_id,
                        "page_no_or_section": page_no,
                        "bbox_json": json.dumps(bbox, ensure_ascii=False) if bbox is not None else "",
                        "source_block_order": raw_block.get("block_order", 0),
                        "mapping_order": mapping_order,
                        "notes": note,
                    }
                )
            raw_pointer = end_index

    return mapping_rows, {
        "paragraph_count": len(paragraphs),
        "mapped_count": mapped_paragraphs,
        "unmapped_count": unmapped_paragraphs,
    }


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_into_db(db_path: Path, rows: list[dict[str, object]]) -> None:
    connection = sqlite3.connect(db_path)
    try:
        connection.executemany(
            """
            INSERT OR REPLACE INTO paragraph_source_map (
                paragraph_source_map_id,
                paragraph_id,
                source_evidence_id,
                document_id,
                page_no_or_section,
                bbox_json,
                source_block_order,
                mapping_order,
                notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    row["paragraph_source_map_id"],
                    row["paragraph_id"],
                    row["source_evidence_id"],
                    row["document_id"],
                    row["page_no_or_section"],
                    row["bbox_json"],
                    row["source_block_order"],
                    row["mapping_order"],
                    row["notes"],
                )
                for row in rows
            ],
        )
        connection.commit()
    finally:
        connection.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--normalized-dir", required=True)
    parser.add_argument("--text-dir", required=True)
    parser.add_argument("--out-csv", required=True)
    parser.add_argument("--out-report", required=True)
    parser.add_argument("--db-path")
    args = parser.parse_args()

    normalized_dir = Path(args.normalized_dir)
    text_dir = Path(args.text_dir)
    all_rows: list[dict[str, object]] = []
    report_rows: list[dict[str, object]] = []

    for paragraph_csv in sorted(normalized_dir.glob("DOC-*__paragraphs.csv")):
        document_id = paragraph_csv.name.split("__", 1)[0]
        rows, stats = build_document_rows(document_id, normalized_dir, text_dir)
        all_rows.extend(rows)
        report_rows.append({"document_id": document_id, **stats})

    write_csv(
        Path(args.out_csv),
        all_rows,
        [
            "paragraph_source_map_id",
            "paragraph_id",
            "source_evidence_id",
            "document_id",
            "page_no_or_section",
            "bbox_json",
            "source_block_order",
            "mapping_order",
            "notes",
        ],
    )
    write_json(Path(args.out_report), report_rows)

    if args.db_path:
        load_into_db(Path(args.db_path), all_rows)

    print(f"Mapped rows: {len(all_rows)}")
    print(f"Documents: {len(report_rows)}")


if __name__ == "__main__":
    main()
