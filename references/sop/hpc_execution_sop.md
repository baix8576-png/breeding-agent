# HPC Execution SOP

## HPC dry run before submit

```yaml
knowledge_item.v2:
  doc_id: sop_hpc_dry_run_before_submit
  version: v2
  species: multi_species
  blueprint_scope: shared
  evidence_level: sop
  source: sop
  updated_at: 2026-05-26T00:00:00Z
  owner: hpc_scheduler
```

HPC execution must begin with dry-run or submit-preview. The preview should show command, scheduler script, resource request, input paths, output paths, blocking risks, and manual confirmations before any real submit action.

## HPC scheduler portability

```yaml
knowledge_item.v2:
  doc_id: sop_hpc_scheduler_portability
  version: v2
  species: multi_species
  blueprint_scope: shared
  evidence_level: sop
  source: sop
  updated_at: 2026-05-26T00:00:00Z
  owner: hpc_scheduler
```

Scheduler scripts must preserve semantic consistency across SLURM, PBS, and SGE where supported: submit, poll, job ID capture, log paths, and recovery explanation. Queue/account/QOS names remain cluster-local configuration.

## HPC safe retry policy

```yaml
knowledge_item.v2:
  doc_id: sop_hpc_safe_retry_policy
  version: v2
  species: multi_species
  blueprint_scope: shared
  evidence_level: sop
  source: sop
  updated_at: 2026-05-26T00:00:00Z
  owner: safety_fuse
```

Failed jobs must not be resubmitted automatically unless the failure class has an approved safe retry condition. Resource-limit failures, missing input files, account errors, and tool parameter errors require a changed script, changed resource request, or operator confirmation before retry.
