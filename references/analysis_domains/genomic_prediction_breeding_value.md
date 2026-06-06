# Genomic Prediction And Breeding Value Domain

This file defines the quantitative-genetics domain for genomic prediction, GBLUP/ssGBLUP boundaries, GEBV outputs, validation, and breeding-decision safeguards.

## Domain scope and scientific intent

```yaml
knowledge_item.v2:
  doc_id: domain_genomic_prediction_breeding_value_scope
  version: v2
  species: multi_species
  blueprint_scope: quantitative_genetics
  evidence_level: sop
  source: sop
  updated_at: 2026-06-06T00:00:00+08:00
  owner: popgen_quantgen
```

Primary `domain_scope`: `genomic_prediction_breeding_value`.

Genomic prediction estimates genetic merit or genomic estimated breeding values under a declared training, validation, and reporting design. It uses genotype-derived relationships, phenotypes, covariates, and sometimes pedigree information, but the core question is predictive utility rather than locus discovery.

Current execution bridge:
- `genomic_prediction` compatibility key.
- `scripts/quantitative_genetics/run_breeding_value_prediction.sh`.
- GCTA GRM + REML + random-effect prediction as a bounded first-pass path when `gcta64` is available.

Not in scope:
- GWAS or QTL discovery
- final breeding decisions without validation review
- Bayesian alphabet or ML model comparison unless implemented and tested
- full ssGBLUP production evaluation with non-genotyped animals

Risk boundary: prediction output is decision support only after validation, bias, calibration, subgroup performance, and deployment constraints are reviewed.

## Model family policy

```yaml
knowledge_item.v2:
  doc_id: domain_genomic_prediction_model_family_policy
  version: v2
  species: multi_species
  blueprint_scope: quantitative_genetics
  evidence_level: sop
  source: sop
  updated_at: 2026-06-06T00:00:00+08:00
  owner: popgen_quantgen
```

Model choice should follow phenotype type, data structure, sample size, trait architecture, and validation design.

Default route:
- Use GBLUP-compatible models for interpretable first-pass genomic prediction when genotype-derived relationships and continuous or approximately continuous phenotypes are available.
- Use fixed-effect covariates for known batch, sex, age, farm, line, or management effects when supplied and reviewed.
- Use pedigree-aware or ssGBLUP routes only when pedigree quality and software support are explicit.

Alternative routes:
- Bayesian or variable-selection models when large-effect loci or sparse architecture is plausible and validation is strong.
- ML models when sample size, feature engineering, and external validation justify complexity.
- Multi-trait or longitudinal models only after trait and record structure are formalized.

Current bridge limitation:
- The wrapper documents a GBLUP-compatible GCTA path.
- It does not run Bayesian alphabet models, ML models, or production ssGBLUP.
- It no longer executes GWAS inside prediction.

Risk boundary: more complex models are not automatically better. They need fair validation against the GBLUP baseline.

## Validation and metric policy

```yaml
knowledge_item.v2:
  doc_id: domain_genomic_prediction_validation_policy
  version: v2
  species: multi_species
  blueprint_scope: quantitative_genetics
  evidence_level: sop
  source: sop
  updated_at: 2026-06-06T00:00:00+08:00
  owner: popgen_quantgen
```

Prediction validation is part of the method, not a post-processing extra.

Minimum validation design fields:
- training, validation, and test split definition
- whether split is random, family-blocked, breed-blocked, farm-blocked, time-forward, or external
- phenotype target: raw, adjusted, deregressed proof, EBV, or observed outcome
- metric definitions and denominators
- subgroup performance for breed, line, sex, farm, batch, or generation when relevant

Recommended metrics:
- predictive correlation for ranking
- RMSE or MAE for scale
- bias or regression slope for calibration
- subgroup metrics for transferability
- uncertainty or reliability when available

Blocking conditions for decision support:
- no held-out validation
- validation split leaks close relatives or replicated records when the goal is deployment
- only one metric reported
- no subgroup review in multi-breed or multi-line data
- strong bias or calibration failure without caveat

Risk boundary: high correlation in a leaked or overly easy split can mislead breeding decisions.

## Breeding decision boundary

```yaml
knowledge_item.v2:
  doc_id: domain_genomic_prediction_breeding_decision_boundary
  version: v2
  species: multi_species
  blueprint_scope: quantitative_genetics
  evidence_level: expert_opinion
  source: sop
  updated_at: 2026-06-06T00:00:00+08:00
  owner: popgen_quantgen
```

GeneAgent can help generate prediction artifacts and validation reports, but final breeding decisions require a separate reviewed decision workflow.

Decision-support requirements:
- trait objective and economic or biological direction
- index weights if multiple traits are used
- validation evidence for target population
- bias and calibration review
- subgroup or line-specific performance
- uncertainty, reliability, or confidence labels
- audit trail from input data to predictions

Do not automate:
- animal selection or culling decisions
- deployment of marker panels
- publication claims about prediction superiority
- cross-breed transfer recommendations without external validation
- replacement of breeder or domain-expert review

Risk boundary: GEBV and predicted scores are operationally powerful. They must remain traceable, validated, and reviewed before action.

## Execution bridge and artifacts

```yaml
knowledge_item.v2:
  doc_id: domain_genomic_prediction_execution_bridge
  version: v2
  species: multi_species
  blueprint_scope: quantitative_genetics
  evidence_level: sop
  source: sop
  updated_at: 2026-06-06T00:00:00+08:00
  owner: popgen_quantgen
```

The current execution bridge is `scripts/quantitative_genetics/run_breeding_value_prediction.sh`.

Artifact mapping:

