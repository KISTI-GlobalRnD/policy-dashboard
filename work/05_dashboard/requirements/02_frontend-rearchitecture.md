# 대시보드 프론트엔드 재설계안 v2

## 재설계 이유

기존 React 샘플은 `정책 -> 대표 내용 -> 근거 -> 원문 자산`을 따라가는 trace-first 워크벤치에 가깝다.

이 구조는 provenance 검증에는 강하지만, 지금 더 중요한 질문에는 바로 답하지 못한다.

- 어떤 정책이 어떤 기술 대분류에 실제로 매핑되는가
- 각 정책 내부에서 어떤 `대표 내용(content)`이 그 기술분류에 연결되는가
- 기술분류별로 매핑 밀도와 공백이 어디에 있는가
- 매핑되지 않은 내용이 무엇이며 왜 빠졌는가

즉 1차 화면의 중심축은 `근거 추적`이 아니라 `정책 x 기술 대분류 매핑`이어야 한다.
근거 trace는 여전히 중요하지만, 기본 화면의 주축이 아니라 drill-down 단계로 내려가야 한다.

## 이 문서의 위치

이 문서는 기존 trace-first 시안을 대체하는 프런트엔드 기준 문서다.

- 기존 기준: `정책 -> 내용 -> 근거` 중심
- 새 기준: `정책 x 기술 대분류 매핑 -> 매핑된 내용 -> 근거` 중심

## 설계 목표

- 첫 화면에서 `정책 x 14개 기술 대분류` 매핑을 한눈에 읽을 수 있어야 한다.
- 셀 하나를 눌렀을 때 그 셀을 구성하는 `대표 그룹`과 `대표 내용`으로 바로 내려갈 수 있어야 한다.
- 매핑 결과가 반드시 원문 근거와 연결되어야 한다.
- 매핑된 것뿐 아니라 `미매핑`과 `검토 필요` 상태도 노출해야 한다.
- 현재 샘플 데이터가 작더라도, 최종 목표인 `12개 정책 x 14개 기술 대분류` 화면을 그대로 수용해야 한다.

## 축 우선순위

이 설계는 기존 `12개 정책 x 3개 부문` 첫 화면 제안을 대체한다.

- 1차 주축: `정책 x 기술 대분류`
- 2차 보조 축: `전략`, `자원유형`, `검토 상태`
- 3차 drill-down: `대표 내용`, `근거`, `원문 자산`

즉 `기술 / 인프라·제도 / 인재` 3개 부문은 더 이상 첫 화면의 열 축이 아니다.
이 값은 셀 내부 구성비나 상세 패널의 보조 메타데이터로 내려간다.

## 전제

### 분류 단위

기술분류의 1차 대상은 raw line item이 아니라 `PolicyItemGroup`이다.
실제 화면에서 사용자가 읽는 최소 의미 단위는 `PolicyItemContent`다.

따라서 화면 구조는 아래 순서를 따른다.

`Policy -> TechDomain -> PolicyItemGroup -> PolicyItemContent -> Evidence -> SourceAsset`

### 기술분류 기준

기술 대분류는 `data/260312_중장기투자전략_세부기술분야별_중분류.xlsx`의 14개 대분류를 따른다.

1. 인공지능
2. 에너지
3. 이차전지
4. 국방
5. 소재
6. 사이버보안
7. 차세대통신
8. 첨단로봇제조
9. 반도체디스플레이
10. 양자
11. 첨단바이오
12. 우주항공
13. 해양
14. 첨단모빌리티

### 범위

- 최종 설계 목표: `12개 정책 x 14개 기술 대분류`
- 현재 샘플 데이터: 정책 3개, 대표 내용 19개, 기술 태그는 일부만 존재

현재 샘플이 작더라도, UI 구조는 최종 범위를 기준으로 설계한다.

## 핵심 질문

첫 화면은 최소한 아래 질문을 바로 답해야 한다.

1. 어떤 정책이 어떤 기술 대분류에 연결되는가
2. 각 정책 안에서 기술 대분류별로 몇 개의 대표 그룹/대표 내용이 매핑되는가
3. 매핑되지 않은 대표 내용은 어느 정책에 몰려 있는가
4. 특정 정책-기술대분류 셀을 구성하는 실제 내용과 근거는 무엇인가

