# DOC-POL-006 Text Normalization Review

## 대상

- 문서 ID: `DOC-POL-006`
- 문서명: `초혁신경제 15대 프로젝트 추진계획`

## 입력

- `work/02_structured-extraction/text/DOC-POL-006_pages.json`

## 출력

- `work/03_processing/normalized/DOC-POL-006__pages-clean.json`
- `work/03_processing/normalized/DOC-POL-006__paragraphs.json`
- `work/03_processing/normalized/DOC-POL-006__paragraphs.csv`
- `work/03_processing/normalized/DOC-POL-006__text-normalization-report.json`

## 결과 요약

- 페이지 수: 38
- 문단 수: 504
- 본문 문단 수: 494
- 제거된 푸터 수: 41
- 병합된 연속 블록 수: 363
- 표 Markdown 블록 수: 10
- 고립 marker 토큰: 0
- 표 bbox overlap으로 제외된 블록 수: 139
- 후처리에서 제거된 cover/중복 heading/noise 수: 17

## 확인 사항

- bbox text block을 기준으로 본문을 다시 재구성했다.
- 페이지 하단 쪽번호가 제거됐다.
- Markdown 표는 일반 문단으로 풀지 않고 유지됐다.
- 표 bbox와 겹치는 셀 텍스트는 pure text에서 제외됐다.
- 하나의 raw block 안에 섞여 있던 불릿은 추가 분리됐다.
- marker-only 라인(`➌`, `ㅇ`, `❶ ❷`)은 제거됐다.
- 공간 제약으로 쪼개진 같은 줄 조각과 연속 본문은 bbox 정렬 기준으로 추가 병합됐다.
- 페이지 2의 `□｢ ... ｣` 계열 조각과 페이지 26의 `② 신규...` 소제목 오병합은 보정됐다.
- page 1의 회의명/날짜/`관계부처합동` cover metadata는 제거됐다.
- pages 17, 23, 29의 반복 `현장의 목소리` heading은 첫 heading만 남겼다.
- `*`, `**`, `***` 계열 보조설명은 bullet이 아니라 note로 재분류했다.
- `* *`, `** *`처럼 깨진 footnote marker는 `**`, `***`로 정규화했다.
- `□`, `ㅇ`, `▪` 계열 표기 간격은 low-risk 범위에서 정리했다.
- `재정·세제·금융· 규제개선`, `해외진출· 입지지원`, `국내중소· 벤처기업` 같은 가운데점 주변 공백은 low-risk 규칙으로 정리했다.
- `전문가의견 등을 통해 선정`, `관계부처 및 유관협회 및 기관`, `AI 도구 구독비 지원 신설`, `콘텐츠 제작지원 확대` 같은 반복 표현은 exact/fragment 치환으로 본문 쪽에서 정리했다.
- `국정과제와의 연계성`, `바이오헬스산업 전문인력 부족`, `ICT 기반 의료시스템 해외진출 기반 조성`, `현지 인수․진출 병원`, `정책지원 방안 마련`, `금융지원 방안 마련` 같은 정책 문구도 추가 exact 치환으로 정리했다.
- page 21, 27의 `중기부 협업`, `인허가 컨설팅`, `글로벌 액셀러레이팅 플랫폼`, `빅데이터 기반 디지털의료기기 연구개발을 통해` 같은 압축 표현을 추가 exact 치환으로 정리했다.
- `③(글로벌 진출 지원)`, `❷(정책 패키지)`, `❸ (금융지원)`, `❺ (성과확산)` 같은 inline 소제목은 별도 블록으로 분리했다.
- 기존 `TBL-*.json`이 없어도 `pages.json.tables[].bbox`를 fallback으로 읽어 table overlap 제외를 계속 적용한다.
- `table_markdown`은 본문 spacing 보정 대상에서 제외하고 원문 추출 상태를 유지한다.
- 결과가 JSON과 CSV 두 형태로 모두 저장됐다.

## 남은 이슈

- 문장 내부 공백은 아직 일부 남아 있다.
  - 예: `생산성정체로잠재성장률의지속적`, `기업을 중심으로한민관합동추진단`, `프로젝트추진계획 발표Ⅰ` 같은 초기 페이지 밀착 표현
- 반복 citation은 남아 있다.
  - 예: 페이지 17의 회의 출처 반복
- 도식/표 인접 영역은 여전히 heuristic merge 영향권이다.
  - 예: 페이지 30 전후의 도식 라벨 영역

## 판단

현재 결과는 `정책 항목 태깅 전 단계의 정제 텍스트`로는 사용 가능하다.
우선순위였던 `공간 제약 줄바꿈 병합`은 usable 수준을 넘어서 문장형 읽기 품질까지 상당 부분 올라왔다.
특히 page 21, 27의 디지털헬스·바이오 구간은 inline 소제목 분리까지 포함해 태깅 가능한 블록 구조에 가까워졌다.
다만 온톨로지 연결 전에는 잔여 압축 표현과 figure-adjacent 영역 정리가 한 번 더 필요하다.
