# Quantitative Genetics Execution SOP

## Scope and Inputs

```yaml
knowledge_item.v2:
  doc_id: sop_quantitative_genetics_execution
  version: v2
  species: multi_species
  blueprint_scope: quantitative_genetics
  evidence_level: sop
  source: sop
  updated_at: 2026-06-11T00:00:00+08:00
  owner: popgen_quantgen
```

This SOP covers relationship-matrix construction, GRM/kinship summaries, variance-component estimation, heritability review, and first-pass genomic prediction or breeding-value outputs currently routed through `scripts/quantitative_genetics/`.

Inputs include a genotype matrix, optional pedigree, phenotype table, covariate table, trait-column hint, and previously generated QC/structure summaries. ssGBLUP, Bayesian prediction, machine-learning prediction, and breeding decisions remain planning/reporting topics unless a dedicated executable backend is available.

## Preflight Checks

- Confirm genotype samples, phenotype IDs, covariates, and pedigree IDs are reconciled before execution.
- Require trait type, trait units, missingness handling, fixed/random effect intent, and validation design to be declared.
- Confirm `gcta`/`plink2` availability for requested GRM/REML operations.
- Require explicit `--threads`, `--memory-mb`, `--tmp-dir`, `--log-dir`, and run-root-contained outputs.
- Block prediction deployment claims when no cross-validation, calibration, or subgroup validation artifact exists.

## Execution Steps

1. Build GRM or kinship inputs and record marker/sample order.
2. Write `grm_ids.tsv` and matrix provenance before downstream modeling.
3. Run or simulate GCTA REML or prediction steps according to tool availability.
4. Record model specification, phenotype/covariate role, and trait interpretation boundary.
5. Produce validation placeholders only when validation is explicitly run; never invent accuracy.
6. Package matrix QC, variance-component summaries, and prediction audit sidecars.

## Expected Outputs

- `results/grm/run_manifest.json`
- `results/grm/audit_sidecar.json`
- `results/grm/marker_standardization.md`
- `results/grm/grm_matrix.tsv` or a pointer to binary GRM outputs
- `results/grm/grm_ids.tsv`
- `reports/grm_qc.md`
- `results/prediction/run_manifest.json`
- `results/prediction/audit_sidecar.json`
- `results/prediction/model_spec.json`
- `results/prediction/gebv.tsv` when prediction is executed
- `results/prediction/validation_metrics.tsv` when validation is executed
- `reports/prediction_summary.md`

## Failure and Breaker Rules

Breaker conditions include genotype/phenotype ID mismatch, missing trait column, missing GRM sample order, matrix dimension mismatch, GCTA convergence failure, unknown fixed/random effect intent, resource requests above caps, and any attempt to auto-change sample filters or breeding decisions after model failure.

Low-risk repairs include creating directories, writing sidecar manifests, retrying transient file reads, and reporting model non-convergence with safer next steps. The Agent must not silently drop animals, alter phenotypes, or change validation splits.

## Report and Audit Handoff

Reports must include trait definition, sample counts, matrix construction method, model family, fixed/random effect summary, validation availability, bias/calibration notes, subgroup caveats, and a clear statement that breeding decisions require human review. Audit records must keep sample-order files and model specs traceable.
