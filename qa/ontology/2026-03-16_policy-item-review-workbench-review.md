# Policy Item Review Workbench Review

## 대상

- `work/04_ontology/review_workbenches/DOC-POL-005__policy-item-review-workbench.csv`
- `work/04_ontology/review_workbenches/DOC-POL-006__policy-item-review-workbench.csv`
- `work/04_ontology/review_workbenches/DOC-POL-010__policy-item-review-workbench.csv`

## 목적

merge draft를 사람이 바로 검토할 수 있는 작업지로 전환했는지 확인한다.

## 생성 기준

- `candidate_role_draft`
- `merge_confidence`
- taxonomy 후보 유무
- continuation / support review 부착 여부

위 네 가지를 기준으로 `review_priority`와 `suggested_reviewer_action`을 자동 제안한다.

## 문서별 요약

- `DOC-POL-005`
  - 후보 222건
  - `high`: 24 / `medium`: 196 / `low`: 2
  - `drop_or_attach_background`: 5
  - `attach_as_background`: 8
  - `recast_or_attach_background`: 11
- `DOC-POL-006`
  - 후보 137건
  - `high`: 11 / `medium`: 107 / `low`: 19
  - `drop_or_attach_background`: 9
  - `attach_as_case_example`: 2
  - `keep_as_regulatory_delta`: 3
- `DOC-POL-010`
  - 후보 86건
  - `high`: 14 / `medium`: 67 / `low`: 5
  - `attach_as_background`: 5
  - `recast_or_attach_background`: 8

## 잘 된 점

- `meta_program_frame`, `background_context`, `problem_or_requirement`, `case_example`가 workbench에서 우선 검토 대상으로 바로 올라온다.
- `DOC-POL-006`의 기업 인용 2건은 `attach_as_case_example`로 분기되어, 일반 정책항목과 섞이지 않는다.
- `regulatory_delta`는 `keep_as_regulatory_delta`로 별도 검토할 수 있게 됐다.

## 남은 이슈

- `DOC-POL-005`와 `DOC-POL-010`은 여전히 `medium`이 많다. 이건 오류라기보다 action 후보가 넓게 남아 있다는 뜻이다.
- `review_priority`는 현재 작업 순서를 정하는 용도이지, ontology 적재 가능 여부의 최종 판정은 아니다.
- `build_reviewed_policy_items_from_workbench.py`와 `run_phase1_reviewed_policy_item_export_batch.py`를 붙여 workbench -> reviewed ontology CSV 경로는 준비됐다.
- `DOC-POL-006`에는 sample-reviewed starter set `11`건을 반영했고, batch export 기준 `completed / reviewed_item_count=6 / issue_count=0`까지 확인했다.
- `DOC-POL-005`에는 수동 starter decision manifest `24`건을 반영했고, batch export 기준 `completed / reviewed_item_count=9 / issue_count=0`까지 확인했다.
- `DOC-POL-010`에도 수동 starter decision manifest `29`건을 반영했고, batch export 기준 `completed / reviewed_item_count=17 / issue_count=0`까지 확인했다.
- `load_reviewed_policy_items.py`를 추가해 reviewed ontology CSV를 `ontology.sqlite`에 다시 적재하도록 연결했고, `2026-03-16` 기준 phase1 reviewed item load와 전체 pipeline validation까지 `pass`를 확인했다.
- 따라서 phase1 workbench -> reviewed ontology CSV 경로의 현재 병목은 reviewer 입력이 아니라 reviewed item 이후 strategy alignment 운영이다.
