# Relationship Matrix And Variance Components Domain

This file defines the quantitative-genetics domain for GRM, kinship, pedigree comparison, REML, heritability, and variance components.

## Domain scope and scientific intent

```yaml
knowledge_item.v2:
  doc_id: domain_relationship_matrix_variance_components_scope
  version: v2
  species: multi_species
  blueprint_scope: quantitative_genetics
  evidence_level: sop
  source: sop
  updated_at: 2026-06-06T00:00:00+08:00
  owner: popgen_quantgen
```

Primary `domain_scope`: `relationship_matrix_variance_components`.

This domain asks how animals are related at genomic and pedigree levels, and how that relationship structure supports variance decomposition, heritability, GWAS correction, and prediction. It is the foundation for many animal breeding analyses but is not itself a breeding-value decision workflow.

Current execution bridge:
- `grm_builder` compatibility key.
- `scripts/quantitative_genetics/run_relationship_matrix.sh`.
- PLINK2 relationship matrix and optional GCTA binary GRM generation.

Scientific outputs:
- GRM or kinship matrix
- sample ID/order file
- marker standardization notes
- matrix QC summary
- optional GCTA binary GRM artifacts

Not in scope:
- ssGBLUP H-matrix construction as a complete evaluation backend
- full heritability modeling without phenotype/model design
- breeding value prediction
- deployment of selection decisions

Risk boundary: a GRM is only useful when sample order, marker coding, scaling, filtering, and downstream model assumptions are traceable.

## GRM construction policy

```yaml
knowledge_item.v2:
  doc_id: domain_relationship_matrix_grm_construction_policy
  version: v2
  species: multi_species
  blueprint_scope: quantitative_genetics
  evidence_level: sop
  source: sop
  updated_at: 2026-06-06T00:00:00+08:00
  owner: popgen_quantgen
```

GRM construction should be treated as a model input contract, not a generic matrix export.

Minimum planning fields:
- genotype source and retained marker count
- allele coding and missingness policy
- MAF and chromosome filters used before matrix construction
- sample inclusion list and order
- backend and matrix formula family when known
- output format: text matrix, binary GCTA GRM, or both

Recommended checks:
- Confirm the matrix is square.
- Confirm row count equals ID count.
- Preserve `.fam` or explicit ID order.
- Record whether close duplicates or highly related animals were retained.
- Keep PLINK2 and GCTA outputs separate when both are produced.

Risk boundary: different GRM formulations and scaling choices can change downstream REML, GBLUP, and GWAS correction results.

## Variance component and heritability policy

```yaml
knowledge_item.v2:
  doc_id: domain_relationship_matrix_variance_component_policy
  version: v2
  species: multi_species
  blueprint_scope: quantitative_genetics
  evidence_level: expert_opinion
  source: sop
  updated_at: 2026-06-06T00:00:00+08:00
  owner: popgen_quantgen
```

Variance component analysis estimates genetic and residual contributions under an explicit mixed model. It is not guaranteed by the presence of a GRM file.

Required context:
- phenotype definition and transformation
- fixed effects and covariates
- random effects and relationship matrix source
- cohort, breed, line, farm, or family structure
- convergence status and model diagnostics
- standard errors or uncertainty where available

Use cases:
- heritability estimates
- genetic correlation or partitioning when implemented
- support for deciding whether GBLUP-like prediction is appropriate
- risk review for GWAS and prediction models

Do not overclaim:
- SNP-based heritability is not necessarily total narrow-sense heritability.
- REML estimates are model- and cohort-specific.
- Low heritability does not prove a trait is not genetically influenced.
- High heritability does not guarantee useful prediction accuracy.

Risk boundary: heritability is a population and model parameter, not an individual animal property.

## Sample order and ID policy

```yaml
knowledge_item.v2:
  doc_id: domain_relationship_matrix_sample_order_policy
  version: v2
  species: multi_species
  blueprint_scope: quantitative_genetics
  evidence_level: sop
  source: sop
  updated_at: 2026-06-06T00:00:00+08:00
  owner: popgen_quantgen
```

Sample ordering is a hard contract for matrix consumers. A matrix that is numerically valid but paired with the wrong ID order can silently corrupt GWAS correction, REML, or prediction.

Required artifacts:
- matrix file
- ID file in the exact matrix row/column order
- source PLINK prefix or genotype manifest
- any keep/remove list used before matrix generation
- report-visible matrix shape

Blocking conditions:
- matrix row count differs from ID count
- missing ID file
- duplicated IDs
- genotype, phenotype, covariate, and GRM IDs do not overlap sufficiently for requested downstream modeling
- hidden reordering between GRM and model inputs

Risk boundary: the safest response to uncertain matrix order is to block downstream modeling and produce a diagnostic, not to guess.

## Execution bridge and artifacts

```yaml
knowledge_item.v2:
  doc_id: domain_relationship_matrix_execution_bridge
  version: v2
  species: multi_species
  blueprint_scope: quantitative_genetics
  evidence_level: sop
  source: sop
  updated_at: 2026-06-06T00:00:00+08:00
  owner: popgen_quantgen
```

The current execution bridge is `scripts/quantitative_genetics/run_relationship_matrix.sh`.

Artifact mapping:

