# relationship_matrix

Execution wrapper for genomic relationship matrix and kinship analysis.

Compatibility blueprint:
- `grm_builder`

Main entrypoint:
- `run_relationship_matrix.sh`

Supported toolchain:
- `plink2`: relationship matrix (`--make-rel square`) generation.
- `gcta64`: binary GRM generation for downstream quantitative-genetics tools.

Expected inputs:
- genotype-bearing dataset: VCF or PLINK trio
- optional pedigree table

Expected outputs:
- `results/grm/marker_standardization.md`
- `results/grm/grm_matrix.tsv`
- `results/grm/grm_ids.tsv`
- `reports/grm_qc.md`
- `results/grm/README.md`

Notes:
- Wrapper can run with `plink2`, `gcta64`, or both; outputs are indexed for downstream model stages.
- `--dry-run` writes `results/grm/run_manifest.json`, `results/grm/audit_sidecar.json`, and `logs/relationship_matrix.log` without invoking `plink2` or `gcta64`.
