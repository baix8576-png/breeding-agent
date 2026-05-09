# Genomic Prediction Stage SOP (v1)

```yaml
knowledge_item.v2:
  doc_id: "sop_genomic_prediction_stage_v1"
  version: "v2"
  species: "multi_species"
  blueprint_scope: "genomic_prediction"
  evidence_level: "sop"
  source: "sop"
  updated_at: "2026-05-09T15:10:00+08:00"
  owner: "popgen_quantgen"
```

## Purpose
- Standardize stage-by-stage operation for `genomic_prediction`.
- Keep behavior aligned with `scripts/genomic_prediction/run_genomic_prediction.sh`.

## Stage: cohort_alignment

### Input Thresholds
- Required:
- genotype backbone (PLINK trio or VCF convertible to PLINK)
- phenotype table (must exist and be readable)
- Optional:
- covariate table
- pedigree table
- Recommended cohort size >= 50 for baseline model diagnostics.

### Default Parameters
- `analysis_targets=gwas,heritability,genomic_prediction`
- Auto-discovery fallback:
- phenotype filename patterns: `*pheno*` or `*trait*`
- VCF to PLINK conversion via `plink2 --vcf --make-bed` when needed
- Output manifest:
- `results/prediction/cohort_alignment.json`

### Manual Confirmation Points
- Confirm sample ID namespace is consistent across genotype/phenotype/covariate/pedigree.
- Confirm trait column or trait selection logic before training.
- Confirm missing phenotype handling policy before model execution.

### Disable Conditions
- Phenotype table missing or unreadable.
- No usable genotype backbone.
- Validation gate reports blocking consistency failures.

## Stage: relationship_selection

### Input Thresholds
- Cohort alignment manifest must be present.
- At least one executable modeling backend route must be available.

### Default Parameters
- Default backbone note:
- GBLUP-compatible path using GCTA REML + random-effect prediction
- Optional routes:
- PLINK2 GWAS (`--glm hide-covar --allow-no-sex`)
- ssGBLUP/Bayes pathways require explicit manual opt-in and supporting assets
- Output note:
- `results/prediction/model_family.md`

### Manual Confirmation Points
- Confirm selected model family is fit-for-purpose for trait architecture.
- Confirm whether pedigree is included and why.
- Confirm if covariates are enforced, optional, or excluded.

### Disable Conditions
- No backend tool available (`plink2` and `gcta64` both unavailable for requested targets).
- Requested route lacks required inputs (for example, heritability without phenotype).
- Attempt to auto-escalate from diagnostics to breeding decisions.

## Stage: model_blueprint

### Input Thresholds
- `cohort_alignment.json` and `model_family.md` required.
- Trait specification must be explicit (`--trait-column` or documented auto-detection rule).

### Default Parameters
- Model specification output:
- `results/prediction/model_spec.json`
- GWAS default command block:
- `plink2 --glm hide-covar --allow-no-sex`
- GCTA default command block:
- `gcta64 --make-grm`
- `gcta64 --reml --reml-pred-rand`
- Prediction output:
- `results/prediction/predictions.tsv`

### Manual Confirmation Points
- Confirm fixed/random effects are documented before execution.
- Confirm fallback behavior if `heritability.indi.blp` is missing.
- Confirm GWAS outputs are indexed and not over-interpreted.

### Disable Conditions
- No execution step succeeds for requested targets.
- Model spec cannot be serialized.
- Prediction output cannot be produced even as fallback sample list.

## Stage: cross_validation_design

### Input Thresholds
- Model spec must exist.
- Metric output path must be writable.

### Default Parameters
- Validation design baseline:
- k-fold cross-validation for production contexts
- track predictive correlation and calibration bias by cohort
- Outputs:
- `results/prediction/validation_plan.md`
- `results/prediction/metrics.tsv`
- optional `results/prediction/heritability/heritability.hsq`

### Manual Confirmation Points
- Confirm fold strategy (random, family-aware, time-aware) with analyst.
- Confirm subgroup slices for bias checks.
- Confirm acceptable metric floor before downstream usage.

### Disable Conditions
- Validation plan generation fails.
- Metric extraction fails and no fallback metric rows are available.
- Requested evaluation policy conflicts with safety gate.

## Stage: prediction_report

### Input Thresholds
- `predictions.tsv` and `metrics.tsv` required.
- At least one executed modeling step recorded.

### Default Parameters
- Summary output:
- `reports/genomic_prediction_summary.md`
- Expected indexed artifacts:
- `results/prediction/cohort_alignment.json`
- `results/prediction/model_family.md`
- `results/prediction/model_spec.json`
- `results/prediction/gwas/README.md`
- `results/prediction/predictions.tsv`
- `results/prediction/validation_plan.md`
- `results/prediction/metrics.tsv`

### Manual Confirmation Points
- Confirm report language stays at diagnostics/analysis level.
- Confirm no automatic breeding or culling recommendation is emitted.
- Confirm uncertainty and caveats are clearly listed.

### Disable Conditions
- Prediction or metric artifacts missing.
- Report generation fails.
- Any request asks to convert one-run metrics into final breeding decisions without human review.
