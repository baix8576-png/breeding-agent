# GeneAgent Knowledge Completion Modules

This file is the planning map for completing the GeneAgent knowledge base one small module at a time. It is a Git-versioned ontology asset, not a runtime cache and not a PDF store.

The public name is always `GeneAgent knowledge base`. Development labels such as V1, V1.5, and V2 are history or schema context only; they are not user-facing knowledge-base names.

## Completion Scope Map

```yaml
knowledge_item.v2:
  doc_id: ontology_knowledge_completion_scope_map
  version: v2
  species: multi_species
  blueprint_scope: knowledge_governance
  evidence_level: sop
  source: ontology
  updated_at: 2026-06-06T00:00:00+08:00
  owner: llm_orchestrator
```

The knowledge base is completed by module, not by old execution-blueprint names. `domain_scope` and `references/analysis_domains/*` define the scientific organization; `blueprint_scope` remains a compatibility filter for current retrieval and execution routing.

| Module | Scientific scope | Primary assets | Completion target |
|---|---|---|---|
| M01 | Knowledge governance and ontology | `references/ontology/*` | vocabularies, doc ID registry rules, evidence levels, source fetching policy |
| M02 | Input bundle and sample identity | `references/input_specs/*` | file roles, sidecars, sample ID normalization, phenotype/covariate/pedigree checks |
| M03 | Genotype data QC | `references/qc_rules/*`, `references/parameter_playbooks/qc_defaults.md` | missingness, MAF, HWE, heterozygosity, sex/duplicate checks |
| M04 | Genotype processing | `references/analysis_domains/genotype_processing.md` | VCF/PLINK normalization, allele alignment, liftover, phasing, imputation boundaries |
| M05 | Population structure | `references/analysis_domains/population_structure.md`, `references/structure_analysis/*` | PCA, pruning, relatedness, admixture, cluster-labeling cautions |
| M06 | Genetic diversity and inbreeding | `references/analysis_domains/genetic_diversity_inbreeding.md` | ROH, LD decay, nucleotide diversity, heterozygosity, kinship interpretation |
| M07 | Selection signatures | `references/analysis_domains/selection_signatures.md` | Fst, XP-EHH, iHS, XP-CLR, pi ratio, Tajima D, candidate-region reporting |
| M08 | Association mapping and QTL | `references/analysis_domains/association_mapping_gwas_qtl.md` | GWAS model choice, covariates, mixed models, fine mapping, QTL evidence boundaries |
| M09 | Functional genomics and annotation | `references/analysis_domains/functional_genomics_annotation.md` | gene models, regulatory atlases, eQTL, single-cell, pangenome/SV/CNV interpretation |
| M10 | Relationship matrices and variance components | `references/analysis_domains/relationship_matrix_variance_components.md` | GRM, numerator relationship matrix, REML, heritability, sample-order safeguards |
| M11 | Genomic prediction and breeding value | `references/analysis_domains/genomic_prediction_breeding_value.md` | GBLUP, ssGBLUP, Bayesian/ML models, CV, bias, calibration, GEBV interpretation |
| M12 | Species overlays | `references/papers/species_literature_index.md` plus domain files | cattle, pig, poultry, sheep/goat, aquaculture defaults and cautions |
| M13 | Literature landmark packs | `references/papers/*` | classic methods and 2022-2026 high-impact animal genomics cards |
| M14 | Execution, reporting, diagnostics, audit | `references/sop/*`, `references/evaluation/*`, `references/failure_cases/*`, `references/report_templates/*` | safe remote execution, failure diagnosis, report index, audit bundle, review gates |
| M15 | Retrieval QA and index health | `tests/unit/knowledge/*` and ontology controls | chunk traceability, metadata validity, regression queries, fetcher safety tests |

Every module must leave at least one searchable `knowledge_item.v2` chunk, a reader-facing explanation, and a retrieval query that proves the module can be found through local-first RAG.

## Module Order and Dependency Gates

```yaml
knowledge_item.v2:
  doc_id: ontology_knowledge_completion_module_order
  version: v2
  species: multi_species
  blueprint_scope: knowledge_governance
  evidence_level: sop
  source: ontology
  updated_at: 2026-06-06T00:00:00+08:00
  owner: llm_orchestrator
```

The safe completion order is:

1. Finish M01 ontology controls before adding new large batches. This prevents inconsistent `doc_id`, source, evidence, and domain naming.
2. Finish M02-M04 data intake and genotype processing before analysis-specific methods. These modules define which inputs are legal and how sample identity is preserved.
3. Finish M05-M08 population genetics and association mapping before interpretation-heavy functional annotation. These modules generate most candidate loci and risk reports.
4. Finish M09-M11 functional and quantitative genetics after the core analysis domains are stable, because they depend on output interpretation, model assumptions, and evidence ranking.
5. Add M12 species overlays only after shared method rules exist, so cattle, pig, poultry, sheep/goat, and aquaculture differences do not become duplicated method files.
6. Add M13 literature packs in batches, linking each paper card to the relevant module and `domain_scope` wording.
7. Finish M14-M15 operational and retrieval QA after the knowledge content exists, then keep them running as regression gates for every later batch.

Definition of done for one module:

