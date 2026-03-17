# 정책-근거 추적형 온톨로지 및 대시보드 기획안

## 목적

최종 대시보드의 1차 목표는 아래 질의를 안정적으로 답하는 것이다.

- 12대 과학기술정책마다 `기술`, `인프라·제도`, `인재`에 어떤 항목이 있는가
- 각 항목의 설명 또는 내용은 무엇인가
- 그 항목은 어떤 정책 문서의 어떤 근거 문단, 표, 그림에 기반하는가

전략 15개, 기술분야 14개 대분류, 해외 비교는 중요한 확장 축이지만 1차 출시의 주축은 아니다.  
1차 축은 반드시 `정책 -> 3개 부문 -> 항목 -> 내용 -> 근거`여야 한다.

## 2026-03-14 기준 현재 데이터 상태

### 확보 문서

- 정책 원문은 `DOC-POL-002` 부터 `DOC-POL-012`까지 11건이 정규화 완료 상태다.
- `DOC-POL-001 123대 국정과제`는 레지스트리에 있으나 `missing` 상태다.
- `DOC-REF-001 정책-항목 구성(안)`은 OCR 라인 단위 추출본이 있어 분류 시드로 재사용 가능하다.
- `DOC-TAX-001`은 기술 대분류/중분류 authoritative source로 활용 가능하다.

### 정규화 규모

- 정책 문단 총량: `2601`
- block type 분포:
  - `bullet`: `1525`
  - `note`: `634`
  - `heading`: `244`
  - `paragraph`: `176`
  - `citation`: `12`
  - `table_markdown`: `10`

### 현재 모델의 강점

- 문서 레지스트리와 정규화 문단이 이미 분리되어 있다.
- `classification-template` 스키마가 있어 문단별 검토 워크플로를 확장하기 쉽다.
- PDF 문서는 `canonical table` 개념까지 일부 확보되어 있다.

### 현재 모델의 핵심 공백

- `paragraphs.csv/json`에는 `paragraph_id`는 있으나 원본 `evidence_id`와 `bbox` 연결이 없다.
- HWP/HWPX 계열은 `page_no`가 실제 페이지가 아니라 `section2`, `section7` 같은 섹션 기반 값인 경우가 많다.
- 따라서 현재 상태만으로는 대시보드에서 "이 항목의 정확한 원문 위치"를 일관되게 열어주기 어렵다.

## 핵심 설계 원칙

### 1. 원문 문서와 편집 결과를 분리한다

- `DOC-POL-*` 원문은 authoritative evidence다.
- `DOC-REF-001 정책-항목 구성(안)`은 사람이 정리한 시드 또는 큐레이션 가이드다.
- 화면에서는 둘 다 보여줄 수 있지만, 근거의 기본 출처는 항상 원문 문서여야 한다.

### 2. 정책과 3개 부문을 1급 엔티티로 올린다

기존 초안의 `PolicyItem` 하나만으로는 부족하다.  
정책별 3개 부문 슬롯이 먼저 있어야 항목이 안정적으로 정렬된다.

### 3. 근거는 문단/표/그림을 모두 허용한다

- 대부분의 항목은 문단 근거로 설명된다.
- 일부 항목은 표나 도식 없이는 의미가 손실된다.
- 따라서 item-evidence 관계는 다형성 구조가 필요하다.

### 4. 전략/기술분야는 교차분류 축으로 둔다

- 메인 탐색은 `정책 중심`
- 교차 필터는 `전략`, `기술분야`, `기관`, `발행시점`

### 5. provenance는 요약보다 우선한다

항목 요약문이 조금 거칠더라도 근거 링크가 명확해야 한다.  
1차 대시보드는 설명 생성보다 근거 추적의 신뢰성을 우선한다.

### 6. 근거는 3계층으로 분리한다

사용자가 실제로 보는 정보와 데이터 계보를 분리해야 한다.

