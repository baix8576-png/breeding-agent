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
