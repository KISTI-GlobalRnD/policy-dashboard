#!/usr/bin/env python3
"""Normalize text-first outputs for HWP / HWPX style structured blocks."""

from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path


NUMBERED_HEADING_PATTERN = re.compile(r"^\d+[.)]\s*\S")
ROMAN_HEADING_PATTERN = re.compile(r"^[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]+(?:[.)]\s*|\s+)")
CIRCLED_HEADING_PATTERN = re.compile(r"^[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳]\s+\S")
ASCII_ROMAN_ONLY_PATTERN = re.compile(r"^(?:I|II|III|IV|V|VI|VII|VIII|IX|X)$")
BULLET_PATTERN = re.compile(r"^(?:[-*]+|ㅇ|□|▪|•|⦁|◦|➊|➋|➌|➍|➎|➏|➐|➑|➒|➓|☞|⇒|⇨)\s*")
DATE_NOTE_PATTERN = re.compile(r"^\(.*[’']?\d{2}.*\)$")
HWP_SPACED_HANGUL_LABEL_PATTERN = re.compile(r"^[가-힣](?:\s+[가-힣]){1,5}$")
HWP_NUMBERED_LABEL_PATTERN = re.compile(r"^분야\s*\d+$")
STAR_NOTE_PATTERN = re.compile(r"^\*{1,2}\s*\S")
STRUCTURED_NOISE_PATTERN = re.compile(r"^(?:<+|>+|\*+\s*[①-⑳▲△▷▶▸]+)$")
STRUCTURED_MARKER_ONLY_PATTERN = re.compile(r"^(?:ㅇ|□|▪|•|⦁|◦|➊|➋|➌|➍|➎|➏|➐|➑|➒|➓|☞|⇒|⇨|-+|\*+)$")
CIRCLED_ITEM_PATTERN = re.compile(r"^[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳]\s*\S")
CONTACT_LINE_PATTERN = re.compile(r"^(?:전\s*화|E-?mail)\s*:", re.IGNORECASE)
HWP_STANDALONE_LABELS = {
    "내용",
    "예산",
    "유형",
    "인재",
    "인프라",
    "전략",
    "제도",
    "참고",
    "금융",
}
LEADING_COVER_MARKERS = {"공개", "대외비"}


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def classify_text_block(text: str, source_block_type: str) -> str:
    if source_block_type == "shape_text" and len(text) <= 12:
        return "heading"
    if text.startswith("【") or (text.startswith("<") and text.endswith(">")):
        return "heading"
    if CIRCLED_HEADING_PATTERN.match(text):
        return "heading"
    if ROMAN_HEADING_PATTERN.match(text):
        return "heading"
    if NUMBERED_HEADING_PATTERN.match(text):
        return "heading"
    if text.startswith("(") and text.endswith(")") and DATE_NOTE_PATTERN.match(text):
        return "citation"
    if text.startswith("※"):
        return "note"
    if STAR_NOTE_PATTERN.match(text):
        return "note"
    if BULLET_PATTERN.match(text):
        return "bullet"
    return "paragraph"


def normalize_text(text: str) -> str:
    text = "".join("-" if unicodedata.category(char) == "Co" else char for char in text)
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def is_structured_noise_text(text: str) -> bool:
    compact = text.strip()
    return bool(STRUCTURED_NOISE_PATTERN.fullmatch(compact)) or bool(STRUCTURED_MARKER_ONLY_PATTERN.fullmatch(compact))


def split_structured_text_units(text: str, source_block_type: str) -> list[dict]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return []
    if len(lines) == 1:
        return [
            {
                "text": lines[0],
                "source_line_count": 1,
            }
        ]

    units: list[list[str]] = []
    current = [lines[0]]

    for line in lines[1:]:
        line_type = classify_text_block(line, source_block_type)
        starts_new_unit = (
            bool(BULLET_PATTERN.match(line))
            or bool(STAR_NOTE_PATTERN.match(line))
            or line.startswith("※")
            or bool(CIRCLED_ITEM_PATTERN.match(line))
            or bool(ROMAN_HEADING_PATTERN.match(line))
            or bool(NUMBERED_HEADING_PATTERN.match(line))
        )
        if starts_new_unit:
            units.append(current)
            current = [line]
            continue
        if current and line_type == "citation" and classify_text_block(current[0], source_block_type) != "note":
            units.append(current)
            current = [line]
            continue
        current.append(line)

    if current:
        units.append(current)

    return [
        {
            "text": " ".join(unit).strip(),
            "source_line_count": len(unit),
        }
        for unit in units
        if unit
    ]


