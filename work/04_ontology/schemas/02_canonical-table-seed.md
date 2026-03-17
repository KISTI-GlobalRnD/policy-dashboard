# canonical table seed 스키마 v0.1

## 목적

문서별 표 후보를 검토한 뒤, 실제로 사용할 표만 `canonical_table` 단위로 확정하기 위한 스키마다.

## 입력

- `qa/extraction/review_queues/*__table-review-queue.csv`
- `qa/extraction/review_decisions/*__table-review-decisions.json`

## 출력

- `qa/extraction/reviewed_queues/*__table-review-reviewed.csv`
- `work/04_ontology/instances/*__canonical-tables.csv`
- `work/04_ontology/instances/*__canonical-tables.json`

## 주요 컬럼

- `canonical_table_id`
- `document_id`
- `title_hint`
- `page_start`
- `page_end`
- `preferred_candidate_source`
- `preferred_candidate_id`
- `canonical_status`
- `dashboard_ready`
- `source_review_item_ids`
- `notes`

## canonical_status 값

- `ready`
  - 구조가 충분히 안정적이며 참조 표로 바로 사용 가능
- `needs_normalization`
  - 표 구조는 맞지만 셀 값 정리가 더 필요
- `needs_merge`
  - 다중 페이지 또는 다중 조각 병합이 필요

## 규칙

- 같은 의미의 표가 여러 추출 경로에서 잡히면 하나의 `canonical_table_id`로 묶는다.
- `preferred_candidate_id`는 우선 참조 소스일 뿐이며, provenance는 `source_review_item_ids` 전체를 유지한다.
- `dashboard_ready = yes` 인 표만 대시보드에 바로 연결한다.
- `dashboard_ready = no` 인 표는 후속 정규화나 병합이 끝난 뒤 승격한다.
