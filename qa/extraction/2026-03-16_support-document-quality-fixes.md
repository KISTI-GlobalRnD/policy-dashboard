# Support Document Quality Fixes

## Scope

- target group: support documents in the registry
- related scripts:
  - `scripts/extract_pdf_text_from_zip.py`
  - `scripts/ocr_page_images_rapidocr.py`
  - `scripts/reconstruct_support_ocr_tables.py`
  - `scripts/run_support_document_extraction_batch.py`

## Fix 1. Text-layer PDF page-text fallback

Problem:

- some Hancom-exported 1-page PDFs exposed usable text blocks in `*_blocks.json`
- but `PyMuPDF4LLM` page chunk text and `.md` were empty or title-only

Applied rule:

- if page chunk text is empty, use PyMuPDF block-order text as fallback
- if page chunk text is extremely sparse relative to block text, also use the fallback

Affected documents:

- `DOC-CTX-005`
- `DOC-CTX-006`
- `DOC-CTX-007`
- `DOC-CTX-010`
- `DOC-CTX-011`

Result:

- all above docs now have non-empty `*_pages.json` and `.md`
- manifest `extraction_run_id` moved to `pilot-gs-002-v3`
- manifest `counts.page_text_fallback_pages = 1`

Example outcome:

- `DOC-CTX-005.md` changed from page marker only to usable body text
- `DOC-CTX-010.md` changed from title-only output to full bio/medical taxonomy text

## Fix 2. OCR PDF page-level text/markdown

Problem:

- OCR PDFs previously produced only line-level `*_blocks.json`
- manual review was possible but inconvenient because there was no page-level OCR text or markdown view

Applied rule:

- aggregate OCR lines into page text using bbox sort order
- write `*_pages.json` and `.md`

Affected documents:

- `DOC-REF-001`
- `DOC-REF-002`
- `DOC-CTX-002`
- `DOC-CTX-003`
- `DOC-CTX-004`

Result:

- all above docs now have page-level OCR text and markdown
- manifest `extraction_run_id` moved to `pilot-gs-001-korean-ocr-v2`

Current usability:

- `DOC-REF-002.md` is now readable enough for manual strategy audit, but still contains OCR noise
- `DOC-CTX-002.md` to `DOC-CTX-004.md` are reviewable, but still not canonical table extraction outputs

## Residual Risk

## Fix 3. OCR support table candidates

Problem:

- OCR text and markdown were available, but there were still no table objects for the scanned support PDFs

Applied rule:

- group OCR lines into row bands
- assign them into coarse column buckets by document profile
- write a review-oriented table candidate JSON/CSV

Affected documents:

- `DOC-REF-002`
- `DOC-CTX-002`
- `DOC-CTX-003`
- `DOC-CTX-004`

Result:

- each document now has `TBL-*-OCR-001.json` and `.csv`
- manifests now include one OCR-derived table candidate with `candidate_source = rapidocr_line_reconstruction`
- `run_support_document_extraction_batch.py` now chains this step automatically for these OCR support docs

Current usability:

- `DOC-CTX-003`, `DOC-CTX-004` are coarse but reviewable as 2-column table candidates
- `DOC-CTX-002` is partially useful, with residual OCR noise in the label column
- `DOC-REF-002` is still too noisy for canonical use, but now exists as a coarse review candidate instead of pure OCR text only

## Residual Risk

1. `DOC-REF-002` remains OCR-noisy and should not be treated as a canonical structured strategy table without cleanup.
2. `DOC-CTX-002` to `DOC-CTX-004` table candidates are heuristic reconstructions, not confirmed cell-accurate tables.
3. `DOC-CTX-005` to `DOC-CTX-011` page text is now present, but some are still block-joined rather than semantically normalized.

## Operational Note

- `run_support_document_extraction_batch.py` now writes a suffixed batch filename when `--documents` is used, so targeted reruns no longer overwrite the daily full-batch summary.