def is_hwp_cover_heading(text: str) -> bool:
    return bool(re.search(r"(의결주문|제안이유|주요 내용|추진 배경|추진 과제|향후 조치 계획)", text))


def normalize_hwp_label_text(text: str) -> str:
    text = text.strip()
    if HWP_SPACED_HANGUL_LABEL_PATTERN.fullmatch(text):
        return text.replace(" ", "")
    return re.sub(r"\s+", " ", text)


def is_hwp_label_heading(text: str) -> bool:
    return text in HWP_STANDALONE_LABELS or bool(HWP_NUMBERED_LABEL_PATTERN.fullmatch(text))


def trim_leading_cover_markers(blocks: list[dict]) -> list[dict]:
    trimmed = list(blocks)
    while trimmed and trimmed[0]["block_type"] == "heading" and trimmed[0]["text"].strip() in LEADING_COVER_MARKERS:
        trimmed.pop(0)
    return trimmed


def trim_trailing_contact_blocks(blocks: list[dict]) -> list[dict]:
    trimmed = list(blocks)
    contact_index = None
    for index in range(len(trimmed) - 1, -1, -1):
        if CONTACT_LINE_PATTERN.match(trimmed[index]["text"].strip()):
            contact_index = index
            break
    if contact_index is None:
        return trimmed

    start = contact_index
    while start > 0:
        previous = trimmed[start - 1]
        if previous["block_type"] != "paragraph":
            break
        if len(previous["text"].strip()) > 50:
            break
        start -= 1
    return trimmed[:start]


def merge_hwp_blocks(base_block: dict, next_block: dict, action: str) -> dict:
    merged_actions = [value for value in [base_block.get("normalization_actions", ""), action] if value]
    return {
        **base_block,
        "text": f"{base_block['text'].rstrip()} {next_block['text'].lstrip()}".strip(),
        "source_line_count": base_block.get("source_line_count", 1) + next_block.get("source_line_count", 1),
        "merged_block_count": base_block.get("merged_block_count", 1) + next_block.get("merged_block_count", 1),
        "normalization_actions": "|".join(merged_actions),
    }


def is_hwp_note_continuation(base_block: dict, next_block: dict) -> bool:
    return (
        base_block["block_type"] == "note"
        and next_block["block_type"] in {"paragraph", "heading"}
        and base_block["text"].rstrip().endswith((",", "·", "→"))
        and bool(CIRCLED_ITEM_PATTERN.match(next_block["text"].strip()))
    )


def is_hwp_caption_continuation(base_block: dict, next_block: dict) -> bool:
    return (
        base_block["block_type"] == "paragraph"
        and next_block["block_type"] == "paragraph"
        and ":" in base_block["text"]
        and ":" not in next_block["text"]
        and len(base_block["text"].strip()) <= 32
        and len(next_block["text"].strip()) <= 32
    )


def is_hwp_short_fragment(block: dict) -> bool:
    if block["block_type"] not in {"paragraph", "heading"}:
        return False
    text = block["text"].strip()
    if len(text) > 12:
        return False
    if re.search(r"\d", text):
        return False
    if BULLET_PATTERN.match(text):
        return False
    if ASCII_ROMAN_ONLY_PATTERN.fullmatch(text) or is_hwp_cover_heading(text):
        return False
    return True