- 1계층: `원문 자산`
  - PDF, PNG, 스캔 페이지, 원문 표 이미지 같은 최종 근거 파일
- 2계층: `가공 표현`
  - 원문에서 추출한 텍스트, 정규화 문단, 재구성 표, 구조화된 그림 요약
- 3계층: `표시용 메타텍스트`
  - 대시보드 카드나 상세패널에 노출할 설명문, 항목 설명, 근거 요약문

대시보드는 기본적으로 3계층을 먼저 보여주고, 필요 시 2계층과 1계층으로 drill-down 한다.

### 7. raw 추출과 대표 내용은 분리한다

원문에서 자동 추출한 bullet, note, 표 단편은 그대로 저장해야 한다.  
하지만 사람 검토와 최종 분류를 이 낱줄 단위로 수행하면 운영 비용이 지나치게 커진다.

따라서 ontology는 아래 2층을 분리해야 한다.

- `raw item`
  - 정규화 문단에서 바로 추출한 개별 항목
  - provenance 보존의 최소 단위
- `curated content item`
  - 여러 raw item을 묶은 대표 정책 항목
  - 실제 전략 분류, 기술분야 분류, 화면 노출의 기준 단위

즉:

- 저장 단위는 낱줄
- 판단 단위는 대표 내용

## 제안 온톨로지

## 1. 핵심 엔티티

### `Policy`

12대 정책 자체를 나타내는 기준 엔티티다.

필수 속성 예시:

- `policy_id`
- `policy_name`
- `policy_order`
- `policy_status`
- `primary_document_id`
- `has_source_document`

비고:

- `policy_id`는 문서 ID와 분리하는 편이 좋다.
- 정책은 유지되지만 근거 문서는 추후 교체 또는 추가될 수 있기 때문이다.

### `PolicyDocument`

기존 `Document`를 정책 문서 관점에서 사용하는 뷰다.

필수 속성 예시:

- `document_id`
- `policy_id`
- `title`
- `issued_date`
- `issuing_org`
- `source_format`
- `location_granularity`

`location_granularity` 예시:

- `page`
- `section`
- `mixed`

### `ResourceCategory`

정책별 3개 부문 통제어휘다.

저장값 제안:

- `technology`
- `infrastructure_institutional`
- `talent`

화면값 제안:

- `기술`
- `인프라·제도`
- `인재`

### `PolicyBucket`

정책과 3개 부문의 교차 슬롯이다.  
예: `AI-바이오 국가전략 > 인재`

필수 속성 예시:

- `policy_bucket_id`
- `policy_id`
- `resource_category_id`
- `display_order`
- `bucket_summary`

이 객체가 있어야 `12 x 3` 매트릭스를 안정적으로 렌더링할 수 있다.

### `PolicyItem`

각 부문 안에서 자동 추출된 raw 항목 단위다.

필수 속성 예시:

- `policy_item_id`
- `policy_bucket_id`
- `item_label`
- `item_statement`
- `item_description`
- `item_status`
- `source_basis_type`

`source_basis_type` 예시:

- `source_document_only`
- `curated_from_ref_note`
- `mixed`

비고:

- 이 엔티티는 provenance 보존에는 필요하지만 최종 화면 단위와 동일하지 않을 수 있다.

### `PolicyItemGroup`

여러 raw `PolicyItem`을 묶은 대표 정책 항목이다.

예:

- `고온 초전도 자석 실용화`
- `ICT 기반 의료시스템 해외진출`
- `게임·웹툰 해외진출 지원`

필수 속성 예시:

- `policy_item_group_id`
- `policy_bucket_id`
- `group_label`
- `group_summary`
- `group_status`

### `PolicyItemContent`

대표 정책 항목 아래의 실제 `내용` 단위다.

예:

- 기술개발 추진
- 시험 인프라 구축
- 규제 개선
- 펀드 조성
- 해외진출 지원

필수 속성 예시:

