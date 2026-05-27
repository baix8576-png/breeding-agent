# Diagnostic Report Template

## Diagnostic report template

```yaml
knowledge_item.v2:
  doc_id: template_diagnostic_report
  version: v2
  species: multi_species
  blueprint_scope: shared
  evidence_level: sop
  source: sop
  updated_at: 2026-05-26T00:00:00Z
  owner: safety_fuse
```

A diagnostic report explains readiness or failure state. It should include request scope, detected blueprint, local retrieval hits, missing inputs, scheduler policy, tool failure class, safe next action, and whether cluster execution remains blocked.

Required sections:
- diagnostic summary
- evidence and matched patterns
- affected files or artifacts
- safe repair suggestions
- retry and manual confirmation boundary

## Diagnostic evidence table

```yaml
knowledge_item.v2:
  doc_id: template_diagnostic_evidence_table
  version: v2
  species: multi_species
  blueprint_scope: shared
  evidence_level: sop
  source: sop
  updated_at: 2026-05-26T00:00:00Z
  owner: safety_fuse
```

The diagnostic evidence table should keep `doc_id`, `chunk_id`, `source_path`, `page_or_anchor`, matched log text or rule name, confidence, and recommended action separate. This keeps retrieval confidence distinct from the severity of the operational failure.
