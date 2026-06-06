# parameter_playbooks

Owner: `popgen_quantgen`; scheduler entries owned by `hpc_scheduler`

Purpose:
- Store reusable parameter presets and tuning boundaries for `qc / pca / grm / gwas / genomic_prediction` compatibility blueprints and their scientific-domain scripts.
- Support dry-run, submit-preview, report explanation, and manual review.

Formal knowledge files:
- `core_parameter_playbooks.md`: consolidated indexed overview for core parameter policies.
- `qc_defaults.md`: dedicated QC defaults lookup anchor.
- `pca_component_policy.md`: dedicated PCA component policy lookup anchor.
- `grm_resource_baseline.md`: dedicated GRM resource estimate lookup anchor.
- `genomic_prediction_cv_policy.md`: dedicated genomic prediction CV policy lookup anchor.
- `scheduler_resource_presets.md`: dedicated SLURM/PBS/SGE resource preset lookup anchor.

Maintenance notes:
- Presets are not universal defaults; keep cluster and project overrides visible.
- New formal Markdown files must include `knowledge_item.v2`.
