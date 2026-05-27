# Audit Bundle Template

## Audit bundle template

```yaml
knowledge_item.v2:
  doc_id: template_audit_bundle
  version: v2
  species: multi_species
  blueprint_scope: shared
  evidence_level: sop
  source: sop
  updated_at: 2026-05-26T00:00:00Z
  owner: orchestrator
```

The audit bundle captures the evidence needed to reconstruct a run without storing raw entity data. It should include input summaries, normalized paths, planning summary, generated commands, scheduler IDs, log paths, manual confirmations, diagnostic outcomes, and report index references.

Required exclusions:
- no raw VCF, BAM, FASTQ, FASTA, or large private entity data
- no secrets, tokens, private keys, or credentials
- no copyrighted full-text PDF or TEI unless explicitly cleared

## Audit manual confirmation record

```yaml
knowledge_item.v2:
  doc_id: template_audit_manual_confirmation_record
  version: v2
  species: multi_species
  blueprint_scope: shared
  evidence_level: sop
  source: sop
  updated_at: 2026-05-26T00:00:00Z
  owner: safety_fuse
```

Manual confirmation records should capture high-risk action type, operator identity or local alias, timestamp, requested action, approved scope, affected files or job IDs, and rollback plan. Confirmation is required for overwrite, delete, cross-directory write, unusual resource request, and failed-job retry.
