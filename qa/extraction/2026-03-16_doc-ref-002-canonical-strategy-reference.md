# DOC-REF-002 Canonical Strategy Reference

## Summary
- `DOC-REF-002`는 일반 표가 아니라 `기술 / 인프라·제도 / 인재·제도` 3개 밴드로 구성된 one-page reference board다.
- 이번 정리에서는 3개 밴드를 각각 별도 canonical table로 확정했다.
- canonical ids:
- `CTBL-DOC-REF-002-001`: 기술 전략 reference
- `CTBL-DOC-REF-002-002`: 인프라·제도 common factors
- `CTBL-DOC-REF-002-003`: 인재·제도 common factors

## Why This Scope
- 현재 `strategies_seed.csv`가 기대는 stable reference는 `기술` 밴드의 15개 전략 축이다.
- `인프라·제도`, `인재·제도` 밴드는 직접 seed에 연결되지는 않지만, policy taxonomy와 future reference lookup에 재사용 가치가 있어 함께 고정했다.

## Normalization Notes
- source asset: `work/02_structured-extraction/figures/assets/DOC-REF-002/page_001.png`
- source candidate: `TBL-DOC-REF-002-OCR-001`
- methods:
- `manual_visual_review_from_doc_ref_002_page_1_technology_band`
- `manual_visual_review_from_doc_ref_002_page_1_infrastructure_band`
- `manual_visual_review_from_doc_ref_002_page_1_talent_band`
- 기술 밴드 row `11`, `12`, `14`는 우측 설명 텍스트가 일부 훼손되어 보드 라벨과 가독 가능한 키워드를 기준으로 summary를 정규화했다.
- 인프라·제도 밴드 row `1`, `2`, `3`, `4`, `8`, `9`, `11`, `15`는 OCR 가독성이 낮아 대응 정책 문구를 참고해 summary 또는 label을 보강했다.
- 인재·제도 밴드 row `1`, `3`, `4`, `6`, `8`, `9`, `11`, `13`, `14`는 OCR 가독성이 낮아 대응 정책 문구와 보드 키워드를 함께 써서 정규화했다.

## Strategy Seed Impact
- `STR-001`~`STR-009`, `STR-011`~`STR-015`의 `source_basis`는 `DOC-REF-002; CTBL-DOC-REF-002-001`로 강화했다.
- `STR-010`의 전략명은 유지하되, `source_basis`는 `DOC-POL-006; POL-012 reviewed healthcare cluster; STX-STR-010-001`로 교체했다.
- 이유: 현재 taxonomy의 `디지털 헬스케어 서비스 혁신` 라벨은 보드의 row 10 `사이버 보안 및 AI 신뢰성 검증 기술 확보`와 1:1 대응하지 않는다.
- 근거는 `POL-012` reviewed manual mapping 3건과 `work/04_ontology/instances/strategy_alignment_exceptions.csv`에 남겼다.
- 따라서 `DOC-REF-002`는 `STR-001`~`009`, `011`~`015`의 stable reference로만 쓰고, `STR-010` 재정의는 후속 taxonomy review로 남긴다.
