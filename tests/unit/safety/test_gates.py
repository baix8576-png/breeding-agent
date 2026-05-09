from __future__ import annotations

from safety.gates import SafetyGateService, SafetyReviewContext


def test_safety_gate_returns_awaiting_confirmation_for_prechecked_overwrite() -> None:
    service = SafetyGateService()

    result = service.review(
        context=SafetyReviewContext(
            task_id="task-safety-001",
            run_id="run-safety-001",
            action_name="overwrite_results",
            target_paths=["/cluster/work/output"],
            overwrite_existing=True,
            scheduler_dry_run_done=True,
            rollback_plan_ready=True,
        )
    )

    assert result.task_id == "task-safety-001"
    assert result.run_id == "run-safety-001"
    assert result.ready_for_gate.value == "awaiting_confirmation"
    assert result.decision.value == "require_confirmation"
    assert result.risk_level.value == "manual_approval"
    assert result.dry_run_required is True
    assert result.requires_human_confirmation is True
    assert "Overwriting existing results requires operator confirmation." in result.human_confirmation_conditions


def test_safety_gate_blocks_raw_data_delete_requests() -> None:
    service = SafetyGateService()

    result = service.review(
        context=SafetyReviewContext(
            task_id="task-safety-002",
            run_id="run-safety-002",
            action_name="delete_files",
            target_paths=["/cluster/raw/sheep.vcf.gz"],
            touches_raw_data=True,
            delete_requested=True,
        )
    )

    assert result.ready_for_gate.value == "blocked"
    assert result.decision.value == "block"
    assert result.risk_level.value == "high"
    assert any(check.name == "raw_data_boundary" and check.status.value == "fail" for check in result.preflight_checks)
    assert any("Raw genomic data" in reason for reason in result.reasons)


def test_safety_gate_blocks_submit_execution_when_stage_guard_is_invalid() -> None:
    service = SafetyGateService()

    result = service.review(
        context=SafetyReviewContext(
            task_id="task-safety-003",
            run_id="run-safety-003",
            action_name="submit_execution",
            stage_id="stage_07_execution",
            scheduler_dry_run_done=True,
        )
    )

    assert result.ready_for_gate.value == "blocked"
    assert any(check.name == "stage_guard" and check.status.value == "fail" for check in result.preflight_checks)


def test_safety_gate_allows_submit_execution_when_stage_guard_is_satisfied() -> None:
    service = SafetyGateService()

    result = service.review(
        context=SafetyReviewContext(
            task_id="task-safety-004",
            run_id="run-safety-004",
            action_name="submit_execution",
            stage_id="stage_06_resource_and_safety_gate",
            scheduler_dry_run_done=True,
            cost_estimated=True,
            rollback_plan_ready=True,
        )
    )

    assert any(check.name == "stage_guard" and check.status.value == "pass" for check in result.preflight_checks)
    assert result.decision.value in {"pass", "require_confirmation"}
