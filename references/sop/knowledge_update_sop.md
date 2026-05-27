# Knowledge Update SOP

## Knowledge update intake

```yaml
knowledge_item.v2:
  doc_id: sop_knowledge_update_intake
  version: v2
  species: multi_species
  blueprint_scope: shared
  evidence_level: sop
  source: sop
  updated_at: 2026-05-26T00:00:00Z
  owner: llm_orchestrator
```

Every knowledge update starts by classifying the asset as Git-versioned summary, local runtime artifact, or rejected input. Shareable summaries belong in `references/*`; raw PDFs, TEI, extracted text, chunks, and indexes belong in `.geneagent/knowledge/*` and stay out of Git unless a later review explicitly allows a small derived summary.

## Knowledge metadata review

```yaml
knowledge_item.v2:
  doc_id: sop_knowledge_metadata_review
  version: v2
  species: multi_species
  blueprint_scope: shared
  evidence_level: sop
  source: sop
  updated_at: 2026-05-26T00:00:00Z
  owner: llm_orchestrator
```

Before merge, every formal Markdown knowledge section must expose `knowledge_item.v2` with valid `doc_id`, `version`, `species`, `blueprint_scope`, `evidence_level`, `source`, `updated_at`, and `owner`. Reviewers must reject duplicate doc IDs and untraceable recommendations.

## Knowledge update verification

```yaml
knowledge_item.v2:
  doc_id: sop_knowledge_update_verification
  version: v2
  species: multi_species
  blueprint_scope: shared
  evidence_level: sop
  source: sop
  updated_at: 2026-05-26T00:00:00Z
  owner: test_eval
```

After adding or changing knowledge assets, run the reference coverage test and the unit knowledge test suite. The minimum gate is full `ReferenceKnowledgeIndexer(Path("references")).build()` without metadata errors, global doc ID uniqueness, and no raw data or local index artifacts under `references/`.
