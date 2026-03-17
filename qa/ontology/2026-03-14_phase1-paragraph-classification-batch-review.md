# Phase1 Paragraph Classification Batch Review

## 대상

- 입력 배치: `work/03_processing/normalized/batch_runs/2026-03-14_phase1-policy-normalization-batch.json`
- 출력 배치:
  - `work/04_ontology/instances/batch_runs/2026-03-14_phase1-paragraph-classification-batch.json`
  - `work/04_ontology/instances/batch_runs/2026-03-14_phase1-paragraph-classification-batch.csv`

## 결과 요약

- 완료 문서: 11
- 실패 문서: 0
- 총 문단 수: 2,556
- `policy_item_candidate = yes`: 1,512
- `policy_item_candidate = review`: 747
- `policy_item_candidate = no`: 297
- 자원유형 자동 제안 수: 1,085
- 전략 자동 제안 수: 1,013
- 기술분야 자동 제안 수: 968
- 기술 중분류 자동 제안 수: 908

## 문서별 관찰

- `DOC-POL-002`, `004`, `007`, `011`, `012`는 문서 제목과 키워드 사전이 잘 맞아 전략/기술분야 제안률이 높다.
- `DOC-POL-006`은 종합계획 문서라 문단별 키워드 편차가 커서 전략·기술분야 제안률이 상대적으로 낮다.
- `DOC-POL-005`, `008`, `009`, `010`은 연구생태계·제도 성격이 강해 전략/기술분야 자동 제안이 제한적이다.
- `note`, `caption`, `table_markdown`은 검토 큐로 남겨 표/그림과 본문 문단을 섞지 않도록 했다.

## 확인 사항

- cover title, 요약 title, heading, 일부 scaffold 문구는 `no`로 자동 하향됐다.
- 문서 제목 prior를 사용하므로 특정 문서에서는 전략/기술분야 제안이 넓게 붙는다.
- 현재 제안값은 검토용 seed이며, 자동 확정값으로 사용하면 안 된다.
- 특히 종합계획 문서의 `yes` 집합은 넓게 잡힌 작업지이므로, policy item 병합 전에 그대로 쓰면 false positive가 남는다.
- `auto_suggestion_notes`에 점수와 필터 근거가 남아 후속 spot check에 쓸 수 있다.

## 남은 이슈

- `개발`, `혁신`, `전략`처럼 일반성이 높은 표현은 자원유형 또는 전략 제안을 과대하게 만들 수 있다.
- 종합계획 문서의 문단은 policy item 단위 병합 없이는 전략 제안이 잘게 쪼개질 수 있다.
- 기술분야와 무관한 제도 문단은 `review_required`로 남는 비율이 높다.

## 판단

phase1 문단 분류 템플릿은 이제 수동 검토 큐로 넘길 수 있는 수준이다.
다음 단계는 `policy_item 후보 병합 규칙`과 `짧은 scaffold/noise 제거 규칙`을 더 붙이는 것이다.
