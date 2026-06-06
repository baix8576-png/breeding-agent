# breeding_value_prediction

Execution wrapper for quantitative-genetics breeding-value prediction.

Compatibility blueprint:
- `genomic_prediction`

Main entrypoint:
- `run_breeding_value_prediction.sh`

Supported toolchain:
- `plink2`: VCF-to-PLINK conversion when needed.
- `gcta64`: GRM generation, REML heritability, and random-effect prediction.

Expected inputs:
- genotype-bearing dataset: VCF or PLINK trio
- phenotype table
- optional covariate table
- optional pedigree table

Expected outputs:
- `results/prediction/cohort_alignment.json`
- `results/prediction/model_family.md`
- `results/prediction/model_spec.json`
- `results/prediction/predictions.tsv`
- `results/prediction/validation_plan.md`
- `results/prediction/metrics.tsv`
- `results/prediction/heritability/heritability.hsq` (optional)
- `reports/genomic_prediction_summary.md`

Notes:
- GWAS is handled by `scripts/association_mapping/run_gwas.sh`, not this wrapper.
- The wrapper executes real algorithms but does not auto-generate breeding decisions.
- `--dry-run` writes `results/prediction/run_manifest.json`, `results/prediction/audit_sidecar.json`, and `logs/breeding_value_prediction.log` without invoking `plink2` or `gcta64`.
