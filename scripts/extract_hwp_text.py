#!/usr/bin/env python3
"""Rough pure-text extractor for legacy HWP v5 documents.

This path is intentionally text-first. It preserves paragraph-like evidence
units from BodyText section streams and defers tables / figures to later work.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
import zipfile
import zlib
from pathlib import Path


RUNTIME_PACKAGES = [
    ("olefile", ".whl"),
]

HWP_PARA_HEADER_TAG = 66
HWP_PARA_TEXT_TAG = 67
CONTROL_CHAR_PATTERN = re.compile(r"[\u0000-\u0008\u000b-\u001f\u007f]")
MULTI_CJK_NOISE_PATTERN = re.compile(r"[\u3400-\u4DBF\u4E00-\u9FFF]{2,}")


def ensure_runtime(loader_root: Path) -> None:
    lib_dir = loader_root / "lib"
    if (lib_dir / "olefile").exists():
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


def clean_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = text.replace("\r", "\n")
    text = CONTROL_CHAR_PATTERN.sub("", text)
    text = MULTI_CJK_NOISE_PATTERN.sub("", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def maybe_decompress_hwp_stream(payload: bytes) -> bytes:
    try:
        return zlib.decompress(payload, -15)
    except zlib.error:
        return payload


def iter_hwp_records(payload: bytes):
    cursor = 0
    total = len(payload)
    while cursor + 4 <= total:
        header = int.from_bytes(payload[cursor : cursor + 4], "little")
        cursor += 4
        tag_id = header & 0x3FF
        level = (header >> 10) & 0x3FF
        size = (header >> 20) & 0xFFF
        if size == 0xFFF:
            if cursor + 4 > total:
                break
            size = int.from_bytes(payload[cursor : cursor + 4], "little")
            cursor += 4
        if cursor + size > total:
            break
        record_payload = payload[cursor : cursor + size]
        cursor += size
        yield tag_id, level, record_payload


def decode_para_text(record_payload: bytes) -> str:
    try:
        text = record_payload.decode("utf-16le", errors="ignore")
    except Exception:
        return ""
    text = text.replace("\u000d", "\n")
    text = text.replace("\u001e", "")
    text = text.replace("\u001f", "")
    return clean_text(text)


def extract_section_paragraphs(section_bytes: bytes) -> list[str]:
    paragraphs: list[str] = []
    current_parts: list[str] = []
    payload = maybe_decompress_hwp_stream(section_bytes)

    for tag_id, _level, record_payload in iter_hwp_records(payload):
        if tag_id == HWP_PARA_HEADER_TAG:
            if current_parts:
                paragraph_text = clean_text(" ".join(part for part in current_parts if part))
                if paragraph_text:
                    paragraphs.append(paragraph_text)
            current_parts = []
            continue
        if tag_id == HWP_PARA_TEXT_TAG:
            para_text = decode_para_text(record_payload)
            if para_text:
                current_parts.append(para_text)

    if current_parts:
        paragraph_text = clean_text(" ".join(part for part in current_parts if part))
        if paragraph_text:
            paragraphs.append(paragraph_text)

    return paragraphs


def cleanup_outputs(document_id: str, text_dir: Path, layout_dir: Path, manifest_dir: Path) -> None:
    for target_dir in [text_dir, layout_dir, manifest_dir]:
        for path in target_dir.glob(f"{document_id}*"):
            if path.is_file():
                path.unlink()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-hwp", required=True)
    parser.add_argument("--document-id", required=True)
    parser.add_argument("--registry-id", required=True)
    parser.add_argument("--out-root", required=True)
    args = parser.parse_args()

    out_root = Path(args.out_root)
    loader_root = out_root / "tmp" / "olefile_loader"
    ensure_runtime(loader_root)

    import olefile  # type: ignore

    text_dir = out_root / "work/02_structured-extraction/text"
    layout_dir = out_root / "work/02_structured-extraction/layout"
    manifest_dir = out_root / "work/02_structured-extraction/manifests"
    text_dir.mkdir(parents=True, exist_ok=True)
    layout_dir.mkdir(parents=True, exist_ok=True)
    manifest_dir.mkdir(parents=True, exist_ok=True)
    cleanup_outputs(args.document_id, text_dir, layout_dir, manifest_dir)

    ole = olefile.OleFileIO(args.source_hwp)
    body_sections = []
    for entry in ole.listdir(streams=True, storages=False):
        if len(entry) == 2 and entry[0] == "BodyText" and entry[1].startswith("Section"):
            section_index = int(entry[1].replace("Section", "") or 0)
            body_sections.append((section_index, entry))
    body_sections.sort(key=lambda item: item[0])

    text_blocks = []
    layout_sections = []
    block_order = 0
    section_count = 0

    for section_index, entry in body_sections:
        section_name = f"section{section_index}"
        section_bytes = ole.openstream(entry).read()
        paragraphs = extract_section_paragraphs(section_bytes)
        layout_sections.append(
            {
                "section_name": section_name,
                "source_path": "/".join(entry),
                "paragraph_count": len(paragraphs),
            }
        )
        section_count += 1
        for paragraph in paragraphs:
            block_order += 1
            text_blocks.append(
                {
                    "evidence_id": f"EVD-{args.document_id}-{block_order:05d}",
                    "document_id": args.document_id,
                    "page_no_or_sheet_name": section_name,
                    "block_order": block_order,
                    "block_type": "paragraph",
                    "text": paragraph,
                    "bbox": None,
                    "extraction_method": "hwp-v5-ole-rough-text",
                    "extraction_confidence": "medium",
                }
            )

    ole.close()

    text_path = text_dir / f"{args.document_id}_blocks.json"
    layout_path = layout_dir / f"{args.document_id}_layout.json"
    manifest_path = manifest_dir / f"{args.document_id}_manifest.json"

    write_json(text_path, text_blocks)
    write_json(
        layout_path,
        {
            "document_id": args.document_id,
            "sections": layout_sections,
        },
    )
    write_json(
        manifest_path,
        {
            "document_id": args.document_id,
            "registry_id": args.registry_id,
            "source_rel_path": relative_or_absolute(args.source_hwp, out_root),
            "internal_path": "",
            "source_format": "hwp",
            "extraction_run_id": "text-first-hwp-v1",
            "page_count_or_sheet_count": section_count,
            "processing_status": "completed",
            "quality_notes": [
                "Legacy HWP v5 text was extracted from BodyText section streams.",
                "This is a rough text-first path and does not yet recover tables or figures.",
                "Paragraph boundaries are inferred from ParaHeader / ParaText records.",
            ],
            "text_path": str(text_path.relative_to(out_root)),
            "layout_path": str(layout_path.relative_to(out_root)),
            "tables": [],
            "figures": [],
            "counts": {
                "evidence_units": len(text_blocks),
                "tables": 0,
                "figures": 0,
            },
        },
    )


if __name__ == "__main__":
    main()
