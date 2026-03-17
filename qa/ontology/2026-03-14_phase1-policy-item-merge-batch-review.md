# Phase1 Policy Item Merge Batch Review

## 대상

- 입력:
  - `work/04_ontology/instances/batch_runs/2026-03-14_phase1-paragraph-classification-batch.json`
- 출력:
  - `work/04_ontology/merge_drafts/batch_runs/2026-03-14_phase1-policy-item-merge-batch.json`
  - `work/04_ontology/merge_drafts/batch_runs/2026-03-14_phase1-policy-item-merge-batch.csv`

## 결과 요약

- 완료 문서 수: 11
- 실패 문서 수: 0
- merge candidate 총계: 1,114
- merge primary 필터 제외 총계: 231

## 문서별 관찰

- `DOC-POL-005`: merge candidate 222건으로 가장 많다. support review 118건도 커서 실제 policy item 병합 규칙보다 `기초 분류 yes 폭`이 넓은 문서로 보인다.
- `DOC-POL-006`: 2차 필터를 적용했지만 여전히 meta bullet과 need-type bullet이 남는다. 현재 문서별 기준 문서 역할은 유지 가능하다.
- `DOC-POL-010`: skip rate가 15.1%로 가장 높다. 구조/배경 문단이 많아 merge 전에 `classification yes` 자체를 더 줄이는 편이 낫다.
- `DOC-POL-011`: skip rate가 13.8%로 높다. 분량은 작지만 배경/섹션 scaffold 비중이 높다.
- `DOC-POL-007`: continuation group 31건으로 가장 많다. paragraph split이 잦아서 merge rule이 실제로 유효하게 작동하는 문서다.
- `DOC-POL-002`, `DOC-POL-004`, `DOC-POL-011`, `DOC-POL-012`: strategy/tech_domain 후보가 merge candidate 수와 거의 같아 taxonomy 자동제안 밀도가 높다.
- `DOC-POL-005`, `DOC-POL-009`, `DOC-POL-010`: strategy 후보 수가 매우 낮아 taxonomy 자동제안 보강이 필요하다.

## 판단

현재 배치는 `phase1 전체 문서를 수동 큐레이션 가능한 merge draft`로 바꾸는 데는 성공했다.
다만 문서별 상태는 균일하지 않다.

- `DOC-POL-006`, `DOC-POL-010`, `DOC-POL-011`: classification 단계에서 scaffold/noise를 더 줄여야 한다.
- `DOC-POL-005`, `DOC-POL-009`: merge candidate 총량이 커서 merge 이후의 `item dedupe / grouping` 규칙이 필요하다.
- `DOC-POL-007`: continuation attachment 검토를 통해 split paragraph 병합 품질을 확인할 필요가 있다.

## 다음 우선순위

1. `DOC-POL-005`, `DOC-POL-006`, `DOC-POL-010` spot review
2. `need-type bullet`과 `현재/개선 비교형 bullet`의 ontology role 분기
3. merge draft를 기반으로 `policy item reviewed` 작업지 생성
