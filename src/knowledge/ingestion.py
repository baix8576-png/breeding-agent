"""Bridge local extracted knowledge into the runtime RAG store."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from contracts.knowledge import KnowledgeChunk, KnowledgeItemV2
from knowledge.grobid import GrobidDocument, GrobidTeiParser
from knowledge.indexing import tokenize_knowledge_text
from knowledge.runtime_store import KnowledgeRuntimeStore, RuntimeKnowledgeBuildResult


class KnowledgeIngestionResult(BaseModel):
    """Result of importing local extracted text into runtime chunks."""

    schema_version: str = "knowledge_ingestion_result.v1"
    status: str = "ingested"
    doc_id: str = Field(min_length=3)
    source_path: str = Field(min_length=1)
    chunks_written: int = Field(ge=0)
    chunks_path: str = Field(min_length=1)
    rebuilt_manifest_path: str | None = None
    copyright_boundary: str = "local_runtime_only_no_git"
    messages: list[str] = Field(default_factory=list)


class KnowledgeIngestionBridge:
    """Convert local TEI/extracted text into runtime-store chunks."""

    def __init__(self, store: KnowledgeRuntimeStore | None = None) -> None:
        self.store = store or KnowledgeRuntimeStore()

    def ingest_grobid_tei(
        self,
        tei_path: Path | str,
        *,
        item: KnowledgeItemV2,
        rebuild_index: bool = True,
    ) -> KnowledgeIngestionResult:
        """Parse a local GROBID TEI file and upsert chunks into the runtime store."""

        path = Path(tei_path)
        document = GrobidTeiParser().parse_file(path, doc_id=item.doc_id)
        return self.ingest_grobid_document(document, item=item, rebuild_index=rebuild_index)

    def ingest_grobid_document(
        self,
        document: GrobidDocument,
        *,
        item: KnowledgeItemV2,
        rebuild_index: bool = True,
    ) -> KnowledgeIngestionResult:
        """Convert a parsed GROBID document into traceable runtime chunks."""

        chunks = _chunks_from_grobid_document(document=document, item=item)
        self.store.write_local_ingestion_chunks(chunks)
        rebuild_result: RuntimeKnowledgeBuildResult | None = None
        if rebuild_index:
            rebuild_result = self.store.rebuild_runtime_index_from_chunks()
        return KnowledgeIngestionResult(
            doc_id=item.doc_id,
            source_path=document.source_path or item.doc_id,
            chunks_written=len(chunks),
            chunks_path=_display_path(self.store.local_ingestion_chunks_path, self.store.project_root),
            rebuilt_manifest_path=rebuild_result.manifest_path if rebuild_result else None,
            messages=[
                "source_text_stays_in_local_runtime_store",
                "do_not_commit_pdf_tei_extracted_text_or_runtime_chunks",
            ],
        )


def _chunks_from_grobid_document(*, document: GrobidDocument, item: KnowledgeItemV2) -> list[KnowledgeChunk]:
    source_path = document.source_path or f"grobid:{item.doc_id}"
    sections: list[tuple[str, str, str]] = []
    if document.abstract.strip():
        sections.append(("Abstract", document.abstract.strip(), "#abstract"))
    for section in document.sections:
        sections.append((section.title, section.text, section.page_or_anchor or f"#{_slugify(section.title)}"))
    if not sections:
        fallback_text = document.title or item.doc_id
        sections.append(("Document", fallback_text, "#document"))

    chunks: list[KnowledgeChunk] = []
    for title, text, page_or_anchor in sections:
        chunk_text = "\n".join(part for part in [document.title, title, text] if part).strip()
        chunks.append(
            KnowledgeChunk(
                chunk_id=f"{item.doc_id}::{_slugify(title)}",
                doc_id=item.doc_id,
                source_path=source_path.replace("\\", "/"),
                blueprint_scope=item.blueprint_scope,
                species=item.species,
                evidence_level=item.evidence_level,
                source=item.source,
                section=title,
                page_or_anchor=page_or_anchor,
                text=chunk_text,
                updated_at=item.updated_at,
                owner=item.owner,
                keywords=_keywords(item.doc_id, item.species, item.blueprint_scope.value, title, chunk_text),
                embedding_model="keyword-overlap-v1",
            )
        )
    return chunks


def _keywords(*parts: str) -> list[str]:
    tokens: list[str] = []
    for part in parts:
        tokens.extend(tokenize_knowledge_text(part))
    return list(dict.fromkeys(tokens))


def _slugify(value: str) -> str:
    tokens = tokenize_knowledge_text(value)
    return "-".join(tokens) if tokens else "section"


def _display_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()
