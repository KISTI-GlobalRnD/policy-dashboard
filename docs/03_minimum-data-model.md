# 최소 데이터모델 초안

이 문서는 추출, 가공, 온톨로지, 대시보드가 같은 기준으로 움직이기 위한 최소 모델이다.

## 모델 목표

- 원문 근거를 잃지 않는다.
- 표와 그림을 본문 텍스트와 분리해 저장한다.
- 정책 항목, 전략, 기술분야, 자원유형을 서로 연결할 수 있게 만든다.
- 처음에는 단순한 테이블 구조로 구현하고, 필요하면 그래프 형태로 확장한다.

## 핵심 개체

| 개체 | 설명 | 필수 속성 예시 |
| --- | --- | --- |
| `Document` | 원문 문서 단위 | `document_id`, `title`, `issued_date`, `issuing_org`, `country`, `source_path`, `source_format` |
| `EvidenceUnit` | 본문에서 추출한 최소 근거 블록 | `evidence_id`, `document_id`, `page_no`, `block_type`, `text`, `bbox`, `extraction_confidence` |
| `TableUnit` | 표 단위 객체 | `table_id`, `document_id`, `page_no`, `title`, `header_rows`, `table_path`, `extraction_confidence` |
| `FigureUnit` | 그림/도식 단위 객체 | `figure_id`, `document_id`, `page_no`, `caption`, `figure_type`, `summary`, `asset_path` |
| `PolicyItem` | 정책 문헌에서 의미 있는 항목 단위 | `policy_item_id`, `document_id`, `label`, `statement`, `resource_type` |
| `Strategy` | 재구성된 전략 축 | `strategy_id`, `name`, `description`, `source_basis` |
| `TechDomain` | 기술 대분류 | `tech_domain_id`, `name`, `source_basis` |
| `TechSubdomain` | 기술 중분류 | `tech_subdomain_id`, `tech_domain_id`, `name` |
| `Institution` | 부처, 기관, 국가 단위 발행 주체 | `institution_id`, `name`, `institution_type`, `country` |
| `Classification` | 근거 또는 정책항목에 대한 분류 결과 | `classification_id`, `source_object_type`, `source_object_id`, `strategy_id`, `tech_domain_id`, `tech_subdomain_id`, `resource_type`, `confidence`, `review_status` |

## 핵심 관계

- `Document`는 여러 `EvidenceUnit`, `TableUnit`, `FigureUnit`, `PolicyItem`을 가진다.
- `Document`는 하나 이상의 `Institution`과 연결된다.
- `PolicyItem`은 하나 이상의 `EvidenceUnit`, `TableUnit`, `FigureUnit`으로 근거를 가질 수 있다.
- `TechSubdomain`은 하나의 `TechDomain`에 속한다.
- `Classification`은 `PolicyItem` 또는 `EvidenceUnit`을 전략/기술분야/자원유형에 매핑한다.

## 자원유형 통제어휘

초기값:

- `technology`
- `infrastructure_policy`
- `talent`

문서 표기와 화면 표기는 아래처럼 분리해도 된다.

- 저장값: `technology`, `infrastructure_policy`, `talent`
- 화면값: `기술`, `인프라 및 제도`, `인재 및 인력양성`

## 권장 ID 규칙

- `DOC-0001`
- `EVD-000001`
- `TBL-000001`
- `FIG-000001`
- `POL-000001`
- `STR-001`
- `TD-001`
- `TSD-001001`
- `CLS-000001`

## 구현 권장 방식

1. 1차 저장은 CSV, Parquet, SQLite 중 하나로 단순하게 시작
2. 대시보드 연결용으로는 정규화 테이블과 요약 마트를 별도 유지
3. RDF/OWL 또는 그래프 DB는 분류 체계가 안정된 뒤 2차 도입

## 추출 단계에서 반드시 남길 필드

- 원문 파일명
- 페이지 번호
- 블록 유형
- 추출 위치 정보
- 추출 신뢰도
- 검토자 또는 검토 상태

이 필드가 없으면 나중에 매핑 오류를 다시 검증하기 어렵다.
