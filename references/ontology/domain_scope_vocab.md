# Domain Scope Vocabulary

This document defines the professional animal genetics and breeding analysis domains used by the GeneAgent knowledge base. `domain_scope` is the scientific curation dimension, while `blueprint_scope` is the typed knowledge-module scope required by `knowledge_item.v2`.

## Domain scope contract

```yaml
knowledge_item.v2:
  doc_id: "ontology_domain_scope_contract"
  version: "v2"
  species: "multi_species"
  blueprint_scope: knowledge_governance
  evidence_level: "sop"
  source: "ontology"
  updated_at: "2026-06-04T00:00:00+08:00"
  owner: "architect"
```

`domain_scope` answers the scientific question: what professional analysis domain does this knowledge support? `blueprint_scope` answers the engineering question: which current GeneAgent knowledge/execution module should index and route the item?

Rules:
- Use `blueprint_scope` for current module routing: `knowledge_governance`, `genotype_processing`, `population_genetics`, `quantitative_genetics`, `association_mapping`, or `reporting_audit`.
- Treat legacy execution blueprint keys such as `qc_pipeline`, `pca_pipeline`, `grm_builder`, `association_mapping_gwas`, and `genomic_prediction` as execution bridges, not formal knowledge metadata values.
- Code may normalize legacy metadata labels `qc`, `pca`, `grm`, `genomic_prediction`, and `shared` for backward compatibility, but new or edited `references/*` assets must use the current module scopes.
- Use `domain_scope` in document body, front matter conventions, reports, and curation tables to describe the scientific domain.
- A knowledge item may map to more than one domain in prose, but one primary domain should be selected for indexing policy.
- Do not create new `domain_scope` names without updating this vocabulary and the analysis-domain README.

Risk boundary: tree-shaped directories are not enough for animal genomics because methods such as ROH, Fst, and PCA support multiple scientific purposes. `domain_scope` keeps those cross-links explicit.

## Domain scope vocabulary

```yaml
knowledge_item.v2:
  doc_id: "ontology_domain_scope_vocabulary"
  version: "v2"
  species: "multi_species"
  blueprint_scope: knowledge_governance
  evidence_level: "sop"
  source: "ontology"
  updated_at: "2026-06-04T00:00:00+08:00"
  owner: "popgen_quantgen"
```

| domain_scope | Scientific domain | Typical questions | Current metadata `blueprint_scope` |
|---|---|---|---|
| `data_preparation_qc` | input readiness and quality control | Are samples, variants, IDs, and formats safe for analysis? | `genotype_processing` |
| `genotype_processing` | variant processing, phasing, imputation, and format conversion | How should VCF/PLINK/BAM-derived inputs be normalized before downstream use? | `genotype_processing` |
| `population_structure` | PCA/MDS/admixture/ancestry and stratification | What population structure or batch/ancestry pattern exists? | `population_genetics` |
| `genetic_diversity_inbreeding` | LD, pi, heterozygosity, ROH, inbreeding, effective population context | How diverse or inbred are groups or individuals? | `population_genetics` |
| `selection_signatures` | selection scans and candidate selected regions | Which loci or regions show evidence of selection, and under which assumptions? | `population_genetics` |
| `association_mapping_gwas_qtl` | GWAS, QTL mapping, fine mapping, candidate gene ranking | Which loci are associated with traits? | `association_mapping` |
| `relationship_matrix_variance_components` | GRM, kinship, pedigree comparison, heritability, variance components | What relationship structure and variance decomposition support models? | `quantitative_genetics` |
| `genomic_prediction_breeding_value` | GBLUP/ssGBLUP/Bayesian/ML prediction and GEBV reporting | How should breeding values or genomic predictions be estimated and validated? | `quantitative_genetics` |
| `functional_genomics_annotation` | gene annotation, pangenome/SV/CNV, eQTL/FarmGTEx, single-cell, regulatory interpretation | What functional evidence explains candidate regions or variants? | `association_mapping` |
| `multi_omics_integration` | transcriptome, epigenome, metabolome, microbiome, proteome integration | How should omics layers be integrated without overclaiming causality? | `knowledge_governance` until a dedicated module exists |
| `species_specific_playbooks` | species-specific defaults and caveats | What differs for cattle, pig, chicken, sheep/goat, aquaculture, or companion animals? | `knowledge_governance` |
| `hpc_execution_reporting_audit` | HPC execution, resource policy, reports, diagnostics, audit, recovery | How should jobs run safely and remain traceable? | `reporting_audit` |

