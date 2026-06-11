"""Runtime knowledge store for local-first RAG artifacts."""

from __future__ import annotations

import json
from collections.abc import Iterable
from collections import Counter
from datetime import datetime
from datetime import timezone
from pathlib import Path

from pydantic import BaseModel, Field

from contracts.knowledge import (
    BlueprintScope,
    EvidenceLevel,
    KnowledgeChunk,
    KnowledgeSource,
    normalize_blueprint_scope_value,
)
from knowledge.indexing import (
    HybridKnowledgeIndex,
    KnowledgeSearchHit,
    ReferenceKnowledgeIndexer,
    tokenize_knowledge_text,
)
from knowledge.query_router import KnowledgeQueryRouter, KnowledgeRetrievalPlan
from knowledge.rerank import KnowledgeReranker
from knowledge.traceability import KnowledgeRetrievalTrace, build_retrieval_trace


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


class RuntimeBm25IndexArtifact(BaseModel):
    """Persisted BM25/keyword statistics for runtime chunk search."""

    schema_version: str = "knowledge_bm25_index.v1"
    index_id: str = Field(min_length=3)
    created_at: datetime
    chunks_path: str = Field(min_length=1)
    chunk_count: int = Field(ge=0)
    avg_doc_length: float = Field(ge=0)
    chunk_ids: list[str] = Field(default_factory=list)
    chunk_lengths: dict[str, int] = Field(default_factory=dict)
    document_frequency: dict[str, int] = Field(default_factory=dict)
    term_frequency: dict[str, dict[str, int]] = Field(default_factory=dict)


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
    plan: KnowledgeRetrievalPlan | None = None
    metadata_fallbacks: list[str] = Field(default_factory=list)
    rerank_applied: bool = False
    rerank_mode: str | None = None
    trace: KnowledgeRetrievalTrace | None = None
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
    def bm25_dir(self) -> Path:
        return self.indexes_dir / "bm25"

    @property
    def references_chunks_path(self) -> Path:
        return self.chunks_dir / "references.jsonl"

    @property
    def local_ingestion_chunks_path(self) -> Path:
        return self.chunks_dir / "local_ingestion.jsonl"

    @property
    def bm25_artifact_path(self) -> Path:
        return self.bm25_dir / "references_bm25.json"

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
        self.bm25_dir.mkdir(parents=True, exist_ok=True)
        _write_chunks_jsonl(self.references_chunks_path, chunks)
        bm25_artifact = _build_bm25_artifact(
            chunks=chunks,
            index_id=result.manifest.index_id,
            chunks_path=_display_path(self.references_chunks_path, self.project_root),
        )
        _write_text_atomic(self.bm25_artifact_path, bm25_artifact.model_dump_json(indent=2) + "\n")

        manifest = RuntimeKnowledgeManifest(
            index_id=result.manifest.index_id,
            created_at=result.manifest.created_at,
            references_root=_display_path(indexer.references_root, self.project_root),
            runtime_root=_display_path(self.runtime_root, self.project_root),
            chunks_path=_display_path(self.references_chunks_path, self.project_root),
            manifest_path=_display_path(self.manifest_path, self.project_root),
            doc_count=result.manifest.doc_count,
            chunk_count=len(chunks),
            bm25_index_path=_display_path(self.bm25_artifact_path, self.project_root),
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

        if chunks_path is None:
            if not self.chunks_dir.is_dir():
                raise FileNotFoundError(f"runtime knowledge chunks not found: {self.chunks_dir}")
            chunks: list[KnowledgeChunk] = []
            for path in sorted(self.chunks_dir.glob("*.jsonl")):
                chunks.extend(self._load_chunks_file(path))
            if not chunks:
                raise FileNotFoundError(f"runtime knowledge chunks not found: {self.chunks_dir}")
            return chunks
        path = Path(chunks_path)
        return self._load_chunks_file(path)

    def _load_chunks_file(self, path: Path) -> list[KnowledgeChunk]:
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

    def write_local_ingestion_chunks(self, chunks: list[KnowledgeChunk]) -> None:
        """Upsert locally ingested chunks into the runtime ingestion JSONL cache."""

        self.chunks_dir.mkdir(parents=True, exist_ok=True)
        existing = []
        if self.local_ingestion_chunks_path.exists():
            existing = [
                chunk for chunk in self._load_chunks_file(self.local_ingestion_chunks_path)
                if chunk.doc_id not in {new_chunk.doc_id for new_chunk in chunks}
            ]
        merged = sorted([*existing, *chunks], key=lambda chunk: (chunk.source_path, chunk.doc_id, chunk.chunk_id))
        _write_chunks_jsonl(self.local_ingestion_chunks_path, merged)

    def rebuild_runtime_index_from_chunks(
        self,
        *,
        embedding_model: str | None = "keyword-overlap-v1",
    ) -> RuntimeKnowledgeBuildResult:
        """Rebuild manifest and BM25 artifact from all runtime chunk files."""

        chunks = sorted(self.load_chunks(), key=lambda chunk: (chunk.source_path, chunk.doc_id, chunk.chunk_id))
        self.indexes_dir.mkdir(parents=True, exist_ok=True)
        self.bm25_dir.mkdir(parents=True, exist_ok=True)
        index_id = f"runtime-{len({chunk.doc_id for chunk in chunks})}-docs-{len(chunks)}-chunks"
        bm25_artifact = _build_bm25_artifact(
            chunks=chunks,
            index_id=index_id,
            chunks_path=_display_path(self.chunks_dir, self.project_root),
        )
        _write_text_atomic(self.bm25_artifact_path, bm25_artifact.model_dump_json(indent=2) + "\n")
        manifest = RuntimeKnowledgeManifest(
            index_id=index_id,
            created_at=bm25_artifact.created_at,
            references_root=_display_path(self.project_root / "references", self.project_root),
            runtime_root=_display_path(self.runtime_root, self.project_root),
            chunks_path=_display_path(self.chunks_dir, self.project_root),
            manifest_path=_display_path(self.manifest_path, self.project_root),
            doc_count=len({chunk.doc_id for chunk in chunks}),
            chunk_count=len(chunks),
            bm25_index_path=_display_path(self.bm25_artifact_path, self.project_root),
            embedding_index_path=None,
            embedding_model=embedding_model,
            sources=sorted({chunk.source_path for chunk in chunks}),
        )
        _write_text_atomic(self.manifest_path, manifest.model_dump_json(indent=2) + "\n")
        return RuntimeKnowledgeBuildResult(
            manifest=manifest,
            chunks_path=manifest.chunks_path,
            manifest_path=manifest.manifest_path,
            errors=[],
        )

    def load_bm25_artifact(self) -> RuntimeBm25IndexArtifact:
        """Load persisted BM25/keyword statistics."""

        if not self.bm25_artifact_path.is_file():
            raise FileNotFoundError(f"runtime BM25 artifact not found: {self.bm25_artifact_path}")
        return RuntimeBm25IndexArtifact.model_validate_json(
            self.bm25_artifact_path.read_text(encoding="utf-8")
        )

    def build_index(
        self,
        *,
        embedding_model: str | None = "keyword-overlap-v1",
        use_persisted_bm25: bool = True,
    ) -> HybridKnowledgeIndex:
        """Build an in-memory hybrid index from persisted runtime chunks."""

        chunks = self.load_chunks()
        if not use_persisted_bm25:
            return HybridKnowledgeIndex(chunks, embedding_model=embedding_model)
        try:
            artifact = self.load_bm25_artifact()
        except FileNotFoundError:
            return HybridKnowledgeIndex(chunks, embedding_model=embedding_model)
        precomputed = _precomputed_bm25_for_chunks(chunks=chunks, artifact=artifact)
        if precomputed is None:
            return HybridKnowledgeIndex(chunks, embedding_model=embedding_model)
        chunk_terms, chunk_lengths, avg_doc_length, document_frequency = precomputed
        return HybridKnowledgeIndex(
            chunks,
            embedding_model=embedding_model,
            chunk_terms=chunk_terms,
            chunk_lengths=chunk_lengths,
            avg_doc_length=avg_doc_length,
            document_frequency=document_frequency,
        )

    def plan_query(self, query: str) -> KnowledgeRetrievalPlan:
        """Create a metadata-aware retrieval plan for a user query."""

        return KnowledgeQueryRouter().plan(query)

    def search(
        self,
        query: str,
        *,
        blueprint_scope: BlueprintScope | str | None = None,
        species: str | None = None,
        evidence_levels: list[EvidenceLevel | str] | None = None,
        sources: list[KnowledgeSource | str] | None = None,
        limit: int = 5,
        include_embedding: bool = True,
        embedding_model: str | None = "keyword-overlap-v1",
        use_persisted_bm25: bool = True,
        use_query_router: bool = False,
        rerank: bool = True,
    ) -> RuntimeKnowledgeSearchResult:
        """Search persisted runtime chunks with traceable hybrid retrieval."""

        chunks = self.load_chunks()
        plan = self.plan_query(query) if use_query_router else None
        effective_blueprint_scope = blueprint_scope or (plan.blueprint_scope if plan else None)
        effective_species = species or (plan.species if plan else None)
        effective_evidence_levels = evidence_levels or (plan.evidence_levels if plan else None)
        effective_sources = sources or (plan.sources if plan else None)
        applied_blueprint_scope = _as_blueprint_scope(effective_blueprint_scope)
        applied_species = effective_species
        applied_evidence_levels = _as_evidence_levels(effective_evidence_levels)
        applied_sources = _as_sources(effective_sources)
        index = self.build_index(
            embedding_model=embedding_model,
            use_persisted_bm25=use_persisted_bm25,
        )
        metadata_fallbacks: list[str] = []
        hits = index.search(
            query,
            blueprint_scope=effective_blueprint_scope,
            species=effective_species,
            evidence_levels=effective_evidence_levels,
            sources=effective_sources,
            limit=limit,
            include_embedding=include_embedding,
        )
        if not hits and plan and (effective_evidence_levels or effective_sources):
            metadata_fallbacks.append("dropped_evidence_source_filters")
            applied_evidence_levels = []
            applied_sources = []
            hits = index.search(
                query,
                blueprint_scope=effective_blueprint_scope,
                species=effective_species,
                limit=limit,
                include_embedding=include_embedding,
            )
        if not hits and plan and effective_species:
            metadata_fallbacks.append("dropped_species_filter")
            applied_species = None
            hits = index.search(
                query,
                blueprint_scope=effective_blueprint_scope,
                limit=limit,
                include_embedding=include_embedding,
            )
        if not hits and plan and effective_blueprint_scope:
            metadata_fallbacks.append("dropped_blueprint_scope_filter")
            applied_blueprint_scope = None
            hits = index.search(
                query,
                limit=limit,
                include_embedding=include_embedding,
            )
        rerank_mode = None
        if rerank and hits:
            reranker = KnowledgeReranker()
            rerank_mode = reranker.config.mode
            hits = reranker.rerank(query=query, hits=hits, plan=plan, limit=limit)
        trace = build_retrieval_trace(
            user_query=query,
            plan=plan,
            applied_blueprint_scope=applied_blueprint_scope,
            applied_species=applied_species,
            applied_evidence_levels=applied_evidence_levels,
            applied_sources=applied_sources,
            used_query_router=use_query_router,
            metadata_fallbacks=metadata_fallbacks,
            hits=hits,
        )
        return RuntimeKnowledgeSearchResult(
            query=query,
            runtime_root=_display_path(self.runtime_root, self.project_root),
            chunk_count=len(chunks),
            plan=plan,
            metadata_fallbacks=metadata_fallbacks,
            rerank_applied=bool(rerank and hits),
            rerank_mode=rerank_mode,
            trace=trace,
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


def _write_chunks_jsonl(path: Path, chunks: list[KnowledgeChunk]) -> None:
    _write_text_atomic(path, "".join(f"{chunk.model_dump_json()}\n" for chunk in chunks))


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


def _as_blueprint_scope(value: BlueprintScope | str | None) -> BlueprintScope | None:
    if value is None:
        return None
    if isinstance(value, BlueprintScope):
        return value
    return BlueprintScope(normalize_blueprint_scope_value(value))


def _as_evidence_levels(values: list[EvidenceLevel | str] | None) -> list[EvidenceLevel]:
    if not values:
        return []
    return [value if isinstance(value, EvidenceLevel) else EvidenceLevel(value) for value in values]


def _as_sources(values: list[KnowledgeSource | str] | None) -> list[KnowledgeSource]:
    if not values:
        return []
    return [value if isinstance(value, KnowledgeSource) else KnowledgeSource(value) for value in values]


def _build_bm25_artifact(
    *,
    chunks: list[KnowledgeChunk],
    index_id: str,
    chunks_path: str,
) -> RuntimeBm25IndexArtifact:
    term_counters = {chunk.chunk_id: Counter(tokenize_knowledge_text(chunk.text)) for chunk in chunks}
    document_frequency: Counter[str] = Counter()
    for counter in term_counters.values():
        for token in counter:
            document_frequency[token] += 1
    chunk_lengths = {chunk_id: sum(counter.values()) for chunk_id, counter in term_counters.items()}
    avg_doc_length = sum(chunk_lengths.values()) / len(chunk_lengths) if chunk_lengths else 0.0
    return RuntimeBm25IndexArtifact(
        index_id=index_id,
        created_at=datetime.now(timezone.utc),
        chunks_path=chunks_path,
        chunk_count=len(chunks),
        avg_doc_length=avg_doc_length,
        chunk_ids=[chunk.chunk_id for chunk in chunks],
        chunk_lengths=chunk_lengths,
        document_frequency=dict(document_frequency),
        term_frequency={chunk_id: dict(counter) for chunk_id, counter in term_counters.items()},
    )


def _precomputed_bm25_for_chunks(
    *,
    chunks: list[KnowledgeChunk],
    artifact: RuntimeBm25IndexArtifact,
) -> tuple[list[Counter[str]], list[int], float, Counter[str]] | None:
    chunk_ids = [chunk.chunk_id for chunk in chunks]
    if chunk_ids != artifact.chunk_ids:
        return None
    chunk_terms: list[Counter[str]] = []
    chunk_lengths: list[int] = []
    for chunk_id in chunk_ids:
        term_frequency = artifact.term_frequency.get(chunk_id)
        if term_frequency is None:
            return None
        chunk_terms.append(Counter(term_frequency))
        chunk_lengths.append(artifact.chunk_lengths.get(chunk_id, sum(term_frequency.values())))
    return (
        chunk_terms,
        chunk_lengths,
        artifact.avg_doc_length,
        Counter(artifact.document_frequency),
    )
