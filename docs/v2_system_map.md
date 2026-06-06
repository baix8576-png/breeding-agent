# GeneAgent V2 System Map (Single Truth View)

## 1) What Is Already Built

GeneAgent V2 is the current completed stage. It inherits the V1.5 executable bioinformatics loop and adds stable API versioning, console, observability, audit export, production gate, release plan, and final review controls.

V1.5 remains the historical execution-kernel baseline:

- entry: CLI/API
- planning: intent routing + 9-stage bio chain / lightweight non-bio chain
- execution: script generation + scheduler submit/poll adapters (SLURM mainline, PBS compatible)
- closure: artifact index + report integration + audit + memory handoff
- V2 control plane: `/v2/*` API, console, observability, audit export, release governance

For the current workflow-to-file responsibility map, use `docs/current_workflow_file_map.md`.

---

## 2) End-to-End Runtime Flow

### 2.1 Unified Entry

- CLI entry: `src/cli/app.py`
- API entry: `src/api/routes/tasks.py`

Both call the same runtime facade:

- runtime facade: `src/runtime/facade.py`
- dependency wiring: `src/runtime/bootstrap.py`
- unified request envelope mapper (v2 + legacy compatibility): `src/runtime/compat.py` + `src/contracts/envelope.py`
- API version policy + compatibility window: `src/api/routes/versioning.py` + `src/runtime/settings.py`

### 2.2 Planning Core

- orchestrator: `src/orchestration/service.py`
- workflow composition: `src/orchestration/workflow.py`
- intent routing: `src/orchestration/router.py`
- local-first retrieval + gated external fallback: `src/knowledge/retrieval.py`

Bio requests follow 9 stages:

1. `Intake`
2. `Intent + Scope`
3. `Input Validation`
4. `Local-first RAG`
5. `Blueprint Selection`
6. `Resource + Safety Gate`
7. `Execution`
8. `Artifact + Report`
9. `Audit + Memory`

Non-bio requests follow lightweight branch:

- `intake -> local retrieval -> answer blueprint -> optional safety review`
- no cluster execution
- no scheduler script generation

### 2.3 Blueprint and Script Binding

- pipeline catalog and aliases: `src/pipeline/catalog.py`
- pack-first blueprint payloads: `src/pipeline/packs/builtin_blueprints.py`
- workflow compatibility layer: `src/pipeline/workflows.py`
- command planning: `src/pipeline/execution.py`
- input bundle validation: `src/pipeline/validators.py`

V1.5-inherited compatibility blueprints mapped to professional script domains:

- `qc_pipeline` -> `scripts/genotype_processing/run_genotype_qc.sh`
- `pca_pipeline` -> `scripts/population_genetics/run_population_structure_diversity.sh`
- `grm_builder` -> `scripts/quantitative_genetics/run_relationship_matrix.sh`
- `association_mapping_gwas` -> `scripts/association_mapping/run_gwas.sh`
- `genomic_prediction` -> `scripts/quantitative_genetics/run_breeding_value_prediction.sh`

### 2.4 Scheduler and Runtime Closure

- scheduler base/retry model: `src/scheduler/base.py`
- SLURM adapter: `src/scheduler/slurm.py`
- PBS adapter: `src/scheduler/pbs.py`
- poll explanation: `src/scheduler/poller.py`
- runtime state machine (bio 9-stage + non-bio lightweight): `src/runtime/state_machine.py`
- idempotent submit cache (task_id/run_id keyed): `.geneagent/scheduler/submissions/*`

report + closure path:

- report generator script: `scripts/reporting_audit/run_report_generator.sh`
- report index builder: `scripts/reporting_audit/build_result_index.sh`
- runtime integration entry: `src/runtime/facade.py` (`_run_report_generator_artifact_index`)

audit and memory:

- audit store: `src/audit/store.py`
- memory store/handoff: `src/memory/stores.py`

---

## 3) V2 Acceptance Gate (Current Stage)

- build gate: `python -m compileall src tests`
- test gate: `python -m pytest -q`
- entry coverage:
  - CLI: `plan/report/diagnostic/dry-run/submit-preview/submit/poll-explain`
  - API v1 compat: `/tasks/draft-plan /tasks/validate-inputs /tasks/review-action /tasks/report /tasks/diagnostic /tasks/dry-run /tasks/submit-preview /tasks/submit /tasks/poll-explain /tasks/remote-check /tasks/watch-run /tasks/resume-run /tasks/audit-export`
  - API v2 stable: `/v2/tasks/draft-plan /v2/tasks/validate-inputs /v2/tasks/review-action /v2/tasks/report /v2/tasks/diagnostic /v2/tasks/dry-run /v2/tasks/submit-preview /v2/tasks/submit /v2/tasks/poll-explain /v2/tasks/remote-check /v2/tasks/watch-run /v2/tasks/resume-run /v2/tasks/audit-export`
  - API control plane: `/v2/version-policy /v2/console /v2/console/board /v2/console/runs/{run_id}`
- policy gate:
  - non-bio branch must clearly stay outside cluster execution

---

## 4) Known Practical Gap

The core framework exists, but one practical environment gap can still appear:

- Windows sessions that only expose WSL bridge `bash.exe` may skip bash-based integration tests.
- test-side bash resolution has been hardened in `tests/conftest.py` to prefer runnable bash and skip explicitly when unavailable.

This is environment consistency debt, not architecture missing.

---

## 5) Team Execution Rule

For future iteration, all work should be described against this map first:

1. Which stage in the runtime flow is changed?
2. Which module owns it (`orchestration/pipeline/scheduler/runtime/...`)?
3. Which acceptance gate test covers it?

