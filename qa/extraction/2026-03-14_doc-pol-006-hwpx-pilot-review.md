# DOC-POL-006 HWPX Pilot Review

## 대상

- 기준 문서: `DOC-POL-006` `초혁신경제 15대 프로젝트 추진계획`
- 비교 원본:
  - PDF: `data/260312_12개 정책 문헌 자료/251216_(안건) 초혁신경제 15대 프로젝트 추진계획 IV.pdf`
  - HWPX: `data/260312_12개 정책 문헌 자료/251216_(안건) 초혁신경제 15대 프로젝트 추진계획 IV.hwpx`
- 파일럿 문서 ID: `DOC-POL-006-HWPX`

## 실행 경로

- HWPX 추출기: `scripts/extract_hwpx_from_zip.py`
- HWPX 정규화: `scripts/normalize_structured_text_blocks.py`

## 산출물

- `work/02_structured-extraction/manifests/DOC-POL-006-HWPX_manifest.json`
- `work/02_structured-extraction/text/DOC-POL-006-HWPX_blocks.json`
- `work/03_processing/normalized/DOC-POL-006-HWPX__paragraphs.json`
- `work/03_processing/normalized/DOC-POL-006-HWPX__text-normalization-report.json`

## 결과 요약

- HWPX 기준:
  - `page_count_or_sheet_count 1`
  - `evidence_units 494`
  - `tables 0`
  - `figures 0`
  - 정규화 `paragraph_count 490`
  - `skipped_noise_count 4`
- PDF 기준:
  - `page_count 38`
  - `evidence_units 1026`
  - `pages_with_tables_markdown 10`
  - `pages_with_images_markdown 6`
  - 정규화 `paragraph_count 504`

## 관찰

- 변환 HWPX는 유효한 파일이며 본문 문단 자체는 잘 읽힌다.
- 다만 내부 구조는 사실상 `section0` 하나뿐이라 페이지 provenance가 없다.
- 표 객체와 그림 객체가 모두 `0`이므로, 구조형 원본이라고 보기 어렵다.
- 즉 현재 HWPX는 본문만 보존한 flattened 변환본에 가깝다.

## 판단

- `DOC-POL-006`에서 HWPX는 `pure text reference`로는 사용 가능하다.
- 그러나 표, 그림, 페이지 근거가 필요한 canonical source로는 부적합하다.
- 따라서 이 문서는 `본문 참조본 = HWPX`, `canonical 근거/표 = PDF`로 운용하는 것이 맞다.

## 다음 단계

1. `DOC-POL-006` canonical 문서 ID는 계속 PDF 기준으로 유지
2. 문장 내부 띄어쓰기나 paragraph boundary 검토가 필요할 때만 HWPX를 참조
3. 표와 그림 review/canonical table은 기존 PDF 산출물을 계속 사용
