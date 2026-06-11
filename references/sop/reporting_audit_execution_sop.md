# Reporting Audit Execution SOP

## Scope and Inputs

```yaml
knowledge_item.v2:
  doc_id: sop_reporting_audit_execution
  version: v2
  species: multi_species
  blueprint_scope: reporting_audit
  evidence_level: sop
  source: sop
  updated_at: 2026-06-11T00:00:00+08:00
  owner: popgen_quantgen
```

This SOP covers report-index generation, artifact packaging, traceability export, diagnostic summarization, and audit bundle handoff through `scripts/reporting_audit/`. It does not run scientific analyses or change upstream results.

Inputs include a run working directory, results root, task/run/session IDs, pipeline name, optional job ID/state, wrapper path, stdout/stderr paths, diagnostic logs, and audit sidecar paths.

## Preflight Checks

- Confirm report generation writes only under the approved run root.
- Confirm secrets, passwords, private keys, raw entity data, and real credentials are not included in report options or logs.
- Verify expected upstream artifact directories exist or record missing-artifact diagnostics.
- Require `task_id`, `run_id`, `session_id`, pipeline name, and report output directory.
- Block packaging if it would overwrite an existing report bundle without explicit approval.

## Execution Steps

1. Scan results, reports, logs, and traceability inputs.
2. Build or update `report_index.v2` with run context, collections, blueprint summary, diagnostics, traceability, and summary.
3. Render summary report sections from existing artifacts only.
4. Export traceability records linking command, wrapper, job ID, logs, artifact paths, and audit sidecars.
5. Mark missing required artifacts as warnings or failures instead of inventing outputs.
6. Produce an audit bundle manifest for downstream review.

## Expected Outputs

- `results/report_index.json`
- `reports/summary_report.md`
- `results/traceability/traceability.md`
- `results/audit/audit_bundle_manifest.json`
- `results/audit/diagnostic_summary.json`
- copied or indexed figure/table references when present
- `logs/reporting_audit.log`

## Failure and Breaker Rules

Breaker conditions include writing outside the run root, secret or credential exposure, missing required run IDs, malformed upstream audit sidecars, output overwrite risk, path traversal, and attempts to alter upstream scientific artifacts.

Low-risk repairs include creating report/log directories, indexing existing artifacts, recording missing-output diagnostics, and re-running report packaging after upstream jobs finish. The Agent must not delete upstream results, suppress failed-job status, or fabricate metrics/figures.

## Report and Audit Handoff

The final report package must make provenance visible: input summary, planning summary, execution mode, command preview or submit command, job ID/PID, stdout/stderr paths, artifact index, diagnostics, missing artifacts, and manual confirmation records. The audit bundle is the handoff object for later review and resume.
