#!/usr/bin/env python3
"""Helpers for cleaning stale generated artifacts."""

from __future__ import annotations

from pathlib import Path


def cleanup_stale_files(directory: Path, keep_names: set[str], patterns: list[str]) -> list[str]:
    removed: list[str] = []
    if not directory.exists():
        return removed

    seen: set[str] = set()
    for pattern in patterns:
        for path in directory.glob(pattern):
            if not path.is_file():
                continue
            if path.name in keep_names or path.name in seen:
                continue
            path.unlink()
            removed.append(path.name)
            seen.add(path.name)
    return sorted(removed)
