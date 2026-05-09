"""Registry helpers for pipeline packs."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pipeline.catalog import PIPELINE_ALIASES
from pipeline.packs.builtin_blueprints import build_blueprint, list_blueprints

from .models import (
    PipelinePack,
    PipelinePackArtifact,
    PipelinePackReportTemplate,
    PipelinePackSpec,
    PipelinePackStage,
    PipelinePackTestSpec,
)

_PACK_TESTS = {
    "qc_pipeline": PipelinePackTestSpec(
        unit_paths=["tests/unit/pipeline/test_pipeline_execution.py", "tests/unit/pipeline/test_packs.py"],
        integration_paths=["tests/integration/api/test_task_routes.py"],
        e2e_paths=["tests/e2e/test_v1_completion.py"],
    ),
    "pca_pipeline": PipelinePackTestSpec(
        unit_paths=["tests/unit/pipeline/test_pipeline_execution.py", "tests/unit/pipeline/test_packs.py"],
        integration_paths=["tests/integration/api/test_task_routes.py"],
        e2e_paths=["tests/e2e/test_v1_completion.py"],
    ),
    "grm_builder": PipelinePackTestSpec(
        unit_paths=["tests/unit/pipeline/test_pipeline_execution.py", "tests/unit/pipeline/test_packs.py"],
        integration_paths=["tests/integration/api/test_task_routes.py"],
        e2e_paths=["tests/e2e/test_v1_completion.py"],
    ),
    "genomic_prediction": PipelinePackTestSpec(
        unit_paths=["tests/unit/pipeline/test_pipeline_execution.py", "tests/unit/pipeline/test_packs.py"],
        integration_paths=["tests/integration/test_genomic_prediction_script.py"],
        e2e_paths=["tests/e2e/test_v1_completion.py"],
    ),
}

_PACK_SCRIPT_ENTRYPOINT = {
    "qc_pipeline": "scripts/qc_pipeline/run_qc_pipeline.sh",
    "pca_pipeline": "scripts/pca_pipeline/run_pca_pipeline.sh",
    "grm_builder": "scripts/grm_builder/run_grm_builder.sh",
    "genomic_prediction": "scripts/genomic_prediction/run_genomic_prediction.sh",
}


def list_pipeline_packs() -> list[str]:
    """List canonical pack names."""

    return sorted(_canonical_pack_index().keys())


def build_pipeline_pack(name: str) -> PipelinePack:
    """Return one canonical pack by name or alias."""

    canonical = PIPELINE_ALIASES.get(name, name)
    pack = _canonical_pack_index().get(canonical)
    if pack is None:
        available = ", ".join(sorted(_canonical_pack_index().keys()))
        raise ValueError(f"Unknown pipeline pack '{name}'. Available pipeline packs: {available}.")
    return pack


@lru_cache(maxsize=1)
def _canonical_pack_index() -> dict[str, PipelinePack]:
    index: dict[str, PipelinePack] = {}
    for canonical_name in list_blueprints():
        blueprint = build_blueprint(canonical_name)
        stage_models: list[PipelinePackStage] = []
        for stage in blueprint.stages:
            outputs = [PipelinePackArtifact.model_validate(item) for item in stage.get("outputs", [])]
            stage_models.append(
                PipelinePackStage(
                    id=str(stage["id"]),
                    title=str(stage["title"]),
                    kind=str(stage["kind"]),
                    objective=str(stage["objective"]),
                    required_inputs=[str(item) for item in stage.get("required_inputs", [])],
                    optional_inputs=[str(item) for item in stage.get("optional_inputs", [])],
                    checks=[str(item) for item in stage.get("checks", [])],
                    outputs=outputs,
                )
            )

        aliases = sorted(alias for alias, target in PIPELINE_ALIASES.items() if target == canonical_name)
        references = [str(item) for item in blueprint.assets.get("references", [])]
        template_paths = [item for item in references if "report_templates/" in item.replace("\\", "/")]
        report_template = PipelinePackReportTemplate(
            template_id=f"{canonical_name}_report_template",
            sections=[str(item) for item in blueprint.report_sections],
            template_paths=template_paths,
            notes=["Template paths are local-first references and should be resolved before external fallback."],
        )
        index[canonical_name] = PipelinePack(
            spec=PipelinePackSpec(
                name=canonical_name,
                summary=blueprint.summary,
                focus=blueprint.focus,
                aliases=aliases,
                input_requirements=[dict(item) for item in blueprint.input_requirements],
                stages=stage_models,
                assets={key: [str(value) for value in values] for key, values in blueprint.assets.items()},
                interpretation_notes=[str(item) for item in blueprint.interpretation_notes],
                ready_for_gate=blueprint.ready_for_gate,
                script_entrypoint=_PACK_SCRIPT_ENTRYPOINT.get(canonical_name),
            ),
            report_template=report_template,
            test_spec=_PACK_TESTS.get(canonical_name, PipelinePackTestSpec()),
        )
    return index


def validate_pipeline_pack_tests(pack: PipelinePack, *, project_root: Path | None = None) -> list[str]:
    """Return missing test-path entries declared by a pack."""

    root = project_root or Path(__file__).resolve().parents[3]
    missing: list[str] = []
    for relative in pack.test_spec.all_paths:
        if not (root / relative).exists():
            missing.append(relative)
    return missing
