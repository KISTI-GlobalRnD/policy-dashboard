# Curated Content Sample Pack

## 목적

현재 raw `policy_items`만으로는 `대표 내용(content) - 근거(evidence)` 구조를 바로 보여주기 어렵다.

이 샘플 팩은 아래 목적을 위해 소규모 수동 큐레이션 예시를 제공한다.

- `PolicyItemGroup`와 `PolicyItemContent`가 실제로 어떻게 채워지는지 예시 제공
- raw item 여러 개가 하나의 대표 항목으로 묶이는 방식 예시 제공
- 대표 `내용`이 어떤 `derived_representation`을 근거로 연결하는지 예시 제공
- 대시보드 구현 시 nested JSON 참조본 제공
- `strict implementation contract`가 아니라 `manual sample reference`라는 범위를 명확히 제공

## 샘플 범위

샘플은 아래 3개 정책에서 골랐다.

- `POL-002 AI-바이오 국가전략`
- `POL-005 AI반도체 산업 도약 전략`
- `POL-011 정부 AX사업 전주기 원스톱 지원방안`

이 범위를 고른 이유는 다음과 같다.

- `기술`, `인프라·제도`, `인재` 3개 부문이 모두 포함된다.
- 데이터/규제/인재/실증/투자처럼 다른 유형의 `content_type`을 함께 보여줄 수 있다.
- 현재 raw item과 evidence link가 비교적 명확하다.

## 생성 파일

생성 스크립트:

- [build_curated_content_sample_pack.py](/mnt/c/users/owner/documents/github/과기부-대시보드/scripts/build_curated_content_sample_pack.py)

검증 스크립트:

- [validate_curated_content_sample_pack.py](/mnt/c/users/owner/documents/github/과기부-대시보드/scripts/validate_curated_content_sample_pack.py)

적재 스크립트:

- [load_curated_content_sample_pack.py](/mnt/c/users/owner/documents/github/과기부-대시보드/scripts/load_curated_content_sample_pack.py)

부트스트랩 스크립트:

- [bootstrap_curated_content_sample_layer.py](/mnt/c/users/owner/documents/github/과기부-대시보드/scripts/bootstrap_curated_content_sample_layer.py)

생성 대상 폴더 권장 경로:

- `work/04_ontology/instances/curated_content_sample/`

생성 대상 파일:

- `policy_item_groups_sample.csv`
- `policy_item_group_members_sample.csv`
- `policy_item_contents_sample.csv`
- `policy_item_content_evidence_links_sample.csv`
- `policy_item_group_taxonomy_map_sample.csv`
- `display_texts_curated_sample.csv`
- `curated_content_sample_pack.json`
- `curated_content_sample_summary.json`

## JSON 구조

`curated_content_sample_pack.json`은 아래 구조를 따른다.

- `sample_scope`
- `policies[]`
- `policies[].buckets[]`
- `policies[].buckets[].groups[]`
- `groups[].member_items[]`
- `groups[].contents[]`
- `contents[].evidence[]`
- `evidence[].source_assets[]`

즉 대시보드 구현은 이 JSON만 읽어도 아래 drill-down을 그대로 테스트할 수 있다.

`정책 -> 부문 -> 대표 항목 -> 내용 -> 가공 근거 -> 원문 자산`

## 현재 포함 범위

- evidence 예시는 현재 `normalized_paragraph` 중심이며, `canonical_table` 예시 1건과 `figure_or_diagram` 예시 1건을 함께 포함한다.
- taxonomy 예시는 현재 `strategy`, `tech_domain`, `tech_subdomain`을 포함한다.
- 각 `evidence.source_assets[]`는 pack 생성 시점의 `derived_to_source_asset_map`와 `source_assets` master 기준 매핑을 그대로 복사한다.
- 최신 샘플 빌드에서는 `work/04_ontology/sample_build/derived_to_source_asset_map_auto.csv`와 `work/04_ontology/sample_build/source_assets_auto.csv`를 traceability master로 사용한다.

## 현재 비포함 범위

- 전체 정책에 대한 권위 있는 full curation

## 주의

- 이 샘플 팩은 `authoritative full curation`이 아니다.
- 현재 raw 데이터를 기준으로 만든 `manual_sample` 예시다.
- 따라서 ontology 구현의 엄격한 계약본이라기보다 `shape reference + UI prototyping sample`로 써야 한다.
- 운영용 본 구축에서는 같은 구조를 전체 정책으로 확장해야 한다.
- 현재 메인 ontology 파이프라인은 이 샘플 팩을 빌드한 뒤 본체 DB에 `sample_curated` 상태로 적재해 `PolicyItemGroup`와 `PolicyItemContent` 예시 레이어를 함께 제공한다.
