# Policy Item Review Workbench

`policy-item-review-workbench`는 merge draft를 사람이 검토해 ontology 적재용 policy item으로 확정하기 위한 작업지다.

## 입력

- `work/04_ontology/merge_drafts/{document_id}__policy-item-merge-draft.csv`

## 주요 컬럼

- `review_priority`
  - `high`: meta, background, problem, case example 등 우선 검토 대상
  - `medium`: 유지 가능성이 높지만 merge/support/taxonomy 공백 때문에 확인 필요
  - `low`: 상대적으로 그대로 유지 가능
- `suggested_reviewer_action`
  - `keep_or_merge`
  - `drop_or_attach_background`
  - `recast_or_attach_background`
  - `attach_as_background`
  - `attach_as_case_example`
  - `keep_as_regulatory_delta`
- `reviewer_decision`
  - reviewer가 실제로 입력하는 값
- `reviewer_role_override`
  - `policy_action`
  - `problem_or_requirement`
  - `background_context`
  - `case_example`
  - `regulatory_delta`
  - `meta_program_frame`
- `merge_into_candidate_id`
  - `merge` 결정일 때 대상 merge candidate id
- `final_item_label`
- `final_item_statement`

## 권장 reviewer_decision 값

- `keep`
- `keep_or_merge`
- `recast_keep`
- `keep_as_regulatory_delta`
- `merge`
- `drop`
- `attach_as_background`
- `attach_as_case_example`
- `recast_or_attach_background`

## 현재 converter 해석 규칙

- `keep`, `keep_or_merge`, `recast_keep`, `keep_as_regulatory_delta`:
  - policy item 생성
- `merge`:
  - `merge_into_candidate_id`로 지정된 target policy item에 evidence를 병합
- `drop`, `attach_as_background`, `attach_as_case_example`:
  - policy item 생성 안 함
- `recast_or_attach_background`:
  - `final_item_label` 또는 `final_item_statement`가 있으면 생성
  - 없으면 생성 안 함

## 출력

converter는 아래 파일을 생성한다.

- `policy-items-reviewed.csv`
- `display-texts-reviewed.csv`
- `policy-item-evidence-links-reviewed.csv`
- `policy-item-taxonomy-map-reviewed.csv`
- `derived-to-display-map-reviewed.csv`
- `reviewed-items-summary.json`
