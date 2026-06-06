# Population Structure Domain

This file defines the population-structure knowledge domain behind the `pca_pipeline` compatibility bridge and `scripts/population_genetics/run_population_structure_diversity.sh`.

## Domain scope and scientific intent

```yaml
knowledge_item.v2:
  doc_id: domain_population_structure_scope
  version: v2
  species: multi_species
  blueprint_scope: population_genetics
  evidence_level: sop
  source: sop
  updated_at: 2026-06-06T00:00:00+08:00
  owner: popgen_quantgen
```

Primary `domain_scope`: `population_structure`.

Population structure analysis asks whether genotype covariance reflects breed composition, ancestry gradients, batch effects, family structure, sampling design, or outlier groups. It is descriptive and diagnostic before it becomes a downstream modeling covariate.

Current execution bridge:
- `pca_pipeline` compatibility key.
- `scripts/population_genetics/run_population_structure_diversity.sh`.
- `plink2` LD pruning and PCA as the current executable core.

Scientific outputs:
- eigenvectors and eigenvalues
- LD-pruned marker set provenance
- outlier and cluster review notes
- stratification-risk summary for GWAS and prediction planning

Not in scope:
- automatic breed naming from PCA clusters
- definitive ancestry inference
- model-based admixture unless a dedicated wrapper and review policy exist
- causal interpretation of PCA axes

Risk boundary: PCA is a projection of the selected markers and samples. It is not a population labeler.

## PCA pruning and component policy

```yaml
knowledge_item.v2:
  doc_id: domain_population_structure_pca_pruning_policy
  version: v2
  species: multi_species
  blueprint_scope: population_genetics
  evidence_level: sop
  source: sop
  updated_at: 2026-06-06T00:00:00+08:00
  owner: popgen_quantgen
```

PCA should be run on a dataset whose QC and LD-pruning choices are visible. High-LD regions, duplicated animals, close relatives, uneven breed sampling, and platform batch effects can dominate leading PCs.

Planning checks:
- Record the pre-pruning marker count and post-pruning marker count.
- Preserve LD pruning parameters such as window, step, and r2 threshold.
- Use the same retained sample set when comparing PCA with downstream GRM, GWAS, or prediction reports.
- Plot and summarize multiple PC pairs, not only PC1 and PC2.
- Do not automatically add PCs to later models; propose candidate PCs for review.

Recommended report fields:
- eigenvalue table
- variance proxy or component magnitude summary
- metadata overlays: breed, farm, batch, sex, chip, sequencing lane when available
- outlier list with review status

Risk boundary: a PC can reflect real ancestry, recent relatedness, genotyping platform, batch, or sample imbalance. The report should not collapse those possibilities into one story.

## Stratification and cluster boundary

```yaml
knowledge_item.v2:
  doc_id: domain_population_structure_stratification_boundary
  version: v2
  species: multi_species
  blueprint_scope: population_genetics
  evidence_level: expert_opinion
  source: sop
  updated_at: 2026-06-06T00:00:00+08:00
  owner: popgen_quantgen
```

Stratification risk is a downstream modeling risk, not a PCA plot decoration. It matters because unmodeled structure can inflate association signals, make validation splits optimistic, and hide subgroup-specific failures.

Use PCA findings as:
- a diagnostic for sample mix-ups and outliers
- a candidate covariate source for GWAS or mixed models
- a subgroup validation guide for genomic prediction
- a report explanation for breed or population composition

Do not use PCA findings as:
- an automatic sample exclusion rule
- a proof of breed identity
- a replacement for pedigree or metadata checks
- a claim that groups are biologically discrete

Review checklist:
- Are clusters aligned with known metadata?
- Are outliers driven by missingness or platform effects?
- Are close relatives or family groups inflating structure?
- Do proposed PCs change the downstream model interpretation?

Risk boundary: cluster labels must be user-provided or metadata-supported. GeneAgent should write "cluster A/B" or "PC outlier group" until reviewed names are supplied.

## Admixture and ancestry boundary

```yaml
knowledge_item.v2:
  doc_id: domain_population_structure_admixture_boundary
  version: v2
  species: multi_species
  blueprint_scope: population_genetics
  evidence_level: expert_opinion
  source: sop
  updated_at: 2026-06-06T00:00:00+08:00
  owner: popgen_quantgen
```

Admixture and ancestry estimation require stronger assumptions than PCA. PCA can motivate an admixture-style analysis, but it does not itself estimate ancestry proportions.

If admixture is requested, the plan should require:
- explicit marker pruning policy
- relatedness filtering or an explanation for retaining relatives
- K range and replicate strategy
- seed and convergence policy
- metadata-aware interpretation review
- distinction between exploratory clusters and ancestry claims

Until a dedicated execution blueprint is implemented, admixture is knowledge/planning scope. The current `population_genetics` wrapper can provide PCA and structure diagnostics, but it should not output ancestry proportions.

Risk boundary: K selection and ancestry labels are common overclaim points. Reports should state whether a result is exploratory, model-based, or validated by independent metadata.

## Execution bridge and artifacts

```yaml
knowledge_item.v2:
  doc_id: domain_population_structure_execution_bridge
  version: v2
  species: multi_species
  blueprint_scope: population_genetics
  evidence_level: sop
  source: sop
  updated_at: 2026-06-06T00:00:00+08:00
  owner: popgen_quantgen
```

The current execution bridge is a bounded population-structure subset inside `run_population_structure_diversity.sh`.

Artifact mapping:

| Domain concern | Current artifact |
|---|---|
| LD pruning provenance | `results/structure/pruning_manifest.json`, `results/structure/prune.prune.in` |
| PCA coordinates | `results/structure/pca/eigenvec.tsv` |
| PCA component magnitudes | `results/structure/pca/eigenval.tsv` |
| visualization handoff | `results/structure/figures/README.md` |
| stratification note | `reports/stratification_risk.md` |
| run traceability | `results/structure/run_manifest.json`, `results/structure/audit_sidecar.json` |

Submit blockers:
- missing genotype matrix
- missing `plink2`
- non-POSIX paths
- resource request above configured caps
- output overwrite without approval

Risk boundary: this bridge currently supports PCA-style population structure, not complete ancestry modeling.

## Pruning and relatedness detail policy

```yaml
knowledge_item.v2:
  doc_id: domain_population_structure_pruning_relatedness_detail
  version: v2
  species: multi_species
  blueprint_scope: population_genetics
  evidence_level: expert_opinion
  source: sop
  updated_at: 2026-06-06T21:30:00+08:00
  owner: popgen_quantgen
```

PCA should be planned with both LD pruning and relatedness in mind. In livestock, close relatives, full-sib families, inbred lines, and duplicated animals can dominate the leading PCs even after standard marker pruning.

Planning checks:
- define whether PCA is for sample QC, population description, GWAS covariates, or validation splitting
- report the LD-pruning window, step, and r2 threshold
- flag close relatives or duplicate-like pairs before interpreting PCA clusters
- decide whether to run PCA on all animals or on a less-related reference subset with projection
- keep a note when family structure is retained intentionally

Recommended artifacts:
- pruned marker list
- relatedness or duplicate-pair warning table when available
- retained sample list
- PCA cohort definition
- explanation of whether related animals were retained, removed, or marked for review

Risk boundary: LD pruning removes correlated markers, not correlated animals. Relatedness needs its own review when PCA is used for population interpretation.

## PCA component retention policy

```yaml
knowledge_item.v2:
  doc_id: domain_population_structure_pca_component_retention_policy
  version: v2
  species: multi_species
  blueprint_scope: population_genetics
  evidence_level: expert_opinion
  source: sop
  updated_at: 2026-06-06T21:30:00+08:00
  owner: popgen_quantgen
```

PC retention should be a review decision tied to downstream purpose. GeneAgent should not automatically treat PC1-PC10 as covariates or assume only PC1-PC2 matter.

Review dimensions:
- scree/eigenvalue pattern
- metadata overlay with breed, farm, batch, line, sex, chip, or lane
- known sample design and family structure
- whether PCs correlate with the phenotype
- whether PCs represent ancestry, batch, or management effects

Use cases:
- for GWAS, propose PCs only when they reduce stratification risk without absorbing the biological contrast of interest
- for genomic prediction, use PCs to define subgroup validation or transferability checks before using them as model covariates
- for QC, use extreme PC outliers as review candidates rather than automatic removals

Report language:
- "candidate PC covariates" until model review is complete
- "PC-associated metadata pattern" instead of unreviewed population labels
- "component retained for visualization" separate from "component retained for modeling"

Risk boundary: retaining too many PCs can remove real signal; retaining too few can leave confounding. The decision must be visible.

## Admixture K selection policy

```yaml
knowledge_item.v2:
  doc_id: domain_population_structure_admixture_k_selection_policy
  version: v2
  species: multi_species
  blueprint_scope: population_genetics
  evidence_level: expert_opinion
  source: sop
  updated_at: 2026-06-06T21:30:00+08:00
  owner: popgen_quantgen
```

If model-based admixture is planned outside the current executable wrapper, K selection must be explicit. The goal is to prevent a visually appealing bar plot from becoming an unsupported ancestry claim.

Minimum plan:
- define K range and rationale
- use pruned markers appropriate for admixture-style models
- account for relatedness and duplicated animals
- run multiple seeds or replicates when the tool supports it
- record convergence or likelihood summaries
- interpret K values against metadata, known breeds, and sampling design

Do not:
- choose K only because a plot looks clean
- name clusters by breed without metadata support
- compare ancestry proportions across datasets with different marker panels without caveats
- report individual ancestry proportions as validated breed composition unless validated externally

Current automation boundary:
- GeneAgent may write the plan and caveats.
- Execution remains blocked until a dedicated wrapper, artifact contract, and tests exist.

Risk boundary: K is a modeling parameter, not the number of real populations. Reports must keep exploratory status visible.

## Cluster name review policy

```yaml
knowledge_item.v2:
  doc_id: domain_population_structure_cluster_name_review_policy
  version: v2
  species: multi_species
  blueprint_scope: population_genetics
  evidence_level: sop
  source: sop
  updated_at: 2026-06-06T21:30:00+08:00
  owner: popgen_quantgen
```

Cluster naming is a high-risk interpretation step. GeneAgent should separate unsupervised structure from reviewed labels.

Allowed labels before review:
- `PC outlier group`
- `cluster A`, `cluster B`, or numbered groups
- `metadata-aligned group` when a known variable explains the pattern
- `batch-associated group` when technical metadata support that explanation

Required evidence for breed or population names:
- user-supplied breed/population metadata
- concordance between metadata and genotype structure
- sample-size summary for each named group
- note about crossbred, admixed, or uncertain samples
- reviewer approval when labels will affect filtering or downstream models

Blocking conditions:
- automatic exclusion based only on cluster name
- downstream model split based on unreviewed cluster labels
- selection-signature population contrast derived from unreviewed PCA clusters

Risk boundary: naming a cluster can turn a diagnostic plot into a biological claim. GeneAgent should preserve uncertainty until metadata support is present.