def cleanup_hwp_blocks(raw_blocks: list[dict]) -> list[dict]:
    if not raw_blocks:
        return raw_blocks

    merged_blocks = []
    skip_next = False
    for index, block in enumerate(raw_blocks):
        if skip_next:
            skip_next = False
            continue
        if (
            ASCII_ROMAN_ONLY_PATTERN.fullmatch(block["text"].strip())
            and index + 1 < len(raw_blocks)
            and len(raw_blocks[index + 1]["text"].strip()) <= 24
            and raw_blocks[index + 1]["block_type"] in {"paragraph", "heading"}
        ):
            merged_blocks.append(
                {
                    **block,
                    "block_type": "heading",
                    "text": f"{block['text'].strip()} {raw_blocks[index + 1]['text'].strip()}",
                    "merged_block_count": block.get("merged_block_count", 1) + raw_blocks[index + 1].get("merged_block_count", 1),
                    "normalization_actions": "|".join(
                        value
                        for value in [block.get("normalization_actions", ""), "merged_ascii_roman_heading"]
                        if value
                    ),
                }
            )
            skip_next = True
            continue
        normalized_text = normalize_hwp_label_text(block["text"])
        if normalized_text != block["text"]:
            merged_blocks.append(
                {
                    **block,
                    "text": normalized_text,
                    "normalization_actions": "|".join(
                        value for value in [block.get("normalization_actions", ""), "normalized_compact_label"] if value
                    ),
                }
            )
            continue
        merged_blocks.append(block)

    first_main_heading_index = next(
        (index for index, block in enumerate(merged_blocks) if block["block_type"] == "heading" and is_hwp_cover_heading(block["text"])),
        None,
    )
    if first_main_heading_index is not None and first_main_heading_index > 0:
        merged_blocks = merged_blocks[first_main_heading_index:]

    if (
        len(merged_blocks) <= 12
        and not any(block["block_type"] in {"bullet", "note", "citation"} for block in merged_blocks)
        and sum(1 for block in merged_blocks if len(block["text"].strip()) <= 18) >= max(5, len(merged_blocks) - 1)
    ):
        return []

    for index, block in enumerate(merged_blocks[:-1]):
        if (
            block["block_type"] == "paragraph"
            and len(block["text"].strip()) <= 20
            and (len(block["text"].strip()) > 6 or re.search(r"\d", block["text"]))
            and merged_blocks[index + 1]["block_type"] in {"bullet", "note"}
        ):
            block["block_type"] = "heading"
            block["normalization_actions"] = "|".join(
                value for value in [block.get("normalization_actions", ""), "promoted_short_heading"] if value
            )

    for index, block in enumerate(merged_blocks[:-1]):
        next_block = merged_blocks[index + 1]
        if (
            block["block_type"] == "paragraph"
            and is_hwp_label_heading(block["text"].strip())
            and next_block["block_type"] in {"paragraph", "bullet", "note", "heading"}
            and not is_hwp_label_heading(next_block["text"].strip())
        ):
            block["block_type"] = "heading"
            block["normalization_actions"] = "|".join(
                value
                for value in [block.get("normalization_actions", ""), "promoted_compact_label_heading"]
                if value
            )

    stitched = []
    index = 0
    while index < len(merged_blocks):
        current = merged_blocks[index]
        if index + 1 < len(merged_blocks):
            next_block = merged_blocks[index + 1]
            if is_hwp_note_continuation(current, next_block):
                stitched.append(merge_hwp_blocks(current, next_block, "merged_note_continuation"))
                index += 2
                continue
            if is_hwp_caption_continuation(current, next_block):
                stitched.append(merge_hwp_blocks(current, next_block, "merged_caption_continuation"))
                index += 2
                continue
        stitched.append(current)
        index += 1

    merged_blocks = stitched
    merged_blocks = trim_trailing_contact_blocks(merged_blocks)

    cleaned = []
    index = 0
    while index < len(merged_blocks):
        if is_hwp_short_fragment(merged_blocks[index]):
            run_end = index
            while run_end < len(merged_blocks) and is_hwp_short_fragment(merged_blocks[run_end]):
                run_end += 1
            run_length = run_end - index
            tableish_run = run_length >= 2 and all(
                len(block["text"].strip()) <= 10 and not re.search(r"\d", block["text"]) for block in merged_blocks[index:run_end]
            )
            if run_length >= 3 or tableish_run:
                index = run_end
                continue
        cleaned.append(merged_blocks[index])
        index += 1

    return cleaned


