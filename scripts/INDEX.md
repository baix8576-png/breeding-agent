# scripts index

This directory holds executable shell wrappers owned by the genetics pipeline layer.

Current status:
- `qc_pipeline/run_qc_pipeline.sh` executes QC metrics with plink2/bcftools.
- `pca_pipeline/run_pca_pipeline.sh` executes PCA, LD, ROH, and optional Fst/pi/Tajima's D.
- `grm_builder/run_grm_builder.sh` executes GRM/kinship generation with plink2 and optional gcta64.
- `genomic_prediction/run_genomic_prediction.sh` executes GWAS plus optional heritability/prediction with gcta64.
- Scheduler submission still belongs to `src/scheduler`; scripts are pure analysis wrappers.

Subdirectories:
- `qc_pipeline/`: sample and variant QC execution wrappers.
- `pca_pipeline/`: LD pruning, PCA, population-statistics wrappers.
- `grm_builder/`: relationship matrix builders and matrix QC wrappers.
- `genomic_prediction/`: GWAS, heritability, and genomic prediction wrappers.
- `report_generator/`: artifact indexing, figure collection, summary report rendering, and traceability export.

Expected file pattern per subdirectory:
- `README.md`: scope, inputs, outputs, and runtime dependencies.
- `build_result_index.sh`, `collect_figures.sh`, `render_summary_report.sh`, `export_traceability.sh`: executable report-packaging entrypoints.
- `manifest.example.yaml`: example contract for workflow integration.

Conventions:
- Keep raw data read-only from this layer.
- Do not embed scheduler-specific `sbatch` or `qsub` logic here; that belongs to the scheduler layer.
- Prefer explicit input and output paths over implicit working-directory assumptions.
