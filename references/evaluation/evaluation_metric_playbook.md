# Evaluation Metric Playbook

## Cross validation patterns

```yaml
knowledge_item.v2:
  doc_id: evaluation_cross_validation_patterns
  version: v2
  species: multi_species
  blueprint_scope: quantitative_genetics
  evidence_level: expert_opinion
  source: sop
  updated_at: 2026-05-26T00:00:00Z
  owner: popgen_quantgen
```

Cross-validation design must match the intended use case. Random k-fold validation estimates within-cohort performance; family-aware, breed-aware, farm-aware, or time-forward splits estimate harder deployment settings.

Minimum reporting:
- fold construction rule
- fold counts and sample counts
- stratification variables
- train/test relatedness warning when available
- whether hyperparameter selection is separated from final testing

Risk boundary: leakage through relatives, repeated records, or shared management groups can inflate performance.

## Bias and calibration notes

```yaml
knowledge_item.v2:
  doc_id: evaluation_bias_calibration_notes
  version: v2
  species: multi_species
  blueprint_scope: quantitative_genetics
  evidence_level: expert_opinion
  source: sop
  updated_at: 2026-05-26T00:00:00Z
  owner: popgen_quantgen
```

Prediction accuracy alone is not enough. Bias and calibration indicate whether scores are systematically too high or too low and whether uncertainty or score scale is usable for decision support.

Suggested outputs:
- correlation or accuracy metric appropriate to trait type
- regression slope or bias estimate when expected values are available
- calibration by subgroup or score decile
- residual patterns by batch, breed, or cohort

Risk boundary: a model can rank animals well while producing biased absolute values.

## Subgroup validation policy

```yaml
knowledge_item.v2:
  doc_id: evaluation_subgroup_validation_policy
  version: v2
  species: multi_species
  blueprint_scope: quantitative_genetics
  evidence_level: expert_opinion
  source: sop
  updated_at: 2026-05-26T00:00:00Z
  owner: popgen_quantgen
```

Subgroup validation checks whether performance is stable across breed, line, sex, farm, batch, time period, genotype platform, or management group. It should be included whenever a subgroup label is available and sample size is sufficient.

Report guidance:
- Include subgroup sample counts before metrics.
- Suppress or label unstable metrics for very small subgroups.
- Compare subgroup calibration and bias, not only correlation.
- Flag subgroups absent from training data as deployment risks.

Risk boundary: strong average performance can hide poor performance in minority or newly introduced groups.

## Prediction metric dictionary

```yaml
knowledge_item.v2:
  doc_id: evaluation_prediction_metric_dictionary
  version: v2
  species: multi_species
  blueprint_scope: quantitative_genetics
  evidence_level: sop
  source: ontology
  updated_at: 2026-05-26T00:00:00Z
  owner: popgen_quantgen
```

Metric names must be explicit. Common entries include Pearson correlation, Spearman correlation, RMSE, MAE, regression slope, classification AUC, balanced accuracy, Brier score, and calibration intercept.

Dictionary rules:
- State numerator, denominator, and target variable.
- Distinguish observed phenotype, adjusted phenotype, deregressed proof, and estimated breeding value targets.
- Label metrics as ranking, scale, calibration, or classification metrics.
- Avoid mixing metrics across trait types without explanation.

Risk boundary: ambiguous metric names make reports hard to reproduce and compare.

## Acceptance gate policy

```yaml
knowledge_item.v2:
  doc_id: evaluation_acceptance_gate_policy
  version: v2
  species: multi_species
  blueprint_scope: quantitative_genetics
  evidence_level: sop
  source: sop
  updated_at: 2026-05-26T00:00:00Z
  owner: test_eval
```

Evaluation acceptance gates are project-specific and must not be invented after seeing results. Gates should be declared before production scoring and recorded in the audit bundle.

Gate examples:
- required input validation completion
- minimum retained sample and marker counts
- no blocking ID mismatches
- full report index generation
- metric threshold or non-regression criterion
- manual review completed for flagged risks

Risk boundary: post-hoc gate selection is not valid evidence of readiness.

## Diagnostic evaluation policy

```yaml
knowledge_item.v2:
  doc_id: evaluation_diagnostic_policy
  version: v2
  species: multi_species
  blueprint_scope: quantitative_genetics
  evidence_level: sop
  source: sop
  updated_at: 2026-05-26T00:00:00Z
  owner: safety_fuse
```

Diagnostic reports evaluate readiness, failure class, and next repair action rather than scientific performance. They should include retrieval evidence, tool error patterns, scheduler state, affected artifacts, and whether cluster execution remains blocked.

Minimum fields:
- detected failure class
- matching evidence or log pattern
- suggested repair
- safe retry condition
- manual confirmation requirement

Risk boundary: a diagnostic suggestion must not automatically resubmit a failed cluster job.

## Operational acceptance gate

```yaml
knowledge_item.v2:
  doc_id: evaluation_operational_acceptance_gate
  version: v2
  species: multi_species
  blueprint_scope: reporting_audit
  evidence_level: sop
  source: sop
  updated_at: 2026-06-06T21:30:00+08:00
  owner: test_eval
```

Operational acceptance decides whether a GeneAgent run is complete enough for delivery, independent of whether the scientific result is impressive.

Gate checklist:
- input validation completed with no blocking ID, sidecar, or path errors
- dry-run or submit-preview was recorded before execution
- execution mode and resource caps are visible
- submitted command, wrapper path, job ID or shell PID, stdout, and stderr paths are recorded
- report index and audit bundle exist
- every expected artifact is present or has an explicit missing-artifact diagnostic
- no breaker condition is unresolved
- manual-review items are listed separately from automated actions

Failure states:
- `accepted`: all required traces and artifacts exist
- `accepted_with_caveat`: artifact exists but scientific interpretation has stated limits
- `blocked`: missing critical input, execution trace, report index, audit bundle, or safety approval
- `diagnostic_only`: execution did not run, but the failure explanation is complete

Risk boundary: a run can be computationally successful and operationally incomplete if traceability, logs, or report artifacts are missing.
