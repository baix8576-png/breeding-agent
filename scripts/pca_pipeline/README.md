# pca_pipeline

Execution wrapper directory for population genetics analyses in v1.

Main entrypoint:
- `run_pca_pipeline.sh`

Supported toolchain:
- `plink2`: LD pruning, PCA, LD decay, ROH.
- `vcftools`: Fst, pi, Tajima's D (when VCF and required group files are provided).

Expected inputs:
- genotype-bearing dataset: VCF or PLINK trio
- optional covariate table
- optional population sample lists (`--population-a`, `--population-b`) for Fst

Expected outputs:
- `results/structure/pruning_manifest.json`
- `results/structure/pca/eigenvec.tsv`
- `results/structure/pca/eigenval.tsv`
- `results/structure/ld/ld_decay.ld.gz` (optional)
- `results/structure/roh/roh.hom` (optional)
- `results/structure/popstats/*` (optional, depends on vcftools inputs)
- `results/structure/figures/README.md`
- `reports/structure_summary.md`
- `reports/stratification_risk.md`

Notes:
- Population labeling and biological interpretation remain expert-review tasks.
