#!/usr/bin/env python3
"""Package a dated ontology/dashboard snapshot into a delivery zip."""

from __future__ import annotations

import argparse
import json
import zipfile
from datetime import date
from pathlib import Path


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


def add_tree(zip_handle: zipfile.ZipFile, root: Path, arc_prefix: str) -> int:
    count = 0
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        arcname = f"{arc_prefix}/{path.relative_to(root).as_posix()}"
        zip_handle.write(path, arcname)
        count += 1
    return count


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-root", default=".")
    parser.add_argument("--snapshot-date", default=date.today().isoformat())
    args = parser.parse_args()

    repo_root = Path(args.out_root).resolve()
    snapshot_date = args.snapshot_date

    ontology_snapshot_dir = repo_root / "work/04_ontology/exports/snapshots" / snapshot_date
    dashboard_snapshot_dir = repo_root / "work/05_dashboard/data-contracts/snapshots" / snapshot_date
    frontend_snapshot_dir = repo_root / "work/05_dashboard/frontend/dist-snapshots" / snapshot_date
    manifest_path = ontology_snapshot_dir / "snapshot-manifest.json"

    for path in [ontology_snapshot_dir, dashboard_snapshot_dir, frontend_snapshot_dir, manifest_path]:
        if not path.exists():
            raise FileNotFoundError(path)

    manifest = load_json(manifest_path)
    release_dir = repo_root / "work/releases"
    release_dir.mkdir(parents=True, exist_ok=True)
    zip_path = release_dir / f"{snapshot_date}_ontology-dashboard-release-bundle.zip"
    readme_path = release_dir / f"{snapshot_date}_ontology-dashboard-release-bundle.README.md"

    file_count = 0
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as handle:
        file_count += add_tree(handle, ontology_snapshot_dir, f"ontology_snapshot_{snapshot_date}")
        file_count += add_tree(handle, dashboard_snapshot_dir, f"dashboard_snapshot_{snapshot_date}")
        file_count += add_tree(handle, frontend_snapshot_dir, f"dashboard_build_snapshot_{snapshot_date}")

    lines = [
        f"# {snapshot_date} Ontology Dashboard Release Bundle",
        "",
        f"- zip_path: `{zip_path.relative_to(repo_root).as_posix()}`",
        f"- file_count: `{file_count}`",
        f"- bundle_size_bytes: `{zip_path.stat().st_size}`",
        f"- ontology_validation_status: `{manifest['summary']['ontology_validation_status']}`",
        f"- technology_lens_validation_status: `{manifest['summary']['technology_lens_validation_status']}`",
        f"- active_strategy_review_queue_count: `{manifest['summary']['active_strategy_review_queue_count']}`",
        "",
        "## Included Trees",
        f"- `ontology_snapshot_{snapshot_date}/`",
        f"- `dashboard_snapshot_{snapshot_date}/`",
        f"- `dashboard_build_snapshot_{snapshot_date}/`",
        "",
        "## Source Manifest",
        f"- `{manifest_path.relative_to(repo_root).as_posix()}`",
        "",
    ]
    write_text(readme_path, "\n".join(lines))

    print(zip_path)
    print(readme_path)


if __name__ == "__main__":
    main()