## 사용자 작업 흐름

권장 기본 흐름은 아래와 같다.

1. 정책 x 기술대분류 매트릭스에서 관심 셀을 찾는다.
2. 셀을 선택해 해당 정책과 기술분류에 속한 대표 그룹/대표 내용을 본다.
3. 대표 내용을 선택해 연결된 근거 문단, 표, 그림을 확인한다.
4. 필요 시 원문 자산을 열어 provenance를 검증한다.

보조 흐름은 아래와 같다.

1. 기술 대분류 또는 전략을 먼저 선택한다.
2. 관련 정책들을 비교한다.
3. 특정 정책-기술분류 셀로 내려가 내용을 확인한다.

## 정보 구조

새 UI는 아래 5개 영역으로 고정한다.

### 1. `MappingHeader`

역할:

- 현재 데이터셋 범위와 매핑 품질을 요약
- 사용자가 지금 보는 범위가 `전체`, `필터 결과`, `검토 완료 범위` 중 어디인지 즉시 이해하게 함

핵심 KPI:

- 정책 수
- 14개 기술 대분류 중 매핑이 존재하는 대분류 수
- 매핑된 대표 그룹 수
- 매핑된 대표 내용 수
- 미매핑 대표 내용 수
- 검토 완료 비율 또는 검토 필요 개수

### 2. `MappingFilterBar`

역할:

- 매트릭스를 좁히는 전역 필터
- drill-down 이전의 탐색 조건 설정

필수 필터:

- 검색어
- 정책
- 전략
- 자원유형
- 기술 대분류
- 기술 중분류
- 매핑 상태: `mapped`, `unmapped`, `all`
- 검토 상태: `reviewed`, `needs_review`, `all`

보조 컨트롤:

- 정렬 기준: 정책 순서, 매핑 내용 수, 미매핑 수
- 행 밀도: compact, default
- 초기화 버튼

### 3. `PolicyTechMatrixBoard`

역할:

- 이 화면의 핵심
- 정책과 기술 대분류의 관계를 한 번에 보여주는 주 작업면

행:

- 정책

열:

- 14개 기술 대분류
- 선택적으로 맨 오른쪽에 `미매핑` 고정 열 추가

셀에서 보여줄 것:

- 대표 그룹 수
- 대표 내용 수
- 필요하면 근거 수
- 자원유형 혼합 정도
- 검토 필요 상태

셀 표현 원칙:

- 색 농도는 `대표 내용 수` 기준
- 셀 모서리 또는 배지는 `검토 필요` / `근거 부족` 상태 표시
- 셀 내부 숫자는 `G / C` 또는 `C / E` 중 하나로 통일

고정 영역:

- 상단 기술 대분류 헤더는 sticky
- 좌측 정책 헤더는 sticky
- `미매핑` 열은 가급적 우측 고정

### 4. `CellInspectorPanel`

역할:

- 현재 선택된 `정책 x 기술대분류` 셀을 해석하는 상세 패널

패널 상단 요약:

- 정책명
- 기술 대분류명
- 연결 전략 태그
- 대표 그룹 수
- 대표 내용 수
- 미검토 수
- 대표 자원유형 비중

패널 본문 탭:

#### `Contents`

- 해당 셀에 속한 `PolicyItemContent` 목록
- 각 항목에서 보여줄 것:
  - 내용 라벨
  - 짧은 요약
  - 상위 그룹명
  - 자원유형
  - 전략 태그
  - 기술 중분류 태그
  - 근거 수
  - 검토 상태

#### `Groups`

- 같은 기술분류 아래 대표 그룹을 묶어서 보여줌
- 그룹 단위 분류 타당성 검토에 유리

#### `Gaps`

- 선택 정책 안에서 해당 기술분류와 유사하지만 아직 미매핑 또는 검토 필요인 내용
- 자동 분류 결과 점검용

### 5. `EvidenceTraceDrawer`

역할:

- 선택된 대표 내용의 provenance 확인
- 지금까지의 trace panel은 이 영역으로 흡수한다

구성:

- content statement
- 연결 근거 목록
- representation 유형
- source asset 목록
- 원문 preview

규칙:

- 기본은 collapsed
- content를 고르면 열림
- matrix 화면을 가리지 않도록 side drawer 또는 bottom drawer 형태 권장

