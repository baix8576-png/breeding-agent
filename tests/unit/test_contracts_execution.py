from __future__ import annotations

import pytest
from pydantic import ValidationError

from contracts import (
    ExecutionArtifacts,
    JobHandle,
    JobState,
    PipelineSpec,
    ResourceEstimate,
    RoleOutputHeader,
    RunContext,
    SchedulerKind,
    SubmissionPreview,
    TaskDomain,
    TaskPlan,
)
from contracts.common import GateStatus


def test_execution_contracts_expose_tracking_and_submission_fields() -> None:
    run_context = RunContext(
        task_id="task-contracts-001",
        run_id="run-contracts-001",
        working_directory="/cluster/work/contracts",
    )
    header = RoleOutputHeader(
        role="orchestrator",
        task_id=run_context.task_id,
        run_id=run_context.run_id,
        ready_for_gate=GateStatus.DESIGN_PASS,
    )
    pipeline_spec = PipelineSpec(
        name="bioinformatics-analysis-mvp",
        domain=TaskDomain.BIOINFORMATICS,
        stages=["stage_01_intake"],
        deliverables=["pipeline_blueprint"],
    )
    plan = TaskPlan(
        header=header,
        run_context=run_context,
        summary="Contract smoke test",
        domain=TaskDomain.BIOINFORMATICS,
        workflow_name="bioinformatics-analysis-mvp",
        workflow_steps=["stage_01_intake"],
        pipeline_spec=pipeline_spec,
        resource_estimate=ResourceEstimate(),
    )
    preview = SubmissionPreview(
        run_context=run_context,
        working_directory=run_context.working_directory or ".",
        script_preview="#!/usr/bin/env bash",
        job_handle=JobHandle(
            run_context=run_context,
            scheduler=SchedulerKind.SLURM,
            job_id="DRYRUN-SLURM-task-contracts-001-run-contracts-001-GENEAGENT-JOB",
            state=JobState.DRAFT,
        ),
        artifacts=ExecutionArtifacts(
            run_context=run_context,
            script_preview="#!/usr/bin/env bash",
        ),
    )

    assert "run_context" in TaskPlan.model_fields
    assert "pipeline_spec" in TaskPlan.model_fields
    assert "job_handle" in SubmissionPreview.model_fields
    assert "run_context" in JobHandle.model_fields
    assert plan.header.ready_for_gate == GateStatus.DESIGN_PASS
    assert plan.run_context.task_id == "task-contracts-001"
    assert plan.pipeline_spec is not None
    assert plan.pipeline_spec.name == "bioinformatics-analysis-mvp"
    assert preview.job_handle.scheduler == SchedulerKind.SLURM
    assert preview.job_handle.state == JobState.DRAFT
    assert preview.artifacts is not None
    assert preview.artifacts.run_context.run_id == "run-contracts-001"


def test_tracking_contracts_require_task_and_run_identifiers() -> None:
    with pytest.raises(ValidationError):
        RoleOutputHeader(role="orchestrator", run_id="run-missing-task")

    with pytest.raises(ValidationError):
        RunContext(task_id="task-missing-run")
