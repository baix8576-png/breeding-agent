"""Orchestration service that drafts plans without executing business workflows yet."""

from __future__ import annotations

import hashlib

from contracts.common import GateStatus, RoleOutputHeader
from contracts.execution import PipelineSpec, RunContext, TaskPlan
from contracts.tasks import UserRequest
from knowledge.retrieval import KnowledgeResolver
from memory.stores import MemoryCoordinator
from orchestration.router import IntentRouter
from orchestration.workflow import WorkflowComposer
from safety.circuit_breaker import CircuitBreaker
from safety.gates import SafetyGateService, SafetyReviewContext
from scheduler.resource_estimator import ConservativeResourceEstimator
from tools.registry import ToolRegistry


class OrchestratorService:
    """Entry service for turning a user request into a draft execution plan."""

    def __init__(
        self,
        resource_estimator: ConservativeResourceEstimator,
        safety_gate: SafetyGateService,
        circuit_breaker: CircuitBreaker,
        intent_router: IntentRouter | None = None,
        knowledge_resolver: KnowledgeResolver | None = None,
        tool_registry: ToolRegistry | None = None,
        memory_coordinator: MemoryCoordinator | None = None,
    ) -> None:
        self._resource_estimator = resource_estimator
        self._safety_gate = safety_gate
        self._circuit_breaker = circuit_breaker
        self._intent_router = intent_router or IntentRouter()
        self._knowledge_resolver = knowledge_resolver or KnowledgeResolver()
        self._tool_registry = tool_registry or ToolRegistry()
        self._tool_registry.bootstrap_defaults()
        self._memory_coordinator = memory_coordinator or MemoryCoordinator()
        self._workflow_composer = WorkflowComposer(tool_registry=self._tool_registry)

    def draft_plan(self, request: UserRequest, run_context: RunContext | None = None) -> TaskPlan:
        """Generate a stable planning skeleton from free-form text."""

        classification = self._intent_router.analyze(request.text)
        resolved_context = self._resolve_run_context(
            request=request,
            run_context=run_context,
            domain_key=classification.domain.value,
        )
        retrieval = self._knowledge_resolver.resolve(query=request.text, domain=classification.domain)
        workflow = self._workflow_composer.compose(
            classification=classification,
            request_text=request.text,
            requested_outputs=sorted(set(request.requested_outputs)),
            retrieval=retrieval,
        )
        run_record = self._memory_coordinator.plan_run(
            task_id=resolved_context.task_id,
            run_id=resolved_context.run_id,
            request_text=request.text,
            domain=classification.domain,
            stage_specs=[
                {
                    "stage_id": stage.stage_id,
                    "owner": stage.owner,
                    "outputs": stage.outputs,
                    "notes": stage.notes,
                }
                for stage in workflow.stages
            ],
            available_tools=workflow.referenced_tools,
            retrieval_sources=retrieval.source_labels,
        )
        estimate = self._resource_estimator.estimate_for_domain(classification.domain)
        gate_stage_present = any(stage.stage_id == "stage_05_resource_and_gate" for stage in workflow.stages)
        gate_ready = gate_stage_present and self._circuit_breaker.allows_automatic_submission()
        risks = [
            "This plan is a workflow skeleton and does not submit jobs yet.",
            "Tool manifests describe planning contracts, not completed execution.",
        ]
        if retrieval.fallback_used:
            risks.append("Local knowledge coverage was incomplete, so external retrieval remains placeholder-only.")
        if classification.risk_hints:
            risks.append(f"Potential risk hints detected: {', '.join(classification.risk_hints)}.")
        header = RoleOutputHeader(
            role="orchestrator",
            task_id=resolved_context.task_id,
            run_id=resolved_context.run_id,
            scope_in=[
                "user_request",
                "runtime_settings",
                "local_knowledge_base",
                "tool_registry",
                "memory_store",
            ],
            scope_out=[
                "draft_plan",
                "retrieval_context",
                "tool_plan",
                "memory_handoff",
                "resource_placeholder",
                "pipeline_spec",
            ],
            risks=risks,
            next_actions=[
                "Bind manifest names to concrete tool implementations.",
                "Wire scheduler dry-run and polling outputs into stage transitions.",
                "Add regression tests against the stable workflow step format.",
            ],
            ready_for_gate=GateStatus.DESIGN_PASS if gate_ready else GateStatus.NOT_READY,
        )
        return TaskPlan(
            header=header,
            run_context=resolved_context,
            summary=(
                f"{classification.domain.value} workflow skeleton ready; "
                f"name={workflow.name}; stages={len(workflow.stages)}; "
                f"retrieval={retrieval.retrieval_mode}; tools={len(workflow.referenced_tools)}"
            ),
            domain=classification.domain,
            workflow_name=workflow.name,
            workflow_steps=workflow.steps,
            assumptions=[
                "Raw genomic data remains on the local cluster.",
                "External retrieval remains placeholder-only until a sanitized connector is wired in.",
                "Workflow stages are planning contracts, not evidence of completed analysis.",
                f"run_id={resolved_context.run_id}",
                f"retrieval_coverage={retrieval.coverage}",
                f"gate_stage_status={'design_pass' if gate_ready else 'not_ready'}",
                f"memory_handoffs={len(run_record.handoffs)}",
                f"stable_outputs={','.join(workflow.stable_outputs)}",
            ],
            deliverables=[
                "parsed_request_summary",
                f"workflow_stage_map:{','.join(stage.stage_id for stage in workflow.stages)}",
                f"context_sources:{','.join(retrieval.source_labels) if retrieval.source_labels else 'none'}",
                f"tool_registry_selection:{','.join(workflow.referenced_tools) if workflow.referenced_tools else 'none'}",
                f"memory_handoff_count:{len(run_record.handoffs)}",
                "resource_placeholder",
            ],
            required_roles=workflow.required_roles,
            pipeline_spec=PipelineSpec(
                name=workflow.name,
                domain=classification.domain,
                stages=workflow.steps,
                requested_outputs=request.requested_outputs,
                deliverables=workflow.stable_outputs,
            ),
            resource_estimate=estimate,
        )

    def review_high_risk_action(self, action_name: str, run_context: RunContext | None = None) -> dict[str, str]:
        """Forward an action through the safety gate until runtime wiring is complete."""

        resolved_context = run_context or RunContext(task_id="compat-task", run_id="compat-run")
        decision = self._safety_gate.review(
            context=SafetyReviewContext(
                task_id=resolved_context.task_id,
                run_id=resolved_context.run_id,
                action_name=action_name,
            )
        )
        return {
            "action_name": action_name,
            "decision": decision.decision.value,
            "risk_level": decision.risk_level.value,
        }

    def _build_task_id(self, request: UserRequest, domain_key: str) -> str:
        normalized = "|".join(
            [
                domain_key,
                request.text.strip().lower(),
                request.working_directory or "",
            ]
        )
        digest = hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:10]
        return f"task-{domain_key}-{digest}"

    def _resolve_run_context(
        self,
        request: UserRequest,
        run_context: RunContext | None,
        domain_key: str,
    ) -> RunContext:
        if run_context is not None:
            return run_context.model_copy(
                update={
                    "working_directory": run_context.working_directory or request.working_directory,
                }
            )
        task_id = self._build_task_id(request=request, domain_key=domain_key)
        return RunContext(
            task_id=task_id,
            run_id=task_id,
            working_directory=request.working_directory,
        )
