#!/usr/bin/env python3
"""Build reviewed policy-item CSV outputs from a reviewed workbench."""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path


TECHNOLOGY_KEYWORDS = {
    "기술", "개발", "R&D", "AI", "반도체", "바이오", "양자", "로봇", "NPU", "GPU", "실증",
}
INFRA_KEYWORDS = {
    "플랫폼", "데이터", "제도", "규제", "법", "법률", "거버넌스", "조달", "허브", "센터",
    "펀드", "세액", "투자", "융자", "인허가", "지원체계", "인프라",
}
TALENT_KEYWORDS = {
    "인재", "인력", "교육", "양성", "유치", "훈련", "대학원", "연구자",
}

KEEP_DECISIONS = {
    "keep",
    "keep_or_merge",
    "recast_keep",
    "keep_as_regulatory_delta",
    "keep_as_problem",
    "keep_as_background",
    "keep_as_case_example",
}
MERGE_DECISIONS = {"merge", "merge_into"}
DROP_DECISIONS = {
    "drop",
    "drop_or_attach_background",
    "attach_as_background",
    "attach_as_case_example",
}
RESOURCE_TYPE_ALIASES = {
    "infrastructure_policy": "infrastructure_institutional",
    "infrastructure": "infrastructure_institutional",
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
    return " ".join((text or "").split()).strip()


def parse_ids(raw: str) -> list[str]:
    if not raw:
        return []
    normalized = raw.replace(",", "|")
    return [value.strip() for value in normalized.split("|") if value.strip()]


def decision_key(value: str) -> str:
    return clean_text(value).lower().replace(" ", "_")


def build_summary(text: str) -> str:
    normalized = clean_text(text)
    if len(normalized) <= 180:
        return normalized
    return f"{normalized[:177].rstrip()}..."


def dedupe_preserve(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered


def infer_resource_type(text: str, fallback_role: str) -> str:
    combined = clean_text(text)
    if any(keyword in combined for keyword in TALENT_KEYWORDS):
        return "talent"
    if any(keyword in combined for keyword in INFRA_KEYWORDS):
        return "infrastructure_institutional"
    if fallback_role == "regulatory_delta":
        return "infrastructure_institutional"
    if any(keyword in combined for keyword in TECHNOLOGY_KEYWORDS):
        return "technology"
    return "technology"


def normalize_resource_type(value: str) -> str:
    normalized = clean_text(value)
    return RESOURCE_TYPE_ALIASES.get(normalized, normalized)


def load_policy_context(out_root: Path) -> tuple[dict[str, dict[str, str]], dict[tuple[str, str], str], dict[str, int]]:
    documents = {
        row["document_id"]: row
        for row in read_csv_rows(out_root / "work/04_ontology/instances/documents_seed.csv")
    }
    buckets = {
        (row["policy_id"], row["resource_category_id"]): row["policy_bucket_id"]
        for row in read_csv_rows(out_root / "work/04_ontology/instances/policy_bucket_master.csv")
    }
    policy_orders = {
        row["policy_id"]: int(row["policy_order"])
        for row in read_csv_rows(out_root / "work/04_ontology/instances/policy_master.csv")
    }
    return documents, buckets, policy_orders


def load_paragraph_to_derived(db_path: Path, document_id: str) -> dict[str, str]:
    connection = sqlite3.connect(db_path)
    try:
        rows = connection.execute(
            """
            SELECT source_object_id, derived_representation_id
            FROM derived_representations
            WHERE document_id = ?
              AND source_object_type = 'paragraph'
            """,
            (document_id,),
        ).fetchall()
    finally:
        connection.close()
    return {row[0]: row[1] for row in rows}


def load_classification_seed_to_paragraph(out_root: Path, document_id: str) -> dict[str, str]:
    rows = read_csv_rows(out_root / "work/04_ontology/instances" / f"{document_id}__classification-template.csv")
    return {
        row["classification_seed_id"]: row["source_object_id"]
        for row in rows
        if row.get("source_object_id", "").startswith("PAR-")
    }


def resolve_resource_type(row: dict[str, str], final_role: str) -> str:
    override = normalize_resource_type(row.get("reviewer_resource_type_override", ""))
    if override:
        return override
    guessed = normalize_resource_type(row.get("bucket_resource_type_guess", ""))
    if guessed:
        return guessed
    return normalize_resource_type(
        infer_resource_type(row.get("final_item_statement", "") or row.get("item_statement_draft", ""), final_role)
    )


def resolve_role(row: dict[str, str]) -> str:
    return clean_text(row.get("reviewer_role_override", "")) or clean_text(row.get("candidate_role_draft", "")) or "policy_action"


def resolve_label(row: dict[str, str]) -> str:
    return clean_text(row.get("final_item_label", "")) or clean_text(row.get("item_label_draft", ""))


def resolve_statement(row: dict[str, str]) -> str:
    return clean_text(row.get("final_item_statement", "")) or clean_text(row.get("item_statement_draft", ""))


def issue(code: str, row: dict[str, str], message: str, details: dict[str, object] | None = None) -> dict[str, object]:
    payload = {
        "code": code,
        "merge_candidate_id": row.get("merge_candidate_id", ""),
        "message": message,
    }
    if details:
        payload["details"] = details
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--document-id", required=True)
    parser.add_argument("--out-root", required=True)
    parser.add_argument("--workbench-path")
    parser.add_argument("--db-path")
    parser.add_argument("--output-dir")
    args = parser.parse_args()

    out_root = Path(args.out_root)
    workbench_path = (
        Path(args.workbench_path)
        if args.workbench_path
        else out_root / "work/04_ontology/review_workbenches" / f"{args.document_id}__policy-item-review-workbench.csv"
    )
    db_path = Path(args.db_path) if args.db_path else out_root / "work/04_ontology/ontology.sqlite"
    output_dir = (
        Path(args.output_dir)
        if args.output_dir
        else out_root / "work/04_ontology/reviewed_items"
    )

    rows = read_csv_rows(workbench_path)
    documents, bucket_by_key, policy_orders = load_policy_context(out_root)
    paragraph_to_derived = load_paragraph_to_derived(db_path, args.document_id)
    seed_to_paragraph = load_classification_seed_to_paragraph(out_root, args.document_id)

    document_row = documents[args.document_id]
    policy_id = document_row["policy_id"]
    policy_order = policy_orders[policy_id]

    leader_rows: dict[str, dict[str, str]] = {}
    merged_rows_by_target: dict[str, list[dict[str, str]]] = defaultdict(list)
    ignored_rows: list[dict[str, str]] = []
    unresolved_merges: list[dict[str, str]] = []
    issues: list[dict[str, object]] = []
    reviewed_rows = [
        row for row in rows if clean_text(row.get("review_status", "")) in {"reviewed", "reviewed_manual"}
    ]
    reviewed_decision_counter = Counter(
        decision_key(row.get("reviewer_decision", "")) or "<blank>" for row in reviewed_rows
    )

    for row in reviewed_rows:
        decision = decision_key(row.get("reviewer_decision", ""))
        if not decision:
            continue

        merge_target = clean_text(row.get("merge_into_candidate_id", ""))
        if decision in DROP_DECISIONS:
            ignored_rows.append(row)
            continue
        if decision == "recast_or_attach_background":
            if clean_text(row.get("final_item_label", "")) or clean_text(row.get("final_item_statement", "")):
                leader_rows[row["merge_candidate_id"]] = row
            else:
                ignored_rows.append(row)
            continue
        if decision in MERGE_DECISIONS or merge_target:
            if not merge_target:
                ignored_rows.append(row)
                continue
            merged_rows_by_target[merge_target].append(row)
            continue
        if decision in KEEP_DECISIONS:
            leader_rows[row["merge_candidate_id"]] = row
            continue
        ignored_rows.append(row)

    for target_id in list(merged_rows_by_target):
        if target_id not in leader_rows:
            unresolved_merges.extend(merged_rows_by_target[target_id])
            for row in merged_rows_by_target[target_id]:
                issues.append(
                    issue(
                        "unresolved_merge_target",
                        row,
                        "merge target is missing from reviewed leader rows.",
                        {"merge_into_candidate_id": target_id},
                    )
                )
            del merged_rows_by_target[target_id]

    policy_items: list[dict[str, object]] = []
    display_texts: list[dict[str, object]] = []
    evidence_links: list[dict[str, object]] = []
    taxonomy_rows: list[dict[str, object]] = []
    derived_to_display: list[dict[str, object]] = []

    counter = 1
    for merge_candidate_id in sorted(leader_rows):
        leader = leader_rows[merge_candidate_id]
        followers = merged_rows_by_target.get(merge_candidate_id, [])
        final_role = resolve_role(leader)
        final_label = resolve_label(leader)
        final_statement_parts = [resolve_statement(leader)]
        final_statement_parts.extend(resolve_statement(row) for row in followers)
        final_statement = " ".join(dedupe_preserve([part for part in final_statement_parts if part]))
        if not final_label or not final_statement:
            issues.append(
                issue(
                    "missing_final_text",
                    leader,
                    "final item label or statement is empty after review resolution.",
                    {"final_label": final_label, "final_statement": final_statement},
                )
            )
            continue
        resource_type = resolve_resource_type(leader, final_role)
        bucket_id = bucket_by_key.get((policy_id, resource_type), "")
        if not bucket_id:
            issues.append(
                issue(
                    "missing_bucket_mapping",
                    leader,
                    "resource type does not map to a policy bucket.",
                    {"policy_id": policy_id, "resource_type": resource_type},
                )
            )
            continue

        policy_item_id = f"ITM-{policy_id}-RV-{counter:05d}"
        display_text_id = f"DSP-{policy_id}-RV-{counter:05d}"
        counter += 1

        notes = dedupe_preserve(
            [
                f"source_merge_candidate={merge_candidate_id}",
                f"candidate_role={final_role}",
                f"merged_followers={len(followers)}" if followers else "",
            ]
        )

        policy_items.append(
            {
                "policy_item_id": policy_item_id,
                "policy_bucket_id": bucket_id,
                "item_label": final_label,
                "item_statement": final_statement,
                "item_description": f"{args.document_id} p.{leader['page_no']} | {final_role}",
                "item_status": "reviewed",
                "source_basis_type": "source_document_only",
                "curation_priority": policy_order,
                "notes": "; ".join(notes),
            }
        )
        display_texts.append(
            {
                "display_text_id": display_text_id,
                "target_object_type": "policy_item",
                "target_object_id": policy_item_id,
                "display_role": "policy_item_summary",
                "title_text": final_label,
                "summary_text": build_summary(final_statement),
                "description_text": f"{args.document_id} | {final_role}",
                "generated_by": "review_workbench_v1",
                "review_status": "reviewed",
                "source_basis_type": "source_document_only",
                "notes": "",
            }
        )

        member_rows = [leader] + followers
        member_derived_ids: list[tuple[str, str]] = []
        for row in member_rows:
            seed_ids = parse_ids(row.get("member_seed_ids", ""))
            review_seed_ids = parse_ids(row.get("supporting_review_seed_ids", ""))
            paragraph_ids = [
                seed_to_paragraph.get(seed_id, seed_id)
                for seed_id in seed_ids + review_seed_ids
            ]
            derived_ids = dedupe_preserve([paragraph_to_derived.get(paragraph_id, "") for paragraph_id in paragraph_ids])
            for derived_id in derived_ids:
                if derived_id:
                    member_derived_ids.append((row["merge_candidate_id"], derived_id))

        deduped_member_derived_ids: list[tuple[str, str]] = []
        seen_derived_ids: set[str] = set()
        for merge_candidate_id, derived_id in member_derived_ids:
            if derived_id in seen_derived_ids:
                continue
            seen_derived_ids.add(derived_id)
            deduped_member_derived_ids.append((merge_candidate_id, derived_id))

        if not deduped_member_derived_ids:
            issues.append(
                issue(
                    "missing_evidence_links",
                    leader,
                    "reviewed item does not resolve to any derived paragraph evidence.",
                    {"member_seed_ids": leader.get("member_seed_ids", "")},
                )
            )
            policy_items.pop()
            display_texts.pop()
            continue

        primary_rep = ""
        link_counter = 1
        for merge_candidate_id, derived_id in deduped_member_derived_ids:
                is_primary = 1 if not primary_rep else 0
                if is_primary:
                    primary_rep = derived_id
                evidence_links.append(
                    {
                        "policy_item_evidence_link_id": f"LNK-{policy_item_id}-{link_counter:02d}",
                        "policy_item_id": policy_item_id,
                        "derived_representation_id": derived_id,
                        "link_role": "primary_support" if is_primary else "secondary_support",
                        "evidence_strength": "high" if is_primary else "medium",
                        "is_primary": is_primary,
                        "sort_order": link_counter,
                        "notes": f"source_merge_candidate={merge_candidate_id}",
                    }
                )
                if is_primary:
                    derived_to_display.append(
                        {
                            "derived_to_display_map_id": f"DTD-{policy_item_id}-{link_counter:02d}",
                            "derived_representation_id": derived_id,
                            "display_text_id": display_text_id,
                            "display_role": "policy_item_summary",
                            "is_primary": 1,
                            "notes": "",
                        }
                    )
                link_counter += 1

        strategy_ids = parse_ids(clean_text(leader.get("reviewer_strategy_override", "")) or leader.get("primary_strategy_candidates", ""))
        tech_domain_ids = parse_ids(clean_text(leader.get("reviewer_tech_domain_override", "")) or leader.get("tech_domain_candidates", ""))
        tech_subdomain_ids = parse_ids(clean_text(leader.get("reviewer_tech_subdomain_override", "")) or leader.get("tech_subdomain_candidates", ""))

        for index, strategy_id in enumerate(strategy_ids, start=1):
            taxonomy_rows.append(
                {
                    "policy_item_taxonomy_map_id": f"PIT-{policy_item_id}-STR-{index:02d}",
                    "policy_item_id": policy_item_id,
                    "taxonomy_type": "strategy",
                    "term_id": strategy_id,
                    "is_primary": 1 if index == 1 else 0,
                    "confidence": "high" if clean_text(leader.get("reviewer_strategy_override", "")) else "medium",
                    "review_status": "reviewed",
                    "notes": "source=review_workbench",
                }
            )
        for index, tech_domain_id in enumerate(tech_domain_ids, start=1):
            taxonomy_rows.append(
                {
                    "policy_item_taxonomy_map_id": f"PIT-{policy_item_id}-TD-{index:02d}",
                    "policy_item_id": policy_item_id,
                    "taxonomy_type": "tech_domain",
                    "term_id": tech_domain_id,
                    "is_primary": 1 if index == 1 else 0,
                    "confidence": "high" if clean_text(leader.get("reviewer_tech_domain_override", "")) else "medium",
                    "review_status": "reviewed",
                    "notes": "source=review_workbench",
                }
            )
        for index, tech_subdomain_id in enumerate(tech_subdomain_ids, start=1):
            taxonomy_rows.append(
                {
                    "policy_item_taxonomy_map_id": f"PIT-{policy_item_id}-TSD-{index:02d}",
                    "policy_item_id": policy_item_id,
                    "taxonomy_type": "tech_subdomain",
                    "term_id": tech_subdomain_id,
                    "is_primary": 1 if index == 1 else 0,
                    "confidence": "high" if clean_text(leader.get("reviewer_tech_subdomain_override", "")) else "medium",
                    "review_status": "reviewed",
                    "notes": "source=review_workbench",
                }
            )

    summary = {
        "document_id": args.document_id,
        "workbench_path": str(workbench_path),
        "run_status": "no_reviewed_rows" if not reviewed_rows else "completed",
        "reviewed_source_row_count": len(reviewed_rows),
        "reviewed_decision_counts": dict(reviewed_decision_counter),
        "reviewed_item_count": len(policy_items),
        "display_text_count": len(display_texts),
        "evidence_link_count": len(evidence_links),
        "taxonomy_row_count": len(taxonomy_rows),
        "ignored_reviewed_row_count": len(ignored_rows),
        "unresolved_merge_count": len(unresolved_merges),
        "issue_count": len(issues),
        "issue_counts": dict(Counter(entry["code"] for entry in issues)),
        "issues": issues[:20],
    }

    write_csv(
        output_dir / f"{args.document_id}__policy-items-reviewed.csv",
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
        output_dir / f"{args.document_id}__display-texts-reviewed.csv",
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
        output_dir / f"{args.document_id}__policy-item-evidence-links-reviewed.csv",
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
        output_dir / f"{args.document_id}__policy-item-taxonomy-map-reviewed.csv",
        taxonomy_rows,
        [
            "policy_item_taxonomy_map_id",
            "policy_item_id",
            "taxonomy_type",
            "term_id",
            "is_primary",
            "confidence",
            "review_status",
            "notes",
        ],
    )
    write_csv(
        output_dir / f"{args.document_id}__derived-to-display-map-reviewed.csv",
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
    write_json(output_dir / f"{args.document_id}__reviewed-items-summary.json", summary)


if __name__ == "__main__":
    main()
