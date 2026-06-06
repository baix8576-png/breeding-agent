# population_genetics

Execution wrappers for population structure and genetic diversity summaries.

Detailed operation guide:
- `operation_guide.md`

Compatibility blueprint:
- `pca_pipeline`

Main entrypoint:
- `run_population_structure_diversity.sh`

Supported toolchain:
- `plink2`: LD pruning, PCA, LD decay, ROH.
- `vcftools`: Fst, pi, Tajima's D when VCF and population files are provided.

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
- `results/structure/popstats/*` (optional)
- `results/structure/figures/README.md`
- `reports/structure_summary.md`
- `reports/stratification_risk.md`

Notes:
- Population labeling and biological interpretation remain expert-review tasks.
- `--dry-run` writes `results/structure/run_manifest.json`, `results/structure/audit_sidecar.json`, and `logs/population_structure_diversity.log` without invoking `plink2` or `vcftools`.
- Scientific-domain knowledge for this directory is maintained across `references/analysis_domains/population_structure.md`, `references/analysis_domains/genetic_diversity_inbreeding.md`, and `references/analysis_domains/selection_signatures.md`.
- Basic Fst, pi, and Tajima's D outputs are first-pass selection-adjacent diagnostics, not a complete selection-signature workflow.
