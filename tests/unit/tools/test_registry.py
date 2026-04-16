from __future__ import annotations

from contracts.common import TaskDomain
from tools import ToolRegistry


def test_tool_registry_bootstrap_defaults_is_idempotent() -> None:
    registry = ToolRegistry()

    assert registry.list_names() == []

    registry.bootstrap_defaults()
    first_names = registry.list_names()
    registry.bootstrap_defaults()
    second_names = registry.list_names()

    assert first_names == second_names
    assert "input_contract_reader" in first_names
    assert "scheduler_dry_run_preview" in first_names


def test_tool_registry_list_for_stage_and_domain_filters_manifests() -> None:
    registry = ToolRegistry()
    registry.bootstrap_defaults()

    manifests = registry.list_for_stage("lite_02_local_retrieval", TaskDomain.KNOWLEDGE)
    names = [manifest.name for manifest in manifests]

    assert "local_context_search" in names
    assert "external_context_fallback" in names
    assert "genetics_pipeline_blueprint" not in names