Naming rules:
- Use lowercase snake_case.
- Prefer scientific problem names over tool names.
- Do not encode project versions such as `v1`, `v1_5`, or `v2` in domain names.
- Keep species-specific distinctions inside content or `species` metadata unless the entire file is a species playbook.

## Method family vocabulary

```yaml
knowledge_item.v2:
  doc_id: "ontology_method_family_vocabulary"
  version: "v2"
  species: "multi_species"
  blueprint_scope: knowledge_governance
  evidence_level: "sop"
  source: "ontology"
  updated_at: "2026-06-04T00:00:00+08:00"
  owner: "popgen_quantgen"
```

| method_family | Primary domain_scope | Common methods/tools | Notes |
|---|---|---|---|
| `input_bundle_validation` | `data_preparation_qc` | role matrix, sidecar checks, sample ID matching | Required before any execution blueprint. |
| `variant_sample_qc` | `data_preparation_qc` | missingness, MAF, HWE, heterozygosity, sex/pedigree checks | Thresholds are project-specific until validated. |
| `format_normalization` | `genotype_processing` | VCF normalization, PLINK conversion, allele alignment, liftover | Prevents downstream silent mismatch. |
| `phasing_imputation` | `genotype_processing` | Beagle, Eagle, Minimac-style workflows | Required for haplotype scans such as iHS/XP-EHH. |
| `pca_mds_structure` | `population_structure` | PCA, MDS, EIGENSTRAT, FlashPCA | Structure interpretation must avoid automatic breed claims. |
| `admixture_ancestry` | `population_structure` | STRUCTURE, ADMIXTURE, fastSTRUCTURE | K selection and label interpretation require review. |
| `ld_diversity_statistics` | `genetic_diversity_inbreeding` | LD decay, pi, observed/expected heterozygosity | Often paired with population structure reports. |
| `roh_inbreeding` | `genetic_diversity_inbreeding` | PLINK ROH, FROH, length-class summaries | Also relevant to selection scans and demography. |
| `population_differentiation` | `selection_signatures` | Fst, PBS, dXY, XP-CLR-like contrasts | Requires explicit population definitions. |
| `haplotype_selection_scan` | `selection_signatures` | iHS, XP-EHH, nSL, EHH-family methods | Requires phased genotypes and careful demographic caveats. |
| `sfs_selection_scan` | `selection_signatures` | Tajima's D, Fay and Wu's H, SweeD/RAiSD-style scans | Sensitive to demography and ascertainment. |
| `candidate_region_annotation` | `selection_signatures` | window merging, gene overlap, GO/KEGG, regulatory tracks | Annotation is explanatory, not proof of causality. |
| `mixed_model_gwas` | `association_mapping_gwas_qtl` | MLM, LMM, BOLT/GEMMA/GCTA-style models | Needs structure and relatedness control. |
| `qtl_fine_mapping` | `association_mapping_gwas_qtl` | interval mapping, regional association, credible sets | Evidence level depends on design and validation. |
| `relationship_matrix` | `relationship_matrix_variance_components` | VanRaden GRM, GCTA GRM, PLINK relatedness | Sample ordering and scaling must be traceable. |
| `variance_components` | `relationship_matrix_variance_components` | REML, heritability, genetic correlation | Requires phenotype and model-design review. |
| `prediction_modeling` | `genomic_prediction_breeding_value` | GBLUP, ssGBLUP, Bayesian alphabet, ML models | Validation design is part of the method, not an afterthought. |
| `prediction_evaluation` | `genomic_prediction_breeding_value` | accuracy, bias, calibration, subgroup validation | Avoid breeding decisions from single-run metrics. |
| `functional_annotation` | `functional_genomics_annotation` | gene models, pangenome/SV/CNV, eQTL, single-cell, pathway annotation | Used to interpret candidates from GWAS or selection scans. |
| `omics_integration` | `multi_omics_integration` | transcriptome, epigenome, metabolome, microbiome integration | Must label correlation, mediation, and causality separately. |
| `species_context` | `species_specific_playbooks` | cattle, pig, chicken, sheep/goat, aquaculture playbooks | Species defaults cannot be copied without caveats. |
| `execution_traceability` | `hpc_execution_reporting_audit` | scheduler profile, logs, report_index, audit bundle | Cross-cutting production safety domain. |

