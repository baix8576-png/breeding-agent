"""Workflow templates used to structure first-pass orchestration outputs."""

from __future__ import annotations

from pydantic import BaseModel, Field

from contracts.common import TaskDomain
from knowledge.retrieval import RetrievalBundle
from orchestration.router import IntentClassification
from tools.registry import ToolRegistry


class WorkflowStage(BaseModel):
    """Single deterministic workflow stage used by the MVP skeleton."""

    stage_id: str
    title: str
    owner: str
    objective: str
    outputs: list[str] = Field(default_factory=list)
    tool_candidates: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)

    def render(self) -> str:
        """Render a stable text representation for CLI/API consumers."""

        tools = ",".join(self.tool_candidates) if self.tool_candidates else "none"
        outputs = ",".join(self.outputs) if self.outputs else "none"
        return (
            f"{self.stage_id} | owner={self.owner} | title={self.title} | "
            f"objective={self.objective} | tools={tools} | outputs={outputs}"
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
        )


class WorkflowComposer:
    """Compose deterministic workflow stages from routing and retrieval results."""

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
            return self._compose_bioinformatics(
                classification=classification,
                request_text=request_text,
                requested_outputs=requested_outputs,
                retrieval=retrieval,
            )
        if classification.domain == TaskDomain.SYSTEM:
            return self._compose_system(
                classification=classification,
                request_text=request_text,
                requested_outputs=requested_outputs,
                retrieval=retrieval,
            )
        return self._compose_knowledge(
            classification=classification,
            request_text=request_text,
            requested_outputs=requested_outputs,
            retrieval=retrieval,
        )

    def _compose_bioinformatics(
        self,
        *,
        classification: IntentClassification,
        request_text: str,
        requested_outputs: list[str],
        retrieval: RetrievalBundle,
    ) -> WorkflowTemplate:
        targets = classification.analysis_targets or ["generic_genetics_workflow"]
        deliverables = requested_outputs or ["analysis_blueprint", "report_outline"]
        stages = [
            self._stage(
                stage_id="stage_01_intake",
                title="Intake and Scope Normalization",
                owner="orchestrator",
                objective=f"Normalize the genetics request and capture targets: {', '.join(targets)}.",
                outputs=["request_scope", "input_contract"],
                domain=classification.domain,
                notes=[f"matched_keywords={','.join(classification.matched_keywords) or 'none'}"],
            ),
            self._stage(
                stage_id="stage_02_retrieval",
                title="Local-First Context Retrieval",
                owner="llm_orchestrator",
                objective=(
                    f"Resolve local planning context first; retrieval_mode={retrieval.retrieval_mode}; "
                    f"coverage={retrieval.coverage}."
                ),
                outputs=["retrieval_context", "method_notes"],
                domain=classification.domain,
                notes=retrieval.rationale,
            ),
            self._stage(
                stage_id="stage_03_tool_bootstrap",
                title="Tool Manifest Selection",
                owner="llm_orchestrator",
                objective="Select deterministic tool manifests for planning-only execution.",
                outputs=["tool_selection"],
                domain=classification.domain,
                notes=["No real tool invocation occurs in this skeleton stage."],
            ),
            self._stage(
                stage_id="stage_04_domain_blueprint",
                title="Genetics Pipeline Blueprint",
                owner="popgen_quantgen",
                objective=f"Draft QC, structure, relatedness, and prediction workflow for: {', '.join(targets)}.",
                outputs=["pipeline_blueprint", *deliverables],
                domain=classification.domain,
                notes=[
                    "Do not fabricate scientific results.",
                    "Stop at workflow design, expected inputs, and evaluation placeholders.",
                ],
            ),
            self._stage(
                stage_id="stage_05_resource_and_gate",
                title="Resource and Safety Review",
                owner="hpc_scheduler",
                objective="Attach conservative resources and stop at dry-run gating.",
                outputs=["resource_estimate", "gate_stage_status"],
                domain=classification.domain,
                notes=["High-risk actions remain subject to manual confirmation."],
            ),
            self._stage(
                stage_id="stage_06_handoff",
                title="Memory Handoff and Stable Deliverables",
                owner="orchestrator",
                objective="Persist stage handoff placeholders for downstream execution and tests.",
                outputs=["memory_handoff", "deliverable_contract"],
                domain=classification.domain,
                notes=[f"request_excerpt={request_text[:80]}"],
            ),
        ]
        return WorkflowTemplate.from_stages(
            name="bioinformatics-analysis-mvp",
            domain=classification.domain,
            stages=stages,
            retrieval_mode=retrieval.retrieval_mode,
        )

    def _compose_system(
        self,
        *,
        classification: IntentClassification,
        request_text: str,
        requested_outputs: list[str],
        retrieval: RetrievalBundle,
    ) -> WorkflowTemplate:
        deliverables = requested_outputs or ["diagnostic_outline"]
        stages = [
            self._stage(
                stage_id="stage_01_intake",
                title="Diagnostic Intake",
                owner="orchestrator",
                objective="Normalize the troubleshooting request and capture sanitized diagnostic scope.",
                outputs=["request_scope", "sanitized_request"],
                domain=classification.domain,
                notes=[f"matched_keywords={','.join(classification.matched_keywords) or 'none'}"],
            ),
            self._stage(
                stage_id="stage_02_retrieval",
                title="Local Troubleshooting Retrieval",
                owner="llm_orchestrator",
                objective=(
                    f"Search local diagnostic guidance first; retrieval_mode={retrieval.retrieval_mode}; "
                    f"coverage={retrieval.coverage}."
                ),
                outputs=["retrieval_context"],
                domain=classification.domain,
                notes=retrieval.rationale,
            ),
            self._stage(
                stage_id="stage_03_tool_bootstrap",
                title="Diagnostic Tool Selection",
                owner="llm_orchestrator",
                objective="Select planning-time tools for sanitization, diagnostics, and safe scheduler preview.",
                outputs=["tool_selection"],
                domain=classification.domain,
                notes=["Keep output diagnostic-only when retrieval remains incomplete."],
            ),
            self._stage(
                stage_id="stage_04_domain_blueprint",
                title="Diagnostic Workflow Draft",
                owner="llm_orchestrator",
                objective="Draft the next diagnostic steps without claiming unavailable runtime evidence.",
                outputs=["diagnostic_outline", *deliverables],
                domain=classification.domain,
                notes=["Prefer log normalization and safe reproduction steps before escalation."],
            ),
            self._stage(
                stage_id="stage_05_resource_and_gate",
                title="Risk and Dry-Run Review",
                owner="safety_fuse",
                objective="Confirm the request stays within sanitized text and dry-run boundaries.",
                outputs=["gate_stage_status"],
                domain=classification.domain,
                notes=["Block unsafe data export requests before any downstream action."],
            ),
            self._stage(
                stage_id="stage_06_handoff",
                title="Diagnostic Memory Handoff",
                owner="orchestrator",
                objective="Persist a deterministic handoff record for later scheduler or tool integration.",
                outputs=["memory_handoff", "deliverable_contract"],
                domain=classification.domain,
                notes=[f"request_excerpt={request_text[:80]}"],
            ),
        ]
        return WorkflowTemplate.from_stages(
            name="system-diagnosis-mvp",
            domain=classification.domain,
            stages=stages,
            retrieval_mode=retrieval.retrieval_mode,
        )

    def _compose_knowledge(
        self,
        *,
        classification: IntentClassification,
        request_text: str,
        requested_outputs: list[str],
        retrieval: RetrievalBundle,
    ) -> WorkflowTemplate:
        deliverables = requested_outputs or ["response_outline"]
        stages = [
            self._stage(
                stage_id="stage_01_intake",
                title="Knowledge Request Intake",
                owner="orchestrator",
                objective="Capture the requested topic, constraints, and preferred answer shape.",
                outputs=["request_scope"],
                domain=classification.domain,
                notes=[f"matched_keywords={','.join(classification.matched_keywords) or 'none'}"],
            ),
            self._stage(
                stage_id="stage_02_retrieval",
                title="Local Knowledge Retrieval",
                owner="llm_orchestrator",
                objective=(
                    f"Retrieve local SOP and FAQ context first; retrieval_mode={retrieval.retrieval_mode}; "
                    f"coverage={retrieval.coverage}."
                ),
                outputs=["retrieval_context"],
                domain=classification.domain,
                notes=retrieval.rationale,
            ),
            self._stage(
                stage_id="stage_03_tool_bootstrap",
                title="Response Tool Selection",
                owner="llm_orchestrator",
                objective="Select non-executing planning tools for response assembly.",
                outputs=["tool_selection"],
                domain=classification.domain,
                notes=["Keep external retrieval as a placeholder until a real connector is wired in."],
            ),
            self._stage(
                stage_id="stage_04_domain_blueprint",
                title="Response Blueprint",
                owner="llm_orchestrator",
                objective="Draft a grounded response outline from retrieval results and explicit gaps.",
                outputs=["response_outline", *deliverables],
                domain=classification.domain,
                notes=["State uncertainty explicitly when local material is incomplete."],
            ),
            self._stage(
                stage_id="stage_05_resource_and_gate",
                title="Safety Review",
                owner="safety_fuse",
                objective="Confirm only sanitized text can leave the local environment if fallback is later enabled.",
                outputs=["gate_stage_status"],
                domain=classification.domain,
                notes=["No raw genomic files or full sample identifiers may be exposed."],
            ),
            self._stage(
                stage_id="stage_06_handoff",
                title="Memory Handoff",
                owner="orchestrator",
                objective="Persist a deterministic planning record for downstream execution or review.",
                outputs=["memory_handoff", "deliverable_contract"],
                domain=classification.domain,
                notes=[f"request_excerpt={request_text[:80]}"],
            ),
        ]
        return WorkflowTemplate.from_stages(
            name="knowledge-response-mvp",
            domain=classification.domain,
            stages=stages,
            retrieval_mode=retrieval.retrieval_mode,
        )

    def _stage(
        self,
        *,
        stage_id: str,
        title: str,
        owner: str,
        objective: str,
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
            outputs=outputs,
            tool_candidates=tool_candidates,
            notes=notes,
        )
