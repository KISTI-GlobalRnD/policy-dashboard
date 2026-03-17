# Phase1 Footnote Link Audit

## 목적

- pure text 정규화 후 `본문 * 표시`와 다음 `note` 줄의 연결 관계를 점검
- 자동 정규화로 충분한 문서와 원문 재확인이 필요한 문서를 구분

## 문서별 연결 note 수

- `DOC-POL-002`: 3
- `DOC-POL-004`: 5
- `DOC-POL-005`: 11
- `DOC-POL-007`: 4
- `DOC-POL-008`: 0
- `DOC-POL-009`: 15
- `DOC-POL-010`: 1
- `DOC-POL-011`: 0
- `DOC-POL-012`: 2

## 판단

- `DOC-POL-002`, `005`, `007`, `009`, `012`의 note는 대부분 직전 문장에 대한 통계·보충 설명으로 읽히며, `note` 분류만으로도 pure text 검토에는 충분하다.
- `DOC-POL-004`, `DOC-POL-010`의 문제는 정규화가 아니라 HWPX inline tail 누락이었다.
- 추출기 수정 후 두 문서의 note는 원문 기준으로 복원됐고, 현재는 별도 우선 점검 대상이 아니다.

## 짧은 ambiguous note

- `DOC-POL-002`: `* 예쁜꼬마선충, 초파리 등`
- `DOC-POL-005`: `* 범부처 통합 예산 투자 적용`
- `DOC-POL-007`: 추출기 수정 후 `* 자동차, IoT · 가전, 기계 · 로봇, 방산 등 4대 분야`로 복원

## 우선 수동 점검 대상

1. 별도 footnote 수동 점검 필요성은 낮음
2. 나머지는 현 단계에서는 `note` 유지로 충분

## 결론

- phase1 pure text 경로에서 footnote anchor 자체는 공통 패턴으로 안정적이다.
- 남은 리스크는 footnote가 아니라 `DOC-POL-006` PDF 문장 복원과 figure-adjacent 영역 쪽에 더 가깝다.
