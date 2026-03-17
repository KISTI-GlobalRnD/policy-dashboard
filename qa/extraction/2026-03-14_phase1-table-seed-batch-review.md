# Phase1 Table Seed Batch Review

## 대상

- phase1 정책 문서 11건

## 입력

- `qa/extraction/review_queues/batch_runs/2026-03-14_phase1-table-review-queue-batch.json`
- `qa/extraction/reviewed_queues/batch_runs/2026-03-14_phase1-table-seed-batch.json`

## 결과 요약

- 전체 1차 reviewed: `568`
- 전체 review_required 잔여: `73`
- `keep_for_dashboard = yes`: `71`
- `keep_for_dashboard = no`: `497`
- 생성된 canonical seed: `71`
- `DOC-POL-006`은 기존 수동 review가 있어 heuristic seed 대상에서 제외

## 추가 수동 검토 반영 후 현재 상태

- 전체 reviewed: `671`
- 전체 review_required 잔여: `0`
- `keep_for_dashboard = yes`: `105`
- `keep_for_dashboard = after_merge`: `6`
- `keep_for_dashboard = no`: `556`
- canonical table: `100`
- phase1 정책 문서 11건의 `review_required`는 모두 해소

## 핵심 판단

- phase1 표 후보의 대부분은 실제 데이터 표가 아니라 layout box다.
- 특히 HWPX 문서는 제목, 비전, front matter, 전략 박스를 표 도구로 만든 사례가 많다.
- heuristic seed 이후에는 review 대상이 크게 줄었고, 현재 phase1에서는 `review_required`가 더 이상 남지 않는다.

## 문서별 메모

- `DOC-POL-005`
  - 후보 `83`
  - seed reviewed `77`
  - 잔여 review_required `6`
  - canonical seed `16`

- `DOC-POL-006`
  - 기존 reviewed queue 유지
  - canonical table `7`
  - ready `5`, needs_normalization `1`, needs_merge `1`

- `DOC-POL-007`
  - 후보 `108`
  - reviewed `108`
  - 잔여 review_required `0`
  - canonical table `14`
  - 투자지원 카드 박스·연락처 박스는 제외했고, SWOT/지원유형/금융유형/인력양성 표는 구조표로 확정
  - 동일한 일정표가 요약/본문에 중복 등장하는 사례가 있어 후속 dedupe 검토 필요

- `DOC-POL-009`
  - 후보 `94`
  - reviewed `94`
  - 잔여 review_required `0`
  - canonical table `15`
  - `불만족 사유 | 비중` 표를 추가 구조표로 확정

- `DOC-POL-002`
  - 후보 `94`
  - reviewed `94`
  - 잔여 review_required `0`
  - canonical table `15`
  - 시범거점 확대 일정, 참여주체 인센티브, 뇌 지도 비교, As-Is/To-Be 전환표를 추가 구조표로 확정

- `DOC-POL-003`
  - 후보 `41`
  - reviewed `41`
  - 잔여 review_required `0`
  - canonical table `4`
  - 3대 전략 요약표와 유형별 프로젝트 예시 표를 추가 구조표로 확정

- `DOC-POL-004`
  - 후보 `54`
  - reviewed `54`
  - 잔여 review_required `0`
  - canonical table `4`
  - 남은 3x2/3x3 박스는 모두 설명/연락처 박스로 정리

- `DOC-POL-005`
  - 후보 `83`
  - reviewed `83`
  - 잔여 review_required `0`
  - canonical table `20`
  - `PBS 폐지/우수연구자 확보`, `투자시스템/대형R&D`, `평가 보상체계`, `공동활용 역할 분담` 표를 추가 구조표로 확정

- `DOC-POL-008`
  - 후보 `28`
  - reviewed `28`
  - 잔여 review_required `0`
  - canonical table `5`
  - `팁스 지역별 운영사 현황` 표를 추가 구조표로 확정

- `DOC-POL-010`
  - 후보 `76`
  - reviewed `76`
  - 잔여 review_required `0`
  - canonical table `9`
  - 연구주제 기획 절차, 평가 환류, 성과급 비교, 정년 후 연구 제도를 추가 구조표로 확정

- `DOC-POL-011`
  - 후보 `19`
  - reviewed `19`
  - 잔여 review_required `0`
  - canonical table `3`
  - 남은 후보는 모두 제목/연락처 박스로 정리

- `DOC-POL-012`
  - 후보 `44`
  - reviewed `44`
  - 잔여 review_required `0`
  - canonical table `4`
  - `GPU / 데이터 / AI모델 / 인재 / 클라우드 / 평가·검증` 지원자원 표를 추가 구조표로 확정

## 남은 리스크

- summary section과 main body에 같은 표가 반복되는 중복 canonical 가능성
- 일부 canonical seed는 title_hint가 header preview 기반이라 후속 정제 필요

## 다음 우선순위

1. 동일 표의 summary/main body 중복 정리
2. `canonical_table` title_hint와 notes 정제
3. `DOC-POL-006`의 `needs_normalization`, `needs_merge` 표 후속 처리
4. visual table과 figure 내부 표의 예외 경로 정리
