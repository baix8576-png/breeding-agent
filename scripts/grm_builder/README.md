# grm_builder

Placeholder directory for relationship matrix and kinship builder scripts.

Planned contents:
- `manifest.example.yaml`: placeholder contract for GRM builders and matrix QC.
- `run_grm_builder.sh`: future relationship-matrix launcher.
- `build_grm.sh`: matrix construction wrapper placeholder.
- `convert_matrix_format.sh`: matrix export helper placeholder.
- `check_grm_matrix.sh`: matrix QC helper placeholder.

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
- This layer only defines artifact contracts and stage boundaries.
