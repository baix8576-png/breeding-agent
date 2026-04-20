"""High-level runtime facade for CLI and API entry points."""

from __future__ import annotations

import json
from pathlib import Path, PurePosixPath, PureWindowsPath
import shlex
import shutil
import subprocess
from uuid import uuid4

from pydantic import BaseModel, Field

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


class ReportPreview(BaseModel):
    """Report preview payload for CLI/API report endpoints."""

    run_context: RunContext
    domain: str
    workflow_name: str
    selected_blueprint: str
    report_sections: list[str] = Field(default_factory=list)
    expected_artifacts: dict[str, list[str]] = Field(default_factory=dict)
    cluster_execution_enabled: bool = False
    non_bio_cluster_policy: str | None = None


class DiagnosticPreview(BaseModel):
    """Diagnostic preview payload for CLI/API diagnostic endpoints."""

    run_context: RunContext
    domain: str
    retrieval_mode: str
    coverage: str
    fallback_requested: bool = False
    fallback_gate_decision: str = "not_requested"
    fallback_gate_reason: str = "coverage_high"
    fallback_used: bool = False
    fallback: dict[str, object] = Field(default_factory=dict)
    diagnostic_suggestions: list[dict[str, object]] = Field(default_factory=list)
    sources: list[dict[str, object]] = Field(default_factory=list)
    cluster_execution_enabled: bool = False
    non_bio_cluster_policy: str | None = None


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

    def build_report_preview(
        self,
        *,
        request_text: str = "Prepare report preview",
        identity: RequestIdentity | None = None,
        requested_outputs: list[str] | None = None,
    ) -> ReportPreview:
        """Build report-facing preview fields without scheduler submission."""

        run_context = self._resolve_run_context(identity=identity)
        plan = self._orchestrator.draft_plan(
            UserRequest(
                text=request_text,
                working_directory=run_context.working_directory,
                requested_outputs=requested_outputs or [],
            ),
            run_context=run_context,
        )
        selected_blueprint = (
            plan.pipeline_spec.name
            if plan.pipeline_spec is not None
            else f"{plan.domain.value}_lightweight"
        )
        working_directory = run_context.working_directory or self._settings.work_root
        non_bio_cluster_policy = (
            "non-bio lightweight branch does not enter cluster execution; "
            "use intake->local retrieval->answer blueprint only."
            if plan.domain != TaskDomain.BIOINFORMATICS
            else None
        )
        return ReportPreview(
            run_context=run_context,
            domain=plan.domain.value,
            workflow_name=plan.workflow_name,
            selected_blueprint=selected_blueprint,
            report_sections=self._resolve_report_sections_for_preview(plan=plan),
            expected_artifacts=self._resolve_expected_artifacts_for_preview(
                plan=plan,
                working_directory=working_directory,
            ),
            cluster_execution_enabled=False,
            non_bio_cluster_policy=non_bio_cluster_policy,
        )

    def build_diagnostic_preview(
        self,
        *,
        request_text: str = "Inspect retrieval diagnostics",
        identity: RequestIdentity | None = None,
    ) -> DiagnosticPreview:
        """Build retrieval diagnostics preview without scheduler submission."""

        run_context = self._resolve_run_context(identity=identity)
        diagnostics = self._orchestrator.inspect_retrieval_diagnostics(
            UserRequest(
                text=request_text,
                working_directory=run_context.working_directory,
            ),
            run_context=run_context,
        )
        domain = str(diagnostics.get("domain", TaskDomain.KNOWLEDGE.value))
        fallback_requested = bool(diagnostics.get("fallback_requested", False))
        fallback_gate_decision = str(diagnostics.get("fallback_gate_decision", "not_requested"))
        fallback_gate_reason = str(diagnostics.get("fallback_gate_reason", "coverage_high"))
        fallback_used = bool(diagnostics.get("fallback_used", False))
        raw_run_context = diagnostics.get("run_context")
        if isinstance(raw_run_context, RunContext):
            diagnostic_run_context = raw_run_context
        elif isinstance(raw_run_context, dict):
            diagnostic_run_context = RunContext.model_validate(raw_run_context)
        else:
            diagnostic_run_context = run_context
        non_bio_cluster_policy = (
            "non-bio request is restricted to lightweight branch and does not enter cluster execution."
            if domain != TaskDomain.BIOINFORMATICS.value
            else None
        )
        return DiagnosticPreview(
            run_context=diagnostic_run_context,
            domain=domain,
            retrieval_mode=str(diagnostics.get("retrieval_mode", "local_only")),
            coverage=str(diagnostics.get("coverage", "low")),
            fallback_requested=fallback_requested,
            fallback_gate_decision=fallback_gate_decision,
            fallback_gate_reason=fallback_gate_reason,
            fallback_used=fallback_used,
            fallback={
                "requested": fallback_requested,
                "gate_decision": fallback_gate_decision,
                "gate_reason": fallback_gate_reason,
                "used": fallback_used,
            },
            diagnostic_suggestions=list(diagnostics.get("diagnostic_suggestions", [])),
            sources=list(diagnostics.get("sources", [])),
            cluster_execution_enabled=False,
            non_bio_cluster_policy=non_bio_cluster_policy,
        )

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
        submit_command_text = shlex.join(submission_plan.submit_command)
        predicted_audit_record_path = self._predict_audit_record_path(
            run_context=run_context,
            working_directory=submission_plan.paths.working_directory,
        )
        artifact_index, report_summary, report_generator_status, report_generator_message = self._build_bio_artifact_index(
            plan=plan,
            working_directory=submission_plan.paths.working_directory,
            log_paths=[submission_plan.paths.stdout_path, submission_plan.paths.stderr_path],
            run_context=run_context,
            job_handle=job_handle,
            submission_command=submit_command_text,
            scheduler_script_path=submission_plan.paths.script_path,
            wrapper_path=submission_plan.paths.wrapper_path,
            audit_path=predicted_audit_record_path,
        )
        audit_record_path = self._append_execution_audit(
            run_context=run_context,
            mode=mode,
            request_text=request_text,
            planning_summary=plan.summary,
            submission_command=submit_command_text,
            job_id=job_handle.job_id,
            log_paths=[submission_plan.paths.stdout_path, submission_plan.paths.stderr_path],
            manual_confirmation_records=safety_review.human_confirmation_conditions,
            artifact_index=artifact_index,
            report_summary=report_summary,
        )
        if audit_record_path:
            artifact_index["results"] = self._stable_unique(
                [*artifact_index.get("results", []), audit_record_path]
            )
        run_record = self._memory_coordinator.record_execution_closure(
            task_id=run_context.task_id,
            run_id=run_context.run_id,
            session_id=run_context.session_id,
            domain=plan.domain,
            input_summary=request_text,
            planning_summary=plan.summary,
            submission_command=submit_command_text,
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
                report_generator_status=report_generator_status,
                report_generator_message=report_generator_message,
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
                report_generator_status="skipped_non_bio",
                report_generator_message="non-bio lightweight branch does not invoke report_generator",
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
        run_context: RunContext,
        job_handle: JobHandle,
        submission_command: str,
        scheduler_script_path: str,
        wrapper_path: str,
        audit_path: str | None,
    ) -> tuple[dict[str, list[str]], str, str, str | None]:
        pipeline_name = plan.pipeline_spec.name if plan.pipeline_spec is not None else "qc_pipeline"
        fallback_index, fallback_summary = self._build_blueprint_artifact_index(
            plan=plan,
            working_directory=working_directory,
            log_paths=log_paths,
        )
        report_status, report_message, report_payload = self._run_report_generator_artifact_index(
            pipeline_name=pipeline_name,
            working_directory=working_directory,
            run_context=run_context,
            job_handle=job_handle,
            submission_command=submission_command,
            scheduler_script_path=scheduler_script_path,
            wrapper_path=wrapper_path,
            log_paths=log_paths,
            audit_path=audit_path,
        )
        if report_payload is None:
            fallback_report_summary = self._append_report_generator_status(
                summary=fallback_summary,
                status=report_status,
                message=report_message,
            )
            return fallback_index, fallback_report_summary, report_status, report_message
        report_index = self._classify_report_generator_artifacts(
            working_directory=working_directory,
            payload=report_payload,
        )

        artifact_index = {
            "results": self._stable_unique([*fallback_index["results"], *report_index["results"]]),
            "figures": self._stable_unique([*fallback_index["figures"], *report_index["figures"]]),
            "logs": [path for path in log_paths if path],
            "reports": self._stable_unique([*fallback_index["reports"], *report_index["reports"]]),
        }
        report_summary = self._build_report_generator_summary(
            payload=report_payload,
            pipeline_name=pipeline_name,
            artifact_index=artifact_index,
        )
        report_summary = self._append_report_generator_status(
            summary=report_summary,
            status=report_status,
            message=report_message,
        )
        return artifact_index, report_summary, report_status, report_message

    def _build_blueprint_artifact_index(
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

    def _run_report_generator_artifact_index(
        self,
        *,
        pipeline_name: str,
        working_directory: str,
        run_context: RunContext,
        job_handle: JobHandle,
        submission_command: str,
        scheduler_script_path: str,
        wrapper_path: str,
        log_paths: list[str],
        audit_path: str | None,
    ) -> tuple[str, str | None, dict[str, object] | None]:
        script_path = Path(__file__).resolve().parents[2] / "scripts" / "report_generator" / "run_report_generator.sh"
        if not script_path.exists():
            return ("skipped_script_missing", "report_generator_script_missing", None)

        bash = shutil.which("bash")
        if bash is None:
            return ("skipped_bash_missing", "bash_not_found", None)

        work_path = Path(working_directory)
        if not work_path.is_dir():
            return ("skipped_workdir_missing", "working_directory_not_found", None)

        results_root = self._join_work_path(working_directory, "results")
        if not Path(results_root).is_dir():
            return ("skipped_results_root_missing", "results_root_not_found", None)

        index_path = self._join_work_path(working_directory, "results/report_index.json")
        summary_output = self._join_work_path(working_directory, "reports/summary_report.md")
        traceability_dir = self._join_work_path(working_directory, "results/traceability")
        command = [
            bash,
            "--noprofile",
            "--norc",
            script_path.as_posix(),
            "--workdir",
            working_directory,
            "--results-root",
            results_root,
            "--summary-output",
            summary_output,
            "--traceability-dir",
            traceability_dir,
            "--pipeline",
            pipeline_name,
            "--task-id",
            run_context.task_id,
            "--run-id",
            run_context.run_id,
            "--job-id",
            job_handle.job_id,
            "--job-state",
            job_handle.state.value,
            "--submit-command",
            submission_command,
            "--scheduler-script",
            scheduler_script_path,
            "--wrapper",
            wrapper_path,
            "--stdout-path",
            log_paths[0] if len(log_paths) > 0 else "",
            "--stderr-path",
            log_paths[1] if len(log_paths) > 1 else "",
            "--force",
        ]
        if run_context.session_id:
            command.extend(["--session-id", run_context.session_id])
        if audit_path:
            command.extend(["--audit-path", audit_path])
        for log_path in log_paths:
            if log_path:
                command.extend(["--log-path", log_path])
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
                timeout=max(10, self._settings.scheduler_command_timeout_seconds),
            )
        except (OSError, subprocess.TimeoutExpired):
            return ("failed_invocation", "report_generator_invocation_error", None)
        if completed.returncode != 0:
            failure_message = completed.stderr.strip() or completed.stdout.strip() or "report_generator_nonzero_exit"
            failure_token = "_".join(failure_message.split()[:8]).lower()
            return ("failed_nonzero_exit", failure_token[:120] or "report_generator_nonzero_exit", None)

        index_file = Path(index_path)
        if not index_file.is_file():
            return ("failed_index_missing", "report_index_missing_after_run", None)

        try:
            payload = json.loads(index_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return ("failed_index_invalid", "report_index_json_invalid", None)
        if not isinstance(payload, dict):
            return ("failed_index_invalid", "report_index_payload_not_object", None)
        return ("integrated", "report_index_v2_loaded", payload)

    def _classify_report_generator_artifacts(
        self,
        *,
        working_directory: str,
        payload: dict[str, object],
    ) -> dict[str, list[str]]:
        results: list[str] = []
        figures: list[str] = []
        reports: list[str] = []
        collections = payload.get("collections")
        if isinstance(collections, dict):
            results.extend(self._resolve_collection_paths(working_directory=working_directory, values=collections.get("results")))
            figures.extend(self._resolve_collection_paths(working_directory=working_directory, values=collections.get("figures")))
            reports.extend(self._resolve_collection_paths(working_directory=working_directory, values=collections.get("reports")))

        by_kind = payload.get("by_kind")
        if isinstance(by_kind, dict):
            results.extend(self._resolve_collection_paths(working_directory=working_directory, values=by_kind.get("results")))
            figures.extend(self._resolve_collection_paths(working_directory=working_directory, values=by_kind.get("figures")))
            reports.extend(self._resolve_collection_paths(working_directory=working_directory, values=by_kind.get("reports")))
            traceability_paths = self._resolve_collection_paths(
                working_directory=working_directory,
                values=by_kind.get("traceability"),
            )
            for path in traceability_paths:
                if path.lower().endswith((".md", ".markdown")):
                    reports.append(path)
                else:
                    results.append(path)

        raw_artifacts = payload.get("artifacts", [])
        if isinstance(raw_artifacts, list):
            for item in raw_artifacts:
                if not isinstance(item, dict):
                    continue
                raw_path = str(item.get("path", "")).strip()
                if not raw_path:
                    continue
                resolved_path = self._resolve_artifact_path(
                    working_directory=working_directory,
                    path=raw_path,
                )
                kind = str(item.get("kind", "")).strip().lower()
                lowered_path = raw_path.replace("\\", "/").lower()
                suffix = Path(raw_path).suffix.lower()
                if kind in {"figure", "figures"} or "/figures/" in lowered_path or suffix in {".png", ".svg", ".jpg", ".jpeg", ".pdf"}:
                    figures.append(resolved_path)
                elif kind in {"report", "reports"} or lowered_path.startswith("reports/") or "report" in lowered_path or suffix in {".md", ".markdown"}:
                    reports.append(resolved_path)
                elif kind in {"traceability"} and suffix in {".md", ".markdown"}:
                    reports.append(resolved_path)
                else:
                    results.append(resolved_path)

        traceability = payload.get("traceability")
        if isinstance(traceability, dict):
            links = traceability.get("links", [])
            if isinstance(links, list):
                for link in links:
                    if not isinstance(link, dict):
                        continue
                    raw_path = str(link.get("path", "")).strip()
                    if not raw_path:
                        continue
                    resolved_path = self._resolve_artifact_path(
                        working_directory=working_directory,
                        path=raw_path,
                    )
                    suffix = Path(raw_path).suffix.lower()
                    if suffix in {".md", ".markdown"}:
                        reports.append(resolved_path)
                    elif suffix in {".json", ".jsonl"}:
                        results.append(resolved_path)
        return {
            "results": self._stable_unique(results),
            "figures": self._stable_unique(figures),
            "reports": self._stable_unique(reports),
        }

    def _resolve_collection_paths(
        self,
        *,
        working_directory: str,
        values: object,
    ) -> list[str]:
        if not isinstance(values, list):
            return []
        resolved: list[str] = []
        for item in values:
            raw_path = str(item).strip()
            if not raw_path:
                continue
            resolved.append(
                self._resolve_artifact_path(
                    working_directory=working_directory,
                    path=raw_path,
                )
            )
        return resolved

    def _build_report_generator_summary(
        self,
        *,
        payload: dict[str, object],
        pipeline_name: str,
        artifact_index: dict[str, list[str]],
    ) -> str:
        base = (
            f"{pipeline_name} report_generator integrated "
            f"{len(artifact_index['results']) + len(artifact_index['figures']) + len(artifact_index['reports'])} indexed artifacts; "
            f"{len(artifact_index['results'])} results, {len(artifact_index['figures'])} figures, "
            f"{len(artifact_index['logs'])} logs, {len(artifact_index['reports'])} reports."
        )
        details: list[str] = []

        summary = payload.get("summary")
        if isinstance(summary, dict):
            one_line = str(summary.get("one_line", "")).strip()
            if one_line:
                details.append(f"index={one_line}")

        selected_blueprint = payload.get("selected_blueprint_summary")
        if isinstance(selected_blueprint, dict):
            blueprint_name = str(selected_blueprint.get("name", "")).strip()
            coverage = selected_blueprint.get("coverage", {})
            if blueprint_name:
                details.append(f"blueprint={blueprint_name}")
            if isinstance(coverage, dict):
                present = coverage.get("present_markers", 0)
                required = coverage.get("required_markers", 0)
                details.append(f"coverage={present}/{required}")

        diagnostics = payload.get("diagnostics")
        if isinstance(diagnostics, dict):
            diagnostic_status = str(diagnostics.get("status", "")).strip()
            diagnostic_summary = str(diagnostics.get("summary", "")).strip()
            if diagnostic_status:
                if diagnostic_summary:
                    details.append(f"diagnostics={diagnostic_status}:{diagnostic_summary}")
                else:
                    details.append(f"diagnostics={diagnostic_status}")

        traceability = payload.get("traceability")
        if isinstance(traceability, dict):
            links = traceability.get("links", [])
            if isinstance(links, list):
                labels: list[str] = []
                for link in links:
                    if not isinstance(link, dict):
                        continue
                    label = str(link.get("rel", "")).strip()
                    if label:
                        labels.append(label)
                if labels:
                    details.append(f"traceability={','.join(self._stable_unique(labels)[:4])}")

        if details:
            return f"{base} {'; '.join(details)}."
        return base

    @staticmethod
    def _append_report_generator_status(
        *,
        summary: str,
        status: str,
        message: str | None,
    ) -> str:
        stripped = summary.strip()
        if stripped.endswith("."):
            stripped = stripped[:-1]
        suffix = f"report_generator_status={status}"
        if message:
            suffix = f"{suffix}; report_generator_message={message}"
        return f"{stripped}. {suffix}."

    def _resolve_artifact_path(
        self,
        *,
        working_directory: str,
        path: str,
    ) -> str:
        normalized = path.replace("\\", "/").strip()
        if not normalized:
            return normalized
        if normalized.startswith("/") or (len(normalized) >= 2 and normalized[1] == ":"):
            return normalized
        return self._join_work_path(working_directory, normalized)

    @staticmethod
    def _stable_unique(items: list[str]) -> list[str]:
        ordered: list[str] = []
        seen: set[str] = set()
        for item in items:
            if not item or item in seen:
                continue
            seen.add(item)
            ordered.append(item)
        return ordered

    def _predict_audit_record_path(
        self,
        *,
        run_context: RunContext,
        working_directory: str,
    ) -> str:
        return self._join_work_path(
            working_directory,
            f".geneagent/audit/{run_context.task_id}/{run_context.run_id}.jsonl",
        )

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

    def _resolve_report_sections_for_preview(self, *, plan: TaskPlan) -> list[str]:
        if plan.pipeline_spec is None:
            return [
                "Request scope and intent",
                "Local retrieval context",
                "Answer blueprint summary",
                "Safety review note (if needed)",
            ]
        try:
            blueprint = build_blueprint(plan.pipeline_spec.name)
        except ValueError:
            return [
                "Pipeline summary",
                "Expected artifacts",
                "Diagnostics and caveats",
            ]
        sections = [str(item) for item in blueprint.report_sections if str(item).strip()]
        if sections:
            return sections
        return [
            "Pipeline summary",
            "Expected artifacts",
            "Diagnostics and caveats",
        ]

    def _resolve_expected_artifacts_for_preview(
        self,
        *,
        plan: TaskPlan,
        working_directory: str,
    ) -> dict[str, list[str]]:
        if plan.pipeline_spec is None:
            return {
                "results": [self._join_work_path(working_directory, "results/answer_blueprint.md")],
                "reports": [self._join_work_path(working_directory, "reports/answer_summary.md")],
                "figures": [],
                "logs": [],
            }
        try:
            blueprint = build_blueprint(plan.pipeline_spec.name)
        except ValueError:
            return {
                "results": [self._join_work_path(working_directory, "results/pipeline_outputs.md")],
                "reports": [self._join_work_path(working_directory, "reports/summary_report.md")],
                "figures": [],
                "logs": [],
            }
        results: list[str] = []
        reports: list[str] = []
        figures: list[str] = []
        for output in blueprint.outputs:
            relative_path = str(output.get("relative_path", "")).strip()
            if not relative_path:
                continue
            resolved = self._join_work_path(working_directory, relative_path)
            lowered_path = relative_path.lower()
            lowered_format = str(output.get("format", "")).lower()
            if "figure" in lowered_path or lowered_format in {"png", "svg", "jpg", "jpeg", "pdf"}:
                figures.append(resolved)
                continue
            if lowered_path.startswith("reports/") or "report" in lowered_path or lowered_format == "markdown":
                reports.append(resolved)
                continue
            results.append(resolved)
        return {
            "results": self._stable_unique(results),
            "reports": self._stable_unique(reports),
            "figures": self._stable_unique(figures),
            "logs": [],
        }

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
