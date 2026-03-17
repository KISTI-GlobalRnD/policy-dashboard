# 표 검토 전략 v0.2

## 결론

표는 룰 기반만으로 확정하지 않는다.

현재 운영 기준은 다음과 같다.

1. 자동 추출로 표 후보를 최대한 모은다.
2. 후보를 `structured`, `layout_false_positive`, `visual_table`, `multi_page_fragment`, `review_required`로 분류한다.
3. 사람 검토를 거쳐 `canonical_table`만 대시보드 연결 대상으로 확정한다.

## 왜 필요한가

정책 문서 PDF / HWPX에는 다음이 섞여 있다.

- 진짜 데이터 표
- 제목 박스나 체계도 박스처럼 표 도구로 만든 레이아웃
- 그림처럼 삽입된 표
- 여러 페이지에 나뉜 표

그래서 `find_tables()`만 믿으면 false positive가 생기고, `PyMuPDF4LLM` Markdown 표만 믿으면 누락이 생긴다.

## 후보 생성 경로

### 1. `PyMuPDF4LLM` Markdown 표

- 장점: 문서 읽기 순서 안에서 큰 표를 비교적 자연스럽게 보존한다.
- 약점: 일부 페이지 표를 놓친다.

### 2. `PyMuPDF find_tables()`

- 장점: 셀 구조를 직접 보존한다.
- 약점: 제목 박스, 단순 레이아웃, 문장 조각도 표로 잘못 잡을 수 있다.

### 3. `HWPX XML table`

- 장점: 원본 셀 구조를 잃지 않는다.
- 약점: 한국 정책문서는 제목 박스, 비전 박스, front matter까지 표 도구로 만드는 경우가 많아 false positive가 특히 많다.

## 검토 분류 체계

- `structured_table`
  - 실제 행/열 의미가 있고 대시보드 표나 데이터 소스로 사용할 수 있는 표
- `layout_false_positive`
  - 표 도구로 만들었지만 실질적으로는 제목, 박스, 레이아웃인 경우
- `visual_table`
  - 그림 또는 이미지 내부에 표 형태가 있는 경우
- `multi_page_fragment`
  - 같은 표가 여러 페이지로 나뉘어 있는 경우
- `review_required`
  - 자동으로 판단하기 어려운 경우

## 검토 큐

문서별로 다음 파일을 만든다.

- `qa/extraction/review_queues/*__table-review-queue.csv`
- `qa/extraction/review_queues/*__table-review-queue-summary.json`

CSV 기본 컬럼:

- `review_item_id`
- `document_id`
- `page_no`
- `candidate_source`
- `candidate_id`
- `rows`
- `cols`
- `preview_text`
- `suggested_class`
- `heuristic_reason`
- `keep_for_dashboard`
- `merge_group_hint`
- `canonical_table_id`
- `review_status`
- `reviewer_notes`
- `source_format`
- `treat_as_char`
- `text_wrap`

## HWPX 1차 heuristic

- `1x1`, `1x2`, `1x3` 박스는 기본적으로 layout false positive 우선 검토
- `의안번호`, `제출 연월일`, `과학기술관계장관회의` 같은 front matter 표는 layout false positive
- `<비전 및 목표>`, `Ⅰ. 추진배경`, `◇ ...` 같은 heading box는 layout false positive
- `rows >= 3 && cols >= 4`는 structured table 우선 후보
- `rows >= 4 && cols >= 2`이면서 `구분`, `%`, 연도, `기존/개선` 같은 header가 있으면 structured table 우선 후보
- `single column info box`와 `3x2/3x3 경계 사례`는 `review_required`

## heuristic seed

- `layout_false_positive`는 1차 seed에서 `keep_for_dashboard = no`
- `structured_table`는 1차 seed에서 `keep_for_dashboard = yes` 및 canonical seed 생성
- `review_required`만 후속 수동 검토 대상으로 남긴다

## 확정 규칙

- 대시보드는 `review_status = reviewed` 이고 `keep_for_dashboard = yes` 인 표만 사용한다.
- 다중 페이지 표는 병합 후 하나의 `canonical_table_id`를 부여한다.
- `layout_false_positive`는 provenance는 유지하되 대시보드 데이터셋에서는 제외한다.

## 현재 문서 기준 판단

`DOC-POL-006`에서는 다음이 이미 확인됐다.

- page chunk 표는 10개 페이지만 잡는다.
- `find_tables()`는 14개 페이지에서 후보를 잡지만 일부는 false positive다.
- 페이지 36~38은 다중 페이지 일정표 조각이다.
- 페이지 26은 표 누락 보정 샘플로 삼기 좋다.

phase1 HWPX 문서에서는 다음이 추가로 확인됐다.

- 표 후보의 대다수는 layout box다.
- `DOC-POL-005`, `007`, `009`만 봐도 HWPX table 후보의 약 70~80%가 false positive다.
- 하지만 heuristic seed를 적용하면 실제 structured table과 review_required만 남겨 검토량을 크게 줄일 수 있다.

## 다음 단계

1. phase1 문서의 `review_required`만 우선 수동 검토
2. 중복 표와 summary/main body 중복 표의 병합 규칙 추가
3. `needs_normalization`, `needs_merge` 후보 정리
4. visual table 샘플이 나오면 OCR/vision 예외 경로 추가
