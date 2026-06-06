# QC Defaults

## QC defaults file

```yaml
knowledge_item.v2:
  doc_id: playbook_qc_defaults_file
  version: v2
  species: multi_species
  blueprint_scope: genotype_processing
  evidence_level: expert_opinion
  source: parameter_playbook
  updated_at: 2026-05-26T00:00:00Z
  owner: popgen_quantgen
```

This file is the dedicated lookup anchor for QC default parameters. Use it with `playbook_qc_defaults` and `qc_rule_*` cards when generating dry-run parameters for missingness, MAF, HWE review, duplicate marker checks, heterozygosity outlier review, and retained-count reporting.

Defaults must be shown to the user as editable recommendations. They are not universal scientific thresholds and should not overwrite project-specific SOP settings.
