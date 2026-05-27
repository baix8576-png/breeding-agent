# evaluation

Owner: `popgen_quantgen`; diagnostic safety entries owned by `safety_fuse` and `hpc_scheduler`

Purpose:
- Store validation, metric, calibration, subgroup, acceptance gate, and diagnostic evaluation guidance.
- Support genomic prediction reporting, production gates, and failure diagnosis.

Formal knowledge files:
- `evaluation_metric_playbook.md`: cross-validation, bias/calibration, subgroup validation, metric dictionary, acceptance gate, and diagnostic evaluation policy.
- `diagnostics/scheduler_error_patterns.md`: SLURM/PBS diagnostic patterns with `knowledge_item.v2`.
- `diagnostics/bio_tool_error_patterns.md`: `plink2`/`bcftools`/`vcftools`/`gcta` diagnostic patterns with `knowledge_item.v2`.

Maintenance notes:
- Keep benchmark metric definitions separate from measured project results.
- Diagnostic suggestions must not automatically trigger scheduler retries.
- New formal Markdown files must include `knowledge_item.v2`.
