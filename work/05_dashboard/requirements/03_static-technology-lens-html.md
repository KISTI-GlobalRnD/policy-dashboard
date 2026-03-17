# 정적 HTML 기술축 시안 기준

> 이 문서는 단일 HTML 기준의 이전 시안 문서다.
> 최신 정적 UX 기준은 `work/05_dashboard/requirements/04_overview-detail-static-ux.md`를 따른다.

## 목적

이 문서는 `work/05_dashboard/index.html` 하나만 남기는 정적 시안의 기준 문서다.

이 시안의 목적은 아래를 한 화면에서 읽게 하는 것이다.

1. 어떤 기술대분류 아래에 어떤 대표 정책 그룹이 배치되는가
2. 그 그룹이 어느 정책과 부문에서 왔는가
3. 그 그룹 아래 대표 내용과 대표 정책 근거가 무엇인가
4. 이전 raw item 계보가 어떻게 이어지는가

## 권위 기준

정적 HTML 시안은 아래를 기준으로 한다.

- 구조 기준: `work/04_ontology/schemas/06_technology-lens-projection.md`
- 샘플 숫자와 payload 기준: `work/05_dashboard/data-contracts/technology-lens.json`

참고:

- `work/05_dashboard/requirements/02_frontend-rearchitecture.md`는 React 매트릭스 시안 기준 문서다.
- 이번 정적 HTML은 위 문서를 참고할 수 있지만, 권위 입력 계약은 아니다.

## 산출물 범위

- 최종 산출물: `work/05_dashboard/index.html`
- 외부 JS 없음
- 외부 JSON fetch 없음
- 외부 CSS 파일 없음
- 정적 선택 상태를 가진 고정 시안

즉 이 파일은 실행형 앱이 아니라 `technology-lens` 데이터 계약을 설명하는 고충실도 reference mock이다.

## 루트 구조

기술축 시안의 1차 루트는 `정책`이 아니라 `기술대분류`다.

화면의 기본 drill-down은 아래를 따른다.

`기술대분류 -> 대표 정책 그룹 -> 대표 내용 -> primary policy evidence -> evidence stack -> member items -> source asset`

## 화면 구조

### 1. Context Bar

역할:

- projection의 정체성과 범위를 한 줄로 설명
- 현재 샘플 범위와 품질 상태를 요약

표시 항목:

- projection 이름
- projection 버전
- generated_at
- projected tech domain 수
- group 수
- content 수
- unassigned group 수

### 2. Tech Domain Index

역할:

- 14개 기술대분류 전체를 왼쪽에서 고정 인덱스로 보여줌

표시 항목:

- `tech_domain_label`
- `group_count`
- `content_count`

규칙:

- 0건 기술도 숨기지 않음
- 현재 선택 기술을 명확히 강조

### 3. Selected Domain Summary

역할:

- 선택 기술의 정책 분포와 성격을 먼저 읽게 함

표시 항목:

- `policy_count`
- `resource_category_counts`
- `strategies[]`
- `subdomains[]`

정책은 여기서 `related policies` 요약으로만 노출한다.
독립된 `Policy Ledger` 패널은 두지 않는다.

### 4. Group Board

역할:

- 선택 기술 아래의 `groups[]`를 주 작업면으로 보여줌

각 카드 필수 항목:

- `group_label`
- `group_summary`
- `policy.policy_name`
- `bucket.resource_category_label`
- `taxonomy.primary_tech_subdomain.label`
- `taxonomy.strategies[]`
- `content_count`
- `member_item_count`
- 첫 content의 `content_summary`
- 첫 content의 `primary_policy_evidence.location_value`

정책 정보는 이 카드 안에 흡수한다.

### 5. Detail Panel

역할:

- 현재 선택된 group/content의 상세와 이전 데이터 계보를 복원

표시 순서:

1. lineage summary
2. content list
3. `primary_policy_evidence`
4. `evidence[]`
5. `member_items[]`
6. `source_assets[]`

