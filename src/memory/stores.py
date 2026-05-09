"""In-memory stores used until persistent storage is introduced."""

from __future__ import annotations

from pydantic import BaseModel, Field

from contracts.common import TaskDomain


class SessionRecord(BaseModel):
    """Short-term conversation state."""

    session_id: str
    messages: list[str] = Field(default_factory=list)
    last_task_id: str | None = None
    active_domain: TaskDomain | None = None
    run_ids: list[str] = Field(default_factory=list)
    project_ids: list[str] = Field(default_factory=list)
    handoff_summaries: list[str] = Field(default_factory=list)


class StageSnapshot(BaseModel):
    """Planned or completed stage state stored for later handoff."""

    stage_id: str
    owner: str
    status: str = "planned"
    outputs: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class WorkflowHandoff(BaseModel):
    """Context passed from one workflow stage to the next."""

    task_id: str
    run_id: str
    from_stage: str
    to_stage: str
    summary: str
    carried_context: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)


class RunRecord(BaseModel):
    """Single execution trace stored by the worker runtime."""

    run_id: str
    task_id: str
    project_id: str | None = None
    input_summary: str
    job_ids: list[str] = Field(default_factory=list)
    domain: TaskDomain | None = None
    request_text: str = ""
    available_tools: list[str] = Field(default_factory=list)
    retrieval_sources: list[str] = Field(default_factory=list)
    stage_history: list[StageSnapshot] = Field(default_factory=list)
    handoffs: list[WorkflowHandoff] = Field(default_factory=list)
    session_id: str | None = None
    planning_summary: str | None = None
    submission_commands: list[str] = Field(default_factory=list)
    log_paths: list[str] = Field(default_factory=list)
    manual_confirmation_records: list[str] = Field(default_factory=list)
    artifact_index: dict[str, list[str]] = Field(default_factory=dict)
    report_summary: str | None = None
    audit_paths: list[str] = Field(default_factory=list)
    failure_records: list["FailureRecord"] = Field(default_factory=list)
    approval_records: list["ApprovalRecord"] = Field(default_factory=list)
    provenance_records: list["ProvenanceRecord"] = Field(default_factory=list)


class FailureRecord(BaseModel):
    """Failure-level memory for retry and diagnostics."""

    run_id: str
    stage_id: str
    error_code: str
    message: str
    retryable: bool = False
    retry_suggestion: str | None = None
    tool_name: str | None = None


class ApprovalRecord(BaseModel):
    """Manual approval evidence captured during safety gating."""

    run_id: str
    stage_id: str
    decision: str
    reason: str
    scope: list[str] = Field(default_factory=list)
    approver: str = "human"


class ProvenanceRecord(BaseModel):
    """Provenance trace linking artifacts, commands, and audit outputs."""

    run_id: str
    stage_id: str
    source_type: str
    source_ref: str
    artifact_path: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


class ProjectRecord(BaseModel):
    """Project-level long-memory index across sessions and runs."""

    project_id: str
    run_ids: list[str] = Field(default_factory=list)
    session_ids: list[str] = Field(default_factory=list)
    task_ids: list[str] = Field(default_factory=list)
    domains: list[TaskDomain] = Field(default_factory=list)
    run_summaries: list[str] = Field(default_factory=list)
    failure_records: list[FailureRecord] = Field(default_factory=list)
    approval_records: list[ApprovalRecord] = Field(default_factory=list)
    provenance_records: list[ProvenanceRecord] = Field(default_factory=list)


class InMemorySessionStore:
    """Simple in-process store for session context."""

    def __init__(self) -> None:
        self._items: dict[str, SessionRecord] = {}

    def save(self, record: SessionRecord) -> None:
        self._items[record.session_id] = record

    def get(self, session_id: str) -> SessionRecord | None:
        return self._items.get(session_id)


class InMemoryRunStore:
    """Simple in-process store for run context."""

    def __init__(self) -> None:
        self._items: dict[str, RunRecord] = {}

    def save(self, record: RunRecord) -> None:
        self._items[record.run_id] = record

    def get(self, run_id: str) -> RunRecord | None:
        return self._items.get(run_id)


class InMemoryProjectStore:
    """Simple in-process store for project-level context."""

    def __init__(self) -> None:
        self._items: dict[str, ProjectRecord] = {}

    def save(self, record: ProjectRecord) -> None:
        self._items[record.project_id] = record

    def get(self, project_id: str) -> ProjectRecord | None:
        return self._items.get(project_id)


