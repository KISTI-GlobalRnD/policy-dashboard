# Phase1 Policy Text-First Batch Review

## 대상

- 범위: `12개 정책 문헌 자료` 기준 phase1 정책 문서
- 실행 요약:
  - `work/02_structured-extraction/manifests/batch_runs/2026-03-14_phase1-policy-text-first-batch.json`
  - `work/02_structured-extraction/manifests/batch_runs/2026-03-14_phase1-policy-text-first-batch.csv`

## 결과 요약

- phase1 정책 행 수: 12
- 초벌 추출 완료: 11
- 미실행: 1
  - `DOC-POL-001` `123대 국정과제`: 원문 미확보
- 실패: 0

## 포맷별 판단

### HWPX

- 현재 초벌 추출의 주력 경로로 적절하다.
- 문단, 표, 그림 객체가 원본 구조에 가깝게 보존된다.
- 다만 표/그림 수가 많아도 현 단계에서는 `추출만 보관`하고 본문 텍스트 검토를 우선한다.
- HWPX 원문 내부 `hp:fwSpace` 같은 inline control 뒤 tail text도 보존하도록 추출기를 보정했다.
- 이 수정으로 `DOC-POL-004`, `DOC-POL-010`의 잘리던 footnote 본문이 복원됐다.
- 단, `PDF -> HWPX` 변환본은 예외 검증이 필요하다.
- `DOC-POL-006` 변환 HWPX는 유효한 HWPX이지만 내부 객체가 `tables 0 / figures 0`이라서 구조형 원본으로는 부적합했다.
- 이런 케이스는 HWPX를 본문-only 참조본으로만 쓰고, canonical 표/근거는 PDF를 유지하는 것이 맞다.

### PDF

- `DOC-POL-006`은 텍스트형 PDF라서 순수 텍스트 경로가 안정적이다.
- page chunk와 bbox block이 모두 확보되어 후속 정규화에 바로 연결 가능하다.

### HWPX 보강 메모

- `DOC-POL-003` 원문이 HWPX로 확보되어, 이제 phase1 정책 문서는 PDF 1건과 HWPX 10건 체계로 정리됐다.
- `DOC-POL-003`도 HWPX 직추출로 다시 생성했고, 현재 초벌 기준 `evidence_units 133`, `tables 41`, `figures 10`을 보존한다.
- 따라서 phase1 pure text 경로에서 legacy HWP 예외 문서는 더 이상 직접 대상이 아니다.

## 문서별 상태

- `DOC-POL-002` `AI-바이오 국가전략`: 완료
- `DOC-POL-003` `제조AX 추진방향`: 완료, HWPX 직추출
- `DOC-POL-004` `과학기술xAI 국가전략`: 완료
- `DOC-POL-005` `연구개발 생태계 혁신방안`: 완료
- `DOC-POL-006` `초혁신경제 15대 프로젝트 추진계획`: 완료
- `DOC-POL-007` `AI반도체 산업 도약 전략`: 완료
- `DOC-POL-008` `민간투자연계, 팁스 R&D 확산방안`: 완료
- `DOC-POL-009` `기초연구 생태계 육성 방안`: 완료
- `DOC-POL-010` `과학기술분야 출연(연) 정책방향`: 완료
- `DOC-POL-011` `AI시대 대한민국 네트워크 전략`: 완료
- `DOC-POL-012` `정부 AX사업 전주기 원스톱 지원방안`: 완료

## 다음 검토 우선순위

1. `DOC-POL-006` 본문 정규화 고도화 지속
2. `DOC-POL-003` HWPX 구조 추출 결과의 표/그림 보존 상태 점검
3. phase1 pure text 기준이 안정된 뒤 표와 그림을 별도 review queue로 분리
