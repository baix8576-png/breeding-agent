# Knowledge Update Workflow (V1.5 -> V2 Ready)

This guide defines the required update loop for `references/*` and `src/knowledge/*` so new evidence can be added without breaking local-first retrieval guarantees.

## Scope
- Evidence assets: `references/papers/`, `references/sop/`, `references/parameter_playbooks/`, `references/failure_cases/`, `references/ontology/`
- Retrieval code: `src/knowledge/retrieval.py`, `src/knowledge/indexing.py`
- Metadata schema: `knowledge_item.v2`

## Update Flow
1. Intake and triage:
- Create a change card with `intent_domain=knowledge`, `stage_id=Local-first RAG`.
- Label the change as one of: `paper`, `sop`, `parameter_playbook`, `failure_case`, `ontology`.

2. Evidence normalization:
- For each new item, provide: `doc_id`, `version`, `species`, `blueprint_scope`, `evidence_level`, `source`, `updated_at`, `owner`.
- Ensure each item states method boundary, parameter suggestions, and risk notes.

3. Asset landing:
- Write structured markdown card(s) under the proper `references/*` subdirectory.
- Keep original large artifacts (PDF/raw datasets) outside Git when needed; store only metadata, card content, and trace links in repo.

4. Index refresh and retrieval checks:
- Rebuild/update local knowledge indexing path used by `ReferenceKnowledgeIndexer`.
- Verify retrieval output includes evidence-chain fields: hit reasons, conflict entries, confidence sources, confidence scores.

5. Fallback policy gate check:
- Confirm external fallback still follows configured gate policy (`tiered` by default).
- Confirm sensitive requests remain blocked when domain sensitivity ceiling is exceeded.

6. Regression and acceptance:
- Run targeted tests for retrieval relevance and evidence consistency.
- Run full gates: `python -m compileall src tests`, `python -m pytest -q`.

## Minimal Reviewer Checklist
- [ ] New knowledge item passes `knowledge_item.v2` required fields.
- [ ] Blueprint scope is one of `qc/pca/grm/genomic_prediction/shared`.
- [ ] Evidence chain fields are visible in resolver output.
- [ ] External fallback branch remains explicit, auditable, and policy-gated.
- [ ] Unit/integration tests cover the new evidence behavior.

