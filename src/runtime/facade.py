"""High-level runtime facade for CLI and API entry points."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path, PurePosixPath, PureWindowsPath
import shlex
import shutil
import subprocess
import zipfile
from uuid import uuid4

from pydantic import BaseModel, Field

from audit.observability import ObservabilityService
from audit.store import AuditEvent, FileAuditStore
from contracts.api import RequestIdentity
from contracts.common import ExecutionMode, GateDecision, JobState, SchedulerKind, TaskDomain
from contracts.envelope import ExecutionIntent, RuntimeRequestEnvelopeV2
from contracts.execution import (
    AuditBundleExport,
    AuditBundleItem,
    ExecutionArtifacts,
    JobHandle,
    RunContext,
    SubmissionPreview,
    TaskPlan,
)
from contracts.remote_execution import RemoteCheckResult, RemoteSmokeResult, RunState
from contracts.tasks import ResourceEstimate, UserRequest
from contracts.validation import InputBundle, ValidationReport
from memory.stores import MemoryCoordinator
from pipeline.execution import build_execution_command
from pipeline.workflows import build_blueprint
from pipeline.validators import InputValidator
from safety.automation_policy import TrustedAutomationPolicy
from safety.gates import GateStage, SafetyGateResult, SafetyGateService, SafetyReviewContext
from scheduler.base import BaseSchedulerAdapter
from scheduler.remote import RemoteSlurmSchedulerAdapter, build_manual_submit_card
from scheduler.ssh_shell import RemoteShellSchedulerAdapter
from scheduler.models import PollExplanation
from scheduler.poller import JobPoller
from runtime.governance import GovernanceService
from runtime.automation import TrustedRunController
from runtime.run_state import RunStateStore
from runtime.state_machine import RuntimeStage, create_stage_trace
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
    explanation_layer: dict[str, object] = Field(default_factory=dict)


class DiagnosticPreview(BaseModel):
    """Diagnostic preview payload for CLI/API diagnostic endpoints."""

    run_context: RunContext
    domain: str
    retrieval_mode: str
    coverage: str
    fallback_requested: bool = False
    fallback_gate_decision: str = "not_requested"
    fallback_gate_reason: str = "coverage_high"
    fallback_gate_audit: dict[str, object] = Field(default_factory=dict)
    fallback_used: bool = False
    fallback: dict[str, object] = Field(default_factory=dict)
    diagnostic_suggestions: list[dict[str, object]] = Field(default_factory=list)
    sources: list[dict[str, object]] = Field(default_factory=list)
    cluster_execution_enabled: bool = False
    non_bio_cluster_policy: str | None = None
    explanation_layer: dict[str, object] = Field(default_factory=dict)


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
        self._observability = ObservabilityService(audit_store)
        self._governance = GovernanceService(settings=settings, audit_store=audit_store)
        self._run_state_store = RunStateStore(settings.local_state_root)
        self._trusted_controller = TrustedRunController(
            state_store=self._run_state_store,
            policy=TrustedAutomationPolicy(
                level=settings.remote_auto_repair_level,
                cpu_cap=settings.max_cpu,
                memory_gb_cap=settings.max_mem_gb,
            ),
        )

    def draft_plan(
        self,
        text: str,
        *,
        identity: RequestIdentity | None = None,
        requested_outputs: list[str] | None = None,
        input_bundle: InputBundle | None = None,
    ) -> TaskPlan:
        """Build a draft plan from natural-language input."""

        envelope = self._build_runtime_envelope(
            intent=ExecutionIntent.PLAN,
            request_text=text,
            identity=identity,
            requested_outputs=requested_outputs,
            input_bundle=input_bundle,
        )
        run_context = self._resolve_run_context(identity=self._identity_from_envelope(envelope))
        normalized_bundle, validation_report = self._prepare_input_bundle(envelope.input_bundle)
        plan = self._orchestrator.draft_plan(
            UserRequest(
                text=envelope.request_text,
                working_directory=run_context.working_directory,
                requested_outputs=envelope.requested_outputs,
                input_bundle=normalized_bundle,
            ),
            run_context=run_context,
        )
        plan = self._attach_input_bundle_to_plan(
            plan=plan,
            input_bundle=normalized_bundle,
            validation_report=validation_report,
        )
        trace = create_stage_trace(task_id=run_context.task_id, run_id=run_context.run_id, domain=plan.domain)
        if plan.domain == TaskDomain.BIOINFORMATICS:
            trace.advance(RuntimeStage.STAGE_02_INTENT_AND_SCOPE.value)
            trace.advance(RuntimeStage.STAGE_03_INPUT_VALIDATION.value)
            trace.advance(RuntimeStage.STAGE_04_LOCAL_FIRST_RAG.value)
            trace.advance(RuntimeStage.STAGE_05_BLUEPRINT_SELECTION.value)
            trace.advance(RuntimeStage.STAGE_06_RESOURCE_AND_SAFETY_GATE.value)
        else:
            trace.advance(RuntimeStage.LITE_02_LOCAL_RETRIEVAL.value)
            trace.advance(RuntimeStage.LITE_03_ANSWER_BLUEPRINT.value)
        selected_blueprint = (
            plan.pipeline_spec.name
            if plan.pipeline_spec is not None
            else f"{plan.domain.value}_lightweight"
        )
        explanation_layer = self._build_explanation_layer(
            domain=plan.domain.value,
            selected_blueprint=selected_blueprint,
            blueprint_reason=(
                f"intent routed to {plan.domain.value} domain and mapped to `{selected_blueprint}` "
                "under the fixed blueprint selection contract."
            ),
            gate_decision="design_pass" if plan.header.ready_for_gate.value == "design_pass" else "not_ready",
            gate_reason=(
                "stage-06 resource/safety checks are required before real submit; "
                "current plan is design-level and execution-gated."
            ),
            repair_recommendation=(
                "If downstream execution fails, use diagnostic suggestions and cross-run failure-repair hints "
                "before retrying submit."
            ),
            repair_basis=[
                f"cross_run_failure_hints={len((plan.cross_run_handoff or {}).get('prioritized_failure_repairs', []))}",
                f"cross_run_reuse_hints={len((plan.cross_run_handoff or {}).get('reused_parameters', []))}",
            ],
        )
        return plan.model_copy(
            update={
                "runtime_lifecycle": trace.to_contract(),
                "explanation_layer": explanation_layer,
            }
        )

    def validate_inputs(
        self,
        inputs: list[str] | list[dict[str, object]] | dict[str, object],
    ) -> ValidationReport:
        """Validate local input paths before a workflow is drafted or submitted."""

        return self._input_validator.validate(inputs)

    def _prepare_input_bundle(
        self,
        input_bundle: InputBundle | None,
    ) -> tuple[InputBundle | None, ValidationReport | None]:
        if input_bundle is None:
            return None, None
        snapshot = self._input_validator.inspect(input_bundle)
        return snapshot.bundle, snapshot.to_contract_report()

    def _build_runtime_envelope(
        self,
        *,
        intent: ExecutionIntent,
        request_text: str,
        identity: RequestIdentity | None = None,
        requested_outputs: list[str] | None = None,
        input_bundle: InputBundle | None = None,
        command: list[str] | None = None,
        dry_run_completed: bool = False,
        approval: dict[str, object] | None = None,
        outbound_payload: dict[str, object] | None = None,
        execution_mode: ExecutionMode | None = None,
        remote_profile_name: str | None = None,
        watch: bool = False,
        auto_continue: bool | None = None,
    ) -> RuntimeRequestEnvelopeV2:
        return RuntimeRequestEnvelopeV2(
            intent=intent,
            request_text=request_text,
            identity=identity or RequestIdentity(),
            input_bundle=input_bundle,
            requested_outputs=requested_outputs or [],
            command=command,
            dry_run_completed=dry_run_completed,
            approval=approval,
            outbound_payload=outbound_payload,
            execution_mode=execution_mode,
            remote_profile_name=remote_profile_name,
            watch=watch,
            auto_continue=auto_continue,
        )

    def _identity_from_envelope(self, envelope: RuntimeRequestEnvelopeV2) -> RequestIdentity:
        if envelope.working_directory is None:
            return envelope.identity
        return envelope.identity.model_copy(update={"working_directory": envelope.working_directory})

    def _attach_input_bundle_to_plan(
        self,
        *,
        plan: TaskPlan,
        input_bundle: InputBundle | None,
        validation_report: ValidationReport | None,
    ) -> TaskPlan:
        if plan.pipeline_spec is None:
            return plan.model_copy(update={"input_validation": validation_report})
        updated_pipeline_spec = plan.pipeline_spec.model_copy(
            update={
                "input_bundle": input_bundle,
                "input_paths": [entry.path for entry in input_bundle.entries] if input_bundle is not None else [],
            }
        )
        return plan.model_copy(
            update={
                "pipeline_spec": updated_pipeline_spec,
                "input_validation": validation_report,
            }
        )

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
        explanation_layer = self._build_explanation_layer(
            domain=plan.domain.value,
            selected_blueprint=selected_blueprint,
            blueprint_reason=(
                f"report preview reuses orchestration selection `{selected_blueprint}` from the same request intent."
            ),
            gate_decision="informational_preview",
            gate_reason="report preview does not submit jobs; scheduler gate remains closed in preview mode.",
            repair_recommendation=(
                "If report sections are missing, run diagnostic preview to inspect artifact gaps and failure signals."
            ),
            repair_basis=[
                f"report_sections={len(self._resolve_report_sections_for_preview(plan=plan))}",
                f"cluster_execution_enabled=false",
            ],
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
            explanation_layer=explanation_layer,
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
        fallback_gate_audit = dict(diagnostics.get("fallback_gate_audit", {}))
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
        top_repair = ""
        suggestions = list(diagnostics.get("diagnostic_suggestions", []))
        if suggestions and isinstance(suggestions[0], dict):
            top_repair = str(suggestions[0].get("recommended_fix", "")).strip()
        explanation_layer = self._build_explanation_layer(
            domain=domain,
            selected_blueprint=(
                "non_bio_lightweight"
                if domain != TaskDomain.BIOINFORMATICS.value
                else "diagnostic_only"
            ),
            blueprint_reason=(
                "diagnostic preview follows local-first retrieval diagnostics and does not trigger a workflow submit path."
            ),
            gate_decision=fallback_gate_decision,
            gate_reason=(
                f"fallback gate decision is `{fallback_gate_decision}` because `{fallback_gate_reason}`."
            ),
            repair_recommendation=(
                top_repair
                or "Use the top diagnostic_suggestions item and linked references before retrying execution."
            ),
            repair_basis=[
                f"suggestions={len(suggestions)}",
                f"fallback_used={str(fallback_used).lower()}",
                f"retrieval_mode={str(diagnostics.get('retrieval_mode', 'local_only'))}",
            ],
        )
        return DiagnosticPreview(
            run_context=diagnostic_run_context,
            domain=domain,
            retrieval_mode=str(diagnostics.get("retrieval_mode", "local_only")),
            coverage=str(diagnostics.get("coverage", "low")),
            fallback_requested=fallback_requested,
            fallback_gate_decision=fallback_gate_decision,
            fallback_gate_reason=fallback_gate_reason,
            fallback_gate_audit=fallback_gate_audit,
            fallback_used=fallback_used,
            fallback={
                "requested": fallback_requested,
                "gate_decision": fallback_gate_decision,
                "gate_reason": fallback_gate_reason,
                "gate_audit": fallback_gate_audit,
                "used": fallback_used,
            },
            diagnostic_suggestions=list(diagnostics.get("diagnostic_suggestions", [])),
            sources=list(diagnostics.get("sources", [])),
            cluster_execution_enabled=False,
            non_bio_cluster_policy=non_bio_cluster_policy,
            explanation_layer=explanation_layer,
        )

    def review_action(
        self,
        action_name: str,
        *,
        identity: RequestIdentity | None = None,
        reason: str | None = None,
        target_paths: list[str] | None = None,
        external_network: bool = False,
        cloud_llm: bool = False,
        outbound_payload: dict[str, object] | None = None,
        approval: dict[str, object] | None = None,
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
                external_network=external_network,
                cloud_llm=cloud_llm,
                outbound_payload=outbound_payload,
                manual_approval=approval,
                current_active_jobs=self._settings.scheduler_current_active_jobs,
                quota_cpu_hours_limit=self._settings.scheduler_quota_cpu_hours_limit,
                quota_memory_gb_limit=self._settings.scheduler_quota_memory_gb_limit,
                quota_max_concurrent_jobs=self._settings.scheduler_quota_max_concurrent_jobs,
                outbound_allowed_fields=self._settings.allow_cloud_fields,
                outbound_policy_enforced=self._settings.outbound_policy_enforced,
            )
        )

    def build_dry_run_submission(
        self,
        *,
        command: list[str] | None = None,
        request_text: str = "Prepare a dry-run submission",
        identity: RequestIdentity | None = None,
        input_bundle: InputBundle | None = None,
        approval: dict[str, object] | None = None,
        outbound_payload: dict[str, object] | None = None,
    ) -> SubmissionPreview:
        """Generate a scheduler script preview and a synthetic dry-run handle."""

        return self._build_submission_preview(
            mode="dry-run",
            command=command,
            request_text=request_text,
            identity=identity,
            dry_run_completed=True,
            execute_submit=False,
            input_bundle=input_bundle,
            approval=approval,
            outbound_payload=outbound_payload,
        )

    def build_submit_preview(
        self,
        *,
        command: list[str] | None = None,
        request_text: str = "Prepare a submit-preview",
        identity: RequestIdentity | None = None,
        dry_run_completed: bool = False,
        input_bundle: InputBundle | None = None,
        approval: dict[str, object] | None = None,
        outbound_payload: dict[str, object] | None = None,
        execution_mode: ExecutionMode | None = None,
        remote_profile_name: str | None = None,
        watch: bool = False,
        auto_continue: bool | None = None,
    ) -> SubmissionPreview:
        """Build a submit-preview payload without issuing a real scheduler command."""

        return self._build_submission_preview(
            mode="submit-preview",
            command=command,
            request_text=request_text,
            identity=identity,
            dry_run_completed=dry_run_completed,
            execute_submit=False,
            input_bundle=input_bundle,
            approval=approval,
            outbound_payload=outbound_payload,
            execution_mode=execution_mode,
            remote_profile_name=remote_profile_name,
            watch=watch,
            auto_continue=auto_continue,
        )

    def submit(
        self,
        *,
        command: list[str] | None = None,
        request_text: str = "Submit scheduler job",
        identity: RequestIdentity | None = None,
        dry_run_completed: bool = False,
        input_bundle: InputBundle | None = None,
        approval: dict[str, object] | None = None,
        outbound_payload: dict[str, object] | None = None,
        execution_mode: ExecutionMode | None = None,
        remote_profile_name: str | None = None,
        watch: bool = False,
        auto_continue: bool | None = None,
    ) -> SubmissionPreview:
        """Submit a real scheduler job after passing the safety gate."""

        return self._build_submission_preview(
            mode="submit",
            command=command,
            request_text=request_text,
            identity=identity,
            dry_run_completed=dry_run_completed,
            execute_submit=True,
            input_bundle=input_bundle,
            approval=approval,
            outbound_payload=outbound_payload,
            execution_mode=execution_mode,
            remote_profile_name=remote_profile_name,
            watch=watch,
            auto_continue=auto_continue,
        )

    def explain_poll_state(self, job_id: str) -> PollExplanation:
        """Explain a scheduler job state using real or synthetic poll interpretation."""

        state = self._scheduler.poll(job_id)
        return self._poller.explain(
            scheduler=self._settings.scheduler_type,
            job_id=job_id,
            state=state,
        )

    def remote_check(
        self,
        *,
        execution_mode: ExecutionMode | None = None,
        remote_profile_name: str | None = None,
    ) -> RemoteCheckResult:
        """Check the configured execution target without exposing credentials."""

        resolved_mode = self._resolve_execution_mode(execution_mode)
        profile = self._settings.remote_execution_profile(remote_profile_name)
        if resolved_mode == ExecutionMode.SSH_SHELL_TRUSTED:
            checker = self._build_remote_shell_check_scheduler(profile=profile)
            return checker.remote_check(timeout_seconds=self._settings.hpc_connect_timeout_seconds)
        if resolved_mode == ExecutionMode.SSH_SLURM_TRUSTED and self._settings.scheduler_type == SchedulerKind.SLURM:
            checker = self._build_remote_check_scheduler(profile=profile)
            return checker.remote_check(timeout_seconds=self._settings.hpc_connect_timeout_seconds)
        if resolved_mode == ExecutionMode.MANUAL_SBASE:
            return RemoteCheckResult(
                profile_name=profile.profile_name,
                execution_mode=ExecutionMode.MANUAL_SBASE,
                scheduler=self._settings.scheduler_type,
                ssh_target=profile.ssh_target,
                work_root=profile.work_root,
                reachable=False,
                safe_for_submit=False,
                messages=["manual_sbase_requires_operator_submit"],
            )
        return RemoteCheckResult(
            profile_name=profile.profile_name,
            execution_mode=resolved_mode,
            scheduler=self._settings.scheduler_type,
            ssh_target=profile.ssh_target,
            work_root=profile.work_root,
            reachable=resolved_mode == ExecutionMode.HPC_LOCAL,
            safe_for_submit=resolved_mode == ExecutionMode.HPC_LOCAL and self._settings.scheduler_real_execution_enabled,
            messages=["local_preview_no_remote_check" if resolved_mode == ExecutionMode.LOCAL_PREVIEW else "hpc_local_uses_local_scheduler_cli"],
        )

    def remote_smoke(
        self,
        *,
        execution_mode: ExecutionMode | None = None,
        remote_profile_name: str | None = None,
        task_id: str | None = None,
        run_id: str | None = None,
    ) -> RemoteSmokeResult:
        """Submit one fixed harmless command to validate ordinary remote execution."""

        resolved_mode = self._resolve_execution_mode(execution_mode or ExecutionMode.SSH_SHELL_TRUSTED)
        smoke_command = ["bash", "-lc", "hostname && pwd && date && sleep 5"]
        remote_check = self.remote_check(
            execution_mode=resolved_mode,
            remote_profile_name=remote_profile_name,
        )
        messages = list(remote_check.messages)
        profile = self._settings.remote_execution_profile(remote_profile_name)
        if resolved_mode != ExecutionMode.SSH_SHELL_TRUSTED:
            messages.append("remote_smoke_requires_ssh_shell_trusted")
            return RemoteSmokeResult(
                profile_name=profile.profile_name,
                execution_mode=resolved_mode,
                command=smoke_command,
                remote_check=remote_check,
                submitted=False,
                messages=messages,
            )
        if not remote_check.safe_for_submit:
            return RemoteSmokeResult(
                profile_name=profile.profile_name,
                execution_mode=resolved_mode,
                command=smoke_command,
                remote_check=remote_check,
                submitted=False,
                messages=messages,
            )
        if not self._settings.scheduler_real_execution_enabled:
            messages.append("scheduler_real_execution_disabled")
            return RemoteSmokeResult(
                profile_name=profile.profile_name,
                execution_mode=resolved_mode,
                command=smoke_command,
                remote_check=remote_check,
                submitted=False,
                messages=messages,
            )

        scheduler = self._scheduler_for_execution_mode(
            execution_mode=resolved_mode,
            remote_profile_name=remote_profile_name,
        )
        resolved_task_id = task_id or f"task-smoke-{uuid4().hex[:8]}"
        resolved_run_id = run_id or f"run-smoke-{uuid4().hex[:8]}"
        handle = scheduler.submit(
            working_directory=profile.work_root,
            resources=ResourceEstimate(cpus=1, memory_gb=1, walltime="00:05:00"),
            command=smoke_command,
            job_name="geneagent-smoke",
            task_id=resolved_task_id,
            run_id=resolved_run_id,
        )
        run_state = RunState(
            task_id=resolved_task_id,
            run_id=resolved_run_id,
            execution_mode=resolved_mode,
            remote_profile_name=profile.profile_name,
            scheduler=SchedulerKind.SHELL,
            working_directory=profile.work_root,
            current_stage=RuntimeStage.STAGE_07_EXECUTION.value,
            status=handle.state,
            job_id=handle.job_id,
            auto_continue=False,
            next_action="watch shell state",
        ).with_stage(
            stage_id=RuntimeStage.STAGE_07_EXECUTION.value,
            status="submitted",
            message="fixed remote smoke command submitted",
            job_id=handle.job_id,
            run_status=handle.state,
            auto_continue_ready=False,
        )
        run_state_path = self._run_state_store.save(run_state)
        return RemoteSmokeResult(
            profile_name=profile.profile_name,
            execution_mode=resolved_mode,
            command=smoke_command,
            remote_check=remote_check,
            submitted=True,
            job_handle=handle,
            initial_state=handle.state,
            run_state_path=str(run_state_path),
            messages=messages,
        )

    def _build_remote_check_scheduler(self, *, profile) -> RemoteSlurmSchedulerAdapter:
        return RemoteSlurmSchedulerAdapter(
            profile=profile,
            local_cache_root=Path(self._settings.local_state_root),
            real_execution_enabled=False,
            idempotent_submit_enabled=False,
            retry_max_attempts=1,
            retry_backoff_seconds=[0],
            command_timeout_seconds=self._settings.hpc_connect_timeout_seconds,
            quota_cpu_hours_limit=self._settings.scheduler_quota_cpu_hours_limit,
            quota_memory_gb_limit=self._settings.scheduler_quota_memory_gb_limit,
            quota_max_concurrent_jobs=self._settings.scheduler_quota_max_concurrent_jobs,
            current_active_jobs=self._settings.scheduler_current_active_jobs,
        )

    def _build_remote_shell_check_scheduler(self, *, profile) -> RemoteShellSchedulerAdapter:
        return RemoteShellSchedulerAdapter(
            profile=profile,
            local_cache_root=Path(self._settings.local_state_root),
            remote_cpu_cap=self._settings.remote_shell_cpu_cap,
            remote_memory_gb_cap=self._settings.remote_shell_memory_gb_cap,
            remote_walltime_cap=self._settings.remote_shell_walltime_cap,
            remote_max_concurrent_runs=self._settings.remote_shell_max_concurrent_runs,
            process_limits_enabled=self._settings.remote_shell_process_limits_enabled,
            real_execution_enabled=False,
            idempotent_submit_enabled=False,
            retry_max_attempts=1,
            retry_backoff_seconds=[0],
            command_timeout_seconds=self._settings.hpc_connect_timeout_seconds,
            quota_cpu_hours_limit=self._settings.scheduler_quota_cpu_hours_limit,
            quota_memory_gb_limit=self._settings.scheduler_quota_memory_gb_limit,
            quota_max_concurrent_jobs=self._settings.scheduler_quota_max_concurrent_jobs,
            current_active_jobs=self._settings.scheduler_current_active_jobs,
        )

    def _scheduler_for_execution_mode(
        self,
        *,
        execution_mode: ExecutionMode,
        remote_profile_name: str | None,
    ):
        if (
            execution_mode == self._settings.execution_mode
            and (remote_profile_name is None or remote_profile_name == self._settings.remote_profile_name)
        ):
            return self._scheduler
        if execution_mode == ExecutionMode.SSH_SHELL_TRUSTED:
            return RemoteShellSchedulerAdapter(
                profile=self._settings.remote_execution_profile(remote_profile_name),
                local_cache_root=Path(self._settings.local_state_root),
                remote_cpu_cap=self._settings.remote_shell_cpu_cap,
                remote_memory_gb_cap=self._settings.remote_shell_memory_gb_cap,
                remote_walltime_cap=self._settings.remote_shell_walltime_cap,
                remote_max_concurrent_runs=self._settings.remote_shell_max_concurrent_runs,
                process_limits_enabled=self._settings.remote_shell_process_limits_enabled,
                real_execution_enabled=self._settings.scheduler_real_execution_enabled,
                idempotent_submit_enabled=self._settings.scheduler_idempotent_submit_enabled,
                retry_max_attempts=self._settings.scheduler_retry_max_attempts,
                retry_backoff_seconds=self._settings.scheduler_retry_backoff_seconds,
                command_timeout_seconds=self._settings.scheduler_command_timeout_seconds,
                quota_cpu_hours_limit=self._settings.scheduler_quota_cpu_hours_limit,
                quota_memory_gb_limit=self._settings.scheduler_quota_memory_gb_limit,
                quota_max_concurrent_jobs=self._settings.scheduler_quota_max_concurrent_jobs,
                current_active_jobs=self._settings.scheduler_current_active_jobs,
            )
        if execution_mode == ExecutionMode.SSH_SLURM_TRUSTED and self._settings.scheduler_type == SchedulerKind.SLURM:
            return RemoteSlurmSchedulerAdapter(
                profile=self._settings.remote_execution_profile(remote_profile_name),
                local_cache_root=Path(self._settings.local_state_root),
                real_execution_enabled=self._settings.scheduler_real_execution_enabled,
                idempotent_submit_enabled=self._settings.scheduler_idempotent_submit_enabled,
                retry_max_attempts=self._settings.scheduler_retry_max_attempts,
                retry_backoff_seconds=self._settings.scheduler_retry_backoff_seconds,
                command_timeout_seconds=self._settings.scheduler_command_timeout_seconds,
                quota_cpu_hours_limit=self._settings.scheduler_quota_cpu_hours_limit,
                quota_memory_gb_limit=self._settings.scheduler_quota_memory_gb_limit,
                quota_max_concurrent_jobs=self._settings.scheduler_quota_max_concurrent_jobs,
                current_active_jobs=self._settings.scheduler_current_active_jobs,
            )
        return self._scheduler

    def watch_run(self, *, task_id: str, run_id: str) -> RunState:
        """Watch one persisted trusted run state."""

        return self._trusted_controller.watch_run(task_id=task_id, run_id=run_id, scheduler=self._scheduler)

    def resume_run(self, *, task_id: str, run_id: str, auto_continue: bool | None = None) -> RunState:
        """Resume one persisted trusted run state."""

        return self._trusted_controller.resume_run(
            task_id=task_id,
            run_id=run_id,
            scheduler=self._scheduler,
            auto_continue=auto_continue,
        )

    def list_task_board(
        self,
        *,
        working_directory: str | None = None,
        limit: int = 20,
    ) -> dict[str, object]:
        """List recent run closures for minimal dashboard/task-board rendering."""

        rows = self._audit_store.list_recent_runs(
            working_directory=working_directory or self._settings.work_root,
            limit=max(1, limit),
        )
        return {
            "source": "file_audit_store",
            "limit": max(1, limit),
            "runs": rows,
        }

    def observability_metrics(
        self,
        *,
        working_directory: str | None = None,
        limit: int = 200,
    ) -> dict[str, object]:
        """Return task/scheduler/failure metrics derived from audit traces."""

        return self._observability.build_metrics(
            working_directory=working_directory or self._settings.work_root,
            limit=limit,
        )

    def observability_dashboard(
        self,
        *,
        working_directory: str | None = None,
        limit: int = 100,
    ) -> dict[str, object]:
        """Return dashboard payload combining metrics with recent run board."""

        return self._observability.build_dashboard(
            working_directory=working_directory or self._settings.work_root,
            limit=limit,
        )

    def production_gate_pipeline(
        self,
        *,
        working_directory: str | None = None,
        execute_tests: bool = False,
        timeout_seconds: int = 300,
    ) -> dict[str, object]:
        """Run production gate checks (contract/scheduler/knowledge/audit)."""

        return self._governance.run_production_gate(
            working_directory=working_directory or self._settings.work_root,
            execute_tests=execute_tests,
            timeout_seconds=timeout_seconds,
        )

    def release_plan(
        self,
        *,
        version_tag: str,
        change_summary: str,
        stage_ids: list[str] | None = None,
    ) -> dict[str, object]:
        """Generate standardized release plan with changelog and rollback template."""

        return self._governance.build_release_plan(
            version_tag=version_tag,
            change_summary=change_summary,
            stage_ids=stage_ids or [],
        )

    def final_acceptance_review(
        self,
        *,
        working_directory: str | None = None,
    ) -> dict[str, object]:
        """Run V2.0 final acceptance review across architecture/governance/operability."""

        return self._governance.final_acceptance_review(
            working_directory=working_directory or self._settings.work_root,
        )

    def get_run_snapshot(
        self,
        *,
        run_id: str,
        task_id: str | None = None,
        working_directory: str | None = None,
    ) -> dict[str, object]:
        """Build one run-level snapshot from memory + audit traces."""

        run_record = self._memory_coordinator.get_run(run_id)
        events, audit_path = self._audit_store.read_run_events(
            run_id=run_id,
            task_id=task_id or (run_record.task_id if run_record else None),
            working_directory=working_directory or self._settings.work_root,
        )
        if run_record is None and not events:
            raise ValueError(f"No run trace found for run_id={run_id}.")
        latest_event = events[-1] if events else None
        metadata = latest_event.metadata if latest_event is not None else {}
        if not isinstance(metadata, dict):
            metadata = {}
        runtime_lifecycle = metadata.get("runtime_lifecycle", {})
        if not isinstance(runtime_lifecycle, dict):
            runtime_lifecycle = {}
        metadata_log_paths = metadata.get("log_paths", [])
        if not isinstance(metadata_log_paths, list):
            metadata_log_paths = []
        metadata_manual_records = metadata.get("manual_confirmation_records", [])
        if not isinstance(metadata_manual_records, list):
            metadata_manual_records = []

        resolved_task_id = (
            task_id
            or (run_record.task_id if run_record is not None else None)
            or (latest_event.task_id if latest_event is not None else None)
            or "unknown_task"
        )
        resolved_session_id = run_record.session_id if run_record is not None else None
        resolved_workdir = (
            working_directory
            or (
                self._resolve_working_directory_from_paths(
                    paths=(
                        run_record.log_paths
                        if run_record is not None
                        else []
                    ),
                )
            )
            or self._settings.work_root
        )
        run_context = RunContext(
            task_id=resolved_task_id,
            run_id=run_id,
            session_id=resolved_session_id,
            working_directory=resolved_workdir,
        )
        artifact_index = self._merge_artifact_index(
            run_record.artifact_index if run_record is not None else {},
            metadata.get("artifact_index", {}),
        )
        submission_commands = self._stable_unique(
            [
                *(
                    run_record.submission_commands
                    if run_record is not None
                    else []
                ),
                str(metadata.get("submission_command", "")).strip(),
            ]
        )
        job_ids = self._stable_unique(
            [
                *(
                    run_record.job_ids
                    if run_record is not None
                    else []
                ),
                str(metadata.get("job_id", "")).strip(),
            ]
        )
        log_paths = self._stable_unique(
            [
                *(
                    run_record.log_paths
                    if run_record is not None
                    else []
                ),
                *[
                    str(path).strip()
                    for path in metadata_log_paths
                    if str(path).strip()
                ],
                *artifact_index.get("logs", []),
            ]
        )
        report_paths = self._stable_unique(artifact_index.get("reports", []))
        manual_confirmation_records = self._stable_unique(
            [
                *(
                    run_record.manual_confirmation_records
                    if run_record is not None
                    else []
                ),
                *[
                    str(item).strip()
                    for item in metadata_manual_records
                    if str(item).strip()
                ],
            ]
        )
        approval_records = (
            [
                item.model_dump(mode="json")
                for item in run_record.approval_records
            ]
            if run_record is not None
            else []
        )
        report_summary = (
            (run_record.report_summary if run_record is not None else None)
            or str(metadata.get("report_summary", "")).strip()
            or None
        )
        planning_summary = (
            (run_record.planning_summary if run_record is not None else None)
            or str(metadata.get("planning_summary", "")).strip()
            or None
        )
        input_summary = (
            (run_record.input_summary if run_record is not None else "")
            or str(metadata.get("input_summary", "")).strip()
        )
        selected_blueprint = "unknown"
        submission_cmd_first = submission_commands[0] if submission_commands else ""
        lowered_cmd = submission_cmd_first.lower()
        if "run_genotype_qc.sh" in lowered_cmd:
            selected_blueprint = "qc_pipeline"
        elif "run_population_structure_diversity.sh" in lowered_cmd:
            selected_blueprint = "pca_pipeline"
        elif "run_relationship_matrix.sh" in lowered_cmd:
            selected_blueprint = "grm_builder"
        elif "run_gwas.sh" in lowered_cmd:
            selected_blueprint = "association_mapping_gwas"
        elif "run_breeding_value_prediction.sh" in lowered_cmd:
            selected_blueprint = "genomic_prediction"
        gate_decision = "unknown"
        if runtime_lifecycle.get("runtime_path") == "non_bio_lightweight":
            gate_decision = "pass_non_bio_skip_cluster"
        elif submission_commands and submission_commands[0] == "scheduler_skipped":
            gate_decision = "pass_non_bio_skip_cluster"
        elif manual_confirmation_records:
            gate_decision = "require_confirmation"
        else:
            gate_decision = "pass_or_preview"
        explanation_layer = self._build_explanation_layer(
            domain=(
                run_record.domain.value
                if run_record is not None and run_record.domain is not None
                else "unknown"
            ),
            selected_blueprint=selected_blueprint,
            blueprint_reason="derived from persisted plan/command snapshot in audit+memory records.",
            gate_decision=gate_decision,
            gate_reason=(
                f"runtime_stage={runtime_lifecycle.get('current_stage', 'unknown')}; "
                f"manual_confirmation_records={len(manual_confirmation_records)}."
            ),
            repair_recommendation=(
                "Prioritize failure_repair hints from history and diagnostic suggestions before re-submit."
            ),
            repair_basis=[
                f"job_ids={len(job_ids)}",
                f"audit_event_count={len(events)}",
                f"report_paths={len(report_paths)}",
            ],
        )
        return {
            "run_context": run_context.model_dump(mode="json"),
            "input_summary": input_summary,
            "planning_summary": planning_summary,
            "submission_commands": submission_commands,
            "job_ids": job_ids,
            "log_paths": log_paths,
            "report_paths": report_paths,
            "report_summary": report_summary,
            "manual_confirmation_records": manual_confirmation_records,
            "approval_records": approval_records,
            "artifact_index": artifact_index,
            "runtime_lifecycle": runtime_lifecycle,
            "audit_path": audit_path,
            "audit_event_count": len(events),
            "explanation_layer": explanation_layer,
        }

    def export_audit_bundle(
        self,
        *,
        run_id: str,
        task_id: str | None = None,
        identity: RequestIdentity | None = None,
        output_path: str | None = None,
        include_files: bool = True,
    ) -> AuditBundleExport:
        """Export one-click audit package (zip + manifest) for a run."""

        snapshot = self.get_run_snapshot(
            run_id=run_id,
            task_id=task_id or (identity.task_id if identity else None),
            working_directory=identity.working_directory if identity else None,
        )
        run_context = RunContext.model_validate(snapshot["run_context"])
        export_path = self._resolve_audit_bundle_output_path(
            run_context=run_context,
            output_path=output_path,
        )
        export_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path = export_path.with_suffix(".manifest.json")

        artifact_index_raw = snapshot.get("artifact_index", {})
        if not isinstance(artifact_index_raw, dict):
            artifact_index_raw = {}
        artifact_index: dict[str, list[str]] = {}
        for key, values in artifact_index_raw.items():
            if isinstance(values, list):
                artifact_index[key] = [str(item) for item in values if str(item).strip()]

        audit_path = str(snapshot.get("audit_path", "")).strip() or None
        attachment_sources: list[tuple[str, str]] = []
        for kind in ("results", "figures", "logs", "reports"):
            for path in artifact_index.get(kind, []):
                attachment_sources.append((kind, path))
        for path in snapshot.get("log_paths", []):
            if str(path).strip():
                attachment_sources.append(("logs", str(path)))
        for path in snapshot.get("report_paths", []):
            if str(path).strip():
                attachment_sources.append(("reports", str(path)))
        if audit_path:
            attachment_sources.append(("audit", audit_path))

        exported_items: list[AuditBundleItem] = []
        missing_items: list[AuditBundleItem] = []
        archives_for_manifest: list[dict[str, object]] = []
        workdir = run_context.working_directory or self._settings.work_root

        manifest_payload = {
            "schema_version": "audit_bundle.v1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "run_context": run_context.model_dump(mode="json"),
            "input": {"summary": snapshot.get("input_summary", "")},
            "plan": {"summary": snapshot.get("planning_summary")},
            "execution": {
                "commands": snapshot.get("submission_commands", []),
                "job_ids": snapshot.get("job_ids", []),
                "runtime_lifecycle": snapshot.get("runtime_lifecycle", {}),
            },
            "logs": {"paths": snapshot.get("log_paths", [])},
            "report": {
                "summary": snapshot.get("report_summary"),
                "paths": snapshot.get("report_paths", []),
            },
            "approval_trail": {
                "manual_confirmation_records": snapshot.get("manual_confirmation_records", []),
                "approval_records": snapshot.get("approval_records", []),
            },
            "audit": {
                "source_path": audit_path,
                "event_count": int(snapshot.get("audit_event_count", 0)),
            },
            "artifact_index": artifact_index,
            "attachments": archives_for_manifest,
        }
        manifest_path.write_text(
            json.dumps(manifest_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        with zipfile.ZipFile(export_path, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
            if include_files:
                for index, (kind, source) in enumerate(attachment_sources):
                    resolved_source = self._resolve_artifact_path(
                        working_directory=workdir,
                        path=source,
                    )
                    path_obj = Path(resolved_source)
                    if not path_obj.is_file():
                        missing = AuditBundleItem(
                            kind=kind,
                            source_path=resolved_source,
                            exists=False,
                        )
                        missing_items.append(missing)
                        archives_for_manifest.append(missing.model_dump(mode="json"))
                        continue
                    archive_name = f"attachments/{kind}/{index:03d}_{path_obj.name}"
                    try:
                        archive.write(path_obj, arcname=archive_name)
                    except OSError:
                        missing = AuditBundleItem(
                            kind=kind,
                            source_path=resolved_source,
                            exists=False,
                        )
                        missing_items.append(missing)
                        archives_for_manifest.append(missing.model_dump(mode="json"))
                        continue
                    exported = AuditBundleItem(
                        kind=kind,
                        source_path=resolved_source,
                        archived_path=archive_name,
                        exists=True,
                    )
                    exported_items.append(exported)
                    archives_for_manifest.append(exported.model_dump(mode="json"))
            manifest_payload["attachments"] = archives_for_manifest
            archive.writestr(
                "manifest.json",
                json.dumps(manifest_payload, ensure_ascii=False, indent=2),
            )

        manifest_payload["attachments"] = archives_for_manifest
        manifest_path.write_text(
            json.dumps(manifest_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        return AuditBundleExport(
            run_context=run_context,
            bundle_path=str(export_path),
            manifest_path=str(manifest_path),
            source_audit_path=audit_path,
            audit_event_count=int(snapshot.get("audit_event_count", 0)),
            exported_items=exported_items,
            missing_items=missing_items,
            summary=(
                f"audit bundle exported: {len(exported_items)} files archived, "
                f"{len(missing_items)} files missing."
            ),
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
        input_bundle: InputBundle | None,
        approval: dict[str, object] | None,
        outbound_payload: dict[str, object] | None,
        execution_mode: ExecutionMode | None = None,
        remote_profile_name: str | None = None,
        watch: bool = False,
        auto_continue: bool | None = None,
    ) -> SubmissionPreview:
        """Shared builder for dry-run, submit-preview, and submit modes."""

        intent = ExecutionIntent.DRY_RUN
        if mode == "submit-preview":
            intent = ExecutionIntent.SUBMIT_PREVIEW
        elif mode == "submit":
            intent = ExecutionIntent.SUBMIT
        envelope = self._build_runtime_envelope(
            intent=intent,
            request_text=request_text,
            identity=identity,
            command=command,
            dry_run_completed=dry_run_completed,
            input_bundle=input_bundle,
            approval=approval,
            outbound_payload=outbound_payload,
            execution_mode=execution_mode,
            remote_profile_name=remote_profile_name,
            watch=watch,
            auto_continue=auto_continue,
        )
        resolved_execution_mode = self._resolve_execution_mode(envelope.execution_mode)
        resolved_profile_name = envelope.remote_profile_name or remote_profile_name or self._settings.remote_profile_name
        resolved_auto_continue = (
            envelope.auto_continue
            if envelope.auto_continue is not None
            else (
                auto_continue
                if auto_continue is not None
                else self._settings.remote_auto_continue_enabled
            )
        )
        normalized_identity = self._identity_from_envelope(envelope)
        run_context = self._resolve_run_context(identity=normalized_identity)
        plan = self.draft_plan(text=envelope.request_text, identity=normalized_identity, input_bundle=envelope.input_bundle)
        validation_report = plan.input_validation
        runtime_trace = create_stage_trace(task_id=run_context.task_id, run_id=run_context.run_id, domain=plan.domain)
        if plan.domain != TaskDomain.BIOINFORMATICS:
            runtime_trace.advance(RuntimeStage.LITE_02_LOCAL_RETRIEVAL.value)
            runtime_trace.advance(RuntimeStage.LITE_03_ANSWER_BLUEPRINT.value)
            runtime_trace.advance(RuntimeStage.COMPLETED.value)
            return self._build_non_bio_submission_preview(
                run_context=run_context,
                mode=mode,
                request_text=request_text,
                plan_summary=plan.summary,
                domain=plan.domain,
                input_bundle=plan.pipeline_spec.input_bundle if plan.pipeline_spec is not None else None,
                validation_report=validation_report,
                runtime_lifecycle=runtime_trace.to_contract(),
            )
        execution_scheduler = self._scheduler_for_execution_mode(
            execution_mode=resolved_execution_mode,
            remote_profile_name=resolved_profile_name,
        )
        execution_working_directory = self._execution_working_directory(
            run_context=run_context,
            execution_mode=resolved_execution_mode,
            remote_profile_name=resolved_profile_name,
        )
        if execute_submit and validation_report is not None and not validation_report.valid:
            raise PermissionError(
                "InputBundle validation failed; resolve blocking input issues before real submit."
            )
        command = envelope.command or self._build_default_bio_command(
            plan=plan,
            request_text=request_text,
            working_directory=execution_working_directory,
        )
        runtime_trace.advance(RuntimeStage.STAGE_02_INTENT_AND_SCOPE.value)
        runtime_trace.advance(RuntimeStage.STAGE_03_INPUT_VALIDATION.value)
        runtime_trace.advance(RuntimeStage.STAGE_04_LOCAL_FIRST_RAG.value)
        runtime_trace.advance(RuntimeStage.STAGE_05_BLUEPRINT_SELECTION.value)
        runtime_trace.advance(RuntimeStage.STAGE_06_RESOURCE_AND_SAFETY_GATE.value)
        resources = plan.resource_estimate
        if resources is None:
            raise ValueError("Draft plan did not return a resource estimate.")
        atomic_tools = (
            list(plan.pipeline_spec.atomic_algorithms)
            if plan.pipeline_spec is not None
            else []
        )
        submission_plan = execution_scheduler.build_submission_plan(
            command=command,
            working_directory=execution_working_directory,
            resources=resources,
            mode=mode,
            task_id=run_context.task_id,
            run_id=run_context.run_id,
            atomic_tools=atomic_tools,
        )
        manual_submit_card = None
        if resolved_execution_mode == ExecutionMode.MANUAL_SBASE:
            manual_submit_card = build_manual_submit_card(
                plan=submission_plan,
                profile=self._settings.remote_execution_profile(resolved_profile_name),
            )
        gate_resources = resources.model_copy(
            update={
                "cpus": submission_plan.resource_request.total_cpus,
                "memory_gb": submission_plan.resource_request.memory_gb,
                "walltime": submission_plan.resource_request.walltime,
            }
        )
        safety_review = self._build_safety_review_for_scheduler(
            run_context=run_context,
            mode=mode,
            command=command,
            dry_run_completed=dry_run_completed,
            resources=gate_resources,
            stage_id=RuntimeStage.STAGE_06_RESOURCE_AND_SAFETY_GATE.value,
            target_paths=[
                submission_plan.paths.script_path,
                submission_plan.paths.wrapper_path,
                submission_plan.paths.stdout_path,
                submission_plan.paths.stderr_path,
            ],
            manual_approval=envelope.approval,
            outbound_payload=envelope.outbound_payload,
            concurrent_jobs=submission_plan.resource_request.tasks,
        )
        if validation_report is not None and not validation_report.valid:
            safety_review = self._apply_validation_warnings_to_safety_review(
                safety_review=safety_review,
                validation_report=validation_report,
            )
        if submission_plan.quota_gate_status == "blocked":
            safety_review = self._apply_submission_quota_block_to_safety_review(
                safety_review=safety_review,
                quota_reasons=submission_plan.quota_gate_reasons,
                quota_usage=submission_plan.quota_usage,
            )
        if mode == "submit" and safety_review.decision == GateDecision.BLOCK:
            raise PermissionError(
                "Safety gate rejected real submit; run dry-run and complete manual confirmation requirements first."
            )
        runtime_trace.advance(RuntimeStage.STAGE_07_EXECUTION.value)
        job_handle = submission_plan.job_handle
        effective_execute_submit = execute_submit and resolved_execution_mode not in {
            ExecutionMode.LOCAL_PREVIEW,
            ExecutionMode.MANUAL_SBASE,
        }
        if effective_execute_submit:
            if safety_review.decision != GateDecision.PASS:
                raise PermissionError(
                    "Safety gate rejected real submit; run dry-run and complete manual confirmation requirements first."
                )
            job_handle = execution_scheduler.submit(
                working_directory=execution_working_directory,
                resources=resources,
                command=command,
                task_id=run_context.task_id,
                run_id=run_context.run_id,
                atomic_tools=atomic_tools,
            )
        remote_check_summary = (
            self.remote_check(
                execution_mode=resolved_execution_mode,
                remote_profile_name=resolved_profile_name,
            )
            if resolved_execution_mode in {
                ExecutionMode.SSH_SHELL_TRUSTED,
                ExecutionMode.SSH_SLURM_TRUSTED,
                ExecutionMode.MANUAL_SBASE,
            }
            else None
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
        runtime_trace.advance(RuntimeStage.STAGE_08_ARTIFACT_AND_REPORT.value)
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
            runtime_lifecycle=runtime_trace.to_contract(),
        )
        runtime_trace.advance(RuntimeStage.STAGE_09_AUDIT_AND_MEMORY.value)
        runtime_trace.advance(RuntimeStage.COMPLETED.value)
        if audit_record_path:
            artifact_index["results"] = self._stable_unique(
                [*artifact_index.get("results", []), audit_record_path]
            )
        run_record = self._memory_coordinator.record_execution_closure(
            task_id=run_context.task_id,
            run_id=run_context.run_id,
            session_id=run_context.session_id,
            project_id=None,
            working_directory=submission_plan.paths.working_directory,
            domain=plan.domain,
            input_summary=request_text,
            planning_summary=plan.summary,
            submission_command=submit_command_text,
            job_id=job_handle.job_id,
            log_paths=[submission_plan.paths.stdout_path, submission_plan.paths.stderr_path],
            manual_confirmation_records=safety_review.human_confirmation_conditions,
            approval_records=[safety_review.approval_record] if safety_review.approval_record else None,
            artifact_index=artifact_index,
            report_summary=report_summary,
            audit_path=audit_record_path,
            parameter_snapshot=self._parameter_snapshot_from_plan(plan),
        )
        run_state = RunState(
            task_id=run_context.task_id,
            run_id=run_context.run_id,
            execution_mode=resolved_execution_mode,
            remote_profile_name=resolved_profile_name,
            scheduler=self._scheduler_kind_for_execution_mode(resolved_execution_mode),
            working_directory=submission_plan.paths.working_directory,
            current_stage=RuntimeStage.STAGE_07_EXECUTION.value,
            status=job_handle.state,
            job_id=job_handle.job_id,
            auto_continue=bool(resolved_auto_continue),
            next_action=(
                "resource cap blocked; adjust request or configured caps before submit"
                if submission_plan.quota_gate_status == "blocked"
                else (
                    "watch scheduler state"
                    if job_handle.state != JobState.DRAFT
                    else "submit or manual SBASE submission pending"
                )
            ),
        ).with_stage(
            stage_id=RuntimeStage.STAGE_07_EXECUTION.value,
            status="submitted" if effective_execute_submit and job_handle.state != JobState.DRAFT else "planned",
            message=f"execution_mode={resolved_execution_mode.value}",
            job_id=job_handle.job_id,
            run_status=job_handle.state,
            auto_continue_ready=False,
        )
        run_state_path = self._run_state_store.save(run_state)
        run_state = run_state.model_copy(update={"state_path": str(run_state_path)})
        if watch and effective_execute_submit and job_handle.state != JobState.DRAFT:
            run_state = self._trusted_controller.watch_run(
                task_id=run_context.task_id,
                run_id=run_context.run_id,
                scheduler=execution_scheduler,
            )
            if run_state.state_path:
                run_state_path = Path(run_state.state_path)
        explanation_layer = self._build_explanation_layer(
            domain=plan.domain.value,
            selected_blueprint=plan.pipeline_spec.name if plan.pipeline_spec is not None else "bioinformatics_pipeline",
            blueprint_reason=(
                f"selected blueprint `{plan.pipeline_spec.name if plan.pipeline_spec is not None else 'unknown'}` "
                f"with key `{plan.pipeline_spec.blueprint_key if plan.pipeline_spec is not None else 'none'}` "
                "based on intent/scope and pipeline contract."
            ),
            gate_decision=safety_review.decision.value,
            gate_reason=(
                f"gate_status={safety_review.ready_for_gate.value}; "
                f"manual_confirmations={len(safety_review.human_confirmation_conditions)}; "
                f"quota_status={safety_review.quota_gate.get('status', 'unknown') if isinstance(safety_review.quota_gate, dict) else 'unknown'}."
            ),
            repair_recommendation=(
                safety_review.rollback_or_remediation[0]
                if safety_review.rollback_or_remediation
                else "Inspect stderr/logs and apply failure_recovery checklist before retry."
            ),
            repair_basis=[
                f"failure_recovery_steps={len(submission_plan.failure_recovery)}",
                f"report_generator_status={report_generator_status}",
                f"audit_record={'present' if bool(audit_record_path) else 'missing'}",
            ],
        )
        return SubmissionPreview(
            run_context=run_context,
            mode=mode,
            execution_mode=resolved_execution_mode,
            remote_profile_name=resolved_profile_name,
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
            gate_status=(
                submission_plan.ready_for_gate
                if submission_plan.quota_gate_status == "blocked"
                else safety_review.ready_for_gate.value
            ),
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
            input_bundle=plan.pipeline_spec.input_bundle if plan.pipeline_spec is not None else None,
            input_validation=validation_report,
            runtime_lifecycle=runtime_trace.to_contract(),
            explanation_layer=explanation_layer,
            manual_submit_card=manual_submit_card,
            remote_check_summary=remote_check_summary,
            run_state_path=str(run_state_path),
            run_state=run_state,
        )

    def _build_non_bio_submission_preview(
        self,
        *,
        run_context: RunContext,
        mode: str,
        request_text: str | None = None,
        plan_summary: str | None = None,
        domain: TaskDomain = TaskDomain.KNOWLEDGE,
        input_bundle: InputBundle | None = None,
        validation_report: ValidationReport | None = None,
        runtime_lifecycle: dict[str, object] | None = None,
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
            runtime_lifecycle=runtime_lifecycle,
        )
        run_record = self._memory_coordinator.record_execution_closure(
            task_id=run_context.task_id,
            run_id=run_context.run_id,
            session_id=run_context.session_id,
            project_id=None,
            working_directory=run_context.working_directory or self._settings.work_root,
            domain=domain,
            input_summary=request_text or "non-bio lightweight branch",
            planning_summary=plan_summary or "non-bio lightweight plan",
            submission_command="scheduler_skipped",
            job_id=f"SKIPPED-NONBIO-{run_context.task_id}-{run_context.run_id}",
            log_paths=[],
            manual_confirmation_records=[],
            approval_records=None,
            artifact_index=artifact_index,
            report_summary=report_summary,
            audit_path=audit_record_path,
            parameter_snapshot={},
        )
        explanation_layer = self._build_explanation_layer(
            domain=domain.value,
            selected_blueprint=f"{domain.value}_lightweight",
            blueprint_reason="non-bio intent routed to lightweight branch by intent+scope policy.",
            gate_decision="pass",
            gate_reason="non-bio branch explicitly forbids cluster submit/poll and keeps execution skipped.",
            repair_recommendation=(
                "Refine retrieval scope and answer blueprint; do not use scheduler recovery on non-bio branch."
            ),
            repair_basis=[
                "cluster_execution_enabled=false",
                "scheduler_script_generation=skipped",
            ],
        )
        return SubmissionPreview(
            run_context=run_context,
            mode=mode,
            execution_mode=ExecutionMode.LOCAL_PREVIEW,
            remote_profile_name=None,
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
            input_bundle=input_bundle,
            input_validation=validation_report,
            runtime_lifecycle=runtime_lifecycle,
            explanation_layer=explanation_layer,
            run_state_path=None,
        )

    def _resolve_execution_mode(self, execution_mode: ExecutionMode | str | None) -> ExecutionMode:
        if execution_mode is None:
            return self._settings.execution_mode
        if isinstance(execution_mode, ExecutionMode):
            return execution_mode
        return ExecutionMode(str(execution_mode))

    def _execution_working_directory(
        self,
        *,
        run_context: RunContext,
        execution_mode: ExecutionMode,
        remote_profile_name: str | None,
    ) -> str:
        if execution_mode == ExecutionMode.SSH_SHELL_TRUSTED:
            return self._settings.remote_execution_profile(remote_profile_name).work_root
        return run_context.working_directory or self._settings.work_root

    def _scheduler_kind_for_execution_mode(self, execution_mode: ExecutionMode) -> SchedulerKind:
        if execution_mode == ExecutionMode.SSH_SHELL_TRUSTED:
            return SchedulerKind.SHELL
        return self._settings.scheduler_type

    def _build_safety_review_for_scheduler(
        self,
        *,
        run_context: RunContext,
        mode: str,
        command: list[str],
        dry_run_completed: bool,
        resources,
        stage_id: str,
        target_paths: list[str],
        manual_approval: dict[str, object] | None = None,
        outbound_payload: dict[str, object] | None = None,
        concurrent_jobs: int = 1,
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
                stage_id=stage_id,
                action_name=action_name,
                target_paths=target_paths,
                command_preview=" ".join(command),
                scheduler_dry_run_done=dry_run_completed,
                cost_estimated=True,
                rollback_plan_ready=True,
                cpu_cores=resources.cpus,
                memory_gb=resources.memory_gb,
                walltime_hours=self._walltime_to_hours(resources.walltime),
                job_count=max(1, concurrent_jobs),
                current_active_jobs=self._settings.scheduler_current_active_jobs,
                quota_cpu_hours_limit=self._settings.scheduler_quota_cpu_hours_limit,
                quota_memory_gb_limit=self._settings.scheduler_quota_memory_gb_limit,
                quota_max_concurrent_jobs=self._settings.scheduler_quota_max_concurrent_jobs,
                manual_approval=manual_approval,
                outbound_payload=outbound_payload,
                outbound_allowed_fields=self._settings.allow_cloud_fields,
                outbound_policy_enforced=self._settings.outbound_policy_enforced,
                cloud_llm=bool(outbound_payload),
            )
        )

    def _apply_validation_warnings_to_safety_review(
        self,
        *,
        safety_review: SafetyGateResult,
        validation_report: ValidationReport,
    ) -> SafetyGateResult:
        blocking_messages = [
            issue.message
            for issue in validation_report.issues
            if issue.blocking
        ]
        if not blocking_messages:
            return safety_review
        return safety_review.model_copy(
            update={
                "human_confirmation_conditions": self._stable_unique(
                    [
                        *safety_review.human_confirmation_conditions,
                        "Resolve blocking InputBundle validation issues before real submit.",
                    ]
                ),
                "circuit_break_conditions": self._stable_unique(
                    [
                        *safety_review.circuit_break_conditions,
                        *[f"input_validation:{message}" for message in blocking_messages],
                    ]
                ),
                "rollback_or_remediation": self._stable_unique(
                    [
                        *safety_review.rollback_or_remediation,
                        *validation_report.recommended_next_actions,
                    ]
                ),
            }
        )

    def _apply_submission_quota_block_to_safety_review(
        self,
        *,
        safety_review: SafetyGateResult,
        quota_reasons: list[str],
        quota_usage: dict[str, float | int],
    ) -> SafetyGateResult:
        quota_conditions = [f"quota:{reason}" for reason in quota_reasons]
        return safety_review.model_copy(
            update={
                "ready_for_gate": GateStage.BLOCKED,
                "decision": GateDecision.BLOCK,
                "requires_human_confirmation": True,
                "human_confirmation_conditions": self._stable_unique(
                    [
                        *safety_review.human_confirmation_conditions,
                        "Requested resources exceed trusted remote caps; adjust request or configured caps before submit.",
                    ]
                ),
                "circuit_break_conditions": self._stable_unique(
                    [
                        *safety_review.circuit_break_conditions,
                        *quota_conditions,
                    ]
                ),
                "quota_gate": {
                    **safety_review.quota_gate,
                    "status": "blocked",
                    "reasons": list(quota_reasons),
                    "usage": dict(quota_usage),
                },
                "reasons": self._stable_unique(
                    [
                        *safety_review.reasons,
                        "remote_shell_resource_cap_blocked",
                        *quota_conditions,
                    ]
                ),
                "rollback_or_remediation": self._stable_unique(
                    [
                        *safety_review.rollback_or_remediation,
                        "Lower CPU/memory/walltime request or raise the configured server caps after operator review.",
                    ]
                ),
            }
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
        script_path = Path(__file__).resolve().parents[2] / "scripts" / "reporting_audit" / "run_report_generator.sh"
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
                encoding="utf-8",
                errors="replace",
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

    def _build_explanation_layer(
        self,
        *,
        domain: str,
        selected_blueprint: str,
        blueprint_reason: str,
        gate_decision: str,
        gate_reason: str,
        repair_recommendation: str,
        repair_basis: list[str] | None = None,
    ) -> dict[str, object]:
        basis = [item for item in (repair_basis or []) if str(item).strip()]
        return {
            "schema_version": "explanation_layer.v1",
            "why_blueprint": {
                "domain": domain,
                "selected_blueprint": selected_blueprint,
                "reason": blueprint_reason,
            },
            "why_gate": {
                "decision": gate_decision,
                "reason": gate_reason,
            },
            "why_repair": {
                "recommendation": repair_recommendation,
                "basis": basis,
            },
            "summary": (
                f"blueprint={selected_blueprint}; gate={gate_decision}; "
                f"repair={repair_recommendation[:120]}"
            ),
        }

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

    def _merge_artifact_index(
        self,
        existing: dict[str, object] | None,
        incoming: dict[str, object] | None,
    ) -> dict[str, list[str]]:
        merged: dict[str, list[str]] = {}
        for payload in (existing or {}, incoming or {}):
            if not isinstance(payload, dict):
                continue
            for key, values in payload.items():
                if not isinstance(values, list):
                    continue
                bucket = merged.setdefault(str(key), [])
                for value in values:
                    normalized = str(value).strip()
                    if normalized and normalized not in bucket:
                        bucket.append(normalized)
        return merged

    def _resolve_working_directory_from_paths(self, *, paths: list[str]) -> str | None:
        for raw_path in paths:
            normalized = str(raw_path).strip()
            if not normalized:
                continue
            candidate = Path(normalized)
            if candidate.is_file():
                return str(candidate.parent.parent if candidate.parent.name == "logs" else candidate.parent)
            if candidate.is_dir():
                return str(candidate)
        return None

    def _resolve_audit_bundle_output_path(
        self,
        *,
        run_context: RunContext,
        output_path: str | None,
    ) -> Path:
        if output_path:
            candidate = Path(output_path)
            if candidate.suffix.lower() == ".zip":
                return candidate
            return candidate / f"{run_context.task_id}__{run_context.run_id}.zip"

        primary_root = Path(run_context.working_directory or self._settings.work_root) / "results" / "audit_bundles"
        try:
            primary_root.mkdir(parents=True, exist_ok=True)
            return primary_root / f"{run_context.task_id}__{run_context.run_id}.zip"
        except OSError:
            fallback_root = Path.cwd() / "results" / "audit_bundles"
            fallback_root.mkdir(parents=True, exist_ok=True)
            return fallback_root / f"{run_context.task_id}__{run_context.run_id}.zip"

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
        runtime_lifecycle: dict[str, object] | None = None,
    ) -> str | None:
        event = AuditEvent(
            task_id=run_context.task_id,
            run_id=run_context.run_id,
            event_type="execution_closure",
            stage_id="stage_09_audit_and_memory",
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
                "runtime_lifecycle": runtime_lifecycle or {},
            },
            traceability={
                "submission_command": submission_command,
                "job_id": job_id,
                "log_paths": [path for path in log_paths if path],
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

    @staticmethod
    def _parameter_snapshot_from_plan(plan: TaskPlan) -> dict[str, str]:
        snapshot: dict[str, str] = {
            "domain": plan.domain.value,
            "workflow_name": plan.workflow_name,
        }
        if plan.pipeline_spec is not None:
            snapshot["blueprint_name"] = plan.pipeline_spec.name
            snapshot["blueprint_key"] = plan.pipeline_spec.blueprint_key or "none"
            snapshot["analysis_targets"] = ",".join(plan.pipeline_spec.analysis_targets) or "none"
            snapshot["atomic_algorithms"] = ",".join(plan.pipeline_spec.atomic_algorithms) or "none"
            if plan.pipeline_spec.input_bundle is not None:
                snapshot["input.species"] = plan.pipeline_spec.input_bundle.species or "unknown"
                snapshot["input.cohort"] = plan.pipeline_spec.input_bundle.cohort_name or "unknown"
        if plan.resource_estimate is not None:
            snapshot["resource.partition"] = plan.resource_estimate.partition or "none"
            snapshot["resource.cpus"] = str(plan.resource_estimate.cpus)
            snapshot["resource.memory_gb"] = str(plan.resource_estimate.memory_gb)
            snapshot["resource.walltime"] = plan.resource_estimate.walltime
        return snapshot

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
