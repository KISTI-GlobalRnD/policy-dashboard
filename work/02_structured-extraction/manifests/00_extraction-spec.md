# 구조화 추출 명세 v0.1

## 목적

원문을 단순 텍스트가 아니라 재사용 가능한 구조 객체로 분해한다.

## 적용 범위

- PDF
- HWP
- HWPX
- XLSX

## 추출 원칙

- 원문은 수정하지 않는다.
- 추출 결과는 원문 근거를 반드시 남긴다.
- `텍스트`, `표`, `그림`, `레이아웃`을 분리 저장한다.
- 모든 객체는 문서 ID와 페이지 또는 시트 기준으로 추적 가능해야 한다.
- OCR 결과만 저장하지 말고 검토 가능한 품질 메타데이터를 함께 저장한다.

## 필수 출력 객체

### 1. 문서 매니페스트

저장 위치:
- `work/02_structured-extraction/manifests/`

필수 필드:
- `document_id`
- `registry_id`
- `source_rel_path`
- `internal_path`
- `source_format`
- `extraction_run_id`
- `page_count_or_sheet_count`
- `processing_status`
- `quality_notes`

### 2. 텍스트 블록

저장 위치:
- `work/02_structured-extraction/text/`

필수 필드:
- `evidence_id`
- `document_id`
- `page_no_or_sheet_name`
- `block_order`
- `block_type`
- `text`
- `bbox`
- `extraction_method`
- `extraction_confidence`

### 3. 표 객체

저장 위치:
- `work/02_structured-extraction/tables/`

필수 필드:
- `table_id`
- `document_id`
- `page_no_or_sheet_name`
- `table_title`
- `header_rows`
- `table_shape`
- `cell_matrix`
- `merged_cell_info`
- `source_bbox`
- `extraction_confidence`

### 4. 그림 객체

저장 위치:
- `work/02_structured-extraction/figures/`

필수 필드:
- `figure_id`
- `document_id`
- `page_no`
- `figure_type`
- `caption`
- `legend_text`
- `summary`
- `asset_path`
- `source_bbox`
- `extraction_confidence`

### 5. 레이아웃 메타데이터

저장 위치:
- `work/02_structured-extraction/layout/`

필수 필드:
- `document_id`
- `page_no`
- `page_width`
- `page_height`
- `blocks`

## 형식별 처리 기준

### PDF

- 우선 `텍스트 기반 PDF`와 `이미지 기반 PDF`를 구분한다.
- 텍스트 기반 PDF의 주 추출기는 `PyMuPDF4LLM`로 한다.
- 텍스트 기반 PDF는 `PyMuPDF4LLM` page chunk와 `PyMuPDF` bbox block을 함께 저장한다.
- 이미지 기반 PDF는 OCR 또는 비전 기반 추출을 수행하고 신뢰도를 남긴다.
- 표는 OCR 텍스트 한 덩어리로 저장하지 말고 셀 단위 구조를 남긴다.

### HWP/HWPX

- 가능한 경우 문단, 표, 이미지 객체를 분리 추출한다.
- 변환 HWPX는 내부 객체 수를 먼저 검증한다.
- `tables = 0`, `figures = 0`인데 본문 문단만 많은 경우, 구조 보존 실패로 간주한다.
- 이 경우 변환 HWPX는 `본문-only 참조본`으로만 쓰고, canonical 근거와 표/그림 추출은 원 PDF 또는 원 DOCX를 유지한다.
- 변환 과정에서 페이지 정보가 사라지면 블록 순서와 문단 ID를 보존한다.
- 표는 변환 후 CSV와 원래 위치 메타데이터를 함께 남긴다.

### XLSX

- 시트 단위로 구조화한다.
- 셀 값뿐 아니라 머리글 행, 병합 셀, 시트 이름을 보존한다.
- 기준표와 코드표 성격의 시트는 별도 태그를 단다.

## 표 처리 규칙

- 각 표는 독립 객체로 저장한다.
- 병합 셀과 다단 헤더를 보존한다.
- 셀 좌표는 최소 `row_index`, `col_index`로 남긴다.
- 표 제목이 없으면 인접 문장 또는 위치 기반 임시 이름을 부여한다.

## 그림 처리 규칙

- 그림은 최소 `캡션`, `범례`, `도식 유형`, `요약문`을 남긴다.
- 도표 유형 예시:
  - `chart`
  - `diagram`
  - `process_flow`
  - `timeline`
  - `map`
  - `photo`
- 축, 노드, 범주가 있으면 텍스트 요소를 별도 추출한다.

## 추출 품질 등급

- `A`: 구조와 텍스트가 거의 완전
- `B`: 일부 좌표 또는 표 구조 보정 필요
- `C`: OCR 의존도가 높고 수동 검토 필요
- `F`: 재추출 또는 다른 방식 필요

## 파일럿 우선 순위

- `P0`: 스캔형 PDF 1건
- `P0`: 텍스트형 PDF 1건
- `P0`: HWP/HWPX 1건
- `P0`: XLSX 1건

상세 목록은 `01_golden-sample-list.md`를 따른다.

## 검증 기준

- 원문 페이지 또는 시트 단위로 역추적 가능해야 한다.
- 표는 화면에서 다시 렌더링 가능한 수준이어야 한다.
- 그림은 단순 이미지 저장이 아니라 검색 가능한 요약 메타데이터를 가져야 한다.
- 추출 실패 항목은 누락이 아니라 실패 상태로 기록해야 한다.
