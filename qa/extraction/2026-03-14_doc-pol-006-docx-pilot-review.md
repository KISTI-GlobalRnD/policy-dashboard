# DOC-POL-006 DOCX Pilot Review

## 대상

- 기준 문서: `DOC-POL-006` `초혁신경제 15대 프로젝트 추진계획`
- 비교 원본:
  - PDF: `data/260312_12개 정책 문헌 자료/251216_(안건) 초혁신경제 15대 프로젝트 추진계획 IV.pdf`
  - DOCX: `data/260312_12개 정책 문헌 자료/251216_(안건) 초혁신경제 15대 프로젝트 추진계획 IV.docx`
- 파일럿 문서 ID: `DOC-POL-006-DOCX`

## 실행 경로

- DOCX 추출기: `scripts/extract_docx_text.py`
- DOCX 정규화: `scripts/normalize_structured_text_blocks.py`

## 산출물

- `work/02_structured-extraction/manifests/DOC-POL-006-DOCX_manifest.json`
- `work/02_structured-extraction/text/DOC-POL-006-DOCX_blocks.json`
- `work/03_processing/normalized/DOC-POL-006-DOCX__paragraphs.json`
- `work/03_processing/normalized/DOC-POL-006-DOCX__text-normalization-report.json`

## 비교 요약

- PDF 기준:
  - `page_count 38`
  - `evidence_units 1026`
  - `tables 10`
  - `figures 6`
  - 정규화 `paragraph_count 482`
  - `merge_count 360`
- DOCX 기준:
  - `section_count 43`
  - `evidence_units 501`
  - `tables 9`
  - `figure_occurrences 63`
  - `unique_figure_assets 46`
  - 정규화 `paragraph_count 501`
  - `merge_count 0`

## 강점

- DOCX는 일부 문장 내부 띄어쓰기가 PDF보다 자연스럽다.
  - 예: `전문가 의견`, `글로벌 탑티어 해외 석학 30명 유치 추진`, `AI 도구 구독비 지원 신설`
- DOCX는 구조형 문서처럼 paragraph 단위가 이미 살아 있어 bbox 병합 규칙이 거의 필요 없다.
- 표도 별도 객체로 추출 가능하다.

## 약점

- DOCX는 page provenance가 아니라 section provenance만 안정적이다.
  - PDF처럼 페이지 기준 근거 연결이 어렵다.
- 변환 과정에서 일부 구간이 과도하게 합쳐진다.
  - 예: `① (기존)ICT 기반 의료시스템 ... ② (신규) ...`가 하나의 긴 heading/paragraph로 붙는다.
- 장표/도식 인접 구간은 PDF보다 더 큰 mega-paragraph가 생긴다.
  - 일정표, 참고 도식 구간에서 압축 현상이 크다.
- figure count가 과도하게 커진다.
  - `63`회 참조지만 실제 asset은 `46`개이며, 같은 자산이 반복 참조되는 경우가 많다.
- 현재 DOCX 추출은 converted DOCX 특성을 그대로 받기 때문에, figure/table canonical review에는 추가 보정이 필요하다.

## 판단

- 현재 기준에서는 `DOCX가 PDF를 대체하지는 못한다`.
- 하지만 `문장 내부 띄어쓰기 보조 소스`로는 가치가 있다.
- 따라서 `DOC-POL-006`은 여전히 PDF를 주 경로로 유지하고, DOCX는 보조 비교본 또는 spacing repair reference로 쓰는 편이 맞다.

## 다음 단계

1. PDF 주 경로 유지
2. DOCX는 `spacing repair`가 필요한 문장 비교용으로 한정 사용
3. DOCX를 주 경로로 올리려면 section/page 재구성, 중복 image dedupe, heading over-merge 완화가 먼저 필요
