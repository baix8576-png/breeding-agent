# Report Review SOP

## Report review traceability

```yaml
knowledge_item.v2:
  doc_id: sop_report_review_traceability
  version: v2
  species: multi_species
  blueprint_scope: reporting_audit
  evidence_level: sop
  source: sop
  updated_at: 2026-05-26T00:00:00Z
  owner: orchestrator
```

A report is reviewable only if it links input summary, blueprint selection, generated scripts, scheduler state, artifacts, diagnostics, and audit bundle. Reviewers should reject reports that contain output metrics without `report_index.v2` traceability.

## Report interpretation boundary

```yaml
knowledge_item.v2:
  doc_id: sop_report_interpretation_boundary
  version: v2
  species: multi_species
  blueprint_scope: reporting_audit
  evidence_level: sop
  source: sop
  updated_at: 2026-05-26T00:00:00Z
  owner: safety_fuse
```

Generated narrative must distinguish observed results, diagnostic warnings, literature-supported context, and expert-review recommendations. It must not turn placeholder metrics, dry-run previews, or low-confidence retrieval hits into production conclusions.

## Report signoff checklist

```yaml
knowledge_item.v2:
  doc_id: sop_report_signoff_checklist
  version: v2
  species: multi_species
  blueprint_scope: reporting_audit
  evidence_level: sop
  source: sop
  updated_at: 2026-05-26T00:00:00Z
  owner: test_eval
```

Signoff requires input validation completed, blocking diagnostics resolved or documented, report index present, audit bundle present, manual review items listed, and no raw entity data embedded in the report package.
