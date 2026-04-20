# references index

This directory stores project-local reference documents for genetics workflow design, interpretation boundaries, and report packaging.

Current status:
- Documents in this tree are placeholders and templates.
- They define expected knowledge organization for the MVP but do not claim validated scientific defaults.
- Pipeline blueprints may point to these files as human-readable companions.

Subdirectories:
- `input_specs/`: expected file roles, naming patterns, and dataset bundle templates.
- `qc_rules/`: placeholder thresholds, anomaly review checklists, and QC decision notes.
- `structure_analysis/`: PCA interpretation notes, cluster-labeling cautions, and stratification guidance.
- `modeling_guides/`: genomic prediction route notes and model-family decision templates.
- `evaluation/`: correlation, bias, cross-validation, subgroup validation guidance, and runtime diagnostics playbooks.
- `report_templates/`: markdown templates for QC, structure, and genomic prediction summaries.

Diagnostics entrypoint:
- `evaluation/diagnostics/README.md`: stable markdown schema (`diagnostics_v1`) for pattern-based troubleshooting knowledge.
- `evaluation/diagnostics/scheduler_error_patterns.md`: common SLURM/PBS submit and poll failures with executable remediation steps.
- `evaluation/diagnostics/bio_tool_error_patterns.md`: common `plink2`/`bcftools`/`vcftools`/`gcta64` failures with executable remediation steps.

Conventions:
- Keep thresholds and modeling choices explicitly marked as project-specific until validated by SOPs.
- Reference files should explain assumptions, not hide them.
- If a blueprint depends on a reference file, list the exact file path inside the blueprint asset index.
