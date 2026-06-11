"""Typer-based CLI entrypoint for GeneAgent V2 workflows."""

from __future__ import annotations

import json
import shutil
import shlex
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import typer
from rich.console import Console
from scheduler.base import SchedulerExecutionError
from scheduler.remote import SshControlMasterManager

from contracts.api import RequestIdentity
from contracts.common import ExecutionMode, SshAuthMode
from contracts.knowledge import KnowledgeItemV2
from contracts.validation import InputBundle, InputBundleEntry
from knowledge.ingestion import KnowledgeIngestionBridge
from knowledge.query_router import KnowledgeQueryRouter
from knowledge.runtime_store import KnowledgeRuntimeStore
from runtime.bootstrap import create_application_context

app = typer.Typer(help="GeneAgent CLI for local genetics workflow orchestration.")
knowledge_app = typer.Typer(help="Build and query the local runtime knowledge store.")
console = Console()
app.add_typer(knowledge_app, name="knowledge")


@knowledge_app.command("build-index")
def knowledge_build_index(
    runtime_root: str = typer.Option(
        ".geneagent/knowledge",
        "--runtime-root",
        help="Local ignored runtime knowledge root.",
    ),
    references_root: str = typer.Option(
        "references",
        "--references-root",
        help="Git-versioned references root to index.",
    ),
    source_file: list[str] | None = typer.Option(
        None,
        "--source-file",
        help="Specific Markdown source file to index; repeat for multiple files.",
    ),
) -> None:
    """Materialize reference knowledge chunks under the local runtime store."""

    store = KnowledgeRuntimeStore(runtime_root=Path(runtime_root))
    paths = [Path(path) for path in source_file] if source_file else None
    try:
        payload = store.build_from_references(Path(references_root), paths=paths)
    except ValueError as error:
        console.print_json(json.dumps({"error": str(error), "action": "knowledge_build_index"}))
        raise typer.Exit(code=1) from error
    console.print_json(json.dumps(payload.model_dump(mode="json")))


@knowledge_app.command("search")
def knowledge_search(
    query: str,
    runtime_root: str = typer.Option(
        ".geneagent/knowledge",
        "--runtime-root",
        help="Local ignored runtime knowledge root.",
    ),
    blueprint_scope: str | None = typer.Option(None, "--blueprint-scope"),
    species: str | None = typer.Option(None, "--species"),
    limit: int = typer.Option(5, "--limit", min=1),
    include_embedding: bool = typer.Option(True, "--include-embedding/--no-include-embedding"),
    use_persisted_bm25: bool = typer.Option(True, "--use-persisted-bm25/--rebuild-bm25"),
    use_query_router: bool = typer.Option(True, "--planned/--raw"),
    rerank: bool = typer.Option(True, "--rerank/--no-rerank"),
) -> None:
    """Search the persisted local runtime knowledge store."""

    store = KnowledgeRuntimeStore(runtime_root=Path(runtime_root))
    try:
        payload = store.search(
            query=query,
            blueprint_scope=blueprint_scope,
            species=species,
            limit=limit,
            include_embedding=include_embedding,
            use_persisted_bm25=use_persisted_bm25,
            use_query_router=use_query_router,
            rerank=rerank,
        )
    except (FileNotFoundError, ValueError) as error:
        console.print_json(json.dumps({"error": str(error), "action": "knowledge_search"}))
        raise typer.Exit(code=1) from error
    console.print_json(json.dumps(payload.model_dump(mode="json")))


@knowledge_app.command("ingest-tei")
def knowledge_ingest_tei(
    tei_path: str,
    doc_id: str = typer.Option(..., "--doc-id"),
    species: str = typer.Option(..., "--species"),
    blueprint_scope: str = typer.Option(..., "--blueprint-scope"),
    evidence_level: str = typer.Option(..., "--evidence-level"),
    source: str = typer.Option("paper", "--source"),
    owner: str = typer.Option("geneagent", "--owner"),
    updated_at: str | None = typer.Option(None, "--updated-at"),
    runtime_root: str = typer.Option(
        ".geneagent/knowledge",
        "--runtime-root",
        help="Local ignored runtime knowledge root.",
    ),
    rebuild_index: bool = typer.Option(True, "--rebuild-index/--no-rebuild-index"),
) -> None:
    """Ingest a local GROBID TEI file into the runtime knowledge store."""

    item = KnowledgeItemV2(
        doc_id=doc_id,
        version="v2",
        species=species,
        blueprint_scope=blueprint_scope,
        evidence_level=evidence_level,
        source=source,
        updated_at=updated_at or datetime.now(timezone.utc).isoformat(),
        owner=owner,
    )
    bridge = KnowledgeIngestionBridge(KnowledgeRuntimeStore(runtime_root=Path(runtime_root)))
    try:
        payload = bridge.ingest_grobid_tei(Path(tei_path), item=item, rebuild_index=rebuild_index)
    except (FileNotFoundError, ValueError) as error:
        console.print_json(json.dumps({"error": str(error), "action": "knowledge_ingest_tei"}))
        raise typer.Exit(code=1) from error
    console.print_json(json.dumps(payload.model_dump(mode="json")))


@knowledge_app.command("plan-query")
def knowledge_plan_query(query: str) -> None:
    """Plan metadata filters for a local-first knowledge query."""

    payload = KnowledgeQueryRouter().plan(query)
    console.print_json(json.dumps(payload.model_dump(mode="json")))


