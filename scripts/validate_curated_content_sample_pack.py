#!/usr/bin/env python3
"""Validate curated content sample pack traceability and declared scope."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def iter_pack_evidence(pack: dict[str, object]):
    for policy in pack.get("policies", []):
        for bucket in policy.get("buckets", []):
            for group in bucket.get("groups", []):
                for content in group.get("contents", []):
                    for evidence in content.get("evidence", []):
                        yield {
                            "policy_id": policy.get("policy_id", ""),
                            "policy_bucket_id": bucket.get("policy_bucket_id", ""),
                            "policy_item_group_id": group.get("policy_item_group_id", ""),
                            "policy_item_content_id": content.get("policy_item_content_id", ""),
                            "derived_representation_id": evidence.get("derived_representation_id", ""),
                            "representation_type": evidence.get("representation_type", ""),
                            "source_asset_ids": [asset.get("source_asset_id", "") for asset in evidence.get("source_assets", [])],
                        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pack-json", required=True)
    parser.add_argument("--derived-map-csv", required=True)
    parser.add_argument("--source-assets-csv", required=True)
    parser.add_argument("--out-json")
    args = parser.parse_args()

    pack_path = Path(args.pack_json)
    pack = json.loads(pack_path.read_text(encoding="utf-8"))

    derived_rows = load_csv_rows(Path(args.derived_map_csv))
    source_asset_rows = load_csv_rows(Path(args.source_assets_csv))

    expected_assets_by_rep: dict[str, list[str]] = {}
    for row in derived_rows:
        expected_assets_by_rep.setdefault(row["derived_representation_id"], []).append(row["source_asset_id"])

    source_asset_lookup = {row["source_asset_id"]: row for row in source_asset_rows}

    evidence_records = list(iter_pack_evidence(pack))
    mismatches: list[dict[str, object]] = []
    missing_source_assets: list[dict[str, object]] = []
    representation_types = sorted(
        {record["representation_type"] for record in evidence_records if record["representation_type"]}
    )
    taxonomy_types = sorted(
        {
            taxonomy.get("taxonomy_type", "")
            for policy in pack.get("policies", [])
            for bucket in policy.get("buckets", [])
            for group in bucket.get("groups", [])
            for taxonomy in group.get("taxonomies", [])
            if taxonomy.get("taxonomy_type")
        }
    )

    for record in evidence_records:
        expected_asset_ids = expected_assets_by_rep.get(record["derived_representation_id"], [])
        actual_asset_ids = record["source_asset_ids"]
        if expected_asset_ids != actual_asset_ids:
            mismatches.append(
                {
                    "derived_representation_id": record["derived_representation_id"],
                    "policy_item_group_id": record["policy_item_group_id"],
                    "policy_item_content_id": record["policy_item_content_id"],
                    "expected_source_asset_ids": expected_asset_ids,
                    "actual_source_asset_ids": actual_asset_ids,
                }
            )
        for source_asset_id in actual_asset_ids:
            if source_asset_id not in source_asset_lookup:
                missing_source_assets.append(
                    {
                        "derived_representation_id": record["derived_representation_id"],
                        "source_asset_id": source_asset_id,
                    }
                )

    warnings: list[str] = []
    if representation_types == ["normalized_paragraph"]:
        warnings.append("Sample pack currently includes normalized_paragraph evidence only.")
    if "tech_subdomain" not in taxonomy_types:
        warnings.append("Sample pack does not include tech_subdomain taxonomy examples.")
    if pack.get("sample_scope", {}).get("strict_implementation_contract", True):
        warnings.append("strict_implementation_contract should be false for this sample pack.")

    payload = {
        "status": "pass" if not mismatches and not missing_source_assets else "fail",
        "pack_path": str(pack_path),
        "contract_level": pack.get("sample_scope", {}).get("contract_level", ""),
        "evidence_count": len(evidence_records),
        "matched_evidence_count": len(evidence_records) - len(mismatches),
        "mismatch_count": len(mismatches),
        "missing_source_asset_count": len(missing_source_assets),
        "included_representation_types": representation_types,
        "included_taxonomy_types": taxonomy_types,
        "warnings": warnings,
        "mismatches": mismatches,
        "missing_source_assets": missing_source_assets,
    }

    output = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.out_json:
        out_path = Path(args.out_json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output, encoding="utf-8")
    else:
        print(output)


if __name__ == "__main__":
    main()
