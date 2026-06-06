# genotype_processing

Execution wrappers for genotype preprocessing and QC.

Detailed operation guide:
- `operation_guide.md`

Compatibility blueprint:
- `qc_pipeline`

Main entrypoint:
- `run_genotype_qc.sh`

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
- Scheduler integration is handled by `src/scheduler`; this directory focuses on algorithm execution only.
- `--dry-run` writes `results/qc/run_manifest.json`, `results/qc/audit_sidecar.json`, and `logs/genotype_qc.log` without invoking `plink2` or `bcftools`.
- Scientific-domain knowledge for this directory is maintained in `references/analysis_domains/data_preparation_qc.md` and `references/analysis_domains/genotype_processing.md`; do not treat this script directory as the full animal-genomics taxonomy.
- Advanced phasing, imputation, liftover, and allele-harmonization execution is not complete in this directory yet; use the genotype-processing domain file for planning boundaries.
