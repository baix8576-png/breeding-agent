"""Schema models for tool manifest catalog loading and validation."""

from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from contracts.common import TaskDomain

SUPPORTED_SCHEMA_MAJOR = "1"
SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")

STAGE_SCOPE_ALLOWLIST = {
    "stage_01_intake",
    "stage_02_intent_and_scope",
    "stage_03_input_validation",
    "stage_04_local_first_rag",
    "stage_05_blueprint_selection",
    "stage_06_resource_and_safety_gate",
    "stage_07_execution",
    "stage_08_artifact_and_report",
    "stage_09_audit_and_memory",
    "lite_01_intake",
    "lite_02_local_retrieval",
    "lite_03_answer_blueprint",
    "lite_04_optional_safety_review",
}

DOMAIN_SCOPE_ALLOWLIST = {
    "shared",
    TaskDomain.BIOINFORMATICS.value,
    TaskDomain.KNOWLEDGE.value,
    TaskDomain.SYSTEM.value,
}


def _validate_semver(value: str, *, field_name: str, lock_major: bool) -> str:
    normalized = value.strip()
    if not SEMVER_PATTERN.fullmatch(normalized):
        raise ValueError(f"{field_name} must use semantic version format `MAJOR.MINOR.PATCH`")
    if lock_major and normalized.split(".")[0] != SUPPORTED_SCHEMA_MAJOR:
        raise ValueError(f"{field_name} major version must be `{SUPPORTED_SCHEMA_MAJOR}`")
    return normalized


def _normalize_string_list(values: list[str], *, field_name: str) -> list[str]:
    normalized: list[str] = []
    for raw in values:
        item = str(raw).strip()
        if not item:
            raise ValueError(f"{field_name} cannot contain empty values")
        normalized.append(item)
    if len(normalized) != len(set(normalized)):
        raise ValueError(f"{field_name} cannot contain duplicate values")
    return normalized


class ToolManifest(BaseModel):
    """Validated runtime manifest entry."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str
    manifest_version: str
    name: str
    description: str = ""
    category: str = "workflow"
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    preconditions: list[str] = Field(default_factory=list)
    resource_requirements: list[str] = Field(default_factory=list)
    error_codes: list[str] = Field(default_factory=list)
    supports_dry_run: bool = True
    stage_scope: list[str]
    domain_scope: list[str]

    @field_validator("schema_version")
    @classmethod
    def _validate_schema_version(cls, value: str) -> str:
        return _validate_semver(value, field_name="schema_version", lock_major=True)

    @field_validator("manifest_version")
    @classmethod
    def _validate_manifest_version(cls, value: str) -> str:
        return _validate_semver(value, field_name="manifest_version", lock_major=False)

    @field_validator("name")
    @classmethod
    def _validate_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("name cannot be blank")
        if not re.fullmatch(r"^[a-z][a-z0-9_]*$", normalized):
            raise ValueError("name must use snake_case")
        return normalized

    @field_validator("description", "category")
    @classmethod
    def _normalize_text_fields(cls, value: str) -> str:
        return value.strip()

    @field_validator(
        "inputs",
        "outputs",
        "preconditions",
        "resource_requirements",
        "error_codes",
    )
    @classmethod
    def _validate_generic_lists(cls, value: list[str], info) -> list[str]:
        return _normalize_string_list(value, field_name=info.field_name)

    @field_validator("stage_scope")
    @classmethod
    def _validate_stage_scope(cls, value: list[str]) -> list[str]:
        normalized = _normalize_string_list(value, field_name="stage_scope")
        unknown = sorted(set(normalized) - STAGE_SCOPE_ALLOWLIST)
        if unknown:
            raise ValueError(f"stage_scope includes unsupported stage ids: {', '.join(unknown)}")
        return normalized

    @field_validator("domain_scope")
    @classmethod
    def _validate_domain_scope(cls, value: list[str]) -> list[str]:
        normalized = _normalize_string_list(value, field_name="domain_scope")
        unknown = sorted(set(normalized) - DOMAIN_SCOPE_ALLOWLIST)
        if unknown:
            raise ValueError(f"domain_scope includes unsupported domains: {', '.join(unknown)}")
        return normalized

    @model_validator(mode="after")
    def _validate_required_lists(self) -> "ToolManifest":
        if not self.stage_scope:
            raise ValueError("stage_scope must include at least one stage id")
        if not self.domain_scope:
            raise ValueError("domain_scope must include at least one domain id")
        return self


class ToolManifestCatalog(BaseModel):
    """File-level catalog document for one or more tool manifests."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str
    manifests: list[ToolManifest] = Field(default_factory=list)

    @field_validator("schema_version")
    @classmethod
    def _validate_catalog_schema_version(cls, value: str) -> str:
        return _validate_semver(value, field_name="schema_version", lock_major=True)

    @model_validator(mode="after")
    def _validate_names_unique(self) -> "ToolManifestCatalog":
        if not self.manifests:
            raise ValueError("manifests cannot be empty")
        names = [item.name for item in self.manifests]
        duplicates = sorted({name for name in names if names.count(name) > 1})
        if duplicates:
            raise ValueError(f"manifests contain duplicated names: {', '.join(duplicates)}")
        return self
