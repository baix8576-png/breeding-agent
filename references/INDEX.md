# references index

This directory is the Git-versioned asset layer of the GeneAgent knowledge base. It stores copyright-safe summaries, templates, SOPs, parameter playbooks, diagnostic patterns, ontology controls, and curated paper cards.

Runtime-only assets such as raw PDFs, GROBID TEI, extracted full text, chunks, BM25 indexes, and embedding indexes belong under `.geneagent/knowledge/*` and are not committed.

## Subdirectories

| Directory | Owner | Formal assets |
|---|---|---|
| `analysis_domains/` | `popgen_quantgen`, reviewed by `llm_orchestrator` and `architect` | scientific-domain index plus data preparation, genotype processing, population structure, diversity/inbreeding, selection-signature, association-mapping, functional-annotation, quantitative-genetics, and reporting/audit domain playbooks |
| `input_specs/` | `popgen_quantgen` | `input_bundle_contract.md`, `dataset-bundle-template.md` |
| `qc_rules/` | `popgen_quantgen` | `default_qc_threshold_profile.md` |
| `structure_analysis/` | `popgen_quantgen` | `pca_structure_interpretation.md` |
| `modeling_guides/` | `popgen_quantgen` | `genomic_modeling_routes.md` |
| `evaluation/` | `popgen_quantgen`, `safety_fuse`, `hpc_scheduler` | `evaluation_metric_playbook.md`, diagnostics pattern files |
| `report_templates/` | `popgen_quantgen`, `orchestrator`, `safety_fuse` | QC, structure, genomic prediction, diagnostic, audit, and `report_index.v2` templates |
| `papers/` | `popgen_quantgen` with metadata review by `llm_orchestrator` | core method cards, animal genomics landmark cards, recent high-impact cards, species index |
| `sop/` | `popgen_quantgen`, `llm_orchestrator`, `hpc_scheduler` | blueprint SOPs, GROBID ingestion SOP, knowledge update SOP, report review SOP, HPC execution SOP |
| `parameter_playbooks/` | `popgen_quantgen`, `hpc_scheduler` | QC, PCA, GRM, genomic prediction CV, scheduler resource presets |
| `failure_cases/` | `popgen_quantgen`, `hpc_scheduler`, `safety_fuse` | operational failure cases and safe retry boundaries |
| `ontology/` | `llm_orchestrator`, `architect` | `knowledge_item.v2`, curation policy, knowledge completion modules, delivery gates, glossary, species naming, scope/evidence/doc ID/retrieval trace controls |

## Diagnostics Entry Point

- `evaluation/diagnostics/README.md`: stable markdown schema (`diagnostics_v1`) for pattern-based troubleshooting knowledge.
- `evaluation/diagnostics/scheduler_error_patterns.md`: common SLURM/PBS submit and poll failures with executable remediation steps.
- `evaluation/diagnostics/bio_tool_error_patterns.md`: common `plink2`/`bcftools`/`vcftools`/`gcta64` failures with executable remediation steps.

## Metadata Standard

- `ontology/knowledge_item.v2.md`: required field contract for formal knowledge assets (`doc_id/version/species/blueprint_scope/evidence_level/source/updated_at/owner`).
- `ontology/domain_scope_vocab.md`: controlled scientific-domain vocabulary that maps professional analysis domains to current execution blueprints.
- `ontology/knowledge_completion_modules.md`: module-by-module completion map, literature batch plan, ingestion boundaries, and acceptance gates.
- `ontology/knowledge_delivery_gate.md`: delivery-time gate catalog for input readiness, domain execution, resource caps, safety breakers, report/audit traceability, literature evidence boundaries, and expansion limits.
- All formal Markdown knowledge files, except README/index/schema explainers, must include at least one `knowledge_item.v2` block under a `##` heading.
- `doc_id` values must be globally unique.

## Current Paper Seed Packs

- `papers/qc_core_papers_v1.md`
- `papers/pca_core_papers_v1.md`
- `papers/grm_core_papers_v1.md`
- `papers/genomic_prediction_core_papers_v1.md`
- `papers/animal_genomics_classic_landmarks.md`
- `papers/animal_genomics_recent_high_impact_2022_2026.md`
- `papers/species_literature_index.md`

## Literature Curation Policy

- `ontology/literature_curation_policy.md`
- Public-facing name: `GeneAgent knowledge base`
- Development-history labels (`V1`, `V1.5`, `V2`) must not replace the user-facing knowledge-base name.

## Conventions

- Keep thresholds and modeling choices explicitly marked as project-specific until validated by SOPs.
- Reference files should explain assumptions and risk boundaries.
- If a blueprint depends on a reference file, list the exact file path inside the blueprint asset index.
- Do not commit raw VCF, BAM, FASTQ, FASTA, PDF, TEI, extracted full text, chunks, BM25 indexes, or embedding indexes.
