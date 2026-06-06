# Literature Curation Policy

This policy defines how papers enter the GeneAgent knowledge base.

## Curation scope and naming
```yaml
knowledge_item.v2:
  doc_id: "policy_literature_curation_scope"
  version: "v2"
  species: "multi_species"
  blueprint_scope: knowledge_governance
  evidence_level: "sop"
  source: "ontology"
  updated_at: "2026-05-26T20:20:00+08:00"
  owner: "llm_orchestrator"
```
- Public name: `GeneAgent 鐭ヨ瘑搴揱 / `GeneAgent knowledge base`.
- Version words such as V1, V1.5, and V2 are development history only; they are not user-facing knowledge-base names.
- `knowledge_item.v2` remains the metadata schema version and is not a product-stage label.
- Paper-card files under `references/papers/*` store copyright-safe summaries, not original PDFs.

## Inclusion tiers
```yaml
knowledge_item.v2:
  doc_id: "policy_literature_inclusion_tiers"
  version: "v2"
  species: "multi_species"
  blueprint_scope: knowledge_governance
  evidence_level: "sop"
  source: "ontology"
  updated_at: "2026-05-26T20:20:00+08:00"
  owner: "llm_orchestrator"
```
- Tier A: landmark theory/method papers that define durable concepts such as BLUP, GBLUP, ssGBLUP, PCA, FST, LD, ROH, imputation, and multiple testing.
- Tier B: high-quality recent primary papers from 2022-2026 in animal genomics, functional genomics, pangenomes, single-cell atlases, and genomic prediction.
- Tier C: recent high-quality reviews used for orientation, gap analysis, and emerging-field synthesis.
- Exclusion: low-quality outlets, unsupported preprints, unverified PDFs, unclear copyright status, or papers that cannot be mapped to GeneAgent use.

## Metadata and traceability
```yaml
knowledge_item.v2:
  doc_id: "policy_literature_metadata_traceability"
  version: "v2"
  species: "multi_species"
  blueprint_scope: knowledge_governance
  evidence_level: "sop"
  source: "ontology"
  updated_at: "2026-05-26T20:20:00+08:00"
  owner: "llm_orchestrator"
```
- Each retrievable paper section must include `knowledge_item.v2`.
- Each card must include Paper, Year, DOI/PMID, species/data, GeneAgent use, boundary/risk, and source links.
- If DOI/PMID is not fully verified, the card must say `verify before citation export`.
- Formal citation exports must refresh metadata through CrossRef, PubMed, Semantic Scholar, publisher pages, or Zotero.

## Recency audit
```yaml
knowledge_item.v2:
  doc_id: "policy_literature_recency_audit"
  version: "v2"
  species: "multi_species"
  blueprint_scope: knowledge_governance
  evidence_level: "sop"
  source: "ontology"
  updated_at: "2026-05-26T20:20:00+08:00"
  owner: "llm_orchestrator"
```
- For the current audit date 2026-05-26, the last-five-year window is 2022-2026.
- Landmark papers can be older but must be labelled as foundational.
- Emerging fields such as pangenomes, single-cell omics, graph genomes, WGS prediction, multi-omics, and AI-enabled genomics should be dominated by 2022-2026 evidence.
- Recency must not be padded with low-quality journals; quality outranks year.

## Local and Git boundaries
```yaml
knowledge_item.v2:
  doc_id: "policy_literature_local_git_boundary"
  version: "v2"
  species: "multi_species"
  blueprint_scope: knowledge_governance
  evidence_level: "sop"
  source: "ontology"
  updated_at: "2026-05-26T20:20:00+08:00"
  owner: "llm_orchestrator"
```
- Git-tracked knowledge: summary cards, SOPs, parameter notes, failure cases, and metadata schemas.
- Local-only knowledge: original PDFs, GROBID TEI, extracted full text, chunks, BM25 indexes, embedding indexes.
- Source links may point to publishers, PubMed, CrossRef, Semantic Scholar, or Google Scholar.
- Do not commit copyrighted PDFs or full-text extraction outputs without explicit license review.
