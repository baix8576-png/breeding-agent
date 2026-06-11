# ontology

Owner: `llm_orchestrator`; contract-sensitive entries reviewed by `architect`

Purpose:
- Store controlled vocabulary, concept mappings, metadata schemas, and retrieval trace rules for GeneAgent knowledge assets.

Current standards:
- `knowledge_item.v2.md`: required metadata fields for reference assets consumed by retrieval and orchestration.
- `literature_curation_policy.md`: paper-card curation policy and public `GeneAgent knowledge base` naming rule.
- `knowledge_completion_modules.md`: module-by-module completion map, literature batch plan, source-fetch boundaries, and knowledge acceptance gates.
- `knowledge_ontology_controls.md`: terminology glossary, species naming table, blueprint scope vocabulary, evidence level strategy, doc ID registry policy, and retrieval trace schema.
- `domain_scope_vocab.md`: scientific domain, method-family, and execution-blueprint mapping vocabulary.
- `knowledge_delivery_gate.md`: delivery-time gates for inputs, analysis domains, resource caps, safety, evidence boundaries, report/audit traceability, and expansion limits.

Maintenance notes:
- Do not add new `blueprint_scope`, `evidence_level`, or `source` values in Markdown without updating contracts and tests.
- New formal Markdown files must include `knowledge_item.v2`, except schema explainer files such as `knowledge_item.v2.md`.