| Domain concern | Current artifact |
|---|---|
| marker standardization | `results/grm/marker_standardization.md` |
| relationship matrix | `results/grm/grm_matrix.tsv` |
| sample order | `results/grm/grm_ids.tsv` |
| optional GCTA GRM | `results/grm/grm_gcta.grm.bin`, `.grm.N.bin`, `.grm.id` |
| matrix QC summary | `reports/grm_qc.md` |
| run traceability | `results/grm/run_manifest.json`, `results/grm/audit_sidecar.json` |

Submit blockers:
- no genotype matrix
- neither PLINK2 nor GCTA is available
- non-POSIX paths
- resource request above configured caps
- output overwrite without approval

Risk boundary: this bridge creates relationship artifacts. It does not certify that those artifacts are appropriate for every REML, ssGBLUP, GWAS, or prediction model.

## GRM QC prerequisite policy

```yaml
knowledge_item.v2:
  doc_id: domain_relationship_matrix_grm_qc_prerequisites
  version: v2
  species: multi_species
  blueprint_scope: quantitative_genetics
  evidence_level: sop
  source: sop
  updated_at: 2026-06-06T21:30:00+08:00
  owner: popgen_quantgen
```

GRM construction should start only after genotype QC is clear enough for relationship inference. A GRM built from poorly controlled markers can be numerically valid and scientifically misleading.

Prerequisite checks:
- sample IDs are unique and reconciled with phenotype/covariate/pedigree IDs when needed
- marker missingness, sample missingness, MAF, and chromosome filters are recorded
- duplicate markers and allele-coding conflicts are resolved or excluded
- close duplicates and sample swaps are reviewed
- retained marker count is sufficient for the intended relationship estimate
- population structure and breed composition are visible for interpretation

Blocking conditions:
- duplicated sample IDs
- missing sample-order artifact
- incompatible genotype format
- hidden marker-set mismatch between GRM and downstream model
- output overwrite without approval

Risk boundary: GRM quality depends on both technical QC and biological sampling. It is not just a file conversion step.

## A matrix and H matrix boundary

```yaml
knowledge_item.v2:
  doc_id: domain_relationship_matrix_a_matrix_h_matrix_boundary
  version: v2
  species: multi_species
  blueprint_scope: quantitative_genetics
  evidence_level: expert_opinion
  source: sop
  updated_at: 2026-06-06T21:30:00+08:00
  owner: popgen_quantgen
```

The pedigree numerator relationship matrix (`A`), genomic relationship matrix (`G`), and single-step relationship matrix (`H`) are related but distinct model objects.

Boundary rules:
- `A` requires a reviewed pedigree and founder/missing-parent policy.
- `G` requires genotype markers, allele-frequency/scaling policy, and sample order.
- `H` requires both pedigree and genomic inputs plus compatibility rules for genotyped and non-genotyped animals.
- ssGBLUP is not complete just because both pedigree and genotype files exist.
- Pedigree-genomic conflict should trigger diagnostic review before single-step planning.

Current GeneAgent status:
- GRM and relatedness artifacts are partially executable through quantitative-genetics scripts.
- A/H matrix construction is knowledge/planning scope unless a dedicated backend and tests are added.
- Reports should distinguish GBLUP-like genomic-only prediction from ssGBLUP.

Risk boundary: mixing `A`, `G`, and `H` terminology can mislead users about which animals and relationships were modeled.

## REML convergence policy

```yaml
knowledge_item.v2:
  doc_id: domain_relationship_matrix_reml_convergence_policy
  version: v2
  species: multi_species
  blueprint_scope: quantitative_genetics
  evidence_level: sop
  source: sop
  updated_at: 2026-06-06T21:30:00+08:00
  owner: popgen_quantgen
```

REML outputs should be treated as model results with convergence and diagnostic status, not as a guaranteed heritability value.

Required REML report fields:
- model formula and random effects
- phenotype and transformation
- fixed effects and covariates
- GRM or relationship matrix source
- sample count after model merge
- convergence status and software return code
- variance component estimates and standard errors when available
- boundary estimates or singularity warnings

Review triggers:
- convergence failure
- variance component near zero or boundary
- negative or impossible estimates from unsupported workflows
- high standard error relative to estimate
- sample count too small for the requested model
- phenotype/covariate missingness removes a large cohort fraction

Risk boundary: heritability and variance components are model-dependent estimates. GeneAgent should surface uncertainty and convergence before interpretation.

## Sparse relatedness policy

```yaml
knowledge_item.v2:
  doc_id: domain_relationship_matrix_sparse_relatedness_policy
  version: v2
  species: multi_species
  blueprint_scope: quantitative_genetics
  evidence_level: expert_opinion
  source: sop
  updated_at: 2026-06-06T21:30:00+08:00
  owner: popgen_quantgen
```

Large cohorts may require sparse relatedness summaries, pairwise thresholds, or block processing. Sparse representations should not hide sample-order or threshold choices.

Planning fields:
- threshold used to retain pairwise relationships
- whether diagonal and close relatives are retained
- matrix or edge-list output format
- sample-order or node-ID file
- intended downstream use: duplicate detection, validation split, mixed model, or report summary
- chunking or block strategy when pairwise calculations are large

Interpretation rules:
- sparse relatedness is usually a thresholded view, not the full GRM
- close relatives retained for breeding models may be excluded for validation-split design
- pairwise relatedness thresholds should be stated as review parameters
- edge lists must preserve both sample IDs and relationship estimate type

Risk boundary: sparse relatedness can save resources, but thresholding can remove information needed for model fitting or interpretation.