If any change cannot answer these three points, do not merge.

---

## 6) Trusted Remote Execution Addendum

Safe startup mode is `local_preview`; trusted remote automation is enabled only after `remote-check` passes and real execution is explicitly enabled. Two trusted execution backends are supported:

- PC runs the Agent control plane through CLI/API.
- Ordinary Linux servers can run the bioinformatics execution plane through `ssh_shell_trusted` with SSH + Bash/nohup.
- HPC login/compute nodes can run the bioinformatics execution plane through `ssh_slurm_trusted` with SLURM commands.
- Remote submit/poll uses SSH batch mode by default; no passwords or private keys are stored in GeneAgent contracts, settings, docs, or state files.
- Password-account fallback prefers OpenSSH ControlMaster: `remote-session-doctor` checks local readiness, `remote-session-open` lets the operator type the server password once into the SSH prompt, then `remote-check`, submit, watch, and resume reuse the local control socket. `remote-session-smoke --open-session` is the guarded first-validation shortcut for opening/checking the control session and running the fixed smoke flow. If Windows OpenSSH ControlMaster is unavailable, `password_env` mode uses `remote-password-set` to write the password only to local ignored `.env` and then executes through the in-process Paramiko SSH client.
- CLI-only operator-auth commands: `remote-session-doctor`, `remote-session-open`, `remote-session-check`, `remote-session-close`, `remote-session-smoke`, `remote-password-set`, and fixed-command `remote-smoke`. They touch local SSH session state or local ignored `.env` password state and are intentionally not API routes.
- `remote-smoke` submits only the fixed harmless command `hostname && pwd && date && sleep 5` after `remote-check` passes and real execution is enabled.
- `ssh_shell_trusted` stores each remote run under `<remote_work_root>/<task_id>/<run_id>/` with `run.sh`, `logs/*`, and `state/pid|done|failed|exit_code`.
- Ordinary-server write scope is bounded by `GENEAGENT_HPC_WORK_ROOT`; `GENEAGENT_REMOTE_ALLOWED_WRITE_ROOTS` can further require the work root to stay under the operator's user directory, for example `/data2/<user>`.
- For the current 96-core / 1 TB ordinary server, ordinary-server caps default to 32 CPU cores, 256 GB memory, 24 hours walltime, and 2 concurrent runs. Exceeding these caps blocks real submit before any remote files are materialized.
- Generated shell scripts export common thread-limit variables and apply `ulimit` CPU-time/memory guards when `GENEAGENT_REMOTE_SHELL_PROCESS_LIMITS_ENABLED=true`.
- `ssh_slurm_trusted` without `GENEAGENT_SCHEDULER_REAL_EXECUTION_ENABLED=true` is still a preview path and returns a synthetic planning handle instead of calling `sbatch`.
- `manual_sbase` remains the SBASE web-workbench fallback. It generates a copyable submit card, but the operator performs the web submission.
- Local state lives under `.geneagent/runs/<task_id>/<run_id>/state.json` or the configured `GENEAGENT_LOCAL_STATE_ROOT`.
- `watch-run` and `resume-run` update local run state, poll scheduler status, and only continue after a completed stage and output validation.
- Safety policy allows low-risk automation and blocks destructive/result-changing/data-egress actions.
- Xshell/WinSCP/SBASE are manual fallbacks only, not production automation control surfaces.
- Ordinary Linux servers do not provide queue-side resource enforcement; GeneAgent treats CPU/memory/walltime caps as pre-submit gates plus script-level process guards in `ssh_shell_trusted`.

---

## 7) V2 Control Plane Additions (M3, Implemented)

- M3-04 audit bundle one-click export:
  - runtime export entry: `src/runtime/facade.py` (`export_audit_bundle`)
  - audit file query/read board support: `src/audit/store.py`
  - user entrypoints: `POST /tasks/audit-export`, `POST /v2/tasks/audit-export`, `cli audit-export`
- M3-05 API versioning and stability strategy:
  - v1 compatibility preserved with deprecation/sunset headers
  - v2 stable surface provided under `/v2/*`
  - version policy endpoint: `GET /v2/version-policy`
- M3-06 minimal web console:
  - HTML console: `GET /v2/console`
  - task board: `GET /v2/console/board`
  - run status/report snapshot: `GET /v2/console/runs/{run_id}`
  - diagnostic entry in console calls `/v2/tasks/diagnostic`

---

## 8) M3.5 Governance/Observability Expansion

- M3-07 unified explanation layer:
  - output field: `explanation_layer`
  - surfaces in `TaskPlan`, `SubmissionPreview`, `report/diagnostic previews`, and console run snapshots
  - explains: why this blueprint, why this gate decision, why this repair suggestion

- M3-08 observability:
  - metrics: `GET /v2/observability/metrics`
  - dashboard: `GET /v2/observability/dashboard`
  - covers task metrics, scheduler distribution, gate distribution, failure taxonomy, timeline

- M3-09 performance/stability:
  - integration load tests for concurrent dry-run/submit-preview
  - long-loop poll stability regression
  - transient submit failure retry-recovery regression

- M3-10 production gate pipeline:
  - API: `POST /v2/release/production-gate`
  - CLI: `production-gate`
  - checks: contract regression, scheduler simulation, knowledge retrieval regression, audit integrity

- M3-11 release standardization:
  - API: `POST /v2/release/plan`
  - CLI: `release-plan`
  - docs: `docs/release_process_v2.md`

- M3-12 final architect review:
  - API: `GET /v2/release/final-review`
  - CLI: `final-review`
  - docs: `docs/v2_0_final_acceptance_review.md`
