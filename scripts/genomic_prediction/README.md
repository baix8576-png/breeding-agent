# genomic_prediction

Execution wrapper directory for quantitative-genetics analyses in v1.

Main entrypoint:
- `run_genomic_prediction.sh`

Supported toolchain:
- `plink2`: GWAS (`--glm`) and genotype preprocessing.
- `gcta64`: GRM generation, REML heritability, random-effect prediction (when available).

Expected inputs:
- genotype-bearing dataset: VCF or PLINK trio
- phenotype table
- optional covariate table
- optional pedigree table

Expected outputs:
- `results/prediction/cohort_alignment.json`
- `results/prediction/model_family.md`
- `results/prediction/model_spec.json`
- `results/prediction/gwas/README.md`
- `results/prediction/predictions.tsv`
- `results/prediction/validation_plan.md`
- `results/prediction/metrics.tsv`
- `results/prediction/heritability/heritability.hsq` (optional, requires gcta64)
- `reports/genomic_prediction_summary.md`

Notes:
- The wrapper executes real algorithms but does not auto-generate breeding decisions.