## 화면 구조

### 데스크톱

권장 레이아웃:

```text
+-----------------------------------------------------------------------------------+
| MappingHeader                                                                     |
+-----------------------------------------------------------------------------------+
| MappingFilterBar                                                                  |
+-----------------------------------------------------------------------------------+
| PolicyTechMatrixBoard                         | CellInspectorPanel                 |
|                                               |                                   |
|                                               |                                   |
|                                               |                                   |
+-----------------------------------------------------------------------------------+
| EvidenceTraceDrawer                                                               |
+-----------------------------------------------------------------------------------+
```

핵심 원칙:

- 첫 화면의 시선은 무조건 매트릭스로 먼저 가야 한다.
- 상세 패널이 매트릭스를 이기면 안 된다.
- trace는 세 번째 단계다.

### 태블릿

- 매트릭스는 상단
- Inspector는 하단 접이식 패널
- Evidence는 full-width drawer

### 모바일

- 표를 그대로 축소하지 않는다.
- `정책 카드 -> 기술대분류 칩/행 -> 내용 목록` 구조로 재배치한다.
- 모바일은 matrix의 시각적 동형보다 탐색 효율을 우선한다.

## 상호작용 설계

### 초기 상태

- 전체 정책
- 전체 기술 대분류
- `mapped` 우선
- 정렬은 정책 원래 순서
- 첫 셀은 자동 선택하지 않고 전체 분포를 먼저 보여준다

즉 첫 진입에서는 특정 셀 상세보다 전체 맵이 먼저 보여야 한다.

### 정책 헤더 클릭

- 해당 정책 행 강조
- Inspector에 정책 요약 표시
- 필요 시 row solo mode 진입

### 기술 대분류 헤더 클릭

- 해당 열 강조
- Inspector에 기술 대분류 설명, 연결 정책 목록 표시
- 기술분야 개요 문서 링크 노출

### 셀 클릭

- Inspector를 `정책 x 기술대분류` 상세 상태로 전환
- 해당 셀의 group/content 목록 표시

### content 클릭

- EvidenceTraceDrawer 오픈
- 근거, representation, 원문 자산 표시

### 미매핑 열 클릭

- 해당 정책에서 아직 기술 대분류가 붙지 않은 content 목록 표시
- 분류 누락 검토 작업에 직접 연결

## 시각 언어

이 화면은 보고서형 카드 모음이 아니라 분석 작업면이어야 한다.

### 시각 원칙

- 배경보다 데이터 격자가 먼저 읽혀야 한다.
- 기술 대분류 열 구분은 색보다는 구조와 타이포로 구분한다.
- 셀 색상은 의미가 하나여야 한다.
  - 권장: `대표 내용 수` 또는 `매핑 강도`
- 상태 배지는 별도로 분리한다.
  - `review`
  - `gap`
  - `evidence`

### 색상 원칙

- 기술 대분류마다 고유 색을 강하게 주지 않는다.
  - 14개 열에 서로 다른 색을 주면 시각적 노이즈가 과해진다.
- 대신 선택 상태, 경고 상태, 미매핑 상태만 강하게 분리한다.

### 타이포 원칙

- 정책명은 행 헤더에서 가장 크게
- 기술 대분류명은 짧은 한글 라벨 + 약어 병기 가능
- 셀 수치는 모노스페이스 숫자로 통일

## 상태 설계

### 데이터 상태

- `dataset`
- `policyMatrixRows`
- `techDomainColumns`
- `matrixCells`
- `unmappedRows`
- `domainReferenceMap`

### UI 상태

- `search`
- `activePolicyId`
- `activeTechDomainId`
- `activeStrategyId`
- `activeResourceCategoryId`
- `mappingStatus`
- `reviewStatus`
- `activeCellKey`
- `activeContentId`
- `matrixDensity`
- `sortKey`

### URL 상태

- `q`: 검색어
- `policy`: 선택 정책
- `domain`: 선택 기술 대분류
- `strategy`: 전략
- `resource`: 자원유형
- `mapping`: 매핑 상태
- `review`: 검토 상태
- `content`: 선택 대표 내용
- `density`: matrix 밀도
- `sort`: 정렬 기준

## selector 설계

