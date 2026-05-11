from __future__ import annotations

from pathlib import Path

from audit.store import FileAuditStore
from runtime.governance import GovernanceService
from runtime.settings import Settings


def test_governance_production_gate_plans_checks_without_execution(tmp_path) -> None:
    service = GovernanceService(
        settings=Settings(),
        audit_store=FileAuditStore(fallback_root=str(tmp_path / "audit")),
    )

    report = service.run_production_gate(
        working_directory=str(tmp_path),
        execute_tests=False,
    )

    assert report["schema_version"] == "production_gate.v1"
    assert report["overall_status"] in {"planned", "pass"}
    assert isinstance(report["checks"], list)
    assert any(item["check_id"] == "contract_regression" for item in report["checks"])
    assert any(item["check_id"] == "audit_integrity" for item in report["checks"])


def test_governance_release_plan_includes_template_and_rollback() -> None:
    service = GovernanceService(
        settings=Settings(),
        audit_store=FileAuditStore(),
    )

    plan = service.build_release_plan(
        version_tag="2.0.1",
        change_summary="Stabilize observability and explanation-layer outputs.",
        stage_ids=["stage_05_blueprint_selection", "stage_06_resource_and_safety_gate"],
    )

    assert plan["schema_version"] == "release_plan.v1"
    assert plan["version_tag"] == "v2.0.1"
    assert "## Scope" in plan["release_notes_template"]
    assert plan["rollback_plan"]


def test_governance_final_review_reports_architecture_governance_and_operability() -> None:
    service = GovernanceService(
        settings=Settings(),
        audit_store=FileAuditStore(),
    )
    repo_root = Path(__file__).resolve().parents[3]

    review = service.final_acceptance_review(working_directory=str(repo_root))

    assert review["schema_version"] == "v2_final_review.v1"
    assert set(review).issuperset(
        {"architecture_boundary", "governance_requirements", "operability", "overall_status"}
    )
    assert review["architecture_boundary"]["status"] in {"pass", "fail"}
