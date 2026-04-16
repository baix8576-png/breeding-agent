from __future__ import annotations

from pathlib import Path
import shutil
import subprocess

import pytest

from contracts.common import TaskDomain
from knowledge.retrieval import RetrievalBundle
from orchestration.router import IntentRouter
from orchestration.workflow import WorkflowComposer
from tools.registry import ToolRegistry
from pipeline import build_blueprint, list_blueprints


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"


def test_v1_bio_blueprints_are_stable_and_emit_expected_contracts() -> None:
    expected = {"qc_pipeline", "pca_pipeline", "grm_builder", "genomic_prediction"}
    assert set(list_blueprints()) == expected

    for name in sorted(expected):
        blueprint = build_blueprint(name)
        assert blueprint.name == name
        assert blueprint.stages, name
        assert blueprint.outputs, name
        assert blueprint.ready_for_gate == "design_ready"
        assert blueprint.assets["scripts"], name
        assert blueprint.report_sections, name
        assert blueprint.interpretation_notes, name

    pca = build_blueprint("pca_pipeline")
    pca_stage_ids = [stage["id"] for stage in pca.stages]
    pca_output_ids = [artifact["artifact_id"] for artifact in pca.outputs]
    assert pca_stage_ids == [
        "ld_pruning",
        "pca_computation",
        "structure_summary",
        "stratification_warning",
    ]
    assert pca_output_ids == [
        "pruning_manifest",
        "eigenvec_table",
        "eigenval_table",
        "ld_decay_table",
        "roh_segments",
        "fst_table",
        "pi_table",
        "tajima_d_table",
        "pca_plot_index",
        "structure_summary_report",
        "stratification_risk_note",
    ]


def test_non_bio_requests_clearly_skip_cluster_execution() -> None:
    router = IntentRouter()
    classification = router.analyze("Summarize local SOP guidance for audit review templates")
    registry = ToolRegistry()
    registry.bootstrap_defaults()
    composer = WorkflowComposer(tool_registry=registry)
    workflow = composer.compose(
        classification=classification,
        request_text="Summarize local SOP guidance for audit review templates",
        requested_outputs=[],
        retrieval=RetrievalBundle(
            query="Summarize local SOP guidance for audit review templates",
            domain=TaskDomain.KNOWLEDGE,
            retrieval_mode="local_only",
            coverage="high",
            rationale=["local knowledge branch should never reach cluster execution"],
        ),
    )

    assert classification.domain == TaskDomain.KNOWLEDGE
    assert workflow.execution_enabled is False
    assert workflow.selected_blueprint is None
    assert workflow.selected_blueprint_key is None
    assert workflow.name == "knowledge-lightweight-chain-v1"
    assert not any(step.startswith("stage_07_execution") for step in workflow.steps)


@pytest.mark.parametrize(
    "script_path",
    [
        SCRIPTS / "report_generator" / "run_report_generator.sh",
    ],
)
def test_report_generator_critical_script_exists_and_has_help(script_path: Path) -> None:
    assert script_path.exists(), f"Missing report-generator entrypoint: {script_path}"

    bash = shutil.which("bash")
    if bash is None:
        pytest.skip("bash is not available in the current test environment")

    result = subprocess.run(
        [bash, "--noprofile", "--norc", script_path.as_posix(), "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    output = f"{result.stdout}{result.stderr}"
    normalized_output = output.replace("\x00", "")
    if result.returncode != 0 and (
        "E_ACCESSDENIED" in normalized_output
        or "Bash/Service/CreateInstance" in normalized_output
    ):
        pytest.skip("bash is present but WSL bash service is unavailable in this Windows session")

    assert result.returncode == 0, result.stderr or result.stdout
    assert "usage" in (result.stdout + result.stderr).lower()