## Execution blueprint mapping

```yaml
knowledge_item.v2:
  doc_id: "ontology_domain_execution_blueprint_mapping"
  version: "v2"
  species: "multi_species"
  blueprint_scope: knowledge_governance
  evidence_level: "sop"
  source: "ontology"
  updated_at: "2026-06-04T00:00:00+08:00"
  owner: "architect"
```

| Current execution blueprint | Scientific domains it can currently support | Scientific domains it must not pretend to complete |
|---|---|---|
| `qc_pipeline` | `data_preparation_qc`, part of `genotype_processing` | full imputation/phasing, association mapping, selection scans |
| `pca_pipeline` | `population_structure`, part of `genetic_diversity_inbreeding`, limited `selection_signatures` via Fst/pi/Tajima's D/ROH outputs | complete selection-signature delivery, GWAS/QTL, genomic prediction |
| `grm_builder` | `relationship_matrix_variance_components`, part of `genetic_diversity_inbreeding` through relatedness/inbreeding context | full heritability analysis unless phenotype/model stages are present |
| `association_mapping_gwas` | first-pass `association_mapping_gwas_qtl` through bounded PLINK2 GWAS | QTL/fine mapping, causal interpretation, functional validation |
| `genomic_prediction` | `genomic_prediction_breeding_value`, part of `relationship_matrix_variance_components` | GWAS/QTL/fine mapping, functional validation, breeding decision automation |
| `report_generator` | `hpc_execution_reporting_audit` and report assembly across domains | scientific inference beyond reviewed upstream artifacts |

Execution policy:
- Existing compatibility bioinformatics blueprints are delivery entry points, not the professional taxonomy of animal genomics.
- New scientific domains should first be curated in `references/analysis_domains/` and `references/ontology/`.
- A domain becomes an automated execution blueprint only after pipeline, tool manifest, scheduler profile, report template, safety gates, and tests are added.

## Cross-domain placement rules

```yaml
knowledge_item.v2:
  doc_id: "ontology_cross_domain_placement_rules"
  version: "v2"
  species: "multi_species"
  blueprint_scope: knowledge_governance
  evidence_level: "sop"
  source: "ontology"
  updated_at: "2026-06-04T00:00:00+08:00"
  owner: "llm_orchestrator"
```

Use these placement rules when a method appears to belong to several domains:

- `ROH`: primary domain is `genetic_diversity_inbreeding`; secondary domains may include `selection_signatures` and `relationship_matrix_variance_components`.
- `Fst`: primary domain is `selection_signatures` when used for outlier scans; primary domain is `population_structure` or `genetic_diversity_inbreeding` when used descriptively.
- `PCA`: primary domain is `population_structure`; secondary domains include GWAS covariate design, selection outlier caution, and prediction subgroup validation.
- `GRM`: primary domain is `relationship_matrix_variance_components`; secondary domains include genomic prediction and GWAS correction.
- `GWAS`: primary domain is `association_mapping_gwas_qtl`; route executable first-pass scans through `association_mapping_gwas`, not through `genomic_prediction`.
- `Functional annotation`: primary domain is `functional_genomics_annotation`; it explains candidate regions but does not validate selection, association, or prediction claims by itself.

Risk boundary: when a result is reused across domains, the report must state whether it is descriptive, diagnostic, predictive, or inferential evidence.
