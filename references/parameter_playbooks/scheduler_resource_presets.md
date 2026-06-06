# Scheduler Resource Presets

## Scheduler resource presets file

```yaml
knowledge_item.v2:
  doc_id: playbook_scheduler_resource_presets_file
  version: v2
  species: multi_species
  blueprint_scope: reporting_audit
  evidence_level: sop
  source: parameter_playbook
  updated_at: 2026-05-26T00:00:00Z
  owner: hpc_scheduler
```

This file is the dedicated lookup anchor for SLURM, PBS, and SGE resource presets. It records queue or partition target, walltime, memory, CPU count, scratch path, job name, log path, and retry boundary as cluster-specific settings rather than global constants.
