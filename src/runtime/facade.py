"""High-level runtime facade for CLI and API entry points."""

from __future__ import annotations

from pathlib import PurePosixPath, PureWindowsPath
import shlex
from uuid import uuid4

from audit.store import AuditEvent, FileAuditStore
from contracts.api import RequestIdentity
from contracts.common import GateDecision, JobState, TaskDomain
from contracts.execution import ExecutionArtifacts, JobHandle, RunContext, SubmissionPreview, TaskPlan
from contracts.tasks import UserRequest
from contracts.validation import ValidationReport
from memory.stores import MemoryCoordinator
from pipeline.execution import build_execution_command
from pipeline.workflows import build_blueprint
from pipeline.validators import InputValidator
from safety.gates import SafetyGateResult, SafetyGateService, SafetyReviewContext
from scheduler.base import BaseSchedulerAdapter
from scheduler.models import PollExplanation
from scheduler.poller import JobPoller
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
        memory_coordinator: MemoryCoordinator,
        audit_store: FileAuditStore,
    ) -> None:
        self._settings = settings
        self._orchestrator = orchestrator
        self._scheduler = scheduler
        self._safety_gate = safety_gate
        self._input_validator = input_validator
        self._poller = JobPoller()
        self._memory_coordinator = memory_coordinator
        self._audit_store = audit_store

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

    def validate_inputs(
        self,
        inputs: list[str] | list[dict[str, object]] | dict[str, object],
    ) -> ValidationReport:
        """Validate local input paths before a workflow is drafted or submitted."""

        return self._input_validator.validate(inputs)

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

        return self._build_submission_preview(
            mode="dry-run",
            command=command,
            request_text=request_text,
            identity=identity,
            dry_run_completed=True,
            execute_submit=False,
        )

    def build_submit_preview(
        self,
        *,
        command: list[str] | None = None,
        request_text: str = "Prepare a submit-preview",
        identity: RequestIdentity | None = None,
        dry_run_completed: bool = False,
    ) -> SubmissionPreview:
        """Build a submit-preview payload without issuing a real scheduler command."""

        return self._build_submission_preview(
            mode="submit-preview",
            command=command,
            request_text=request_text,
            identity=identity,
            dry_run_completed=dry_run_completed,
            execute_submit=False,
        )

    def submit(
        self,
        *,
        command: list[str] | None = None,
        request_text: str = "Submit scheduler job",
        identity: RequestIdentity | None = None,
        dry_run_completed: bool = False,
    ) -> SubmissionPreview:
        """Submit a real scheduler job after passing the safety gate."""

        return self._build_submission_preview(
            mode="submit",
            command=command,
            request_text=request_text,
            identity=identity,
            dry_run_completed=dry_run_completed,
            execute_submit=True,
        )

    def explain_poll_state(self, job_id: str) -> PollExplanation:
        """Explain a scheduler job state using real or synthetic poll interpretation."""

        state = self._scheduler.poll(job_id)
        return self._poller.explain(
            scheduler=self._settings.scheduler_type,
            job_id=job_id,
            state=state,
        )

    def _build_submission_preview(
        self,
        *,
        mode: str,
        command: list[str] | None,
        request_text: str,
        identity: RequestIdentity | None,
        dry_run_completed: bool,
        execute_submit: bool,
    ) -> SubmissionPreview:
        """Shared builder for dry-run, submit-preview, and submit modes."""

        run_context = self._resolve_run_context(identity=identity)
        plan = self.draft_plan(text=request_text, identity=identity)
        if plan.domain != TaskDomain.BIOINFORMATICS:
            return self._build_non_bio_submission_preview(
                run_context=run_context,
                mode=mode,
                request_text=request_text,
                plan_summary=plan.summary,
                domain=plan.domain,
            )
        command = command or self._build_default_bio_command(
            plan=plan,
            request_text=request_text,
            working_directory=run_context.working_directory or self._settings.work_root,
        )
        resources = plan.resource_estimate
        if resources is None:
            raise ValueError("Draft plan did not return a resource estimate.")
        submission_plan = self._scheduler.build_submission_plan(
            command=command,
            working_directory=run_context.working_directory or self._settings.work_root,
            resources=resources,
            mode=mode,
            task_id=run_context.task_id,
            run_id=run_context.run_id,
        )
        safety_review = self._build_safety_review_for_scheduler(
            run_context=run_context,
            mode=mode,
            command=command,
            dry_run_completed=dry_run_completed,
            resources=resources,
            target_paths=[
                submission_plan.paths.script_path,
                submission_plan.paths.wrapper_path,
                submission_plan.paths.stdout_path,
                submission_plan.paths.stderr_path,
            ],
        )
        job_handle = submission_plan.job_handle
        if execute_submit:
            if safety_review.decision != GateDecision.PASS:
                raise PermissionError(
                    "Safety gate rejected real submit; run dry-run and complete manual confirmation requirements first."
                )
            job_handle = self._scheduler.submit(
                working_directory=run_context.working_directory or self._settings.work_root,
                resources=resources,
                command=command,
                task_id=run_context.task_id,
                run_id=run_context.run_id,
            )
        artifact_index, report_summary = self._build_bio_artifact_index(
            plan=plan,
            working_directory=submission_plan.paths.working_directory,
            log_paths=[submission_plan.paths.stdout_path, submission_plan.paths.stderr_path],
        )
        audit_record_path = self._append_execution_audit(
            run_context=run_context,
            mode=mode,
            request_text=request_text,
            planning_summary=plan.summary,
            submission_command=shlex.join(submission_plan.submit_command),
            job_id=job_handle.job_id,
            log_paths=[submission_plan.paths.stdout_path, submission_plan.paths.stderr_path],
            manual_confirmation_records=safety_review.human_confirmation_conditions,
            artifact_index=artifact_index,
            report_summary=report_summary,
        )
        run_record = self._memory_coordinator.record_execution_closure(
            task_id=run_context.task_id,
            run_id=run_context.run_id,
            session_id=run_context.session_id,
            domain=plan.domain,
            input_summary=request_text,
            planning_summary=plan.summary,
            submission_command=shlex.join(submission_plan.submit_command),
            job_id=job_handle.job_id,
            log_paths=[submission_plan.paths.stdout_path, submission_plan.paths.stderr_path],
            manual_confirmation_records=safety_review.human_confirmation_conditions,
            artifact_index=artifact_index,
            report_summary=report_summary,
            audit_path=audit_record_path,
        )
        return SubmissionPreview(
            run_context=run_context,
            mode=mode,
            cluster_execution_enabled=True,
            working_directory=submission_plan.paths.working_directory,
            command=command,
            script_preview=submission_plan.script_preview,
            wrapper_preview=submission_plan.wrapper_preview,
            scheduler_script_path=submission_plan.paths.script_path,
            wrapper_path=submission_plan.paths.wrapper_path,
            job_handle=job_handle,
            polling_hint=submission_plan.polling_hint,
            poll_strategy=submission_plan.poll_strategy,
            failure_recovery=submission_plan.failure_recovery,
            gate_status=safety_review.ready_for_gate.value,
            gate_decision=safety_review.decision.value,
            manual_confirmation_items=safety_review.human_confirmation_conditions,
            circuit_break_conditions=safety_review.circuit_break_conditions,
            artifacts=ExecutionArtifacts(
                run_context=run_context,
                script_preview=submission_plan.script_preview,
                stdout_path=submission_plan.paths.stdout_path,
                stderr_path=submission_plan.paths.stderr_path,
                result_paths=artifact_index.get("results", []),
                figure_paths=artifact_index.get("figures", []),
                log_paths=artifact_index.get("logs", []),
                report_paths=artifact_index.get("reports", []),
                artifact_index=artifact_index,
                report_summary=report_summary,
                audit_record_path=audit_record_path,
                memory_handoff_summary=run_record.handoffs[-1].summary if run_record.handoffs else None,
            ),
        )

    def _build_non_bio_submission_preview(
        self,
        *,
        run_context: RunContext,
        mode: str,
        request_text: str | None = None,
        plan_summary: str | None = None,
        domain: TaskDomain = TaskDomain.KNOWLEDGE,
    ) -> SubmissionPreview:
        skip_message = (
            "scheduler_skipped: non-bio request uses lightweight "
            "intake->retrieval->answer blueprint branch"
        )
        artifact_index = {
            "results": [self._join_work_path(run_context.working_directory or self._settings.work_root, "results/answer_blueprint.md")],
            "figures": [],
            "logs": [],
            "reports": [self._join_work_path(run_context.working_directory or self._settings.work_root, "reports/answer_summary.md")],
        }
        report_summary = (
            "Non-bio lightweight branch prepared answer blueprint and summary slots without scheduler execution."
        )
        audit_record_path = self._append_execution_audit(
            run_context=run_context,
            mode=mode,
            request_text=request_text or "non-bio lightweight branch",
            planning_summary=plan_summary or "non-bio lightweight plan",
            submission_command="scheduler_skipped",
            job_id=f"SKIPPED-NONBIO-{run_context.task_id}-{run_context.run_id}",
            log_paths=[],
            manual_confirmation_records=[],
            artifact_index=artifact_index,
            report_summary=report_summary,
        )
        run_record = self._memory_coordinator.record_execution_closure(
            task_id=run_context.task_id,
            run_id=run_context.run_id,
            session_id=run_context.session_id,
            domain=domain,
            input_summary=request_text or "non-bio lightweight branch",
            planning_summary=plan_summary or "non-bio lightweight plan",
            submission_command="scheduler_skipped",
            job_id=f"SKIPPED-NONBIO-{run_context.task_id}-{run_context.run_id}",
            log_paths=[],
            manual_confirmation_records=[],
            artifact_index=artifact_index,
            report_summary=report_summary,
            audit_path=audit_record_path,
        )
        return SubmissionPreview(
            run_context=run_context,
            mode=mode,
            cluster_execution_enabled=False,
            working_directory=run_context.working_directory or self._settings.work_root,
            command=[],
            script_preview=skip_message,
            wrapper_preview=skip_message,
            scheduler_script_path=None,
            wrapper_path=None,
            job_handle=JobHandle(
                run_context=run_context,
                scheduler=self._settings.scheduler_type,
                job_id=f"SKIPPED-NONBIO-{run_context.task_id}-{run_context.run_id}",
                state=JobState.DRAFT,
            ),
            polling_hint="non-bio branch: no scheduler polling required",
            poll_strategy=[
                "skip scheduler poll loop",
                "continue with answer blueprint and local safety review if needed",
            ],
            failure_recovery=[
                "non-bio branch: revise prompt scope and retrieval context instead of requeueing jobs",
            ],
            gate_status="ready",
            gate_decision="pass",
            manual_confirmation_items=[],
            circuit_break_conditions=[],
            artifacts=ExecutionArtifacts(
                run_context=run_context,
                result_paths=artifact_index["results"],
                figure_paths=artifact_index["figures"],
                log_paths=artifact_index["logs"],
                report_paths=artifact_index["reports"],
                artifact_index=artifact_index,
                report_summary=report_summary,
                audit_record_path=audit_record_path,
                memory_handoff_summary=run_record.handoffs[-1].summary if run_record.handoffs else None,
            ),
        )

    def _build_safety_review_for_scheduler(
        self,
        *,
        run_context: RunContext,
        mode: str,
        command: list[str],
        dry_run_completed: bool,
        resources,
        target_paths: list[str],
    ) -> SafetyGateResult:
        action_name = "dry_run_preview"
        if mode == "submit-preview":
            action_name = "submit_preview"
        elif mode == "submit":
            action_name = "submit_execution"
        return self._safety_gate.review(
            context=SafetyReviewContext(
                task_id=run_context.task_id,
                run_id=run_context.run_id,
                action_name=action_name,
                target_paths=target_paths,
                command_preview=" ".join(command),
                scheduler_dry_run_done=dry_run_completed,
                cost_estimated=True,
                rollback_plan_ready=True,
                cpu_cores=resources.cpus,
                memory_gb=resources.memory_gb,
                walltime_hours=self._walltime_to_hours(resources.walltime),
                job_count=1,
            )
        )

    def _walltime_to_hours(self, walltime: str) -> int:
        """Convert HH:MM:SS or HH:MM walltime string into rounded-up hours."""

        parts = walltime.split(":")
        if len(parts) == 3:
            hours, minutes, _seconds = parts
        elif len(parts) == 2:
            hours, minutes = parts
        else:
            return 0
        try:
            parsed_hours = int(hours)
            parsed_minutes = int(minutes)
        except ValueError:
            return 0
        return parsed_hours + (1 if parsed_minutes > 0 else 0)

    def _build_bio_artifact_index(
        self,
        *,
        plan: TaskPlan,
        working_directory: str,
        log_paths: list[str],
    ) -> tuple[dict[str, list[str]], str]:
        pipeline_name = plan.pipeline_spec.name if plan.pipeline_spec is not None else "qc_pipeline"
        blueprint = build_blueprint(pipeline_name)
        results: list[str] = []
        figures: list[str] = []
        reports: list[str] = []
        for output in blueprint.outputs:
            relative_path = str(output.get("relative_path", "")).strip()
            if not relative_path:
                continue
            resolved_path = self._join_work_path(working_directory, relative_path)
            lowered_path = relative_path.lower()
            lowered_format = str(output.get("format", "")).lower()
            if "figure" in lowered_path or lowered_format in {"png", "svg", "jpg", "jpeg", "pdf"}:
                figures.append(resolved_path)
            elif lowered_path.startswith("reports/") or "report" in lowered_path or lowered_format == "markdown":
                reports.append(resolved_path)
            else:
                results.append(resolved_path)

        artifact_index = {
            "results": results,
            "figures": figures,
            "logs": [path for path in log_paths if path],
            "reports": reports,
        }
        report_summary = (
            f"{pipeline_name} {len(results)} results, {len(figures)} figures, "
            f"{len(artifact_index['logs'])} logs, {len(reports)} reports indexed."
        )
        return artifact_index, report_summary

    def _append_execution_audit(
        self,
        *,
        run_context: RunContext,
        mode: str,
        request_text: str,
        planning_summary: str,
        submission_command: str,
        job_id: str,
        log_paths: list[str],
        manual_confirmation_records: list[str],
        artifact_index: dict[str, list[str]],
        report_summary: str,
    ) -> str | None:
        event = AuditEvent(
            task_id=run_context.task_id,
            run_id=run_context.run_id,
            event_type="execution_closure",
            summary=f"{mode} execution closure recorded for task/run context.",
            metadata={
                "input_summary": request_text[:200],
                "planning_summary": planning_summary,
                "submission_command": submission_command,
                "job_id": job_id,
                "log_paths": [path for path in log_paths if path],
                "manual_confirmation_records": manual_confirmation_records,
                "artifact_index": artifact_index,
                "report_summary": report_summary,
            },
        )
        return self._audit_store.append(
            event,
            working_directory=run_context.working_directory or self._settings.work_root,
        )

    def _join_work_path(self, base_directory: str, relative_path: str) -> str:
        path_cls = self._path_class(base_directory)
        normalized = relative_path.replace("\\", "/").strip("/")
        parts = [part for part in normalized.split("/") if part]
        resolved = path_cls(base_directory)
        for part in parts:
            resolved = resolved / part
        return str(resolved)

    def _build_default_bio_command(
        self,
        *,
        plan: TaskPlan,
        request_text: str,
        working_directory: str,
    ) -> list[str]:
        pipeline_spec = plan.pipeline_spec
        if pipeline_spec is None:
            raise ValueError("Bioinformatics draft plan is missing pipeline_spec.")
        return build_execution_command(
            pipeline_spec,
            request_text=request_text,
            working_directory=working_directory,
        )

    def _path_class(self, raw_path: str):
        if raw_path.startswith("/") or ("/" in raw_path and "\\" not in raw_path):
            return PurePosixPath
        return PureWindowsPath

    def _resolve_run_context(self, identity: RequestIdentity | None) -> RunContext:
        """Build a stable run context, generating identifiers when omitted by the caller."""

        identity = identity or RequestIdentity()
        return RunContext(
            task_id=identity.task_id or f"task-{uuid4().hex[:12]}",
            run_id=identity.run_id or f"run-{uuid4().hex[:12]}",
            session_id=identity.session_id,
            working_directory=identity.working_directory or self._settings.work_root,
        )
