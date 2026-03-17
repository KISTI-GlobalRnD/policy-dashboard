# STR-010 Alignment Review

## Summary
- `DOC-REF-002`의 기술 밴드 row `10`은 `사이버 보안 및 AI 신뢰성 검증 기술 확보`로 정규화됐다.
- 현재 taxonomy의 `STR-010`은 `디지털 헬스케어 서비스 혁신`이며, reviewed manual mapping 3건도 모두 healthcare item에 붙어 있다.
- 따라서 `DOC-REF-002` row `10`과 `STR-010`은 현재 기준에서 `not_aligned`로 유지하는 것이 맞다.

## Reviewed Evidence
- reviewed strategy mappings:
- `PIT-ITM-POL-012-00899-STR-010-R01` -> `SRD-POL-012-edf0789d256e` -> `DRV-PAR-DOC-POL-006-00348`
- `PIT-ITM-POL-012-01001-STR-010-R01` -> `SRD-POL-012-bd818983dc30` -> `DRV-PAR-DOC-POL-006-00335`
- `PIT-ITM-POL-012-01016-STR-010-R01` -> `SRD-POL-012-6f87aec3eac5` -> `DRV-PAR-DOC-POL-006-00336`
- evidence previews:
- `Medical Korea 브랜드 확산`
- `비대면진료 활성화를 위한 통합플랫폼 구축`
- `원격협진 외 국내의료인-외국인환자간 비대면진료 제도화`

## Decision
- `STR-010` 라벨과 description은 유지한다.
- `STR-010`의 provenance는 `DOC-REF-002 provisional OCR`에서 분리하고, `DOC-POL-006; POL-012 reviewed healthcare cluster; STX-STR-010-001`로 교체한다.
- `DOC-REF-002` 기술 밴드 row `10`은 canonical reference row로만 보존하고, taxonomy id에는 연결하지 않는다.

## Artifacts
- machine-readable exception:
- `work/04_ontology/instances/strategy_alignment_exceptions.csv`
- `work/04_ontology/instances/strategy_alignment_exceptions.json`
- related canonical table:
- `work/04_ontology/instances/derived_tables/CTBL-DOC-REF-002-001__strategy-reference.csv`
- focused review packet:
- `qa/ontology/review_packets/strategy-alignment-exception-index.csv`
- `qa/ontology/review_packets/strategy_alignment_exceptions/STX-STR-010-001__디지털-헬스케어-서비스-혁신__alignment-review.csv`
- `qa/ontology/review_packets/strategy_alignment_exceptions/STX-STR-010-001__디지털-헬스케어-서비스-혁신__alignment-review.md`
- draft triage:
- `qa/ontology/review_drafts/strategy-alignment-exception-draft-index.csv`
- `qa/ontology/review_drafts/strategy_alignment_exceptions/STX-STR-010-001__디지털-헬스케어-서비스-혁신__alignment-review__draft.csv`
- `qa/ontology/review_drafts/strategy_alignment_exceptions/STX-STR-010-001__디지털-헬스케어-서비스-혁신__alignment-review__draft-brief.md`
- final manual decisions:
- `qa/ontology/review_drafts/strategy_alignment_exceptions/STX-STR-010-001__manual-decisions.csv`
- `qa/ontology/review_drafts/strategy_alignment_exceptions/STX-STR-010-001__manual-decisions-summary.json`

## Pipeline Guard
- `classify_policy_items_strategies.py`는 alignment exception이 걸린 전략을 auto-map하지 않도록 바꿨다.
- 중간 rerun 기준 blocked item은 `20`건이었고 모두 review queue로 남겼다.
- `build_strategy_review_queue.py`는 `alignment_exception_ids`, `alignment_exception_notes`, `auto_seed_blocked` 컬럼을 추가했다.
- `sync_strategy_review_decisions.py`는 blocked row를 auto-seed하지 않고, 기존 `auto_seed` reviewed row도 stale auto-seed면 다시 `pending`으로 되돌린다.
- `build_strategy_review_drafts.py`, `build_strategy_review_draft_priority_queue.py`는 현재 `strategy-review-batch-index.csv`에 들어있는 batch만 처리하도록 바꿨다.
- alignment exception draft 기준 현재 triage 초안은 `keep_primary 15`, `demote_from_primary 2`, `taxonomy_split_review 3`이다.

## Final Manual Resolution
- `STX-STR-010-001` packet `20`건을 한 건씩 검토해 `reviewed 18`, `no_strategy 2`로 확정했다.
- `no_strategy`로 바꾼 항목은 `SRD-POL-012-dab70a92dcb0`, `SRD-POL-012-bc0be1062e6c`이며, composite schedule row라 `STR-010` primary를 제거했다.
- split candidate `3`건은 `STR-010` primary는 유지하되 secondary로 `STR-001`, `STR-003`를 남겼다.
- `finalize_strategy_alignment_exception_manual_decisions.py`를 수정해 기존 master decision row가 없어도 `policy-item-strategy-review-decisions.csv`에 append되도록 했다. 이번 rerun에서 `17`건이 새로 append됐다.
- 현재 기준 `policy-item-strategy-review-queue-summary.json`은 `review_item_count=0`, `auto_seed_blocked_count=0`이다.
- 현재 기준 `policy-item-strategy-review-decisions-summary.json`은 `decision_item_count=559`, `reviewed=175`, `no_strategy=384`, `active_in_queue_count=0`이다.
- 현재 기준 `policy-item-strategy-review-reviewed-summary.json`은 `applied_item_count=559`, `applied_mapping_row_count=302`, `no_strategy_item_count=384`, `invalid_decision_count=0`이다.
- decision CSV는 by-policy strategy packet `6`개에서 재구성해 UTF-8 손상 없이 복구했다.
- 현재 기준 `strategy-alignment-exception-index-summary.json`은 `exception_packet_count=1`, `total_item_count=20`이며, packet row 기준 `active_item_count=0`, `reviewed_count=18`, `no_strategy_count=2`다.
- 현재 기준 `strategy-alignment-exception-draft-summary.json`은 `exception_draft_count=0`이며, 이전 heuristic draft 산출물 `3`개는 stale file로 제거됐다.
- 현재 기준 `strategy-review-batch-index-summary.json`은 `batch_count=0`이며, legacy batch CSV `24`개와 관련 brief/draft 파일은 cleanup 대상에서 제거됐다.
- 따라서 `STR-010` alignment exception backlog는 해소됐고, 남겨진 packet은 active work queue가 아니라 resolved audit artifact다.
