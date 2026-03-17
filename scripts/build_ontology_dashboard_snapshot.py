#!/usr/bin/env python3
"""Freeze ontology and dashboard artifacts into a dated snapshot."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import date
from pathlib import Path


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


def reset_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def sha256sum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def copy_with_meta(source: Path, destination: Path, repo_root: Path) -> dict[str, object]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return {
        "source_path": str(source.relative_to(repo_root)).replace("\\", "/"),
        "snapshot_path": str(destination.relative_to(repo_root)).replace("\\", "/"),
        "size_bytes": destination.stat().st_size,
        "sha256": sha256sum(destination),
    }


def copy_tree_with_meta(source_dir: Path, destination_dir: Path, repo_root: Path) -> list[dict[str, object]]:
    copied: list[dict[str, object]] = []
    for source in sorted(path for path in source_dir.rglob("*") if path.is_file()):
        relative = source.relative_to(source_dir)
        copied.append(copy_with_meta(source, destination_dir / relative, repo_root))
    return copied


def summarize_paragraph_map(report_rows: list[dict[str, object]]) -> dict[str, object]:
    total = sum(int(row.get("paragraph_count", 0)) for row in report_rows)
    mapped = sum(int(row.get("mapped_count", 0)) for row in report_rows)
    return {
        "document_count": len(report_rows),
        "paragraph_count": total,
        "mapped_count": mapped,
        "coverage_ratio": round((mapped / total), 6) if total else 0.0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-root", default=".")
    parser.add_argument("--snapshot-date", default=date.today().isoformat())
    args = parser.parse_args()

    repo_root = Path(args.out_root).resolve()
    snapshot_date = args.snapshot_date

    ontology_snapshot_dir = repo_root / "work/04_ontology/exports/snapshots" / snapshot_date
    dashboard_snapshot_dir = repo_root / "work/05_dashboard/data-contracts/snapshots" / snapshot_date
    dashboard_build_snapshot_dir = repo_root / "work/05_dashboard/frontend/dist-snapshots" / snapshot_date
    qa_md_path = repo_root / "qa/ontology" / f"{snapshot_date}_ontology-dashboard-frozen-snapshot.md"
    manifest_path = ontology_snapshot_dir / "snapshot-manifest.json"

    ontology_sources = [
        repo_root / "work/04_ontology/ontology.sqlite",
        repo_root / "work/04_ontology/ontology_curated_sample.sqlite",
        repo_root / "work/04_ontology/exports/policy-ontology.jsonld",
        repo_root / "work/04_ontology/exports/policy-ontology.ttl",
        repo_root / "qa/ontology" / f"{snapshot_date}_ontology-store-validation.json",
        repo_root / "qa/ontology" / f"{snapshot_date}_paragraph-source-map-report.json",
    ]
    dashboard_sources = [
        repo_root / "work/05_dashboard/data-contracts/technology-lens.json",
        repo_root / "work/05_dashboard/data-contracts/sample-dashboard.json",
        repo_root / "work/05_dashboard/index.html",
        repo_root / "work/05_dashboard/briefing.css",
        repo_root / "qa/ontology" / f"{snapshot_date}_technology-lens-validation.json",
    ]
    dashboard_dist_dir = repo_root / "work/05_dashboard/frontend/dist"

    for path in ontology_sources + dashboard_sources:
        if not path.exists():
            raise FileNotFoundError(path)
    if not dashboard_dist_dir.exists():
        raise FileNotFoundError(dashboard_dist_dir)

    reset_dir(ontology_snapshot_dir)
    reset_dir(dashboard_snapshot_dir)
    reset_dir(dashboard_build_snapshot_dir)

    ontology_validation = load_json(repo_root / "qa/ontology" / f"{snapshot_date}_ontology-store-validation.json")
    technology_validation = load_json(repo_root / "qa/ontology" / f"{snapshot_date}_technology-lens-validation.json")
    paragraph_report = load_json(repo_root / "qa/ontology" / f"{snapshot_date}_paragraph-source-map-report.json")
    strategy_decision_summary = load_json(
        repo_root / "qa/ontology/review_queues/policy-item-strategy-review-decisions-summary.json"
    )

    copied_files: list[dict[str, object]] = []
    for source in ontology_sources:
        copied_files.append(copy_with_meta(source, ontology_snapshot_dir / source.name, repo_root))
    for source in dashboard_sources:
        copied_files.append(copy_with_meta(source, dashboard_snapshot_dir / source.name, repo_root))
    copied_files.extend(copy_tree_with_meta(dashboard_dist_dir, dashboard_build_snapshot_dir, repo_root))

    manifest = {
        "snapshot_date": snapshot_date,
        "snapshot_kind": "ontology-dashboard-frozen-snapshot",
        "status": "frozen",
        "summary": {
            "ontology_validation_status": ontology_validation.get("status"),
            "ontology_issue_count": len(ontology_validation.get("issues", [])),
            "technology_lens_validation_status": technology_validation.get("status"),
            "technology_lens_issue_count": technology_validation.get("issue_count", 0),
            "active_strategy_review_queue_count": strategy_decision_summary.get("active_in_queue_count", 0),
            "strategy_review_status_counts": strategy_decision_summary.get("status_counts", {}),
            "policy_item_count": ontology_validation.get("stats", {}).get("policy_item_count"),
            "derived_representation_count": ontology_validation.get("stats", {}).get("derived_representation_count"),
            "source_asset_count": ontology_validation.get("stats", {}).get("source_asset_count"),
            "paragraph_source_map": summarize_paragraph_map(paragraph_report),
        },
        "files": copied_files,
        "source_refs": {
            "extraction_snapshot": "work/02_structured-extraction/manifests/batch_runs/2026-03-17_extraction-completion-snapshot.json",
            "strategy_review_decision_summary": "qa/ontology/review_queues/policy-item-strategy-review-decisions-summary.json",
            "strategy_review_batch_summary": "qa/ontology/review_packets/strategy-review-batch-index-summary.json",
        },
    }
    write_json(manifest_path, manifest)

    lines = [
        f"# {snapshot_date} Ontology Dashboard Frozen Snapshot",
        "",
        "## Status",
        f"- ontology_validation_status: `{manifest['summary']['ontology_validation_status']}`",
        f"- ontology_issue_count: `{manifest['summary']['ontology_issue_count']}`",
        f"- technology_lens_validation_status: `{manifest['summary']['technology_lens_validation_status']}`",
        f"- technology_lens_issue_count: `{manifest['summary']['technology_lens_issue_count']}`",
        f"- active_strategy_review_queue_count: `{manifest['summary']['active_strategy_review_queue_count']}`",
        f"- policy_item_count: `{manifest['summary']['policy_item_count']}`",
        f"- derived_representation_count: `{manifest['summary']['derived_representation_count']}`",
        f"- source_asset_count: `{manifest['summary']['source_asset_count']}`",
        f"- paragraph_source_coverage_ratio: `{manifest['summary']['paragraph_source_map']['coverage_ratio']}`",
        "",
        "## Snapshot Directories",
        f"- ontology snapshot: `work/04_ontology/exports/snapshots/{snapshot_date}`",
        f"- dashboard snapshot: `work/05_dashboard/data-contracts/snapshots/{snapshot_date}`",
        f"- dashboard build snapshot: `work/05_dashboard/frontend/dist-snapshots/{snapshot_date}`",
        "",
        "## Frozen Files",
    ]
    for file_info in copied_files:
        lines.append(
            f"- `{file_info['snapshot_path']}` <= `{file_info['source_path']}` sha256=`{file_info['sha256'][:16]}`"
        )
    lines.append("")

    write_text(qa_md_path, "\n".join(lines))
    print(manifest_path)
    print(qa_md_path)


if __name__ == "__main__":
    main()
