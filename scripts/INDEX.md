# scripts index

This directory holds thin executable wrappers for animal genetics and breeding bioinformatics workflows.

Scripts are grouped by scientific analysis domain. The legacy blueprint keys (`qc_pipeline`, `pca_pipeline`, `grm_builder`, `genomic_prediction`) remain API-compatible routing names, but they no longer define the directory layout.

Current entrypoints:
- `genotype_processing/run_genotype_qc.sh`: genotype QC with PLINK2 and bcftools.
- `population_genetics/run_population_structure_diversity.sh`: LD pruning, PCA, ROH, and optional Fst/pi/Tajima's D.
- `quantitative_genetics/run_relationship_matrix.sh`: GRM/kinship generation with PLINK2 and optional GCTA.
- `quantitative_genetics/run_breeding_value_prediction.sh`: heritability and breeding-value prediction with GCTA.
- `association_mapping/run_gwas.sh`: PLINK2 GWAS association mapping.
- `reporting_audit/run_report_generator.sh`: artifact indexing, summary report rendering, and traceability export.

Common runtime template options:
- `--task-id`, `--run-id`, `--session-id`: run context for audit and report traceability.
- `--threads`: tool thread count; defaults to remote CPU cap env, `SLURM_CPUS_PER_TASK`, or `1`.
- `--memory-mb`: tool memory cap in MB.
- `--tmp-dir`: temporary spill directory for tools.
- `--log-dir`: run log destination; defaults to `workdir/logs`.
- `--dry-run`: write manifests and planned outputs without invoking bioinformatics tools.
- `--force`: allow overwriting template manifest/audit files.

Common template outputs:
- `results/<domain>/run_manifest.json`: `analysis_script_template.v1` run metadata, inputs, outputs, tools, and safety notes.
- `results/<domain>/audit_sidecar.json`: `analysis_script_audit_sidecar.v1` run-context sidecar for downstream report/audit packaging.
- `logs/<pipeline>.log`: script-level stdout/stderr capture for scheduler and report diagnostics.

Subdirectories:
- `genotype_processing/`: sample and variant QC wrappers.
- `population_genetics/`: PCA, LD, ROH, and population-statistics wrappers.
- `quantitative_genetics/`: relationship-matrix and breeding-value prediction wrappers.
- `association_mapping/`: GWAS and future QTL/fine-mapping wrappers.
- `reporting_audit/`: artifact indexing, figure collection, summary report rendering, and traceability export.

Conventions:
- Keep raw data read-only from this layer.
- Do not embed scheduler-specific `sbatch`, `qsub`, or SSH submission logic here; that belongs to `src/scheduler/`.
- Prefer explicit input and output paths over implicit working-directory assumptions.
- Use POSIX-style `/` paths in script arguments; Windows backslash paths are rejected before execution.
