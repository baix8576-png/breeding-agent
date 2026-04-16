# grm_builder

Execution wrapper directory for GRM and kinship analyses in v1.

Main entrypoint:
- `run_grm_builder.sh`

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