@knowledge_app.command("inspect-doc")
def knowledge_inspect_doc(
    doc_id: str,
    runtime_root: str = typer.Option(
        ".geneagent/knowledge",
        "--runtime-root",
        help="Local ignored runtime knowledge root.",
    ),
) -> None:
    """Inspect persisted chunks for one knowledge document id."""

    store = KnowledgeRuntimeStore(runtime_root=Path(runtime_root))
    try:
        payload = store.inspect_doc(doc_id)
    except (FileNotFoundError, ValueError) as error:
        console.print_json(json.dumps({"error": str(error), "action": "knowledge_inspect_doc"}))
        raise typer.Exit(code=1) from error
    console.print_json(json.dumps(payload.model_dump(mode="json")))


@app.command("plan")
def plan(
    request_text: str,
    task_id: str | None = None,
    run_id: str | None = None,
    session_id: str | None = None,
    working_directory: str | None = None,
    input_entry: list[str] | None = typer.Option(
        None,
        "--input-entry",
        help="Structured input entry in role=path form; repeat for multiple values.",
    ),
    input_species: str | None = typer.Option(None, "--input-species", help="Optional species label for InputBundle."),
    input_cohort: str | None = typer.Option(None, "--input-cohort", help="Optional cohort label for InputBundle."),
) -> None:
    """Draft a plan from a natural-language request."""

    context = create_application_context()
    plan_result = context.facade.draft_plan(
        text=request_text,
        identity=RequestIdentity(
            task_id=task_id,
            run_id=run_id,
            session_id=session_id,
            working_directory=working_directory,
        ),
        input_bundle=_build_cli_input_bundle(
            input_entries=input_entry,
            species=input_species,
            cohort_name=input_cohort,
        ),
    )
    console.print_json(json.dumps(plan_result.model_dump(mode="json")))


@app.command("report")
def report(
    working_directory: str | None = None,
    request_text: str = "Prepare report preview",
    requested_outputs: list[str] | None = typer.Option(
        None,
        "--requested-output",
        help="Requested report outputs; repeat this option for multiple values.",
    ),
    task_id: str | None = None,
    run_id: str | None = None,
    session_id: str | None = None,
) -> None:
    """Generate a report-oriented preview payload without adding runtime business logic here."""

    context = create_application_context()
    report_preview = context.facade.build_report_preview(
        request_text=request_text,
        requested_outputs=requested_outputs or [],
        identity=RequestIdentity(
            task_id=task_id,
            run_id=run_id,
            session_id=session_id,
            working_directory=working_directory,
        ),
    )
    console.print_json(json.dumps(report_preview.model_dump(mode="json")))


@app.command("diagnostic")
def diagnostic(
    working_directory: str | None = None,
    request_text: str = "Prepare diagnostic preview",
    task_id: str | None = None,
    run_id: str | None = None,
    session_id: str | None = None,
) -> None:
    """Generate diagnostic preview guidance while keeping non-bio intent off cluster execution paths."""

    context = create_application_context()
    diagnostic_preview = context.facade.build_diagnostic_preview(
        request_text=request_text,
        identity=RequestIdentity(
            task_id=task_id,
            run_id=run_id,
            session_id=session_id,
            working_directory=working_directory,
        ),
    )
    console.print_json(json.dumps(diagnostic_preview.model_dump(mode="json")))


@app.command("validate-inputs")
def validate_inputs(paths: list[str]) -> None:
    """Validate local input files before workflow construction."""

    context = create_application_context()
    report = context.facade.validate_inputs(paths)
    console.print_json(json.dumps(report.model_dump(mode="json")))


@app.command("review-action")
def review_action(
    action_name: str,
    task_id: str | None = None,
    run_id: str | None = None,
    session_id: str | None = None,
    working_directory: str | None = None,
    reason: str | None = None,
    target_path: list[str] | None = typer.Option(
        None,
        "--target-path",
        help="Target path in scope for the reviewed action; repeat for multiple paths.",
    ),
    external_network: bool = False,
    cloud_llm: bool = False,
    approval_approver: str | None = typer.Option(None, "--approval-approver", help="Manual approval approver."),
    approval_reason: str | None = typer.Option(None, "--approval-reason", help="Manual approval reason."),
    approval_time: str | None = typer.Option(None, "--approval-time", help="Manual approval timestamp (ISO-8601)."),
    outbound_field: list[str] | None = typer.Option(
        None,
        "--outbound-field",
        help="Outbound payload field in key=value form; repeat for multiple fields.",
    ),
) -> None:
    """Review a named action through the safety gate."""

    context = create_application_context()
    review = context.facade.review_action(
        action_name=action_name,
        identity=RequestIdentity(
            task_id=task_id,
            run_id=run_id,
            session_id=session_id,
            working_directory=working_directory,
        ),
        reason=reason,
        target_paths=target_path,
        external_network=external_network,
        cloud_llm=cloud_llm,
        approval=_build_approval_payload(
            approver=approval_approver,
            reason=approval_reason,
            approved_at=approval_time,
        ),
        outbound_payload=_build_outbound_payload(outbound_field),
    )
    console.print_json(json.dumps(review.model_dump(mode="json")))