class MemoryCoordinator:
    """Create deterministic run records and stage handoff summaries."""

    def __init__(
        self,
        session_store: InMemorySessionStore | None = None,
        run_store: InMemoryRunStore | None = None,
        project_store: InMemoryProjectStore | None = None,
    ) -> None:
        self._session_store = session_store or InMemorySessionStore()
        self._run_store = run_store or InMemoryRunStore()
        self._project_store = project_store or InMemoryProjectStore()

    def plan_run(
        self,
        *,
        task_id: str,
        run_id: str,
        request_text: str,
        domain: TaskDomain,
        stage_specs: list[dict[str, object]],
        available_tools: list[str],
        retrieval_sources: list[str],
        session_id: str | None = None,
        project_id: str | None = None,
    ) -> RunRecord:
        """Persist a deterministic run plan and return the resulting record."""

        stage_history = [
            StageSnapshot(
                stage_id=str(stage["stage_id"]),
                owner=str(stage["owner"]),
                outputs=list(stage.get("outputs", [])),
                notes=list(stage.get("notes", [])),
            )
            for stage in stage_specs
        ]

        handoffs: list[WorkflowHandoff] = []
        for index in range(len(stage_history) - 1):
            current_stage = stage_history[index]
            next_stage = stage_history[index + 1]
            handoffs.append(
                WorkflowHandoff(
                    task_id=task_id,
                    run_id=run_id,
                    from_stage=current_stage.stage_id,
                    to_stage=next_stage.stage_id,
                    summary=(
                        f"Carry outputs from {current_stage.stage_id} to {next_stage.stage_id} "
                        "without recomputing previous stage decisions."
                    ),
                    carried_context=[
                        f"owner={current_stage.owner}",
                        f"outputs={','.join(current_stage.outputs) if current_stage.outputs else 'none'}",
                    ],
                    open_questions=[
                        "Attach runtime observations after this stage executes to complete the handoff trace."
                    ],
                )
            )

        resolved_project_id = self._resolve_project_id(
            project_id=project_id,
            task_id=task_id,
            session_id=session_id,
        )
        record = RunRecord(
            run_id=run_id,
            task_id=task_id,
            project_id=resolved_project_id,
            input_summary=request_text[:160],
            domain=domain,
            request_text=request_text,
            available_tools=available_tools,
            retrieval_sources=retrieval_sources,
            stage_history=stage_history,
            handoffs=handoffs,
            session_id=session_id,
            planning_summary=f"Draft plan prepared with {len(stage_history)} stages.",
        )
        self._run_store.save(record)
        self._upsert_session(
            session_id=session_id,
            task_id=task_id,
            run_id=run_id,
            project_id=resolved_project_id,
            domain=domain,
            messages=[f"plan_run:{run_id}"],
            handoff_summaries=[handoff.summary for handoff in handoffs],
        )
        self._upsert_project(
            project_id=resolved_project_id,
            run_id=run_id,
            session_id=session_id,
            task_id=task_id,
            domain=domain,
            run_summary=record.planning_summary or "",
        )
        return record

    def record_execution_closure(
        self,
        *,
        task_id: str,
        run_id: str,
        session_id: str | None,
        project_id: str | None,
        domain: TaskDomain,
        input_summary: str,
        planning_summary: str,
        submission_command: str,
        job_id: str,
        log_paths: list[str],
        manual_confirmation_records: list[str],
        artifact_index: dict[str, list[str]],
        report_summary: str,
        audit_path: str | None,
    ) -> RunRecord:
        """Write back stage-3 runtime closure context for run and session scopes."""

        record = self._run_store.get(run_id)
        if record is None:
            record = RunRecord(
                run_id=run_id,
                task_id=task_id,
                project_id=project_id,
                input_summary=input_summary[:160],
                domain=domain,
                session_id=session_id,
            )

        resolved_project_id = self._resolve_project_id(
            project_id=project_id or record.project_id,
            task_id=task_id,
            session_id=session_id,
        )
        record.task_id = task_id
        record.domain = domain
        record.session_id = session_id
        record.project_id = resolved_project_id
        record.input_summary = input_summary[:160]
        record.planning_summary = planning_summary
        self._append_unique(record.job_ids, [job_id])
        self._append_unique(record.submission_commands, [submission_command])
        self._append_unique(record.log_paths, [path for path in log_paths if path])
        self._append_unique(record.manual_confirmation_records, [item for item in manual_confirmation_records if item])
        record.artifact_index = self._merge_artifact_index(record.artifact_index, artifact_index)
        record.report_summary = report_summary
        if audit_path:
            self._append_unique(record.audit_paths, [audit_path])
        self._append_approval_records(
            record=record,
            run_id=run_id,
            manual_confirmation_records=manual_confirmation_records,
        )
        self._append_provenance_records(
            record=record,
            run_id=run_id,
            submission_command=submission_command,
            job_id=job_id,
            artifact_index=record.artifact_index,
            log_paths=record.log_paths,
            audit_path=audit_path,
        )

        lite_mode = any(snapshot.stage_id.startswith("lite_") for snapshot in record.stage_history)
        if lite_mode:
            self._mark_stage_completed(record.stage_history, "lite_03_answer_blueprint")
            self._mark_stage_completed(record.stage_history, "stage_09_audit_and_memory")
            closure_handoffs = [
                WorkflowHandoff(
                    task_id=task_id,
                    run_id=run_id,
                    from_stage="lite_03_answer_blueprint",
                    to_stage="stage_09_audit_and_memory",
                    summary="Lightweight answer artifacts indexed and audit-memory closure persisted.",
                    carried_context=[
                        f"job_id={job_id}",
                        f"audit_path={audit_path or 'in_memory_only'}",
                    ],
                    open_questions=[],
                )
            ]
        else:
            self._mark_stage_completed(record.stage_history, "stage_07_execution")
            self._mark_stage_completed(record.stage_history, "stage_08_artifact_and_report")
            self._mark_stage_completed(record.stage_history, "stage_09_audit_and_memory")
            closure_handoffs = [
                WorkflowHandoff(
                    task_id=task_id,
                    run_id=run_id,
                    from_stage="stage_07_execution",
                    to_stage="stage_08_artifact_and_report",
                    summary="Execution preview artifacts converted into a unified artifact/report index.",
                    carried_context=[
                        f"job_id={job_id}",
                        f"log_count={len(log_paths)}",
                    ],
                    open_questions=[],
                ),
                WorkflowHandoff(
                    task_id=task_id,
                    run_id=run_id,
                    from_stage="stage_08_artifact_and_report",
                    to_stage="stage_09_audit_and_memory",
                    summary="Audit trail persisted and memory context synced for downstream handoff.",
                    carried_context=[
                        f"audit_path={audit_path or 'in_memory_only'}",
                        f"manual_confirmation_count={len(manual_confirmation_records)}",
                    ],
                    open_questions=[],
                ),
            ]
        for handoff in closure_handoffs:
            if not self._has_handoff(record.handoffs, handoff):
                record.handoffs.append(handoff)

        self._run_store.save(record)
        self._upsert_session(
            session_id=session_id,
            task_id=task_id,
            run_id=run_id,
            project_id=resolved_project_id,
            domain=domain,
            messages=[f"execution_closure:{run_id}", report_summary],
            handoff_summaries=[handoff.summary for handoff in closure_handoffs],
        )
        self._upsert_project(
            project_id=resolved_project_id,
            run_id=run_id,
            session_id=session_id,
            task_id=task_id,
            domain=domain,
            run_summary=planning_summary,
            failure_records=record.failure_records,
            approval_records=record.approval_records,
            provenance_records=record.provenance_records,
        )
        return record

    def get_run(self, run_id: str) -> RunRecord | None:
        return self._run_store.get(run_id)

    def get_session(self, session_id: str) -> SessionRecord | None:
        return self._session_store.get(session_id)

    def get_project(self, project_id: str) -> ProjectRecord | None:
        return self._project_store.get(project_id)

    def record_failure(
        self,
        *,
        run_id: str,
        stage_id: str,
        error_code: str,
        message: str,
        retryable: bool,
        retry_suggestion: str | None = None,
        tool_name: str | None = None,
    ) -> None:
        """Record one execution failure for run/project memory layers."""

        record = self._run_store.get(run_id)
        if record is None:
            return
        failure = FailureRecord(
            run_id=run_id,
            stage_id=stage_id,
            error_code=error_code,
            message=message,
            retryable=retryable,
            retry_suggestion=retry_suggestion,
            tool_name=tool_name,
        )
        if failure not in record.failure_records:
            record.failure_records.append(failure)
        self._run_store.save(record)
        if record.project_id:
            self._upsert_project(
                project_id=record.project_id,
                run_id=record.run_id,
                session_id=record.session_id,
                task_id=record.task_id,
                domain=record.domain,
                run_summary=record.planning_summary or "",
                failure_records=record.failure_records,
            )

    def _upsert_session(
        self,
        *,
        session_id: str | None,
        task_id: str,
        run_id: str,
        project_id: str | None,
        domain: TaskDomain,
        messages: list[str],
        handoff_summaries: list[str],
    ) -> None:
        if not session_id:
            return
        existing = self._session_store.get(session_id) or SessionRecord(session_id=session_id)
        existing.last_task_id = task_id
        existing.active_domain = domain
        self._append_unique(existing.run_ids, [run_id])
        if project_id:
            self._append_unique(existing.project_ids, [project_id])
        self._append_unique(existing.messages, [message for message in messages if message])
        self._append_unique(existing.handoff_summaries, [summary for summary in handoff_summaries if summary])
        self._session_store.save(existing)

    def _upsert_project(
        self,
        *,
        project_id: str,
        run_id: str,
        session_id: str | None,
        task_id: str,
        domain: TaskDomain | None,
        run_summary: str,
        failure_records: list[FailureRecord] | None = None,
        approval_records: list[ApprovalRecord] | None = None,
        provenance_records: list[ProvenanceRecord] | None = None,
    ) -> None:
        existing = self._project_store.get(project_id) or ProjectRecord(project_id=project_id)
        self._append_unique(existing.run_ids, [run_id])
        if session_id:
            self._append_unique(existing.session_ids, [session_id])
        self._append_unique(existing.task_ids, [task_id])
        if domain is not None and domain not in existing.domains:
            existing.domains.append(domain)
        if run_summary and run_summary not in existing.run_summaries:
            existing.run_summaries.append(run_summary)
        if failure_records:
            for item in failure_records:
                if item not in existing.failure_records:
                    existing.failure_records.append(item)
        if approval_records:
            for item in approval_records:
                if item not in existing.approval_records:
                    existing.approval_records.append(item)
        if provenance_records:
            for item in provenance_records:
                if item not in existing.provenance_records:
                    existing.provenance_records.append(item)
        self._project_store.save(existing)

    def _resolve_project_id(
        self,
        *,
        project_id: str | None,
        task_id: str,
        session_id: str | None,
    ) -> str:
        if project_id:
            return project_id
        if session_id:
            return f"project-{session_id}"
        return f"project-{task_id}"

    def _append_approval_records(
        self,
        *,
        record: RunRecord,
        run_id: str,
        manual_confirmation_records: list[str],
    ) -> None:
        for item in manual_confirmation_records:
            normalized = item.strip()
            if not normalized:
                continue
            approval = ApprovalRecord(
                run_id=run_id,
                stage_id="stage_06_resource_and_safety_gate",
                decision="confirmed",
                reason=normalized,
                scope=["scheduler_submit"],
                approver="human",
            )
            if approval not in record.approval_records:
                record.approval_records.append(approval)

    def _append_provenance_records(
        self,
        *,
        record: RunRecord,
        run_id: str,
        submission_command: str,
        job_id: str,
        artifact_index: dict[str, list[str]],
        log_paths: list[str],
        audit_path: str | None,
    ) -> None:
        provenance_candidates: list[ProvenanceRecord] = [
            ProvenanceRecord(
                run_id=run_id,
                stage_id="stage_07_execution",
                source_type="submission_command",
                source_ref=submission_command,
                metadata={"job_id": job_id},
            ),
        ]
        for log_path in log_paths:
            if not log_path:
                continue
            provenance_candidates.append(
                ProvenanceRecord(
                    run_id=run_id,
                    stage_id="stage_07_execution",
                    source_type="log_path",
                    source_ref=log_path,
                    artifact_path=log_path,
                )
            )
        for kind, paths in artifact_index.items():
            for path in paths:
                if not path:
                    continue
                provenance_candidates.append(
                    ProvenanceRecord(
                        run_id=run_id,
                        stage_id="stage_08_artifact_and_report",
                        source_type=f"artifact:{kind}",
                        source_ref=path,
                        artifact_path=path,
                    )
                )
        if audit_path:
            provenance_candidates.append(
                ProvenanceRecord(
                    run_id=run_id,
                    stage_id="stage_09_audit_and_memory",
                    source_type="audit_path",
                    source_ref=audit_path,
                    artifact_path=audit_path,
                )
            )
        for item in provenance_candidates:
            if item not in record.provenance_records:
                record.provenance_records.append(item)

    def _append_unique(self, target: list[str], values: list[str]) -> None:
        for value in values:
            if value not in target:
                target.append(value)

    def _merge_artifact_index(
        self,
        existing: dict[str, list[str]],
        incoming: dict[str, list[str]],
    ) -> dict[str, list[str]]:
        merged = {key: list(values) for key, values in existing.items()}
        for key, values in incoming.items():
            bucket = merged.setdefault(key, [])
            self._append_unique(bucket, [value for value in values if value])
        return merged

    def _mark_stage_completed(self, stage_history: list[StageSnapshot], stage_id: str) -> None:
        for snapshot in stage_history:
            if snapshot.stage_id == stage_id:
                snapshot.status = "completed"
                return
        stage_history.append(StageSnapshot(stage_id=stage_id, owner="runtime", status="completed"))

    def _has_handoff(self, handoffs: list[WorkflowHandoff], candidate: WorkflowHandoff) -> bool:
        return any(
            handoff.from_stage == candidate.from_stage
            and handoff.to_stage == candidate.to_stage
            and handoff.summary == candidate.summary
            for handoff in handoffs
        )
