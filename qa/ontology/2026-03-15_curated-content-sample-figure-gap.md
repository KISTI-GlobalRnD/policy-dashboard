# Curated Content Sample Figure Gap

## 상태

이 이슈는 `2026-03-16` figure 적재 파이프라인 반영으로 해소됐다.

## 이전 상태 요약

현재 curated content sample에는 `figure/diagram evidence`를 넣지 않았다.

이유는 샘플 pack 문제라기보다 현재 ontology store 적재 상태에서
`figure evidence -> derived representation -> source asset` 체인이 비어 있기 때문이다.

## 확인 결과

- `work/04_ontology/ontology.sqlite` 기준 `evidence_figures` row 수는 `0`
- 같은 DB 기준 `derived_representations`에서 `source_object_type='figure'` 또는 `representation_type`이 `figure/diagram` 계열인 row 수도 `0`
- 따라서 현재 sample pack에는 `normalized_paragraph`와 `canonical_table`만 안정적으로 넣을 수 있다

## 의미

- sample pack에서 figure가 빠진 것은 설계 누락이 아니다
- 현 단계에서는 `figure extraction` 결과가 일부 파일 시스템에 존재해도, ontology store까지 아직 연결되지 않았다는 뜻이다
- 따라서 대시보드/온톨로지 구현은 당분간 `paragraph + table` 경로를 기준으로 진행하고, figure는 후속 적재 파이프라인 작업으로 분리하는 것이 맞다

## 반영된 작업

1. `evidence_figures` 적재 스크립트 추가
2. `derived_representations`에 `figure_or_diagram` representation 생성
3. `derived_to_source_asset_map`에 figure asset direct mapping 반영
4. curated sample pack에 figure 예시 1건 추가
