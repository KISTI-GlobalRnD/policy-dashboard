# 2026-03-17 Missing Context Source Replacement

## Summary
- `DOC-CTX-012`, `DOC-CTX-013`, `DOC-CTX-014`를 proxy note에서 source-backed raw context note로 교체했다.
- 원문은 PACST 68-4 공식 PDF `제5차 과학기술기본계획 및 제1차 국가연구개발 중장기 투자전략 2025년 시행계획(안)`에서 해당 기술분야 섹션을 발췌한 cropped PDF다.
- full source는 `data/2026-03-17_pacst_68-4_2025-implementation-plan.pdf`로 저장했고, 문서별 crop은 `data/2026-03-17_missing-context-raw-sources/`에 생성했다.

## Replacement Map
- `DOC-CTX-012` `기술분야 개요 인공지능`
  - source crop: `DOC-CTX-012__pacst-68-4-page-208.pdf`
  - PACST source page: `208`
  - section title: `인공지능`
- `DOC-CTX-013` `기술분야 개요 첨단로봇제조`
  - source crop: `DOC-CTX-013__pacst-68-4-page-235.pdf`
  - PACST source page: `235`
  - section title: `첨단 로봇·제조`
- `DOC-CTX-014` `기술분야 개요 반도체디스플레이`
  - source crop: `DOC-CTX-014__pacst-68-4-page-232.pdf`
  - PACST source page: `232`
  - section title: `반도체·디스플레이`

## Extraction Notes
- `run_registry_document_extraction_batch.py` targeted rerun으로 3건 모두 `completed` 처리했다.
- cropped page는 PyMuPDF4LLM이 placeholder `2-column markdown table`로 잘못 인식해서, `finalize_missing_context_raw_extractions.py`로 block-text 기반 page/md로 후처리했다.
- stale `TBL-DOC-CTX-012~014-PROXY-*` artifacts는 삭제했다.

## Result
- extraction snapshot 기준 `source_backed_document_count=37`, `proxy_document_count=0`
- table backlog snapshot 기준 active backlog는 그대로 `0`
