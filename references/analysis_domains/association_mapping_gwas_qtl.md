# Association Mapping GWAS And QTL Domain

This file defines the association-mapping knowledge domain behind the `association_mapping_gwas` execution bridge. It separates first-pass GWAS execution from QTL mapping, fine mapping, and candidate interpretation.

## Domain scope and scientific intent

```yaml
knowledge_item.v2:
  doc_id: domain_association_mapping_gwas_qtl_scope
  version: v2
  species: multi_species
  blueprint_scope: association_mapping
  evidence_level: sop
  source: sop
  updated_at: 2026-06-06T00:00:00+08:00
  owner: popgen_quantgen
```

Primary `domain_scope`: `association_mapping_gwas_qtl`.

Association mapping asks whether genotype markers or genomic regions are statistically associated with phenotypes under an explicit model, population structure control, and multiple-testing policy. In animal genetics and breeding, this domain must handle breed structure, family relatedness, commercial-line selection history, phenotype definition, and species-specific annotation gaps.

Current execution bridge:
- `association_mapping_gwas` executable blueprint key.
- `scripts/association_mapping/run_gwas.sh` bounded first-pass PLINK2 `--glm` wrapper.
- `blueprint_scope=association_mapping` in `knowledge_item.v2` metadata; `association_mapping_gwas` remains an execution bridge key, not the metadata scope.

Current automated scope:
- prepare first-pass GWAS artifacts
- preserve phenotype/covariate/model metadata
- report that locus interpretation requires review

Not yet automated:
- mixed-model GWAS with GRM/kinship correction
- QTL interval mapping
- regional fine mapping and credible sets
- functional candidate gene prioritization
- causal interpretation or breeding decision automation

Risk boundary: association is not causation. A significant marker is a hypothesis that needs population, model, LD, annotation, and validation context.

## GWAS input and model policy

```yaml
knowledge_item.v2:
  doc_id: domain_association_mapping_gwas_input_model_policy
  version: v2
  species: multi_species
  blueprint_scope: association_mapping
  evidence_level: sop
  source: sop
  updated_at: 2026-06-06T00:00:00+08:00
  owner: popgen_quantgen
```

GWAS planning must make the phenotype and model contract explicit before executing any marker-trait scan.

Required inputs:
- genotype matrix: complete PLINK binary triplet or VCF convertible by the wrapper
- phenotype table with sample ID and trait column
- trait definition, units, transformation status, and missing-value code when available
- covariate table when fixed effects are needed
- sample ID reconciliation from genotype to phenotype and covariate roles

Model planning checks:
- identify whether the trait is quantitative, binary, count, ordinal, repeated, or survival-like
- record whether PLINK2 `--glm` is sufficient for first-pass screening
- record trait column name or the reason it remains a hint rather than an enforced parser contract
- preserve covariate names and provenance when supplied
- state if population PCs, batch, sex, age, farm, or line effects are only recommended and not yet applied

Blocking conditions:
- no phenotype table
- genotype IDs and phenotype IDs cannot be reconciled
- duplicate phenotype rows without an aggregation policy
- covariate IDs mismatch the phenotype/genotype cohort
- trait type requires a model family not supported by the current wrapper

Risk boundary: a syntactically valid PLINK2 command can still be scientifically invalid if the phenotype, covariates, and sample alignment are not reviewed.

## Population correction and relatedness policy

```yaml
knowledge_item.v2:
  doc_id: domain_association_mapping_population_correction_policy
  version: v2
  species: multi_species
  blueprint_scope: association_mapping
  evidence_level: expert_opinion
  source: sop
  updated_at: 2026-06-06T00:00:00+08:00
  owner: popgen_quantgen
```

Population structure and relatedness are first-order GWAS risks in animal datasets. Breed composition, family structure, selection lines, farm or batch effects, and commercial breeding design can produce association signals that are not trait-causing loci.

Minimum review before interpreting associations:
- PCA or structure diagnostics from the same retained cohort
- known breed, line, farm, batch, sex, and age covariates when relevant
- relatedness or GRM context when close relatives are present
- phenotype distribution by population or batch
- genomic inflation, QQ plot, or equivalent calibration artifact when implemented

Current bridge limitation:
- `run_gwas.sh` runs a bounded PLINK2 `--glm` first pass.
- It does not yet build mixed-model GWAS with GRM random effects.
- It does not automatically choose or inject PCA covariates unless supplied by the planned inputs.

Recommended escalation:
- use mixed-model GWAS when close relatives, strong stratification, or family design is expected
- require GRM/kinship outputs before interpreting high-risk livestock cohorts
- treat simple linear/logistic GWAS as exploratory screening when correction is incomplete

