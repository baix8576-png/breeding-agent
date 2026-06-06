from __future__ import annotations

from contracts.common import AutoRepairLevel
from safety.automation_policy import AutomationActionRequest, TrustedAutomationPolicy


def test_trusted_automation_policy_allows_low_risk_repairs() -> None:
    policy = TrustedAutomationPolicy(
        level=AutoRepairLevel.LOW_RISK,
        cpu_cap=32,
        memory_gb_cap=128,
        max_repeated_failures=2,
    )

    decision = policy.review(
        AutomationActionRequest(
            action="create_log_dir",
            requested_cpus=4,
            requested_memory_gb=16,
        )
    )

    assert decision.allowed is True
    assert decision.requires_human_confirmation is False
    assert decision.reason == "low_risk_action_allowed"


def test_trusted_automation_policy_blocks_destructive_or_boundary_crossing_repairs() -> None:
    policy = TrustedAutomationPolicy(level=AutoRepairLevel.TRUSTED, cpu_cap=32, memory_gb_cap=128)

    delete_decision = policy.review(AutomationActionRequest(action="delete_files"))
    quota_decision = policy.review(
        AutomationActionRequest(
            action="increase_resources",
            requested_cpus=64,
            requested_memory_gb=256,
        )
    )
    egress_decision = policy.review(AutomationActionRequest(action="copy_data_off_cluster"))

    assert delete_decision.allowed is False
    assert delete_decision.requires_human_confirmation is True
    assert quota_decision.allowed is False
    assert "resource_cap_exceeded" in quota_decision.reason
    assert egress_decision.allowed is False
    assert egress_decision.reason == "blocked_high_risk_action"