@app.command("dry-run")
def dry_run(
    working_directory: str | None = None,
    request_text: str = "Prepare a dry-run submission",
    task_id: str | None = None,
    run_id: str | None = None,
    session_id: str | None = None,
    input_entry: list[str] | None = typer.Option(
        None,
        "--input-entry",
        help="Structured input entry in role=path form; repeat for multiple values.",
    ),
    input_species: str | None = typer.Option(None, "--input-species", help="Optional species label for InputBundle."),
    input_cohort: str | None = typer.Option(None, "--input-cohort", help="Optional cohort label for InputBundle."),
    approval_approver: str | None = typer.Option(None, "--approval-approver", help="Manual approval approver."),
    approval_reason: str | None = typer.Option(None, "--approval-reason", help="Manual approval reason."),
    approval_time: str | None = typer.Option(None, "--approval-time", help="Manual approval timestamp (ISO-8601)."),
    outbound_field: list[str] | None = typer.Option(
        None,
        "--outbound-field",
        help="Outbound payload field in key=value form; repeat for multiple fields.",
    ),
) -> None:
    """Generate a scheduler script preview without submitting a real job."""

    context = create_application_context()
    submission = context.facade.build_dry_run_submission(
        request_text=request_text,
        identity=RequestIdentity(
            task_id=task_id,
            run_id=run_id,
            session_id=session_id,
            working_directory=working_directory,
        ),
        input_bundle=_build_cli_input_bundle(
            input_entries=input_entry,
            species=input_species,
            cohort_name=input_cohort,
        ),
        approval=_build_approval_payload(
            approver=approval_approver,
            reason=approval_reason,
            approved_at=approval_time,
        ),
        outbound_payload=_build_outbound_payload(outbound_field),
    )
    console.print_json(json.dumps(submission.model_dump(mode="json")))


@app.command("submit-preview")
def submit_preview(
    working_directory: str | None = None,
    request_text: str = "Prepare a submit-preview",
    dry_run_completed: bool = False,
    task_id: str | None = None,
    run_id: str | None = None,
    session_id: str | None = None,
    execution_mode: ExecutionMode | None = typer.Option(
        None,
        "--execution-mode",
        help="Execution mode: local_preview, manual_sbase, ssh_shell_trusted, ssh_slurm_trusted, or hpc_local.",
    ),
    remote_profile_name: str | None = typer.Option(None, "--remote-profile-name"),
    watch: bool = typer.Option(False, "--watch/--no-watch"),
    auto_continue: bool | None = typer.Option(None, "--auto-continue/--no-auto-continue"),
    input_entry: list[str] | None = typer.Option(
        None,
        "--input-entry",
        help="Structured input entry in role=path form; repeat for multiple values.",
    ),
    input_species: str | None = typer.Option(None, "--input-species", help="Optional species label for InputBundle."),
    input_cohort: str | None = typer.Option(None, "--input-cohort", help="Optional cohort label for InputBundle."),
    approval_approver: str | None = typer.Option(None, "--approval-approver", help="Manual approval approver."),
    approval_reason: str | None = typer.Option(None, "--approval-reason", help="Manual approval reason."),
    approval_time: str | None = typer.Option(None, "--approval-time", help="Manual approval timestamp (ISO-8601)."),
    outbound_field: list[str] | None = typer.Option(
        None,
        "--outbound-field",
        help="Outbound payload field in key=value form; repeat for multiple fields.",
    ),
) -> None:
    """Generate submit-preview artifacts without issuing a real scheduler submission."""

    context = create_application_context()
    submission = context.facade.build_submit_preview(
        request_text=request_text,
        dry_run_completed=dry_run_completed,
        identity=RequestIdentity(
            task_id=task_id,
            run_id=run_id,
            session_id=session_id,
            working_directory=working_directory,
        ),
        input_bundle=_build_cli_input_bundle(
            input_entries=input_entry,
            species=input_species,
            cohort_name=input_cohort,
        ),
        approval=_build_approval_payload(
            approver=approval_approver,
            reason=approval_reason,
            approved_at=approval_time,
        ),
        outbound_payload=_build_outbound_payload(outbound_field),
        execution_mode=execution_mode,
        remote_profile_name=remote_profile_name,
        watch=watch,
        auto_continue=auto_continue,
    )
    console.print_json(json.dumps(submission.model_dump(mode="json")))


@app.command("submit")
def submit(
    working_directory: str | None = None,
    request_text: str = "Submit scheduler job",
    dry_run_completed: bool = False,
    task_id: str | None = None,
    run_id: str | None = None,
    session_id: str | None = None,
    execution_mode: ExecutionMode | None = typer.Option(
        None,
        "--execution-mode",
        help="Execution mode: local_preview, manual_sbase, ssh_shell_trusted, ssh_slurm_trusted, or hpc_local.",
    ),
    remote_profile_name: str | None = typer.Option(None, "--remote-profile-name"),
    watch: bool = typer.Option(False, "--watch/--no-watch"),
    auto_continue: bool | None = typer.Option(None, "--auto-continue/--no-auto-continue"),
    input_entry: list[str] | None = typer.Option(
        None,
        "--input-entry",
        help="Structured input entry in role=path form; repeat for multiple values.",
    ),
    input_species: str | None = typer.Option(None, "--input-species", help="Optional species label for InputBundle."),
    input_cohort: str | None = typer.Option(None, "--input-cohort", help="Optional cohort label for InputBundle."),
    approval_approver: str | None = typer.Option(None, "--approval-approver", help="Manual approval approver."),
    approval_reason: str | None = typer.Option(None, "--approval-reason", help="Manual approval reason."),
    approval_time: str | None = typer.Option(None, "--approval-time", help="Manual approval timestamp (ISO-8601)."),
    outbound_field: list[str] | None = typer.Option(
        None,
        "--outbound-field",
        help="Outbound payload field in key=value form; repeat for multiple fields.",
    ),
) -> None:
    """Submit a real scheduler job after safety checks pass."""

    context = create_application_context()
    try:
        submission = context.facade.submit(
            request_text=request_text,
            dry_run_completed=dry_run_completed,
            identity=RequestIdentity(
                task_id=task_id,
                run_id=run_id,
                session_id=session_id,
                working_directory=working_directory,
            ),
            input_bundle=_build_cli_input_bundle(
                input_entries=input_entry,
                species=input_species,
                cohort_name=input_cohort,
            ),
            approval=_build_approval_payload(
                approver=approval_approver,
                reason=approval_reason,
                approved_at=approval_time,
            ),
            outbound_payload=_build_outbound_payload(outbound_field),
            execution_mode=execution_mode,
            remote_profile_name=remote_profile_name,
            watch=watch,
            auto_continue=auto_continue,
        )
    except PermissionError as error:
        console.print_json(json.dumps({"error": str(error), "gate": "blocked_or_confirmation_required"}))
        raise typer.Exit(code=1) from error
    except SchedulerExecutionError as error:
        console.print_json(
            json.dumps(
                {
                    "error": str(error),
                    "command": error.command,
                    "stdout": error.stdout,
                    "stderr": error.stderr,
                    "attempts": error.attempts,
                }
            )
        )
        raise typer.Exit(code=1) from error
    console.print_json(json.dumps(submission.model_dump(mode="json")))


