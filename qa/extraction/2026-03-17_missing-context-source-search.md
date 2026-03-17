# 2026-03-17 Missing Context Source Search

## 대상
- `DOC-CTX-012` `기술분야 개요 인공지능`
- `DOC-CTX-013` `기술분야 개요 첨단로봇제조`
- `DOC-CTX-014` `기술분야 개요 반도체디스플레이`

## 확인 결과
- 저장소의 `data/260313_기술분야 개요.zip`와 압축 해제 폴더에는 위 3건 원문이 없다.
- 사용자 로컬 문서/다운로드 경로에서도 동일 제목 또는 대응 filename을 찾지 못했다.
- 웹 검색도 시도했지만 바로 회수 가능한 원문 PDF/HWPX는 확인하지 못했다.

## 오늘 보강
- `build_missing_context_note_proxies.py`가 proxy note마다 `2`개의 table artifact를 생성하도록 확장됐다.
- `PROXY-001`: taxonomy subdomain summary
- `PROXY-002`: supporting evidence matrix

## 현재 산출물
- `DOC-CTX-012/013/014` manifest는 모두 `derived-context-proxy-v2`
- 각 문서는 `supporting_evidence_snippets`와 `tables=2`를 가진다
- raw source가 확보되면 현재 proxy 산출물은 교체 대상이다
