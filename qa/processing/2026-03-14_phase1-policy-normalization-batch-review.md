# Phase1 Policy Normalization Batch Review

## 대상

- 범위: phase1 정책 문서 11건
- 배치 결과:
  - `work/03_processing/normalized/batch_runs/2026-03-14_phase1-policy-normalization-batch.json`
  - `work/03_processing/normalized/batch_runs/2026-03-14_phase1-policy-normalization-batch.csv`

## 결과 요약

- 정규화 완료: 11건
- 실패: 0건

## 형식별 판단

### PDF

- `DOC-POL-006`은 가장 성숙한 텍스트 경로다.
- 줄바꿈 병합, 표 분리, paragraph 작업지가 이미 갖춰져 있다.
- page 1 cover metadata 제거, 반복 `현장의 목소리` heading suppression, star footnote note화까지 반영됐다.
- 가운데점 주변의 비정상 공백과 반복 문장형 밀착 표현도 low-risk 범위에서 정리했다.
- 디지털헬스/바이오 구간의 `정책지원 방안 마련`, `금융지원 방안 마련`, `해외진출 기반 조성`, `현지 인수․진출 병원` 같은 반복 정책 문구도 추가 정리했다.
- page 21, 27의 `③(글로벌 진출 지원)`, `❷(정책 패키지)` 같은 inline 소제목은 별도 블록으로 분리됐다.
- `TBL-*.json`이 없는 경우에도 page chunk의 table bbox를 fallback으로 읽어 pure text 표 overlap 제외를 유지한다.
- `table_markdown`은 본문 spacing 보정 대상에서 제외했다.
- 최신 문단 수는 `DOC-POL-006 504`이다.

### HWPX

- `DOC-POL-002`, `004`, `005`, `007`~`012`는 본문 문단 기준으로 바로 읽을 수 있는 수준이다.
- `DOC-POL-003`도 HWPX 원문 전환 후 이 그룹에 합류했다.
- 구조상 표/그림 객체는 많이 추출되지만, 현재는 본문 텍스트 검토를 먼저 해도 무방하다.
- 공통 선두 cover marker였던 `공개`는 제거 규칙을 적용해 배치 재생성했다.
- `*` / `**` 계열 보조설명은 `note`로 재분류했다.
- multiline structured block은 내부 줄바꿈을 접합하고, `☞ 개선방향`처럼 새 marker로 시작하는 줄은 별도 문단으로 분리한다.
- marker-only `ㅇ`, `□`, `☞`, `⇒` 조각은 noise로 제거한다.
- HWPX 추출기에서 inline control tail 누락을 복구해 footnote truncation을 해소했다.
- `DOC-POL-003`은 HWPX 기준 `paragraph_count 132`, `tables 41`, `figures 10`으로 재생성됐다.
- `DOC-POL-005`, `DOC-POL-007`, `DOC-POL-009` spot check 결과 embedded newline은 0건이다.
- 최신 문단 수는 `DOC-POL-002 239`, `DOC-POL-003 132`, `DOC-POL-004 195`, `DOC-POL-005 485`, `DOC-POL-007 261`, `DOC-POL-008 100`, `DOC-POL-009 292`, `DOC-POL-010 185`, `DOC-POL-011 65`, `DOC-POL-012 98`이다.
- 현재 HWPX pure text 쪽에서 별도 blocker는 크지 않다.

## 문서별 메모

- `DOC-POL-002`: 본문 구조 양호
- `DOC-POL-003`: HWPX 전환 반영, 본문 구조 양호
- `DOC-POL-004`: 본문 구조 양호
- `DOC-POL-005`: 본문 구조 양호, 분량 큼
- `DOC-POL-005`: `현장의견` / `☞ 개선방향` 분리 반영
- `DOC-POL-006`: 본문 정규화 심화 진행 중
  - 현재 남은 리스크는 초기 페이지 압축 표현과 figure-adjacent 영역
- `DOC-POL-007`: 본문 구조 양호
- `DOC-POL-008`: 본문 구조 양호
- `DOC-POL-009`: 본문 구조 양호
- `DOC-POL-009`: 고립 `ㅇ` marker 제거 반영
- `DOC-POL-010`: 본문 구조 양호
- `DOC-POL-011`: 분량 짧음, 본문 구조 양호
- `DOC-POL-012`: heading 비중 높음, 본문 구조는 읽을 수 있음

## 다음 우선순위

1. `DOC-POL-006` 내부 띄어쓰기와 figure-adjacent 영역 점검
2. `DOC-POL-003` 표/도형 canonical review 준비
3. 그 뒤에야 표/그림 review queue를 별도 운영
