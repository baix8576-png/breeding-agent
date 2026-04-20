# scheduler error patterns (diagnostics_v1)

## ENTRY: slurm.account_partition_mismatch

- pattern_id: `slurm.account_partition_mismatch`
- component: `scheduler.slurm`
- stage: `submit`
- severity: `high`
- trigger_keywords:
  - `Invalid account`
  - `Invalid account or account/partition combination specified`
  - `sbatch: error: Batch job submission failed`
- trigger_regex:
  - `(?i)invalid account`
  - `(?i)account/partition combination`
- likely_root_causes:
  1. `--account` value is not authorized for the current user.
  2. Account exists but is not bound to the target partition.
  3. Wrapper omitted required account parameter from cluster policy.
- executable_fix_steps:
  1. List allowed associations and verify account/partition mapping.
  2. Switch to an authorized account and partition pair.
  3. Re-submit with explicit `-A` and `-p`.
- command_examples:
```bash
sacctmgr show assoc where user=$USER format=Account,Partition%30
sinfo -s
sbatch -A <valid_account> -p <valid_partition> job.slurm
```
- risk_notice:
  - Wrong account can violate charging policy and cause cost attribution errors.
  - Repeated blind retries may trigger submission throttling.
- verification:
  1. `sbatch` returns a numeric `Submitted batch job <job_id>`.
  2. `squeue -j <job_id>` shows `PD` or `R` instead of immediate rejection.

## ENTRY: slurm.qos_or_resource_limit

- pattern_id: `slurm.qos_or_resource_limit`
- component: `scheduler.slurm`
- stage: `submit`
- severity: `high`
- trigger_keywords:
  - `QOSMaxCpuPerUserLimit`
  - `Job violates accounting/QOS policy`
  - `AssocGrpCpuLimit`
  - `Requested time limit is invalid`
- trigger_regex:
  - `(?i)qos.*limit`
  - `(?i)violates accounting`
  - `(?i)requested time limit is invalid`
- likely_root_causes:
  1. Requested `--cpus-per-task`, `--mem`, or `--time` exceeds partition/QOS limit.
  2. User or account has reached concurrent CPU or job quota.
  3. Default wrapper resources are too large for small queue profiles.
- executable_fix_steps:
  1. Inspect queue and QOS constraints.
  2. Reduce resource request and runtime.
  3. Re-submit with conservative resources, then scale up after success.
- command_examples:
```bash
scontrol show partition <partition_name>
sacctmgr show qos format=Name,MaxWall,MaxTRESPU%40,GrpTRESMins%30
sbatch -p <partition_name> --cpus-per-task=4 --mem=16G --time=04:00:00 job.slurm
```
- risk_notice:
  - Aggressive downscaling may lead to OOM or timeout during real execution.
  - Request inflation to bypass limit is usually audited and may be blocked.
- verification:
  1. Submit succeeds and job enters queue.
  2. `sacct -j <job_id> --format=JobID,State,Elapsed,MaxRSS` shows resource usage below limits.

## ENTRY: slurm.node_constraint_unavailable

- pattern_id: `slurm.node_constraint_unavailable`
- component: `scheduler.slurm`
- stage: `submit`
- severity: `medium`
- trigger_keywords:
  - `Requested node configuration is not available`
  - `Invalid generic resource (gres) specification`
  - `Batch job submission failed: Requested`
- trigger_regex:
  - `(?i)node configuration is not available`
  - `(?i)invalid generic resource`
- likely_root_causes:
  1. GPU type/count requested by `--gres` does not exist in target partition.
  2. Constraint flags (`--constraint`) conflict with available nodes.
  3. Queue supports only shared nodes but script forces exclusive settings.
- executable_fix_steps:
  1. Query real node features and GRES inventory.
  2. Relax constraint or move to the correct partition.
  3. Re-submit with minimal valid resource shape.
- command_examples:
```bash
sinfo -o "%P %a %l %D %G %f"
scontrol show nodes | grep -E "NodeName=|Gres=|Partitions="
sbatch -p <gpu_partition> --gres=gpu:1 job.slurm
```
- risk_notice:
  - Wrong GPU/feature assumptions can create long pending queues without progress.
  - Over-relaxing constraints may run on unsupported hardware and affect reproducibility.
