"""Knowledge metadata contracts shared by references, retrieval, and orchestration."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class BlueprintScope(str, Enum):
    """Supported blueprint scopes for knowledge assets."""

    QC = "qc"
    PCA = "pca"
    GRM = "grm"
    GENOMIC_PREDICTION = "genomic_prediction"
    SHARED = "shared"


class EvidenceLevel(str, Enum):
    """Evidence confidence level for a knowledge asset."""

    SOP = "sop"
    BENCHMARK = "benchmark"
    PEER_REVIEWED = "peer_reviewed"
    INCIDENT_VERIFIED = "incident_verified"
    EXPERT_OPINION = "expert_opinion"


class KnowledgeSource(str, Enum):
    """Primary source channel for a knowledge asset."""

    PAPER = "paper"
    SOP = "sop"
    PARAMETER_PLAYBOOK = "parameter_playbook"
    FAILURE_CASE = "failure_case"
    ONTOLOGY = "ontology"
    INTERNAL_NOTE = "internal_note"


class KnowledgeItemV2(BaseModel):
    """Typed metadata contract for `knowledge_item.v2`."""

    doc_id: str = Field(min_length=3)
    version: str = Field(min_length=2, description="Metadata version token (for example v2).")
    species: str = Field(min_length=2)
    blueprint_scope: BlueprintScope
    evidence_level: EvidenceLevel
    source: KnowledgeSource
    updated_at: datetime
    owner: str = Field(min_length=2)

    @field_validator("doc_id", "version", "species", "owner")
    @classmethod
    def _strip_and_validate(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("must not be empty")
        return normalized


class KnowledgeChunk(BaseModel):
    """Traceable searchable unit derived from a validated knowledge asset."""

    chunk_id: str = Field(min_length=3)
    doc_id: str = Field(min_length=3)
    source_path: str = Field(min_length=3)
    blueprint_scope: BlueprintScope
    species: str = Field(min_length=2)
    evidence_level: EvidenceLevel
    source: KnowledgeSource
    section: str = Field(min_length=1)
    page_or_anchor: str = Field(min_length=1)
    text: str = Field(min_length=1)
    updated_at: datetime
    owner: str = Field(min_length=2)
    keywords: list[str] = Field(default_factory=list)
    embedding_model: str | None = None

    @field_validator(
        "chunk_id",
        "doc_id",
        "source_path",
        "species",
        "section",
        "page_or_anchor",
        "text",
        "owner",
    )
    @classmethod
    def _strip_required_strings(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("must not be empty")
        return normalized


class KnowledgeIndexManifest(BaseModel):
    """Manifest describing a local-first knowledge index build."""

    schema_version: str = "knowledge_index_manifest.v1"
    index_id: str = Field(min_length=3)
    created_at: datetime
    metadata_schema: str = "knowledge_item.v2"
    source_root: str = Field(min_length=1)
    doc_count: int = Field(ge=0)
    chunk_count: int = Field(ge=0)
    bm25_index_path: str | None = None
    embedding_index_path: str | None = None
    embedding_model: str | None = None
    sources: list[str] = Field(default_factory=list)

    @field_validator("schema_version", "index_id", "metadata_schema", "source_root")
    @classmethod
    def _strip_manifest_strings(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("must not be empty")
        return normalized