- `policy_item_content_id`
- `policy_item_group_id`
- `content_label`
- `content_statement`
- `content_type`
- `display_order`

### `EvidenceObject`

정책 항목을 뒷받침하는 최소 근거 객체의 상위 개념이다.

하위 타입:

- `EvidenceParagraph`
- `EvidenceTable`
- `EvidenceFigure`

필수 공통 속성 예시:

- `evidence_object_type`
- `evidence_object_id`
- `document_id`
- `location_type`
- `location_value`
- `display_location`
- `text_excerpt`
- `confidence`

### `SourceAsset`

가장 아래의 원문 파일 또는 원문 조각이다.

필수 속성 예시:

- `source_asset_id`
- `document_id`
- `asset_type`
- `mime_type`
- `asset_path_or_url`
- `page_no`
- `bbox`
- `thumbnail_path`

`asset_type` 예시:

- `pdf_page`
- `page_image`
- `source_table_image`
- `figure_image`

### `DerivedRepresentation`

원문 자산을 가공한 구조화 표현이다.

필수 속성 예시:

- `derived_representation_id`
- `source_asset_id`
- `representation_type`
- `structured_payload_path`
- `plain_text`
- `table_json_path`
- `normalization_version`
- `quality_status`

`representation_type` 예시:

- `normalized_paragraph`
- `canonical_table`
- `figure_summary`
- `ocr_text_block`

### `DisplayText`

대시보드에 실제 노출되는 메타정보 텍스트다.

필수 속성 예시:

- `display_text_id`
- `target_object_type`
- `target_object_id`
- `display_role`
- `title_text`
- `summary_text`
- `description_text`
- `generated_by`
- `review_status`

`display_role` 예시:

- `policy_item_group_label`
- `policy_item_content_summary`
- `evidence_caption`
- `table_note`

비고:

- `DisplayText`는 주로 `PolicyItemGroup`, `PolicyItemContent`, `DerivedRepresentation`을 대상으로 한다.
- raw `PolicyItem`에 직접 붙는 텍스트는 진단용 또는 임시 자동 생성 결과로 본다.

### `EvidenceLink`

raw 정책 항목과 근거 객체의 연결 테이블이다.

필수 속성 예시:

- `evidence_link_id`
- `policy_item_id`
- `evidence_object_type`
- `evidence_object_id`
- `link_role`
- `evidence_strength`
- `is_primary`

`link_role` 예시:

- `primary_support`
- `secondary_support`
- `reference_table`
- `reference_figure`

비고:

- 이 링크는 raw provenance 보존용이다.
- 최종 ontology의 대표 `내용-근거` 연결은 `ContentEvidenceLink`를 우선 사용한다.

### `ContentEvidenceLink`

대표 `내용`과 근거 객체의 연결 테이블이다.

필수 속성 예시:

- `content_evidence_link_id`
- `policy_item_content_id`
- `evidence_object_type`
- `evidence_object_id`
- `link_role`
- `evidence_strength`
- `is_primary`

비고:

- 하나의 `PolicyItemContent`는 여러 문단, 표, 그림을 함께 근거로 가질 수 있다.
- 이 객체가 실제 대시보드와 semantic export에서 가장 중요한 연결점이다.

### `CurationAssertion`

사람이 정리한 분류 판단 자체를 별도 기록하는 객체다.

필수 속성 예시:

- `assertion_id`
- `target_object_type`
- `target_object_id`
- `assertion_type`
- `asserted_value`
- `asserted_by`
- `asserted_at`
- `review_status`

이 객체는 아래 분류를 담당한다.

- 문단 -> 정책항목 후보
- 문단 -> 3개 부문
- 문단 -> 전략
- 문단 -> 기술분야
- raw item -> group membership
- group -> 대표 전략
- content -> 대표 근거 확정

### `TaxonomyTerm`

교차 필터용 분류축이다.

초기 범위:

