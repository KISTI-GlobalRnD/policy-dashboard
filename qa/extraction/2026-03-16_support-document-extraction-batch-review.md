# Support Document Extraction Batch Review

## Scope

- Registry filter: `include_status = support`
- Batch summary:
  - `work/02_structured-extraction/manifests/batch_runs/2026-03-16_support-document-extraction-batch.json`
  - `work/02_structured-extraction/manifests/batch_runs/2026-03-16_support-document-extraction-batch.csv`
- Later targeted reruns on the same date may update the machine summary file; follow-up quality changes are tracked in `qa/extraction/2026-03-16_support-document-quality-fixes.md`.

## Result Summary

- support source rows: `13`
- reused existing extraction: `1`
  - `DOC-REF-001`
- newly extracted this run: `12`
- failed: `0`
- missing source: `0`

## Extraction Routing

### Text-layer PDF

- `DOC-CTX-001` `기술분야 개요 국방`
- `DOC-CTX-005` `기술분야 개요 에너지`
- `DOC-CTX-006` `기술분야 개요 우주항공`
- `DOC-CTX-007` `기술분야 개요 이차전지`
- `DOC-CTX-008` `기술분야 개요 차세대통신`
- `DOC-CTX-009` `기술분야 개요 첨단모빌리티`
- `DOC-CTX-010` `기술분야 개요 첨단바이오`
- `DOC-CTX-011` `기술분야 개요 해양`

Routing:

- `extract_pdf_text_from_zip.py`
- status: `completed`

Notes:

- all above files exposed an embedded text layer on the single page
- `DOC-CTX-008`, `DOC-CTX-009` reported `pages_with_tables_markdown = 1`

### OCR PDF

- `DOC-REF-002` `정책기술분야별 재구성(안)`
- `DOC-CTX-002` `기술분야 개요 사이버보안`
- `DOC-CTX-003` `기술분야 개요 소재`
- `DOC-CTX-004` `기술분야 개요 양자`

Routing:

- `extract_scanned_pdf_pages.py`
- `ocr_page_images_rapidocr.py`
- status: `partial_table_pending`

Notes:

- all four files had `text_layer_pages = 0`
- OCR line blocks were generated, but table structure reconstruction is still pending
- `DOC-REF-002` now has a manifest and OCR evidence for the strategy reference PDF

## Output Check

- manifests created:
  - `work/02_structured-extraction/manifests/DOC-REF-002_manifest.json`
  - `work/02_structured-extraction/manifests/DOC-CTX-001_manifest.json`
  - `work/02_structured-extraction/manifests/DOC-CTX-002_manifest.json`
  - `work/02_structured-extraction/manifests/DOC-CTX-003_manifest.json`
  - `work/02_structured-extraction/manifests/DOC-CTX-004_manifest.json`
  - `work/02_structured-extraction/manifests/DOC-CTX-005_manifest.json`
  - `work/02_structured-extraction/manifests/DOC-CTX-006_manifest.json`
  - `work/02_structured-extraction/manifests/DOC-CTX-007_manifest.json`
  - `work/02_structured-extraction/manifests/DOC-CTX-008_manifest.json`
  - `work/02_structured-extraction/manifests/DOC-CTX-009_manifest.json`
  - `work/02_structured-extraction/manifests/DOC-CTX-010_manifest.json`
  - `work/02_structured-extraction/manifests/DOC-CTX-011_manifest.json`

## Next Step

1. If `DOC-REF-002` needs canonical strategy label recovery, add a lightweight OCR cleanup or manual seed audit pass.
2. If `DOC-CTX-002` to `DOC-CTX-004` need structured tables, add an OCR row-grouping/table-reconstruction step rather than treating line OCR as final.
3. Keep the new batch script as the reusable entrypoint for future support PDF/HWPX additions.
