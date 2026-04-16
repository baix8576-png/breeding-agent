"""Workflow templates used to structure first-pass orchestration outputs."""

from __future__ import annotations

from pydantic import BaseModel, Field

from contracts.common import TaskDomain
from knowledge.retrieval import RetrievalBundle
from orchestration.router import IntentClassification
from pipeline.workflows import build_blueprint
from tools.registry import ToolRegistry


class WorkflowStage(BaseModel):
    """Single deterministic workflow stage used by the v1 orchestration chain."""

    stage_id: str
    title: str
    owner: str
    objective: str
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    tool_candidates: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)

    def render(self) -> str:
        """Render a stable text representation for CLI/API consumers."""

        tools = ",".join(self.tool_candidates) if self.tool_candidates else "none"
        inputs = ",".join(self.inputs) if self.inputs else "none"
        outputs = ",".join(self.outputs) if self.outputs else "none"
        return (
            f"{self.stage_id} | owner={self.owner} | title={self.title} | "
            f"objective={self.objective} | tools={tools} | inputs={inputs} | outputs={outputs}"
        )


class WorkflowTemplate(BaseModel):
    """Structured workflow description returned by the draft orchestrator."""

    name: str
    domain: TaskDomain
    stages: list[WorkflowStage] = Field(default_factory=list)
    steps: list[str] = Field(default_factory=list)
    required_roles: list[str] = Field(default_factory=list)
    stable_outputs: list[str] = Field(default_factory=list)
    retrieval_mode: str = "local_only"
    selected_blueprint_key: str | None = None
    selected_blueprint: str | None = None
    blueprint_stage_ids: list[str] = Field(default_factory=list)
    artifact_contract: list[str] = Field(default_factory=list)
    execution_enabled: bool = False

    @property
    def referenced_tools(self) -> list[str]:
        """Return all referenced tool names in a stable order."""

        seen: list[str] = []
        for stage in self.stages:
            for tool_name in stage.tool_candidates:
                if tool_name not in seen:
                    seen.append(tool_name)
        return seen

    @classmethod
    def from_stages(
        cls,
        *,
        name: str,
        domain: TaskDomain,
        stages: list[WorkflowStage],
        retrieval_mode: str,
        selected_blueprint_key: str | None = None,
        selected_blueprint: str | None = None,
        blueprint_stage_ids: list[str] | None = None,
        artifact_contract: list[str] | None = None,
        execution_enabled: bool = False,
    ) -> "WorkflowTemplate":
        """Build a workflow template with normalized steps and output contracts."""

        steps = [stage.render() for stage in stages]
        required_roles: list[str] = []
        stable_outputs: list[str] = []
        for stage in stages:
            if stage.owner not in required_roles:
                required_roles.append(stage.owner)
            for output_name in stage.outputs:
                if output_name not in stable_outputs:
                    stable_outputs.append(output_name)

        return cls(
            name=name,
            domain=domain,
            stages=stages,
            steps=steps,
            required_roles=required_roles,
            stable_outputs=stable_outputs,
            retrieval_mode=retrieval_mode,
            selected_blueprint_key=selected_blueprint_key,
            selected_blueprint=selected_blueprint,
            blueprint_stage_ids=blueprint_stage_ids or [],
            artifact_contract=artifact_contract or [],
            execution_enabled=execution_enabled,
        )


