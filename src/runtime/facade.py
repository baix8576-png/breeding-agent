"""High-level runtime facade for CLI and API entry points."""

from __future__ import annotations

from uuid import uuid4

from contracts.api import RequestIdentity
from contracts.execution import ExecutionArtifacts, RunContext, SubmissionPreview, TaskPlan
from contracts.tasks import UserRequest
from contracts.validation import ValidationReport
from pipeline.validators import InputValidator
from safety.gates import SafetyGateResult, SafetyGateService, SafetyReviewContext
from scheduler.base import BaseSchedulerAdapter
from runtime.settings import Settings


class ApplicationFacade:
    """Expose a stable application-facing API over lower-level services."""

    def __init__(
        self,
        settings: Settings,
        orchestrator,
        scheduler: BaseSchedulerAdapter,
        safety_gate: SafetyGateService,
        input_validator: InputValidator,
    ) -> None:
        self._settings = settings
        self._orchestrator = orchestrator
        self._scheduler = scheduler
        self._safety_gate = safety_gate
        self._input_validator = input_validator

    def draft_plan(
        self,
        text: str,
        *,
        identity: RequestIdentity | None = None,
        requested_outputs: list[str] | None = None,
    ) -> TaskPlan:
        """Build a draft plan from natural-language input."""

        run_context = self._resolve_run_context(identity=identity)
        return self._orchestrator.draft_plan(
            UserRequest(
                text=text,
                working_directory=run_context.working_directory,
                requested_outputs=requested_outputs or [],
            ),
            run_context=run_context,
        )

    def validate_inputs(self, paths: list[str]) -> ValidationReport:
        """Validate local input paths before a workflow is drafted or submitted."""

        return self._input_validator.validate(paths)

    def review_action(
        self,
        action_name: str,
        *,
        identity: RequestIdentity | None = None,
        reason: str | None = None,
        target_paths: list[str] | None = None,
    ) -> SafetyGateResult:
        """Run a named action through the safety gate."""

        run_context = self._resolve_run_context(identity=identity)
        return self._safety_gate.review(
            context=SafetyReviewContext(
                task_id=run_context.task_id,
                run_id=run_context.run_id,
                action_name=action_name,
                target_paths=target_paths or [],
                command_preview=reason,
            )
        )

    def build_dry_run_submission(
        self,
        *,
        command: list[str] | None = None,
        request_text: str = "Prepare a dry-run submission",
        identity: RequestIdentity | None = None,
    ) -> SubmissionPreview:
        """Generate a scheduler script preview and a synthetic dry-run handle."""

        run_context = self._resolve_run_context(identity=identity)
        command = command or ["echo", "geneagent-dry-run"]
        plan = self.draft_plan(text=request_text, identity=identity)
        resources = plan.resource_estimate
        if resources is None:
            raise ValueError("Draft plan did not return a resource estimate.")
        submission_plan = self._scheduler.build_submission_plan(
            command=command,
            working_directory=run_context.working_directory or self._settings.work_root,
            resources=resources,
            task_id=run_context.task_id,
            run_id=run_context.run_id,
        )
        return SubmissionPreview(
            run_context=run_context,
            working_directory=submission_plan.paths.working_directory,
            command=command,
            script_preview=submission_plan.script_preview,
            job_handle=submission_plan.job_handle,
            artifacts=ExecutionArtifacts(
                run_context=run_context,
                script_preview=submission_plan.script_preview,
                stdout_path=submission_plan.paths.stdout_path,
                stderr_path=submission_plan.paths.stderr_path,
            ),
        )

    def _resolve_run_context(self, identity: RequestIdentity | None) -> RunContext:
        """Build a stable run context, generating identifiers when omitted by the caller."""

        identity = identity or RequestIdentity()
        return RunContext(
            task_id=identity.task_id or f"task-{uuid4().hex[:12]}",
            run_id=identity.run_id or f"run-{uuid4().hex[:12]}",
            session_id=identity.session_id,
            working_directory=identity.working_directory or self._settings.work_root,
        )
