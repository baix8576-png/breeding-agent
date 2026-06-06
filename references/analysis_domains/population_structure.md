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
