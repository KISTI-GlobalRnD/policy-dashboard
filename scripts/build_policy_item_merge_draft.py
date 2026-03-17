#!/usr/bin/env python3
"""Build a reviewable policy-item merge draft from paragraph classification templates."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path


BULLET_PREFIX_RE = re.compile(r"^(?:[ㅇ□\-*▪•⇨⇒]+)\s*")
PAREN_LABEL_RE = re.compile(r"^[ㅇ□\-*▪•⇨⇒]*\s*\(([^)]+)\)")
GROUP_COUNT_RE = re.compile(r"^\([^)]{1,40}:\s*\d+개")
EXAMPLE_RE = re.compile(r"^[A-Z]社[:(]")
CASE_EXAMPLE_RE = re.compile(r"(?:[A-Z]社|기업[가-힣A-Z0-9]+)\s*[:：]")
NEED_CUE_RE = re.compile(r"(?:필요성 제기|필요|시급|절실)(?:\s|$|[.,)·])")

ACTION_KEYWORDS = {
    "구축", "개발", "확보", "확충", "고도화", "지원", "육성", "양성", "유치", "정비",
    "개선", "마련", "조성", "개방", "도입", "추진", "신설", "확대", "운영", "가동",
    "실증", "정착", "자립화", "사업화", "상용화", "연계", "제공", "투자", "융자", "창출",
    "설립", "활성화", "과제화", "구체화", "도출", "공고", "시행", "발의", "검증", "결성",
    "착수", "공유", "서비스", "설계", "제작", "보급", "송출",
}
STRONG_ACTION_KEYWORDS = {
    "구축", "개발", "확충", "지원", "육성", "양성", "유치", "정비", "개선", "마련",
    "조성", "도입", "추진", "신설", "확대", "운영", "실증", "설립", "과제화", "구체화",
}
NEGATIVE_KEYWORDS = {
    "추진 배경", "현황", "위기", "한계", "전망", "성장전망", "필요", "배경", "이유", "현주소",
    "현 주소", "글로벌 주요국", "요구", "대응 필요", "설명", "필수", "시급", "중요성", "가능",
    "부족", "불안정", "진입장벽", "전환이시급",
}
BACKGROUND_TAIL_KEYWORDS = {
    "필요", "시급", "전망", "필수", "절실", "중요성", "기대", "가능", "둔화", "증대",
}
CONTEXT_PREFIXES = {
    "최근", "글로벌 주요국", "해외 주요국", "한편", "방대한 데이터", "전통적 방식",
    "빅파마", "AI를 통해", "전 세계적인", "대한민국", "네트워크는", "향후 AI 서비스",
    "우리나라의", "세계콘텐츠시장", "글로벌디지털헬스시장", "특히", "다만",
}
SCHEDULE_PREFIXES = ("참 고", "시기 세부 일정")
SECTION_PREFIXES = ("◇", "◈")
IMPLEMENTATION_CUES = {
    "마련", "구성", "운영", "구축", "도입", "개선", "제도화", "공고", "시행", "발의",
    "착수", "결성", "신설", "확대", "정책지원 방안", "지원방안", "로드맵",
}
ROLE_META_KEYWORDS = {
    "의결함", "추진계획 발표", "추진 전략 및 과제", "추진 배경 및 경과",
    "세부실행계획업데이트", "실무 추진협의체", "추진단 구성", "3대분야",
}
ROLE_BACKGROUND_KEYWORDS = {
    "현장의견", "문제인식", "대외환경", "부작용", "지적", "한계", "미흡",
    "부족", "저조", "진입장벽", "추세", "대비되면서",
}
ROLE_HARD_PROBLEM_KEYWORDS = {
    "미흡", "부재", "저조", "진입장벽", "부작용", "필요성 제기", "어려움",
}
ROLE_SOFT_PROBLEM_KEYWORDS = {
    "한계", "역할 요구", "문제", "위기요인", "제한",
}
ROLE_DELTA_MARKERS = {
    "(현재)", "→(개선)", "현행", "→",
}
ROLE_DELTA_ACTIONS = {
    "개선", "제도화", "개정", "폐지", "완화", "정비",
}


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def parse_ids(raw: str) -> list[str]:
    return [value.strip() for value in (raw or "").split("|") if value.strip()]


def unique_preserve(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered


def build_label(text: str) -> str:
    normalized = clean_text(text)
    parenthetical = PAREN_LABEL_RE.search(normalized)
    if parenthetical:
        label = parenthetical.group(1).strip()
    else:
        label = BULLET_PREFIX_RE.sub("", normalized)
        label = re.split(r"[,:;]", label, maxsplit=1)[0].strip()
    if len(label) > 60:
        label = f"{label[:57].rstrip()}..."
    return label


def strip_leading_markers(text: str) -> str:
    return BULLET_PREFIX_RE.sub("", clean_text(text))


def row_page(row: dict[str, str]) -> str:
    return str(row.get("page_no", "")).strip()


def row_text(row: dict[str, str]) -> str:
    return clean_text(row.get("text", ""))


def starts_with_marker(text: str) -> bool:
    stripped = text.strip()
    return stripped.startswith(("ㅇ ", "□ ", "- ", "* ", "▪ ", "• ", "⇨", "⇒"))


def row_has_taxonomy_hints(row: dict[str, str]) -> bool:
    return any(
        clean_text(row.get(key, ""))
        for key in (
            "suggested_resource_type",
            "primary_strategy_id",
            "secondary_strategy_ids",
            "tech_domain_id",
            "tech_subdomain_id",
        )
    )


def has_action_hint(text: str) -> bool:
    normalized = strip_leading_markers(text)
    if any(keyword in normalized for keyword in STRONG_ACTION_KEYWORDS):
        return True
    return any(keyword in normalized for keyword in ACTION_KEYWORDS)


def has_strong_action_hint(text: str) -> bool:
    normalized = strip_leading_markers(text)
    return any(keyword in normalized for keyword in STRONG_ACTION_KEYWORDS)


def primary_skip_reason(row: dict[str, str]) -> str:
    text = row_text(row)
    stripped = strip_leading_markers(text)
    label = build_label(text)
    block_type = row.get("block_type", "")
    has_action = has_action_hint(stripped)
    has_taxonomy = row_has_taxonomy_hints(row)
    tail = stripped[-50:]

    if stripped.startswith(SCHEDULE_PREFIXES) or "시기 세부 일정" in stripped:
        return "schedule_scaffold"
    if stripped.startswith(SECTION_PREFIXES):
        return "section_scaffold"
    if GROUP_COUNT_RE.search(stripped):
        return "group_count_scaffold"
    if EXAMPLE_RE.search(stripped):
        return "example_scaffold"
    if label in {"다만", "특히"} and not has_action:
        return "context_scaffold"
    if any(stripped.startswith(prefix) for prefix in CONTEXT_PREFIXES) and not has_action:
        return "context_scaffold"
    if any(keyword in tail for keyword in BACKGROUND_TAIL_KEYWORDS) and not any(
        cue in stripped for cue in IMPLEMENTATION_CUES
    ):
        return "background_tail"
    if any(keyword in stripped for keyword in NEGATIVE_KEYWORDS) and not has_action:
        return "background_statement"
    if block_type == "paragraph" and len(stripped) <= 40 and not has_action:
        return "short_paragraph_scaffold"
    if block_type == "paragraph" and (
        stripped.count("․") >= 4 or stripped.count("[") >= 3 or stripped.count("→") >= 2
    ) and not has_action:
        return "diagram_or_schedule_paragraph"
    if block_type == "paragraph" and len(stripped) >= 150 and not has_action:
        return "long_background_paragraph"
    if not has_action and not has_taxonomy and len(stripped) <= 80:
        return "no_action_no_taxonomy"
    return ""


def can_attach_review(row: dict[str, str], current: dict[str, object]) -> bool:
    if not current:
        return False
    if row_page(row) != current["page_no"]:
        return False
    return row.get("block_type") in {"note", "citation", "caption"}


def can_attach_continuation(row: dict[str, str], previous_row: dict[str, str] | None, current: dict[str, object]) -> bool:
    if not current or not previous_row:
        return False
    if row_page(row) != current["page_no"] or row_page(row) != row_page(previous_row):
        return False
    if row.get("policy_item_candidate") != "yes":
        return False

    text = row_text(row)
    if row.get("block_type") == "paragraph" and len(text) <= 80:
        return True

    if row.get("block_type") == "paragraph" and not starts_with_marker(text):
        return True

    return False


def bucket_guess(rows: list[dict[str, str]]) -> tuple[str, list[str]]:
    ordered = unique_preserve([row.get("suggested_resource_type", "") for row in rows if row.get("suggested_resource_type", "")])
    return (ordered[0] if ordered else "", ordered)


def collect_strategy_ids(rows: list[dict[str, str]]) -> list[str]:
    values = []
    for row in rows:
        values.extend(parse_ids(row.get("primary_strategy_id", "")))
        values.extend(parse_ids(row.get("secondary_strategy_ids", "")))
    return unique_preserve(values)


def collect_tech_ids(rows: list[dict[str, str]]) -> tuple[list[str], list[str]]:
    domains = unique_preserve([row.get("tech_domain_id", "") for row in rows if row.get("tech_domain_id", "")])
    subdomains = unique_preserve([row.get("tech_subdomain_id", "") for row in rows if row.get("tech_subdomain_id", "")])
    return domains, subdomains


def merge_confidence(primary_row: dict[str, str], attached_continuations: list[dict[str, str]], attached_reviews: list[dict[str, str]]) -> str:
    if attached_continuations:
        return "medium"
    if attached_reviews:
        return "medium"
    if primary_row.get("block_type") == "bullet":
        return "medium"
    return "low"


def infer_candidate_role(
    primary_row: dict[str, str],
    member_rows: list[dict[str, str]],
    support_rows: list[dict[str, str]],
) -> tuple[str, list[str]]:
    primary_text = row_text(primary_row)
    normalized = strip_leading_markers(primary_text)
    notes: list[str] = []
    has_action = has_action_hint(normalized)
    has_impl = has_action or any(cue in normalized for cue in IMPLEMENTATION_CUES)

    if any(marker in normalized for marker in ROLE_DELTA_MARKERS) and any(
        cue in normalized for cue in ROLE_DELTA_ACTIONS
    ):
        notes.append("detected_current_to_improvement_pattern")
        return "regulatory_delta", notes

    if any(keyword in normalized for keyword in ROLE_META_KEYWORDS):
        notes.append("detected_program_frame_keyword")
        return "meta_program_frame", notes

    if len(normalized) <= 30 and any(
        keyword in normalized for keyword in {"본격추진", "환경 조성", "지원체계", "성장 기반", "추진 전략"}
    ):
        notes.append("detected_short_meta_bullet")
        return "meta_program_frame", notes

    if CASE_EXAMPLE_RE.search(normalized) and ("“" in normalized or "\"" in normalized):
        notes.append("detected_case_example_quote")
        return "case_example", notes

    if normalized.startswith("☞ 개선방향"):
        notes.append("detected_improvement_direction_prefix")
        return "policy_action", notes

    if any(keyword in normalized for keyword in ROLE_BACKGROUND_KEYWORDS) and not has_strong_action_hint(normalized):
        notes.append("detected_background_keyword")
        return "background_context", notes

    if any(keyword in normalized for keyword in ROLE_HARD_PROBLEM_KEYWORDS):
        notes.append("detected_problem_keyword")
        return "problem_or_requirement", notes

    if any(keyword in normalized for keyword in ROLE_SOFT_PROBLEM_KEYWORDS):
        if has_impl:
            notes.append("detected_soft_problem_but_action_overrides")
            return "policy_action", notes
        notes.append("detected_problem_keyword")
        return "problem_or_requirement", notes

    if NEED_CUE_RE.search(normalized):
        if has_impl:
            notes.append("detected_need_phrase_but_action_overrides")
            return "policy_action", notes
        notes.append("detected_need_phrase")
        return "problem_or_requirement", notes

    return "policy_action", notes


def finalize_group(document_id: str, group_index: int, current: dict[str, object]) -> dict[str, object]:
    primary_row = current["primary_row"]
    member_rows = [primary_row] + current["continuation_rows"]
    support_rows = current["review_rows"]
    resource_primary, resource_all = bucket_guess(member_rows + support_rows)
    strategy_ids = collect_strategy_ids(member_rows + support_rows)
    tech_domain_ids, tech_subdomain_ids = collect_tech_ids(member_rows + support_rows)
    candidate_role_draft, candidate_role_notes = infer_candidate_role(primary_row, member_rows, support_rows)

    merged_statement_parts = [row_text(row) for row in member_rows]
    merged_statement = " ".join(part for part in merged_statement_parts if part)
    merge_notes = []
    if current["continuation_rows"]:
        merge_notes.append("attached_continuation")
    if current["review_rows"]:
        merge_notes.append("attached_review_support")

    return {
        "merge_candidate_id": f"PMD-{document_id}-{group_index:04d}",
        "document_id": document_id,
        "page_no": current["page_no"],
        "primary_seed_id": primary_row["classification_seed_id"],
        "primary_source_object_id": primary_row["source_object_id"],
        "primary_block_type": primary_row["block_type"],
        "item_label_draft": build_label(primary_row["text"]),
        "item_statement_draft": merged_statement,
        "candidate_role_draft": candidate_role_draft,
        "candidate_role_notes": " | ".join(candidate_role_notes),
        "bucket_resource_type_guess": resource_primary,
        "resource_type_candidates": " | ".join(resource_all),
        "primary_strategy_candidates": " | ".join(strategy_ids),
        "tech_domain_candidates": " | ".join(tech_domain_ids),
        "tech_subdomain_candidates": " | ".join(tech_subdomain_ids),
        "member_seed_ids": " | ".join(row["classification_seed_id"] for row in member_rows),
        "member_source_object_ids": " | ".join(row["source_object_id"] for row in member_rows),
        "member_count": len(member_rows),
        "supporting_review_seed_ids": " | ".join(row["classification_seed_id"] for row in support_rows),
        "supporting_review_count": len(support_rows),
        "primary_text": row_text(primary_row),
        "continuation_texts": " || ".join(row_text(row) for row in current["continuation_rows"]),
        "supporting_review_texts": " || ".join(row_text(row) for row in support_rows),
        "merge_confidence": merge_confidence(primary_row, current["continuation_rows"], support_rows),
        "merge_status": "review_required",
        "merge_notes": " | ".join(merge_notes),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--document-id", required=True)
    parser.add_argument("--out-root", required=True)
    args = parser.parse_args()

    out_root = Path(args.out_root)
    classification_path = out_root / "work/04_ontology/instances" / f"{args.document_id}__classification-template.csv"
    if not classification_path.exists():
        raise FileNotFoundError(f"Missing classification template: {classification_path}")

    rows = read_csv_rows(classification_path)
    merge_rows: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    previous_row: dict[str, str] | None = None
    group_index = 1
    skipped_primary_count = 0
    skip_reason_counts: Counter[str] = Counter()

    for row in rows:
        candidate = row.get("policy_item_candidate", "")

        if candidate == "yes":
            skip_reason = primary_skip_reason(row)
            if skip_reason:
                skipped_primary_count += 1
                skip_reason_counts[skip_reason] += 1
                if current and row_page(row) != current["page_no"]:
                    merge_rows.append(finalize_group(args.document_id, group_index, current))
                    group_index += 1
                    current = None
            elif current and can_attach_continuation(row, previous_row, current):
                current["continuation_rows"].append(row)
            else:
                if current:
                    merge_rows.append(finalize_group(args.document_id, group_index, current))
                    group_index += 1
                current = {
                    "page_no": row_page(row),
                    "primary_row": row,
                    "continuation_rows": [],
                    "review_rows": [],
                }
        elif candidate == "review":
            if current and can_attach_review(row, current):
                current["review_rows"].append(row)
        else:
            if current and row_page(row) != current["page_no"]:
                merge_rows.append(finalize_group(args.document_id, group_index, current))
                group_index += 1
                current = None

        previous_row = row

    if current:
        merge_rows.append(finalize_group(args.document_id, group_index, current))

    summary = {
        "document_id": args.document_id,
        "classification_row_count": len(rows),
        "merge_candidate_count": len(merge_rows),
        "skipped_primary_count": skipped_primary_count,
        "skip_reason_counts": dict(skip_reason_counts),
        "candidate_role_counts": dict(Counter(row["candidate_role_draft"] for row in merge_rows)),
        "attached_continuation_group_count": sum(1 for row in merge_rows if row["continuation_texts"]),
        "attached_review_group_count": sum(1 for row in merge_rows if int(row["supporting_review_count"]) > 0),
        "resource_type_guess_count": sum(1 for row in merge_rows if row["bucket_resource_type_guess"]),
        "strategy_candidate_count": sum(1 for row in merge_rows if row["primary_strategy_candidates"]),
        "tech_domain_candidate_count": sum(1 for row in merge_rows if row["tech_domain_candidates"]),
    }

    out_dir = out_root / "work/04_ontology/merge_drafts"
    write_csv(
        out_dir / f"{args.document_id}__policy-item-merge-draft.csv",
        merge_rows,
        [
            "merge_candidate_id",
            "document_id",
            "page_no",
            "primary_seed_id",
            "primary_source_object_id",
            "primary_block_type",
            "item_label_draft",
            "item_statement_draft",
            "candidate_role_draft",
            "candidate_role_notes",
            "bucket_resource_type_guess",
            "resource_type_candidates",
            "primary_strategy_candidates",
            "tech_domain_candidates",
            "tech_subdomain_candidates",
            "member_seed_ids",
            "member_source_object_ids",
            "member_count",
            "supporting_review_seed_ids",
            "supporting_review_count",
            "primary_text",
            "continuation_texts",
            "supporting_review_texts",
            "merge_confidence",
            "merge_status",
            "merge_notes",
        ],
    )
    write_json(out_dir / f"{args.document_id}__policy-item-merge-draft-summary.json", summary)


if __name__ == "__main__":
    main()