@app.command("poll-explain")
def poll_explain(job_id: str) -> None:
    """Explain a scheduler poll state from a job identifier."""

    context = create_application_context()
    poll = context.facade.explain_poll_state(job_id=job_id)
    console.print_json(json.dumps(poll.model_dump(mode="json")))


@app.command("remote-check")
def remote_check(
    execution_mode: ExecutionMode | None = typer.Option(
        None,
        "--execution-mode",
        help="Execution mode to check.",
    ),
    remote_profile_name: str | None = typer.Option(None, "--remote-profile-name"),
) -> None:
    """Check SSH shell or SSH/SLURM readiness for trusted remote execution."""

    context = create_application_context()
    payload = context.facade.remote_check(
        execution_mode=execution_mode,
        remote_profile_name=remote_profile_name,
    )
    console.print_json(json.dumps(payload.model_dump(mode="json")))


@app.command("remote-session-open")
def remote_session_open(
    remote_profile_name: str | None = typer.Option(None, "--remote-profile-name"),
    print_command: bool = typer.Option(False, "--print-command"),
) -> None:
    """Open an operator-authenticated SSH control session for password-based login."""

    context = create_application_context()
    profile = context.settings.remote_execution_profile(profile_name=remote_profile_name)
    manager = SshControlMasterManager(profile=profile)
    command = manager.open_command()
    if print_command:
        console.print_json(json.dumps(_remote_session_payload("open", profile, command)))
        return
    result = manager.open()
    payload = _remote_session_payload(
        "open",
        profile,
        command,
        returncode=result.returncode,
        stdout=getattr(result, "stdout", None),
        stderr=getattr(result, "stderr", None),
    )
    console.print_json(json.dumps(payload))
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)


@app.command("remote-session-check")
def remote_session_check(
    remote_profile_name: str | None = typer.Option(None, "--remote-profile-name"),
    print_command: bool = typer.Option(False, "--print-command"),
) -> None:
    """Check whether the SSH control session is alive."""

    context = create_application_context()
    profile = context.settings.remote_execution_profile(profile_name=remote_profile_name)
    manager = SshControlMasterManager(profile=profile)
    command = manager.check_command()
    if print_command:
        console.print_json(json.dumps(_remote_session_payload("check", profile, command)))
        return
    result = manager.check()
    payload = _remote_session_payload(
        "check",
        profile,
        command,
        returncode=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
    )
    console.print_json(json.dumps(payload))
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)


@app.command("remote-session-close")
def remote_session_close(
    remote_profile_name: str | None = typer.Option(None, "--remote-profile-name"),
    print_command: bool = typer.Option(False, "--print-command"),
) -> None:
    """Close the SSH control session."""

    context = create_application_context()
    profile = context.settings.remote_execution_profile(profile_name=remote_profile_name)
    manager = SshControlMasterManager(profile=profile)
    command = manager.close_command()
    if print_command:
        console.print_json(json.dumps(_remote_session_payload("close", profile, command)))
        return
    result = manager.close()
    payload = _remote_session_payload(
        "close",
        profile,
        command,
        returncode=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
    )
    console.print_json(json.dumps(payload))
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)


