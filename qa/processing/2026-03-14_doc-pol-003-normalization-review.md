# DOC-POL-003 Normalization Review

## 대상

- 문서 ID: `DOC-POL-003`
- 제목: `제조AX 추진방향`
- 원문 형식: `HWPX`
- 산출물:
  - `work/03_processing/normalized/DOC-POL-003__pages-clean.json`
  - `work/03_processing/normalized/DOC-POL-003__paragraphs.json`
  - `work/03_processing/normalized/DOC-POL-003__text-normalization-report.json`

## 적용한 정리 규칙

- cover metadata 제거
- HWPX block 순서를 유지한 문단 단위 정리
- `*`, `**` 계열 보조설명 note 재분류
- short label/heading 보정
- `⦁`, `◦` bullet 표지 인식

## 결과

- 추출 evidence unit: `133`
- 정규화 문단 수: `132`
- 시작부는 `Ⅰ. 의결주문`, `Ⅱ. 제안이유`, `Ⅲ. 주요 내용`, `□ 추진 배경` 순으로 안정화됐다.
- 제조 AX 3대 전략과 추진과제가 초기 구간에서 연속 bullet 구조로 정리된다.
- note와 bullet 경계가 legacy HWP 시절보다 자연스럽다.
- 정규화 보고서 기준 `merge_count`는 `0`이다.
- 구조 추출 기준으로 표 `41`, 그림 `10`이 별도 보존된다.

## 남은 이슈

- section 기반 provenance라 PDF처럼 페이지 번호가 직접 복원되지는 않는다.
- 일부 문장에는 `해외인수병원을거점으로` 같은 내부 공백 손상이 남을 수 있다.
- 표/그림 자체는 아직 canonical review를 하지 않았다.

## 판단

- pure text 초벌 검토용으로는 충분히 usable
- 구조화 품질은 더 이상 legacy HWP 예외 문서 수준이 아니다.
- phase1 정책 텍스트화 경로에서는 일반 HWPX 문서로 관리해도 된다.
