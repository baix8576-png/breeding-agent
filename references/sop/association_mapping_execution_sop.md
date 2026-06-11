# Association Mapping Execution SOP

## Scope and Inputs

```yaml
knowledge_item.v2:
  doc_id: sop_association_mapping_execution
  version: v2
  species: multi_species
  blueprint_scope: association_mapping
  evidence_level: sop
  source: sop
  updated_at: 2026-06-11T00:00:00+08:00
  owner: popgen_quantgen
```

This SOP covers first-pass marker-trait association execution for GWAS-style requests currently routed through `scripts/association_mapping/run_gwas.sh`. It supports PLINK2 `--glm` style exploratory association when genotype, phenotype, trait, and optional covariates are explicit.

QTL interval mapping, fine mapping, mixed-model GWAS, credible sets, causal inference, and functional validation are not automatic execution outputs in the current bridge.

## Preflight Checks

- Confirm genotype input, phenotype table, and requested trait column exist.
- Confirm phenotype sample IDs match genotype sample IDs or are stopped for upstream reconciliation.
- Record trait type, covariate file, PCA/structure correction intent, and multiple-testing policy.
- Require explicit `--threads`, `--memory-mb`, `--tmp-dir`, and `--log-dir`.
- Block GWAS execution when no phenotype, no trait column, unknown tool, non-POSIX path, or overwrite risk is detected.

## Execution Steps

1. Build cohort-alignment and model-spec sidecars.
2. Validate genotype, phenotype, covariate, and trait inputs.
3. Run or simulate PLINK2 association according to dry-run/tool availability.
4. Write metrics and README indexes for raw association outputs.
5. Flag whether QQ/Manhattan plots, genomic-control checks, and annotation are present or still missing.
6. Hand off candidate interpretation to report/knowledge reasoning only when artifacts exist.

## Expected Outputs

- `results/association/gwas/run_manifest.json`
- `results/association/gwas/audit_sidecar.json`
- `results/association/gwas/cohort_alignment.json`
- `results/association/gwas/model_spec.json`
- `results/association/gwas/README.md`
- `results/association/gwas/metrics.tsv`
- PLINK2 association output files when execution is enabled
- `reports/gwas_summary.md`
- `logs/association_mapping_gwas.log`

## Failure and Breaker Rules

Breaker conditions include missing phenotype, missing trait column, genotype/phenotype mismatch, unknown covariate role, missing `plink2`, resource requests above caps, non-POSIX paths, output overwrite risk, and attempts to report unvalidated associations as causal.

Low-risk repairs include creating run-local directories, emitting dry-run model specs, and recommending covariate/PCA review. The Agent must not auto-drop samples, impute phenotypes, choose covariates without review, or change trait encoding after a failed run.

## Report and Audit Handoff

Reports must state the model family, phenotype trait, covariates, population correction status, multiple-testing interpretation, artifact availability, and candidate-region caveats. Audit handoff must retain cohort-alignment files, model specs, command previews, logs, and explicit notes when mixed-model or QTL analysis was out of scope.