@app.command("remote-session-smoke")
def remote_session_smoke(
    remote_profile_name: str | None = typer.Option(None, "--remote-profile-name"),
    task_id: str | None = typer.Option(None, "--task-id"),
    run_id: str | None = typer.Option(None, "--run-id"),
    open_session: bool = typer.Option(
        True,
        "--open-session/--no-open-session",
        help="Open the SSH control session through OpenSSH if no live session is found.",
    ),
    print_command: bool = typer.Option(False, "--print-command"),
) -> None:
    """Run the ordinary-server smoke flow through an operator-authenticated SSH session."""

    context = create_application_context()
    profile = context.settings.remote_execution_profile(profile_name=remote_profile_name)
    manager = SshControlMasterManager(profile=profile)
    if profile.ssh_auth_mode != SshAuthMode.CONTROL_MASTER:
        payload = {
            "action": "remote-session-smoke",
            "auth_mode": profile.ssh_auth_mode.value,
            "session_ready": False,
            "submitted": False,
            "messages": ["remote_session_smoke_requires_control_master_auth_mode"],
        }
        console.print_json(json.dumps(payload))
        raise typer.Exit(code=1)

    try:
        open_command = manager.open_command()
        check_command = manager.check_command()
    except ValueError as error:
        payload = {
            "action": "remote-session-smoke",
            "profile_name": profile.profile_name,
            "auth_mode": profile.ssh_auth_mode.value,
            "session_ready": False,
            "submitted": False,
            "messages": ["remote_ssh_target_not_configured", str(error)],
        }
        console.print_json(json.dumps(payload))
        raise typer.Exit(code=1) from error

    next_commands = [
        "remote-check --execution-mode ssh_shell_trusted",
        _remote_smoke_command_text(task_id=task_id, run_id=run_id),
    ]
    if print_command:
        payload = {
            "action": "remote-session-smoke",
            "profile_name": profile.profile_name,
            "auth_mode": profile.ssh_auth_mode.value,
            "ssh_target": profile.ssh_target,
            "control_path": profile.ssh_control_path,
            "open_command": open_command,
            "open_command_text": shlex.join(open_command),
            "check_command": check_command,
            "check_command_text": shlex.join(check_command),
            "next_commands": next_commands,
        }
        console.print_json(json.dumps(payload))
        return

    messages: list[str] = []
    first_check = manager.check()
    session_ready = first_check.returncode == 0
    open_payload: dict[str, object] | None = None
    if not session_ready and open_session:
        open_result = manager.open()
        open_payload = {
            "returncode": open_result.returncode,
            "stdout": getattr(open_result, "stdout", None),
            "stderr": getattr(open_result, "stderr", None),
        }
        messages.append("ssh_control_session_open_attempted")
    final_check = manager.check()
    session_ready = final_check.returncode == 0
    if not session_ready:
        payload = {
            "action": "remote-session-smoke",
            "profile_name": profile.profile_name,
            "auth_mode": profile.ssh_auth_mode.value,
            "session_ready": False,
            "submitted": False,
            "open": open_payload,
            "check": {
                "returncode": final_check.returncode,
                "stdout": final_check.stdout,
                "stderr": final_check.stderr,
            },
            "messages": [*messages, "ssh_control_session_not_ready"],
        }
        console.print_json(json.dumps(payload))
        raise typer.Exit(code=1)

    remote_check_payload = context.facade.remote_check(
        execution_mode=ExecutionMode.SSH_SHELL_TRUSTED,
        remote_profile_name=remote_profile_name,
    )
    if not remote_check_payload.safe_for_submit:
        payload = {
            "action": "remote-session-smoke",
            "profile_name": profile.profile_name,
            "auth_mode": profile.ssh_auth_mode.value,
            "session_ready": True,
            "submitted": False,
            "remote_check": remote_check_payload.model_dump(mode="json"),
            "messages": [*messages, "remote_check_not_safe_for_submit"],
        }
        console.print_json(json.dumps(payload))
        raise typer.Exit(code=1)

    smoke_payload = context.facade.remote_smoke(
        execution_mode=ExecutionMode.SSH_SHELL_TRUSTED,
        remote_profile_name=remote_profile_name,
        task_id=task_id,
        run_id=run_id,
    )
    payload = {
        "action": "remote-session-smoke",
        "profile_name": profile.profile_name,
        "auth_mode": profile.ssh_auth_mode.value,
        "session_ready": True,
        "submitted": smoke_payload.submitted,
        "remote_check": remote_check_payload.model_dump(mode="json"),
        "smoke": smoke_payload.model_dump(mode="json"),
        "messages": messages,
    }
    console.print_json(json.dumps(payload))
    if not smoke_payload.submitted:
        raise typer.Exit(code=1)


@app.command("remote-session-doctor")
def remote_session_doctor(
    remote_profile_name: str | None = typer.Option(None, "--remote-profile-name"),
    skip_ssh_probe: bool = typer.Option(
        False,
        "--skip-ssh-probe",
        help="Skip the local `ssh -G` capability probe; no remote connection is attempted either way.",
    ),
) -> None:
    """Check local readiness for the operator-authenticated ordinary-server flow."""

    context = create_application_context()
    profile = context.settings.remote_execution_profile(profile_name=remote_profile_name)
    payload = _remote_session_doctor_payload(
        context=context,
        profile=profile,
        skip_ssh_probe=skip_ssh_probe,
    )
    console.print_json(json.dumps(payload))
    if not payload["ready_for_auth"]:
        raise typer.Exit(code=1)


@app.command("remote-password-set")
def remote_password_set(
    env_file: Path = typer.Option(Path(".env"), "--env-file", help="Local ignored dotenv file to update."),
    password: str = typer.Option(
        ...,
        prompt="Server SSH password",
        hide_input=True,
        help="Prompted value; prefer interactive input instead of passing this on the command line.",
    ),
) -> None:
    """Store the operator-approved SSH password only in the local ignored .env file."""

    if not password:
        console.print_json(
            json.dumps(
                {
                    "action": "remote-password-set",
                    "password_configured": False,
                    "messages": ["empty_password_refused"],
                }
            )
        )
        raise typer.Exit(code=1)
    _upsert_env_file(
        env_file,
        {
            "GENEAGENT_HPC_SSH_AUTH_MODE": SshAuthMode.PASSWORD_ENV.value,
            "GENEAGENT_HPC_SSH_PASSWORD": password,
        },
    )
    console.print_json(
        json.dumps(
            {
                "action": "remote-password-set",
                "env_file": str(env_file),
                "auth_mode": SshAuthMode.PASSWORD_ENV.value,
                "password_configured": True,
                "messages": ["password_saved_to_local_ignored_env"],
            }
        )
    )


@app.command("remote-smoke")
def remote_smoke(
    execution_mode: ExecutionMode | None = typer.Option(
        ExecutionMode.SSH_SHELL_TRUSTED,
        "--execution-mode",
        help="Execution mode for the harmless remote smoke task.",
    ),
    remote_profile_name: str | None = typer.Option(None, "--remote-profile-name"),
    task_id: str | None = typer.Option(None, "--task-id"),
    run_id: str | None = typer.Option(None, "--run-id"),
) -> None:
    """Submit one fixed harmless remote command after remote-check passes."""

    context = create_application_context()
    try:
        payload = context.facade.remote_smoke(
            execution_mode=execution_mode,
            remote_profile_name=remote_profile_name,
            task_id=task_id,
            run_id=run_id,
        )
    except SchedulerExecutionError as error:
        console.print_json(
            json.dumps(
                {
                    "submitted": False,
                    "error": str(error),
                    "command": error.command,
                    "stdout": error.stdout,
                    "stderr": error.stderr,
                    "attempts": error.attempts,
                }
            )
        )
        raise typer.Exit(code=1) from error
    console.print_json(json.dumps(payload.model_dump(mode="json")))
    if not payload.submitted:
        raise typer.Exit(code=1)


