from __future__ import annotations

from contracts.execution import RunContext
from contracts.tasks import UserRequest
from runtime.bootstrap import create_application_context


def test_draft_plan_preserves_run_context_and_pipeline_contract() -> None:
    context = create_application_context()
    run_context = RunContext(
        task_id="task-orch-001",
        run_id="run-orch-001",
        working_directory="/cluster/work/sheep",
    )

    plan = context.orchestrator.draft_plan(
        UserRequest(
            text="Run PCA on a sheep VCF dataset and draft a report outline",
            working_directory=run_context.working_directory,
            requested_outputs=["pca_plot", "report_outline"],
        ),
        run_context=run_context,
    )

    assert plan.header.task_id == "task-orch-001"
    assert plan.header.run_id == "run-orch-001"
    assert plan.run_context.task_id == "task-orch-001"
    assert plan.run_context.run_id == "run-orch-001"
    assert plan.run_context.working_directory == "/cluster/work/sheep"
    assert plan.header.ready_for_gate.value == "design_pass"
    assert plan.domain.value == "bioinformatics"
    assert plan.workflow_name == "bioinformatics-analysis-mvp"
    assert any(step.startswith("stage_05_resource_and_gate") for step in plan.workflow_steps)
    assert any(item == "run_id=run-orch-001" for item in plan.assumptions)
    assert plan.pipeline_spec is not None
    assert plan.pipeline_spec.name == plan.workflow_name
    assert plan.pipeline_spec.domain == plan.domain
    assert "pca_plot" in plan.pipeline_spec.requested_outputs
    assert "report_outline" in plan.pipeline_spec.requested_outputs


