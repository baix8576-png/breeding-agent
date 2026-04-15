"""Execution preflight reviews for high-risk actions."""

from __future__ import annotations

import re
from enum import Enum

from pydantic import BaseModel, Field

from contracts.common import GateDecision, RiskLevel


class RiskCategory(str, Enum):
    FILE_WRITE = "file_write"
    RAW_DATA = "raw_data_boundary"
    CLOUD_EGRESS = "cloud_egress"
    CREDENTIAL = "credential_access"
    SCHEDULER = "scheduler_resources"
    COMMAND = "dangerous_command"
    RESULT = "result_integrity"


class CheckStatus(str, Enum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    PENDING = "pending"


class GateStage(str, Enum):
    BLOCKED = "blocked"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    READY = "ready"


class PreflightCheck(BaseModel):
    name: str
    status: CheckStatus
    detail: str


class SafetyReviewContext(BaseModel):
    """Safety-only review context. Shared schema still belongs in src/contracts."""

    task_id: str = "unknown-task"
    run_id: str = "unknown-run"
    action_name: str
    target_paths: list[str] = Field(default_factory=list)
    command_preview: str | None = None
    touches_raw_data: bool = False
    overwrite_existing: bool = False
    delete_requested: bool = False
    cross_directory_write: bool = False
    bulk_recompute: bool = False
    external_network: bool = False
    cloud_llm: bool = False
    credential_access: bool = False
    scheduler_dry_run_done: bool = False
    network_approved: bool = False
    credential_source_declared: bool = False
    cost_estimated: bool = False
    rollback_plan_ready: bool = False
    cpu_cores: int | None = None
    memory_gb: int | None = None
    walltime_hours: int | None = None
    job_count: int | None = None


class SafetyGateResult(BaseModel):
    task_id: str
    run_id: str
    ready_for_gate: GateStage
    risk_level: RiskLevel
    decision: GateDecision
    risk_categories: list[RiskCategory] = Field(default_factory=list)
    requires_human_confirmation: bool = False
    human_confirmation_conditions: list[str] = Field(default_factory=list)
    preflight_checks: list[PreflightCheck] = Field(default_factory=list)
    impact_scope: list[str] = Field(default_factory=list)
    dry_run_required: bool = False
    cost_or_quota_impact: str | None = None
    circuit_break_conditions: list[str] = Field(default_factory=list)
    rollback_or_remediation: list[str] = Field(default_factory=list)
    audit_recommendations: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    follow_up_actions: list[str] = Field(default_factory=list)


class SafetyGateService:
    """Evaluate execution risk without performing destructive actions."""

    _blocked_actions = {"exfiltrate_raw_data", "upload_vcf", "upload_bam", "upload_fastq", "upload_fasta"}
    _manual_actions = {
        "overwrite_results",
        "delete_files",
        "requeue_failed_job",
        "cross_directory_write",
        "abnormal_resource_request",
        "bulk_recompute",
    }
    _dangerous_patterns = (
        re.compile(r"\brm\s+-rf\b"),
        re.compile(r"\bRemove-Item\b.*\b-Recurse\b", re.IGNORECASE),
        re.compile(r"\bmkfs(\.| )"),
        re.compile(r"\bdd\s+if="),
    )

    def review(
        self,
        action_name: str | None = None,
        context: SafetyReviewContext | None = None,
    ) -> SafetyGateResult:
        review_context = context or SafetyReviewContext(action_name=action_name or "")
        destructive_write = any(
            (
                review_context.overwrite_existing,
                review_context.delete_requested,
                review_context.cross_directory_write,
                review_context.bulk_recompute,
            )
        )
        dry_run_required = destructive_write or self._is_high_resource(review_context) or (review_context.job_count or 0) > 1

        checks = [
            self._check_task_keys(review_context),
            self._check_target_scope(review_context, destructive_write),
            self._check_raw_data_boundary(review_context),
            self._check_dangerous_command(review_context),
            self._check_dry_run(review_context, dry_run_required),
            self._check_network(review_context),
            self._check_credentials(review_context),
            self._check_cost(review_context),
            self._check_rollback(review_context),
        ]
        blocking = [check.detail for check in checks if check.status == CheckStatus.FAIL]
        pending = [check.detail for check in checks if check.status == CheckStatus.PENDING]
        manual_conditions = self._manual_conditions(review_context)
        if review_context.action_name in self._blocked_actions:
            blocking.append("Action crosses the local genomic data boundary.")
        if review_context.action_name in self._manual_actions:
            manual_conditions.append("Action is classified as manual approval only.")

        if blocking:
            stage = GateStage.BLOCKED
            decision = GateDecision.BLOCK
            risk_level = RiskLevel.HIGH
            reasons = blocking
            follow_up = [
                "Stop automation before command generation or submission.",
                "Replace the operation with a non-destructive path or resolve failed checks.",
            ]
        elif manual_conditions or pending:
            stage = GateStage.AWAITING_CONFIRMATION
            decision = GateDecision.REQUIRE_CONFIRMATION
            risk_level = RiskLevel.MANUAL_APPROVAL if manual_conditions else RiskLevel.MEDIUM
            reasons = pending or ["Manual confirmation is required before execution."]
            follow_up = [
                "Show impact scope, cost, and preflight status to the operator.",
                "Collect explicit approval before resuming execution.",
            ]
        else:
            stage = GateStage.READY
            decision = GateDecision.PASS
            risk_level = RiskLevel.LOW
            reasons = ["Preflight checks passed for the current non-destructive scope."]
            follow_up = ["Proceed with audit logging and conservative execution defaults."]

        return SafetyGateResult(
            task_id=review_context.task_id,
            run_id=review_context.run_id,
            ready_for_gate=stage,
            risk_level=risk_level,
            decision=decision,
            risk_categories=self._categorize(review_context),
            requires_human_confirmation=bool(manual_conditions),
            human_confirmation_conditions=manual_conditions,
            preflight_checks=checks,
            impact_scope=self._impact_scope(review_context),
            dry_run_required=dry_run_required,
            cost_or_quota_impact=self._cost_impact(review_context),
            circuit_break_conditions=self._breaker_conditions(review_context, dry_run_required),
            rollback_or_remediation=self._rollback_guidance(review_context),
            audit_recommendations=self._audit_recommendations(review_context, dry_run_required),
            reasons=reasons,
            follow_up_actions=follow_up,
        )

    def _check_task_keys(self, context: SafetyReviewContext) -> PreflightCheck:
        if context.task_id == "unknown-task" or context.run_id == "unknown-run":
            return PreflightCheck(
                name="task_keys",
                status=CheckStatus.WARN,
                detail="task_id/run_id should be passed end-to-end.",
            )
        return PreflightCheck(name="task_keys", status=CheckStatus.PASS, detail="Correlation keys are present.")

    def _check_target_scope(self, context: SafetyReviewContext, destructive_write: bool) -> PreflightCheck:
        if destructive_write and not context.target_paths:
            return PreflightCheck(
                name="target_scope",
                status=CheckStatus.FAIL,
                detail="Target paths must be declared before destructive or bulk write operations.",
            )
        if context.cross_directory_write:
            return PreflightCheck(
                name="target_scope",
                status=CheckStatus.PENDING,
                detail="Cross-directory write requires explicit scope confirmation.",
            )
        return PreflightCheck(name="target_scope", status=CheckStatus.PASS, detail="Target scope is acceptable.")

    def _check_raw_data_boundary(self, context: SafetyReviewContext) -> PreflightCheck:
        if context.touches_raw_data and (context.overwrite_existing or context.delete_requested):
            return PreflightCheck(
                name="raw_data_boundary",
                status=CheckStatus.FAIL,
                detail="Raw genomic data must not be deleted or overwritten.",
            )
        if context.touches_raw_data:
            return PreflightCheck(
                name="raw_data_boundary",
                status=CheckStatus.WARN,
                detail="Raw data is in scope; only read-only handling should continue.",
            )
        return PreflightCheck(name="raw_data_boundary", status=CheckStatus.PASS, detail="Raw-data boundary respected.")

    def _check_dangerous_command(self, context: SafetyReviewContext) -> PreflightCheck:
        if context.command_preview and any(pattern.search(context.command_preview) for pattern in self._dangerous_patterns):
            return PreflightCheck(
                name="command_preview",
                status=CheckStatus.FAIL,
                detail="Command preview matches a blocked destructive pattern.",
            )
        if context.command_preview:
            return PreflightCheck(name="command_preview", status=CheckStatus.PASS, detail="Command preview is clean.")
        return PreflightCheck(
            name="command_preview",
            status=CheckStatus.WARN,
            detail="No command preview supplied; command-level screening is incomplete.",
        )

    def _check_dry_run(self, context: SafetyReviewContext, dry_run_required: bool) -> PreflightCheck:
        if dry_run_required and not context.scheduler_dry_run_done:
            return PreflightCheck(name="dry_run", status=CheckStatus.PENDING, detail="Dry-run is required before high-impact execution.")
        return PreflightCheck(name="dry_run", status=CheckStatus.PASS, detail="Dry-run requirement is satisfied.")

    def _check_network(self, context: SafetyReviewContext) -> PreflightCheck:
        if (context.external_network or context.cloud_llm) and not context.network_approved:
            return PreflightCheck(name="network_scope", status=CheckStatus.PENDING, detail="External or cloud access requires explicit approval.")
        return PreflightCheck(name="network_scope", status=CheckStatus.PASS, detail="Network scope is acceptable.")

    def _check_credentials(self, context: SafetyReviewContext) -> PreflightCheck:
        if context.credential_access and not context.credential_source_declared:
            return PreflightCheck(name="credential_scope", status=CheckStatus.FAIL, detail="Credential access requires a declared source and approval path.")
        return PreflightCheck(name="credential_scope", status=CheckStatus.PASS, detail="Credential scope is acceptable.")

    def _check_cost(self, context: SafetyReviewContext) -> PreflightCheck:
        if (context.cloud_llm or self._is_high_resource(context)) and not context.cost_estimated:
            return PreflightCheck(name="cost_estimate", status=CheckStatus.PENDING, detail="Cloud cost or cluster quota impact must be declared.")
        return PreflightCheck(name="cost_estimate", status=CheckStatus.PASS, detail="Cost or quota impact is known.")

    def _check_rollback(self, context: SafetyReviewContext) -> PreflightCheck:
        if (context.overwrite_existing or context.delete_requested) and not context.rollback_plan_ready:
            return PreflightCheck(name="rollback_plan", status=CheckStatus.FAIL, detail="Overwrite or delete requests require a rollback or backup plan.")
        return PreflightCheck(name="rollback_plan", status=CheckStatus.PASS, detail="Rollback requirement is satisfied.")

    def _categorize(self, context: SafetyReviewContext) -> list[RiskCategory]:
        categories: set[RiskCategory] = set()
        if any((context.overwrite_existing, context.delete_requested, context.cross_directory_write, context.bulk_recompute)):
            categories.add(RiskCategory.FILE_WRITE)
        if context.touches_raw_data:
            categories.add(RiskCategory.RAW_DATA)
        if context.external_network or context.cloud_llm:
            categories.add(RiskCategory.CLOUD_EGRESS)
        if context.credential_access:
            categories.add(RiskCategory.CREDENTIAL)
        if self._is_high_resource(context):
            categories.add(RiskCategory.SCHEDULER)
        if context.command_preview:
            categories.add(RiskCategory.COMMAND)
        if context.overwrite_existing:
            categories.add(RiskCategory.RESULT)
        return sorted(categories, key=lambda item: item.value)

    def _manual_conditions(self, context: SafetyReviewContext) -> list[str]:
        conditions: list[str] = []
        if context.overwrite_existing:
            conditions.append("Overwriting existing results requires operator confirmation.")
        if context.delete_requested:
            conditions.append("Delete requests require operator confirmation.")
        if context.cross_directory_write:
            conditions.append("Cross-directory writes require scope confirmation.")
        if context.bulk_recompute:
            conditions.append("Bulk recompute requires impact confirmation.")
        if context.external_network or context.cloud_llm:
            conditions.append("External/cloud access requires approval against egress policy.")
        if context.credential_access:
            conditions.append("Credential access requires explicit approval.")
        if self._is_high_resource(context):
            conditions.append("Requested scheduler resources exceed conservative defaults.")
        return conditions

    def _breaker_conditions(self, context: SafetyReviewContext, dry_run_required: bool) -> list[str]:
        conditions: list[str] = []
        if context.touches_raw_data and (context.overwrite_existing or context.delete_requested):
            conditions.append("Attempted destructive operation on protected raw data.")
        if dry_run_required and not context.scheduler_dry_run_done:
            conditions.append("Required dry-run missing for high-impact execution.")
        if context.credential_access and not context.credential_source_declared:
            conditions.append("Credential access lacks declared source.")
        if (context.external_network or context.cloud_llm) and not context.network_approved:
            conditions.append("Outbound access lacks explicit approval.")
        if context.command_preview and any(pattern.search(context.command_preview) for pattern in self._dangerous_patterns):
            conditions.append("Command preview contains a blocked destructive pattern.")
        return conditions

    def _impact_scope(self, context: SafetyReviewContext) -> list[str]:
        scope = [f"action:{context.action_name}"]
        scope.extend(f"path:{path}" for path in context.target_paths)
        if context.job_count:
            scope.append(f"jobs:{context.job_count}")
        return scope

    def _cost_impact(self, context: SafetyReviewContext) -> str | None:
        messages: list[str] = []
        if context.cloud_llm:
            messages.append("Cloud LLM request must remain within approved text-only payload fields.")
        if self._is_high_resource(context):
            messages.append(
                f"High resource request: cpu={context.cpu_cores or 0}, memory_gb={context.memory_gb or 0}, "
                f"walltime_h={context.walltime_hours or 0}, jobs={context.job_count or 0}."
            )
        return " ".join(messages) or None

    def _rollback_guidance(self, context: SafetyReviewContext) -> list[str]:
        guidance: list[str] = []
        if context.overwrite_existing:
            guidance.append("Prefer a new versioned output directory instead of in-place overwrite.")
        if context.delete_requested:
            guidance.append("Prefer quarantine/archive over direct deletion.")
        if context.cloud_llm:
            guidance.append("Send only prompt, sanitized_error_log, tool_summary, software_version, parameter_schema.")
        if not guidance:
            guidance.append("Keep audit records even for low-risk read-only actions.")
        return guidance

    def _audit_recommendations(self, context: SafetyReviewContext, dry_run_required: bool) -> list[str]:
        audit = [
            "Record task_id/run_id, action_name, decision, and reasons.",
            "Record declared target paths and impact scope.",
        ]
        if dry_run_required:
            audit.append("Record dry-run artifact or dry-run summary before execution.")
        if context.cloud_llm:
            audit.append("Record outbound field list and sanitization summary, not raw payload content.")
        return audit

    def _is_high_resource(self, context: SafetyReviewContext) -> bool:
        return (
            (context.cpu_cores or 0) >= 64
            or (context.memory_gb or 0) >= 256
            or (context.walltime_hours or 0) >= 48
            or (context.job_count or 0) >= 200
        )
