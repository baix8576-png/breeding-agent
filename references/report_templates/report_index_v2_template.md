# report_index.v2 template

## report_index.v2 template

```yaml
knowledge_item.v2:
  doc_id: template_report_index_v2
  version: v2
  species: multi_species
  blueprint_scope: reporting_audit
  evidence_level: sop
  source: sop
  updated_at: 2026-05-26T00:00:00Z
  owner: orchestrator
```

`report_index.v2` is the structured inventory that connects run context, input summary, blueprint summary, collections, diagnostics, traceability, and final summary. It should be generated for dry-run artifacts when possible and is required for submitted runs.

Minimum sections:
- `schema_version`
- `run_context`
- `collections`
- `blueprint_summary`
- `diagnostics`
- `traceability`
- `summary`

Required caution: a report without this index is incomplete for production acceptance.

## report_index traceability entries

```yaml
knowledge_item.v2:
  doc_id: template_report_index_traceability_entries
  version: v2
  species: multi_species
  blueprint_scope: reporting_audit
  evidence_level: sop
  source: sop
  updated_at: 2026-05-26T00:00:00Z
  owner: orchestrator
```

Each traceability entry should connect an artifact, source input or command, originating stage, path, optional checksum, and interpretation status. The report should expose missing or stale artifacts as diagnostics rather than hiding them in narrative text.

## Report review completion gate

```yaml
knowledge_item.v2:
  doc_id: template_report_review_completion_gate
  version: v2
  species: multi_species
  blueprint_scope: reporting_audit
  evidence_level: sop
  source: sop
  updated_at: 2026-06-06T21:30:00+08:00
  owner: orchestrator
```

A report is complete only when it can be traced from user request to inputs, plan, execution, artifacts, diagnostics, and interpretation boundaries.

Review checklist:
- `schema_version` is present and matches `report_index.v2`
- `run_context` includes task ID, run ID, session ID, working directory, and execution mode
- input summary lists genotype, phenotype, covariate, pedigree, sidecar, and reference roles when supplied
- blueprint summary names the domain and execution bridge without confusing compatibility keys with scientific domains
- artifact collection lists every expected result, log, and report path
- diagnostics include blockers, warnings, and manual-review items
- traceability links commands, job ID or PID, stdout, stderr, and source inputs
- final summary separates completed, partial, blocked, and diagnostic-only outcomes

Blocking report gaps:
- no `report_index.v2`
- missing run context
- missing command or execution trace for submitted runs
- missing stdout/stderr paths
- missing artifact inventory
- interpretation claims without evidence source or caveat

Risk boundary: a narrative report without structured traceability is not production complete.
