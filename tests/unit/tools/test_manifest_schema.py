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
