# Reviewed Item Export Sample Review

## 대상

- 입력 sample:
  - `work/04_ontology/sample_build/review_workbench_samples/DOC-POL-006__policy-item-review-workbench-sample-reviewed.csv`
- 출력 sample:
  - `work/04_ontology/sample_build/reviewed_items_sample/DOC-POL-006__policy-items-reviewed.csv`
  - `work/04_ontology/sample_build/reviewed_items_sample/DOC-POL-006__display-texts-reviewed.csv`
  - `work/04_ontology/sample_build/reviewed_items_sample/DOC-POL-006__policy-item-evidence-links-reviewed.csv`
  - `work/04_ontology/sample_build/reviewed_items_sample/DOC-POL-006__policy-item-taxonomy-map-reviewed.csv`
  - `work/04_ontology/sample_build/reviewed_items_sample/DOC-POL-006__derived-to-display-map-reviewed.csv`

## 결과 요약

- reviewed source row: 11
- reviewed item: 6
- display text: 6
- evidence link: 10
- taxonomy row: 4
- ignored reviewed row: 5
- unresolved merge: 0

## 확인 사항

- `초전도체`, `K-바이오 글로벌 상업화`, `K-디지털헬스케어`가 reviewed policy item으로 정상 생성된다.
- `현재 → 개선`, `본인인증의무 폐지`, `뮤직비디오 심의 개선`은 `regulatory_delta` item으로 생성된다.
- `디지털헬스기업B/C`는 `attach_as_case_example` 결정이므로 reviewed policy item으로는 생성되지 않는다.
- evidence link는 `classification seed -> paragraph -> derived_representation` 경로로 정상 복원된다.

## 판단

sample 수준에서는 workbench -> reviewed ontology CSV 변환 경로가 정상 동작한다.
현재 converter summary는 `run_status`, `reviewed_source_row_count`, `reviewed_decision_counts`, `issue_count`까지 기록한다.
다만 실제 phase1 적용 전에는 reviewer가 채운 실 workbench 1건에 대해 한 번 더 검증하는 것이 필요하다.
