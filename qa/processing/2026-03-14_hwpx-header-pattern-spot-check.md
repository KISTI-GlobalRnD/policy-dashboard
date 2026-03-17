# HWPX Header Pattern Spot Check

## 대상

- `DOC-POL-002`
- `DOC-POL-004`
- `DOC-POL-005`

## 점검 목적

- phase1 정책 문헌 HWPX 산출물의 선두 cover/header 공통 패턴 확인
- pure text 본문 검토 전에 공통 제거 가능한 노이즈 식별

## 관찰 결과

- 세 문서 모두 첫 블록에 standalone `공개` heading이 있었다.
- 이 `공개`는 문서 본문 의미가 아니라 cover marker에 해당한다.
- 그 외 첫 구간은 `Ⅰ. 의결주문`, `Ⅱ. 제안이유`, `Ⅲ. 주요 내용` 등 본문 heading으로 바로 연결된다.

## 반영 규칙

- `normalize_structured_text_blocks.py`에서 선두 heading이 `공개` 또는 `대외비`이면 제거

## 반영 후 결과

- `DOC-POL-002`: `240 -> 239`
- `DOC-POL-004`: `196 -> 195`
- `DOC-POL-005`: `477 -> 476`
- 동일 규칙을 나머지 phase1 HWPX 문서에도 재적용

## 판단

- HWPX pure text 기준으로 선두 cover marker 제거는 low-risk 공통 규칙이다.
- 다음 공통 점검 대상은 반복 citation, 부처 표기, 주석 라인 연결 여부다.
