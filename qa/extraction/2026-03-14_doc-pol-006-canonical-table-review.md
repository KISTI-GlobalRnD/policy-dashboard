# DOC-POL-006 Canonical Table Review

## 대상

- 문서 ID: `DOC-POL-006`
- reviewed queue: `qa/extraction/reviewed_queues/DOC-POL-006__table-review-reviewed.csv`
- canonical tables: `work/04_ontology/instances/DOC-POL-006__canonical-tables.csv`

## 결과 요약

- review item 수: 30
- reviewed: 30
- dashboard 즉시 사용 가능 후보: 10 review items
- dashboard 제외: 10 review items
- 후속 병합 필요: 6 review items
- canonical table 수: 7

canonical status:

- `ready`: 5
- `needs_normalization`: 1
- `needs_merge`: 1

## ready canonical table

- `CTBL-DOC-POL-006-001`: 선정기준 비교표
- `CTBL-DOC-POL-006-002`: 고온초전도자석 유형별 응용분야
- `CTBL-DOC-POL-006-003`: 바이오 의약 산업 현황 및 목표
- `CTBL-DOC-POL-006-004`: K-디지털헬스케어 주요 기업 사례
- `CTBL-DOC-POL-006-005`: ICT 기반 의료시스템 유형

## 후속 작업 필요 canonical table

- `CTBL-DOC-POL-006-006`
  - 상태: `needs_normalization`
  - 이유: 연도와 수치 셀이 분절되어 있음

- `CTBL-DOC-POL-006-007`
  - 상태: `needs_merge`
  - 이유: 페이지 36~38 일정표가 다중 페이지 조각으로 분리됨

## 대시보드 제외 판단

다음은 표가 아니라 레이아웃/도식 또는 false positive로 판단했다.

- 페이지 2, 3: 제목 박스
- 페이지 9: 조직 체계도
- 페이지 10: 문장 파편
- 페이지 13, 24: 제목 조각
- 페이지 15, 21: 단어 조각

## repair_required

- 페이지 26 `TBL-DOC-POL-006-016`, `TBL-DOC-POL-006-017`
  - 의료기기 전주기 시장진출 프로세스 비교표의 조각으로 보이지만 현재 추출 결과만으로는 canonical table 확정이 어려움
  - 별도 복원 경로가 필요

## 판단

현재 기준으로 `DOC-POL-006`은 표를 자동 추출 결과 그대로 쓰지 않고도 운영 가능한 상태다.
즉시 쓸 수 있는 canonical table 5개와 보류해야 할 표 2개가 명확히 분리됐다.
