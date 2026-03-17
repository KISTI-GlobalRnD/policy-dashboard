# 문단 분류 템플릿 스키마 v0.2

## 목적

정규화된 문단을 `PolicyItem`과 `Classification`으로 연결하기 전 단계의 작업용 템플릿이다.

## 입력

- `work/03_processing/normalized/*__paragraphs.json`

## 출력

- `work/04_ontology/instances/*__classification-template.csv`

## 주요 컬럼

- `classification_seed_id`
- `source_object_type`
- `source_object_id`
- `document_id`
- `page_no`
- `page_block_order`
- `block_type`
- `policy_item_candidate`
- `suggested_resource_type`
- `resource_type_keyword_hits`
- `resource_type_confidence`
- `primary_strategy_id`
- `primary_strategy_label`
- `secondary_strategy_ids`
- `strategy_confidence`
- `tech_domain_id`
- `tech_domain_label`
- `tech_subdomain_id`
- `tech_subdomain_label`
- `tech_domain_confidence`
- `review_status`
- `auto_suggestion_notes`
- `reviewer_notes`
- `text`

## 규칙

- `heading`은 기본적으로 `policy_item_candidate = no`
- `table_markdown`은 기본적으로 `policy_item_candidate = review`
- `note`, `caption`은 기본적으로 `policy_item_candidate = review`
- cover/title/front matter 성격 문단은 기본적으로 `policy_item_candidate = no`
- 일반 bullet, paragraph는 기본적으로 `policy_item_candidate = yes`
- `suggested_resource_type`는 키워드 기반 약한 제안값이다.
- 전략, 기술분야, 중분류는 키워드와 문서 제목 prior를 이용해 `제안`만 하고 자동 확정하지 않는다.
- `auto_suggestion_notes`에는 점수와 자동 필터링 근거를 남긴다.

## 사용 방식

1. 자동 생성 CSV를 연다.
2. `policy_item_candidate`를 1차 검토한다.
3. 대표 전략, 기술분야, 중분류의 자동 제안값을 검토·보정한다.
4. `review_status`를 `reviewed`로 바꾼다.