- `Strategy`
- `TechDomain`
- `TechSubdomain`

## 2. 핵심 관계

- `Policy` 1:N `PolicyDocument`
- `Policy` 1:N `PolicyBucket`
- `PolicyBucket` 1:N `PolicyItem`
- `PolicyBucket` 1:N `PolicyItemGroup`
- `PolicyItemGroup` 1:N `PolicyItemContent`
- `PolicyItemGroup` N:M `PolicyItem` through `PolicyItemGroupMember`
- `SourceAsset` 1:N `DerivedRepresentation`
- `DerivedRepresentation` 1:N `DisplayText`
- `PolicyItem` N:M `EvidenceObject` through `EvidenceLink`
- `PolicyItemContent` N:M `EvidenceObject` through `ContentEvidenceLink`
- `EvidenceObject` 1:1 or 1:N `DerivedRepresentation`
- `DerivedRepresentation` N:1 `SourceAsset`
- `PolicyItem` N:M `TaxonomyTerm`
- `PolicyItemGroup` N:M `TaxonomyTerm`
- `EvidenceObject` N:M `TaxonomyTerm`
- `CurationAssertion` can target `PolicyItem` or `EvidenceObject`

## 3계층 evidence stack

대시보드와 온톨로지는 아래 순서로 연결된다.

### 1. 원문 자산 계층

예시:

- 정책 PDF의 12페이지
- 스캔본 PNG
- 표가 포함된 페이지 이미지

역할:

- 최종 provenance anchor
- 사용자가 "원문 보기"를 눌렀을 때 도달하는 위치

### 2. 가공 표현 계층

예시:

- `PAR-DOC-POL-006-00124`
- `CTBL-DOC-POL-006-003`
- OCR 블록 묶음

역할:

- 검색, 필터링, 분류, 표 렌더링의 실제 데이터 원천
- raw provenance와 대표 내용이 공유하는 operational anchor
- 정책 항목과 직접 연결되는 operational evidence

### 3. 표시용 메타텍스트 계층

예시:

- "AI 반도체 실증 인프라 확충"
- "해당 항목은 실증환경 조성과 장비지원 정책을 의미"
- "근거: 2025년 12월 18일 과기정통부 문서"

역할:

- 사용자가 처음 읽는 텍스트
- 요약, 라벨, 설명, 캡션 제공

주의:

- 3계층 텍스트는 독립 근거가 아니다.
- 3계층은 반드시 2계층 또는 1계층을 참조해야 한다.

## 대시보드용 최소 물리 테이블 제안

RDF/그래프DB로 바로 가지 말고, 우선 SQLite 또는 Parquet 기반 정규화 테이블로 시작하는 편이 낫다.

### 1. 기준 테이블

- `policies`
- `resource_categories`
- `policy_buckets`
- `documents`
- `strategies`
- `tech_domains`
- `tech_subdomains`

### 2. 큐레이션 결과 테이블

- `policy_items`
- `policy_item_groups`
- `policy_item_group_members`
- `policy_item_contents`
- `policy_item_taxonomy_map`
- `policy_item_group_taxonomy_map`
- `policy_item_document_map`
- `display_texts`

### 3. 근거 테이블

- `source_assets`
- `derived_representations`
- `evidence_paragraphs`
- `evidence_tables`
- `evidence_figures`
- `policy_item_evidence_links`
- `policy_item_content_evidence_links`

### 4. provenance 브리지 테이블

- `paragraph_source_map`
  - `paragraph_id`
  - `source_evidence_id`
  - `document_id`
  - `page_no_or_section`
  - `bbox_json`
  - `source_block_order`

- `derived_to_display_map`
  - `derived_representation_id`
  - `display_text_id`
  - `display_role`

- `derived_to_source_asset_map`
  - `derived_representation_id`
  - `source_asset_id`
  - `mapping_type`

