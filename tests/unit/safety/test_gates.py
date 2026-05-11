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


def test_safety_gate_manual_approval_record_allows_high_risk_submit() -> None:
    service = SafetyGateService()

    result = service.review(
        context=SafetyReviewContext(
            task_id="task-safety-005",
            run_id="run-safety-005",
            action_name="submit_execution",
            stage_id="stage_06_resource_and_safety_gate",
            scheduler_dry_run_done=True,
            overwrite_existing=True,
            target_paths=["/cluster/work/sheep/results"],
            rollback_plan_ready=True,
            cost_estimated=True,
            manual_approval={
                "approved": True,
                "approver": "qa_lead",
                "reason": "rerun required after validated metric drift",
                "approved_at": "2026-05-09T11:20:00Z",
            },
        )
    )

    assert result.decision.value == "pass"
    assert result.approval_status == "approved"
    assert result.approval_record is not None
    assert result.approval_record["approver"] == "qa_lead"
    assert result.approval_record["reason"] == "rerun required after validated metric drift"
    assert result.approval_record["approved_at"] == "2026-05-09T11:20:00Z"


def test_safety_gate_blocks_when_manual_approval_is_incomplete() -> None:
    service = SafetyGateService()

    result = service.review(
        context=SafetyReviewContext(
            task_id="task-safety-006",
            run_id="run-safety-006",
            action_name="submit_execution",
            stage_id="stage_06_resource_and_safety_gate",
            scheduler_dry_run_done=True,
            overwrite_existing=True,
            target_paths=["/cluster/work/sheep/results"],
            rollback_plan_ready=True,
            cost_estimated=True,
            manual_approval={
                "approved": True,
                "approver": "operator_1",
            },
        )
    )

    assert result.decision.value == "block"
    assert result.approval_status == "invalid"
    assert any("incomplete" in reason.lower() for reason in result.reasons)


def test_safety_gate_budget_quota_blocks_when_resource_budget_exceeded() -> None:
    service = SafetyGateService(
        quota_cpu_hours_limit=40,
        quota_memory_gb_limit=64,
        quota_max_concurrent_jobs=3,
    )
    result = service.review(
        context=SafetyReviewContext(
            task_id="task-safety-007",
            run_id="run-safety-007",
            action_name="submit_execution",
            stage_id="stage_06_resource_and_safety_gate",
            scheduler_dry_run_done=True,
            cost_estimated=True,
            rollback_plan_ready=True,
            cpu_cores=16,
            memory_gb=96,
            walltime_hours=6,
            job_count=2,
            current_active_jobs=2,
        )
    )

    assert result.decision.value == "block"
    assert result.quota_gate["status"] == "blocked"
    assert result.quota_gate["reasons"]
    assert any(check.name == "budget_quota" and check.status.value == "fail" for check in result.preflight_checks)


def test_safety_gate_outbound_policy_blocks_disallowed_payload_fields() -> None:
    service = SafetyGateService(outbound_allowed_fields=["prompt", "tool_summary"])

    result = service.review(
        context=SafetyReviewContext(
            task_id="task-safety-008",
            run_id="run-safety-008",
            action_name="cloud_diagnostic_sync",
            external_network=True,
            cloud_llm=True,
            network_approved=True,
            outbound_payload={
                "prompt": "summarize error",
                "raw_path": "D:/data/sheep/cohort.vcf.gz",
            },
        )
    )

    assert result.decision.value == "block"
    assert result.outbound_policy_audit["status"] == "blocked"
    assert any(check.name == "outbound_policy" and check.status.value == "fail" for check in result.preflight_checks)