@app.command("watch-run")
def watch_run(
    task_id: str = typer.Option(..., "--task-id"),
    run_id: str = typer.Option(..., "--run-id"),
) -> None:
    """Watch a persisted trusted run state."""

    context = create_application_context()
    try:
        payload = context.facade.watch_run(task_id=task_id, run_id=run_id)
    except FileNotFoundError as error:
        console.print_json(json.dumps({"error": "run_state_not_found", "detail": str(error)}))
        raise typer.Exit(code=1) from error
    console.print_json(json.dumps(payload.model_dump(mode="json")))


@app.command("resume-run")
def resume_run(
    task_id: str = typer.Option(..., "--task-id"),
    run_id: str = typer.Option(..., "--run-id"),
    auto_continue: bool | None = typer.Option(None, "--auto-continue/--no-auto-continue"),
) -> None:
    """Resume a persisted trusted run state."""

    context = create_application_context()
    try:
        payload = context.facade.resume_run(task_id=task_id, run_id=run_id, auto_continue=auto_continue)
    except FileNotFoundError as error:
        console.print_json(json.dumps({"error": "run_state_not_found", "detail": str(error)}))
        raise typer.Exit(code=1) from error
    console.print_json(json.dumps(payload.model_dump(mode="json")))


@app.command("audit-export")
def audit_export(
    run_id: str,
    task_id: str | None = None,
    working_directory: str | None = None,
    output_path: str | None = None,
    include_files: bool = typer.Option(
        True,
        "--include-files/--manifest-only",
        help="Include real log/report/result attachments in zip, or export manifest-only package.",
    ),
) -> None:
    """Export one run-level audit package (input/plan/command/job/log/report/approval trail)."""

    context = create_application_context()
    try:
        bundle = context.facade.export_audit_bundle(
            run_id=run_id,
            task_id=task_id,
            identity=RequestIdentity(
                task_id=task_id,
                run_id=run_id,
                working_directory=working_directory,
            ),
            output_path=output_path,
            include_files=include_files,
        )
    except ValueError as error:
        console.print_json(json.dumps({"error": str(error), "gate": "audit_trace_not_found"}))
        raise typer.Exit(code=1) from error
    console.print_json(json.dumps(bundle.model_dump(mode="json")))


@app.command("doctor")
def doctor() -> None:
    """Display current runtime configuration and scheduler readiness."""

    context = create_application_context()
    scheduler_commands = _scheduler_command_set(context.settings.scheduler_type.value)
    command_paths = {command: shutil.which(command) for command in ["bash", *scheduler_commands]}
    missing_commands = [name for name, resolved in command_paths.items() if resolved is None]
    real_submit_ready = (
        context.settings.scheduler_real_execution_enabled and all(command_paths[name] for name in scheduler_commands)
    )
    recommendation = (
        "real submit/poll ready"
        if real_submit_ready
        else "use dry-run/submit-preview locally, or run real submit/poll on scheduler host"
    )
    console.print(
        {
            "app_name": context.settings.app_name,
            "scheduler_type": context.settings.scheduler_type.value,
            "dry_run_default": context.settings.dry_run_default,
            "scheduler_real_execution_enabled": context.settings.scheduler_real_execution_enabled,
            "work_root": context.settings.work_root,
            "command_paths": command_paths,
            "missing_commands": missing_commands,
            "recommendation": recommendation,
        }
    )


@app.command("observability")
def observability(
    working_directory: str | None = None,
    limit: int = 200,
) -> None:
    """Show observability metrics (task, scheduler, and failure taxonomy)."""

    context = create_application_context()
    payload = context.facade.observability_metrics(
        working_directory=working_directory,
        limit=max(1, limit),
    )
    console.print_json(json.dumps(payload))


@app.command("production-gate")
def production_gate(
    working_directory: str | None = None,
    execute_tests: bool = False,
    timeout_seconds: int = 300,
) -> None:
    """Run production gate pipeline checks for contracts/scheduler/knowledge/audit."""

    context = create_application_context()
    payload = context.facade.production_gate_pipeline(
        working_directory=working_directory,
        execute_tests=execute_tests,
        timeout_seconds=timeout_seconds,
    )
    console.print_json(json.dumps(payload))


@app.command("release-plan")
def release_plan(
    version_tag: str = "v2.0.0",
    change_summary: str = "",
    stage_id: list[str] | None = typer.Option(
        None,
        "--stage-id",
        help="Stage ids mapped to this release; repeat for multiple values.",
    ),
) -> None:
    """Generate standardized release package plan with rollback template."""

    context = create_application_context()
    payload = context.facade.release_plan(
        version_tag=version_tag,
        change_summary=change_summary,
        stage_ids=stage_id or [],
    )
    console.print_json(json.dumps(payload))


@app.command("final-review")
def final_review(working_directory: str | None = None) -> None:
    """Run V2.0 final acceptance review (architecture/governance/operability)."""

    context = create_application_context()
    payload = context.facade.final_acceptance_review(
        working_directory=working_directory,
    )
    console.print_json(json.dumps(payload))


def _scheduler_command_set(scheduler: str) -> list[str]:
    if scheduler.lower() == "shell":
        return ["bash", "nohup", "ps", "kill"]
    if scheduler.lower() == "pbs":
        return ["qsub", "qstat"]
    return ["sbatch", "squeue", "sacct"]