이 브리지 테이블은 현재 구조에서 가장 시급하다.  
정규화 과정에서 사라진 원본 `evidence_id`와 위치정보를 다시 붙여줘야 한다.

### 5. 운영 메타 테이블

- `curation_assertions`
- `review_tasks`
- `data_quality_flags`

## 현재 산출물과의 매핑 방식

### 이미 있는 것

- `work/01_scope-and-ia/requirements/04_document-registry.csv`
  - `documents`, `policies`의 원천
- `work/03_processing/normalized/DOC-POL-*__paragraphs.csv`
  - `evidence_paragraphs`의 1차 입력
- `work/04_ontology/instances/DOC-POL-006__classification-template.csv`
  - `curation_assertions`의 선행 템플릿
- `work/04_ontology/instances/DOC-POL-006__canonical-tables.csv`
  - `evidence_tables`의 선행 템플릿
- `work/03_processing/normalized/DOC-TAX-001__tech-domain-subdomain.csv`
  - `tech_domains`, `tech_subdomains`의 원천

### 추가로 만들어야 하는 것

- `policy_master.csv`
  - 12개 정책의 기준 ID, 순서, 대표 문서, 결손 여부
- `policy_bucket_master.csv`
  - 12 x 3 슬롯 정의
- `policy_items.csv`
  - raw 추출 항목
- `policy_item_groups.csv`
  - 대표 정책 항목
- `policy_item_group_members.csv`
  - 대표 정책 항목과 raw 항목 연결
- `policy_item_contents.csv`
  - 대표 정책 항목 아래의 내용 진술
- `policy_item_evidence_links.csv`
  - raw 항목과 근거 연결
- `policy_item_content_evidence_links.csv`
  - 대표 내용과 근거 연결
- `paragraph_source_map.csv`
  - 문단과 원본 evidence 연결
- `display_texts.csv`
  - 화면 노출용 라벨, 요약, 설명문
- `source_assets.csv`
  - PDF 페이지, PNG, 원문 이미지 링크
- `derived_representations.csv`
  - 정규화 문단, 재구성 표, 그림 요약

## 대시보드 IA 재구성 제안

## 1. 1차 메뉴

### `정책 맵`

첫 화면은 `12개 정책 x 3개 부문` 매트릭스가 맞다.

보여줄 것:

- 정책별 카드 또는 행
- 각 부문별 항목 수
- 근거 문서 확보 여부
- 검토 상태

이 화면에서 사용자는 "어떤 정책의 어떤 부문이 얼마나 채워졌는가"를 바로 본다.

### `정책 상세`

정책 하나를 열면 3개 부문이 탭 또는 세로 섹션으로 보인다.

각 부문에서 보여줄 것:

- 항목 목록
- 항목 요약
- 연결 전략/기술분야 태그
- 대표 근거 1개
- 더보기 시 전체 근거 목록

### `근거 보기`

항목 클릭 시 여는 상세 패널 또는 별도 뷰다.

보여줄 것:

- 표시용 메타텍스트
- 근거 문단 원문 또는 재구성 표
- 문서명
- 페이지 또는 섹션 위치
- 표/그림 연결
- 원문 PDF/PNG 링크
- 추출 신뢰도
- 검토 상태

### `교차 분석`

이 화면에서만 전략/기술분야를 메인 축으로 승격한다.

보여줄 것:

- 전략별 연결 정책 항목 수
- 기술분야별 연결 정책 항목 수
- 부문별 분포

## 2. drill-down 흐름

권장 기본 흐름:

1. `정책 맵`에서 정책 선택
2. `정책 상세`에서 3개 부문 중 하나 선택
3. 항목 선택
4. `근거 보기`에서 메타텍스트와 가공 표현 확인
5. 필요 시 원문 PDF/PNG 뷰로 이동

보조 흐름:

1. 전략 또는 기술분야 필터 선택
2. 연결된 정책 항목 목록 확인
3. 정책 상세 또는 근거 보기로 이동

