"""Query routing for local-first knowledge retrieval."""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel, Field

from contracts.knowledge import BlueprintScope, EvidenceLevel, KnowledgeSource


class KnowledgeRetrievalPlan(BaseModel):
    """Metadata-aware retrieval plan derived from a user query."""

    schema_version: str = "knowledge_retrieval_plan.v1"
    query: str = Field(min_length=1)
    query_type: str = "knowledge_qa"
    species: str | None = None
    blueprint_scope: BlueprintScope | None = None
    evidence_levels: list[EvidenceLevel] = Field(default_factory=list)
    sources: list[KnowledgeSource] = Field(default_factory=list)
    domain_scope_hints: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)


@dataclass(frozen=True)
class _RouteRule:
    label: str
    tokens: tuple[str, ...]


class KnowledgeQueryRouter:
    """Small deterministic router for GeneAgent knowledge queries."""

    _species_rules = (
        _RouteRule("cattle", ("cattle", "bovine", "cow", "dairy", "beef", "牛", "奶牛", "肉牛")),
        _RouteRule("pig", ("pig", "swine", "porcine", "猪", "生猪")),
        _RouteRule("poultry", ("chicken", "poultry", "avian", "broiler", "layer", "鸡", "家禽")),
        _RouteRule("sheep_goat", ("sheep", "goat", "ovine", "caprine", "羊", "绵羊", "山羊")),
        _RouteRule("aquaculture", ("fish", "aquaculture", "tilapia", "salmon", "carp", "水产", "鱼")),
    )

    _scope_rules = (
        (
            BlueprintScope.GENOTYPE_PROCESSING,
            _RouteRule(
                "genotype_processing",
                (
                    "qc",
                    "quality control",
                    "plink",
                    "plink2",
                    "bcftools",
                    "vcf",
                    "maf",
                    "hwe",
                    "missingness",
                    "imputation",
                    "genotype",
                    "基因型质控",
                    "缺失率",
                ),
            ),
        ),
        (
            BlueprintScope.POPULATION_GENETICS,
            _RouteRule(
                "population_genetics",
                (
                    "pca",
                    "admixture",
                    "structure",
                    "roh",
                    "ld",
                    "fst",
                    "selection",
                    "signature",
                    "population",
                    "群体结构",
                    "选择信号",
                    "近交",
                ),
            ),
        ),
        (
            BlueprintScope.QUANTITATIVE_GENETICS,
            _RouteRule(
                "quantitative_genetics",
                (
                    "gblup",
                    "ssgblup",
                    "grm",
                    "gcta",
                    "reml",
                    "heritability",
                    "genomic prediction",
                    "breeding value",
                    "gebv",
                    "数量遗传",
                    "育种值",
                    "遗传力",
                ),
            ),
        ),
        (
            BlueprintScope.ASSOCIATION_MAPPING,
            _RouteRule(
                "association_mapping",
                (
                    "gwas",
                    "qtl",
                    "association",
                    "farmgtex",
                    "eqtl",
                    "regulatory",
                    "variant",
                    "single-cell",
                    "single cell",
                    "关联分析",
                    "调控变异",
                ),
            ),
        ),
        (
            BlueprintScope.REPORTING_AUDIT,
            _RouteRule(
                "reporting_audit",
                (
                    "report",
                    "audit",
                    "traceability",
                    "diagnostic",
                    "error",
                    "failure",
                    "permission denied",
                    "nohup",
                    "pid",
                    "报告",
                    "审计",
                    "报错",
                    "失败",
                ),
            ),
        ),
        (
            BlueprintScope.KNOWLEDGE_GOVERNANCE,
            _RouteRule(
                "knowledge_governance",
                (
                    "knowledge_item",
                    "ontology",
                    "domain_scope",
                    "rag",
                    "ingestion",
                    "grobid",
                    "schema",
                    "知识库",
                    "本体",
                ),
            ),
        ),
    )

    _source_rules = (
        (KnowledgeSource.PAPER, _RouteRule("paper", ("paper", "literature", "doi", "pmid", "nature", "文献", "论文"))),
        (KnowledgeSource.SOP, _RouteRule("sop", ("sop", "procedure", "checklist", "流程", "操作规程"))),
        (
            KnowledgeSource.PARAMETER_PLAYBOOK,
            _RouteRule("parameter_playbook", ("parameter", "thread", "memory", "walltime", "resource", "参数", "线程", "内存", "资源")),
        ),
        (
            KnowledgeSource.FAILURE_CASE,
            _RouteRule("failure_case", ("error", "failure", "failed", "permission denied", "nohup", "pid", "报错", "失败")),
        ),
        (KnowledgeSource.ONTOLOGY, _RouteRule("ontology", ("ontology", "schema", "domain_scope", "本体", "词表"))),
    )

    _evidence_rules = (
        (EvidenceLevel.PEER_REVIEWED, _RouteRule("peer_reviewed", ("paper", "literature", "doi", "pmid", "文献", "论文"))),
        (EvidenceLevel.SOP, _RouteRule("sop", ("sop", "procedure", "checklist", "流程", "操作规程"))),
        (EvidenceLevel.BENCHMARK, _RouteRule("benchmark", ("benchmark", "default", "parameter", "resource", "阈值", "参数"))),
        (EvidenceLevel.INCIDENT_VERIFIED, _RouteRule("incident_verified", ("error", "failure", "failed", "incident", "报错", "失败"))),
        (EvidenceLevel.EXPERT_OPINION, _RouteRule("expert_opinion", ("advice", "suggest", "boundary", "建议", "边界"))),
    )

    _domain_hint_rules = (
        _RouteRule("variant_qc", ("qc", "missingness", "maf", "hwe", "基因型质控")),
        _RouteRule("population_structure", ("pca", "admixture", "structure", "群体结构")),
        _RouteRule("selection_signature", ("selection", "roh", "fst", "选择信号")),
        _RouteRule("genomic_relationship", ("grm", "gblup", "ssgblup", "relationship matrix")),
        _RouteRule("association_mapping", ("gwas", "qtl", "association", "关联分析")),
        _RouteRule("functional_genomics", ("farmgtex", "eqtl", "regulatory", "single-cell", "调控变异")),
        _RouteRule("operational_diagnostics", ("error", "failure", "nohup", "permission denied", "报错")),
    )

    def plan(self, query: str) -> KnowledgeRetrievalPlan:
        """Route a query to metadata filters and retrieval hints."""

        normalized_query = query.strip()
        if not normalized_query:
            raise ValueError("query must not be empty")
        query_lower = normalized_query.lower()
        species, species_reasons = self._first_label_match(query_lower, self._species_rules)
        blueprint_scope, scope_reasons = self._first_scope_match(query_lower)
        sources, source_reasons = self._enum_matches(query_lower, self._source_rules)
        evidence_levels, evidence_reasons = self._enum_matches(query_lower, self._evidence_rules)
        domain_scope_hints, domain_reasons = self._all_label_matches(query_lower, self._domain_hint_rules)
        query_type = self._query_type(query_lower, sources=sources, blueprint_scope=blueprint_scope)
        return KnowledgeRetrievalPlan(
            query=normalized_query,
            query_type=query_type,
            species=species,
            blueprint_scope=blueprint_scope,
            evidence_levels=evidence_levels,
            sources=sources,
            domain_scope_hints=domain_scope_hints,
            reasons=[
                *species_reasons,
                *scope_reasons,
                *source_reasons,
                *evidence_reasons,
                *domain_reasons,
            ],
        )

    @staticmethod
    def _first_label_match(query: str, rules: tuple[_RouteRule, ...]) -> tuple[str | None, list[str]]:
        for rule in rules:
            matched = _matched_tokens(query, rule.tokens)
            if matched:
                return rule.label, [f"{rule.label}:{','.join(matched[:5])}"]
        return None, []

    @staticmethod
    def _all_label_matches(query: str, rules: tuple[_RouteRule, ...]) -> tuple[list[str], list[str]]:
        labels: list[str] = []
        reasons: list[str] = []
        for rule in rules:
            matched = _matched_tokens(query, rule.tokens)
            if not matched:
                continue
            labels.append(rule.label)
            reasons.append(f"{rule.label}:{','.join(matched[:5])}")
        return labels, reasons

    def _first_scope_match(self, query: str) -> tuple[BlueprintScope | None, list[str]]:
        for scope, rule in self._scope_rules:
            matched = _matched_tokens(query, rule.tokens)
            if matched:
                return scope, [f"{scope.value}:{','.join(matched[:5])}"]
        return None, []

    @staticmethod
    def _enum_matches(query: str, rules) -> tuple[list, list[str]]:
        values: list = []
        reasons: list[str] = []
        for enum_value, rule in rules:
            matched = _matched_tokens(query, rule.tokens)
            if not matched:
                continue
            values.append(enum_value)
            reasons.append(f"{enum_value.value}:{','.join(matched[:5])}")
        return values, reasons

    @staticmethod
    def _query_type(
        query: str,
        *,
        sources: list[KnowledgeSource],
        blueprint_scope: BlueprintScope | None,
    ) -> str:
        if KnowledgeSource.FAILURE_CASE in sources or any(token in query for token in ("error", "failure", "报错", "失败")):
            return "diagnostic"
        if KnowledgeSource.PAPER in sources:
            return "literature"
        if KnowledgeSource.PARAMETER_PLAYBOOK in sources:
            return "parameter_guidance"
        if blueprint_scope is not None:
            return "analysis_planning"
        return "knowledge_qa"


def _matched_tokens(query: str, tokens: tuple[str, ...]) -> list[str]:
    return [token for token in tokens if token in query]