원칙:

- `primary_policy_evidence`는 항상 상세 패널 최상단 근거 블록이어야 한다.
- `member_items[]`는 이전 raw item 계보를 설명하는 블록으로 유지한다.

### 6. Unassigned Block

역할:

- `unassigned_groups[]`를 별도 QA 구역으로 노출

규칙:

- 값이 0이어도 블록을 숨기지 않음
- `없음` 상태를 명시적으로 보여줌

## 데이터 필드 매핑

### Tech Domain Index

- `tech_domain_filters[]`

### Selected Domain Summary

- `tech_domains[n].policy_count`
- `tech_domains[n].resource_category_counts`
- `tech_domains[n].strategies[]`
- `tech_domains[n].subdomains[]`

### Group Board

- `tech_domains[n].groups[]`
- `groups[].policy`
- `groups[].bucket`
- `groups[].taxonomy`
- `groups[].contents[]`

### Detail Panel

- `groups[].contents[]`
- `contents[].primary_policy_evidence`
- `contents[].evidence[]`
- `groups[].member_items[]`
- `contents[].primary_policy_evidence.source_assets[]`

### Unassigned Block

- `unassigned_groups[]`

## 기본 선택 상태

정적 시안의 기본 선택은 아래로 고정한다.

- 선택 기술: `인공지능`
- 선택 그룹: `PIG-POL-011-01`
- 선택 content: `PIC-POL-011-01-01`

이유:

- 정책, 부문, 전략, raw item, evidence, source asset 흐름을 가장 압축적으로 보여준다.

## 포함/제외 범위

### 반드시 포함

- 기술대분류 인덱스
- 선택 기술 요약
- group 카드 보드
- 대표 정책 근거
- evidence stack
- raw member trace
- source asset 식별 정보
- unassigned 상태

### 제외

- 기존 `Policy Ledger`
- 긴 `Content Table`
- 이전 prototype/React 링크
- 동적 필터 동작
- 런타임 정렬/검색
- 실제 문서 preview 렌더링

## 링크 정책

- 삭제된 파일을 가리키는 링크는 남기지 않는다.
- 실제 열기 가능 여부를 보장할 수 없는 경우 링크 대신 경로 텍스트만 노출한다.
- 정적 시안에서는 자산 접근보다 traceability 설명이 우선이다.

## 레이아웃 정책

- `body overflow: hidden` 금지
- `height: 100vh` 고정 금지
- 페이지 전체 세로 스크롤 허용
- 첫 화면에서 `Tech Domain Index + Selected Domain Summary + Group Board`가 먼저 보여야 함
- 오른쪽 상세 패널만 보조적으로 sticky 가능

## 실패 조건

아래 중 하나라도 만족하면 시안 실패로 본다.

- 정책이 다시 루트 패널처럼 보임
- group 카드에서 정책명 또는 부문이 보이지 않음
- `primary_policy_evidence`가 상세 패널 최상단이 아님
- `member_items[]`가 숨겨짐
- `unassigned_groups` 상태가 보이지 않음
- 삭제된 경로 링크가 남아 있음
- 페이지 전체 스크롤이 막혀 하단 블록 접근이 안 됨

## 구현 순서

1. dead link 제거
2. `overflow/100vh` 구조 제거
3. 기존 hero와 summary를 `Context Bar` 중심 구조로 압축
4. `Policy Ledger` 제거
5. 메인 본판을 `Group Board`로 교체
6. 오른쪽 상세 패널을 `technology-lens` 계보 기준으로 재배치
7. `unassigned` 블록 추가

## 검증 체크리스트

- HTML 파일은 `work/05_dashboard/index.html` 하나만 사용한다.
- 문서 기준과 화면 구조가 일치한다.
- 선택 기술에서 정책/부문/raw item/evidence/source asset 흐름이 읽힌다.
- count와 라벨이 `technology-lens.json` 샘플과 모순되지 않는다.
