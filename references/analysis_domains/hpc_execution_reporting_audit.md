# HPC Execution Reporting And Audit Domain

This file defines the cross-cutting domain for trusted remote execution evidence, report indexing, diagnostics, traceability, and audit packaging. It applies to ordinary SSH shell execution and scheduler-backed HPC execution.

## Domain scope and operational intent

```yaml
knowledge_item.v2:
  doc_id: domain_hpc_execution_reporting_audit_scope
  version: v2
  species: multi_species
  blueprint_scope: reporting_audit
  evidence_level: sop
  source: sop
  updated_at: 2026-06-06T00:00:00+08:00
  owner: orchestrator
```

Primary `domain_scope`: `hpc_execution_reporting_audit`.

This domain is the production evidence layer for GeneAgent. It does not decide biological meaning. It proves what was planned, submitted, run, collected, diagnosed, reported, and audited.

It covers:
- trusted remote execution evidence
- scheduler or SSH shell job context
- wrapper command and resource context
- stdout/stderr/log capture
- `report_index.v2` inventory
- diagnostic summaries
- traceability exports
- audit bundle assembly

Current execution bridge:
- `scripts/reporting_audit/run_report_generator.sh`
- `scripts/reporting_audit/build_result_index.sh`
- `scripts/reporting_audit/collect_figures.sh`
- `scripts/reporting_audit/render_summary_report.sh`
- `scripts/reporting_audit/export_traceability.sh`

Risk boundary: a complete report package is not proof that the scientific conclusion is correct. It is proof that evidence and caveats are traceable.

## Remote execution traceability policy

```yaml
knowledge_item.v2:
  doc_id: domain_hpc_execution_reporting_remote_traceability_policy
  version: v2
  species: multi_species
  blueprint_scope: reporting_audit
  evidence_level: sop
  source: sop
  updated_at: 2026-06-06T00:00:00+08:00
  owner: hpc_scheduler
```

Every trusted execution should preserve enough context to answer: who asked, what command ran, where it ran, what resources were requested, what job or PID tracked it, where logs landed, and which artifacts were produced.

Required traceability fields:
- `task_id`, `run_id`, `session_id`
- execution mode: `local_preview`, `ssh_shell_trusted`, `ssh_slurm_trusted`, `manual_sbase`, or `hpc_local`
- remote profile name or local execution note
- job ID, shell PID, or synthetic handle
- submit command or wrapper path
- scheduler script path when applicable
- stdout path and stderr path
- audit record path
- report index path
- state path for resume or watch-run

Security constraints:
- Do not serialize passwords, private keys, real credentials, or secret env values.
- Do not copy raw entity data into audit summaries.
- Do not write remote `/data2/...` paths into Windows local directories as if they were local files.
- Keep all local run state under `GENEAGENT_LOCAL_STATE_ROOT` or `.geneagent/runs/*`.

Risk boundary: if job ID/PID and log paths cannot be traced, the run is not production-complete even if output files exist.

## report_index.v2 policy

```yaml
knowledge_item.v2:
  doc_id: domain_hpc_execution_reporting_report_index_policy
  version: v2
  species: multi_species
  blueprint_scope: reporting_audit
  evidence_level: sop
  source: sop
  updated_at: 2026-06-06T00:00:00+08:00
  owner: orchestrator
```

`report_index.v2` is the structured inventory that downstream reports, diagnostics, and audits use as their shared evidence base.

Minimum sections:
- `schema_version`
- `run_context`
- `collections`
- `blueprint_summary`
- `diagnostics`
- `traceability`
- `summary`

Indexing requirements:
- Include declared artifacts and discovered result/report/log files.
- Preserve relative paths for project portability and absolute paths only when needed for operator action.
- Mark missing required blueprint artifacts as warnings.
- Include selected blueprint and coverage status.
- Include scheduler, wrapper, stdout, stderr, and audit links when available.
- Avoid replacing missing evidence with narrative text.