class WorkflowComposer:
    """Compose deterministic workflow stages from routing and retrieval results."""

    _BLUEPRINT_BINDINGS = {
        "qc": "qc_pipeline",
        "pca": "pca_pipeline",
        "grm": "grm_builder",
        "genomic_prediction": "genomic_prediction",
    }

    def __init__(self, tool_registry: ToolRegistry) -> None:
        self._tool_registry = tool_registry

    def compose(
        self,
        *,
        classification: IntentClassification,
        request_text: str,
        requested_outputs: list[str],
        retrieval: RetrievalBundle,
    ) -> WorkflowTemplate:
        """Build a workflow template for the selected domain."""

        if classification.domain == TaskDomain.BIOINFORMATICS:
            return self._compose_bioinformatics_standard_chain(
                classification=classification,
                request_text=request_text,
                requested_outputs=requested_outputs,
                retrieval=retrieval,
            )
        return self._compose_lightweight_non_bio_chain(
            classification=classification,
            request_text=request_text,
            requested_outputs=requested_outputs,
            retrieval=retrieval,
        )

    def _compose_bioinformatics_standard_chain(
        self,
        *,
        classification: IntentClassification,
        request_text: str,
        requested_outputs: list[str],
        retrieval: RetrievalBundle,
    ) -> WorkflowTemplate:
        selected_blueprint_key = self._select_bio_blueprint_key(
            classification=classification,
            request_text=request_text,
            requested_outputs=requested_outputs,
        )
        selected_blueprint = self._BLUEPRINT_BINDINGS[selected_blueprint_key]
        blueprint = build_blueprint(selected_blueprint)
        blueprint_stage_ids = [
            str(stage["id"])
            for stage in blueprint.stages
            if isinstance(stage, dict) and stage.get("id")
        ]
        artifact_contract = [
            str(artifact["artifact_id"])
            for artifact in blueprint.outputs
            if isinstance(artifact, dict) and artifact.get("artifact_id")
        ]

        stages = [
            self._stage(
                stage_id="stage_01_intake",
                title="Intake",
                owner="orchestrator",
                objective="Normalize natural language input and produce task_id, run_id, and session_id.",
                inputs=["request_text"],
                outputs=["task_id", "run_id", "session_id", "normalized_request"],
                domain=classification.domain,
                notes=[f"matched_keywords={','.join(classification.matched_keywords) or 'none'}"],
            ),
            self._stage(
                stage_id="stage_02_intent_and_scope",
                title="Intent + Scope",
                owner="orchestrator",
                objective="Classify intent as bioinformatics, system, or knowledge and lock analysis scope.",
                inputs=["normalized_request", "task_id", "run_id", "session_id"],
                outputs=["intent_domain", "scope_statement"],
                domain=classification.domain,
                notes=[f"analysis_targets={','.join(classification.analysis_targets) or 'none'}"],
            ),
            self._stage(
                stage_id="stage_03_input_validation",
                title="Input Validation",
                owner="orchestrator",
                objective=(
                    "Normalize source paths into InputBundle and check VCF/PLINK/BAM/phenotype/covariate/"
                    "pedigree consistency."
                ),
                inputs=["scope_statement", "task_id", "run_id", "session_id", "raw_input_paths"],
                outputs=["input_bundle", "validation_snapshot"],
                domain=classification.domain,
                notes=["Validation emits execution-ready InputBundle and consistency checks."],
            ),
            self._stage(
                stage_id="stage_04_local_first_rag",
                title="Local-first RAG",
                owner="llm_orchestrator",
                objective=(
                    "Retrieve references/*, local SOP, and templates first; use external placeholder retrieval only when"
                    f" local coverage is insufficient (mode={retrieval.retrieval_mode}, coverage={retrieval.coverage})."
                ),
                inputs=["normalized_request", "scope_statement", "input_bundle"],
                outputs=["retrieval_context", "retrieval_sources"],
                domain=classification.domain,
                notes=retrieval.rationale,
            ),
            self._stage(
                stage_id="stage_05_blueprint_selection",
                title="Blueprint Selection",
                owner="popgen_quantgen",
                objective=(
                    "Bind request to one blueprint among qc/pca/grm/genomic_prediction and emit stage and artifact"
                    " contracts."
                ),
                inputs=["intent_domain", "scope_statement", "retrieval_context", "validation_snapshot"],
                outputs=["selected_blueprint", "stage_contract", "artifact_contract"],
                domain=classification.domain,
                notes=[
                    f"selected_blueprint_key={selected_blueprint_key}",
                    f"selected_blueprint={selected_blueprint}",
                    f"blueprint_stage_count={len(blueprint_stage_ids)}",
                    f"artifact_contract_count={len(artifact_contract)}",
                ],
            ),
            self._stage(
                stage_id="stage_06_resource_and_safety_gate",
                title="Resource + Safety Gate",
                owner="hpc_scheduler",
                objective=(
                    "Estimate resources, attach dry-run preview hooks, list manual confirmations, and define"
                    " circuit-breaker triggers."
                ),
                inputs=["selected_blueprint", "stage_contract", "artifact_contract", "validation_snapshot"],
                outputs=[
                    "resource_estimate",
                    "dry_run_preview",
                    "manual_confirmation_items",
                    "circuit_breaker_conditions",
                ],
                domain=classification.domain,
                notes=["High-risk actions remain blocked until explicit human confirmation."],
            ),
            self._stage(
                stage_id="stage_07_execution",
                title="Execution",
                owner="hpc_scheduler",
                objective=(
                    "Plan Bash wrapper generation, scheduler script creation, submit and poll loop, and failure"
                    " recovery strategy."
                ),
                inputs=["resource_estimate", "dry_run_preview", "manual_confirmation_items", "circuit_breaker_conditions"],
                outputs=["bash_wrapper", "scheduler_script", "submission_handle", "polling_state", "recovery_plan"],
                domain=classification.domain,
                notes=["Execution uses real pipeline wrappers and scheduler submission adapters."],
            ),
            self._stage(
                stage_id="stage_08_artifact_and_report",
                title="Artifact + Report",
                owner="popgen_quantgen",
                objective="Plan result collection, figure indexing, log harvesting, and report summary packaging.",
                inputs=["submission_handle", "polling_state", "recovery_plan", "artifact_contract"],
                outputs=["artifact_index", "figure_index", "report_index", "explanation_summary"],
                domain=classification.domain,
                notes=["Artifact and report outputs are generated from executable pipeline stages."],
            ),
            self._stage(
                stage_id="stage_09_audit_and_memory",
                title="Audit + Memory",
                owner="orchestrator",
                objective=(
                    "Persist input summary, planning summary, submit command, job id, log paths, and manual"
                    " confirmation records."
                ),
                inputs=["input_bundle", "validation_snapshot", "selected_blueprint", "submission_handle", "report_index"],
                outputs=["audit_record", "memory_handoff"],
                domain=classification.domain,
                notes=[f"request_excerpt={request_text[:80]}"],
            ),
        ]
        return WorkflowTemplate.from_stages(
            name="bioinformatics-standard-chain-v1",
            domain=classification.domain,
            stages=stages,
            retrieval_mode=retrieval.retrieval_mode,
            selected_blueprint_key=selected_blueprint_key,
            selected_blueprint=selected_blueprint,
            blueprint_stage_ids=blueprint_stage_ids,
            artifact_contract=artifact_contract,
            execution_enabled=True,
        )

    def _compose_lightweight_non_bio_chain(
        self,
        *,
        classification: IntentClassification,
        request_text: str,
        requested_outputs: list[str],
        retrieval: RetrievalBundle,
    ) -> WorkflowTemplate:
        answer_outputs = ["answer_blueprint", *requested_outputs] if requested_outputs else ["answer_blueprint"]
        chain_name = (
            "system-lightweight-chain-v1"
            if classification.domain == TaskDomain.SYSTEM
            else "knowledge-lightweight-chain-v1"
        )

        stages = [
            self._stage(
                stage_id="lite_01_intake",
                title="Intake",
                owner="orchestrator",
                objective="Normalize user request and keep only lightweight answer scope.",
                inputs=["request_text"],
                outputs=["task_id", "run_id", "session_id", "normalized_request"],
                domain=classification.domain,
                notes=[f"matched_keywords={','.join(classification.matched_keywords) or 'none'}"],
            ),
            self._stage(
                stage_id="lite_02_local_retrieval",
                title="Local Retrieval",
                owner="llm_orchestrator",
                objective=(
                    "Use local references and SOP first; allow external placeholder retrieval only when local"
                    f" coverage is insufficient (mode={retrieval.retrieval_mode}, coverage={retrieval.coverage})."
                ),
                inputs=["normalized_request", "task_id", "run_id"],
                outputs=["retrieval_context", "retrieval_sources"],
                domain=classification.domain,
                notes=retrieval.rationale,
            ),
            self._stage(
                stage_id="lite_03_answer_blueprint",
                title="Answer Blueprint",
                owner="llm_orchestrator",
                objective=(
                    "Draft grounded answer blueprint without cluster execution and without scheduler submission."
                ),
                inputs=["normalized_request", "retrieval_context", "retrieval_sources"],
                outputs=answer_outputs,
                domain=classification.domain,
                notes=["Non-bio lightweight branch never enters cluster execution path."],
            ),
        ]

        if classification.risk_hints:
            stages.append(
                self._stage(
                    stage_id="lite_04_optional_safety_review",
                    title="Optional Safety Review",
                    owner="safety_fuse",
                    objective="Run safety review only when request contains risky intents.",
                    inputs=["answer_blueprint", "risk_hints"],
                    outputs=["safety_review_result"],
                    domain=classification.domain,
                    notes=[f"risk_hints={','.join(classification.risk_hints)}"],
                )
            )

        return WorkflowTemplate.from_stages(
            name=chain_name,
            domain=classification.domain,
            stages=stages,
            retrieval_mode=retrieval.retrieval_mode,
            selected_blueprint=None,
            blueprint_stage_ids=[stage.stage_id for stage in stages],
            artifact_contract=answer_outputs,
            execution_enabled=False,
        )

    def _select_bio_blueprint_key(
        self,
        *,
        classification: IntentClassification,
        request_text: str,
        requested_outputs: list[str],
    ) -> str:
        targets = set(classification.analysis_targets)
        text = request_text.lower()
        output_text = " ".join(requested_outputs).lower()
        joined = f"{text} {output_text}"

        if "qc" in targets or any(token in joined for token in {"qc", "quality control", "input validation"}):
            return "qc"

        if targets.intersection({"genomic_prediction", "bayesian_prediction", "breeding_value_prediction", "heritability", "gwas"}) or any(
            token in joined
            for token in {
                "genomic prediction",
                "genomic selection",
                "gblup",
                "ssgblup",
                "bayes",
                "breeding value",
            }
        ):
            return "genomic_prediction"

        if targets.intersection({"grm", "relationship_matrix", "kinship"}) or any(
            token in joined for token in {"grm", "relationship matrix", "relatedness", "kinship"}
        ):
            return "grm"

        if targets.intersection({"pca", "population_structure", "population_statistics", "ld", "roh"}) or any(
            token in joined for token in {"pca", "structure", "fst", "ld", "roh"}
        ):
            return "pca"

        return "qc"

    def _stage(
        self,
        *,
        stage_id: str,
        title: str,
        owner: str,
        objective: str,
        inputs: list[str],
        outputs: list[str],
        domain: TaskDomain,
        notes: list[str],
    ) -> WorkflowStage:
        tool_candidates = [
            manifest.name
            for manifest in self._tool_registry.list_for_stage(stage_id=stage_id, domain=domain)
        ]
        return WorkflowStage(
            stage_id=stage_id,
            title=title,
            owner=owner,
            objective=objective,
            inputs=inputs,
            outputs=outputs,
            tool_candidates=tool_candidates,
            notes=notes,
        )
