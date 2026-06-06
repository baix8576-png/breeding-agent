# analysis_domains

Owner: `popgen_quantgen`; ontology-sensitive mappings reviewed by `llm_orchestrator` and `architect`.

Purpose:
- Provide the professional animal genetics and breeding analysis-domain layer for the GeneAgent knowledge base.
- Keep scientific domains separate from executable pipeline names.
- Give curators a stable map from user questions to domain knowledge, method families, current execution blueprints, and future expansion boundaries.

This directory is an index-first layer plus detailed domain playbooks. The controlled vocabulary is defined in `references/ontology/domain_scope_vocab.md`. Domain-specific Markdown files should be added one domain at a time so each file can be reviewed, indexed, and tested.

## Why This Layer Exists

The current compatibility execution blueprints are `qc_pipeline`, `pca_pipeline`, `grm_builder`, `association_mapping_gwas`, and `genomic_prediction`. They are useful automation entry points, but they are not a complete scientific taxonomy.

Examples:
- `pca_pipeline` currently carries PCA, LD, ROH, Fst, pi, and Tajima's D, but those belong to different scientific domains.
- `association_mapping_gwas` covers the bounded first GWAS execution bridge; QTL, fine mapping, and functional interpretation remain separate reviewed domains.
- `GRM` supports relatedness, variance components, GWAS correction, and prediction, so it should not be treated as a single-purpose script category.

## Primary Domain Scopes

| domain_scope | Scope summary | First content destination |
|---|---|---|
| `data_preparation_qc` | input contracts, sample IDs, file roles, sample/variant QC | `analysis_domains/data_preparation_qc.md`, `input_specs/`, `qc_rules/` |
| `genotype_processing` | VCF/PLINK/BAM-derived processing, normalization, phasing, imputation | `analysis_domains/genotype_processing.md` |
| `population_structure` | PCA/MDS/admixture/ancestry and stratification interpretation | `analysis_domains/population_structure.md`, `structure_analysis/` |
| `genetic_diversity_inbreeding` | LD, pi, heterozygosity, ROH, inbreeding and diversity metrics | `analysis_domains/genetic_diversity_inbreeding.md` |
| `selection_signatures` | Fst/PBS, iHS/XP-EHH, Tajima's D, XP-CLR, ROH-based candidate regions | `analysis_domains/selection_signatures.md` |
| `association_mapping_gwas_qtl` | GWAS, QTL, fine mapping, candidate gene prioritization | `analysis_domains/association_mapping_gwas_qtl.md` |
| `relationship_matrix_variance_components` | GRM, kinship, pedigree comparison, REML, heritability | `analysis_domains/relationship_matrix_variance_components.md`, `modeling_guides/` |
| `genomic_prediction_breeding_value` | GBLUP, ssGBLUP, Bayesian/ML prediction, GEBV evaluation | `analysis_domains/genomic_prediction_breeding_value.md`, `modeling_guides/`, `evaluation/` |
| `functional_genomics_annotation` | gene annotation, pangenome/SV/CNV, FarmGTEx/eQTL, single-cell, pathways | `analysis_domains/functional_genomics_annotation.md` |
| `multi_omics_integration` | transcriptome, epigenome, metabolome, microbiome, proteome integration | future `analysis_domains/multi_omics_integration.md` |
| `species_specific_playbooks` | cattle, pig, chicken, sheep/goat, aquaculture and comparative caveats | future `analysis_domains/species_specific_playbooks.md` |
| `hpc_execution_reporting_audit` | HPC execution, diagnostics, report index, audit, recovery | `analysis_domains/hpc_execution_reporting_audit.md`, `sop/`, `failure_cases/`, `evaluation/diagnostics/` |

## Current Blueprint Mapping

