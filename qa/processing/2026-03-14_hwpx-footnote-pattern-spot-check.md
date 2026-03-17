# HWPX Footnote Pattern Spot Check

## 대상

- `DOC-POL-002`
- `DOC-POL-004`
- `DOC-POL-005`
- 보조 확인: `DOC-POL-010`

## 점검 목적

- phase1 HWPX 문서에서 `*` / `**` 계열 보조 설명 라인의 공통 처리 기준 확정
- pure text 본문 검토 전에 명백한 조각 노이즈 제거 가능 여부 확인

## 공통 관찰

- `*`, `**`로 시작하는 라인은 대부분 직전 문장의 각주·보충 설명에 해당한다.
- 따라서 본문 bullet보다 `note`로 분류하는 편이 더 적합하다.
- `DOC-POL-005`의 부처 목록, `DOC-POL-002`의 통계 보충, `DOC-POL-010`의 설명 보충은 모두 note로 두어도 의미 손실이 없다.
- HWPX 원문 안의 `hp:fwSpace` 뒤 tail text가 누락되면 note가 비정상적으로 짧아질 수 있다.

## 추출기 보정

- `extract_hwpx_from_zip.py`에서 `hp:fwSpace`, `hp:lineBreak`, `hp:tab` 뒤 tail text를 보존하도록 수정했다.
- 이 수정으로 `DOC-POL-004`, `DOC-POL-010`의 잘린 note가 원문 수준으로 복원됐다.
  - `* ▲ 슈퍼컴 6호기 8,500개의 약 30%(‘26.上~), ▲ 첨단GPU확보사업 2.8만개 중 정부 활용분의 15~20%(’26~), ▲ 대학 기초연구 전용 GPU 약 300개(’26.下) 등`
  - `* 공공형 연구 인프라 제공 + 민간 서비스 육성 Two-track 전략 추진`
  - `* 연구직 1명당 지원인력 수(명) : (NST) 0.5 / (獨, MPG) 1.3 / (佛, CNRS) 1.2 / (日, AIST) 0.96`

## 반영 결과

- `normalize_structured_text_blocks.py`
  - `*` / `**` 시작 라인 -> `note`
  - `* ①`, `* ▲`, `<` 계열 -> 제거
- 추출기 재실행 후 `DOC-POL-004` 문단 수는 `195`로 복원됐다.
- 현재 `DOC-POL-004`, `DOC-POL-010`의 note는 삭제 대상이 아니라 복원된 보충 설명으로 본다.

## 남은 이슈

- `DOC-POL-002`의 `* 예쁜꼬마선충, 초파리 등`
- `DOC-POL-005`의 `* 범부처 통합 예산 투자 적용`
- 위 두 건은 원문 HWPX에서도 동일한 standalone note라서 truncation이 아니다.
- `DOC-POL-007`의 `* 자동차, IoT` 유형은 추출기 보정 후 `* 자동차, IoT · 가전, 기계 · 로봇, 방산 등 4대 분야`로 복원됐다.

## 판단

- HWPX pure text 기준에서 `별표 라인 -> note`와 `inline control tail 보존`은 필수 공통 규칙이다.
- 현재 phase1 HWPX footnote truncation 이슈는 사실상 닫혔다.
- 다음 과제는 HWPX가 아니라 `DOC-POL-006` PDF 줄바꿈 품질과 잔여 내부 띄어쓰기 쪽이다.
