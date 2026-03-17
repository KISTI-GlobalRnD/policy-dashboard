#!/usr/bin/env python3
"""Generate draft recommendation artifacts for all strategy review batches."""

from __future__ import annotations

import argparse
import csv
import subprocess
from pathlib import Path

from generated_artifact_utils import cleanup_stale_files


def run_step(repo_root: Path, args: list[str]) -> None:
    subprocess.run(args, cwd=repo_root, check=True)


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--batches-dir", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--batch-index-csv")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    batches_dir = (repo_root / args.batches_dir).resolve()
    out_dir = (repo_root / args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.batch_index_csv:
        batch_paths = [
            batches_dir / row["output_csv"]
            for row in read_csv_rows((repo_root / args.batch_index_csv).resolve())
            if row.get("output_csv")
        ]
    else:
        batch_paths = sorted(batches_dir.glob("*.csv"))
    keep_names: set[str] = set()
    for batch_path in batch_paths:
        stem = batch_path.stem
        keep_names.update(
            {
                f"{stem}__draft.csv",
                f"{stem}__draft-summary.json",
                f"{stem}__draft-brief.md",
            }
        )
        run_step(
            repo_root,
            [
                "python3",
                "scripts/build_strategy_batch_draft_recommendations.py",
                "--batch-csv",
                str(batch_path.relative_to(repo_root)).replace("\\", "/"),
                "--out-csv",
                str((out_dir / f"{stem}__draft.csv").relative_to(repo_root)).replace("\\", "/"),
                "--out-summary-json",
                str((out_dir / f"{stem}__draft-summary.json").relative_to(repo_root)).replace("\\", "/"),
                "--out-brief-md",
                str((out_dir / f"{stem}__draft-brief.md").relative_to(repo_root)).replace("\\", "/"),
            ],
        )

    cleanup_stale_files(
        out_dir,
        keep_names,
        [
            "*__batch-*__draft.csv",
            "*__batch-*__draft-summary.json",
            "*__batch-*__draft-brief.md",
        ],
    )
    cleanup_stale_files(
        out_dir / "batches",
        keep_names,
        [
            "*__batch-*__draft.csv",
            "*__batch-*__draft-summary.json",
            "*__batch-*__draft-brief.md",
        ],
    )
    print(f"Strategy review draft batches: {len(batch_paths)}")


if __name__ == "__main__":
    main()
