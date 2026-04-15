"""Polling helpers that explain scheduler states without touching a real cluster."""

from __future__ import annotations

from contracts.common import JobState, SchedulerKind
from contracts.execution import JobHandle
from scheduler.models import PollExplanation


class JobPoller:
    """Translate scheduler states into orchestrator actions and human-readable status."""

    def next_action_for_state(self, state: JobState) -> str:
        """Return the recommended orchestrator action for a job state."""

        if state == JobState.DRAFT:
            return "review_plan_before_submission"
        if state in {JobState.QUEUED, JobState.RUNNING}:
            return "sleep_and_poll_again"
        if state == JobState.COMPLETED:
            return "collect_outputs"
        if state == JobState.FAILED:
            return "trigger_failure_recovery"
        return "inspect_scheduler_status"

    def explain(
        self,
        scheduler: SchedulerKind,
        job_id: str,
        state: JobState,
    ) -> PollExplanation:
        """Return a structured interpretation for a scheduler state."""

        recommended_action = self.next_action_for_state(state)
        if state == JobState.DRAFT:
            explanation = (
                "The job is still in planning mode. A script preview and synthetic job handle exist, "
                "but no submission command has been executed."
            )
        elif state == JobState.QUEUED:
            explanation = "The job is waiting in the scheduler queue. Keep polling and inspect queue constraints if it stalls."
        elif state == JobState.RUNNING:
            explanation = "The job is currently running. Continue polling and prepare downstream collection steps."
        elif state == JobState.COMPLETED:
            explanation = "The job reached a terminal success state. Output collection and report generation can start."
        elif state == JobState.FAILED:
            explanation = "The job reached a terminal failure state. Inspect stderr, resource sizing, and scheduler diagnostics."
        else:
            explanation = "The scheduler state cannot be confirmed from the available synthetic information."
        return PollExplanation(
            scheduler=scheduler,
            job_id=job_id,
            state=state,
            recommended_action=recommended_action,
            explanation=explanation,
            poll_command_hint=self._poll_command_hint(scheduler=scheduler, job_id=job_id),
            terminal=state in {JobState.COMPLETED, JobState.FAILED},
        )

    def explain_handle(self, handle: JobHandle) -> PollExplanation:
        """Convenience wrapper for explaining a JobHandle."""

        return self.explain(scheduler=handle.scheduler, job_id=handle.job_id, state=handle.state)

    def _poll_command_hint(self, scheduler: SchedulerKind, job_id: str) -> str:
        """Return a scheduler-specific poll command hint."""

        if scheduler == SchedulerKind.PBS:
            return f"qstat -f {job_id}"
        return f"squeue -j {job_id} -o '%i %t %M %D %R'"