Risk boundary: population correction is not a cosmetic report feature. It changes whether a marker-level association is interpretable.

## QTL and fine-mapping boundary

```yaml
knowledge_item.v2:
  doc_id: domain_association_mapping_qtl_fine_mapping_boundary
  version: v2
  species: multi_species
  blueprint_scope: association_mapping
  evidence_level: sop
  source: sop
  updated_at: 2026-06-06T00:00:00+08:00
  owner: popgen_quantgen
```

QTL mapping and fine mapping are related to GWAS but are not the same automated workflow.

Boundary table:

| Task | Typical inputs | Current status |
|---|---|---|
| first-pass GWAS | genotype matrix, phenotype, covariates | executable through PLINK2 bridge |
| family/linkage QTL | pedigree design, markers, phenotypes, map | knowledge/planning only |
| regional conditional analysis | lead marker, region, covariates, LD context | knowledge/planning only |
| fine mapping | summary statistics, LD reference, priors, credible set method | knowledge/planning only |
| eQTL or molecular QTL | expression/molecular phenotype, genotype, tissue/cell context | knowledge/planning only |

Fine-mapping prerequisites:
- high-quality association statistics
- compatible LD reference or individual genotype data
- consistent genome assembly and allele orientation
- credible-set method and prior assumptions
- region definition and marker inclusion rules

Risk boundary: a GWAS peak is not a fine-mapped causal variant. Fine mapping needs its own method, assumptions, and validation artifacts.

## Candidate interpretation policy

```yaml
knowledge_item.v2:
  doc_id: domain_association_mapping_candidate_interpretation_policy
  version: v2
  species: multi_species
  blueprint_scope: association_mapping
  evidence_level: expert_opinion
  source: sop
  updated_at: 2026-06-06T00:00:00+08:00
  owner: popgen_quantgen
```

Candidate gene and locus interpretation is a report-level reasoning task, not a direct output of PLINK2 `--glm`.

Minimum interpretation fields:
- marker ID, chromosome, position, reference assembly, and allele coding
- trait, model, covariates, sample count, and test type
- p-value or effect estimate with multiple-testing context
- local LD or regional support if available
- nearest gene or overlapping annotation source, if used
- QTL, eQTL, FarmGTEx, single-cell, pangenome/SV, or literature support when available

Do not overclaim:
- nearest gene equals causal gene
- single association equals validated breeding marker
- cross-species functional analogy proves mechanism
- public QTL overlap removes the need for cohort-specific validation
- pangenome or SV interpretation is valid without compatible variant representation

Escalation path:
- route biological explanation to `functional_genomics_annotation`
- route validation design to evaluation guidance
- route marker deployment or breeding decisions to a separate reviewed decision workflow

Risk boundary: candidate interpretation should produce ranked hypotheses and evidence traces, not final causal claims.

## Execution bridge and artifacts

```yaml
knowledge_item.v2:
  doc_id: domain_association_mapping_execution_bridge
  version: v2
  species: multi_species
  blueprint_scope: association_mapping
  evidence_level: sop
  source: sop
  updated_at: 2026-06-06T00:00:00+08:00
  owner: popgen_quantgen
```

The current execution bridge is intentionally narrow: `scripts/association_mapping/run_gwas.sh` runs bounded PLINK2 `--glm` and writes traceable first-pass GWAS artifacts.

Artifact mapping:

| Domain concern | Current artifact |
|---|---|
| cohort/input alignment | `results/association/gwas/cohort_alignment.json` |
| model summary | `results/association/gwas/model_spec.json` |
| PLINK2 GWAS result index | `results/association/gwas/README.md` |
| row-count metric | `results/association/gwas/metrics.tsv` |
| human-readable summary | `reports/gwas_summary.md` |
| run traceability | `results/association/gwas/run_manifest.json`, `results/association/gwas/audit_sidecar.json` |

Submit blockers:
- missing genotype matrix
- missing phenotype table
- missing `plink2`
- ID mismatch or duplicate phenotype rows surfaced by upstream validation
- non-POSIX paths
- resource request above configured caps
- output overwrite without approval

Must remain knowledge/planning only until implemented:
- mixed-model GWAS with GRM random effects
- QTL interval mapping
- fine mapping and credible sets
- candidate gene annotation and biological validation

Risk boundary: this bridge supports first-pass association mapping, not full locus discovery, fine mapping, or functional validation.

## Trait model policy

