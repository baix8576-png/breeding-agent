# Genomic Modeling Routes

## GBLUP route guide

```yaml
knowledge_item.v2:
  doc_id: modeling_gblup_route_guide
  version: v2
  species: multi_species
  blueprint_scope: genomic_prediction
  evidence_level: expert_opinion
  source: sop
  updated_at: 2026-05-26T00:00:00Z
  owner: popgen_quantgen
```

GBLUP is the default interpretable route when the analysis has genotype-derived relationships, a continuous or approximately continuous phenotype, and a defined validation design. GeneAgent should verify sample alignment, GRM availability, phenotype transformation decisions, and fixed-effect covariates before proposing GBLUP execution.

Use GBLUP when:
- The main signal is expected to be distributed across many markers.
- The cohort size and marker density support a stable genomic relationship matrix.
- The user needs transparent breeding-value style output and auditability.

Risk boundary: GBLUP can underfit large-effect architecture or non-additive signals; record this limitation in reports.

## ssGBLUP boundary guide

```yaml
knowledge_item.v2:
  doc_id: modeling_ssgblup_boundary_guide
  version: v2
  species: multi_species
  blueprint_scope: genomic_prediction
  evidence_level: expert_opinion
  source: sop
  updated_at: 2026-05-26T00:00:00Z
  owner: popgen_quantgen
```

Single-step GBLUP combines pedigree, phenotype, and genomic relationship information. It is appropriate when genotyped and non-genotyped animals both contribute evidence, and when pedigree quality is sufficient for the relationship matrix used by the selected backend.

Preconditions:
- Pedigree IDs must align with genotype and phenotype IDs.
- Unknown parents and duplicate pedigree records must be reported.
- Genotyped/non-genotyped group sizes must be visible.
- Matrix construction and scaling assumptions must be documented.

Risk boundary: ssGBLUP is not simply GBLUP plus a pedigree file; inconsistent pedigree and genomic relationships can create unstable or biased estimates.

## Bayesian and ML route guide

```yaml
knowledge_item.v2:
  doc_id: modeling_bayesian_ml_route_guide
  version: v2
  species: multi_species
  blueprint_scope: genomic_prediction
  evidence_level: expert_opinion
  source: sop
  updated_at: 2026-05-26T00:00:00Z
  owner: popgen_quantgen
```

Bayesian variable-selection models and machine-learning models may be useful when the trait architecture, data volume, or operational goal justifies added complexity. They should not replace GBLUP by default unless the validation design is strong enough to compare models fairly.

Decision factors:
- Large-effect loci or sparse architecture may justify Bayesian alternatives.
- Nonlinear predictors may justify ML only with enough samples and leakage control.
- Hyperparameter search must be nested or separated from final evaluation.
- Interpretability and deployment constraints must be recorded.

Risk boundary: flexible models can overfit, especially with relatives split between training and validation sets.

## Fixed and random effect checklist

```yaml
knowledge_item.v2:
  doc_id: modeling_fixed_random_effect_checklist
  version: v2
  species: multi_species
  blueprint_scope: genomic_prediction
  evidence_level: sop
  source: sop
  updated_at: 2026-05-26T00:00:00Z
  owner: popgen_quantgen
```

Fixed and random effects must be declared before model execution. Common fixed effects include sex, age, batch, farm, parity, contemporary group, breed proportion, and selected PCs. Random effects may include additive genetic effect, permanent environment, litter, family, or farm-year depending on the trait and design.

Checklist:
- Confirm every covariate has a merge key and missing-value policy.
- Flag confounding between fixed effects and validation folds.
- Avoid including post-outcome variables as predictors.
- Record formula-like model intent in the report.

Risk boundary: unreviewed covariates can leak outcome information or remove real biological signal.

## Phenotype type modeling guide

```yaml
knowledge_item.v2:
  doc_id: modeling_phenotype_type_guide
  version: v2
  species: multi_species
  blueprint_scope: genomic_prediction
  evidence_level: expert_opinion
  source: sop
  updated_at: 2026-05-26T00:00:00Z
  owner: popgen_quantgen
```

Phenotype type determines modeling assumptions. Continuous traits, binary disease traits, count traits, survival traits, repeated measures, and categorical traits require different loss functions, transformations, or mixed-model structures.

Planning guidance:
- Record phenotype type and unit before choosing a model.
- Do not transform traits without preserving original units and rationale.
- For binary traits, report prevalence and case-control imbalance.
- For repeated records, decide whether records are aggregated or modeled with repeated-effect structure.

Risk boundary: treating binary or count phenotypes as continuous can produce misleading calibration and uncertainty.

## Prediction deployment boundary

```yaml
knowledge_item.v2:
  doc_id: modeling_prediction_deployment_boundary
  version: v2
  species: multi_species
  blueprint_scope: genomic_prediction
  evidence_level: expert_opinion
  source: sop
  updated_at: 2026-05-26T00:00:00Z
  owner: popgen_quantgen
```

Prediction output should be separated into research diagnostics, internal decision support, and production deployment. GeneAgent reports may summarize predictive performance and risk, but breeding decisions require user-approved validation, monitoring, and governance.

Deployment checks:
- Validate on a cohort that reflects the intended use population.
- Report subgroup performance and calibration.
- Keep model version, training data window, and feature set immutable after release.
- Record rollback or retirement conditions for deployed scores.

Risk boundary: a cross-validation score is not the same as production readiness.
