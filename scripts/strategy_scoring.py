#!/usr/bin/env python3
"""Shared scoring helpers for strategy classification workflows."""

from __future__ import annotations

import re
import unicodedata


GENERIC_TOKENS = {
    "",
    "및",
    "전략",
    "혁신",
    "도약",
    "확산",
    "선점",
    "확보",
    "기술",
    "산업",
    "서비스",
    "자립",
    "중심국가",
    "미래",
    "글로벌",
    "지능형",
    "핵심",
    "육성",
}


# Only use a domain fallback where the existing ontology already has a stable
# one-to-one dominant strategy interpretation.
PRIMARY_TECH_DOMAIN_STRATEGY_MAP = {
    "인공지능": "STR-001",
    "에너지": "STR-006",
    "이차전지": "STR-002",
    "차세대통신": "STR-004",
    "반도체디스플레이": "STR-002",
    "양자": "STR-007",
    "첨단바이오": "STR-003",
    "우주항공": "STR-005",
    "해양": "STR-005",
    "첨단모빌리티": "STR-009",
}


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value or "").lower()
    return re.sub(r"\s+", "", normalized)


def strategy_tokens(label: str) -> list[str]:
    tokens = []
    for token in re.split(r"[·(),/\- ]+", label):
        normalized = normalize_text(token)
        if normalized and normalized not in GENERIC_TOKENS and len(normalized) >= 2:
            tokens.append(normalized)
    return tokens


def should_boost_label_match(value: str) -> bool:
    normalized = normalize_text(value)
    if not normalized:
        return False
    if re.search(r"[a-z0-9]", normalized):
        return True
    return len(normalized) >= 3


def score_strategy(
    text_bundle: str,
    title: str,
    strategy_id: str,
    strategy_label: str,
    vocab_entry: dict | None,
    *,
    focus_text: str = "",
    primary_tech_domain: str = "",
) -> int:
    score = 0
    vocabulary = vocab_entry or {}
    normalized_bundle = normalize_text(text_bundle)
    normalized_title = normalize_text(title)
    normalized_label = normalize_text(strategy_label)
    normalized_focus = normalize_text(focus_text)

    if normalized_label and normalized_label in normalized_bundle:
        score += 8

    token_hits = 0
    for token in strategy_tokens(strategy_label):
        if token in normalized_bundle:
            token_hits += 1
    score += min(token_hits, 3) * 2

    for alias in vocabulary.get("aliases", []):
        normalized_alias = normalize_text(alias)
        if not normalized_alias or normalized_alias not in normalized_bundle:
            continue
        score += 3
        if should_boost_label_match(alias) and normalized_focus and normalized_alias in normalized_focus:
            score += 1

    for alias in vocabulary.get("policy_aliases", []):
        normalized_alias = normalize_text(alias)
        if normalized_alias and (
            normalized_alias in normalized_title or normalized_alias in normalized_bundle
        ):
            score += 4

    if primary_tech_domain and PRIMARY_TECH_DOMAIN_STRATEGY_MAP.get(primary_tech_domain) == strategy_id:
        score += 4

    return score
