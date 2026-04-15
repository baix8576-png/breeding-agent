# qc_pipeline

Placeholder directory for quality-control shell templates and wrapper scripts.

Planned contents:
- `manifest.example.yaml`: placeholder contract for QC tool wrappers and expected sidecar files.
- `run_qc_pipeline.sh`: future non-destructive QC launcher entrypoint.
- `sample_qc.sh`: sample-level QC wrapper placeholder.
- `variant_qc.sh`: marker-level QC wrapper placeholder.
- `assemble_qc_report.sh`: QC artifact bundling helper placeholder.

Expected inputs:
- genotype-bearing dataset: VCF or PLINK trio
- optional phenotype table
- optional pedigree table

Expected outputs:
- `results/qc/input_manifest.json`
- `results/qc/sample_qc.tsv`
- `results/qc/variant_qc.tsv`
- `reports/qc_summary.md`
- `results/qc/retained_dataset/README.md`

Notes:
- This directory defines wrapper boundaries only.
- Real filtering logic, thresholds, and scheduler submission remain out of scope here.
