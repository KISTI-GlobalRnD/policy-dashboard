# 2026-03-17 Figure Review Pass 01

## Scope

- `DOC-POL-008`
- `DOC-POL-003`
- `DOC-POL-004`
- `DOC-POL-009`
- `DOC-POL-010`
- `DOC-POL-011`
- `DOC-POL-012`
- `DOC-POL-007`
- `DOC-POL-002`
- `DOC-POL-005`

## Decisions

- `DOC-POL-003`: `10`건 중 `1`건 유지, `9`건 제외
  - 유지: M.AX 얼라이언스 거버넌스/분과 구성 도식
  - 제외: 문서 공통 태극마크 아이콘 `1`, 제품 렌더/예시 이미지 `3`, 일반 아이콘 묶음 `1`, 소형 산업 아이콘 `4`
- `DOC-POL-004`: `27`건 중 `13`건 유지, `14`건 제외
  - 유지: 국가전략 총괄 비전, 과학 패러다임 변화, survey chart, 파운데이션 모델/AI 연구동료 구조도, 바이오 데이터-신약개발 도식, AI 연구동료 플랫폼, 인재양성 경로, 연구시설 자동화, DMP 흐름, 과학AI 허브/생태계 확장 등
  - 제외: 문서 공통 태극마크 아이콘 `1`, 국가 식별용 플래그/기관 아이콘 `3`, 소형 로고/배너 조각 `5`, 중복 총괄 비전 `1`, 저해상도 콜라주·소형 이미지 `3`, 휴머노이드 제품 사진 `1`
- `DOC-POL-009`: `27`건 중 `16`건 유지, `11`건 제외
  - 유지: 교원 수혜율, 성과 생산성, 예산·인력, HCR/Nature Index, 지역 격차, 장기 목표, BRL 체계, 중앙거점형 AI 인프라, 2030 인포그래픽
  - 제외: 태극마크 `1`, 축약 중복 차트 `1`, 플랫폼 스크린샷 `1`, 행사·회의 사진 `2`, 개별 연구 사례 이미지 `5`, 개념 일러스트 `1`
- `DOC-POL-010`: `34`건 전부 제외
  - 제외: 태극마크 `1`, 출연연 기관 CI/logo `24`, 대표성과 사진·이미지 `8`, WMF 자산 `1`
- `DOC-POL-008`: `2`건 중 `1`건 유지, `1`건 제외
  - 유지: 팁스 R&D 추진단 / 통합 BANK 시스템 도식
  - 제외: 문서 공통 태극마크 아이콘
- `DOC-POL-011`: `8`건 중 `2`건 유지, `6`건 제외
  - 유지: 무선 백홀 용량 증가 차트, 6G 상용화/완전자율 AI 네트워크 로드맵 배너
  - 제외: 문서 공통 태극마크 아이콘 `1`, 배너를 구성하는 개별 아이콘 `5`
- `DOC-POL-012`: `3`건 전부 제외
  - 제외: 문서 공통 태극마크 아이콘 `1`, 주요국 동향 문단의 소형 국기 아이콘 `2`
- `DOC-POL-007`: `56`건 중 `36`건 유지, `20`건 제외
  - 유지: 핵심 정책 도식/산업 동향/조직 구조도 중심
  - 제외: 저해상도 중복·중첩된 아이콘/마커성 이미지
- `DOC-POL-002`: `62`건 중 `32`건 유지, `30`건 제외
  - 유지: 본문 정책 지표 및 전략 구조 중심 시각자료
  - 제외: 저해상도, 중복 추정 및 아이콘/마커성 요소
- `DOC-POL-005`: `127`건 중 `14`건 유지, `113`건 제외
  - 유지: 고해상도 페이지형 다중 지표/조직 도식 중심
  - 제외: 아이콘/마커/중복 반복 이미지, 저해상도 패널

## Outputs