Risk boundary: if an artifact is missing, stale, or outside the approved workspace, the index should expose that as a diagnostic rather than hiding it.

## Diagnostics policy

```yaml
knowledge_item.v2:
  doc_id: domain_hpc_execution_reporting_diagnostic_policy
  version: v2
  species: multi_species
  blueprint_scope: reporting_audit
  evidence_level: sop
  source: sop
  updated_at: 2026-06-06T00:00:00+08:00
  owner: safety_fuse
```

Diagnostics translate logs and artifact gaps into actionable, bounded explanations. They must distinguish transient execution failures from scientific review warnings.

Diagnostic sources:
- scheduler state or SSH shell state
- stdout and stderr
- wrapper logs
- report generator logs
- `run_manifest.json`
- `audit_sidecar.json`
- missing expected artifacts
- known error-pattern knowledge in `references/evaluation/diagnostics/`

Diagnostic classes:
- `failed`: hard error or terminal failed job state
- `warning`: artifact gap, missing optional output, or review caveat
- `in_progress`: job has not reached a terminal state
- `ok`: no obvious failure signals in indexed evidence

Auto-repair boundary:
- Allowed: collect more logs, rerun report packaging with `--force` after outputs are stable, retry transient remote reads.
- Not allowed: change biological filters, overwrite scientific results, bypass resource caps, guess missing inputs, or suppress failing diagnostics.

Risk boundary: diagnostics should support safe recovery. They must not rewrite the scientific story to make a failed run look successful.

## Audit bundle policy

```yaml
knowledge_item.v2:
  doc_id: domain_hpc_execution_reporting_audit_bundle_policy
  version: v2
  species: multi_species
  blueprint_scope: reporting_audit
  evidence_level: sop
  source: sop
  updated_at: 2026-06-06T00:00:00+08:00
  owner: orchestrator
```

Audit bundles package the evidence needed for review, rerun, and handoff. They should be concise enough to inspect, but complete enough to reproduce the executed command path.

Minimum bundle contents:
- request and planning summary
- input summary without raw entity data
- selected blueprint and stage list
- resource request and execution mode
- submit command or wrapper command
- job ID or shell PID
- stdout/stderr/log paths
- report index path
- traceability JSON and markdown
- manual confirmation records
- diagnostic status and unresolved risks

Audit bundle rules:
- Keep raw VCF/BAM/FASTQ/FASTA out of the bundle.
- Keep credentials out of the bundle.
- Preserve path boundaries and remote/local distinctions.
- Store enough metadata for resume-run and watch-run to explain current status.

Risk boundary: a run without an audit bundle is not ready for production acceptance, even if scientific output files exist.

## Execution bridge and artifacts

```yaml
knowledge_item.v2:
  doc_id: domain_hpc_execution_reporting_execution_bridge
  version: v2
  species: multi_species
  blueprint_scope: reporting_audit
  evidence_level: sop
  source: sop
  updated_at: 2026-06-06T00:00:00+08:00
  owner: orchestrator
```

The current execution bridge is `scripts/reporting_audit/`.

Artifact mapping:

| Concern | Current artifact |
|---|---|
| report generator dry-run | `results/report_generator_run_manifest.json` |
| report index | `results/report_index.json` |
| collected figures | `results/figures/*` |
| summary report | `reports/summary_report.md` |
| traceability JSON | `results/traceability/traceability.json` |
| traceability markdown | `results/traceability/traceability.md` |
| report logs | `logs/report_generator.log` |

Bridge responsibilities:
- collect declared figures without overwriting by default
- build and refresh `report_index.v2`
- render a human-readable summary
- export traceability bundles
- preserve scheduler/wrapper/log/audit links

Must not do:
- infer missing scientific results
- validate biological claims without upstream evidence
- modify raw outputs from scientific wrappers
- hide missing required artifacts

Risk boundary: the reporting bridge packages evidence. It is not a scientific inference engine.
