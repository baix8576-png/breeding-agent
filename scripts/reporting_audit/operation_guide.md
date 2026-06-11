# Reporting Audit Operation Guide

This guide documents `scripts/reporting_audit/` after the scientific-domain script restructure. It describes how to package artifacts, diagnostics, traceability, and audit evidence without changing scientific outputs.

## Directory role

`scripts/reporting_audit/` is the thin executable layer for report and audit packaging.

Entrypoints:
- `run_report_generator.sh`
- `build_result_index.sh`
- `collect_figures.sh`
- `render_summary_report.sh`
- `export_traceability.sh`

Knowledge domain:

| Current scientific directory | Knowledge domain | Execution role |
|---|---|---|
| `scripts/reporting_audit/` | `hpc_execution_reporting_audit` | package artifacts, diagnostics, traceability, and audit evidence |

The scripts do not run QC, PCA, GRM, GWAS, or prediction analyses. They package artifacts created by those wrappers and by the scheduler/runtime layers.

## Knowledge bridge

- SOP: `references/sop/reporting_audit_execution_sop.md`
- Parameter playbooks: `references/parameter_playbooks/core_parameter_playbooks.md`, `references/parameter_playbooks/scheduler_resource_presets.md`
- Report templates: `references/report_templates/report_index_v2_template.md`, `references/report_templates/audit_bundle_template.md`, `references/report_templates/diagnostic_report_template.md`

## Common invocation

Dry run:

```bash
scripts/reporting_audit/run_report_generator.sh \
  --workdir /data2/user/geneagent_runs/task_006/run_001 \
  --pipeline genomic_prediction \
  --task-id task_006 \
  --run-id run_001 \
  --session-id session_001 \
  --dry-run
```

Full packaging:

```bash
scripts/reporting_audit/run_report_generator.sh \
  --workdir /data2/user/geneagent_runs/task_006/run_001 \
  --results-root /data2/user/geneagent_runs/task_006/run_001/results \
  --pipeline genomic_prediction \
  --task-id task_006 \
  --run-id run_001 \
  --session-id session_001 \
  --job-id shell:12345 \
  --job-state completed \
  --wrapper /data2/user/geneagent_runs/task_006/run_001/run.sh \
  --stdout-path /data2/user/geneagent_runs/task_006/run_001/logs/stdout.log \
  --stderr-path /data2/user/geneagent_runs/task_006/run_001/logs/stderr.log \
  --audit-path /data2/user/geneagent_runs/task_006/run_001/results/prediction/audit_sidecar.json \
  --force
```

All paths should be POSIX `/` paths. Windows local paths should be normalized before remote execution.

## report_index.v2 expectations

The generated index should include:
- `schema_version`
- `run_context`
- `collections`
- `blueprint_summary`
- `diagnostics`
- `traceability`
- `summary`

The index should expose:
- selected blueprint
- artifact counts by type
- missing required markers
- diagnostic status
- scheduler or shell job context
- traceability output paths

It should not invent missing artifacts or suppress gaps.

## Traceability inputs

Recommended command options:

| Option | Meaning |
|---|---|
| `--task-id` | task identity |
| `--run-id` | run identity |
| `--session-id` | local session identity |
| `--job-id` | scheduler job ID or shell PID handle |
| `--job-state` | current or terminal job state |
| `--submit-command` | sanitized submit command |
| `--scheduler-script` | scheduler script path when applicable |
| `--wrapper` | Bash wrapper path |
| `--stdout-path` | stdout log path |
| `--stderr-path` | stderr log path |
| `--audit-path` | audit sidecar or audit record path |
| `--log-path` | additional diagnostic logs, repeatable |

Do not pass secrets, passwords, private keys, or raw entity data through these fields.

## Diagnostics handling

The report generator scans indexed logs and expected artifacts.

Diagnostic outcomes:
- `ok`: no obvious error signals and required artifacts present
- `warning`: missing expected artifacts or non-terminal caveats
- `failed`: hard error signal or failed job state
- `in_progress`: job has not reached a terminal state

Recommended operator flow:
1. Inspect `results/report_index.json`.
2. Open `reports/summary_report.md`.
3. Inspect `results/traceability/traceability.md`.
4. Read stderr before stdout for failed runs.
5. Route tool-specific errors to `references/evaluation/diagnostics/`.

The packaging step may be re-run after upstream outputs become stable, but it must not alter upstream scientific artifacts.

## Output contract

| Path | Meaning |
|---|---|
| `results/report_generator_run_manifest.json` | dry-run or execution manifest |
| `results/report_index.json` | `report_index.v2` structured inventory |
| `results/figures/*` | collected figures |
| `reports/summary_report.md` | human-readable report summary |
| `results/traceability/traceability.json` | structured traceability export |
| `results/traceability/traceability.md` | readable traceability bundle |
| `logs/report_generator.log` | packaging log |

## Safety boundaries

Allowed:
- create report, traceability, and figure directories under the run workdir
- overwrite packaging outputs with `--force`
- refresh the index after traceability files are written
- collect existing figures

Not allowed:
- modify raw genotype/phenotype/result files
- delete or rewrite scientific artifacts
- hide missing required markers
- store credentials in reports or audit bundles
- claim biological validity from packaging completeness

## Cross-links

Use these knowledge assets when planning or explaining this directory:
- `references/analysis_domains/hpc_execution_reporting_audit.md`
- `references/report_templates/report_index_v2_template.md`
- `references/report_templates/audit_bundle_template.md`
- `references/report_templates/diagnostic_report_template.md`
- `references/sop/hpc_execution_sop.md`
- `references/sop/report_review_sop.md`
- `references/evaluation/diagnostics/scheduler_error_patterns.md`
- `references/evaluation/diagnostics/bio_tool_error_patterns.md`
- `references/failure_cases/operational_failure_cases.md`
