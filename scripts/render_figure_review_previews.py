#!/usr/bin/env python3
"""Render figure assets into previewable PNG/JPEG copies for manual review."""

from __future__ import annotations

import argparse
import csv
import shutil
import struct
import zlib
from pathlib import Path


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def write_chunk(handle, chunk_type: bytes, data: bytes) -> None:
    handle.write(struct.pack(">I", len(data)))
    handle.write(chunk_type)
    handle.write(data)
    crc = zlib.crc32(chunk_type)
    crc = zlib.crc32(data, crc)
    handle.write(struct.pack(">I", crc & 0xFFFFFFFF))


def bmp_to_png_bytes(path: Path) -> bytes:
    data = path.read_bytes()
    if data[:2] != b"BM":
        raise ValueError(f"Unsupported BMP header: {path}")

    pixel_offset = struct.unpack_from("<I", data, 10)[0]
    dib_header_size = struct.unpack_from("<I", data, 14)[0]
    if dib_header_size < 40:
        raise ValueError(f"Unsupported DIB header size: {dib_header_size}")

    width = struct.unpack_from("<i", data, 18)[0]
    height = struct.unpack_from("<i", data, 22)[0]
    planes = struct.unpack_from("<H", data, 26)[0]
    bits_per_pixel = struct.unpack_from("<H", data, 28)[0]
    compression = struct.unpack_from("<I", data, 30)[0]

    if planes != 1 or compression != 0 or bits_per_pixel not in {24, 32}:
        raise ValueError(
            f"Unsupported BMP format for {path.name}: planes={planes} bpp={bits_per_pixel} compression={compression}"
        )

    top_down = height < 0
    width = abs(width)
    height = abs(height)
    bytes_per_pixel = bits_per_pixel // 8
    row_stride = ((bits_per_pixel * width + 31) // 32) * 4

    rows: list[bytes] = []
    for row_index in range(height):
        start = pixel_offset + row_index * row_stride
        row = data[start : start + row_stride]
        converted = bytearray()
        for col_index in range(width):
            base = col_index * bytes_per_pixel
            blue = row[base]
            green = row[base + 1]
            red = row[base + 2]
            converted.extend((red, green, blue))
            if bytes_per_pixel == 4:
                alpha = row[base + 3]
                converted.append(alpha)
        rows.append(bytes(converted))

    if not top_down:
        rows.reverse()

    color_type = 6 if bytes_per_pixel == 4 else 2
    ihdr = struct.pack(">IIBBBBB", width, height, 8, color_type, 0, 0, 0)
    raw_scanlines = b"".join(b"\x00" + row for row in rows)
    compressed = zlib.compress(raw_scanlines, level=9)

    output = bytearray(PNG_SIGNATURE)
    from io import BytesIO

    buffer = BytesIO()
    buffer.write(output)
    write_chunk(buffer, b"IHDR", ihdr)
    write_chunk(buffer, b"IDAT", compressed)
    write_chunk(buffer, b"IEND", b"")
    return buffer.getvalue()


def load_queue_rows(queue_csv: Path) -> list[dict[str, str]]:
    with queue_csv.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def render_preview(asset_path: Path, target_path: Path) -> str:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    suffix = asset_path.suffix.lower()
    if suffix == ".bmp":
        target_path.write_bytes(bmp_to_png_bytes(asset_path))
        return "bmp_to_png"

    shutil.copy2(asset_path, target_path)
    return "copied"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--document-id", required=True)
    parser.add_argument("--out-root", required=True)
    parser.add_argument("--queue-csv")
    parser.add_argument("--preview-dir")
    args = parser.parse_args()

    out_root = Path(args.out_root)
    queue_csv = (
        Path(args.queue_csv)
        if args.queue_csv
        else out_root / "qa/extraction/review_queues" / f"{args.document_id}__figure-review-queue.csv"
    )
    preview_dir = (
        Path(args.preview_dir)
        if args.preview_dir
        else out_root / "work/02_structured-extraction/figures/_review_previews" / args.document_id
    )

    rows = load_queue_rows(queue_csv)
    rendered = []
    for row in rows:
        asset_path = out_root / row["asset_path"]
        if not asset_path.exists():
            continue
        suffix = asset_path.suffix.lower()
        preview_name = f"{row['review_item_id']}__{asset_path.stem}{'.png' if suffix == '.bmp' else suffix}"
        preview_path = preview_dir / preview_name
        mode = render_preview(asset_path, preview_path)
        rendered.append(
            {
                "review_item_id": row["review_item_id"],
                "figure_id": row["figure_id"],
                "source_asset_path": row["asset_path"],
                "preview_path": str(preview_path.relative_to(out_root)),
                "render_mode": mode,
            }
        )

    manifest_path = preview_dir / "preview-manifest.csv"
    with manifest_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["review_item_id", "figure_id", "source_asset_path", "preview_path", "render_mode"],
        )
        writer.writeheader()
        for row in rendered:
            writer.writerow(row)

    print(preview_dir)
    print(manifest_path)


if __name__ == "__main__":
    main()