| User asks for | Primary domain_scope | Current execution bridge | Current status |
|---|---|---|---|
| QC, missingness, MAF, HWE, sample consistency | `data_preparation_qc` | `qc_pipeline` | supported execution entry |
| VCF/PLINK conversion or normalization | `genotype_processing` | `qc_pipeline` plus tool-specific scripts when available | partial; processing playbook available, dedicated advanced wrappers not yet complete |
| PCA, population structure, stratification | `population_structure` | `pca_pipeline` | supported execution entry |
| LD decay, nucleotide diversity, ROH/inbreeding | `genetic_diversity_inbreeding` | `pca_pipeline`, `grm_builder` for relatedness context | partial; needs clearer report templates |
| Fst/pi/Tajima's D basic scans | `selection_signatures` | `pca_pipeline` | partial; not a complete selection-signature workflow |
| iHS, XP-EHH, XP-CLR, PBS, haplotype scans | `selection_signatures` | no dedicated execution blueprint yet | knowledge/planning only until implemented |
| GRM, kinship, relatedness | `relationship_matrix_variance_components` | `grm_builder` | supported execution entry |
| Heritability or variance components | `relationship_matrix_variance_components` | `grm_builder` plus `genomic_prediction` depending on phenotype/model inputs | partial; needs explicit model contract |
| GWAS/QTL/fine mapping | `association_mapping_gwas_qtl` | `association_mapping_gwas` for first-pass PLINK2 GWAS | GWAS supported; QTL/fine mapping remains knowledge/planning only |
| GBLUP, ssGBLUP, GEBV | `genomic_prediction_breeding_value` | `genomic_prediction` | supported execution entry |
| Functional annotation of candidate regions | `functional_genomics_annotation` | no dedicated execution blueprint yet | knowledge/report interpretation only; playbook available |
| Multi-omics integration | `multi_omics_integration` | no dedicated execution blueprint yet | knowledge/planning only |
| Species-specific method caveats | `species_specific_playbooks` | all current blueprints through retrieval context | knowledge layer |
| Remote execution, diagnostics, audit | `hpc_execution_reporting_audit` | scheduler + report generator + audit paths | supported system layer |

## Current Domain Files

| File | Primary domain_scope | Current coverage |
|---|---|---|
| `data_preparation_qc.md` | `data_preparation_qc` | domain scope, input roles, sample ID policy, QC decision boundary, and `scripts/genotype_processing/` execution bridge |
| `genotype_processing.md` | `genotype_processing` | format normalization, allele alignment, liftover, phasing/imputation boundaries, and conservative execution bridge |
| `population_structure.md` | `population_structure` | PCA scope, LD pruning policy, stratification risk, admixture boundary, and `scripts/population_genetics/` execution bridge |
| `genetic_diversity_inbreeding.md` | `genetic_diversity_inbreeding` | LD, ROH, pi/heterozygosity, diversity interpretation, and first-pass execution artifacts |
| `selection_signatures.md` | `selection_signatures` | population definition, statistic-family boundary, candidate-region policy, and first-pass Fst/pi/Tajima execution bridge |
| `association_mapping_gwas_qtl.md` | `association_mapping_gwas_qtl` | first-pass GWAS, population correction, QTL/fine-mapping boundary, candidate interpretation, and `scripts/association_mapping/` execution bridge |
| `functional_genomics_annotation.md` | `functional_genomics_annotation` | gene model, regulatory evidence, pangenome/SV/CNV, eQTL/FarmGTEx/single-cell, candidate reporting, and automation boundary |
| `relationship_matrix_variance_components.md` | `relationship_matrix_variance_components` | GRM construction, variance components, sample-order policy, and `scripts/quantitative_genetics/run_relationship_matrix.sh` execution bridge |
| `genomic_prediction_breeding_value.md` | `genomic_prediction_breeding_value` | model family policy, validation, breeding-decision boundary, and `scripts/quantitative_genetics/run_breeding_value_prediction.sh` execution bridge |
| `hpc_execution_reporting_audit.md` | `hpc_execution_reporting_audit` | trusted remote execution evidence, report index, diagnostics, traceability, audit bundle, and `scripts/reporting_audit/` execution bridge |

## Curation Rules

- Use domain names from `references/ontology/domain_scope_vocab.md`.
- Use current `knowledge_item.v2.blueprint_scope` module names: `knowledge_governance`, `genotype_processing`, `population_genetics`, `quantitative_genetics`, `association_mapping`, or `reporting_audit`.
- Keep legacy execution blueprint keys such as `qc_pipeline`, `pca_pipeline`, `grm_builder`, and `genomic_prediction` in execution-bridge tables, not in formal knowledge metadata.
- For cross-domain methods, write a primary domain plus secondary-domain notes in the body.
- Do not duplicate the same method explanation across many files; use cross-links and method-family tables.
- Do not claim an execution blueprint is complete just because a method has a knowledge card.

## Expansion Order

Recommended domain-file expansion order:

1. `multi_omics_integration.md`, after functional annotation is stable enough to support cross-omics interpretation.
2. `species_specific_playbooks.md`, after core cross-species domains are stable enough for species defaults and caveats.

## Acceptance Criteria For A New Domain File

A new domain file should include:
- at least one `knowledge_item.v2` block under a `##` heading
- primary `domain_scope`
- method families
- required inputs and sidecars
- current execution bridge
- not-yet-automated boundary
- reporting and audit expectations
- failure modes and safety notes
- links to paper cards, SOPs, parameter playbooks, and report templates