기존 selector는 `active policy` 기준으로 내용 행을 만드는 방향이었다.
새 selector는 아래 파생 집계를 우선 제공해야 한다.

- `getPolicyTechMatrixRows`
- `getPolicyTechMatrixColumns`
- `getPolicyTechCell(policyId, techDomainId)`
- `getSelectedCellContents`
- `getSelectedCellGroups`
- `getUnmappedContentsByPolicy`
- `getTechDomainCoverageSummary`
- `getPolicyCoverageSummary`

## 데이터 계약 보완

현재 `curated content sample pack`만으로도 1차 UI는 만들 수 있지만, 아래 필드가 있으면 selector가 크게 단순해진다.

### 필수 추가 필드

- `primary_tech_domain_id`
- `primary_tech_domain_label`
- `tech_domain_ids`
- `tech_subdomain_ids`
- `mapping_status`
- `review_status`
- `evidence_ready`
- `content_count_by_policy_and_domain`
- `group_count_by_policy_and_domain`

### 권장 요약 마트

프런트가 raw nested pack만 직접 집계하기보다 아래 마트를 함께 읽는 편이 낫다.

#### `policy_tech_matrix.json`

행 단위 예시:

- `policy_id`
- `policy_name`
- `tech_domain_id`
- `tech_domain_label`
- `group_count`
- `content_count`
- `evidence_count`
- `unmapped_count`
- `reviewed_count`
- `needs_review_count`
- `resource_mix`

#### `policy_tech_cell_contents.json`

- `policy_id`
- `tech_domain_id`
- `policy_item_group_id`
- `policy_item_content_id`
- `content_label`
- `content_summary`
- `resource_category_id`
- `strategy_term_ids`
- `tech_subterm_ids`
- `evidence_count`
- `review_status`

#### `tech_domain_reference.json`

- `tech_domain_id`
- `tech_domain_label`
- `definition`
- `context_document_links`

## 컴포넌트 구조 제안

```text
modules/dashboard-ui/
  MappingWorkbenchPage.tsx
  MappingHeader.tsx
  MappingFilterBar.tsx
  PolicyTechMatrixBoard.tsx
  PolicyTechMatrixCell.tsx
  CellInspectorPanel.tsx
  ContentList.tsx
  EvidenceTraceDrawer.tsx
```

기존 컴포넌트의 처리 방향:

- `DashboardHeader` -> `MappingHeader`로 대체
- `FilterBar` -> `MappingFilterBar`로 확장
- `PolicyRail` 제거
- `EvidenceBoard` 제거 후 `PolicyTechMatrixBoard`로 대체
- `TracePanel`은 `EvidenceTraceDrawer`로 축소 이관

## 1차 출시 범위

### 반드시 포함

- 정책 x 기술 대분류 매트릭스
- 셀 클릭 상세
- 대표 내용 목록
- 원문 근거 drawer
- 미매핑 열
- 전략/자원유형 필터

### 있으면 좋음

- 기술 대분류 설명 패널
- 검토 상태 토글
- 셀 hover preview

### 2차로 미룸

- 해외 비교
- 시계열 비교
- 기관별 보기
- 대형 차트 라이브러리

## 구현 순서

1. 현재 `DashboardWorkbenchPage`를 유지한 채 selector에서 matrix mart 생성
2. 새 `MappingWorkbenchPage` 골격 구현
3. 기존 trace panel 기능을 drawer로 이동
4. policy rail/evidence board 제거
5. full sample 또는 12정책 범위 데이터로 QA

## 설계 검증 체크리스트

- 첫 화면에서 정책과 기술 대분류의 관계를 바로 읽을 수 있는가
- 특정 셀에서 실제 대표 내용과 근거까지 2단계 이내로 내려갈 수 있는가
- 미매핑과 검토 필요 상태가 숨지지 않는가
- 샘플 데이터가 작아도 구조가 붕괴하지 않는가
- 12개 정책 x 14개 대분류가 들어와도 레이아웃이 유지되는가

## 결론

이 프런트엔드의 중심은 더 이상 `trace-first content table`이 아니다.

1차 화면의 정체성은 아래 한 줄로 고정한다.

`정책별 세부 내용을 14개 기술 대분류에 매핑해 읽고, 필요한 경우에만 근거 trace로 내려가는 분석 작업면`
