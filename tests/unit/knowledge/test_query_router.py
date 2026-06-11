from __future__ import annotations

from contracts import BlueprintScope, EvidenceLevel, KnowledgeSource
from knowledge.query_router import KnowledgeQueryRouter


def test_query_router_routes_farmgtex_literature_to_association_mapping() -> None:
    plan = KnowledgeQueryRouter().plan("猪 PigGTEx FarmGTEx eQTL regulatory variants literature DOI")

    assert plan.species == "pig"
    assert plan.blueprint_scope == BlueprintScope.ASSOCIATION_MAPPING
    assert KnowledgeSource.PAPER in plan.sources
    assert EvidenceLevel.PEER_REVIEWED in plan.evidence_levels
    assert "functional_genomics" in plan.domain_scope_hints
    assert plan.query_type == "literature"


def test_query_router_routes_gblup_resource_query_to_quantitative_genetics() -> None:
    plan = KnowledgeQueryRouter().plan("牛 GBLUP GRM GCTA 线程 内存 参数")

    assert plan.species == "cattle"
    assert plan.blueprint_scope == BlueprintScope.QUANTITATIVE_GENETICS
    assert KnowledgeSource.PARAMETER_PLAYBOOK in plan.sources
    assert EvidenceLevel.BENCHMARK in plan.evidence_levels
    assert "genomic_relationship" in plan.domain_scope_hints
    assert plan.query_type == "parameter_guidance"


def test_query_router_routes_failures_to_diagnostic_knowledge() -> None:
    plan = KnowledgeQueryRouter().plan("nohup PID lost permission denied 报错")

    assert plan.blueprint_scope == BlueprintScope.REPORTING_AUDIT
    assert KnowledgeSource.FAILURE_CASE in plan.sources
    assert EvidenceLevel.INCIDENT_VERIFIED in plan.evidence_levels
    assert "operational_diagnostics" in plan.domain_scope_hints
    assert plan.query_type == "diagnostic"
