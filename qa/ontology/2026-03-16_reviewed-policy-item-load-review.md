# Reviewed Policy Item Load Review

## Summary

- `reviewed workbench -> reviewed item export -> ontology load` 경로를 실제 pipeline에 연결했다.
- reviewed item loader `scripts/load_reviewed_policy_items.py`를 추가해 문서 단위로 기존 auto item slice를 삭제하고 reviewed item slice를 적재하도록 했다.
- `DOC-POL-005`, `DOC-POL-006`, `DOC-POL-010` reviewed exports를 `ontology.sqlite`에 적재한 뒤 enrichment pipeline을 재실행했고 전체 validation은 `pass`다.

## Loader Behavior

- target document는 `work/04_ontology/reviewed_items/*__policy-items-reviewed.csv`를 기준으로 잡는다.
- 각 문서별로 기존 `policy_items`, `display_texts`, `policy_item_evidence_links`, `policy_item_taxonomy_map`, `derived_to_display_map`, `curation_assertions`, `data_quality_flags`의 `policy_item` slice를 삭제한 뒤 reviewed CSV를 다시 적재한다.
- 삭제 기준은 `policy_item_evidence_links -> derived_representations -> document_id` 체인이다.
- 이미 curated group에 연결된 item은 삭제하지 않고 실패시키도록 보호했다.

## Classifier / Review Flow Adjustments

- `classify_policy_items_tech_domains.py`
  - 기존 reviewed taxonomy row는 유지하고 `auto_mapped` row만 재생성한다.
- `classify_policy_items_strategies.py`
  - 기존 reviewed strategy row와 reviewed `NO_STRATEGY` assertion이 있는 item은 건너뛴다.
  - `auto_mapped` strategy row만 재생성한다.
- `apply_strategy_review_decisions.py`
  - 현재 queue에 없는 preserved decision이 target item 삭제로 사라진 경우 `inactive_missing_target`로만 기록하고 unresolved로 세지 않는다.

## Load Result

- load summary:
  - `work/04_ontology/reviewed_items/batch_runs/2026-03-16_phase1-reviewed-policy-item-load-batch.json`
- loaded reviewed items:
  - `32`
- loaded reviewed display texts:
  - `32`
- loaded reviewed evidence links:
  - `50`
- loaded reviewed taxonomy rows:
  - `4`
- replaced auto items:
  - `446`

문서별 결과:

- `DOC-POL-005`: auto `193` 삭제 -> reviewed `9` 적재
- `DOC-POL-006`: auto `182` 삭제 -> reviewed `6` 적재, reviewed taxonomy `4` 유지
- `DOC-POL-010`: auto `71` 삭제 -> reviewed `17` 적재

## Pipeline Result

- pipeline command:
  - `python3 scripts/run_ontology_enrichment_pipeline.py --repo-root . --validation-date 2026-03-16`
- ontology validation:
  - `qa/ontology/2026-03-16_ontology-store-validation.json`
  - `status=pass`
- current store stats:
  - `policy_item_count=617`
  - `display_text_count=646`
  - `curation_assertion_count=218`

## Strategy Review Impact

- reviewed item load 이후 strategy queue summary:
  - `qa/ontology/review_queues/policy-item-strategy-review-queue-summary.json`
- current active queue item:
  - `26`
- 정책 분포:
  - `POL-009 15`
  - `POL-010 9`
  - `POL-012 2`
- bucket 분포:
  - `인프라·제도 19`
  - `인재 7`
- 현재 `26`건은 모두 auto-seed decision이 붙어 별도 manual batch는 생성되지 않았다.
  - `25`건은 provisional `no_strategy`
  - `1`건은 `STR-011` provisional reviewed

## Next

- 다음 병목은 reviewed item load가 아니라 이 `26`건 auto-seed decision을 그대로 둘지, reviewed-item 전용 strategy audit packet으로 따로 뽑을지 결정하는 것이다.
