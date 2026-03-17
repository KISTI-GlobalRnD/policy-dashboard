# HWPX Inline Tail Fix Review

## 목적

- HWPX 원문 안의 inline control(`hp:fwSpace`, `hp:lineBreak`, `hp:tab`) 뒤 tail text 누락 여부 점검
- pure text 본문과 footnote truncation의 원인이 추출기인지 확인

## 원인

- 기존 `extract_hwpx_from_zip.py`는 `hp:t` 내부 텍스트는 읽었지만, child element 뒤 `tail` 텍스트를 이어붙이지 않았다.
- 그 결과 `fwSpace` 뒤에 오는 문구가 잘리면서 일부 footnote가 비정상적으로 짧아졌다.

## 수정

- `collect_text_excluding()`에서
  - `hp:fwSpace -> " "`
  - `hp:lineBreak -> "\\n"`
  - `hp:tab -> "\\t"`
  - `child.tail` 보존

## 검증 샘플

- `DOC-POL-004`
  - 수정 전: `* ▲ 활용분의 15~20%(’26~), ▲`
  - 수정 후: `* ▲ 슈퍼컴 6호기 8,500개의 약 30%(‘26.上~), ▲ 첨단GPU확보사업 2.8만개 중 정부 활용분의 15~20%(’26~), ▲ 대학 기초연구 전용 GPU 약 300개(’26.下) 등`
- `DOC-POL-004`
  - 수정 전: `* 공공형 연구 인프라 제공`
  - 수정 후: `* 공공형 연구 인프라 제공 + 민간 서비스 육성 Two-track 전략 추진`
- `DOC-POL-010`
  - 수정 전: `* 연구직`
  - 수정 후: `* 연구직 1명당 지원인력 수(명) : (NST) 0.5 / (獨, MPG) 1.3 / (佛, CNRS) 1.2 / (日, AIST) 0.96`

## 배치 반영

- phase1 정책 문서 text-first 배치 재실행
- phase1 정책 문서 normalization 배치 재실행

## 판단

- 이번 이슈는 정규화 규칙 문제가 아니라 HWPX XML 추출기 결함이었다.
- 현재 phase1 HWPX pure text 경로에서 footnote truncation 리스크는 크게 낮아졌다.