- It has a formal Markdown asset under the assigned `references/*` path.
- It contains validated `knowledge_item.v2` metadata with a globally unique `doc_id`.
- It names the relevant `domain_scope`, method family, input type, species scope, and execution-blueprint bridge.
- It states default-safe parameter guidance and the boundary where operator review is required.
- It contributes at least one retrieval regression query or is covered by an existing query.
- It does not commit raw PDFs, TEI/XML, extracted full text, FASTQ, VCF, BAM, CRAM, or indexes.

## Literature Batch Plan

```yaml
knowledge_item.v2:
  doc_id: ontology_knowledge_completion_literature_batches
  version: v2
  species: multi_species
  blueprint_scope: knowledge_governance
  evidence_level: sop
  source: ontology
  updated_at: 2026-06-06T00:00:00+08:00
  owner: llm_orchestrator
```

Literature enters the Git layer as curated cards and enters the local runtime layer as optional raw source files. The first complete literature pass should use small batches that can be reviewed independently:

| Batch | Size target | Scope | Git output | Local runtime output |
|---|---:|---|---|---|
| L01 | 10-15 | Foundational quantitative genetics and BLUP | paper cards in `references/papers/animal_genomics_classic_landmarks.md` | optional local PDFs only when license permits |
| L02 | 10-15 | GBLUP, ssGBLUP, GRM, REML | paper cards linked to M10-M11 | optional local PDFs |
| L03 | 10-15 | GWAS, QTL, mixed models, population correction | paper cards linked to M08 | optional local PDFs |
| L04 | 10-15 | Population structure, LD, ROH, selection signatures | paper cards linked to M05-M07 | optional local PDFs |
| L05 | 15-20 | 2022-2026 pangenome, T2T, SV/CNV, WGS prediction | paper cards linked to M09-M13 | optional local OA sources |
| L06 | 15-20 | 2022-2026 FarmGTEx, eQTL, single-cell, regulatory atlases | paper cards linked to M09 and species overlays | optional local OA sources |
| L07 | 15-20 | Species-focused cattle, pig, poultry, sheep/goat, aquaculture | species index updates plus paper cards | optional local OA sources |
| L08 | 10-15 | Operational SOP references, software docs, diagnostics | SOP/failure-case cards, not raw manuals in Git | optional local source docs |

Each batch should be accepted only after DOI/PMID or publisher metadata is checked, duplicates are removed, and every card states the GeneAgent use: parameter suggestion, risk boundary, report interpretation, or diagnostic hint.

## Ingestion Boundary and Batch Fetch Rules

```yaml
knowledge_item.v2:
  doc_id: ontology_knowledge_completion_ingestion_boundary
  version: v2
  species: multi_species
  blueprint_scope: knowledge_governance
  evidence_level: sop
  source: ontology
  updated_at: 2026-06-06T00:00:00+08:00
  owner: llm_orchestrator
```

Batch fetching is a local-runtime convenience, not a Git ingestion path. The fetcher must obey these rules:

- It may write only under `.geneagent/knowledge/raw_pdfs/`, `.geneagent/knowledge/source_docs/`, and `.geneagent/knowledge/fetch_reports/`.
- It must reject paths with `..`, Windows backslashes, absolute paths outside the local knowledge root, or destinations under `references/`.
- It must skip entries marked `restricted`, `unknown_license`, or missing an explicit open-access/public-document flag.
- It must never fetch or store account credentials, cookies, private tokens, or publisher session data.
- It must record a status report with `doc_id`, source URL, destination, skipped/downloaded status, checksum when available, and reason.
- It must not create paper cards automatically from raw full text without a later human-curation step.

Recommended manifest fields:

| Field | Required | Meaning |
|---|---|---|
| `doc_id` | yes | Links the source file to a future or existing knowledge card |
| `module_id` | yes | One of M01-M15 or a literature batch such as L05 |
| `title` | yes | Human-readable title for review |
| `url` | yes | Public source URL or DOI landing URL |
| `output_name` | yes | File name only, no directory separators |
| `access` | yes | `open_access`, `public_document`, `restricted`, or `unknown_license` |
| `expected_sha256` | no | Optional checksum for repeatable downloads |

## Acceptance Gates

```yaml
knowledge_item.v2:
  doc_id: ontology_knowledge_completion_acceptance_gates
  version: v2
  species: multi_species
  blueprint_scope: knowledge_governance
  evidence_level: sop
  source: ontology
  updated_at: 2026-06-06T00:00:00+08:00
  owner: llm_orchestrator
```

A knowledge-completion batch is ready only when these gates are satisfied:

- `ReferenceKnowledgeIndexer(Path("references")).build()` returns no metadata errors.
- `doc_id` values are globally unique across all formal Markdown assets.
- Every formal knowledge file outside the allowlist contains at least one `knowledge_item.v2` block.
- Each standard `references/*` directory contributes searchable chunks.
- Retrieval regression queries cover input contracts, genotype QC, population genetics, association mapping, quantitative genetics, functional annotation, reporting/audit, diagnostics, and literature curation.
- Batch fetch tests prove restricted sources are skipped, safe local destinations are enforced, and no raw documents are written into Git-versioned paths.
- Git diff contains no raw entity data, raw PDFs, TEI/XML, extracted full text, chunks, BM25 indexes, embedding indexes, credentials, or private server details.