## 3. 화면에서 반드시 보여야 하는 메타데이터

- 근거가 어느 문서에서 왔는가
- 위치가 페이지인지 섹션인지
- 원문 근거가 1개인지 다수인지
- 사람이 검토했는지 여부
- `정책-항목 구성(안)` 시드를 참고했는지 여부

## 1차 출시 범위 제안

### 반드시 포함

- 12개 정책 기준표
- 3개 부문 슬롯
- 정책별 항목 목록
- 항목별 근거 문단 연결
- 문서/기관/발행일 표시
- 전략/기술분야 태그 필터

### 가능하면 포함

- canonical table 연결
- 근거 문단 다건 연결
- 검토 상태 표시

### 2차로 미뤄도 되는 것

- 해외 비교
- 고급 네트워크 그래프
- 자동 요약 생성
- 정책 간 의미 유사도 탐색

## 운영 워크플로 제안

### 단계 1. 정책 기준표 확정

- 12개 정책 ID 확정
- 대표 문서 매핑
- 결손 정책 슬롯 표시

### 단계 2. 3개 부문 슬롯 생성

- 정책별 `technology / infrastructure_institutional / talent` 슬롯 생성

### 단계 3. 문단 큐레이션

- `classification-template`를 11개 정책 문서 전체로 확장
- 문단별 `정책항목 후보`, `3개 부문`, `전략`, `기술분야` 검토

### 단계 4. 항목 승격

- 같은 의미의 raw `PolicyItem`들을 `PolicyItemGroup`으로 묶음
- 대표 항목 제목과 설명문 정리
- 그룹 아래 `PolicyItemContent`를 생성

### 단계 5. 근거 연결

- `PolicyItemContent`에 대표 근거와 보조 근거 연결
- 표와 그림도 가능하면 함께 연결
- 각 근거에 대해 `원문 자산 -> 가공 표현 -> 표시용 메타텍스트` 연결 확정

### 단계 6. 대시보드 마트 생성

- 정책 맵용 집계
- 정책 상세용 item 리스트
- 근거 보기용 provenance 데이터셋 생성
- display layer용 카드/패널 텍스트 생성

## 당장 필요한 후속 작업

우선순위 순으로 정리하면 아래와 같다.

1. `paragraph_source_map`을 만들 수 있게 정규화 스크립트 또는 후처리 브리지를 설계한다.
2. `policy_master`와 `policy_bucket_master`를 만든다.
3. raw `policy_items`를 `policy_item_groups`로 묶는 클러스터링 규칙을 설계한다.
4. 그룹 아래 `policy_item_contents`와 `policy_item_content_evidence_links`의 CSV 스키마를 확정한다.
5. `DOC-REF-001 정책-항목 구성(안)`을 authoritative source가 아닌 curation seed로 정리한다.

## 결론

현재 파싱 결과는 대시보드 1차 목표를 달성하기에 충분한 출발점이다.  
다만 핵심 성공 조건은 더 많은 파싱이 아니라 아래 두 가지다.

- `정책-3부문-항목`을 고정 슬롯 구조로 먼저 정의하는 것
- `문단 -> 원본 evidence` provenance 브리지를 복구하는 것

이 두 축만 먼저 잡히면, 이후 전략/기술분야/해외 비교는 안정적으로 얹을 수 있다.

최종 ontology의 권장 주축은 아래와 같다.

`Policy -> PolicyBucket -> PolicyItemGroup -> PolicyItemContent -> EvidenceObject -> DerivedRepresentation -> SourceAsset`

그리고 raw provenance 보존을 위해 아래가 병행된다.

`PolicyItem -> EvidenceObject`

즉:

- raw `PolicyItem`은 보존용
- `PolicyItemGroup`과 `PolicyItemContent`는 판단용
- 전략/기술분야 분류는 가능하면 `PolicyItemGroup` 이상에서 수행
