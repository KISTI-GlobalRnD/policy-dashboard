# DOC-POL-010 Workbench Starter Seed

## Summary

- 수동 starter decision manifest `29`건을 실 workbench `DOC-POL-010__policy-item-review-workbench.csv`에 반영했다.
- `merge_candidate_id`와 `candidate_role_draft`, `item_label_draft`, `item_statement_draft`, `primary_text`가 모두 일치하는 row만 적용했다.
- 반영 후 reviewed export batch 기준 `DOC-POL-010`은 `completed`, `reviewed_item_count=17`, `issue_count=0`이다.

## Seed Source

- decision manifest:
  - `qa/ontology/review_workbench_seeds/DOC-POL-010__starter-decisions.csv`
- apply script:
  - `scripts/apply_manual_review_workbench_decisions.py`
- real target:
  - `work/04_ontology/review_workbenches/DOC-POL-010__policy-item-review-workbench.csv`
- seed summary:
  - `qa/ontology/2026-03-16_doc-pol-010-workbench-seed-summary.json`

## Seeded Decisions

- `attach_as_background`: 11
- `drop`: 1
- `keep`: 17

## Review Scope

- 상단 reform overview, 배경·문제 진단, outcome goal row는 `attach_as_background`로 정리했다.
- `전략3` 헤더 `1`건만 `drop` 처리했다.
- `keep`는 재정 체계, 평가·보상, 처우·채용, 연구행정, 법·거버넌스처럼 바로 ontology item으로 쓸 수 있는 실행조치만 남겼다.
- bucket guess가 비거나 모호한 keep row는 `infrastructure_institutional` 또는 `talent`로 수동 override했다.

## Reviewed Export

- batch summary:
  - `work/04_ontology/reviewed_items/batch_runs/2026-03-16_phase1-reviewed-policy-item-export-batch.json`
- document summary:
  - `work/04_ontology/reviewed_items/DOC-POL-010__reviewed-items-summary.json`
- generated outputs:
  - `work/04_ontology/reviewed_items/DOC-POL-010__policy-items-reviewed.csv`
  - `work/04_ontology/reviewed_items/DOC-POL-010__display-texts-reviewed.csv`
  - `work/04_ontology/reviewed_items/DOC-POL-010__policy-item-evidence-links-reviewed.csv`
  - `work/04_ontology/reviewed_items/DOC-POL-010__policy-item-taxonomy-map-reviewed.csv`
  - `work/04_ontology/reviewed_items/DOC-POL-010__derived-to-display-map-reviewed.csv`

## Result

- reviewed source row: `29`
- reviewed item: `17`
- display text: `17`
- evidence link: `31`
- taxonomy row: `0`
- ignored reviewed row: `12`
- unresolved merge: `0`
- issue count: `0`

## Next

- phase1 reviewed workbench 대상 `DOC-POL-005`, `DOC-POL-006`, `DOC-POL-010`은 모두 `completed` 상태다.
- 다음 실제 작업은 reviewed item CSV를 downstream ontology load에 연결하거나, 빈 taxonomy row를 채울 별도 alignment pass를 붙이는 것이다.
