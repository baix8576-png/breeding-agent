"""Tool registry and manifest catalog for GeneAgent V1."""

from __future__ import annotations

from pydantic import BaseModel, Field

from contracts.common import TaskDomain


class ToolManifest(BaseModel):
    """Manifest definition for future genetics and scheduler tools."""

    name: str
    description: str = ""
    category: str = "workflow"
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    preconditions: list[str] = Field(default_factory=list)
    resource_requirements: list[str] = Field(default_factory=list)
    error_codes: list[str] = Field(default_factory=list)
    supports_dry_run: bool = True
    stage_scope: list[str] = Field(default_factory=list)
    domain_scope: list[str] = Field(default_factory=list)


class ToolRegistry:
    """In-memory registry for tool manifests."""

    def __init__(self) -> None:
        self._items: dict[str, ToolManifest] = {}

    def register(self, manifest: ToolManifest) -> None:
        self._items[manifest.name] = manifest

    def register_many(self, manifests: list[ToolManifest]) -> None:
        for manifest in manifests:
            self.register(manifest)

    def bootstrap_defaults(self) -> None:
        """Load the starter manifest set once for workflow planning."""

        if self._items:
            return

        shared = "shared"
        self.register_many(
            [
                ToolManifest(
                    name="input_contract_reader",
                    description="Normalize request scope into expected input classes and path requirements.",
                    inputs=["user_request"],
                    outputs=["input_contract"],
                    preconditions=["natural-language request available"],
                    stage_scope=["stage_01_intake", "stage_02_intent_and_scope", "stage_03_input_validation", "lite_01_intake"],
                    domain_scope=[shared, TaskDomain.BIOINFORMATICS.value, TaskDomain.KNOWLEDGE.value],
                ),
                ToolManifest(
                    name="local_context_search",
                    description="Retrieve local SOP, FAQ, template, and documentation context before any external fallback.",
                    inputs=["query", "task_domain"],
                    outputs=["local_context_hits"],
                    preconditions=["local knowledge index available"],
                    stage_scope=["stage_04_local_first_rag", "lite_02_local_retrieval"],
                    domain_scope=[shared, TaskDomain.BIOINFORMATICS.value, TaskDomain.KNOWLEDGE.value, TaskDomain.SYSTEM.value],
                ),
                ToolManifest(
                    name="external_context_fallback",
                    description="Attach external fallback guidance only when local context coverage is insufficient.",
                    inputs=["query", "task_domain", "sanitized_request"],
                    outputs=["external_context_hits"],
                    preconditions=["local retrieval coverage below threshold"],
                    stage_scope=["stage_04_local_first_rag", "lite_02_local_retrieval"],
                    domain_scope=[shared, TaskDomain.BIOINFORMATICS.value, TaskDomain.KNOWLEDGE.value, TaskDomain.SYSTEM.value],
                ),
                ToolManifest(
                    name="tool_manifest_selector",
                    description="Select manifests for the current workflow stage without invoking real execution.",
                    inputs=["task_domain", "stage_id"],
                    outputs=["tool_selection"],
                    preconditions=["registry bootstrapped"],
                    stage_scope=["stage_05_blueprint_selection", "lite_03_answer_blueprint"],
                    domain_scope=[shared, TaskDomain.BIOINFORMATICS.value, TaskDomain.KNOWLEDGE.value, TaskDomain.SYSTEM.value],
                ),
                ToolManifest(
                    name="genetics_pipeline_blueprint",
                    description="Draft QC, structure, relatedness, and prediction modeling stages for genetics analysis.",
                    inputs=["input_contract", "analysis_targets"],
                    outputs=["pipeline_blueprint"],
                    preconditions=["bioinformatics domain selected"],
                    stage_scope=["stage_05_blueprint_selection"],
                    domain_scope=[TaskDomain.BIOINFORMATICS.value],
                ),
                ToolManifest(
                    name="knowledge_response_scaffold",
                    description="Draft a response outline when the task is knowledge-oriented rather than execution-oriented.",
                    inputs=["retrieval_context", "request_scope"],
                    outputs=["response_outline"],
                    preconditions=["knowledge domain selected"],
                    stage_scope=["lite_03_answer_blueprint"],
                    domain_scope=[TaskDomain.KNOWLEDGE.value],
                ),
                ToolManifest(
                    name="diagnostic_outline_builder",
                    description="Produce a diagnostic route for system or log triage without inventing tool outputs.",
                    inputs=["sanitized_logs", "request_scope"],
                    outputs=["diagnostic_outline"],
                    preconditions=["system domain selected"],
                    stage_scope=["lite_03_answer_blueprint"],
                    domain_scope=[TaskDomain.SYSTEM.value],
                ),
                ToolManifest(
                    name="resource_estimator",
                    description="Attach a conservative resource envelope before dry-run submission.",
                    inputs=["task_domain", "analysis_targets"],
                    outputs=["resource_estimate"],
                    preconditions=["workflow stage map ready"],
                    stage_scope=["stage_06_resource_and_safety_gate"],
                    domain_scope=[shared, TaskDomain.BIOINFORMATICS.value, TaskDomain.SYSTEM.value, TaskDomain.KNOWLEDGE.value],
                ),
                ToolManifest(
                    name="safety_gate_review",
                    description="Review risk class and manual confirmation requirements before any execution path.",
                    inputs=["action_summary", "resource_estimate"],
                    outputs=["gate_decision"],
                    preconditions=["risk factors available"],
                    stage_scope=["stage_06_resource_and_safety_gate", "lite_04_optional_safety_review"],
                    domain_scope=[shared, TaskDomain.BIOINFORMATICS.value, TaskDomain.SYSTEM.value, TaskDomain.KNOWLEDGE.value],
                ),
                ToolManifest(
                    name="scheduler_dry_run_preview",
                    description="Prepare a scheduler-facing dry-run preview instead of submitting a real job.",
                    inputs=["resource_estimate", "working_directory"],
                    outputs=["submission_preview"],
                    preconditions=["scheduler adapter configured"],
                    stage_scope=["stage_06_resource_and_safety_gate", "stage_07_execution"],
                    domain_scope=[TaskDomain.BIOINFORMATICS.value, TaskDomain.SYSTEM.value],
                ),
                ToolManifest(
                    name="memory_handoff_builder",
                    description="Persist stage handoff records for execution-time traceability and enrichment.",
                    inputs=["workflow_stage_map", "retrieval_context", "tool_selection"],
                    outputs=["memory_handoff"],
                    preconditions=["workflow stages ready"],
                    stage_scope=["stage_09_audit_and_memory", "lite_04_optional_safety_review"],
                    domain_scope=[shared, TaskDomain.BIOINFORMATICS.value, TaskDomain.KNOWLEDGE.value, TaskDomain.SYSTEM.value],
                ),
                ToolManifest(
                    name="report_contract_builder",
                    description="Define stable deliverable names for tests and downstream report generation.",
                    inputs=["workflow_stage_map", "requested_outputs"],
                    outputs=["deliverable_contract"],
                    preconditions=["handoff state defined"],
                    stage_scope=["stage_08_artifact_and_report", "lite_03_answer_blueprint"],
                    domain_scope=[shared, TaskDomain.BIOINFORMATICS.value, TaskDomain.KNOWLEDGE.value, TaskDomain.SYSTEM.value],
                ),
            ]
        )

    def get(self, name: str) -> ToolManifest | None:
        return self._items.get(name)

    def list_names(self) -> list[str]:
        return sorted(self._items)

    def list_for_stage(self, stage_id: str, domain: TaskDomain) -> list[ToolManifest]:
        """Return manifests applicable to the given stage and domain."""

        domain_key = domain.value
        manifests = [
            manifest
            for manifest in self._items.values()
            if (not manifest.stage_scope or stage_id in manifest.stage_scope)
            and (
                not manifest.domain_scope
                or "shared" in manifest.domain_scope
                or domain_key in manifest.domain_scope
            )
        ]
        manifests.sort(key=lambda item: item.name)
        return manifests
