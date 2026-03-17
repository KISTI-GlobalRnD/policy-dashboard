# 2026-03-14 Content-Evidence Centered Ontology

## 결정

온톨로지의 판단 단위는 `낱줄 raw item`이 아니라 `대표 내용(content)`으로 둔다.

구조는 아래와 같이 계층화한다.

`Policy -> PolicyBucket -> PolicyItemGroup -> PolicyItemContent -> EvidenceObject -> DerivedRepresentation -> SourceAsset`

동시에 raw provenance 보존을 위해 아래 경로를 병행 유지한다.

`PolicyItem -> EvidenceObject`

## 이유

현재 자동 추출 `policy_items`는 원문 bullet, note, 단문을 거의 그대로 반영한다.

이 방식은 provenance 보존에는 적합하지만, 아래 문제를 만든다.

- 같은 사업/프로젝트가 여러 줄로 중복 추출됨
- 전략/기술분야 분류를 줄 단위로 수행해야 하는 운영 비용이 과도함
- `배경`, `총론`, `실적`, `지원체계`, `법제 정비` 같은 일반 문장도 항목처럼 보이게 됨

따라서 raw 추출과 최종 ontology 단위를 분리해야 한다.

## 의미

### `PolicyItem`

- raw 추출 항목
- provenance 보존의 최소 단위
- 자동 추출 진단과 membership source로 사용

### `PolicyItemGroup`

- 여러 raw item을 묶은 대표 정책 항목
- 실제 전략/기술분야 분류의 1차 대상
- 화면 목록의 기본 단위

### `PolicyItemContent`

- 대표 항목 아래의 실제 내용 진술
- `기술개발`, `인프라 구축`, `규제 개선`, `펀드 조성`, `해외진출 지원` 같은 서술을 분리 저장
- 근거 연결의 실질적 대상

## 구현 원칙

1. raw 추출 결과는 버리지 않는다.
2. 대표 정책 항목은 `policy_item_groups`로 별도 관리한다.
3. 내용 진술은 `policy_item_contents`로 별도 관리한다.
4. 근거 연결은 가능하면 `policy_item_content_evidence_links`에서 수행한다.
5. 전략/기술분야 분류는 장기적으로 `policy_item_group_taxonomy_map`으로 이동한다.

## 이번 결정으로 추가되는 핵심 테이블

- `policy_item_groups`
- `policy_item_group_members`
- `policy_item_contents`
- `policy_item_content_evidence_links`
- `policy_item_group_taxonomy_map`

## 영향

### 긍정적 영향

- 줄 단위 수동 검토를 대표 내용 단위 검토로 축소할 수 있다.
- `내용`과 `증거`의 연결이 명확해진다.
- 대시보드와 RDF export의 주축이 더 안정된다.

### 남는 과제

- raw item -> group 클러스터링 규칙 설계
- group -> content 생성 규칙 설계
- 기존 `policy_item_taxonomy_map`에서 `policy_item_group_taxonomy_map`으로 분류 이관

## 결론

이 프로젝트의 ontology는 `낱줄 분류 시스템`이 아니라 `대표 내용-근거 추적 시스템`이어야 한다.

즉:

- 저장은 낱줄
- 판단은 대표 내용
- 근거는 provenance 3계층
