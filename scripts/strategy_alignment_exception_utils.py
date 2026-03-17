#!/usr/bin/env python3
"""Helpers for strategy/reference alignment exceptions."""

from __future__ import annotations

import csv
from pathlib import Path


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def load_strategy_alignment_exceptions(path: Path | None) -> dict[str, list[dict[str, str]]]:
    if path is None:
        return {}
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in read_csv_rows(path):
        strategy_id = (row.get("strategy_id") or "").strip()
        if not strategy_id:
            continue
        grouped.setdefault(strategy_id, []).append(row)
    return grouped


def summarize_exception_ids(rows: list[dict[str, str]]) -> str:
    return " | ".join(row["exception_id"] for row in rows if row.get("exception_id"))


def summarize_exception_notes(rows: list[dict[str, str]]) -> str:
    notes: list[str] = []
    for row in rows:
        exception_id = row.get("exception_id", "").strip()
        reference_document_id = row.get("reference_document_id", "").strip()
        reference_table_id = row.get("reference_table_id", "").strip()
        reference_sequence_no = row.get("reference_sequence_no", "").strip()
        resolution_status = row.get("resolution_status", "").strip()
        parts = [
            part
            for part in [
                exception_id,
                f"{reference_document_id}/{reference_table_id}#{reference_sequence_no}".strip("/#"),
                resolution_status,
            ]
            if part
        ]
        if parts:
            notes.append(": ".join([parts[0], " | ".join(parts[1:])]) if len(parts) > 1 else parts[0])
    return " || ".join(notes)