| Domain concern | Current artifact |
|---|---|
| cohort alignment | `results/prediction/cohort_alignment.json` |
| model family statement | `results/prediction/model_family.md` |
| model spec | `results/prediction/model_spec.json` |
| predictions | `results/prediction/predictions.tsv` |
| validation plan | `results/prediction/validation_plan.md` |
| metrics | `results/prediction/metrics.tsv` |
| heritability output | `results/prediction/heritability/heritability.hsq` when GCTA completes |
| summary report | `reports/genomic_prediction_summary.md` |
| run traceability | `results/prediction/run_manifest.json`, `results/prediction/audit_sidecar.json` |

Submit blockers:
- no genotype matrix
- missing phenotype table
- missing `gcta64` for current executable prediction path
- non-POSIX paths
- resource request above configured caps
- output overwrite without approval

Risk boundary: this bridge produces first-pass prediction artifacts. It does not by itself establish validated breeding decisions.

## Training and validation split policy

```yaml
knowledge_item.v2:
  doc_id: domain_genomic_prediction_training_validation_split_policy
  version: v2
  species: multi_species
  blueprint_scope: quantitative_genetics
  evidence_level: sop
  source: sop
  updated_at: 2026-06-06T21:30:00+08:00
  owner: popgen_quantgen
```

Training and validation split design is part of the genomic prediction method. GeneAgent should not report model performance without stating how animals and records were split.

Split types:
- random individual split for first-pass internal checks
- family-blocked split to reduce close-relative leakage
- breed- or line-blocked split for transferability
- farm, herd, flock, or batch-blocked split for environment robustness
- time-forward or generation-forward split for deployment realism
- external validation set when a target population is available

Minimum split record:
- split variable and random seed if used
- number of animals and records per split
- relatedness or family leakage summary when available
- trait distribution per split
- breed/line/farm/batch balance
- whether repeated records from one animal are kept in one split

Risk boundary: prediction accuracy from a leaked split can look excellent and fail in deployment. Split design must be visible before any performance claim.

## Multi-breed validation policy

```yaml
knowledge_item.v2:
  doc_id: domain_genomic_prediction_multi_breed_validation_policy
  version: v2
  species: multi_species
  blueprint_scope: quantitative_genetics
  evidence_level: expert_opinion
  source: sop
  updated_at: 2026-06-06T21:30:00+08:00
  owner: popgen_quantgen
```

Multi-breed and cross-line prediction need explicit subgroup validation. A model that performs well in the combined cohort may fail in a smaller breed, line, or family group.

Required subgroup checks:
- sample count by breed, line, farm, batch, and generation when available
- prediction metric by subgroup
- bias or regression slope by subgroup
- calibration plot or summary by subgroup when supported
- marker and imputation quality differences by subgroup
- whether training contains close relatives of validation animals

Interpretation rules:
- report pooled and subgroup metrics separately
- do not claim cross-breed deployment from random split alone
- treat severe subgroup bias as a deployment blocker
- state when subgroup sample size is too small for reliable metrics
- document whether breed labels are user-supplied, metadata-derived, or inferred

Risk boundary: pooled performance can hide inequity and transfer failure. Breeding decisions need target-population evidence.

## Model comparison policy

```yaml
knowledge_item.v2:
  doc_id: domain_genomic_prediction_model_comparison_policy
  version: v2
  species: multi_species
  blueprint_scope: quantitative_genetics
  evidence_level: sop
  source: sop
  updated_at: 2026-06-06T21:30:00+08:00
  owner: popgen_quantgen
```

Model comparison should be fair, reproducible, and tied to validation design. More complex models should be compared with the GBLUP baseline under the same split and metric definitions.

Comparison requirements:
- same training/validation/test split across models
- same phenotype target and covariate policy
- same marker set or documented feature differences
- same metric definitions and denominators
- hyperparameter tuning kept inside training data
- uncertainty or repeated-split summary when available

Model families:
- GBLUP or ridge-like baseline
- ssGBLUP only when pedigree and non-genotyped-animal scope are supported
- Bayesian variable-selection models when trait architecture justifies them
- machine-learning models only with adequate sample size, leakage control, and external validation

Report rules:
- show model complexity and compute cost
- separate accuracy, bias, calibration, and subgroup transferability
- avoid "best model" language when differences are within uncertainty
- keep failed or non-converged model attempts visible in audit logs

Risk boundary: model comparison is vulnerable to leakage and tuning bias. A higher metric is not meaningful unless the comparison is controlled.

## Deployment decision gate

```yaml
knowledge_item.v2:
  doc_id: domain_genomic_prediction_deployment_decision_gate
  version: v2
  species: multi_species
  blueprint_scope: quantitative_genetics
  evidence_level: sop
  source: sop
  updated_at: 2026-06-06T21:30:00+08:00
  owner: popgen_quantgen
```

Prediction artifacts are not automatically deployment-ready. GeneAgent should require a deployment decision gate before any breeding action, marker deployment, or operational selection recommendation.

Gate checklist:
- target population is defined
- validation split matches intended deployment scenario
- accuracy, bias, calibration, and subgroup metrics are reviewed
- phenotype target and economic direction are approved
- input data provenance and model version are auditable
- uncertainty or reliability labels are available or limitations are stated
- fairness or subgroup risk is reviewed for breeds, lines, farms, or generations
- human reviewer approves use beyond exploratory reporting

Automatic blockers:
- no held-out validation
- strong calibration failure
- severe subgroup failure in target population
- missing audit trail from inputs to predictions
- model trained on data outside the approved scope
- output requested as a culling or final selection decision without review

Risk boundary: GeneAgent can support genomic prediction, but final breeding decisions are domain-governed actions and must stay review-gated.
