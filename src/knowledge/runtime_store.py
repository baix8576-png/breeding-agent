"""Runtime knowledge store for local-first RAG artifacts."""

from __future__ import annotations

import json
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field

from contracts.knowledge import BlueprintScope, KnowledgeChunk
from knowledge.indexing import HybridKnowledgeIndex, KnowledgeSearchHit, ReferenceKnowledgeIndexer


class RuntimeKnowledgeManifest(BaseModel):
    """Manifest for generated local runtime knowledge artifacts."""

    schema_version: str = "knowledge_runtime_manifest.v1"
    index_id: str = Field(min_length=3)
    created_at: datetime
    metadata_schema: str = "knowledge_item.v2"
    references_root: str = Field(min_length=1)
    runtime_root: str = Field(min_length=1)
    chunks_path: str = Field(min_length=1)
    manifest_path: str = Field(min_length=1)
    doc_count: int = Field(ge=0)
    chunk_count: int = Field(ge=0)
    bm25_index_path: str | None = None
    embedding_index_path: str | None = None
    embedding_model: str | None = None
    sources: list[str] = Field(default_factory=list)


class RuntimeKnowledgeBuildResult(BaseModel):
    """Result returned after materializing the runtime knowledge store."""

    action: str = "knowledge_build_index"
    manifest: RuntimeKnowledgeManifest
    chunks_path: str = Field(min_length=1)
    manifest_path: str = Field(min_length=1)
    errors: list[str] = Field(default_factory=list)


class RuntimeKnowledgeDocInspection(BaseModel):
    """Traceable view of one document stored in the runtime chunk cache."""

    action: str = "knowledge_inspect_doc"
    doc_id: str = Field(min_length=3)
    runtime_root: str = Field(min_length=1)
    chunk_count: int = Field(ge=0)
    chunks: list[KnowledgeChunk] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)


class RuntimeKnowledgeSearchResult(BaseModel):
    """Search result payload for the runtime knowledge store."""

    action: str = "knowledge_search"
    query: str = Field(min_length=1)
    runtime_root: str = Field(min_length=1)
    chunk_count: int = Field(ge=0)
    hits: list[KnowledgeSearchHit] = Field(default_factory=list)


