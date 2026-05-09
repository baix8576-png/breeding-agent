from __future__ import annotations

from pathlib import Path

from contracts.common import TaskDomain
from tools import ToolRegistry


def test_tool_registry_bootstrap_defaults_is_idempotent() -> None:
    registry = ToolRegistry()

    assert registry.list_names() == []

    load_result = registry.bootstrap_defaults()
    first_names = registry.list_names()
    second_result = registry.bootstrap_defaults()
    second_names = registry.list_names()

    assert first_names == second_names
    assert "input_contract_reader" in first_names
    assert "scheduler_dry_run_preview" in first_names
    assert "plink2_pca" in first_names
    assert load_result.source in {"file", "builtin"}
    assert second_result.source in {"file", "builtin", "in_memory"}
    assert registry.get("input_contract_reader") is not None
    assert registry.get("input_contract_reader").manifest_version == "1.0.0"
    plink2_pca = registry.get("plink2_pca")
    assert plink2_pca is not None
    assert plink2_pca.category == "atomic_algorithm"
    assert plink2_pca.atomic_resource_profile is not None


def test_tool_registry_list_for_stage_and_domain_filters_manifests() -> None:
    registry = ToolRegistry()
    registry.bootstrap_defaults()

    manifests = registry.list_for_stage("lite_02_local_retrieval", TaskDomain.KNOWLEDGE)
    names = [manifest.name for manifest in manifests]

    assert "local_context_search" in names
    assert "external_context_fallback" in names
    assert "genetics_pipeline_blueprint" not in names

    bio_execution_manifests = registry.list_for_stage("stage_07_execution", TaskDomain.BIOINFORMATICS)
    bio_names = [manifest.name for manifest in bio_execution_manifests]
    assert "plink2_pca" in bio_names
    assert "gcta_reml" in bio_names
    assert "vcftools_weir_fst" in bio_names


def test_tool_registry_bootstrap_defaults_fallback_keeps_current_behavior(tmp_path: Path) -> None:
    manifests_dir = tmp_path / "manifests"
    manifests_dir.mkdir(parents=True, exist_ok=True)
    (manifests_dir / "broken.json").write_text("{invalid", encoding="utf-8")

    registry = ToolRegistry(manifests_dir=manifests_dir, strict_manifest_validation=False)
    load_result = registry.bootstrap_defaults()

    assert load_result.source == "builtin"
    assert load_result.used_fallback is True
    assert "input_contract_reader" in registry.list_names()
    manifests = registry.list_for_stage("lite_02_local_retrieval", TaskDomain.KNOWLEDGE)
    names = [manifest.name for manifest in manifests]
    assert "local_context_search" in names
    assert "external_context_fallback" in names
