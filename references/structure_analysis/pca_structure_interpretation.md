# PCA and Structure Interpretation

## PCA interpretation policy

```yaml
knowledge_item.v2:
  doc_id: structure_pca_interpretation_policy
  version: v2
  species: multi_species
  blueprint_scope: population_genetics
  evidence_level: expert_opinion
  source: sop
  updated_at: 2026-05-26T00:00:00Z
  owner: popgen_quantgen
```

PCA summarizes genetic covariance after the selected QC and pruning choices. It is useful for detecting batch effects, breed structure, outliers, and axes that may become fixed covariates, but it does not assign biological labels by itself.

Report guidance:
- State the input marker set, pruning rule, and retained sample count.
- Present PC scatterplots with known metadata only when metadata is supplied.
- Avoid naming clusters as breeds, lines, or ancestry groups without external labels.
- Record whether PCs are candidates for downstream model covariates.

Risk boundary: over-interpreting PCs can hide technical artifacts or turn exploratory structure into unsupported biological labels.

## Cluster naming caution

```yaml
knowledge_item.v2:
  doc_id: structure_cluster_labeling_caution
  version: v2
  species: multi_species
  blueprint_scope: population_genetics
  evidence_level: expert_opinion
  source: sop
  updated_at: 2026-05-26T00:00:00Z
  owner: popgen_quantgen
```

Cluster labels must come from verified metadata or an explicit analyst decision. GeneAgent may describe visible separation, overlap, and outliers, but should not infer breed, farm, batch, disease group, or ancestry labels from position alone.

Required language:
- Use neutral labels such as `PC1 high group`, `PC2 low group`, or `metadata group A`.
- Separate observed pattern from interpretation.
- Flag unknown metadata or inconsistent labels as report risks.

Risk boundary: automatic cluster naming can create misleading downstream decisions and should be blocked from final reports unless labels are verified.

## Stratification risk policy

```yaml
knowledge_item.v2:
  doc_id: structure_stratification_risk_policy
  version: v2
  species: multi_species
  blueprint_scope: population_genetics
  evidence_level: expert_opinion
  source: sop
  updated_at: 2026-05-26T00:00:00Z
  owner: popgen_quantgen
```

Population stratification can inflate association signals, distort prediction validation, and confound trait interpretation. PCA results should therefore be linked to downstream model decisions only through visible covariate handling and subgroup validation.

Checklist:
- Compare PCs with batch, farm, breed, sex, chip, and sequencing lane metadata when available.
- Mark unbalanced trait distributions across PC clusters as a risk.
- Recommend subgroup or stratified validation for genomic prediction when structure is strong.
- Preserve the number of PCs considered and the rationale for including or excluding them.

Risk boundary: using PCs as fixed effects can reduce confounding but may also remove real genetic signal; the report should make this tradeoff explicit.

## Admixture caution policy

```yaml
knowledge_item.v2:
  doc_id: structure_admixture_caution_policy
  version: v2
  species: multi_species
  blueprint_scope: population_genetics
  evidence_level: expert_opinion
  source: sop
  updated_at: 2026-05-26T00:00:00Z
  owner: popgen_quantgen
```

Admixture-style interpretation requires stronger assumptions than PCA plotting. When admixture or ancestry proportions are requested, GeneAgent should separate exploratory evidence from model-based inference and record the selected marker pruning, K range, seed strategy, and replicate stability criteria.

Operational guidance:
- Do not treat one K value as definitive without stability or external rationale.
- Use neutral terminology until labels are verified.
- Record whether LD pruning and relatedness pruning were applied.
- Avoid ancestry claims in production reports unless the pipeline actually ran an appropriate model.

Risk boundary: inferred ancestry proportions can be sensitive to sampling and reference groups.

## Relatedness and kinship interpretation

```yaml
knowledge_item.v2:
  doc_id: structure_relatedness_kinship_interpretation
  version: v2
  species: multi_species
  blueprint_scope: population_genetics
  evidence_level: expert_opinion
  source: sop
  updated_at: 2026-05-26T00:00:00Z
  owner: popgen_quantgen
```

Relatedness and kinship summaries connect structure analysis with GRM construction and model validation. High relatedness can be expected in breeding populations, but it changes cross-validation design and can inflate apparent prediction accuracy if relatives are split across train and test sets.

Report guidance:
- Summarize relationship coefficient ranges and extreme pairs.
- Distinguish duplicate or near-duplicate genotypes from expected family relationships.
- Recommend family-aware validation when close relatives are common.
- Keep pedigree and genomic relationship evidence separate when they disagree.

Risk boundary: random cross-validation in highly related cohorts can overstate deployment performance.
