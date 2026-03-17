#!/usr/bin/env python3
"""Build markdown review briefs for strategy review batches."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path

from generated_artifact_utils import cleanup_stale_files


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def parse_score(value: str) -> int:
    try:
        return int((value or "").strip())
    except ValueError:
        return 0


def summarize_counter(counter: Counter, limit: int = 5) -> list[tuple[str, int]]:
    return counter.most_common(limit)


def top_strategy_lines(rows: list[dict[str, str]]) -> list[str]:
    counter = Counter()
    for row in rows:
        strategy_id = row.get("suggested_primary_strategy_id", "")
        strategy_label = row.get("suggested_primary_strategy_label", "")
        if strategy_id:
            counter[f"{strategy_id} {strategy_label}"] += 1
    return [f"- `{label}`: {count}" for label, count in summarize_counter(counter)] or ["- 없음"]


def top_tech_lines(rows: list[dict[str, str]]) -> list[str]:
    counter = Counter()
    for row in rows:
        for token in (row.get("tech_domains", "") or "").split("|"):
            cleaned = token.strip()
            if cleaned:
                counter[cleaned] += 1
    return [f"- `{label}`: {count}" for label, count in summarize_counter(counter)] or ["- 없음"]


def sample_lines(rows: list[dict[str, str]], with_suggestion: bool, limit: int = 5) -> list[str]:
    filtered = [row for row in rows if bool(row.get("suggested_primary_strategy_id")) is with_suggestion][:limit]
    if not filtered:
        return ["- 없음"]
    lines = []
    for row in filtered:
        strategy = row.get("suggested_primary_strategy_id", "")
        label = row.get("suggested_primary_strategy_label", "")
        score = row.get("suggested_primary_strategy_score", "")
        suffix = f" -> {strategy} {label} (score={score})" if strategy else ""
        if (row.get("auto_seed_blocked") or "").strip().lower() == "yes":
            suffix += f" [auto-seed blocked: {row.get('alignment_exception_ids', '')}]"
        lines.append(f"- `{row['decision_key']}` {row['item_label']}{suffix}")
    return lines


def review_hints(row: dict[str, str]) -> list[str]:
    hints: list[str] = []
    item_count = int(row["item_count"])
    with_suggestion_count = int(row["with_suggestion_count"])
    without_suggestion_count = int(row["without_suggestion_count"])
    dominant_ratio = with_suggestion_count / item_count if item_count else 0.0
    bucket_label = row["bucket_label"]
    batch_id = row["batch_id"]

    if without_suggestion_count / item_count >= 0.7:
        hints.append("자동 제안이 거의 없으므로 기본값은 `no_strategy`에 가깝게 본다.")
    if with_suggestion_count == item_count:
        hints.append("모든 항목에 자동 제안이 있으므로 토큰 바이어스를 특히 경계한다.")
    if dominant_ratio >= 0.8 and row["max_suggested_score"] == row["min_suggested_score"]:
        hints.append("동일 점수 반복 제안이 많아 휴리스틱 신호가 약하다. 제안 전략을 그대로 채택하지 않는다.")
    if bucket_label == "인프라·제도":
        hints.append("규제·펀드·조직·제도 개선은 일반적으로 `no_strategy`이고, 특정 분야 지원 대상이 분명할 때만 전략을 준다.")
    if bucket_label == "인재":
        hints.append("인재 항목은 특정 분야 연구자·전문인력 양성이 직접 명시될 때만 전략을 준다.")
    if batch_id.startswith("POL-010-기술"):
        hints.append("`POL-010` 기술 배치는 `전략기술` 일반어 때문에 `STR-002`로 쏠리기 쉬우므로 보수적으로 본다.")
    if batch_id.startswith("POL-007-기술"):
        hints.append("`POL-007` 기술 배치는 기초연구 일반 지원과 AI 대상 정책을 구분해야 한다.")
    if batch_id.startswith("POL-012-"):
        hints.append("`POL-012`는 개별 프로젝트 직접성이 높아 구체 산업·기술명이 보이면 적극적으로 전략을 매긴다.")
    return hints or ["일반 원칙을 적용한다."]


def build_brief(row: dict[str, str], batch_rows: list[dict[str, str]]) -> str:
    pending_count = sum(1 for batch_row in batch_rows if (batch_row.get("decision_status") or "pending") == "pending")
    reviewed_count = sum(1 for batch_row in batch_rows if batch_row.get("decision_status") == "reviewed")
    no_strategy_count = sum(1 for batch_row in batch_rows if batch_row.get("decision_status") == "no_strategy")
    deferred_count = sum(1 for batch_row in batch_rows if batch_row.get("decision_status") == "deferred")
    auto_seed_blocked_count = sum(
        1 for batch_row in batch_rows if (batch_row.get("auto_seed_blocked") or "").strip().lower() == "yes"
    )

    hints = review_hints(row)
    if auto_seed_blocked_count:
        hints.append("alignment exception이 있는 전략 제안은 reviewed로 자동 확정하지 않고 수동 확인한다.")

    lines = [
        f"# {row['batch_id']}",
        "",
        f"- 정책: `{row['policy_id']}` {row['policy_name']}",
        f"- 부문: `{row['bucket_label']}`",
        f"- 항목 수: `{row['item_count']}`",
        f"- 자동 제안 있음: `{row['with_suggestion_count']}`",
        f"- 자동 제안 없음: `{row['without_suggestion_count']}`",
        f"- auto-seed blocked: `{auto_seed_blocked_count}`",
        f"- 현재 상태: `pending {pending_count}`, `reviewed {reviewed_count}`, `no_strategy {no_strategy_count}`, `deferred {deferred_count}`",
        "",
        "## 검토 힌트",
        "",
        *[f"- {hint}" for hint in hints],
        "",
        "## 상위 자동 제안 전략",
        "",
        *top_strategy_lines(batch_rows),
        "",
        "## 상위 기술분야 태그",
        "",
        *top_tech_lines(batch_rows),
        "",
        "## 제안이 있는 샘플 항목",
        "",
        *sample_lines(batch_rows, with_suggestion=True),
        "",
        "## 제안이 없는 샘플 항목",
        "",
        *sample_lines(batch_rows, with_suggestion=False),
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-index-csv", required=True)
    parser.add_argument("--batches-dir", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--out-index-md", required=True)
    args = parser.parse_args()

    index_rows = read_csv(Path(args.batch_index_csv))
    batches_dir = Path(args.batches_dir)
    out_dir = Path(args.out_dir)
    keep_names: set[str] = set()

    index_lines = [
        "# 전략 검토 배치 브리프",
        "",
        "자동 생성된 배치별 검토 메모이다.",
        "",
    ]

    for row in index_rows:
        batch_rows = read_csv(batches_dir / row["output_csv"])
        brief_path = out_dir / f"{row['batch_id']}.md"
        keep_names.add(brief_path.name)
        write_text(brief_path, build_brief(row, batch_rows))
        index_lines.extend(
            [
                f"## {row['batch_id']}",
                "",
                f"- 정책: `{row['policy_id']}` {row['policy_name']}",
                f"- 부문: `{row['bucket_label']}`",
                f"- 항목 수: `{row['item_count']}` / 자동 제안 있음 `{row['with_suggestion_count']}` / 없음 `{row['without_suggestion_count']}`",
                f"- 브리프: `{brief_path.name}`",
                "",
            ]
        )

    cleanup_stale_files(out_dir, keep_names, ["*.md"])
    write_text(Path(args.out_index_md), "\n".join(index_lines))
    print(f"Strategy review briefs: {len(index_rows)}")


if __name__ == "__main__":
    main()
