# 관계형 온톨로지 스키마 노트

## 목적

`03_relational-ontology-schema.sql`의 테이블 역할과 주요 join 경로를 짧게 정리한다.

## 1차 핵심 조회 경로

대시보드의 기본 drill-down은 아래 순서를 따른다.

1. `policies`
2. `policy_buckets`
3. `policy_item_groups`
4. `policy_item_contents`
5. `policy_item_content_evidence_links`
6. `derived_representations`
7. 필요 시 `evidence_paragraphs` 또는 `evidence_tables`
8. 필요 시 `source_assets`

즉, 화면에서 먼저 잡는 주축은 `policy_item_groups`와 `policy_item_contents`이고, provenance의 operational anchor는 `derived_representations`다.

## raw 추출과 curated ontology 분리

현재 스키마는 같은 정책 문장을 두 층으로 다룬다.

### raw 추출층

- `policy_items`
- `policy_item_evidence_links`

역할:

- 정규화 문단에서 자동 추출된 낱줄 또는 세부 항목을 보존
- 원문 fragment와 1:1 또는 1:n 관계를 유지
- 사람이 직접 최종 화면 단위로 쓰기에는 너무 세분화될 수 있음

### curated ontology 층

- `policy_item_groups`
- `policy_item_group_members`
- `policy_item_contents`
- `policy_item_content_evidence_links`
- `policy_item_group_taxonomy_map`

역할:

- 여러 raw `policy_items`를 하나의 대표 정책 항목으로 묶음
- 대표 항목 아래에 `내용 진술(content statement)`를 별도 저장
- 전략/기술분야 분류는 가능하면 이 curated 층에 부여

즉, `저장은 낱줄`, `분류와 화면 노출은 대표 내용 단위`가 원칙이다.

## 3계층 evidence stack 매핑

### 1. 원문 자산

- `source_assets`

예:

- PDF 페이지
- PNG 스캔 페이지
- 원문 표 이미지

### 2. 가공 표현

- `derived_representations`
- `evidence_paragraphs`
- `evidence_tables`
- `evidence_figures`

예:

- 정규화 문단
- canonical table
- 그림 요약

### 3. 표시용 메타텍스트

- `display_texts`
- `derived_to_display_map`

예:

- 정책 항목 라벨
- 근거 요약문
- 표 설명문

## 정책 구조 테이블

### `policies`

12대 정책 기준 엔터티.

### `documents`

문서 레지스트리에서 가져온 정책 문서 엔터티.  
`policy_id`를 통해 정책에 연결된다.

### `resource_categories`

`기술`, `인프라·제도`, `인재` 통제어휘.

### `policy_buckets`

정책 x 3개 부문 슬롯.  
`12 x 3 = 36`개의 안정된 화면 슬롯을 제공한다.

### `policy_items`

자동 추출된 raw 항목 후보.

### `policy_item_groups`

여러 raw 항목을 묶은 대표 정책 항목.

예:

- `고온 초전도 자석 실용화`
- `ICT 기반 의료시스템 해외진출 지원`
- `게임·웹툰 해외진출 제도 개선`

### `policy_item_group_members`

대표 정책 항목과 raw 항목의 membership 브리지.

### `policy_item_contents`

대표 정책 항목 아래의 실제 `내용` 단위.

예:

- 기술개발 추진
- 인프라 구축
- 규제 개선
- 펀드 조성

### `policy_item_group_taxonomy_map`

전략/기술분야 분류는 이 테이블을 우선 대상으로 삼는다.

## provenance 및 evidence 테이블

### `derived_representations`

가장 중요한 공통 테이블이다.

역할:

- 문단, 표, 그림을 하나의 operational evidence 층으로 묶음
- `policy_item_evidence_links`가 직접 참조
- 3계층 구조에서 가운데 계층을 담당

### `paragraph_source_map`

현재 가장 중요한 후속 테이블이다.

역할:

- 정규화 문단과 원본 evidence block 연결
- `bbox`, `source_evidence_id`, 원본 순서 보존
- 추후 `source_assets` 자동 생성의 입력

### `derived_to_source_asset_map`

가공 표현과 원문 자산의 연결 브리지.

### `policy_item_evidence_links`

raw 정책 항목과 근거 표현의 연결 브리지.

### `policy_item_content_evidence_links`

curated `내용`과 근거 표현의 연결 브리지.

이 테이블 덕분에 하나의 대표 내용이 여러 문단, 표, 그림을 근거로 가질 수 있다.

## 교차 분류 테이블

### `strategies`

15개 전략 축.

### `tech_domains`

14개 기술 대분류.

### `tech_subdomains`

기술 중분류.

### `policy_item_taxonomy_map`

raw 항목과 전략/기술분야의 연결 브리지.

임시 자동 분류나 진단 용도로는 유효하지만, 최종 분류는 `policy_item_group_taxonomy_map`으로 이동시키는 것이 맞다.

## 운영 테이블

### `curation_assertions`

사람 또는 규칙 기반 분류 판단 기록.

### `data_quality_flags`

누락 근거, 위치 불명, 중복 매핑 같은 품질 이슈 기록.

## 현재 적재 상태

2026-03-14 기준:

- 시드 기준 테이블 적재 완료
- `evidence_paragraphs` 적재 완료
- `evidence_tables`는 현재 canonical table이 있는 문서만 일부 적재
- `source_assets`, `display_texts`, `paragraph_source_map` 적재 진행 중
- `policy_item_groups`, `policy_item_contents`, `policy_item_content_evidence_links`는 스키마만 추가된 상태

## 다음 우선순위

1. raw `policy_items`를 대표 `policy_item_groups`로 묶는 클러스터링 규칙 설계
2. 각 그룹 아래 `policy_item_contents`를 생성
3. `policy_item_content_evidence_links`로 대표 내용과 근거를 연결
4. 전략/기술분야 분류를 `policy_item_group_taxonomy_map`으로 이동
