# report_generator

Placeholder directory for report and artifact assembly scripts.

Planned contents:
- `manifest.example.yaml`: placeholder contract for report assembly helpers.
- `build_result_index.sh`: artifact inventory helper placeholder.
- `collect_figures.sh`: figure collation helper placeholder.
- `render_summary_report.sh`: markdown report renderer placeholder.
- `export_traceability.sh`: metadata export helper placeholder.

Expected inputs:
- stage output manifests from QC, PCA, GRM, or genomic prediction workflows
- optional figure directories
- optional audit metadata exported by other layers

Expected outputs:
- `reports/*.md`
- `results/*/README.md`
- `results/report_index.json`

Notes:
- Report assembly does not validate scientific claims; it only packages declared artifacts.
