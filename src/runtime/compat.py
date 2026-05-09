"""Compatibility mappers between legacy request objects and v2 envelopes."""

from __future__ import annotations

from contracts.api import (
    DiagnosticPreviewRequest,
    DraftPlanRequest,
    DryRunRequest,
    ReportPreviewRequest,
    SubmitPreviewRequest,
    SubmitRequest,
)
from contracts.envelope import ExecutionIntent, RuntimeRequestEnvelopeV2


def envelope_from_draft_plan(payload: DraftPlanRequest) -> RuntimeRequestEnvelopeV2:
    return RuntimeRequestEnvelopeV2(
        intent=ExecutionIntent.PLAN,
        request_text=payload.text,
        identity=payload.identity,
        input_bundle=payload.input_bundle,
        requested_outputs=list(payload.requested_outputs),
    )


def envelope_from_dry_run(payload: DryRunRequest) -> RuntimeRequestEnvelopeV2:
    return RuntimeRequestEnvelopeV2(
        intent=ExecutionIntent.DRY_RUN,
        request_text=payload.request_text,
        identity=payload.identity,
        input_bundle=payload.input_bundle,
        command=payload.command,
    )


def envelope_from_submit_preview(payload: SubmitPreviewRequest) -> RuntimeRequestEnvelopeV2:
    return RuntimeRequestEnvelopeV2(
        intent=ExecutionIntent.SUBMIT_PREVIEW,
        request_text=payload.request_text,
        identity=payload.identity,
        input_bundle=payload.input_bundle,
        command=payload.command,
        dry_run_completed=payload.dry_run_completed,
    )


def envelope_from_submit(payload: SubmitRequest) -> RuntimeRequestEnvelopeV2:
    return RuntimeRequestEnvelopeV2(
        intent=ExecutionIntent.SUBMIT,
        request_text=payload.request_text,
        identity=payload.identity,
        input_bundle=payload.input_bundle,
        command=payload.command,
        dry_run_completed=payload.dry_run_completed,
    )


def envelope_from_report(payload: ReportPreviewRequest) -> RuntimeRequestEnvelopeV2:
    return RuntimeRequestEnvelopeV2(
        intent=ExecutionIntent.REPORT,
        request_text=payload.request_text,
        identity=payload.identity,
        requested_outputs=list(payload.requested_outputs),
    )


def envelope_from_diagnostic(payload: DiagnosticPreviewRequest) -> RuntimeRequestEnvelopeV2:
    return RuntimeRequestEnvelopeV2(
        intent=ExecutionIntent.DIAGNOSTIC,
        request_text=payload.request_text,
        identity=payload.identity,
    )

