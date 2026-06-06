"""Trusted run controller for watch, classify, and resume operations."""

from __future__ import annotations

from contracts.common import ExecutionMode, JobState
from contracts.remote_execution import RunState
from runtime.run_state import RunStateStore
from safety.automation_policy import AutomationActionRequest, TrustedAutomationPolicy


class TrustedRunController:
    """Coordinate persisted trusted runs without bypassing safety policy."""

    def __init__(
        self,
        *,
        state_store: RunStateStore,
        policy: TrustedAutomationPolicy | None = None,
    ) -> None:
        self._state_store = state_store
        self._policy = policy or TrustedAutomationPolicy()

    def watch_run(self, *, task_id: str, run_id: str, scheduler) -> RunState:
        state = self._require_state(task_id=task_id, run_id=run_id)
        if not state.job_id:
            updated = state.with_stage(
                stage_id=state.current_stage,
                status="blocked_missing_job_id",
                message="Cannot watch a run without a scheduler job id.",
                next_action="manual review required: missing job id",
                auto_continue_ready=False,
            )
            self._state_store.save(updated)
            return updated

        poll_run = getattr(scheduler, "poll_run", None)
        if callable(poll_run):
            job_state = poll_run(state)
        else:
            job_state = scheduler.poll(state.job_id)
        if job_state == JobState.COMPLETED:
            updated = state.with_stage(
                stage_id="stage_08_artifact_and_report",
                status="completed",
                message="Scheduler job completed; artifact/report validation can proceed.",
                run_status=JobState.COMPLETED,
                current_stage="stage_08_artifact_and_report",
                next_action="validate artifacts then continue",
                auto_continue_ready=bool(state.auto_continue),
            )
        elif job_state == JobState.FAILED:
            updated = self._handle_failed_job(state=state, scheduler=scheduler)
        elif job_state == JobState.RUNNING:
            updated = state.with_stage(
                stage_id="stage_07_execution",
                status="running",
                message="Scheduler job is still running.",
                run_status=JobState.RUNNING,
                next_action="watch scheduler state",
                auto_continue_ready=False,
            )
        elif job_state == JobState.QUEUED:
            updated = state.with_stage(
                stage_id="stage_07_execution",
                status="queued",
                message="Scheduler job is queued.",
                run_status=JobState.QUEUED,
                next_action="watch scheduler state",
                auto_continue_ready=False,
            )
        elif job_state == JobState.UNKNOWN and state.execution_mode == ExecutionMode.SSH_SHELL_TRUSTED:
            updated = state.with_stage(
                stage_id="stage_07_execution",
                status="unknown_shell_pid_lost",
                message="Remote shell PID is not running and no done/failed sentinel resolved the run state.",
                run_status=JobState.UNKNOWN,
                next_action="manual review required: inspect remote shell pid, state files, stdout, and stderr",
                auto_continue_ready=False,
            )
        else:
            updated = state.with_stage(
                stage_id="stage_07_execution",
                status="unknown",
                message="Scheduler returned unknown state; keep run under observation.",
                run_status=JobState.UNKNOWN,
                next_action="inspect scheduler logs",
                auto_continue_ready=False,
            )
        self._state_store.save(updated)
        return updated

    def resume_run(self, *, task_id: str, run_id: str, scheduler, auto_continue: bool | None = None) -> RunState:
        state = self._require_state(task_id=task_id, run_id=run_id)
        if auto_continue is not None:
            state = state.model_copy(update={"auto_continue": auto_continue})
            self._state_store.save(state)
        return self.watch_run(task_id=task_id, run_id=run_id, scheduler=scheduler)

    def _require_state(self, *, task_id: str, run_id: str) -> RunState:
        state = self._state_store.load(task_id=task_id, run_id=run_id)
        if state is None:
            raise FileNotFoundError(f"Run state not found for task_id={task_id}, run_id={run_id}.")
        return state

    def _handle_failed_job(self, *, state: RunState, scheduler) -> RunState:
        failure_count = state.repeated_failures + 1
        decision = self._policy.review(
            AutomationActionRequest(
                action="retry_transient_scheduler_failure",
                repeated_failures=failure_count,
            )
        )
        if not decision.allowed:
            return state.with_stage(
                stage_id="stage_07_execution",
                status="failed",
                message=f"Scheduler job failed; automation retry blocked by policy: {decision.reason}.",
                run_status=JobState.FAILED,
                current_stage="stage_07_execution",
                next_action="manual review required before overwrite, sample filtering, or requeue",
                auto_continue_ready=False,
            ).model_copy(update={"repeated_failures": failure_count})

        retry_job = getattr(scheduler, "retry_job", None)
        if not callable(retry_job):
            return state.with_stage(
                stage_id="stage_07_execution",
                status="failed",
                message=(
                    "Scheduler job failed; policy allowed low-risk retry, "
                    "but this scheduler does not expose a retry hook."
                ),
                run_status=JobState.FAILED,
                current_stage="stage_07_execution",
                next_action="manual review required before overwrite, sample filtering, or requeue",
                auto_continue_ready=False,
            ).model_copy(update={"repeated_failures": failure_count})

        try:
            new_job_id = retry_job(state)
        except Exception as error:
            return state.with_stage(
                stage_id="stage_07_execution",
                status="retry_failed",
                message=f"Low-risk retry was allowed but scheduler retry failed: {error}",
                run_status=JobState.FAILED,
                current_stage="stage_07_execution",
                next_action="manual review required: retry hook failed",
                auto_continue_ready=False,
            ).model_copy(update={"repeated_failures": failure_count})

        return state.with_stage(
            stage_id="stage_07_execution",
            status="auto_retry_submitted",
            message=f"Low-risk scheduler retry submitted after policy decision: {decision.reason}.",
            job_id=new_job_id,
            run_status=JobState.QUEUED,
            current_stage="stage_07_execution",
            next_action="retry submitted; watch scheduler state",
            auto_continue_ready=False,
        ).model_copy(
            update={
                "auto_repair_attempts": state.auto_repair_attempts + 1,
                "repeated_failures": failure_count,
            }
        )
