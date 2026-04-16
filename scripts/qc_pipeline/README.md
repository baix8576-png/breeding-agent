# qc_pipeline

Execution wrapper directory for genotype QC in v1.

Main entrypoint:
- `run_qc_pipeline.sh`

Supported toolchain:
- `plink2`: sample/variant missingness, HWE, allele frequency.
- `bcftools`: VCF-level stats.

Expected inputs:
- genotype-bearing dataset: VCF or PLINK trio
- optional phenotype table
- optional covariate table
- optional pedigree table

Expected outputs:
- `results/qc/input_manifest.json`
- `results/qc/sample_qc.tsv`
- `results/qc/variant_qc.tsv`
- `results/qc/retained_dataset/README.md`
- `reports/qc_summary.md`

Notes:
- Wrapper supports explicit input arguments and automatic discovery under `--input-root`.
- Scheduler integration is handled by `src/scheduler`; this directory focuses on algorithm execution only.
