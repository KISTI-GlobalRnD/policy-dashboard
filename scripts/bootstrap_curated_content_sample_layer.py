#!/usr/bin/env python3
"""Build, validate, and load the curated content sample layer into an ontology store."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def run_step(repo_root: Path, args: list[str]) -> None:
    subprocess.run(["python3", *args], cwd=repo_root, check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--db-path", required=True)
    parser.add_argument("--sample-dir", required=True)
    parser.add_argument("--pack-json", required=True)
    parser.add_argument("--summary-json", required=True)
    parser.add_argument("--pack-validation-json", required=True)
    parser.add_argument("--derived-map-csv", required=True)
    parser.add_argument("--source-assets-csv", required=True)
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()

    run_step(
        repo_root,
        [
            "scripts/build_curated_content_sample_pack.py",
            "--db-path",
            args.db_path,
            "--out-dir",
            args.sample_dir,
            "--out-json",
            args.pack_json,
            "--out-summary-json",
            args.summary_json,
            "--derived-map-csv",
            args.derived_map_csv,
            "--source-assets-csv",
            args.source_assets_csv,
        ],
    )
    run_step(
        repo_root,
        [
            "scripts/validate_curated_content_sample_pack.py",
            "--pack-json",
            args.pack_json,
            "--derived-map-csv",
            args.derived_map_csv,
            "--source-assets-csv",
            args.source_assets_csv,
            "--out-json",
            args.pack_validation_json,
        ],
    )

    validation_payload = json.loads(Path(args.pack_validation_json).read_text(encoding="utf-8"))
    if validation_payload.get("status") != "pass":
        raise RuntimeError(f"Curated content sample validation failed: {args.pack_validation_json}")

    run_step(
        repo_root,
        [
            "scripts/load_curated_content_sample_pack.py",
            "--db-path",
            args.db_path,
            "--sample-dir",
            args.sample_dir,
        ],
    )

    print("curated_content_sample_layer_bootstrapped")


if __name__ == "__main__":
    main()
