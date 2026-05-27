# Knowledge Ontology Controls

## Terminology glossary

```yaml
knowledge_item.v2:
  doc_id: ontology_terminology_glossary
  version: v2
  species: multi_species
  blueprint_scope: shared
  evidence_level: sop
  source: ontology
  updated_at: 2026-05-26T00:00:00Z
  owner: llm_orchestrator
```

GeneAgent terminology must be stable across planning, retrieval, reporting, and audit. Terms such as `InputBundle`, `blueprint`, `artifact`, `report_index`, `audit bundle`, `diagnostic preview`, `knowledge_item.v2`, `chunk`, and `traceability` should be used consistently.

Rule: if a term becomes part of a public report or API contract, define it here or in a linked contract document before using synonyms in generated output.

## Species naming table

```yaml
knowledge_item.v2:
  doc_id: ontology_species_naming_table
  version: v2
  species: multi_species
  blueprint_scope: shared
  evidence_level: sop
  source: ontology
  updated_at: 2026-05-26T00:00:00Z
  owner: popgen_quantgen
```

Species names should be normalized for retrieval and reporting. Use common English labels for user-facing summaries and scientific names when precision matters.

Initial table:
- cattle: `Bos taurus`, including taurine and indicine contexts when specified
- pig: `Sus scrofa`
- chicken: `Gallus gallus`
- sheep: `Ovis aries`
- goat: `Capra hircus`
- aquaculture: species-specific name required when possible

Risk boundary: do not merge species-specific parameter assumptions under a generic livestock label without stating the limitation.

## Blueprint scope vocabulary

```yaml
knowledge_item.v2:
  doc_id: ontology_blueprint_scope_vocabulary
  version: v2
  species: multi_species
  blueprint_scope: shared
  evidence_level: sop
  source: ontology
  updated_at: 2026-05-26T00:00:00Z
  owner: architect
```

Allowed `blueprint_scope` values are `qc`, `pca`, `grm`, `genomic_prediction`, and `shared`. These labels route knowledge into the V2 standard execution chain inherited from the V1.5 core loop.

Scope rules:
- `qc`: genotype and sample quality control.
- `pca`: structure analysis and PC interpretation.
- `grm`: genomic relationship matrix construction and relatedness.
- `genomic_prediction`: prediction model planning, execution, and evaluation.
- `shared`: cross-cutting contracts, scheduler, reports, audit, ontology, and safety.

Do not create new scope names in Markdown assets without changing the contract enum and tests.

## Evidence level strategy

```yaml
knowledge_item.v2:
  doc_id: ontology_evidence_level_strategy
  version: v2
  species: multi_species
  blueprint_scope: shared
  evidence_level: sop
  source: ontology
  updated_at: 2026-05-26T00:00:00Z
  owner: safety_fuse
```

Allowed evidence levels are `peer_reviewed`, `benchmark`, `sop`, `incident_verified`, and `expert_opinion`. The level describes the evidence behind the card, not the importance of the topic.

Usage:
- `peer_reviewed`: literature cards and methods supported by papers.
- `benchmark`: measured internal or external benchmark behavior.
- `sop`: approved workflow rule or operating procedure.
- `incident_verified`: observed failure mode or diagnostic pattern.
- `expert_opinion`: curated guidance requiring review before hard default use.

Risk boundary: expert-opinion entries must not be presented as validated scientific defaults.

## Doc ID registry policy

```yaml
knowledge_item.v2:
  doc_id: ontology_doc_id_registry_policy
  version: v2
  species: multi_species
  blueprint_scope: shared
  evidence_level: sop
  source: ontology
  updated_at: 2026-05-26T00:00:00Z
  owner: llm_orchestrator
```

`doc_id` values must be stable, unique, lowercase, and prefixed by knowledge layer: `input_*`, `qc_rule_*`, `structure_*`, `modeling_*`, `playbook_*`, `evaluation_*`, `template_*`, `failure_*`, `sop_*`, `ontology_*`, `diagnostic_*`, or `paper_*`.

Registry checks:
- Do not rename a `doc_id` after it has been used in audit or report output.
- Prefer deprecating a card and adding a successor over reusing a different meaning.
- Run reference coverage tests before merging knowledge changes.

Risk boundary: duplicate or unstable doc IDs break traceability.

## Retrieval trace schema

```yaml
knowledge_item.v2:
  doc_id: ontology_retrieval_trace_schema
  version: v2
  species: multi_species
  blueprint_scope: shared
  evidence_level: sop
  source: ontology
  updated_at: 2026-05-26T00:00:00Z
  owner: llm_orchestrator
```

The minimum retrieval trace is `user_query -> retrieval_filters -> retrieved_doc_id -> chunk_id -> source_path -> page_or_anchor -> evidence_level -> final_answer_or_plan`.

Trace requirements:
- Preserve retrieval filters in diagnostic or audit output when knowledge influences execution.
- Include chunk ID and source path in tool explanations where feasible.
- Keep confidence and hit reason separate from evidence level.
- Mark external fallback evidence separately from local `references/*` assets.

Risk boundary: an answer without trace should be treated as advisory, not as a production planning rule.
