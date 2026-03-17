# DOC-POL-006 Workbench Starter Seed

## Summary

- sample reviewed workbench `11`건을 실 workbench `DOC-POL-006__policy-item-review-workbench.csv`에 이식했다.
- merge candidate id와 `item_label_draft`, `item_statement_draft`, `primary_text`가 모두 일치하는 row만 반영했다.
- 반영 후 reviewed export batch 기준 `DOC-POL-006`은 `completed`, `reviewed_item_count=6`, `issue_count=0`이다.

## Seed Source

- sample input:
  - `work/04_ontology/sample_build/review_workbench_samples/DOC-POL-006__policy-item-review-workbench-sample-reviewed.csv`
- real target:
  - `work/04_ontology/review_workbenches/DOC-POL-006__policy-item-review-workbench.csv`
- seed summary:
  - `qa/ontology/2026-03-16_doc-pol-006-workbench-seed-summary.json`

## Seeded Decisions

- `drop`: 3
- `keep`: 3
- `attach_as_case_example`: 2
- `keep_as_regulatory_delta`: 3

## Reviewed Export

- batch summary:
  - `work/04_ontology/reviewed_items/batch_runs/2026-03-16_phase1-reviewed-policy-item-export-batch.json`
- document summary:
  - `work/04_ontology/reviewed_items/DOC-POL-006__reviewed-items-summary.json`
- generated outputs:
  - `work/04_ontology/reviewed_items/DOC-POL-006__policy-items-reviewed.csv`
  - `work/04_ontology/reviewed_items/DOC-POL-006__display-texts-reviewed.csv`
  - `work/04_ontology/reviewed_items/DOC-POL-006__policy-item-evidence-links-reviewed.csv`
  - `work/04_ontology/reviewed_items/DOC-POL-006__policy-item-taxonomy-map-reviewed.csv`
  - `work/04_ontology/reviewed_items/DOC-POL-006__derived-to-display-map-reviewed.csv`

## Result

- reviewed source row: `11`
- reviewed item: `6`
- display text: `6`
- evidence link: `10`
- taxonomy row: `4`
- ignored reviewed row: `5`
- unresolved merge: `0`
- issue count: `0`

## Next

- `DOC-POL-005`, `DOC-POL-010`은 아직 `skipped_unreviewed_workbench` 상태다.
- 다음 실제 작업은 두 문서 중 하나에 대해 reviewer starter set을 만들거나, 사람이 직접 workbench를 채운 뒤 같은 export 경로로 넘기는 것이다.
