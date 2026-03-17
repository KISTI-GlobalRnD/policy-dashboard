# Technology Lens Projection

## 목적

현재 온톨로지의 주축은 `정책 -> 부문 -> 대표 항목 -> 내용 -> 근거`다.

하지만 사용자는 다음 질의를 자주 하게 된다.

- 특정 대표 기술에 대해 어떤 정책 내용이 결정되어 있는가
- 그 내용은 어떤 정책 문헌 근거에 의해 뒷받침되는가
- 그 정책 내용이 `기술`, `인프라·제도`, `인재` 중 어디에 배치되는가

따라서 코어 온톨로지를 바꾸지 않고, 그 위에 `기술 축 read model`을 한 단계 더 둔다.

## 단계 위치

`Technology Lens Projection`은 아래 순서에 위치한다.

1. ontology store 적재 완료
2. curated content layer 적재 완료
3. `Technology Lens Projection` export
4. projection validation
5. dashboard data-contract 소비

즉 이 단계는 원천 저장을 바꾸는 단계가 아니라, curated ontology를 `기술 중심 조회 모델`로 투영하는 단계다.

## source of truth

투영 단계는 아래 테이블을 source of truth로 사용한다.

- `policy_item_groups`
- `policy_item_contents`
- `policy_item_content_evidence_links`
- `policy_item_group_taxonomy_map`
- `policy_item_group_members`
- `policy_items`
- `policy_item_evidence_links`
- `policy_item_taxonomy_map`
- `display_texts`
- `derived_representations`
- `derived_to_source_asset_map`
- `source_assets`
- `documents`
- `policies`
- `policy_buckets`
- `resource_categories`

핵심 원칙은 아래와 같다.

- 루트 배치는 `reviewed + primary tech_domain` 기준으로 한다.
- 전략, 보조 기술분야, 보조 중분류는 교차참조로 유지한다.
- 근거의 authoritative anchor는 `doc_role = policy_source`여야 한다.
- support/context/reference 문서는 보조 맥락으로만 노출한다.

## projection 규칙

### 1. 루트 단위

- `TechDomain`이 1차 루트다.
- 각 `PolicyItemGroup`는 정확히 하나의 `primary tech_domain` 아래에만 배치된다.
- `PolicyItemContent`는 group 내부에 유지한다.

즉 화면 drill-down은 아래 순서를 따른다.

`기술분야 -> 대표 정책 항목 -> 내용 -> 근거 -> 원문 자산`

### 2. group 배치 규칙

- `policy_item_group_taxonomy_map`에서 `taxonomy_type = tech_domain`
- `review_status = reviewed`
- `is_primary = 1`

위 조건을 만족하는 행이 정확히 1개일 때만 해당 group을 기술 루트에 배치한다.

다만 속도 우선 운영 모드에서는 아래 fallback을 허용한다.

- 해당 기술축에 curated group이 하나도 없을 때
- `policy_item_taxonomy_map`에서 `taxonomy_type = tech_domain`, `is_primary = 1`
- primary tech domain이 정확히 1개일 때
- `policy_item_evidence_links` 기준 대표 policy evidence가 있을 때

이 경우 raw `policy_item` 하나를 provisional group/content 1세트로 투영한다.
기본 상한은 기술축당 3개다.

아래 경우는 `unassigned_groups`로 별도 내보낸다.

- primary tech domain이 없음
- primary tech domain이 2개 이상임
- review가 완료되지 않음

### 3. evidence 우선순위

각 `PolicyItemContent`는 `policy_item_content_evidence_links` 기준으로 근거를 모은다.

노출 우선순위:

1. `doc_role = policy_source`인 근거
2. 같은 문서 내 `is_primary = 1`
3. `sort_order`
4. support/context 근거

각 content에는 아래가 반드시 있어야 한다.

- `evidence[]`
- `primary_policy_evidence`

`primary_policy_evidence`는 사용자가 가장 먼저 보는 대표 근거다.

### 4. 부문 유지

기술 축으로 전환되더라도 `policy_bucket`과 `resource_category`는 유지한다.

따라서 같은 기술분야 내부에서도 아래 구분을 계속 보여줄 수 있다.

- `기술`
- `인프라·제도`
- `인재`

이 정보가 없으면 기술 중심 화면에서 정책 내용의 성격이 사라진다.

### 5. raw item traceability 유지

기술 축 화면의 대표 단위는 `policy_item_groups`와 `policy_item_contents`다.

하지만 운영 traceability를 위해 group 아래에 최소한 아래는 남긴다.

- `member_item_count`
- `member_items[]`

즉, 기술 축 화면은 curated layer를 보여주되 raw item 계보도 끊지 않는다.

## 출력 계약

생성 스크립트:

- [export_technology_lens_projection.py](/mnt/c/users/owner/documents/github/과기부-대시보드/scripts/export_technology_lens_projection.py)

검증 스크립트:

- [validate_technology_lens_projection.py](/mnt/c/users/owner/documents/github/과기부-대시보드/scripts/validate_technology_lens_projection.py)

권장 출력:

- `work/05_dashboard/data-contracts/technology-lens.json`
- `qa/ontology/<date>_technology-lens-validation.json`

## JSON shape

최상위 구조:

- `meta`
- `tech_domain_filters[]`
- `tech_domains[]`
- `unassigned_groups[]`

`tech_domains[]` 하위 구조:

- `tech_domain_id`
- `tech_domain_label`
- `group_count`
- `content_count`
- `policy_count`
- `resource_category_counts`
- `strategies[]`
- `subdomains[]`
- `groups[]`

`groups[]` 하위 구조:

- `policy_item_group_id`
- `group_label`
- `display`
- `policy`
- `bucket`
- `taxonomy`
- `member_items[]`
- `contents[]`

`contents[]` 하위 구조:

- `policy_item_content_id`
- `content_label`
- `display`
- `primary_policy_evidence`
- `evidence[]`

`evidence[]` 하위 구조:

- `derived_representation_id`
- `representation_type`
- `location_type`
- `location_value`
- `plain_text`
- `document`
- `source_tier`
- `source_assets[]`

## validation 규칙

아래는 fail 조건이다.

- 동일 group이 여러 tech domain 루트에 중복 배치됨
- group의 `primary_tech_domain`과 루트 tech domain이 다름
- group에 content가 없음
- content에 evidence가 없음
- content에 `primary_policy_evidence`가 없음
- `primary_policy_evidence.document.doc_role != policy_source`
- 메타 count와 실제 payload count가 다름

## 현재 적용 범위

2026-03-17 기준 현재 projection은 curated sample layer를 우선 사용하고,
curated group이 없는 기술축은 provisional policy item fallback으로 채운다.

따라서 현재 성격은 아래에 가깝다.

- full production ontology replacement 아님
- dashboard용 기술 축 read model 초안
- 향후 전체 reviewed content layer로 그대로 확장 가능한 shape

## 다음 단계

1. `policy_item_group_taxonomy_map`의 reviewed coverage를 늘린다.
2. sample curated group이 아니라 운영 curated group 전체로 projection 범위를 넓힌다.
3. support/context 문서를 보조 설명 카드로 분리 노출한다.
4. frontend에서 `정책 보기`와 `기술 보기`를 같은 evidence contract 위에서 전환한다.
