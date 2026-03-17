#!/usr/bin/env python3
"""Build source asset and derived-to-source mappings from current ontology content."""

from __future__ import annotations

import argparse
import csv
import sqlite3
from pathlib import Path


def guess_asset_path(document_id: str, source_format: str, source_rel_path: str, internal_path: str, repo_root: Path) -> str:
    extension = source_format.lower()
    if extension in {"pdf", "hwp", "hwpx"}:
        candidate = repo_root / "tmp" / f"{document_id}.{extension}"
        if candidate.exists():
            return str(candidate.relative_to(repo_root))
    if source_rel_path and internal_path:
        return f"{source_rel_path}::{internal_path}"
    return source_rel_path or internal_path or ""


def guess_mime_type(source_format: str) -> str:
    return {
        "pdf": "application/pdf",
        "hwp": "application/x-hwp",
        "hwpx": "application/x-hwp+zip",
    }.get(source_format.lower(), "application/octet-stream")


def guess_mime_type_from_asset_path(asset_path: str) -> str:
    suffix = Path(asset_path).suffix.lower()
    return {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".bmp": "image/bmp",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".svg": "image/svg+xml",
        ".tif": "image/tiff",
        ".tiff": "image/tiff",
    }.get(suffix, "application/octet-stream")


def infer_asset_type(source_format: str, location_type: str) -> str:
    if source_format.lower() == "pdf" and location_type in {"page_or_section", "page_range"}:
        return "pdf_page"
    if source_format.lower() in {"hwp", "hwpx"}:
        return "document_section"
    return "document_fragment"


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", required=True)
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--out-assets-csv", required=True)
    parser.add_argument("--out-map-csv", required=True)
    args = parser.parse_args()

    repo_root = Path(args.repo_root)
    connection = sqlite3.connect(args.db_path)
    connection.row_factory = sqlite3.Row
    try:
        rows = connection.execute(
            """
            SELECT
                d.document_id,
                d.source_format,
                d.source_rel_path,
                d.internal_path,
                dr.derived_representation_id,
                dr.source_object_type,
                dr.source_object_id,
                dr.location_type,
                dr.location_value,
                ef.asset_path AS figure_asset_path,
                ef.figure_type,
                ef.page_no AS figure_page_no
            FROM derived_representations dr
            JOIN documents d ON d.document_id = dr.document_id
            LEFT JOIN evidence_figures ef
                ON ef.figure_id = dr.source_object_id
               AND dr.source_object_type = 'figure'
            ORDER BY d.document_id, dr.location_value, dr.derived_representation_id
            """
        ).fetchall()

        assets: dict[tuple[str, str], dict[str, object]] = {}
        mappings: list[dict[str, object]] = []

        for row in rows:
            if row["source_object_type"] == "figure" and row["figure_asset_path"]:
                location_value = row["figure_page_no"] or row["location_value"] or "document"
                key = ("figure", row["source_object_id"])
            else:
                location_value = row["location_value"] or "document"
                key = (row["document_id"], location_value)
            if key not in assets:
                if row["source_object_type"] == "figure" and row["figure_asset_path"]:
                    asset_type = "figure_image"
                    mime_type = guess_mime_type_from_asset_path(row["figure_asset_path"])
                    asset_path_or_url = row["figure_asset_path"]
                    quality_status = "source_image"
                    notes = f"Figure asset for {row['source_object_id']}"
                else:
                    asset_type = infer_asset_type(row["source_format"], row["location_type"])
                    mime_type = guess_mime_type(row["source_format"])
                    asset_path_or_url = guess_asset_path(
                        document_id=row["document_id"],
                        source_format=row["source_format"],
                        source_rel_path=row["source_rel_path"],
                        internal_path=row["internal_path"],
                        repo_root=repo_root,
                    )
                    quality_status = "derived_locator"
                    notes = f"Derived from document location {location_value}"
                asset_id = f"SRC-{row['document_id']}-{len(assets) + 1:04d}"
                assets[key] = {
                    "source_asset_id": asset_id,
                    "document_id": row["document_id"],
                    "asset_type": asset_type,
                    "mime_type": mime_type,
                    "asset_path_or_url": asset_path_or_url,
                    "page_no": location_value if not str(location_value).startswith("section") else "",
                    "section_id": location_value if str(location_value).startswith("section") else "",
                    "bbox_json": "",
                    "thumbnail_path": "",
                    "quality_status": quality_status,
                    "notes": notes,
                }
            mappings.append(
                {
                    "derived_to_source_asset_map_id": f"DSA-{row['derived_representation_id']}",
                    "derived_representation_id": row["derived_representation_id"],
                    "source_asset_id": assets[key]["source_asset_id"],
                    "mapping_type": "direct_asset" if row["source_object_type"] == "figure" and row["figure_asset_path"] else "location_bucket",
                    "is_primary": 1,
                    "notes": "",
                }
            )

        asset_rows = list(assets.values())
        write_csv(
            Path(args.out_assets_csv),
            asset_rows,
            [
                "source_asset_id",
                "document_id",
                "asset_type",
                "mime_type",
                "asset_path_or_url",
                "page_no",
                "section_id",
                "bbox_json",
                "thumbnail_path",
                "quality_status",
                "notes",
            ],
        )
        write_csv(
            Path(args.out_map_csv),
            mappings,
            [
                "derived_to_source_asset_map_id",
                "derived_representation_id",
                "source_asset_id",
                "mapping_type",
                "is_primary",
                "notes",
            ],
        )

        connection.executemany(
            """
            INSERT OR REPLACE INTO source_assets (
                source_asset_id,
                document_id,
                asset_type,
                mime_type,
                asset_path_or_url,
                page_no,
                section_id,
                bbox_json,
                thumbnail_path,
                quality_status,
                notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    row["source_asset_id"],
                    row["document_id"],
                    row["asset_type"],
                    row["mime_type"],
                    row["asset_path_or_url"],
                    row["page_no"],
                    row["section_id"],
                    row["bbox_json"],
                    row["thumbnail_path"],
                    row["quality_status"],
                    row["notes"],
                )
                for row in asset_rows
            ],
        )
        connection.executemany(
            """
            INSERT OR REPLACE INTO derived_to_source_asset_map (
                derived_to_source_asset_map_id,
                derived_representation_id,
                source_asset_id,
                mapping_type,
                is_primary,
                notes
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    row["derived_to_source_asset_map_id"],
                    row["derived_representation_id"],
                    row["source_asset_id"],
                    row["mapping_type"],
                    row["is_primary"],
                    row["notes"],
                )
                for row in mappings
            ],
        )
        connection.commit()
    finally:
        connection.close()

    print(f"Source assets: {len(asset_rows)}")
    print(f"Derived to source mappings: {len(mappings)}")


if __name__ == "__main__":
    main()
