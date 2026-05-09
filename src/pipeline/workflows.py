"""Pipeline blueprint compatibility layer backed by pipeline packs."""

from __future__ import annotations

from pydantic import BaseModel, Field

from pipeline.catalog import PIPELINE_ALIASES, PIPELINE_CATALOG
from pipeline.packs.registry import build_pipeline_pack, list_pipeline_packs


class PipelineBlueprint(BaseModel):
    """Description of a genetics workflow with execution-ready contracts."""

    name: str
    summary: str
    focus: str
    input_requirements: list[dict[str, object]] = Field(default_factory=list)
    stages: list[dict[str, object]] = Field(default_factory=list)
    outputs: list[dict[str, object]] = Field(default_factory=list)
    assets: dict[str, list[str]] = Field(default_factory=dict)
    report_sections: list[str] = Field(default_factory=list)
    interpretation_notes: list[str] = Field(default_factory=list)
    ready_for_gate: str = "design_ready"


def build_blueprint(name: str) -> PipelineBlueprint:
    """Build a named blueprint from pipeline-pack definitions."""

    canonical_name = PIPELINE_ALIASES.get(name, name)
    try:
        pack = build_pipeline_pack(canonical_name)
    except ValueError as exc:
        available = ", ".join(sorted(list_pipeline_packs()))
        raise ValueError(
            f"Unknown pipeline blueprint '{name}'. Available blueprints: {available}."
        ) from exc
    return PipelineBlueprint.model_validate(pack.to_blueprint_payload())


def build_output_template(name: str) -> list[dict[str, object]]:
    """Return the expected output checklist for a named blueprint."""

    return build_blueprint(name).outputs


def list_blueprints() -> list[str]:
    """List canonical blueprint names supported by the v1 execution layer."""

    return sorted(list_pipeline_packs())


assert set(list_blueprints()).issubset(set(PIPELINE_CATALOG))
