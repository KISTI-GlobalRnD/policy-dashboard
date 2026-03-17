#!/usr/bin/env python3
"""Build heuristic policy items and dashboard display texts from derived paragraphs."""

from __future__ import annotations

import argparse
import csv
import re
import sqlite3
from pathlib import Path


ACTION_KEYWORDS = {
    "구축", "개발", "확보", "확충", "고도화", "지원", "육성", "양성", "유치", "정비", "개선",
    "마련", "조성", "개방", "도입", "추진", "신설", "확대", "운영", "가동", "실증", "정착",
    "자립화", "사업화", "상용화", "고도화", "연계", "제공", "투자", "융자", "창출",
}
STRONG_ACTION_KEYWORDS = {
    "구축", "개발", "확충", "지원", "육성", "양성", "유치", "정비",
    "개선", "마련", "조성", "개방", "도입", "추진", "신설", "확대",
    "운영", "가동", "실증", "설립",
}
NEGATIVE_KEYWORDS = {
    "추진 배경", "현황", "위기", "한계", "전망", "추세", "필요", "배경", "이유", "현 주소",
    "글로벌 주요국", "요구", "대응 필요", "설명", "의결함",
}
CONTEXT_PREFIXES = {
    "최근", "글로벌 주요국", "해외 주요국", "한편", "방대한 데이터", "전통적 방식",
    "빅파마", "AI를 통해", "전 세계적인", "대한민국", "네트워크는", "향후 AI 서비스",
}
TECHNOLOGY_KEYWORDS = {
    "기술", "모델", "연구", "개발", "R&D", "AI", "NPU", "GPU", "PIM", "반도체", "플랫폼 모델",
    "실증", "파운데이션", "로봇", "양자", "바이오", "제조AX", "네트워크", "알고리즘",
}
INFRA_KEYWORDS = {
    "인프라", "플랫폼", "데이터", "제도", "규제", "법률", "법제", "거버넌스", "조달", "클라우드",
    "테스트베드", "실증환경", "장비", "센터", "허브", "펀드", "세액", "투자", "융자", "표준", "인증",
}
TALENT_KEYWORDS = {
    "인재", "인력", "교육", "양성", "유치", "재교육", "대학원", "연구자", "석박사", "훈련", "인턴",
}

STRUCTURAL_TEXTS = {
    "Ⅰ. 의결주문", "Ⅱ. 제안이유", "Ⅲ. 주요 내용", "Ⅳ. 향후계획", "Ⅰ 추진배경",
}

BULLET_PREFIX_RE = re.compile(r"^(?:[ㅇ□\-*▪•]+)\s*")
PAREN_LABEL_RE = re.compile(r"^[ㅇ□\-*▪•]*\s*\(([^)]+)\)")
YEAR_RE = re.compile(r"[’']?\d{2}")


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def is_structural_text(text: str) -> bool:
    text = clean_text(text)
    if text in STRUCTURAL_TEXTS:
        return True
    if len(text) <= 18 and any(keyword in text for keyword in {"추진과제", "주요 내용", "향후계획", "추진 배경", "현황"}):
        return True
    if text.startswith("<") and text.endswith(">"):
        return True
    return False


def classify_resource_category(text: str, heading_text: str) -> tuple[str, dict[str, int]]:
    score = {"technology": 0, "infrastructure_institutional": 0, "talent": 0}
    combined = f"{heading_text} {text}"

    for keyword in TECHNOLOGY_KEYWORDS:
        if keyword in combined:
            score["technology"] += 1
    for keyword in INFRA_KEYWORDS:
        if keyword in combined:
            score["infrastructure_institutional"] += 1
    for keyword in TALENT_KEYWORDS:
        if keyword in combined:
            score["talent"] += 1

    category = max(score, key=lambda key: score[key])
    if score[category] == 0:
        if any(keyword in combined for keyword in {"법", "제도", "규제", "조달", "펀드"}):
            category = "infrastructure_institutional"
        elif any(keyword in combined for keyword in {"인력", "교육", "양성", "유치"}):
            category = "talent"
        else:
            category = "technology"
    return category, score


def is_candidate(text: str, heading_text: str) -> bool:
    text = clean_text(text)
    if len(text) < 20:
        return False
    if is_structural_text(text):
        return False
    if any(text.startswith(prefix) for prefix in CONTEXT_PREFIXES):
        return False
    if any(keyword in text for keyword in NEGATIVE_KEYWORDS):
        if not any(keyword in text for keyword in STRONG_ACTION_KEYWORDS):
            return False
    strong_hits = sum(1 for keyword in STRONG_ACTION_KEYWORDS if keyword in text)
    action_hits = sum(1 for keyword in ACTION_KEYWORDS if keyword in text)
    candidate_score = (strong_hits * 3) + action_hits
    if PAREN_LABEL_RE.search(text):
        candidate_score += 2
    if YEAR_RE.search(text):
        candidate_score += 1
    if len(text) > 180:
        candidate_score -= 1
    if candidate_score >= 4:
        return True
    if candidate_score >= 2 and any(keyword in heading_text for keyword in {"추진과제", "주요 내용", "향후계획"}):
        return True
    return False


