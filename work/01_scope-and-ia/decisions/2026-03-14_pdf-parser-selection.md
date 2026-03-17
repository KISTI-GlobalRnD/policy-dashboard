# 2026-03-14 PDF Parser Selection

## 결정

텍스트형 PDF의 주 추출기는 `PyMuPDF4LLM`으로 채택한다.

보조 추출기는 `PyMuPDF`로 둔다.

## 이유

- 현재 우선순위가 OCR보다 `텍스트 레이어가 있는 PDF의 순수 텍스트 확보`에 있다.
- `PyMuPDF4LLM`은 페이지 단위 읽기 순서 텍스트를 바로 제공한다.
- `PyMuPDF`를 함께 쓰면 bbox provenance를 유지할 수 있다.
- 라이선스 검토는 통과됐다.

## 현재 운영 방식

- `PyMuPDF4LLM`: page chunk JSON + Markdown 텍스트
- `PyMuPDF`: bbox 텍스트 블록 + 레이아웃 메타데이터
- `RapidOCR`: 스캔형 PDF 예외 경로

## 유보 사항

`PyMuPDF4LLM` full layout ONNX 스택은 아직 활성화하지 않는다.

이유:

- `onnxruntime`, `networkx`, `scipy`, `opencv`, `yaml` 계열 의존성이 추가된다.
- 현재 단계에서는 pure text 확보가 더 우선이다.
