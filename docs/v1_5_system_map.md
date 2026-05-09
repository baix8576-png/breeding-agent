# GeneAgent V1.5 System Map (Single Truth View)

## 1) What Is Already Built

GeneAgent V1.5 is not an empty skeleton. It already has an executable closed loop:

- entry: CLI/API
- planning: intent routing + 9-stage bio chain / lightweight non-bio chain
- execution: script generation + scheduler submit/poll adapters (SLURM mainline, PBS compatible)
- closure: artifact index + report integration + audit + memory handoff

---

## 2) End-to-End Runtime Flow

### 2.1 Unified Entry

- CLI entry: `src/cli/app.py`
- API entry: `src/api/routes/tasks.py`

Both call the same runtime facade:

- runtime facade: `src/runtime/facade.py`
- dependency wiring: `src/runtime/bootstrap.py`
- unified request envelope mapper (v2 + legacy compatibility): `src/runtime/compat.py` + `src/contracts/envelope.py`

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

- pipeline blueprint definitions: `src/pipeline/workflows.py`
- command planning: `src/pipeline/execution.py`
- input bundle validation: `src/pipeline/validators.py`

V1.5 fixed bio blueprints:

- `qc_pipeline` -> `scripts/qc_pipeline/run_qc_pipeline.sh`
- `pca_pipeline` -> `scripts/pca_pipeline/run_pca_pipeline.sh`
- `grm_builder` -> `scripts/grm_builder/run_grm_builder.sh`
- `genomic_prediction` -> `scripts/genomic_prediction/run_genomic_prediction.sh`

### 2.4 Scheduler and Runtime Closure

- scheduler base/retry model: `src/scheduler/base.py`
- SLURM adapter: `src/scheduler/slurm.py`
- PBS adapter: `src/scheduler/pbs.py`
- poll explanation: `src/scheduler/poller.py`
- runtime state machine (bio 9-stage + non-bio lightweight): `src/runtime/state_machine.py`
- idempotent submit cache (task_id/run_id keyed): `.geneagent/scheduler/submissions/*`

report + closure path:

- report generator script: `scripts/report_generator/run_report_generator.sh`
- report index builder: `scripts/report_generator/build_result_index.sh`
- runtime integration entry: `src/runtime/facade.py` (`_run_report_generator_artifact_index`)

audit and memory:

- audit store: `src/audit/store.py`
- memory store/handoff: `src/memory/stores.py`

---

## 3) V1.5 Acceptance Gate (Current Baseline)

- build gate: `python -m compileall src tests`
- test gate: `python -m pytest -q`
- entry coverage:
  - CLI: `plan/report/diagnostic/dry-run/submit-preview/submit/poll-explain`
  - API: `/tasks/draft-plan /report /diagnostic /dry-run /submit-preview /submit /poll-explain`
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
