#!/usr/bin/env python3
"""Run the end-to-end sample dashboard pipeline."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


def run_step(repo_root: Path, args: list[str]) -> None:
    subprocess.run(args, cwd=repo_root, check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()

    run_step(
        repo_root,
        [
            "python3",
            "scripts/build_policy_ontology_seeds.py",
            "--registry-path",
            "work/01_scope-and-ia/requirements/04_document-registry.csv",
            "--out-dir",
            "work/04_ontology/instances",
        ],
    )
    run_step(
        repo_root,
        [
            "python3",
            "scripts/init_ontology_store.py",
            "--db-path",
            "work/04_ontology/ontology.sqlite",
            "--schema-path",
            "work/04_ontology/schemas/03_relational-ontology-schema.sql",
            "--seed-dir",
            "work/04_ontology/instances",
            "--replace",
        ],
    )
    run_step(
        repo_root,
        [
            "python3",
            "scripts/load_ontology_evidence.py",
            "--db-path",
            "work/04_ontology/ontology.sqlite",
            "--normalized-dir",
            "work/03_processing/normalized",
            "--instances-dir",
            "work/04_ontology/instances",
            "--figures-dir",
            "work/02_structured-extraction/figures",
        ],
    )
    run_step(
        repo_root,
        [
            "python3",
            "scripts/build_paragraph_source_map.py",
            "--normalized-dir",
            "work/03_processing/normalized",
            "--text-dir",
            "work/02_structured-extraction/text",
            "--out-csv",
            "work/04_ontology/instances/paragraph_source_map.csv",
            "--out-report",
            "qa/ontology/2026-03-14_paragraph-source-map-report.json",
            "--db-path",
            "work/04_ontology/ontology.sqlite",
        ],
    )
    run_step(
        repo_root,
        [
            "python3",
            "scripts/build_source_assets.py",
            "--db-path",
            "work/04_ontology/ontology.sqlite",
            "--repo-root",
            ".",
            "--out-assets-csv",
            "work/04_ontology/instances/source_assets_auto.csv",
            "--out-map-csv",
            "work/04_ontology/instances/derived_to_source_asset_map_auto.csv",
        ],
    )
    run_step(
        repo_root,
        [
            "python3",
            "scripts/build_tech_taxonomy_seeds.py",
            "--taxonomy-csv",
            "work/03_processing/normalized/DOC-TAX-001__tech-domain-subdomain.csv",
            "--out-dir",
            "work/04_ontology/instances",
            "--db-path",
            "work/04_ontology/ontology.sqlite",
        ],
    )
    run_step(
        repo_root,
        [
            "python3",
            "scripts/build_auto_policy_items.py",
            "--db-path",
            "work/04_ontology/ontology.sqlite",
            "--out-dir",
            "work/04_ontology/instances",
        ],
    )
    run_step(
        repo_root,
        [
            "python3",
            "scripts/classify_policy_items_tech_domains.py",
            "--db-path",
            "work/04_ontology/ontology.sqlite",
            "--keyword-json",
            "work/04_ontology/vocabularies/tech-domain-keywords.json",
            "--out-csv",
            "work/04_ontology/instances/policy_item_taxonomy_map_auto.csv",
        ],
    )
    run_step(
        repo_root,
        [
            "python3",
            "scripts/bootstrap_curated_content_sample_layer.py",
            "--repo-root",
            ".",
            "--db-path",
            "work/04_ontology/ontology.sqlite",
            "--sample-dir",
            "work/04_ontology/sample_build/curated_content_sample",
            "--pack-json",
            "work/04_ontology/sample_build/curated_content_sample/curated_content_sample_pack.json",
            "--summary-json",
            "work/04_ontology/sample_build/curated_content_sample/curated_content_sample_summary.json",
            "--pack-validation-json",
            "qa/ontology/2026-03-16_curated-content-sample-pack-validation.json",
            "--derived-map-csv",
            "work/04_ontology/instances/derived_to_source_asset_map_auto.csv",
            "--source-assets-csv",
            "work/04_ontology/instances/source_assets_auto.csv",
        ],
    )
    run_step(
        repo_root,
        [
            "python3",
            "scripts/export_dashboard_sample.py",
            "--db-path",
            "work/04_ontology/ontology.sqlite",
            "--out-json",
            "work/05_dashboard/data-contracts/sample-dashboard.json",
        ],
    )

    print("Sample dashboard pipeline completed.")


if __name__ == "__main__":
    main()