```yaml
knowledge_item.v2:
  doc_id: domain_association_mapping_trait_model_policy
  version: v2
  species: multi_species
  blueprint_scope: association_mapping
  evidence_level: sop
  source: sop
  updated_at: 2026-06-06T21:30:00+08:00
  owner: popgen_quantgen
```

Trait model selection must happen before GWAS command generation. Different phenotype types imply different model families, covariates, diagnostics, and interpretation boundaries.

Trait model mapping:
- continuous trait: linear or mixed linear model after distribution and covariate review
- binary trait: logistic or mixed binary model; case/control balance must be visible
- count trait: count-aware model or transformed first-pass only with caveat
- ordinal trait: ordinal-aware model or exploratory coding with caveat
- repeated records: model must account for animal, time, or environment structure
- EBV or deregressed proof: prediction/evaluation context must be recorded before association claims

Current bridge:
- PLINK2 `--glm` can support bounded first-pass screening for suitable traits.
- Mixed-model GWAS, repeated-record models, and family/linkage QTL are planning-only until wrappers exist.

Risk boundary: choosing the wrong trait model can create significant results that are only artifacts of coding or repeated records.

## Covariate and PC policy

```yaml
knowledge_item.v2:
  doc_id: domain_association_mapping_covariate_pc_policy
  version: v2
  species: multi_species
  blueprint_scope: association_mapping
  evidence_level: expert_opinion
  source: sop
  updated_at: 2026-06-06T21:30:00+08:00
  owner: popgen_quantgen
```

GWAS covariates should be chosen from phenotype biology, batch design, population structure, and relatedness evidence. GeneAgent should propose covariates with reasons rather than automatically injecting all available columns.

Common covariate classes:
- biological: sex, age, parity, developmental stage, body weight when not downstream of the trait
- management: farm, batch, hatch, season, pen, flock, herd
- technical: chip, sequencing lane, caller, batch
- population structure: reviewed PC scores or ancestry-like covariates
- family/relatedness: GRM or mixed-model random effects when supported

PC rules:
- PCs used as GWAS covariates should come from the same retained genotype cohort or a documented projection.
- PC count should be justified by structure diagnostics and phenotype association.
- PCs should not replace GRM correction in close-relative or family-based cohorts.
- PCs should not absorb the biological contrast under test without review.

Risk boundary: covariates are not neutral. Missing covariates can inflate false positives, while leakage or overcorrection can hide real signals.

## Multiple testing policy

```yaml
knowledge_item.v2:
  doc_id: domain_association_mapping_multiple_testing_policy
  version: v2
  species: multi_species
  blueprint_scope: association_mapping
  evidence_level: expert_opinion
  source: sop
  updated_at: 2026-06-06T21:30:00+08:00
  owner: popgen_quantgen
```

Multiple testing context must accompany every GWAS or marker-level scan. Reports should never list significant markers without saying how significance or prioritization was defined.

Acceptable reporting modes:
- Bonferroni threshold with tested-marker count
- false discovery rate when appropriate
- permutation threshold when implemented
- suggestive threshold clearly labeled as exploratory
- top-N candidate list clearly labeled as ranking, not significance

Minimum fields:
- number of tested markers
- number of phenotypes or traits tested
- threshold method
- genomic inflation or QQ calibration artifact when available
- whether relatedness or stratification correction was used
- lead-marker clumping or region-merging rule when reported

Risk boundary: "top hits" and "significant loci" are different claims. GeneAgent must preserve the claim type.

## QTL overlap evidence policy

```yaml
knowledge_item.v2:
  doc_id: domain_association_mapping_qtl_overlap_evidence_policy
  version: v2
  species: multi_species
  blueprint_scope: association_mapping
  evidence_level: expert_opinion
  source: sop
  updated_at: 2026-06-06T21:30:00+08:00
  owner: popgen_quantgen
```

Overlap with QTL databases or prior literature is supporting evidence, not validation. QTL evidence must be handled with assembly, trait, population, and interval-width context.

Minimum overlap fields:
- candidate region and assembly
- QTL source, version, or citation
- QTL trait term and trait relationship to the study phenotype
- overlap type: marker-in-QTL, interval overlap, nearest QTL, or same gene
- interval width and number of genes
- species and population of the prior QTL

Interpretation rules:
- broad QTL intervals provide weak support unless narrowed by independent evidence
- trait ontology mismatch should be stated
- cross-species QTL overlap is comparative context only
- QTL overlap should be routed to functional annotation for gene/regulatory evidence
- absence of known QTL does not invalidate a new association

Risk boundary: database overlap can make a candidate sound established. GeneAgent should state whether overlap is strong, weak, indirect, missing, or conflicting evidence.
