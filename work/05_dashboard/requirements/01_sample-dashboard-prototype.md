# 샘플 대시보드 프로토타입

## 위치

- 전체보기 대시보드: `work/05_dashboard/index.html`
- 기술 상세 시안: `work/05_dashboard/detail-tech.html`
- 정책 상세 시안: `work/05_dashboard/detail-policy.html`
- 공통 스타일: `work/05_dashboard/briefing.css`
- 기술축 데이터 계약: `work/05_dashboard/data-contracts/technology-lens.json`
- 최신 UX 기준: `work/05_dashboard/requirements/04_overview-detail-static-ux.md`

## 목표

샘플 단계에서는 아래 3단 구조를 검토한다.

1. 전체보기에서 각 정책이 어느 기술에 집중하는지 확인
2. 기술 상세에서 특정 기술에 어떤 정책들이 연결되는지 확인
3. 정책 상세에서 특정 정책이 어떤 기술들에 분산되는지 확인

즉 샘플 산출물의 중심은 `정책-기술 집중도 대시보드`다.

## 현재 데이터 기준

2026-03-17 기준 현재 payload는 이미 `13개 활성 기술`과 다수의 교차 정책 분포를 가진다.

대표 예시:

- `AI-바이오 국가전략`은 `인공지능`, `소재`, `양자`, `첨단바이오`에 연결된다.
- `정부 AX사업 전주기 원스톱 지원방안`은 현재 `인공지능`에 집중된다.
- `123대 국정과제`는 여러 기술에 분산된다.

따라서 첫 화면은 카드형 브리핑보다 `정책 x 기술` 집계 보드가 우선이다.

## 실행

정적 산출물은 리포지토리 루트에서 직접 열어 확인한다.

- `work/05_dashboard/index.html`
- `work/05_dashboard/detail-tech.html`
- `work/05_dashboard/detail-policy.html`

데이터 계약이 갱신되면 생성 스크립트도 새 구조에 맞게 다시 연결한다.

## 현재 원칙

- overview는 매트릭스 중심이다.
- detail은 `기술 중심`과 `정책 중심` 두 축으로 나뉜다.
- 0건 기술은 overview/detail 어디에도 노출하지 않는다.
- 내부 식별자와 QA 메타는 본문에 노출하지 않는다.

## 다음 구현 포인트

1. 브라우저 실화면 QA
2. 상세 카드 카피 톤 추가 정리
3. 대표 근거 배치 톤 조정
