# DOC-POL-005 Workbench Starter Seed

## Summary

- 수동 starter decision manifest `24`건을 실 workbench `DOC-POL-005__policy-item-review-workbench.csv`에 반영했다.
- `merge_candidate_id`와 `candidate_role_draft`, `item_label_draft`, `item_statement_draft`, `primary_text`가 모두 일치하는 row만 적용했다.
- 반영 후 reviewed export batch 기준 `DOC-POL-005`는 `completed`, `reviewed_item_count=9`, `issue_count=0`이다.

## Seed Source

- decision manifest:
  - `qa/ontology/review_workbench_seeds/DOC-POL-005__starter-decisions.csv`
- apply script:
  - `scripts/apply_manual_review_workbench_decisions.py`
- real target:
  - `work/04_ontology/review_workbenches/DOC-POL-005__policy-item-review-workbench.csv`
- seed summary:
  - `qa/ontology/2026-03-16_doc-pol-005-workbench-seed-summary.json`

## Seeded Decisions

- `drop`: 5
- `attach_as_background`: 10
- `keep`: 9

## Review Scope

- `drop`는 의결 문구, 대목 제목, 소제목 같은 meta frame에만 적용했다.
- `attach_as_background`는 추진 경과, 문제 인식, 배경 설명 row에만 적용했다.
- `keep`는 `☞ 개선방향` 또는 핵심 축 문장처럼 실제 action으로 읽히는 row만 남겼다.
- `keep` row 중 bucket guess가 비거나 technology 쪽으로 쏠리던 항목은 `infrastructure_institutional` 또는 `talent`로 수동 override했다.

## Reviewed Export

- batch summary:
  - `work/04_ontology/reviewed_items/batch_runs/2026-03-16_phase1-reviewed-policy-item-export-batch.json`
- document summary:
  - `work/04_ontology/reviewed_items/DOC-POL-005__reviewed-items-summary.json`
- generated outputs:
  - `work/04_ontology/reviewed_items/DOC-POL-005__policy-items-reviewed.csv`
  - `work/04_ontology/reviewed_items/DOC-POL-005__display-texts-reviewed.csv`
  - `work/04_ontology/reviewed_items/DOC-POL-005__policy-item-evidence-links-reviewed.csv`
  - `work/04_ontology/reviewed_items/DOC-POL-005__policy-item-taxonomy-map-reviewed.csv`
  - `work/04_ontology/reviewed_items/DOC-POL-005__derived-to-display-map-reviewed.csv`

## Result

- reviewed source row: `24`
- reviewed item: `9`
- display text: `9`
- evidence link: `9`
- taxonomy row: `0`
- ignored reviewed row: `15`
- unresolved merge: `0`
- issue count: `0`

## Next

- `DOC-POL-010`은 아직 `skipped_unreviewed_workbench` 상태다.
- 다음 실제 작업은 `DOC-POL-010`에 대해 같은 방식의 starter seed를 만들거나 사람이 직접 reviewed row를 채우는 것이다.
