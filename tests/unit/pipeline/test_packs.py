from __future__ import annotations

from pathlib import Path

from pipeline import build_blueprint
from pipeline.packs import build_pipeline_pack, list_pipeline_packs, validate_pipeline_pack_tests


def test_pipeline_pack_registry_exposes_four_v15_canonical_packs() -> None:
    assert set(list_pipeline_packs()) == {
        "qc_pipeline",
        "pca_pipeline",
        "grm_builder",
        "genomic_prediction",
    }


def test_pipeline_pack_contains_spec_stage_artifact_report_and_tests_contract() -> None:
    project_root = Path(__file__).resolve().parents[3]
    for name in list_pipeline_packs():
        pack = build_pipeline_pack(name)
        assert pack.spec.name == name
        assert pack.spec.summary
        assert pack.spec.focus
        assert pack.spec.stages
        assert pack.spec.artifact_contract
        assert pack.report_template.sections
        assert pack.test_spec.all_paths
        assert validate_pipeline_pack_tests(pack, project_root=project_root) == []


def test_pipeline_pack_pca_payload_keeps_stage_and_artifact_contract_stable() -> None:
    pack = build_pipeline_pack("pca_pipeline")
    payload = pack.to_blueprint_payload()

    assert [stage["id"] for stage in payload["stages"]] == [
        "ld_pruning",
        "pca_computation",
        "structure_summary",
        "stratification_warning",
    ]
    assert [artifact["artifact_id"] for artifact in payload["outputs"]] == [
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


def test_pipeline_pack_alias_resolution_is_compatible_with_existing_blueprints() -> None:
    alias_pack = build_pipeline_pack("population_structure")
    canonical_pack = build_pipeline_pack("pca_pipeline")
    alias_blueprint = build_blueprint("population_structure")
    canonical_blueprint = build_blueprint("pca_pipeline")

    assert alias_pack.spec.name == "pca_pipeline"
    assert canonical_pack.spec.name == "pca_pipeline"
    assert alias_blueprint.name == canonical_blueprint.name


def test_workflow_blueprint_payload_is_pack_equivalent() -> None:
    for name in list_pipeline_packs():
        pack_payload = build_pipeline_pack(name).to_blueprint_payload()
        blueprint = build_blueprint(name)
        assert blueprint.name == pack_payload["name"]
        assert blueprint.stages == pack_payload["stages"]
        assert blueprint.outputs == pack_payload["outputs"]
        assert blueprint.assets == pack_payload["assets"]
        assert blueprint.report_sections == pack_payload["report_sections"]
