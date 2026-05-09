from __future__ import annotations

from contracts.api import DraftPlanRequest, DryRunRequest, RequestIdentity, SubmitRequest
from contracts.validation import InputBundle, InputBundleEntry
from runtime.compat import envelope_from_draft_plan, envelope_from_dry_run, envelope_from_submit


def test_envelope_mapper_for_draft_plan_preserves_input_bundle() -> None:
    payload = DraftPlanRequest(
        text="Plan PCA for sheep cohort",
        identity=RequestIdentity(task_id="task-env-001", run_id="run-env-001", working_directory="/cluster/work"),
        input_bundle=InputBundle(entries=[InputBundleEntry(role="vcf", path="/data/sheep.vcf.gz")]),
    )
    envelope = envelope_from_draft_plan(payload)

    assert envelope.schema_version == "request_envelope.v2"
    assert envelope.intent.value == "plan"
    assert envelope.request_text == "Plan PCA for sheep cohort"
    assert envelope.identity.task_id == "task-env-001"
    assert envelope.input_bundle is not None
    assert envelope.input_bundle.entries[0].role == "vcf"


def test_envelope_mapper_for_dry_run_preserves_command() -> None:
    payload = DryRunRequest(
        request_text="Dry-run PCA",
        command=["bash", "scripts/pca_pipeline/run_pca_pipeline.sh"],
    )
    envelope = envelope_from_dry_run(payload)

    assert envelope.intent.value == "dry_run"
    assert envelope.command == ["bash", "scripts/pca_pipeline/run_pca_pipeline.sh"]


def test_envelope_mapper_for_submit_preserves_gate_flags() -> None:
    payload = SubmitRequest(
        request_text="Submit genomic prediction",
        dry_run_completed=True,
        identity=RequestIdentity(task_id="task-env-003", run_id="run-env-003"),
    )
    envelope = envelope_from_submit(payload)

    assert envelope.intent.value == "submit"
    assert envelope.dry_run_completed is True
    assert envelope.identity.task_id == "task-env-003"
