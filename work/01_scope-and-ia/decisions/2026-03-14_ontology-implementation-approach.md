# 2026-03-14 Ontology Implementation Approach

## 결정

온톨로지는 아래 2단계 구조로 구현한다.

### 1차 구현

`SQLite`를 authoritative working store로 사용한다.

구성:

- 엔터티와 관계는 관계형 테이블로 구현
- provenance는 브리지 테이블로 명시
- 대시보드 입력용 데이터는 필요 시 `Parquet` 또는 `CSV` 마트로 export

### 2차 확장

`JSON-LD`와 `Turtle`로 RDF export 레이어를 추가한다.

구성:

- 클래스/속성 정의는 `OWL/RDFS`
- 통제어휘는 `SKOS`
- provenance는 `PROV-O`
- 메타데이터 기본 속성은 `DCTERMS`
- 구조 검증은 `SHACL`

## 이유

현재 프로젝트의 핵심 요구는 다음과 같다.

- `정책 -> 3개 부문 -> 대표 내용 -> 근거`를 안정적으로 조회
- 대시보드에서 빠르게 drill-down
- 원문 근거와 가공 데이터의 provenance 유지
- 사람 검토와 운영 보정이 쉬워야 함

이 요구에는 그래프 DB나 순수 RDF 저장소보다 관계형 테이블이 먼저 맞다.

### 관계형 1차 구현이 맞는 이유

- 현재 산출물이 이미 CSV/JSON 중심이다.
- 대시보드 질의는 그래프 추론보다 목록, 집계, 필터, drill-down 비중이 높다.
- `policy_items`, `policy_item_groups`, `policy_item_contents`, `policy_item_content_evidence_links`, `paragraph_source_map` 같은 운영 테이블은 SQL이 가장 단순하다.
- 수동 검토와 배치 수정도 SQLite가 다루기 쉽다.

### RDF export를 2차로 두는 이유

- 외부 연계나 시맨틱 검색이 필요해질 수 있다.
- provenance 3계층 모델은 RDF로도 잘 표현된다.
- 그러나 지금 당장 RDF 저장소를 주 저장소로 쓰면 구현 복잡도만 올라간다.

## 채택 스택

### 저장 계층

- authoritative store: `SQLite`
- 분석/대시보드용 마트: `Parquet`
- 작업 중 교환 포맷: `CSV`, `JSON`

### 시맨틱 계층

- 클래스/관계 정의: `OWL/RDFS`
- 분류체계: `SKOS`
- provenance: `PROV-O`
- 기본 메타데이터: `Dublin Core Terms`
- 검증: `SHACL`

### API/교환 계층

- 내부 앱 연결: SQL 또는 Parquet
- 외부 교환/확장: `JSON-LD`

## 이 프로젝트에 적용할 최소 클래스

- `Policy`
- `PolicyDocument`
- `ResourceCategory`
- `PolicyBucket`
- `PolicyItem`
- `PolicyItemGroup`
- `PolicyItemContent`
- `EvidenceParagraph`
- `EvidenceTable`
- `EvidenceFigure`
- `SourceAsset`
- `DerivedRepresentation`
- `DisplayText`
- `Strategy`
- `TechDomain`
- `TechSubdomain`

## 핵심 관계

- `Policy` -> `PolicyBucket`
- `PolicyBucket` -> `PolicyItemGroup`
- `PolicyItemGroup` -> `PolicyItemContent`
- `PolicyItemGroup` -> `PolicyItem`
- `PolicyItemContent` -> `EvidenceObject`
- `PolicyItem` -> `EvidenceObject`
- `SourceAsset` -> `DerivedRepresentation`
- `DerivedRepresentation` -> `DisplayText`
- `DerivedRepresentation` -> `EvidenceObject`

## 표준 vocabulary 매핑 원칙

### `SKOS`로 둘 것

- 3개 부문
- 15개 전략
- 14개 기술 대분류
- 기술 중분류

이유:

- 계층과 라벨 관리가 쉽다.
- 추후 용어 변경 이력 관리가 편하다.

### `PROV-O`로 둘 것

- `SourceAsset`
- `DerivedRepresentation`
- `DisplayText`
- 문단/표/그림의 파생 관계

예시 관계:

- `prov:wasDerivedFrom`
- `prov:wasGeneratedBy`
- `prov:wasAttributedTo`

### 커스텀 클래스가 필요한 것

- `PolicyBucket`
- `PolicyItem`
- `PolicyItemGroup`
- `PolicyItemContent`
- `EvidenceLink`
- `ContentEvidenceLink`

이유:

- 이 도메인에 특화된 구조라서 범용 vocabulary만으로는 의미가 불명확해진다.

## 지금 쓰지 않을 것

- `Neo4j`를 주 저장소로 바로 도입하지 않음
- `GraphDB`, `Fuseki` 같은 RDF store를 1차 저장소로 쓰지 않음
- 복잡한 OWL reasoning을 1차 범위에 포함하지 않음

## 바로 구현할 파일 수준 산출물

### 스키마

- `work/04_ontology/schemas/`
  - 관계형 테이블 정의
  - RDF class/property 매핑 초안
  - SHACL 검증 규칙 초안

### 인스턴스

- `work/04_ontology/instances/`
  - `policies`
  - `policy_buckets`
  - `policy_items`
  - `policy_item_groups`
  - `policy_item_contents`
  - `source_assets`
  - `derived_representations`
  - `display_texts`
  - `policy_item_evidence_links`
  - `policy_item_content_evidence_links`
  - `paragraph_source_map`

## 구현 순서

1. SQLite 테이블 스키마 확정
2. `policy_master`, `policy_bucket_master` 생성
3. `paragraph_source_map` 설계
4. raw `policy_items` 생성
5. `policy_item_groups`, `policy_item_contents`, `policy_item_content_evidence_links` 생성
6. `display_texts`와 curated taxonomy 매핑 생성
7. RDF export 매핑 정의
8. SHACL 검증 규칙 추가

## 결론

이 프로젝트에서 온톨로지는 처음부터 RDF 저장소로 시작하는 것이 아니라,  
`SQLite 기반 관계형 온톨로지 마트 + JSON-LD/Turtle semantic export`로 가는 것이 맞다.

즉, 지금 만들 것은:

- 운영용으로는 `SQLite`
- 의미모델로는 `OWL/RDFS + SKOS + PROV-O`
- 검증용으로는 `SHACL`

이 조합이 현재 목표와 구현 난이도 사이에서 가장 균형이 좋다.
