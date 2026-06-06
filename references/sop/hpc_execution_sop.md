# HPC Execution SOP

## HPC dry run before submit

```yaml
knowledge_item.v2:
  doc_id: sop_hpc_dry_run_before_submit
  version: v2
  species: multi_species
  blueprint_scope: reporting_audit
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
  blueprint_scope: reporting_audit
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
  blueprint_scope: reporting_audit
  evidence_level: sop
  source: sop
  updated_at: 2026-05-26T00:00:00Z
  owner: safety_fuse
```

Failed jobs must not be resubmitted automatically unless the failure class has an approved safe retry condition. Resource-limit failures, missing input files, account errors, and tool parameter errors require a changed script, changed resource request, or operator confirmation before retry.

## Remote shell execution review gate

```yaml
knowledge_item.v2:
  doc_id: sop_remote_shell_execution_review_gate
  version: v2
  species: multi_species
  blueprint_scope: reporting_audit
  evidence_level: sop
  source: sop
  updated_at: 2026-06-06T21:30:00+08:00
  owner: hpc_scheduler
```

Ordinary Linux server execution through `ssh_shell_trusted` must pass a review gate before remote materialization. This mode has no queue-side isolation, so GeneAgent must enforce boundaries before writing `run.sh`.

Pre-submit gate:
- `GENEAGENT_EXECUTION_MODE=ssh_shell_trusted`
- real execution explicitly enabled
- remote-check passed for SSH, bash, nohup, ps, kill, mkdir, chmod, test, and cat
- remote work root is under the approved user-owned write root
- CPU, memory, walltime, and concurrent-run caps are within configured limits
- generated command contains explicit thread and memory parameters when the tool supports them
- no delete, overwrite, data egress, credential echo, or path escape is present

Allowed automatic actions:
- create run, logs, state, results, and reports directories under the run root
- write LF Bash wrapper with `#!/usr/bin/env bash`
- write state sentinels and read stdout/stderr logs
- retry transient SSH connection failures within policy
- continue only after previous stage output validation passes

Breaker conditions:
- output overwrite without approval
- path outside allowed roots
- unknown tool or unresolved executable path
- resource request over caps
- repeated failure after the retry limit
- PID lost without `done` or `failed` sentinel
- any attempt to store or print password, private key, token, or raw credential

Risk boundary: ordinary-server execution can be automated, but it relies on GeneAgent caps and script guards rather than scheduler enforcement.
