# dataset bundle template

## Dataset bundle template contract

```yaml
knowledge_item.v2:
  doc_id: input_dataset_bundle_template
  version: v2
  species: multi_species
  blueprint_scope: shared
  evidence_level: sop
  source: sop
  updated_at: 2026-05-26T00:00:00Z
  owner: popgen_quantgen
```

Use this template to describe the local files supplied to a genetics analysis request.

Suggested fields:
- task_id
- run_id
- project name
- species or breed
- cohort name
- genotype dataset path
- genotype data type: VCF, PLINK, or BAM-derived placeholder route
- phenotype table path and key trait columns
- covariate table path and merge key
- pedigree table path and merge key
- sample ID convention
- notes on missing sidecar files

Validation reminders:
- Keep raw data on the local cluster.
- Record file roles explicitly instead of relying on file names alone.
- Confirm PLINK `.bed/.bim/.fam` completeness before generating wrappers.
