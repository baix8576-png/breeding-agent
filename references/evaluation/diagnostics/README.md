# diagnostics

Owner: `hpc_scheduler`, `popgen_quantgen`, `safety_fuse`

Structured knowledge assets for mapping runtime errors to executable remediation actions.

Scope:
- Scheduler diagnostics: SLURM and PBS submit/poll/recovery failures.
- Bioinformatics tool diagnostics: `plink2`, `bcftools`, `vcftools`, `gcta64`.

Formal knowledge files:
- `scheduler_error_patterns.md`: scheduler failures, account/QOS/resource/queue/hold patterns.
- `bio_tool_error_patterns.md`: bio tool input, filtering, index, phenotype, and ID mismatch patterns.

## Stable Markdown Schema (diagnostics_v1)

Each diagnostic entry keeps the same field keys:

1. `pattern_id`
2. `component`
3. `stage`
4. `severity`
5. `trigger_keywords`
6. `trigger_regex`
7. `likely_root_causes`
8. `executable_fix_steps`
9. `command_examples`
10. `risk_notice`
11. `verification`

Maintenance notes:
- Every `## ENTRY` should include `knowledge_item.v2` so the indexer can expose it as a traceable chunk.
- Remediation steps must be explicit and safe; no automatic retry without gate review.