def _remote_session_payload(
    action: str,
    profile,
    command: list[str],
    *,
    returncode: int | None = None,
    stdout: str | None = None,
    stderr: str | None = None,
) -> dict[str, object]:
    return {
        "action": action,
        "profile_name": profile.profile_name,
        "auth_mode": profile.ssh_auth_mode.value,
        "ssh_target": profile.ssh_target,
        "control_path": profile.ssh_control_path,
        "command": command,
        "command_text": shlex.join(command),
        "returncode": returncode,
        "stdout": stdout,
        "stderr": stderr,
    }


def _remote_smoke_command_text(*, task_id: str | None, run_id: str | None) -> str:
    command = ["remote-smoke"]
    if task_id:
        command.extend(["--task-id", task_id])
    if run_id:
        command.extend(["--run-id", run_id])
    return shlex.join(command)


def _remote_session_doctor_payload(*, context, profile, skip_ssh_probe: bool) -> dict[str, object]:
    messages: list[str] = []
    checks: dict[str, bool | None] = {}

    checks["execution_mode_ssh_shell_trusted"] = context.settings.execution_mode == ExecutionMode.SSH_SHELL_TRUSTED
    checks["real_execution_enabled"] = context.settings.scheduler_real_execution_enabled
    checks["ssh_auth_mode_control_master"] = profile.ssh_auth_mode == SshAuthMode.CONTROL_MASTER
    checks["ssh_auth_mode_password_env"] = profile.ssh_auth_mode == SshAuthMode.PASSWORD_ENV
    checks["ssh_password_configured"] = profile.ssh_password_configured
    checks["ssh_target_configured"] = bool(profile.ssh_target)
    checks["remote_work_root_configured"] = bool(profile.work_root)
    checks["control_path_configured"] = bool(profile.ssh_control_path)

    ssh_binary_path = shutil.which(profile.ssh_binary)
    if ssh_binary_path is None:
        candidate = Path(profile.ssh_binary).expanduser()
        if candidate.exists():
            ssh_binary_path = str(candidate)
    checks["ssh_binary_available"] = ssh_binary_path is not None

    control_dir = None
    if profile.ssh_control_path:
        control_dir = str(Path(profile.ssh_control_path).expanduser().parent)
    control_dir_check = _control_dir_writable(profile.ssh_control_path)
    checks["control_dir_writable"] = bool(control_dir_check["ok"])

    ssh_probe: dict[str, object] = {"skipped": skip_ssh_probe}
    checks["ssh_config_probe_ok"] = None
    if not skip_ssh_probe:
        ssh_probe = _probe_ssh_config(profile=profile)
        checks["ssh_config_probe_ok"] = bool(ssh_probe.get("ok"))

    if not checks["execution_mode_ssh_shell_trusted"]:
        messages.append("execution_mode_not_ssh_shell_trusted")
    if not checks["real_execution_enabled"]:
        messages.append("scheduler_real_execution_disabled")
    if not (checks["ssh_auth_mode_control_master"] or checks["ssh_auth_mode_password_env"]):
        messages.append("ssh_auth_mode_not_control_master_or_password_env")
    if checks["ssh_auth_mode_password_env"] and not checks["ssh_password_configured"]:
        messages.append("ssh_password_not_configured")
    if not checks["ssh_target_configured"]:
        messages.append("remote_ssh_target_not_configured")
    if not checks["remote_work_root_configured"]:
        messages.append("remote_work_root_not_configured")
    if checks["ssh_auth_mode_control_master"] and not checks["control_path_configured"]:
        messages.append("ssh_control_path_not_configured")
    if not checks["ssh_binary_available"]:
        messages.append("ssh_binary_not_found")
    if checks["ssh_auth_mode_control_master"] and not checks["control_dir_writable"]:
        messages.append("ssh_control_dir_not_writable")
    if checks["ssh_config_probe_ok"] is False:
        messages.append("ssh_config_probe_failed")

    ready_for_control_session = all(
        checks[name] is True
        for name in [
            "ssh_auth_mode_control_master",
            "ssh_target_configured",
            "remote_work_root_configured",
            "control_path_configured",
            "ssh_binary_available",
            "control_dir_writable",
        ]
    )
    ready_for_password_auth = all(
        checks[name] is True
        for name in [
            "ssh_auth_mode_password_env",
            "ssh_password_configured",
            "ssh_target_configured",
            "remote_work_root_configured",
        ]
    )
    ready_for_auth = ready_for_control_session or ready_for_password_auth
    ready_for_real_smoke = bool(
        ready_for_auth
        and checks["execution_mode_ssh_shell_trusted"]
        and checks["real_execution_enabled"]
    )
    recommended_command = "fix reported messages, then rerun remote-session-doctor"
    if ready_for_real_smoke and profile.ssh_auth_mode == SshAuthMode.PASSWORD_ENV:
        recommended_command = "remote-smoke --task-id task-smoke-001 --run-id run-smoke-001"
    elif ready_for_real_smoke:
        recommended_command = "remote-session-smoke --open-session --task-id task-smoke-001 --run-id run-smoke-001"
    return {
        "action": "remote-session-doctor",
        "profile_name": profile.profile_name,
        "auth_mode": profile.ssh_auth_mode.value,
        "ssh_target": profile.ssh_target,
        "remote_work_root": profile.work_root,
        "control_path": profile.ssh_control_path,
        "control_dir": control_dir,
        "ssh_binary": profile.ssh_binary,
        "ssh_binary_path": ssh_binary_path,
        "checks": checks,
        "control_dir_check": control_dir_check,
        "ssh_probe": ssh_probe,
        "ready_for_control_session": ready_for_control_session,
        "ready_for_password_auth": ready_for_password_auth,
        "ready_for_auth": ready_for_auth,
        "ready_for_real_smoke": ready_for_real_smoke,
        "remediation": _remote_session_doctor_remediation(messages),
        "recommended_next_command": recommended_command,
        "messages": messages,
    }


