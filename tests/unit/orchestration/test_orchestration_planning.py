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
    assert plan.workflow_name == "bioinformatics-standard-chain-v1"
    assert any(step.startswith("stage_06_resource_and_safety_gate") for step in plan.workflow_steps)
    assert any(step.startswith("stage_09_audit_and_memory") for step in plan.workflow_steps)
    assert any(item == "run_id=run-orch-001" for item in plan.assumptions)
    assert any(item == "selected_blueprint=pca_pipeline" for item in plan.assumptions)
    assert plan.pipeline_spec is not None
    assert plan.pipeline_spec.name == "pca_pipeline"
    assert plan.pipeline_spec.blueprint_key == "pca"
    assert "pca" in plan.pipeline_spec.analysis_targets
    assert plan.pipeline_spec.domain == plan.domain
    assert "pca_computation" in plan.pipeline_spec.stages
    assert "pca_computation" in plan.pipeline_spec.stage_contract
    assert "eigenvec_table" in plan.pipeline_spec.artifact_contract
    assert len(plan.pipeline_spec.stage_io_contract) == 9
    assert "pca_plot" in plan.pipeline_spec.requested_outputs
    assert "report_outline" in plan.pipeline_spec.requested_outputs


def test_non_bio_plan_uses_lightweight_chain_without_execution_stage() -> None:
    context = create_application_context()
    run_context = RunContext(
        task_id="task-orch-knowledge-001",
        run_id="run-orch-knowledge-001",
        working_directory="/cluster/work/sheep",
    )

    plan = context.orchestrator.draft_plan(
        UserRequest(
            text="Summarize local SOP requirements for pedigree and covariate tables",
            working_directory=run_context.working_directory,
        ),
        run_context=run_context,
    )

    assert plan.domain.value == "knowledge"
    assert plan.workflow_name == "knowledge-lightweight-chain-v1"
    assert not any(step.startswith("stage_07_execution") for step in plan.workflow_steps)
    assert plan.pipeline_spec is not None
    assert plan.pipeline_spec.name == "knowledge-lightweight-chain-v1"
    assert plan.pipeline_spec.blueprint_key is None
    assert len(plan.pipeline_spec.stage_io_contract) >= 3


def test_blueprint_selection_binds_grm_and_genomic_prediction_keys() -> None:
    context = create_application_context()

    grm_plan = context.orchestrator.draft_plan(
        UserRequest(text="Build kinship relationship matrix from PLINK files"),
        run_context=RunContext(task_id="task-orch-grm-001", run_id="run-orch-grm-001"),
    )
    genomic_plan = context.orchestrator.draft_plan(
        UserRequest(text="Run GBLUP genomic prediction with phenotype and pedigree"),
        run_context=RunContext(task_id="task-orch-gpred-001", run_id="run-orch-gpred-001"),
    )

    assert grm_plan.pipeline_spec is not None
    assert grm_plan.pipeline_spec.blueprint_key == "grm"
    assert grm_plan.pipeline_spec.name == "grm_builder"
    assert "relationship_estimation" in grm_plan.pipeline_spec.stage_contract
    assert genomic_plan.pipeline_spec is not None
    assert genomic_plan.pipeline_spec.blueprint_key == "genomic_prediction"
    assert genomic_plan.pipeline_spec.name == "genomic_prediction"
    assert "model_blueprint" in genomic_plan.pipeline_spec.stage_contract


