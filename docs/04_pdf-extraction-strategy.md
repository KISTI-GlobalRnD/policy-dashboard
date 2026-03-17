# PDF 추출 전략 v0.2

## 결론

PDF 계열 문서는 다음 이원 경로로 처리한다.

- 텍스트형 PDF 주 추출기: `PyMuPDF4LLM`
- 텍스트형 PDF 보조 추출기: `PyMuPDF`
- 스캔형 PDF 경로: `PyMuPDF` 렌더링 + `RapidOCR`

현재 우선순위는 OCR이 아니라 `텍스트 레이어가 있는 PDF의 순수 텍스트 확보`다. 따라서 텍스트형 PDF는 `PyMuPDF4LLM`을 기준 경로로 채택한다.

## 채택 이유

- `PyMuPDF4LLM`은 페이지 단위 읽기 순서 텍스트를 바로 제공한다.
- `page_chunks=True` 경로로 페이지별 `text`, `tables`, `images`, `graphics`, `metadata`를 함께 확보할 수 있다.
- 같은 문서에 대해 `PyMuPDF` 저수준 블록 추출을 같이 쓰면 bbox provenance도 유지할 수 있다.
- 라이선스 검토는 통과된 상태다.

## 현재 구현 기준

### 1. 텍스트형 PDF

주 경로:

- `pymupdf4llm.to_markdown(..., page_chunks=True)`
- 산출물:
  - 페이지 단위 JSON
  - 통합 Markdown 텍스트

보조 경로:

- `page.get_text("dict", sort=True)`
- 산출물:
  - bbox 포함 텍스트 블록 JSON
  - 페이지 레이아웃 메타데이터

현재 적용 예:

- `DOC-POL-006` (`GS-002`)

### 2. 스캔형 PDF

권장 경로:

1. `PyMuPDF`로 페이지 렌더링
2. `RapidOCR`로 OCR line block 추출
3. OCR confidence와 bbox 저장
4. 후속 단계에서 표 행/열 복원

현재 적용 예:

- `DOC-REF-001` (`GS-001`)

## 구현상 판단

`PyMuPDF4LLM`의 full layout ONNX 스택은 추가로 `onnxruntime`, `networkx`, `scipy`, `opencv`, `yaml` 계열 의존성이 필요하다. 현재 단계에서는 그 비용이 크고, 우선순위도 `순수 텍스트 추출`이므로 아직 활성화하지 않았다.

즉 현재 운영 기준은 다음과 같다.

- 읽기 순서 텍스트: `PyMuPDF4LLM`
- bbox provenance: `PyMuPDF`
- OCR: 스캔형 예외 경로에서만 사용

## 실제 확인된 사항

- `data/260312_정책-항목 구성(안).pdf`는 텍스트 레이어가 없다.
- `DOC-POL-006`은 텍스트 레이어가 있어 `PyMuPDF4LLM` 경로로 직접 추출 가능하다.
- `DOC-POL-006` 기준으로 페이지 38개, page chunk 38개, bbox 텍스트 블록 1026개가 확보됐다.
- 같은 문서에서 `PyMuPDF4LLM` page chunk는 표 후보 bbox 메타데이터도 일부 제공한다.

## 남은 과제

1. page chunk 텍스트 후처리 규칙 정리
2. 헤더/푸터/쪽번호 제거 규칙 추가
3. `tables` bbox와 별도 표 추출 결과의 연결 규칙 설계
4. 스캔형 PDF는 OCR block -> 행 그룹핑 -> 표 복원 단계 진행