def build_label(text: str) -> str:
    text = clean_text(text)
    parenthetical = PAREN_LABEL_RE.search(text)
    if parenthetical:
        label = parenthetical.group(1).strip()
    else:
        label = BULLET_PREFIX_RE.sub("", text)
        label = re.split(r"[,:;]", label, maxsplit=1)[0].strip()
    if label in {"가칭", "예", "한편"} or len(label) < 2:
        label = BULLET_PREFIX_RE.sub("", text)
        label = re.split(r"[,.·;:]", label, maxsplit=1)[0].strip()
    if len(label) > 48:
        label = f"{label[:45].rstrip()}..."
    return label


def build_summary(text: str) -> str:
    text = clean_text(text)
    if len(text) <= 150:
        return text
    return f"{text[:147].rstrip()}..."


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", required=True)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    ensure_dir(out_dir)

    connection = sqlite3.connect(args.db_path)
    connection.row_factory = sqlite3.Row
    try:
        policy_order = {
            row["policy_id"]: row["policy_order"]
            for row in connection.execute("SELECT policy_id, policy_order FROM policies")
        }
        bucket_by_key = {
            (row["policy_id"], row["resource_category_id"]): row["policy_bucket_id"]
            for row in connection.execute("SELECT policy_bucket_id, policy_id, resource_category_id FROM policy_buckets")
        }
        document_to_policy = {
            row["document_id"]: row["policy_id"]
            for row in connection.execute("SELECT document_id, policy_id FROM documents")
        }

        rows = connection.execute(
            """
            SELECT
                ep.paragraph_id,
                ep.document_id,
                ep.page_no,
                ep.page_block_order,
                ep.block_type,
                ep.text,
                dr.derived_representation_id
            FROM evidence_paragraphs ep
            JOIN derived_representations dr
              ON dr.source_object_type = 'paragraph'
             AND dr.source_object_id = ep.paragraph_id
            ORDER BY ep.document_id, ep.page_no, ep.page_block_order
            """
        ).fetchall()

        current_heading_by_doc_page: dict[tuple[str, str], str] = {}
        candidate_items: dict[tuple[str, str], dict[str, object]] = {}

        item_counter = 1
        display_counter = 1

        for row in rows:
            document_id = row["document_id"]
            policy_id = document_to_policy.get(document_id)
            if not policy_id:
                continue

            key = (document_id, row["page_no"])
            text = clean_text(row["text"])
            if row["block_type"] == "heading" or is_structural_text(text):
                current_heading_by_doc_page[key] = text
                continue
            if row["block_type"] not in {"bullet", "paragraph"}:
                continue

            heading_text = current_heading_by_doc_page.get(key, "")
            if not is_candidate(text, heading_text):
                continue

            resource_category_id, category_scores = classify_resource_category(text, heading_text)
            bucket_id = bucket_by_key[(policy_id, resource_category_id)]
            label = build_label(text)
            if label in {"가칭", "예", "한편"} or len(label) < 2:
                continue
            summary = build_summary(text)
            candidate_score = sum(3 for keyword in STRONG_ACTION_KEYWORDS if keyword in text)
            candidate_score += sum(1 for keyword in ACTION_KEYWORDS if keyword in text)
            if PAREN_LABEL_RE.search(text):
                candidate_score += 2
            candidate_key = (bucket_id, label)
            current_candidate = candidate_items.get(candidate_key)
            if current_candidate and current_candidate["candidate_score"] >= candidate_score:
                continue
            candidate_items[candidate_key] = {
                "policy_id": policy_id,
                "policy_bucket_id": bucket_id,
                "item_label": label,
                "item_statement": text,
                "item_description": f"{heading_text} | {text}" if heading_text else text,
                "summary_text": summary,
                "description_text": heading_text,
                "curation_priority": policy_order.get(policy_id, 0),
                "notes": f"auto_extracted; scores={category_scores}",
                "derived_representation_id": row["derived_representation_id"],
                "candidate_score": candidate_score,
            }

        policy_items: list[dict[str, object]] = []
        display_texts: list[dict[str, object]] = []
        evidence_links: list[dict[str, object]] = []
        derived_to_display: list[dict[str, object]] = []

        for candidate_key in sorted(candidate_items, key=lambda key: (candidate_items[key]["policy_id"], candidate_items[key]["policy_bucket_id"], candidate_items[key]["item_label"])):
            candidate = candidate_items[candidate_key]
            policy_item_id = f"ITM-{candidate['policy_id']}-{item_counter:05d}"
            display_text_id = f"DSP-{candidate['policy_id']}-{display_counter:05d}"
            policy_items.append(
                {
                    "policy_item_id": policy_item_id,
                    "policy_bucket_id": candidate["policy_bucket_id"],
                    "item_label": candidate["item_label"],
                    "item_statement": candidate["item_statement"],
                    "item_description": candidate["item_description"],
                    "item_status": "auto_candidate",
                    "source_basis_type": "source_document_only",
                    "curation_priority": candidate["curation_priority"],
                    "notes": candidate["notes"],
                }
            )
            display_texts.append(
                {
                    "display_text_id": display_text_id,
                    "target_object_type": "policy_item",
                    "target_object_id": policy_item_id,
                    "display_role": "policy_item_summary",
                    "title_text": candidate["item_label"],
                    "summary_text": candidate["summary_text"],
                    "description_text": candidate["description_text"],
                    "generated_by": "heuristic_auto_extractor_v1",
                    "review_status": "review_required",
                    "source_basis_type": "source_document_only",
                    "notes": "",
                }
            )
            evidence_links.append(
                {
                    "policy_item_evidence_link_id": f"LNK-{policy_item_id}",
                    "policy_item_id": policy_item_id,
                    "derived_representation_id": candidate["derived_representation_id"],
                    "link_role": "primary_support",
                    "evidence_strength": "medium",
                    "is_primary": 1,
                    "sort_order": 1,
                    "notes": "",
                }
            )
            derived_to_display.append(
                {
                    "derived_to_display_map_id": f"DTD-{candidate['derived_representation_id']}",
                    "derived_representation_id": candidate["derived_representation_id"],
                    "display_text_id": display_text_id,
                    "display_role": "policy_item_summary",
                    "is_primary": 1,
                    "notes": "",
                }
            )
            item_counter += 1
            display_counter += 1

        connection.execute("DELETE FROM derived_to_display_map")
        connection.execute("DELETE FROM policy_item_evidence_links")
        connection.execute("DELETE FROM display_texts WHERE generated_by = 'heuristic_auto_extractor_v1'")
        connection.execute("DELETE FROM policy_items WHERE item_status = 'auto_candidate'")
        write_csv(
            out_dir / "policy_items_auto.csv",
            policy_items,
            [
                "policy_item_id",
                "policy_bucket_id",
                "item_label",
                "item_statement",
                "item_description",
                "item_status",
                "source_basis_type",
                "curation_priority",
                "notes",
            ],
        )
        write_csv(
            out_dir / "display_texts_auto.csv",
            display_texts,
            [
                "display_text_id",
                "target_object_type",
                "target_object_id",
                "display_role",
                "title_text",
                "summary_text",
                "description_text",
                "generated_by",
                "review_status",
                "source_basis_type",
                "notes",
            ],
        )
        write_csv(
            out_dir / "policy_item_evidence_links_auto.csv",
            evidence_links,
            [
                "policy_item_evidence_link_id",
                "policy_item_id",
                "derived_representation_id",
                "link_role",
                "evidence_strength",
                "is_primary",
                "sort_order",
                "notes",
            ],
        )
        write_csv(
            out_dir / "derived_to_display_map_auto.csv",
            derived_to_display,
            [
                "derived_to_display_map_id",
                "derived_representation_id",
                "display_text_id",
                "display_role",
                "is_primary",
                "notes",
            ],
        )

        connection.executemany(
            """
            INSERT OR REPLACE INTO policy_items (
                policy_item_id,
                policy_bucket_id,
                item_label,
                item_statement,
                item_description,
                item_status,
                source_basis_type,
                curation_priority,
                notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    row["policy_item_id"],
                    row["policy_bucket_id"],
                    row["item_label"],
                    row["item_statement"],
                    row["item_description"],
                    row["item_status"],
                    row["source_basis_type"],
                    row["curation_priority"],
                    row["notes"],
                )
                for row in policy_items
            ],
        )
        connection.executemany(
            """
            INSERT OR REPLACE INTO display_texts (
                display_text_id,
                target_object_type,
                target_object_id,
                display_role,
                title_text,
                summary_text,
                description_text,
                generated_by,
                review_status,
                source_basis_type,
                notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    row["display_text_id"],
                    row["target_object_type"],
                    row["target_object_id"],
                    row["display_role"],
                    row["title_text"],
                    row["summary_text"],
                    row["description_text"],
                    row["generated_by"],
                    row["review_status"],
                    row["source_basis_type"],
                    row["notes"],
                )
                for row in display_texts
            ],
        )
        connection.executemany(
            """
            INSERT OR REPLACE INTO policy_item_evidence_links (
                policy_item_evidence_link_id,
                policy_item_id,
                derived_representation_id,
                link_role,
                evidence_strength,
                is_primary,
                sort_order,
                notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    row["policy_item_evidence_link_id"],
                    row["policy_item_id"],
                    row["derived_representation_id"],
                    row["link_role"],
                    row["evidence_strength"],
                    row["is_primary"],
                    row["sort_order"],
                    row["notes"],
                )
                for row in evidence_links
            ],
        )
        connection.executemany(
            """
            INSERT OR REPLACE INTO derived_to_display_map (
                derived_to_display_map_id,
                derived_representation_id,
                display_text_id,
                display_role,
                is_primary,
                notes
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    row["derived_to_display_map_id"],
                    row["derived_representation_id"],
                    row["display_text_id"],
                    row["display_role"],
                    row["is_primary"],
                    row["notes"],
                )
                for row in derived_to_display
            ],
        )
        connection.commit()
    finally:
        connection.close()

    print(f"Policy items: {len(policy_items)}")
    print(f"Display texts: {len(display_texts)}")


if __name__ == "__main__":
    main()
