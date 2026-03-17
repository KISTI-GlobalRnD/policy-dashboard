# 2026-03-17 Extraction Completion Snapshot

## Status
- document_count: `37`
- completed_count: `37`
- source_backed_completed_count: `37` / `37`
- proxy_document_count: `0`
- ocr_curated_document_count: `5`
- total_table_artifact_count: `830`
- total_substantive_table_artifact_count: `93`
- total_figure_artifact_count: `430`

## Notes
- Extraction layer is frozen at this snapshot for downstream ontology/dashboard work.
- Table artifact counts now distinguish raw extracted boxes from heuristic substantive tables.
- `DOC-POL-013` uses the companion HWPX source to recover structured tables and figures.
- `DOC-REF-001`, `DOC-REF-002`, `DOC-CTX-002`, `DOC-CTX-003`, `DOC-CTX-004` are OCR-derived and were finalized into curated tables.
- `DOC-CTX-012`, `DOC-CTX-013`, `DOC-CTX-014` remain proxy context notes until raw PDFs are obtained.

## Table Artifact Classes
- `layout_false_positive`: `541`
- `markdown_only_candidate`: `117`
- `review_required`: `79`
- `structured_table`: `93`
- `unclassified`: `0`

## Proxy Documents

## OCR-Curated Documents
- `DOC-CTX-002`
- `DOC-CTX-003`
- `DOC-CTX-004`
- `DOC-REF-001`
- `DOC-REF-002`
