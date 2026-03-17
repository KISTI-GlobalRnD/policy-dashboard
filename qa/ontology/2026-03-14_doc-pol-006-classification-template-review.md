# DOC-POL-006 Classification Template Review

## 대상

- 문서 ID: `DOC-POL-006`
- 입력 문단 파일: `work/03_processing/normalized/DOC-POL-006__paragraphs.json`

## 출력

- `work/04_ontology/instances/DOC-POL-006__classification-template.csv`
- `work/04_ontology/instances/DOC-POL-006__classification-template-summary.json`

## 결과 요약

- 문단 수: 504
- `policy_item_candidate = yes`: 242
- `policy_item_candidate = review`: 129
- `policy_item_candidate = no`: 133
- 자원유형 자동 제안 수: 186
- 전략 자동 제안 수: 113
- 기술분야 자동 제안 수: 56
- 기술 중분류 자동 제안 수: 40

## 확인 사항

- cover title, 요약 title, `순 서`, `참고. 15대 프로젝트 세부 일정 (Ⅳ)` 같은 목차성 문구는 `no`로 내려갔다.
- `citation`, `note`, `caption`, `table_markdown`은 `review` 상태로 남겨 후속 판단 여지를 확보했다.
- `(1) 우리의 현주소`, `(단위: 백만원, 개)`, `➊세계선도전략기술육성,` 같은 scaffold 문구도 `no`로 보정됐다.
- 자원유형 자동 제안은 키워드 기반 약한 제안으로만 동작한다.
- 전략, 기술분야, 중분류는 자동 확정이 아니라 제안값과 confidence만 채운다.
- `auto_suggestion_notes`에 점수와 front matter 필터 근거가 남는다.

## 남은 이슈

- `개발` 같은 일반 키워드 때문에 `technology` 제안이 과하게 붙는 행이 있다.
- 문서 제목 prior를 쓰기 때문에 특정 문서에서는 전략/기술분야 제안이 넓게 붙는다.
- `초혁신경제 15대 프로젝트 추진계획`처럼 종합 문서는 전략/기술분야 제안률이 상대적으로 낮다.
- `□ 복합위기 속 잠재성장률 하락...`, `- 초혁신경제로의대전환`, `시급히지원해야할프로젝트건의` 같은 짧은 scaffold/목차성 문구가 아직 `yes`로 남는다.
- 현재 `yes`는 정밀 선별 결과가 아니라 `후보를 넓게 잡는 작업지` 수준이다.
- 줄바꿈 병합으로 본문 문단 수가 달라질 수 있으므로, 정규화 직후 순차 재생성이 필요하다.

## 판단

현재 템플릿은 `넓게 후보를 잡는 검토 작업지`로는 쓸 수 있다.
다만 `yes` 집합을 바로 policy item으로 간주하기에는 아직 이르고, 다음 단계는 짧은 scaffold 제거와 policy item 단위 병합이다.
