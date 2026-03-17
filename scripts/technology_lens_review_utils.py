#!/usr/bin/env python3
"""Utility helpers for technology lens review decisions."""

from __future__ import annotations

import hashlib
import re
import unicodedata


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value or "").lower()
    return re.sub(r"\s+", "", normalized)


def parse_ids(value: str) -> list[str]:
    tokens: list[str] = []
    for token in re.split(r"\s*\|\s*|\s*,\s*", value or ""):
        cleaned = token.strip()
        if cleaned:
            tokens.append(cleaned)
    return tokens


def normalize_source_policy_item_ids(value: str) -> str:
    unique_ids = sorted(set(parse_ids(value)))
    return " | ".join(unique_ids)


def build_decision_key(
    tech_domain_id: str,
    policy_id: str,
    resource_category_id: str,
    source_policy_item_ids: str,
) -> str:
    normalized_source_ids = normalize_source_policy_item_ids(source_policy_item_ids)
    source = "|".join(
        [
            tech_domain_id or "",
            policy_id or "",
            resource_category_id or "",
            normalized_source_ids,
        ]
    )
    digest = hashlib.sha1(source.encode("utf-8")).hexdigest()[:12]
    return f"TLR-{tech_domain_id}-{digest}"
