"""Safety policy for trusted remote automation and low-risk repair."""

from __future__ import annotations

from pydantic import BaseModel

from contracts.common import AutoRepairLevel


class AutomationActionRequest(BaseModel):
    """One proposed automation action to review before execution."""

    action: str
    requested_cpus: int = 0
    requested_memory_gb: int = 0
    repeated_failures: int = 0
    path_within_work_root: bool = True
    known_tool: bool = True


class AutomationPolicyDecision(BaseModel):
    """Decision returned by TrustedAutomationPolicy."""

    allowed: bool
    reason: str
    requires_human_confirmation: bool = False


class TrustedAutomationPolicy:
    """Permit narrow low-risk repairs and block destructive or boundary-crossing actions."""

    _low_risk_actions = {
        "create_log_dir",
        "retry_transient_scheduler_failure",
        "generate_safe_sidecar",
        "continue_after_artifact_validation",
    }
    _trusted_actions = _low_risk_actions | {"increase_resources"}
    _blocked_actions = {
        "delete_files",
        "overwrite_results",
        "change_sample_filtering",
        "copy_data_off_cluster",
        "unknown_tool_path",
        "path_outside_work_root",
    }

    def __init__(
        self,
        *,
        level: AutoRepairLevel = AutoRepairLevel.LOW_RISK,
        cpu_cap: int = 64,
        memory_gb_cap: int = 256,
        max_repeated_failures: int = 2,
    ) -> None:
        self.level = level
        self.cpu_cap = max(1, int(cpu_cap))
        self.memory_gb_cap = max(1, int(memory_gb_cap))
        self.max_repeated_failures = max(1, int(max_repeated_failures))

    def review(self, request: AutomationActionRequest) -> AutomationPolicyDecision:
        action = request.action.strip()
        if self.level == AutoRepairLevel.OFF:
            return AutomationPolicyDecision(
                allowed=False,
                reason="automation_disabled",
                requires_human_confirmation=True,
            )
        if action in self._blocked_actions:
            return AutomationPolicyDecision(
                allowed=False,
                reason="blocked_high_risk_action",
                requires_human_confirmation=True,
            )
        if not request.path_within_work_root:
            return AutomationPolicyDecision(
                allowed=False,
                reason="path_boundary_violation",
                requires_human_confirmation=True,
            )
        if not request.known_tool:
            return AutomationPolicyDecision(
                allowed=False,
                reason="unknown_tool_path",
                requires_human_confirmation=True,
            )
        if request.repeated_failures > self.max_repeated_failures:
            return AutomationPolicyDecision(
                allowed=False,
                reason="repeated_failure_limit_exceeded",
                requires_human_confirmation=True,
            )
        if request.requested_cpus > self.cpu_cap or request.requested_memory_gb > self.memory_gb_cap:
            return AutomationPolicyDecision(
                allowed=False,
                reason="resource_cap_exceeded",
                requires_human_confirmation=True,
            )
        if action in self._low_risk_actions:
            return AutomationPolicyDecision(allowed=True, reason="low_risk_action_allowed")
        if self.level == AutoRepairLevel.TRUSTED and action in self._trusted_actions:
            return AutomationPolicyDecision(allowed=True, reason="trusted_action_allowed")
        return AutomationPolicyDecision(
            allowed=False,
            reason="action_not_in_automation_allowlist",
            requires_human_confirmation=True,
        )
