# association_mapping

Execution wrappers for marker-trait association analysis.

Detailed operation guide:
- `operation_guide.md`

Compatibility blueprint:
- `association_mapping_gwas`

Main entrypoint:
- `run_gwas.sh`

Supported toolchain:
- `plink2`: bounded `--glm` GWAS execution.

Expected inputs:
- genotype-bearing dataset: VCF or PLINK trio
- phenotype table
- optional covariate table

Expected outputs:
- `results/association/gwas/cohort_alignment.json`
- `results/association/gwas/model_spec.json`
- `results/association/gwas/README.md`
- `results/association/gwas/metrics.tsv`
- `reports/gwas_summary.md`

Notes:
- Locus interpretation, fine mapping, and functional validation are downstream reviewed tasks.
- `--dry-run` writes `results/association/gwas/run_manifest.json`, `results/association/gwas/audit_sidecar.json`, and `logs/association_mapping_gwas.log` without invoking `plink2`.
- Scientific-domain knowledge for this directory is maintained in `references/analysis_domains/association_mapping_gwas_qtl.md`.
- Current execution is first-pass PLINK2 GWAS only; QTL, fine mapping, candidate-gene interpretation, and functional validation remain reviewed downstream tasks.
