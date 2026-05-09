from __future__ import annotations

import pytest
from pydantic import ValidationError

from tools.manifest_schema import ToolManifest, ToolManifestCatalog


def _valid_manifest_payload() -> dict[str, object]:
    return {
        "schema_version": "1.0.0",
        "manifest_version": "1.0.0",
        "name": "unit_test_tool",
        "description": "Unit test manifest",
        "category": "workflow",
        "inputs": ["request"],
        "outputs": ["result"],
        "preconditions": ["request available"],
        "resource_requirements": ["cpu:1"],
        "error_codes": ["GENERIC_FAILURE"],
        "supports_dry_run": True,
        "stage_scope": ["stage_01_intake"],
        "domain_scope": ["shared", "knowledge"],
    }


def test_schema_accepts_minimal_valid_manifest() -> None:
    manifest = ToolManifest.model_validate(_valid_manifest_payload())

    assert manifest.name == "unit_test_tool"
    assert manifest.schema_version == "1.0.0"
    assert manifest.manifest_version == "1.0.0"
    assert manifest.stage_scope == ["stage_01_intake"]
    assert manifest.domain_scope == ["shared", "knowledge"]


def test_schema_rejects_extra_fields() -> None:
    payload = _valid_manifest_payload()
    payload["unexpected"] = "boom"

    with pytest.raises(ValidationError):
        ToolManifest.model_validate(payload)


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("name", " "),
        ("schema_version", " "),
        ("stage_scope", []),
        ("domain_scope", []),
    ],
)
def test_schema_rejects_missing_or_blank_required_fields(field_name: str, value: object) -> None:
    payload = _valid_manifest_payload()
    payload[field_name] = value

    with pytest.raises(ValidationError):
        ToolManifest.model_validate(payload)


def test_schema_rejects_unsupported_schema_major_version() -> None:
    payload = _valid_manifest_payload()
    payload["schema_version"] = "2.0.0"

    with pytest.raises(ValidationError):
        ToolManifest.model_validate(payload)


def test_schema_rejects_unknown_domain_or_stage() -> None:
    bad_domain = _valid_manifest_payload()
    bad_domain["domain_scope"] = ["unknown_domain"]
    with pytest.raises(ValidationError):
        ToolManifest.model_validate(bad_domain)

    bad_stage = _valid_manifest_payload()
    bad_stage["stage_scope"] = ["stage_99_unknown"]
    with pytest.raises(ValidationError):
        ToolManifest.model_validate(bad_stage)


def test_catalog_rejects_duplicated_manifest_names() -> None:
    payload = {
        "schema_version": "1.0.0",
        "manifests": [_valid_manifest_payload(), _valid_manifest_payload()],
    }

    with pytest.raises(ValidationError):
        ToolManifestCatalog.model_validate(payload)


def test_schema_accepts_atomic_algorithm_manifest() -> None:
    payload = _valid_manifest_payload()
    payload.update(
        {
            "name": "plink2_pca",
            "category": "atomic_algorithm",
            "algorithm_family": "plink2",
            "atomic_resource_profile": {
                "cpus": 12,
                "memory_gb": 48,
                "walltime": "06:00:00",
                "retry_suggestion": "increase memory by +25% and retry once",
            },
            "error_codes": ["INPUT_MISSING", "OUT_OF_MEMORY", "NONZERO_EXIT"],
            "failure_code_map": [
                {
                    "code": "INPUT_MISSING",
                    "message": "input missing",
                    "retryable": False,
                    "retry_suggestion": "fix path",
                },
                {
                    "code": "OUT_OF_MEMORY",
                    "message": "oom",
                    "retryable": True,
                    "retry_suggestion": "increase memory",
                },
            ],
            "stage_scope": ["stage_07_execution"],
            "domain_scope": ["bioinformatics"],
        }
    )

    manifest = ToolManifest.model_validate(payload)

    assert manifest.category == "atomic_algorithm"
    assert manifest.atomic_resource_profile is not None
    assert manifest.atomic_resource_profile.cpus == 12
    assert manifest.failure_code_map[1].code == "OUT_OF_MEMORY"


def test_schema_rejects_atomic_failure_codes_not_declared() -> None:
    payload = _valid_manifest_payload()
    payload.update(
        {
            "name": "gcta_reml",
            "category": "atomic_algorithm",
            "algorithm_family": "gcta",
            "atomic_resource_profile": {
                "cpus": 16,
                "memory_gb": 96,
                "walltime": "12:00:00",
                "retry_suggestion": "drop collinear covariates",
            },
            "error_codes": ["OUT_OF_MEMORY"],
            "failure_code_map": [
                {
                    "code": "MATRIX_SINGULAR",
                    "message": "singular matrix",
                    "retryable": True,
                    "retry_suggestion": "adjust model",
                }
            ],
            "stage_scope": ["stage_07_execution"],
            "domain_scope": ["bioinformatics"],
        }
    )

    with pytest.raises(ValidationError):
        ToolManifest.model_validate(payload)
