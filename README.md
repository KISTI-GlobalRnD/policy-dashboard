# 과기부-대시보드

정책 문헌을 구조화된 데이터로 전환하고, 이를 온톨로지와 대시보드로 연결하기 위한 작업 공간이다.

## 현재 판단

- 현재 단계의 우선순위는 화면 제작보다 범위 확정, 정보설계, 구조화 추출이다.
- 기존 `data/`는 원본 입력 영역으로 유지하고, 가공 산출물은 `work/` 아래 단계별로 분리한다.
- `대시보드 설계`는 초기에 정보설계로 한 번, 후반에 상세 설계와 연결로 한 번 나누어 진행한다.

## 권장 작업 순서

1. 범위 확정과 문서 등록부 작성
2. 핵심 질의 정의와 대시보드 정보설계 초안 작성
3. 최소 데이터모델과 온톨로지 논리설계 확정
4. 샘플 문서 구조화 추출 파일럿
5. 전체 문서 구조화 추출
6. 데이터 정규화와 매핑
7. 온톨로지 구현
8. 대시보드 상세 설계와 연결
9. 검증과 보완

## 디렉터리 구조

```text
과기부-대시보드/
├── data/                       # 원본 입력 데이터
├── docs/                       # 계획, 인벤토리, 데이터모델 문서
├── work/
│   ├── 01_scope-and-ia/        # 범위 확정, 질문 정의, 정보설계
│   ├── 02_structured-extraction/
│   ├── 03_processing/
│   ├── 04_ontology/
│   ├── 05_dashboard/
│   └── 06_integration/
├── qa/                         # 단계별 검증 체크
├── scripts/                    # 추출/가공/검증 스크립트
└── tmp/                        # 임시 분석 파일
```

## 바로 시작할 위치

- 범위/질문/필터 정의: `work/01_scope-and-ia/requirements/`
- 의사결정 로그: `work/01_scope-and-ia/decisions/`
- 추출 결과 저장: `work/02_structured-extraction/`
- 정규화 결과 저장: `work/03_processing/`
- 온톨로지 산출물 저장: `work/04_ontology/`

## 참고 문서

- `docs/01_execution-plan.md`
- `docs/02_data-inventory.md`
- `docs/03_minimum-data-model.md`
- `work/01_scope-and-ia/requirements/04_document-registry.csv`
- `work/02_structured-extraction/manifests/00_extraction-spec.md`

## 정적 배포

- 위치: `work/05_dashboard/frontend`
- 동작 방식: 데이터는 `public/data/*.json`을 번들에 반영해 정적 페이지로만 동작합니다. 백엔드 API가 필요 없습니다.
- 정적 번들 생성:
  - `npm run build`
  - 산출물: `work/05_dashboard/frontend/dist`
- 배포:
  - `dist/` 폴더를 정적 웹서버(예: GitHub Pages, Nginx, S3 + CloudFront)에 업로드합니다.
  - 라우팅은 쿼리 파라미터(`?view=...`, `?board=...`)만 사용하므로 별도 서버 라우팅 규칙이 없습니다.
- 주의:
  - `work/05_dashboard/frontend/index.html`은 Vite 개발 진입점입니다. 배포/공유용 파일은 `work/05_dashboard/frontend/dist/index.html`만 사용합니다.
  - GitHub Pages에서는 `dist/` 업로드 후 별도 서버 로직 없이 동작합니다.
- 로컬 확인:
  - `file:///.../dist/index.html`은 모듈 기반 번들(CORS)을 읽지 못해 실패할 수 있습니다.
  - `npm run preview` 또는 `vite preview`로 `http://` 기반에서 열어 확인하세요.
