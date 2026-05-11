# GeneAgent V2 Release Process (M3-11)

## 1. Scope

This document standardizes release operations for `V2.0`:

- version tagging
- change summary packaging
- production gate execution
- rollback readiness

## 2. Required Inputs

- `version_tag` (example: `v2.0.0`, `v2.0.0-rc1`)
- `change_summary`
- mapped `stage_id` list for traceability

## 3. Standard Commands

```powershell
python -m cli.app release-plan --version-tag v2.0.0 --change-summary "..." --stage-id stage_05_blueprint_selection --stage-id stage_06_resource_and_safety_gate
python -m cli.app production-gate
python -m cli.app final-review
```

If you want production gate to execute the regression suites directly:

```powershell
python -m cli.app production-gate --execute-tests
```

## 4. Production Gate Matrix

- Contract regression: `tests/unit/contracts/test_execution.py`, `tests/unit/runtime/test_compat_envelope.py`
- Scheduler simulation: `tests/unit/scheduler/test_scheduler_planning.py`, `tests/unit/scheduler/test_atomic_profiles.py`
- Knowledge retrieval regression: `tests/unit/knowledge/test_retrieval.py`
- Audit integrity: execution closure required fields check (`input_summary/planning_summary/submission_command/job_id/log_paths/manual_confirmation_records`)

## 5. Rollback Baseline

Rollback plan must include:

1. Preserve current release artifact and manifest before rollout.
2. Revert to previous stable version tag.
3. Restore previous scheduler/runtime config snapshot.
4. Re-run `compileall + pytest + production gate` to verify rollback.

## 6. Change Summary Template

Use the template returned by `release-plan` command/API as the release notes baseline. It already includes:

- scope
- stage mapping
- compatibility window (`/tasks` deprecation + `/v2/tasks` stable)
- verification checklist
- rollback section
