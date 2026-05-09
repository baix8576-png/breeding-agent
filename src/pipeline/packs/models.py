"""Typed pipeline-pack contracts for blueprint packaging."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PipelinePackArtifact(BaseModel):
    """Single artifact contract in a pipeline pack."""

    artifact_id: str
    relative_path: str
    format: str
    description: str
    required: bool = True


class PipelinePackStage(BaseModel):
    """Single stage contract in a pipeline pack."""

    id: str
    title: str
    kind: str
    objective: str
    required_inputs: list[str] = Field(default_factory=list)
    optional_inputs: list[str] = Field(default_factory=list)
    checks: list[str] = Field(default_factory=list)
    outputs: list[PipelinePackArtifact] = Field(default_factory=list)

    def to_stage_payload(self) -> dict[str, object]:
        """Render a workflow-stage payload compatible with blueprint contracts."""

        return {
            "id": self.id,
            "title": self.title,
            "kind": self.kind,
            "objective": self.objective,
            "required_inputs": list(self.required_inputs),
            "optional_inputs": list(self.optional_inputs),
            "checks": list(self.checks),
            "outputs": [artifact.model_dump(mode="json") for artifact in self.outputs],
        }


class PipelinePackSpec(BaseModel):
    """Pack-level spec contract (name, scope, stage schema, assets)."""

    name: str
    summary: str
    focus: str
    aliases: list[str] = Field(default_factory=list)
    input_requirements: list[dict[str, object]] = Field(default_factory=list)
    stages: list[PipelinePackStage] = Field(default_factory=list)
    assets: dict[str, list[str]] = Field(default_factory=dict)
    interpretation_notes: list[str] = Field(default_factory=list)
    ready_for_gate: str = "design_ready"
    script_entrypoint: str | None = None

    @property
    def stage_ids(self) -> list[str]:
        return [stage.id for stage in self.stages]

    @property
    def artifact_contract(self) -> list[str]:
        contracts: list[str] = []
        for stage in self.stages:
            for artifact in stage.outputs:
                if artifact.artifact_id not in contracts:
                    contracts.append(artifact.artifact_id)
        return contracts


class PipelinePackReportTemplate(BaseModel):
    """Report-template contract attached to a pipeline pack."""

    template_id: str
    sections: list[str] = Field(default_factory=list)
    template_paths: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class PipelinePackTestSpec(BaseModel):
    """Minimal regression test contract for a pipeline pack."""

    unit_paths: list[str] = Field(default_factory=list)
    integration_paths: list[str] = Field(default_factory=list)
    e2e_paths: list[str] = Field(default_factory=list)

    @property
    def all_paths(self) -> list[str]:
        return [*self.unit_paths, *self.integration_paths, *self.e2e_paths]


class PipelinePack(BaseModel):
    """Unified blueprint pack (spec + report template + test contract)."""

    spec: PipelinePackSpec
    report_template: PipelinePackReportTemplate
    test_spec: PipelinePackTestSpec

    def to_blueprint_payload(self) -> dict[str, object]:
        """Render a payload compatible with `PipelineBlueprint` construction."""

        outputs = [
            artifact.model_dump(mode="json")
            for stage in self.spec.stages
            for artifact in stage.outputs
        ]
        return {
            "name": self.spec.name,
            "summary": self.spec.summary,
            "focus": self.spec.focus,
            "input_requirements": list(self.spec.input_requirements),
            "stages": [stage.to_stage_payload() for stage in self.spec.stages],
            "outputs": outputs,
            "assets": dict(self.spec.assets),
            "report_sections": list(self.report_template.sections),
            "interpretation_notes": list(self.spec.interpretation_notes),
            "ready_for_gate": self.spec.ready_for_gate,
        }
