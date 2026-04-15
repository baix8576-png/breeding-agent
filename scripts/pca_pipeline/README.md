# pca_pipeline

Placeholder directory for PCA and population-structure shell templates.

Planned contents:
- `manifest.example.yaml`: placeholder contract for LD pruning and PCA wrappers.
- `run_pca_pipeline.sh`: future PCA pipeline launcher.
- `ld_prune.sh`: marker-pruning wrapper placeholder.
- `export_pca_outputs.sh`: eigenvec/eigenval export helper placeholder.
- `assemble_structure_report.sh`: structure summary helper placeholder.

Expected inputs:
- genotype-bearing dataset: VCF or PLINK trio
- optional covariate table

Expected outputs:
- `results/structure/pruning_manifest.json`
- `results/structure/pca/eigenvec.tsv`
- `results/structure/pca/eigenval.tsv`
- `results/structure/figures/README.md`
- `reports/structure_summary.md`
- `reports/stratification_risk.md`

Notes:
- Cluster labeling and ancestry interpretation are intentionally out of scope.