- verification:
  1. Job is accepted with no GRES/constraint errors.
  2. `scontrol show job <job_id>` confirms expected partition and allocated resources.

## ENTRY: pbs.unknown_queue

- pattern_id: `pbs.unknown_queue`
- component: `scheduler.pbs`
- stage: `submit`
- severity: `high`
- trigger_keywords:
  - `qsub: Unknown queue`
  - `qsub: destination not found`
  - `qsub: cannot locate queue`
- trigger_regex:
  - `(?i)qsub:.*unknown queue`
  - `(?i)destination not found`
- likely_root_causes:
  1. Queue name in script/CLI does not exist on target cluster.
  2. Queue exists but is disabled or not visible to user group.
  3. Environment switched cluster endpoint without updating defaults.
- executable_fix_steps:
  1. List queues and states.
  2. Select an enabled queue authorized for the user.
  3. Re-submit with explicit `-q`.
- command_examples:
```bash
qstat -Q
qstat -Qf <queue_name>
qsub -q <valid_queue> job.pbs
```
- risk_notice:
  - Submitting to an incorrect queue may violate project scheduling policy.
  - Hidden/admin queues may require explicit approval before use.
- verification:
  1. `qsub` returns a job id (for example `12345.server`).
  2. `qstat -f <job_id>` shows `queue = <valid_queue>`.

## ENTRY: pbs.resource_limit_exceeded

- pattern_id: `pbs.resource_limit_exceeded`
- component: `scheduler.pbs`
- stage: `submit`
- severity: `high`
- trigger_keywords:
  - `Job exceeds queue resource limits`
  - `qsub: Resource limit exceeded`
  - `qsub: Illegal attribute or resource value`
- trigger_regex:
  - `(?i)exceeds queue resource limits`
  - `(?i)illegal.*resource value`
- likely_root_causes:
  1. `-l select`, `ncpus`, `mem`, or `walltime` exceeds queue max.
  2. Resource format mismatched scheduler policy (`nodes:ppn` vs `select` syntax).
  3. Script template carries SLURM-style resources into PBS path.
- executable_fix_steps:
  1. Inspect queue defaults and max resource caps.
  2. Normalize resource format to cluster-specific PBS syntax.
  3. Re-submit with reduced and valid values.
- command_examples:
```bash
qstat -Qf <queue_name> | grep -E "resources_default|resources_max"
qsub -q <queue_name> -l select=1:ncpus=8:mem=32gb -l walltime=08:00:00 job.pbs
```
- risk_notice:
  - Unit mismatch (`gb` vs `mb`) can silently request wrong memory size.
  - Under-requesting walltime may cause repeated job eviction or termination.
- verification:
  1. `qsub` succeeds without resource validation errors.
  2. `qstat -f <job_id>` reports requested resources exactly as expected.

## ENTRY: pbs.hold_or_permission_denied

- pattern_id: `pbs.hold_or_permission_denied`
- component: `scheduler.pbs`
- stage: `submit,poll`
- severity: `medium`
- trigger_keywords:
  - `qsub: Unauthorized Request`
  - `qsub: Permission denied`
  - `job_state = H`
  - `Hold_Types`
- trigger_regex:
  - `(?i)unauthorized request`
  - `(?i)permission denied`
  - `(?i)job_state\\s*=\\s*H`
- likely_root_causes:
  1. User/group lacks permission for queue or project resource.
  2. Job was placed on hold by policy or dependency failure.
  3. Account string or project code missing from submit arguments.
- executable_fix_steps:
  1. Inspect hold reason and authorization context.
  2. Correct account/project/queue parameters.
  3. Release hold only after root cause is resolved.
- command_examples:
```bash
qstat -f <job_id> | grep -E "job_state|Hold_Types|comment|Account_Name|project"
qrls <job_id>
qsub -A <project_code> -q <valid_queue> job.pbs
```
- risk_notice:
  - Releasing holds without fixing policy violations causes noisy retry loops.
  - Unauthorized queue usage may trigger account-level scheduler restrictions.
- verification:
  1. Held jobs transition from `H` to `Q/R` after correction.
  2. Polling no longer returns authorization/permission errors for new submissions.