class KnowledgeRuntimeStore:
    """Persist and query generated local knowledge chunks under `.geneagent/knowledge`."""

    def __init__(
        self,
        runtime_root: Path | str | None = None,
        *,
        project_root: Path | str | None = None,
    ) -> None:
        self.project_root = Path(project_root or Path(__file__).resolve().parents[2]).resolve()
        self.runtime_root = Path(runtime_root or self.project_root / ".geneagent" / "knowledge").resolve()
        self._reject_references_runtime_root()

    @property
    def chunks_dir(self) -> Path:
        return self.runtime_root / "chunks"

    @property
    def indexes_dir(self) -> Path:
        return self.runtime_root / "indexes"

    @property
    def references_chunks_path(self) -> Path:
        return self.chunks_dir / "references.jsonl"

    @property
    def manifest_path(self) -> Path:
        return self.indexes_dir / "manifest.json"

    def build_from_references(
        self,
        references_root: Path | str | None = None,
        *,
        paths: list[Path] | None = None,
        embedding_model: str | None = "keyword-overlap-v1",
    ) -> RuntimeKnowledgeBuildResult:
        """Build traceable chunks from Git-versioned references and persist them locally."""

        references_root_path = Path(references_root or self.project_root / "references")
        indexer = ReferenceKnowledgeIndexer(references_root_path, embedding_model=embedding_model)
        result = indexer.build(paths=paths)
        if result.errors:
            joined_errors = "; ".join(result.errors[:5])
            raise ValueError(f"reference knowledge metadata errors: {joined_errors}")

        chunks = sorted(result.chunks, key=lambda chunk: (chunk.source_path, chunk.doc_id, chunk.chunk_id))
        duplicate_chunk_ids = _duplicates(chunk.chunk_id for chunk in chunks)
        if duplicate_chunk_ids:
            raise ValueError(f"duplicate knowledge chunk ids: {', '.join(duplicate_chunk_ids[:5])}")

        self.chunks_dir.mkdir(parents=True, exist_ok=True)
        self.indexes_dir.mkdir(parents=True, exist_ok=True)
        _write_text_atomic(
            self.references_chunks_path,
            "".join(f"{chunk.model_dump_json()}\n" for chunk in chunks),
        )

        manifest = RuntimeKnowledgeManifest(
            index_id=result.manifest.index_id,
            created_at=result.manifest.created_at,
            references_root=_display_path(indexer.references_root, self.project_root),
            runtime_root=_display_path(self.runtime_root, self.project_root),
            chunks_path=_display_path(self.references_chunks_path, self.project_root),
            manifest_path=_display_path(self.manifest_path, self.project_root),
            doc_count=result.manifest.doc_count,
            chunk_count=len(chunks),
            bm25_index_path=None,
            embedding_index_path=None,
            embedding_model=embedding_model,
            sources=result.manifest.sources,
        )
        _write_text_atomic(self.manifest_path, manifest.model_dump_json(indent=2) + "\n")
        return RuntimeKnowledgeBuildResult(
            manifest=manifest,
            chunks_path=manifest.chunks_path,
            manifest_path=manifest.manifest_path,
            errors=[],
        )

    def load_manifest(self) -> RuntimeKnowledgeManifest:
        """Load the persisted runtime manifest."""

        if not self.manifest_path.is_file():
            raise FileNotFoundError(f"runtime knowledge manifest not found: {self.manifest_path}")
        return RuntimeKnowledgeManifest.model_validate_json(self.manifest_path.read_text(encoding="utf-8"))

    def load_chunks(self, chunks_path: Path | str | None = None) -> list[KnowledgeChunk]:
        """Load persisted chunks from the runtime JSONL cache."""

        path = Path(chunks_path or self.references_chunks_path)
        if not path.is_file():
            raise FileNotFoundError(f"runtime knowledge chunks not found: {path}")
        chunks: list[KnowledgeChunk] = []
        for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                chunks.append(KnowledgeChunk.model_validate_json(line))
            except (ValueError, json.JSONDecodeError) as error:
                raise ValueError(f"invalid knowledge chunk JSONL at {path}:{line_number}: {error}") from error
        return chunks

    def build_index(self, *, embedding_model: str | None = "keyword-overlap-v1") -> HybridKnowledgeIndex:
        """Build an in-memory hybrid index from persisted runtime chunks."""

        return HybridKnowledgeIndex(self.load_chunks(), embedding_model=embedding_model)

    def search(
        self,
        query: str,
        *,
        blueprint_scope: BlueprintScope | str | None = None,
        species: str | None = None,
        limit: int = 5,
        include_embedding: bool = True,
        embedding_model: str | None = "keyword-overlap-v1",
    ) -> RuntimeKnowledgeSearchResult:
        """Search persisted runtime chunks with traceable hybrid retrieval."""

        chunks = self.load_chunks()
        index = HybridKnowledgeIndex(chunks, embedding_model=embedding_model)
        hits = index.search(
            query,
            blueprint_scope=blueprint_scope,
            species=species,
            limit=limit,
            include_embedding=include_embedding,
        )
        return RuntimeKnowledgeSearchResult(
            query=query,
            runtime_root=_display_path(self.runtime_root, self.project_root),
            chunk_count=len(chunks),
            hits=hits,
        )

    def inspect_doc(self, doc_id: str) -> RuntimeKnowledgeDocInspection:
        """Return all persisted chunks for one document id."""

        chunks = [chunk for chunk in self.load_chunks() if chunk.doc_id == doc_id]
        sources = sorted({chunk.source_path for chunk in chunks})
        return RuntimeKnowledgeDocInspection(
            doc_id=doc_id,
            runtime_root=_display_path(self.runtime_root, self.project_root),
            chunk_count=len(chunks),
            chunks=chunks,
            sources=sources,
        )

    def _reject_references_runtime_root(self) -> None:
        references_root = (self.project_root / "references").resolve()
        try:
            self.runtime_root.relative_to(references_root)
        except ValueError:
            return
        raise ValueError("runtime knowledge root must not point inside references/")


def _write_text_atomic(path: Path, text: str) -> None:
    temporary_path = path.with_name(f"{path.name}.tmp")
    temporary_path.write_text(text, encoding="utf-8", newline="\n")
    temporary_path.replace(path)


def _display_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _duplicates(values: Iterable[object]) -> list[str]:
    seen: set[str] = set()
    duplicated: list[str] = []
    for value in values:
        normalized = str(value)
        if normalized in seen and normalized not in duplicated:
            duplicated.append(normalized)
        seen.add(normalized)
    return duplicated
