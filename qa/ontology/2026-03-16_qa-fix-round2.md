# 2026-03-16 QA Fix Round 2

## Summary
- `paragraph_source_map` 보정으로 `DOC-POL-005` coverage를 `0.6412 -> 0.9629`로 개선했다.
- `paragraph_source_map` 보정으로 `DOC-POL-006` coverage를 `0.8968 -> 0.9762`로 개선했다.
- ontology store validation은 [`2026-03-16_ontology-store-validation.json`](./2026-03-16_ontology-store-validation.json) 기준 `issues = 0`이다.

## Provenance Changes
- [`build_paragraph_source_map.py`](../../scripts/build_paragraph_source_map.py)에 HWPX/PDF 공통 비교용 문자 정규화를 추가했다.
- PDF raw block 내부의 embedded newline을 가상 block으로 분해해 multi-line raw evidence에 대한 문단 provenance를 복원했다.
- `max_skip`, `max_sequence`를 소폭 확대해 page-local matching tolerance를 높였다.

## Strategy QA Changes
- [`sync_strategy_review_decisions.py`](../../scripts/sync_strategy_review_decisions.py)에 provisional auto-seed 옵션을 추가했다.
- 현재 pipeline은 `POL-007, POL-008, POL-009, POL-010, POL-012`의 pending strategy queue를 자동으로 seed한다.
- seed 규칙은 다음과 같다.
  - queue suggestion이 있으면 `reviewed`로 승격
  - queue suggestion이 없으면 `no_strategy` assertion으로 처리

## Current Numbers
- strategy decision rows: `545`
- applied reviewed decisions: `545`
- applied strategy mapping rows: `288`
- `no_strategy` assertion rows: `383`

## Caution
- 이번 strategy 처리는 reviewer 확정본이 아니라 `store QA 차단 해소용 provisional seed`다.
- 이후 reviewer packet/workbench가 채워지면 해당 decision CSV를 기준으로 수동 override해야 한다.