- reviewed queues
  - `qa/extraction/reviewed_queues/DOC-POL-004__figure-review-reviewed.csv`
  - `qa/extraction/reviewed_queues/DOC-POL-009__figure-review-reviewed.csv`
  - `qa/extraction/reviewed_queues/DOC-POL-010__figure-review-reviewed.csv`
  - `qa/extraction/reviewed_queues/DOC-POL-008__figure-review-reviewed.csv`
  - `qa/extraction/reviewed_queues/DOC-POL-011__figure-review-reviewed.csv`
  - `qa/extraction/reviewed_queues/DOC-POL-012__figure-review-reviewed.csv`
  - `qa/extraction/reviewed_queues/DOC-POL-007__figure-review-reviewed.csv`
  - `qa/extraction/reviewed_queues/DOC-POL-002__figure-review-reviewed.csv`
  - `qa/extraction/reviewed_queues/DOC-POL-005__figure-review-reviewed.csv`
- review summaries
  - `qa/extraction/reviewed_queues/DOC-POL-004__figure-review-reviewed-summary.json`
  - `qa/extraction/reviewed_queues/DOC-POL-009__figure-review-reviewed-summary.json`
  - `qa/extraction/reviewed_queues/DOC-POL-010__figure-review-reviewed-summary.json`
  - `qa/extraction/reviewed_queues/DOC-POL-008__figure-review-reviewed-summary.json`
  - `qa/extraction/reviewed_queues/DOC-POL-011__figure-review-reviewed-summary.json`
  - `qa/extraction/reviewed_queues/DOC-POL-012__figure-review-reviewed-summary.json`
  - `qa/extraction/reviewed_queues/DOC-POL-007__figure-review-reviewed-summary.json`
  - `qa/extraction/reviewed_queues/DOC-POL-002__figure-review-reviewed-summary.json`
  - `qa/extraction/reviewed_queues/DOC-POL-005__figure-review-reviewed-summary.json`
- manual decisions
  - `qa/extraction/review_decisions/DOC-POL-004__figure-review-decisions.json`
  - `qa/extraction/review_decisions/DOC-POL-009__figure-review-decisions.json`
  - `qa/extraction/review_decisions/DOC-POL-010__figure-review-decisions.json`
  - `qa/extraction/review_decisions/DOC-POL-008__figure-review-decisions.json`
  - `qa/extraction/review_decisions/DOC-POL-011__figure-review-decisions.json`
  - `qa/extraction/review_decisions/DOC-POL-012__figure-review-decisions.json`
  - `qa/extraction/review_decisions/DOC-POL-007__figure-review-decisions.json`
  - `qa/extraction/review_decisions/DOC-POL-002__figure-review-decisions.json`
  - `qa/extraction/review_decisions/DOC-POL-005__figure-review-decisions.json`

## Backlog Effect

- 현재 figure review snapshot 기준 active backlog는 `10 -> 0` 문서까지 감소했다.
- 상태 분포는 `manual_review_complete 10`, `support_render_only 5`, `deferred_hold_queue_built 1`이다.
- 남은 high priority 문서는 `없음`

## Ontology Reflection

- `load_ontology_evidence.py`는 이제 reviewed figure queue를 우선 반영한다.
- `render_figure_review_previews.py`를 추가해 BMP-heavy 문서도 preview PNG로 빠르게 검토할 수 있게 했다.
- `ontology.sqlite` 기준 품질 상태
  - `DOC-POL-003`: `dashboard_ready 1`, `decorative_excluded 9`
  - `DOC-POL-004`: `dashboard_ready 13`, `decorative_excluded 14`
  - `DOC-POL-009`: `dashboard_ready 16`, `decorative_excluded 11`
  - `DOC-POL-010`: `decorative_excluded 34`
  - `DOC-POL-008`: `dashboard_ready 1`, `decorative_excluded 1`
  - `DOC-POL-011`: `dashboard_ready 2`, `decorative_excluded 6`
  - `DOC-POL-012`: `decorative_excluded 3`
  - `DOC-POL-007`: `dashboard_ready 36`, `decorative_excluded 20`
  - `DOC-POL-002`: `dashboard_ready 32`, `decorative_excluded 30`
  - `DOC-POL-005`: `dashboard_ready 14`, `decorative_excluded 113`
