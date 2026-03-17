#!/usr/bin/env python3
"""Build a paragraph-level classification template from normalized text."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sqlite3
from pathlib import Path

from strategy_scoring import normalize_text, score_strategy


RESOURCE_KEYWORDS = {
    "technology": [
        "개발",
        "고도화",
        "확보",
        "실증",
        "상용화 기술",
        "핵심기술",
        "원천기술",
        "프로토타입",
        "공정",
        "장비",
        "플랫폼",
    ],
    "infrastructure_policy": [
        "제도",
        "지원체계",
        "인프라",
        "센터",
        "클러스터",
        "특구",
        "펀드",
        "세제",
        "규제",
        "협의체",
        "입지",
        "예산",
        "거버넌스",
    ],
    "talent": [
        "인재",
        "인력",
        "양성",
        "교육",
        "교수",
        "연구자",
        "석박사",
        "채용",
        "전문인력",
        "인재양성",
    ],
}


SHORT_FRONT_MATTER_TEXTS = {
    "관계부처합동",
    "관계 부처 합동",
    "공개",
    "요약",
}


FRONT_MATTER_SUBSTRINGS = [
    "관계장관회의",
    "성장전략tf",
    "관계부처합동",
    "(공개)",
]


TITLEISH_KEYWORDS = [
    "추진계획",
    "국가전략",
    "지원방안",
    "정책방향",
    "육성 방안",
    "도약 전략",
]


ACTION_VERB_HINTS = [
    "추진",
    "지원",
    "강화",
    "확대",
    "육성",
    "확보",
    "구축",
    "도입",
    "실증",
    "개발",
    "양성",
    "정비",
    "개선",
    "조성",
    "전환",
]


SCAFFOLD_PATTERNS = [
    re.compile(r"^순\s*서$"),
    re.compile(r"^참고[.．]"),
    re.compile(r"^\(단위[:：]"),
    re.compile(r"^\([0-9]+\)\s*"),
    re.compile(r"^[➊➋➌➍➎❶❷❸❹❺]"),
]


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_taxonomy_rows(db_path: Path) -> tuple[list[sqlite3.Row], list[sqlite3.Row], dict[str, list[sqlite3.Row]]]:
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    try:
        strategy_rows = connection.execute("SELECT * FROM strategies ORDER BY display_order").fetchall()
        domain_rows = connection.execute("SELECT * FROM tech_domains ORDER BY display_order").fetchall()
        subdomain_rows = connection.execute(
            "SELECT * FROM tech_subdomains ORDER BY tech_domain_id, display_order"
        ).fetchall()
    finally:
        connection.close()

    subdomains_by_domain: dict[str, list[sqlite3.Row]] = {}
    for row in subdomain_rows:
        subdomains_by_domain.setdefault(row["tech_domain_id"], []).append(row)
    return strategy_rows, domain_rows, subdomains_by_domain


def suggest_resource_type(text: str) -> tuple[str, str, str]:
    scores = {}
    matches = {}
    for resource_type, keywords in RESOURCE_KEYWORDS.items():
        matched = [keyword for keyword in keywords if keyword in text]
        scores[resource_type] = len(matched)
        matches[resource_type] = matched

    best_type = max(scores, key=scores.get)
    best_score = scores[best_type]
    if best_score == 0:
        return "", "", "low"

    if list(scores.values()).count(best_score) > 1:
        return "", "", "low"

    confidence = "medium"
    if best_score >= 2:
        confidence = "high"
    return best_type, "|".join(matches[best_type]), confidence


def parse_page_rank(page_no: object) -> int | None:
    if isinstance(page_no, int):
        return page_no
    value = str(page_no or "").strip()
    if value.isdigit():
        return int(value)
    match = re.fullmatch(r"section(\d+)", value, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def is_front_matter(block_type: str, text: str, page_no: object) -> bool:
    stripped = text.strip()
    normalized = normalize_text(stripped)
    page_rank = parse_page_rank(page_no)

    if block_type == "heading":
        return True

    if not stripped:
        return True

    if stripped in SHORT_FRONT_MATTER_TEXTS:
        return True

    if re.fullmatch(r"\d{4}\.\s*\d{1,2}\.\s*\d{1,2}\.?", stripped):
        return True

    if any(token in normalized for token in FRONT_MATTER_SUBSTRINGS):
        return True

    if stripped.startswith(("Ⅰ.", "Ⅱ.", "Ⅲ.", "Ⅳ.", "Ⅴ.", "Ⅰ ", "Ⅱ ", "Ⅲ ", "Ⅳ ", "Ⅴ ")):
        return True

    if page_rank is not None and page_rank <= 2:
        if block_type == "paragraph" and len(stripped) <= 60:
            if any(keyword in stripped for keyword in TITLEISH_KEYWORDS):
                if not stripped.startswith(("□", "ㅇ", "①", "②", "③", "-", "•", "*")):
                    return True
        if len(stripped) <= 40 and not any(hint in stripped for hint in ACTION_VERB_HINTS):
            if not stripped.startswith(("□", "ㅇ", "①", "②", "③", "-", "•", "*")):
                return True

    return False


def is_scaffold_text(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return True
    return any(pattern.search(stripped) for pattern in SCAFFOLD_PATTERNS)


def has_action_hint(text: str) -> bool:
    return any(hint in text for hint in ACTION_VERB_HINTS)


def is_short_dash_or_arrow_scaffold(text: str) -> bool:
    stripped = text.strip()
    if not stripped.startswith(("- ", "⇨", "⇒")):
        return False
    if has_action_hint(stripped):
        return False
    return len(stripped) <= 45


def is_short_square_scaffold(text: str) -> bool:
    stripped = text.strip()
    if not stripped.startswith("□ "):
        return False
    if has_action_hint(stripped):
        return False
    return len(stripped) <= 30


def policy_item_candidate(block_type: str, text: str, page_no: object, prev_paragraph: dict | None = None) -> str:
    if block_type == "table_markdown":
        return "review"
    if block_type in {"note", "caption", "citation"}:
        return "review"
    if is_front_matter(block_type, text, page_no):
        return "no"
    if is_scaffold_text(text):
        return "no"
    if is_short_dash_or_arrow_scaffold(text):
        return "no"
    if is_short_square_scaffold(text):
        return "no"
    if prev_paragraph and str(prev_paragraph.get("page_no")) == str(page_no):
        prev_text = str(prev_paragraph.get("text", "")).strip()
        prev_block_type = str(prev_paragraph.get("block_type", ""))
        if prev_block_type == "heading" and block_type == "paragraph" and len(text.strip()) <= 25:
            return "no"
        if is_front_matter(prev_block_type, prev_text, prev_paragraph.get("page_no")):
            if block_type == "paragraph" and len(text.strip()) <= 25:
                return "no"
    if len(text.strip()) < 10:
        return "review"
    return "yes"


def confidence_from_score(score: int) -> str:
    if score >= 10:
        return "high"
    if score >= 6:
        return "medium"
    if score >= 4:
        return "low"
    return ""


def score_domain(text_bundle: str, document_title: str, domain_label: str, vocab_entry: dict) -> int:
    score = 0
    normalized_bundle = normalize_text(text_bundle)
    normalized_title = normalize_text(document_title)
    normalized_label = normalize_text(domain_label)

    if normalized_label and normalized_label in normalized_bundle:
        score += 8

    for alias in vocab_entry.get("aliases", []):
        normalized_alias = normalize_text(alias)
        if normalized_alias and normalized_alias in normalized_bundle:
            score += 3

    for alias in vocab_entry.get("policy_aliases", []):
        normalized_alias = normalize_text(alias)
        if normalized_alias and (
            normalized_alias in normalized_title or normalized_alias in normalized_bundle
        ):
            score += 4

    return score


def infer_subdomain(subdomains: list[sqlite3.Row], text_bundle: str) -> tuple[str, str]:
    normalized_bundle = normalize_text(text_bundle)
    best_subdomain_id = ""
    best_subdomain_label = ""
    best_score = 0

    for subdomain in subdomains:
        label = subdomain["tech_subdomain_label"]
        score = 0
        normalized_label = normalize_text(label)
        if normalized_label and normalized_label in normalized_bundle:
            score += 6
        for token in re.split(r"[·/() ]+", label):
            normalized_token = normalize_text(token)
            if normalized_token and normalized_token in normalized_bundle:
                score += 2
        if score > best_score:
            best_score = score
            best_subdomain_id = subdomain["tech_subdomain_id"]
            best_subdomain_label = label

    if best_score == 0:
        return "", ""
    return best_subdomain_id, best_subdomain_label


def suggest_strategy(
    text_bundle: str,
    document_title: str,
    strategy_rows: list[sqlite3.Row],
    vocabulary: dict,
) -> tuple[str, str, str, str, str]:
    scores = []
    for strategy in strategy_rows:
        vocab_entry = vocabulary.get(strategy["strategy_label"], {})
        score = score_strategy(
            text_bundle,
            document_title,
            strategy["strategy_id"],
            strategy["strategy_label"],
            vocab_entry,
        )
        if score > 0:
            scores.append((strategy, score))

    if not scores:
        return "", "", "", "", ""

    scores.sort(key=lambda pair: (-pair[1], pair[0]["display_order"]))
    top_score = scores[0][1]
    if top_score < 4:
        return "", "", "", "", ""

    selected = [pair for pair in scores if pair[1] >= max(4, top_score - 2)][:2]
    primary = selected[0][0]
    secondary_ids = [strategy["strategy_id"] for strategy, _ in selected[1:]]
    notes = [f"primary_score={selected[0][1]}"]
    if len(selected) > 1:
        notes.append(f"secondary_score={selected[1][1]}")

    return (
        primary["strategy_id"],
        primary["strategy_label"],
        " | ".join(secondary_ids),
        confidence_from_score(top_score),
        "; ".join(notes),
    )


def suggest_tech_domain(
    text_bundle: str,
    document_title: str,
    domain_rows: list[sqlite3.Row],
    subdomains_by_domain: dict[str, list[sqlite3.Row]],
    vocabulary: dict,
) -> tuple[str, str, str, str, str, str]:
    scores = []
    for domain in domain_rows:
        vocab_entry = vocabulary.get(domain["tech_domain_label"], {})
        score = score_domain(text_bundle, document_title, domain["tech_domain_label"], vocab_entry)
        if score > 0:
            scores.append((domain, score))

    if not scores:
        return "", "", "", "", "", ""

    scores.sort(key=lambda pair: (-pair[1], pair[0]["display_order"]))
    top_domain, top_score = scores[0]
    if top_score < 4:
        return "", "", "", "", "", ""

    subdomain_id, subdomain_label = infer_subdomain(
        subdomains_by_domain.get(top_domain["tech_domain_id"], []),
        text_bundle,
    )
    notes = [f"tech_score={top_score}"]
    if subdomain_id:
        notes.append(f"subdomain={subdomain_id}")

    return (
        top_domain["tech_domain_id"],
        top_domain["tech_domain_label"],
        subdomain_id,
        subdomain_label,
        confidence_from_score(top_score),
        "; ".join(notes),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--document-id", required=True)
    parser.add_argument("--out-root", required=True)
    parser.add_argument("--document-title", default="")
    parser.add_argument("--db-path")
    parser.add_argument("--strategy-keyword-json")
    parser.add_argument("--tech-keyword-json")
    args = parser.parse_args()

    out_root = Path(args.out_root)
    paragraph_path = out_root / "work/03_processing/normalized" / f"{args.document_id}__paragraphs.json"
    if not paragraph_path.exists():
        raise FileNotFoundError(f"Missing normalized paragraph file: {paragraph_path}")

    db_path = Path(args.db_path) if args.db_path else out_root / "work/04_ontology/ontology.sqlite"
    strategy_keyword_path = (
        Path(args.strategy_keyword_json)
        if args.strategy_keyword_json
        else out_root / "work/04_ontology/vocabularies/strategy-keywords.json"
    )
    tech_keyword_path = (
        Path(args.tech_keyword_json)
        if args.tech_keyword_json
        else out_root / "work/04_ontology/vocabularies/tech-domain-keywords.json"
    )

    strategy_rows, domain_rows, subdomains_by_domain = load_taxonomy_rows(db_path)
    strategy_vocabulary = load_json(strategy_keyword_path)
    tech_vocabulary = load_json(tech_keyword_path)
    paragraphs = json.loads(paragraph_path.read_text(encoding="utf-8"))
    rows = []

    previous_paragraph: dict | None = None
    for index, paragraph in enumerate(paragraphs, start=1):
        text = paragraph["text"]
        candidate = policy_item_candidate(
            paragraph["block_type"],
            text,
            paragraph["page_no"],
            prev_paragraph=previous_paragraph,
        )
        suggested_resource_type, matched_keywords, resource_confidence = suggest_resource_type(text)

        primary_strategy_id = ""
        primary_strategy_label = ""
        secondary_strategy_ids = ""
        strategy_confidence = ""
        tech_domain_id = ""
        tech_domain_label = ""
        tech_subdomain_id = ""
        tech_subdomain_label = ""
        tech_domain_confidence = ""
        auto_notes = []

        if candidate != "no":
            text_bundle = " ".join([args.document_title, text]).strip()
            (
                primary_strategy_id,
                primary_strategy_label,
                secondary_strategy_ids,
                strategy_confidence,
                strategy_note,
            ) = suggest_strategy(text_bundle, args.document_title, strategy_rows, strategy_vocabulary)
            if strategy_note:
                auto_notes.append(strategy_note)

            (
                tech_domain_id,
                tech_domain_label,
                tech_subdomain_id,
                tech_subdomain_label,
                tech_domain_confidence,
                tech_note,
            ) = suggest_tech_domain(
                text_bundle,
                args.document_title,
                domain_rows,
                subdomains_by_domain,
                tech_vocabulary,
            )
            if tech_note:
                auto_notes.append(tech_note)
        else:
            auto_notes.append("auto_filtered=front_matter")

        rows.append(
            {
                "classification_seed_id": f"CLS-SEED-{args.document_id}-{index:05d}",
                "source_object_type": "paragraph_unit",
                "source_object_id": paragraph["paragraph_id"],
                "document_id": paragraph["document_id"],
                "page_no": paragraph["page_no"],
                "page_block_order": paragraph["page_block_order"],
                "block_type": paragraph["block_type"],
                "policy_item_candidate": candidate,
                "suggested_resource_type": suggested_resource_type,
                "resource_type_keyword_hits": matched_keywords,
                "resource_type_confidence": resource_confidence,
                "primary_strategy_id": primary_strategy_id,
                "primary_strategy_label": primary_strategy_label,
                "secondary_strategy_ids": secondary_strategy_ids,
                "strategy_confidence": strategy_confidence,
                "tech_domain_id": tech_domain_id,
                "tech_domain_label": tech_domain_label,
                "tech_subdomain_id": tech_subdomain_id,
                "tech_subdomain_label": tech_subdomain_label,
                "tech_domain_confidence": tech_domain_confidence,
                "review_status": "review_required",
                "auto_suggestion_notes": " | ".join(auto_notes),
                "reviewer_notes": "",
                "text": text,
            }
        )
        previous_paragraph = paragraph

    summary = {
        "document_id": args.document_id,
        "document_title": args.document_title,
        "paragraph_count": len(rows),
        "resource_type_suggested_count": sum(1 for row in rows if row["suggested_resource_type"]),
        "policy_item_yes_count": sum(1 for row in rows if row["policy_item_candidate"] == "yes"),
        "policy_item_review_count": sum(1 for row in rows if row["policy_item_candidate"] == "review"),
        "policy_item_no_count": sum(1 for row in rows if row["policy_item_candidate"] == "no"),
        "strategy_suggested_count": sum(1 for row in rows if row["primary_strategy_id"]),
        "tech_domain_suggested_count": sum(1 for row in rows if row["tech_domain_id"]),
        "tech_subdomain_suggested_count": sum(1 for row in rows if row["tech_subdomain_id"]),
    }

    instances_dir = out_root / "work/04_ontology/instances"
    csv_path = instances_dir / f"{args.document_id}__classification-template.csv"
    summary_path = instances_dir / f"{args.document_id}__classification-template-summary.json"

    write_csv(
        csv_path,
        rows,
        [
            "classification_seed_id",
            "source_object_type",
            "source_object_id",
            "document_id",
            "page_no",
            "page_block_order",
            "block_type",
            "policy_item_candidate",
            "suggested_resource_type",
            "resource_type_keyword_hits",
            "resource_type_confidence",
            "primary_strategy_id",
            "primary_strategy_label",
            "secondary_strategy_ids",
            "strategy_confidence",
            "tech_domain_id",
            "tech_domain_label",
            "tech_subdomain_id",
            "tech_subdomain_label",
            "tech_domain_confidence",
            "review_status",
            "auto_suggestion_notes",
            "reviewer_notes",
            "text",
        ],
    )
    write_json(summary_path, summary)


if __name__ == "__main__":
    main()
