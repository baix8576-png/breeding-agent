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

## Ordinary server trusted-shell caps

```yaml
knowledge_item.v2:
  doc_id: playbook_ordinary_server_trusted_shell_caps
  version: v2
  species: multi_species
  blueprint_scope: reporting_audit
  evidence_level: sop
  source: parameter_playbook
  updated_at: 2026-06-11T00:00:00+08:00
  owner: hpc_scheduler
```

For `ssh_shell_trusted`, GeneAgent controls a normal Linux server rather than a queue-isolated HPC scheduler. Resource values are therefore pre-submit policy gates plus process-level guards, not hard cluster reservations.

| Server profile | CPU/thread cap | Memory cap | Walltime cap | Concurrent run cap | Required wrapper behavior | Breaker |
|---|---|---|---|---|---|---|
| ordinary 96-core / 1 TB server default | `32` threads | `256` GB | `24:00:00` | `2` runs | export `OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS`, `MKL_NUM_THREADS`, `NUMEXPR_NUM_THREADS`; write logs/state under work root | plan exceeds cap, unknown tool, path outside allowed root, overwrite risk, data exfiltration |
| small dry-run smoke test | `1-2` threads | `1-8` GB | `00:10:00-01:00:00` | `1` run | run `hostname && date` or tool `--help`; no raw data access | any raw data path or credential in command |
| manual SBASE fallback | user-entered resources | user-entered resources | user-entered walltime | web workbench policy | generate copyable submit card only | Agent attempts to click/submit through web UI automatically |

SLURM/PBS/SGE presets remain backend-specific. Queue, account, QOS, and partition names must come from local configuration or operator input and must not be hard-coded into the knowledge base.