def _remote_session_doctor_remediation(messages: list[str]) -> list[str]:
    remediation: list[str] = []
    if "ssh_control_dir_not_writable" in messages:
        remediation.append(
            "Set GENEAGENT_HPC_SSH_CONTROL_PATH to a user-writable local path, for example %TEMP%\\geneagent_ssh\\default.sock on Windows."
        )
        remediation.append("Alternatively set GENEAGENT_LOCAL_STATE_ROOT to a user-writable directory and rerun remote-session-doctor.")
    if "ssh_auth_mode_not_control_master_or_password_env" in messages:
        remediation.append(
            "Set GENEAGENT_HPC_SSH_AUTH_MODE=control_master for operator-entered OpenSSH login, or password_env for local ignored .env password login."
        )
    if "ssh_password_not_configured" in messages:
        remediation.append("Set GENEAGENT_HPC_SSH_PASSWORD only in the local ignored .env file; never commit it.")
    if "execution_mode_not_ssh_shell_trusted" in messages:
        remediation.append("Set GENEAGENT_EXECUTION_MODE=ssh_shell_trusted for ordinary Linux server execution.")
    if "scheduler_real_execution_disabled" in messages:
        remediation.append("Set GENEAGENT_SCHEDULER_REAL_EXECUTION_ENABLED=true only when you are ready for the guarded smoke submit.")
    if "remote_ssh_target_not_configured" in messages:
        remediation.append("Set GENEAGENT_HPC_HOST and GENEAGENT_HPC_USER in the local ignored .env file.")
    if "ssh_binary_not_found" in messages:
        remediation.append("Install OpenSSH Client or set GENEAGENT_HPC_SSH_BINARY to the ssh executable path.")
    return remediation


def _upsert_env_file(env_file: Path, updates: dict[str, str]) -> None:
    lines: list[str] = []
    if env_file.exists():
        lines = env_file.read_text(encoding="utf-8").splitlines()
    seen: set[str] = set()
    updated_lines: list[str] = []
    for line in lines:
        stripped = line.strip()
        matched_key = None
        if stripped and not stripped.startswith("#") and "=" in line:
            matched_key = line.split("=", 1)[0].strip()
        if matched_key in updates:
            updated_lines.append(f"{matched_key}={updates[matched_key]}")
            seen.add(matched_key)
            continue
        updated_lines.append(line)
    for key, value in updates.items():
        if key not in seen:
            updated_lines.append(f"{key}={value}")
    env_file.parent.mkdir(parents=True, exist_ok=True)
    env_file.write_text("\n".join(updated_lines) + "\n", encoding="utf-8")


def _control_dir_writable(control_path: str | None) -> dict[str, object]:
    if not control_path:
        return {"ok": False, "error": "missing_control_path"}
    directory = Path(control_path).expanduser().parent
    probe = directory / ".geneagent_write_probe"
    try:
        directory.mkdir(parents=True, exist_ok=True)
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
    except OSError as error:
        return {
            "ok": False,
            "path": str(directory),
            "error": f"{error.__class__.__name__}: {error}",
        }
    return {"ok": True, "path": str(directory)}


def _probe_ssh_config(*, profile) -> dict[str, object]:
    if not profile.ssh_target:
        return {"skipped": False, "ok": False, "reason": "missing_ssh_target"}
    command = [profile.ssh_binary, "-G", profile.ssh_target]
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=max(1, min(profile.connect_timeout_seconds, 10)),
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return {
            "skipped": False,
            "ok": False,
            "command_text": shlex.join(command),
            "error": str(error),
        }
    output = result.stdout.lower()
    return {
        "skipped": False,
        "ok": result.returncode == 0,
        "command_text": shlex.join(command),
        "returncode": result.returncode,
        "supports_control_master": "controlmaster" in output,
        "supports_control_path": "controlpath" in output,
        "supports_control_persist": "controlpersist" in output,
        "stderr": result.stderr,
    }


def _build_cli_input_bundle(
    *,
    input_entries: list[str] | None,
    species: str | None,
    cohort_name: str | None,
) -> InputBundle | None:
    raw_entries = input_entries or []
    if not raw_entries and species is None and cohort_name is None:
        return None
    entries: list[InputBundleEntry] = []
    for index, item in enumerate(raw_entries):
        role, separator, path = item.partition("=")
        if separator and role.strip() and path.strip():
            entries.append(InputBundleEntry(role=role.strip(), path=path.strip()))
            continue
        entries.append(InputBundleEntry(role=f"input_{index + 1}", path=item.strip()))
    return InputBundle(species=species, cohort_name=cohort_name, entries=entries)


def _build_approval_payload(
    *,
    approver: str | None,
    reason: str | None,
    approved_at: str | None,
) -> dict[str, object] | None:
    if not any([approver, reason, approved_at]):
        return None
    return {
        "approved": True,
        "approver": approver,
        "reason": reason,
        "approved_at": approved_at,
    }


def _build_outbound_payload(entries: list[str] | None) -> dict[str, object] | None:
    raw_entries = entries or []
    if not raw_entries:
        return None
    payload: dict[str, object] = {}
    for item in raw_entries:
        key, separator, value = item.partition("=")
        if not separator:
            continue
        key_norm = key.strip()
        value_norm = value.strip()
        if not key_norm:
            continue
        payload[key_norm] = value_norm
    return payload or None


def main() -> None:
    """Run the Typer application."""

    app()


if __name__ == "__main__":
    main()
