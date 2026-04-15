# scripts index

This directory holds future shell templates and wrapper entrypoints owned by the genetics pipeline layer.

Current status:
- All script directories are placeholders only.
- No real genetics algorithm, scheduler submission logic, or destructive file operation is implemented here.
- The purpose of this index is to keep file naming and ownership stable while multiple roles work in parallel.

Subdirectories:
- `qc_pipeline/`: input checks, sample QC wrappers, variant QC wrappers, and QC report assembly.
- `pca_pipeline/`: LD pruning, PCA export, and structure summary helpers.
- `grm_builder/`: relationship matrix builders, format converters, and matrix QC helpers.
- `genomic_prediction/`: genomic prediction launchers for GBLUP, ssGBLUP, Bayes, or equivalent placeholder routes.
- `report_generator/`: artifact indexing, figure collection, summary report rendering, and traceability export.

Expected placeholder file pattern per subdirectory:
- `README.md`: scope, inputs, outputs, and future file inventory.
- `manifest.yaml` or `manifest.example.yaml`: tool contract placeholder.
- `run_<workflow>.sh`: future non-destructive wrapper entrypoint.
- `assemble_<report>.sh`: future report or artifact assembly helper when relevant.

Conventions:
- Keep raw data read-only from this layer.
- Do not embed scheduler-specific `sbatch` or `qsub` logic here; that belongs to the scheduler layer.
- Prefer explicit input and output paths over implicit working-directory assumptions.
