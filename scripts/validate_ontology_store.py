#!/usr/bin/env python3
"""Validate core ontology store invariants and emit a JSON QA report."""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


def issue(level: str, code: str, message: str, details: object) -> dict[str, object]:
    return {"level": level, "code": code, "message": message, "details": details}


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", required=True)
    parser.add_argument("--out-report", required=True)
    args = parser.parse_args()

    connection = sqlite3.connect(args.db_path)
    connection.row_factory = sqlite3.Row
    try:
        issues: list[dict[str, object]] = []
        stats: dict[str, object] = {}

        bucket_counts = connection.execute(
            """
            SELECT p.policy_id, p.policy_name, COUNT(pb.policy_bucket_id) AS bucket_count
            FROM policies p
            LEFT JOIN policy_buckets pb ON pb.policy_id = p.policy_id
            GROUP BY p.policy_id, p.policy_name
            ORDER BY p.policy_order
            """
        ).fetchall()
        bad_buckets = [dict(row) for row in bucket_counts if row["bucket_count"] != 3]
        if bad_buckets:
            issues.append(issue("error", "policy_bucket_cardinality", "Each policy must have exactly 3 buckets.", bad_buckets))

        item_without_evidence = connection.execute(
            """
            SELECT pi.policy_item_id, pi.item_label
            FROM policy_items pi
            LEFT JOIN policy_item_evidence_links link ON link.policy_item_id = pi.policy_item_id
            WHERE link.policy_item_id IS NULL
            ORDER BY pi.policy_item_id
            """
        ).fetchall()
        if item_without_evidence:
            issues.append(issue("error", "policy_item_missing_evidence", "Policy items without evidence links exist.", [dict(row) for row in item_without_evidence[:20]]))

        item_without_display = connection.execute(
            """
            SELECT pi.policy_item_id, pi.item_label
            FROM policy_items pi
            LEFT JOIN display_texts dt
              ON dt.target_object_type = 'policy_item'
             AND dt.target_object_id = pi.policy_item_id
            WHERE dt.display_text_id IS NULL
            ORDER BY pi.policy_item_id
            """
        ).fetchall()
        if item_without_display:
            issues.append(issue("error", "policy_item_missing_display", "Policy items without display texts exist.", [dict(row) for row in item_without_display[:20]]))

        rep_without_source = connection.execute(
            """
            SELECT dr.derived_representation_id, dr.representation_type
            FROM derived_representations dr
            LEFT JOIN derived_to_source_asset_map map ON map.derived_representation_id = dr.derived_representation_id
            WHERE map.derived_representation_id IS NULL
            ORDER BY dr.derived_representation_id
            """
        ).fetchall()
        if rep_without_source:
            issues.append(issue("error", "derived_representation_missing_source_asset", "Derived representations without source asset mappings exist.", [dict(row) for row in rep_without_source[:20]]))

        paragraph_coverage = connection.execute(
            """
            SELECT
                ep.document_id,
                COUNT(*) AS paragraph_count,
                SUM(CASE WHEN psm.paragraph_id IS NOT NULL THEN 1 ELSE 0 END) AS mapped_count
            FROM evidence_paragraphs ep
            LEFT JOIN (
                SELECT DISTINCT paragraph_id
                FROM paragraph_source_map
            ) psm ON psm.paragraph_id = ep.paragraph_id
            GROUP BY ep.document_id
            ORDER BY ep.document_id
            """
        ).fetchall()
        coverage_rows = []
        for row in paragraph_coverage:
            paragraph_count = row["paragraph_count"]
            mapped_count = row["mapped_count"]
            coverage = mapped_count / paragraph_count if paragraph_count else 0.0
            coverage_rows.append(
                {
                    "document_id": row["document_id"],
                    "paragraph_count": paragraph_count,
                    "mapped_count": mapped_count,
                    "coverage_ratio": round(coverage, 4),
                }
            )
            if coverage < 0.9:
                issues.append(issue("warning", "paragraph_source_map_low_coverage", "Paragraph provenance coverage below 0.90.", coverage_rows[-1]))

        taxonomy_summary = connection.execute(
            """
            SELECT taxonomy_type, COUNT(*) AS mapping_count
            FROM policy_item_taxonomy_map
            GROUP BY taxonomy_type
            ORDER BY taxonomy_type
            """
        ).fetchall()

        strategy_count = connection.execute("SELECT COUNT(*) FROM strategies").fetchone()[0]
        if strategy_count != 15:
            issues.append(
                issue(
                    "error",
                    "strategy_cardinality",
                    "The ontology store must contain exactly 15 strategies.",
                    {"strategy_count": strategy_count},
                )
            )

        missing_primary_strategy = connection.execute(
            """
            SELECT pi.policy_item_id, pi.item_label
            FROM policy_items pi
            LEFT JOIN policy_item_taxonomy_map pitm
              ON pitm.policy_item_id = pi.policy_item_id
             AND pitm.taxonomy_type = 'strategy'
             AND pitm.is_primary = 1
            LEFT JOIN curation_assertions ca
              ON ca.target_object_type = 'policy_item'
             AND ca.target_object_id = pi.policy_item_id
             AND ca.assertion_type = 'primary_strategy'
             AND ca.asserted_value = 'NO_STRATEGY'
             AND ca.review_status = 'reviewed'
            WHERE pitm.policy_item_taxonomy_map_id IS NULL
              AND ca.assertion_id IS NULL
            ORDER BY pi.policy_item_id
            """
        ).fetchall()
        if missing_primary_strategy:
            issues.append(
                issue(
                    "warning",
                    "policy_item_missing_primary_strategy",
                    "Policy items without a primary strategy mapping exist.",
                    [dict(row) for row in missing_primary_strategy[:20]],
                )
            )

        policy_item_group_count = connection.execute("SELECT COUNT(*) FROM policy_item_groups").fetchone()[0]
        policy_item_content_count = connection.execute("SELECT COUNT(*) FROM policy_item_contents").fetchone()[0]
        if policy_item_group_count:
            group_without_members = connection.execute(
                """
                SELECT pig.policy_item_group_id, pig.group_label
                FROM policy_item_groups pig
                LEFT JOIN policy_item_group_members pigm
                  ON pigm.policy_item_group_id = pig.policy_item_group_id
                WHERE pigm.policy_item_group_id IS NULL
                ORDER BY pig.policy_item_group_id
                """
            ).fetchall()
            if group_without_members:
                issues.append(
                    issue(
                        "error",
                        "policy_item_group_missing_members",
                        "Policy item groups without group members exist.",
                        [dict(row) for row in group_without_members[:20]],
                    )
                )

            group_without_contents = connection.execute(
                """
                SELECT pig.policy_item_group_id, pig.group_label
                FROM policy_item_groups pig
                LEFT JOIN policy_item_contents pic
                  ON pic.policy_item_group_id = pig.policy_item_group_id
                WHERE pic.policy_item_group_id IS NULL
                ORDER BY pig.policy_item_group_id
                """
            ).fetchall()
            if group_without_contents:
                issues.append(
                    issue(
                        "error",
                        "policy_item_group_missing_contents",
                        "Policy item groups without content nodes exist.",
                        [dict(row) for row in group_without_contents[:20]],
                    )
                )

            group_without_display = connection.execute(
                """
                SELECT pig.policy_item_group_id, pig.group_label
                FROM policy_item_groups pig
                LEFT JOIN display_texts dt
                  ON dt.target_object_type = 'policy_item_group'
                 AND dt.target_object_id = pig.policy_item_group_id
                WHERE dt.display_text_id IS NULL
                ORDER BY pig.policy_item_group_id
                """
            ).fetchall()
            if group_without_display:
                issues.append(
                    issue(
                        "warning",
                        "policy_item_group_missing_display",
                        "Policy item groups without display texts exist.",
                        [dict(row) for row in group_without_display[:20]],
                    )
                )

        if policy_item_content_count:
            content_without_evidence = connection.execute(
                """
                SELECT pic.policy_item_content_id, pic.content_label
                FROM policy_item_contents pic
                LEFT JOIN policy_item_content_evidence_links picel
                  ON picel.policy_item_content_id = pic.policy_item_content_id
                WHERE picel.policy_item_content_id IS NULL
                ORDER BY pic.policy_item_content_id
                """
            ).fetchall()
            if content_without_evidence:
                issues.append(
                    issue(
                        "error",
                        "policy_item_content_missing_evidence",
                        "Policy item contents without evidence links exist.",
                        [dict(row) for row in content_without_evidence[:20]],
                    )
                )

            content_without_display = connection.execute(
                """
                SELECT pic.policy_item_content_id, pic.content_label
                FROM policy_item_contents pic
                LEFT JOIN display_texts dt
                  ON dt.target_object_type = 'policy_item_content'
                 AND dt.target_object_id = pic.policy_item_content_id
                WHERE dt.display_text_id IS NULL
                ORDER BY pic.policy_item_content_id
                """
            ).fetchall()
            if content_without_display:
                issues.append(
                    issue(
                        "warning",
                        "policy_item_content_missing_display",
                        "Policy item contents without display texts exist.",
                        [dict(row) for row in content_without_display[:20]],
                    )
                )

        stats["policy_count"] = connection.execute("SELECT COUNT(*) FROM policies").fetchone()[0]
        stats["strategy_count"] = strategy_count
        stats["policy_item_count"] = connection.execute("SELECT COUNT(*) FROM policy_items").fetchone()[0]
        stats["policy_item_group_count"] = policy_item_group_count
        stats["policy_item_content_count"] = policy_item_content_count
        stats["derived_representation_count"] = connection.execute("SELECT COUNT(*) FROM derived_representations").fetchone()[0]
        stats["source_asset_count"] = connection.execute("SELECT COUNT(*) FROM source_assets").fetchone()[0]
        stats["display_text_count"] = connection.execute("SELECT COUNT(*) FROM display_texts").fetchone()[0]
        stats["curation_assertion_count"] = connection.execute("SELECT COUNT(*) FROM curation_assertions").fetchone()[0]
        stats["taxonomy_counts"] = [dict(row) for row in taxonomy_summary]
        stats["paragraph_source_coverage"] = coverage_rows
    finally:
        connection.close()

    payload = {
        "status": "pass" if not any(item["level"] == "error" for item in issues) else "fail",
        "issues": issues,
        "stats": stats,
    }
    write_json(Path(args.out_report), payload)
    print(payload["status"])
    print(f"issues={len(issues)}")


if __name__ == "__main__":
    main()