def load_section_metadata(layout_payload: object) -> dict[str, dict]:
    if isinstance(layout_payload, dict) and "sections" in layout_payload:
        return {section["section_name"]: section for section in layout_payload["sections"]}
    if isinstance(layout_payload, list):
        return {section["section_name"]: section for section in layout_payload}
    return {}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--document-id", required=True)
    parser.add_argument("--out-root", required=True)
    args = parser.parse_args()

    out_root = Path(args.out_root)
    blocks_path = out_root / "work/02_structured-extraction/text" / f"{args.document_id}_blocks.json"
    layout_path = out_root / "work/02_structured-extraction/layout" / f"{args.document_id}_layout.json"
    manifest_path = out_root / "work/02_structured-extraction/manifests" / f"{args.document_id}_manifest.json"
    if not blocks_path.exists():
        raise FileNotFoundError(f"Missing text block file: {blocks_path}")
    if not layout_path.exists():
        raise FileNotFoundError(f"Missing layout file: {layout_path}")
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing manifest file: {manifest_path}")

    blocks = json.loads(blocks_path.read_text(encoding="utf-8"))
    layout_payload = json.loads(layout_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    section_meta = load_section_metadata(layout_payload)
    source_format = manifest.get("source_format", "").lower()

    normalized_dir = out_root / "work/03_processing/normalized"
    normalized_dir.mkdir(parents=True, exist_ok=True)

    grouped_blocks: dict[str, list[dict]] = defaultdict(list)
    for block in blocks:
        page_no = str(block["page_no_or_sheet_name"])
        grouped_blocks[page_no].append(block)

    ordered_keys = []
    for key in section_meta:
        if key in grouped_blocks:
            ordered_keys.append(key)
    for key in grouped_blocks:
        if key not in ordered_keys:
            ordered_keys.append(key)

    page_outputs = []
    paragraph_outputs = []
    paragraph_counter = 0
    skipped_noise_count = 0

    for page_no in ordered_keys:
        page_blocks = sorted(grouped_blocks[page_no], key=lambda item: item["block_order"])
        clean_text_parts = []
        text_block_count = 0
        normalized_blocks = []

        for page_block_order, block in enumerate(page_blocks, start=1):
            text = normalize_text(block.get("text", ""))
            if not text:
                continue
            source_block_type = block.get("block_type", "paragraph")
            for unit in split_structured_text_units(text, source_block_type):
                if is_structured_noise_text(unit["text"]):
                    skipped_noise_count += 1
                    continue
                block_type = classify_text_block(unit["text"], source_block_type)
                normalized_blocks.append(
                    {
                        "document_id": args.document_id,
                        "page_no": page_no,
                        "page_block_order": page_block_order,
                        "block_type": block_type,
                        "text": unit["text"],
                        "source_line_count": unit["source_line_count"],
                        "merged_block_count": 1,
                        "normalization_actions": "split_multiline_structured_block" if unit["source_line_count"] > 1 else "",
                        "source_mode": manifest.get("source_format", "structured"),
                    }
                )

        normalized_blocks = trim_leading_cover_markers(normalized_blocks)

        if source_format == "hwp":
            normalized_blocks = cleanup_hwp_blocks(normalized_blocks)

        for page_block_order, block in enumerate(normalized_blocks, start=1):
            paragraph_counter += 1
            text_block_count += 1
            clean_text_parts.append(block["text"])
            paragraph_outputs.append(
                {
                    "paragraph_id": f"PAR-{args.document_id}-{paragraph_counter:05d}",
                    "document_id": args.document_id,
                    "page_no": page_no,
                    "page_block_order": page_block_order,
                    "block_type": block["block_type"],
                    "text": block["text"],
                    "source_line_count": block["source_line_count"],
                    "merged_block_count": block["merged_block_count"],
                    "normalization_actions": block["normalization_actions"],
                    "source_mode": block["source_mode"],
                }
            )

        page_outputs.append(
            {
                "document_id": args.document_id,
                "page_no": page_no,
                "clean_text": "\n\n".join(clean_text_parts).strip(),
                "text_block_count": text_block_count,
                "table_block_count": 0,
                "metadata": section_meta.get(page_no, {}),
            }
        )

    summary_payload = {
        "document_id": args.document_id,
        "source_text_block_path": str(blocks_path.relative_to(out_root)),
        "page_count": len(page_outputs),
        "paragraph_count": len(paragraph_outputs),
        "text_paragraph_count": len(paragraph_outputs),
        "table_block_count": 0,
        "removed_footer_count": 0,
        "skipped_table_overlap_count": 0,
        "skipped_noise_count": skipped_noise_count,
        "merge_count": sum(
            1
            for row in paragraph_outputs
            if any(action.startswith("merged_") for action in row.get("normalization_actions", "").split("|") if action)
        ),
    }

    page_output_path = normalized_dir / f"{args.document_id}__pages-clean.json"
    paragraph_output_path = normalized_dir / f"{args.document_id}__paragraphs.json"
    paragraph_csv_path = normalized_dir / f"{args.document_id}__paragraphs.csv"
    summary_path = normalized_dir / f"{args.document_id}__text-normalization-report.json"

    write_json(page_output_path, page_outputs)
    write_json(paragraph_output_path, paragraph_outputs)
    write_json(summary_path, summary_payload)
    write_csv(
        paragraph_csv_path,
        paragraph_outputs,
        [
            "paragraph_id",
            "document_id",
            "page_no",
            "page_block_order",
            "block_type",
            "text",
            "source_line_count",
            "merged_block_count",
            "normalization_actions",
            "source_mode",
        ],
    )


if __name__ == "__main__":
    main()
