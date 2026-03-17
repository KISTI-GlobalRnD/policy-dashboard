# 의사결정 로그

| 날짜 | 주제 | 상태 | 결정 또는 쟁점 | 메모 |
| --- | --- | --- | --- | --- |
| 2026-03-14 | 분석 대상 문서 범위 | Working | 재구성 초안 기준 12개 정책을 1차 범위 baseline으로 사용 | `2026-03-14_phase1-working-scope.md` 참조 |
| 2026-03-14 | 123대 국정과제 원문 | Open | 원문 확보 필요 | 현재 `data/`에는 없음 |
| 2026-03-14 | 범부처 기술관리체계 문서 포함 여부 | Open | 1차 범위 포함 여부 결정 필요 | ZIP에는 있으나 재구성 초안에는 직접 안 보임 |
| 2026-03-14 | 민주당 공약집 포함 여부 | Open | 정책 비교자료인지 본 분석 범위인지 확정 필요 | 성격이 다름 |
| 2026-03-14 | 기술분야 기준표 | Working | 엑셀 파일을 공식 기준표로 사용 | 14개 대분류와 중분류 포함 |
| 2026-03-14 | 전략 기준표 | Working | 재구성 초안 PDF의 15개 전략 축을 임시 기준으로 사용 | 이후 변경 가능 |
| 2026-03-14 | 텍스트형 PDF 주 추출기 | Working | `PyMuPDF4LLM`을 주 추출기로 채택 | bbox provenance는 `PyMuPDF` 보조 사용 |
| 2026-03-14 | 텍스트형 PDF 정규화 방식 | Working | bbox text block을 본문 기준으로 사용하고, page chunk는 표 Markdown 보존에만 사용 | `normalize_pdf_page_text.py` 참조 |
| 2026-03-14 | 변환 HWPX 소스 전략 | Working | 변환 HWPX가 표/그림 객체를 잃으면 본문-only 참조본으로만 사용하고, canonical 근거와 표는 원 PDF를 유지 | `DOC-POL-006` 케이스로 검증 |
| 2026-03-14 | 표 확정 방식 | Working | 표는 자동 추출 결과를 바로 쓰지 않고 review queue를 거쳐 canonical table로 확정 | `PyMuPDF4LLM`와 `find_tables()`를 병행 사용 |
| 2026-03-14 | canonical table 상태값 | Working | `ready`, `needs_normalization`, `needs_merge` 3단계로 관리 | `dashboard_ready = yes` 인 표만 즉시 연결 |
| 2026-03-14 | 문단 분류 템플릿 방식 | Working | 정규화 문단에서 classification template CSV 생성 | 자원유형만 약한 자동 제안, 나머지는 `review_required` |
| 2026-03-14 | 온톨로지 구현 방식 | Decided | 1차는 SQLite 기반 관계형 온톨로지 마트, 2차는 JSON-LD/Turtle RDF export | OWL/RDFS + SKOS + PROV-O + SHACL 조합으로 확장 |
| 2026-03-14 | 내용-증거 중심 ontology 단위 | Decided | raw `PolicyItem`은 provenance 보존용으로 남기고, 판단/분류/표시는 `PolicyItemGroup`과 `PolicyItemContent`를 기준으로 수행 | `저장은 낱줄, 판단은 대표 내용` 원칙 채택 |
