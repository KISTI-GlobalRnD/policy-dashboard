#!/usr/bin/env python3
"""Load normalized evidence artifacts into the SQLite ontology store."""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from pathlib import Path


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def get_known_documents(connection: sqlite3.Connection) -> set[str]:
    cursor = connection.execute("SELECT document_id FROM documents")
    return {row[0] for row in cursor.fetchall()}


def repo_relative(path: Path, repo_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def derive_figure_quality_status(review_row: dict | None, payload: dict) -> str:
    if review_row:
        explicit = (review_row.get("quality_status") or "").strip()
        if explicit:
            return explicit
        review_status = (review_row.get("review_status") or "").strip()
        keep_for_dashboard = (review_row.get("keep_for_dashboard") or "").strip()
        suggested_class = (review_row.get("suggested_class") or "").strip()
        if review_status == "reviewed":
            if keep_for_dashboard == "yes":
                return "dashboard_ready"
            if suggested_class == "support_render":
                return "support_render"
            if suggested_class in {"deferred_hold_render", "deferred_hold_image"}:
                return "deferred_hold"
            if keep_for_dashboard == "no":
                return "decorative_excluded"
        return "review_required"

    if payload.get("figure_type", "") == "pdf_page_image":
        return "support_render"
    return "extracted"


def append_figure_records(
    evidence_payload: list[tuple],
    representation_payload: list[tuple],
    payload: dict,
    repo_root: Path,
    figure_json_path: Path,
    review_row: dict | None = None,
) -> None:
    document_id = payload.get("document_id", "")
    figure_id = payload.get("figure_id", figure_json_path.stem)
    caption = ((review_row or {}).get("caption") or payload.get("caption") or "").strip()
    summary = ((review_row or {}).get("summary") or payload.get("summary") or "").strip()
    page_value = ((review_row or {}).get("location") or payload.get("page_no_or_sheet_name") or "").strip()
    asset_path = ((review_row or {}).get("asset_path") or payload.get("asset_path") or "").strip()
    quality_status = derive_figure_quality_status(review_row, payload)
    review_status = ((review_row or {}).get("review_status") or "review_required").strip() or "review_required"

    notes = []
    if payload.get("parent_table_id"):
        notes.append(f"parent_table_id={payload['parent_table_id']}")
    if payload.get("internal_asset_path"):
        notes.append(f"internal_asset_path={payload['internal_asset_path']}")
    if payload.get("binary_item_id"):
        notes.append(f"binary_item_id={payload['binary_item_id']}")
    if payload.get("paragraph_id") not in (None, "", 0, "0", 2147483648, "2147483648"):
        notes.append(f"paragraph_id={payload['paragraph_id']}")
    if review_row and review_row.get("reviewer_notes"):
        notes.append(f"reviewer_notes={review_row['reviewer_notes']}")
    notes_text = " | ".join(notes)

    evidence_payload.append(
        (
            figure_id,
            document_id,
            figure_id,
            payload.get("figure_type", ""),
            caption,
            page_value,
            asset_path,
            summary,
            quality_status,
            notes_text,
        )
    )
    representation_payload.append(
        (
            f"DRV-{figure_id}",
            document_id,
            None,
            "figure_or_diagram",
            "figure",
            figure_id,
            "page_or_section",
            page_value,
            summary or caption,
            repo_relative(figure_json_path, repo_root),
            "",
            "phase1_figure_extraction_v1",
            quality_status,
            review_status,
            notes_text,
        )
    )


def load_paragraphs(connection: sqlite3.Connection, normalized_dir: Path) -> tuple[int, int]:
    known_documents = get_known_documents(connection)
    paragraph_count = 0
    representation_count = 0

    for paragraph_csv in sorted(normalized_dir.glob("DOC-*__paragraphs.csv")):
        document_id = paragraph_csv.name.split("__", 1)[0]
        if document_id not in known_documents:
            continue

        rows = read_csv_rows(paragraph_csv)
        evidence_payload = []
        representation_payload = []
        for row in rows:
            evidence_payload.append(
                (
                    row["paragraph_id"],
                    document_id,
                    row["paragraph_id"],
                    row["page_no"],
                    int(row["page_block_order"]),
                    row["block_type"],
                    row["text"],
                    row["source_mode"],
                    int(row["source_line_count"]),
                    int(row["merged_block_count"]),
                    "review_required",
                    row["normalization_actions"],
                )
            )
            representation_payload.append(
                (
                    f"DRV-{row['paragraph_id']}",
                    document_id,
                    None,
                    "normalized_paragraph",
                    "paragraph",
                    row["paragraph_id"],
                    "page_or_section",
                    row["page_no"],
                    row["text"],
                    str(paragraph_csv.relative_to(normalized_dir.parent.parent.parent)),
                    "",
                    "phase1_text_normalization_v1",
                    "usable",
                    "review_required",
                    row["normalization_actions"],
                )
            )

        connection.executemany(
            """
            INSERT OR REPLACE INTO evidence_paragraphs (
                evidence_paragraph_id,
                document_id,
                paragraph_id,
                page_no,
                page_block_order,
                block_type,
                text,
                source_mode,
                source_line_count,
                merged_block_count,
                review_status,
                notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            evidence_payload,
        )
        connection.executemany(
            """
            INSERT OR REPLACE INTO derived_representations (
                derived_representation_id,
                document_id,
                source_asset_id,
                representation_type,
                source_object_type,
                source_object_id,
                location_type,
                location_value,
                plain_text,
                structured_payload_path,
                table_json_path,
                normalization_version,
                quality_status,
                review_status,
                notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            representation_payload,
        )
        paragraph_count += len(evidence_payload)
        representation_count += len(representation_payload)

    return paragraph_count, representation_count


def load_canonical_tables(connection: sqlite3.Connection, instances_dir: Path) -> tuple[int, int]:
    known_documents = get_known_documents(connection)
    table_count = 0
    representation_count = 0

    for canonical_csv in sorted(instances_dir.glob("DOC-*__canonical-tables.csv")):
        document_id = canonical_csv.name.split("__", 1)[0]
        if document_id not in known_documents:
            continue

        rows = read_csv_rows(canonical_csv)
        evidence_payload = []
        representation_payload = []
        for row in rows:
            dashboard_ready = 1 if row["dashboard_ready"].strip().lower() == "yes" else 0
            location_value = row["page_start"]
            if row["page_end"] and row["page_end"] != row["page_start"]:
                location_value = f"{row['page_start']}-{row['page_end']}"
            evidence_payload.append(
                (
                    row["canonical_table_id"],
                    document_id,
                    row["canonical_table_id"],
                    row["title_hint"],
                    row["page_start"],
                    row["page_end"],
                    row["preferred_candidate_source"],
                    row["preferred_candidate_id"],
                    row["canonical_status"],
                    dashboard_ready,
                    row["notes"],
                )
            )
            representation_payload.append(
                (
                    f"DRV-{row['canonical_table_id']}",
                    document_id,
                    None,
                    "canonical_table",
                    "canonical_table",
                    row["canonical_table_id"],
                    "page_range",
                    location_value,
                    row["title_hint"],
                    str(canonical_csv.relative_to(instances_dir.parent.parent.parent)),
                    "",
                    "phase1_canonical_table_v1",
                    "usable" if dashboard_ready else "needs_review",
                    "reviewed" if dashboard_ready else "review_required",
                    row["notes"],
                )
            )

        connection.executemany(
            """
            INSERT OR REPLACE INTO evidence_tables (
                evidence_table_id,
                document_id,
                canonical_table_id,
                title_hint,
                page_start,
                page_end,
                preferred_candidate_source,
                preferred_candidate_id,
                canonical_status,
                dashboard_ready,
                notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            evidence_payload,
        )
        connection.executemany(
            """
            INSERT OR REPLACE INTO derived_representations (
                derived_representation_id,
                document_id,
                source_asset_id,
                representation_type,
                source_object_type,
                source_object_id,
                location_type,
                location_value,
                plain_text,
                structured_payload_path,
                table_json_path,
                normalization_version,
                quality_status,
                review_status,
                notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            representation_payload,
        )
        table_count += len(evidence_payload)
        representation_count += len(representation_payload)

    return table_count, representation_count


def load_figures(connection: sqlite3.Connection, figures_dir: Path) -> tuple[int, int]:
    known_documents = get_known_documents(connection)
    figure_count = 0
    representation_count = 0
    repo_root = figures_dir.parent.parent.parent
    reviewed_dir = repo_root / "qa/extraction/reviewed_queues"

    evidence_payload = []
    representation_payload = []
    raw_payloads_by_doc: dict[str, dict[str, tuple[dict, Path]]] = {}
    for figure_json in sorted(figures_dir.glob("FIG-DOC-*.json")):
        with figure_json.open(encoding="utf-8") as handle:
            payload = json.load(handle)

        document_id = payload.get("document_id", "")
        if document_id not in known_documents:
            continue

        figure_id = payload.get("figure_id", figure_json.stem)
        raw_payloads_by_doc.setdefault(document_id, {})[figure_id] = (payload, figure_json)

    processed_documents: set[str] = set()
    for reviewed_csv in sorted(reviewed_dir.glob("DOC-*__figure-review-reviewed.csv")):
        document_id = reviewed_csv.name.split("__", 1)[0]
        if document_id not in known_documents or document_id not in raw_payloads_by_doc:
            continue
        reviewed_rows = read_csv_rows(reviewed_csv)
        for review_row in reviewed_rows:
            figure_id = review_row.get("figure_id", "")
            payload_entry = raw_payloads_by_doc[document_id].get(figure_id)
            if not payload_entry:
                continue
            payload, figure_json = payload_entry
            append_figure_records(
                evidence_payload,
                representation_payload,
                payload,
                repo_root,
                figure_json,
                review_row=review_row,
            )
        processed_documents.add(document_id)

    for document_id, figure_entries in sorted(raw_payloads_by_doc.items()):
        if document_id in processed_documents:
            continue
        for payload, figure_json in figure_entries.values():
            append_figure_records(
                evidence_payload,
                representation_payload,
                payload,
                repo_root,
                figure_json,
            )

    if evidence_payload:
        connection.executemany(
            """
            INSERT OR REPLACE INTO evidence_figures (
                evidence_figure_id,
                document_id,
                figure_id,
                figure_type,
                caption,
                page_no,
                asset_path,
                summary_text,
                quality_status,
                notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            evidence_payload,
        )
        connection.executemany(
            """
            INSERT OR REPLACE INTO derived_representations (
                derived_representation_id,
                document_id,
                source_asset_id,
                representation_type,
                source_object_type,
                source_object_id,
                location_type,
                location_value,
                plain_text,
                structured_payload_path,
                table_json_path,
                normalization_version,
                quality_status,
                review_status,
                notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            representation_payload,
        )
        figure_count = len(evidence_payload)
        representation_count = len(representation_payload)

    return figure_count, representation_count


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", required=True)
    parser.add_argument("--normalized-dir", required=True)
    parser.add_argument("--instances-dir", required=True)
    parser.add_argument("--figures-dir", required=True)
    args = parser.parse_args()

    connection = sqlite3.connect(args.db_path)
    try:
        paragraph_count, paragraph_representation_count = load_paragraphs(connection, Path(args.normalized_dir))
        table_count, table_representation_count = load_canonical_tables(connection, Path(args.instances_dir))
        figure_count, figure_representation_count = load_figures(connection, Path(args.figures_dir))
        connection.commit()
    finally:
        connection.close()

    print(f"Loaded paragraphs: {paragraph_count}")
    print(f"Loaded paragraph representations: {paragraph_representation_count}")
    print(f"Loaded canonical tables: {table_count}")
    print(f"Loaded table representations: {table_representation_count}")
    print(f"Loaded figures: {figure_count}")
    print(f"Loaded figure representations: {figure_representation_count}")


if __name__ == "__main__":
    main()
