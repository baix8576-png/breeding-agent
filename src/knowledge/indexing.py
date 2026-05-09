"""Local knowledge asset parsing, chunking, and lightweight indexing."""

from __future__ import annotations

import math
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, Field

from contracts.knowledge import (
    BlueprintScope,
    KnowledgeChunk,
    KnowledgeIndexManifest,
    KnowledgeItemV2,
)

_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]+")
_YAML_BLOCK_PATTERN = re.compile(r"```yaml\s+(?P<body>.*?)```", flags=re.DOTALL | re.IGNORECASE)
_HEADING_PATTERN = re.compile(r"^##\s+(?P<title>.+?)\s*$", flags=re.MULTILINE)


class KnowledgeLoadResult(BaseModel):
    """Result of loading local reference assets into searchable chunks."""

    items: list[KnowledgeItemV2] = Field(default_factory=list)
    chunks: list[KnowledgeChunk] = Field(default_factory=list)
    manifest: KnowledgeIndexManifest
    errors: list[str] = Field(default_factory=list)


class KnowledgeSearchHit(BaseModel):
    """Scored local index hit with traceability back to the source asset."""

    chunk: KnowledgeChunk
    score: float
    bm25_score: float
    keyword_score: int
    embedding_score: float
    hit_reasons: list[str] = Field(default_factory=list)
    confidence: float


class HybridKnowledgeIndex:
    """In-memory BM25 + keyword + optional embedding-lite index."""

    def __init__(
        self,
        chunks: list[KnowledgeChunk],
        *,
        embedding_model: str | None = "keyword-overlap-v1",
    ) -> None:
        self._chunks = list(chunks)
        self._embedding_model = embedding_model
        self._chunk_terms = [Counter(_tokenize(chunk.text)) for chunk in self._chunks]
        self._chunk_lengths = [sum(counter.values()) for counter in self._chunk_terms]
        self._avg_doc_length = (
            sum(self._chunk_lengths) / len(self._chunk_lengths) if self._chunk_lengths else 0.0
        )
        self._document_frequency = self._build_document_frequency()

    @property
    def chunks(self) -> list[KnowledgeChunk]:
        return list(self._chunks)

    def _build_document_frequency(self) -> Counter[str]:
        frequency: Counter[str] = Counter()
        for terms in self._chunk_terms:
            for token in terms:
                frequency[token] += 1
        return frequency

    def search(
        self,
        query: str,
        *,
        blueprint_scope: BlueprintScope | str | None = None,
        species: str | None = None,
        limit: int = 5,
        include_embedding: bool = True,
    ) -> list[KnowledgeSearchHit]:
        """Return scored chunks from the local index."""

        query_tokens = _tokenize(query)
        if not query_tokens:
            return []

        scope_filter = _normalize_scope(blueprint_scope)
        species_filter = species.strip().lower() if species else None
        hits: list[KnowledgeSearchHit] = []
        for chunk, terms in zip(self._chunks, self._chunk_terms):
            if scope_filter and chunk.blueprint_scope != scope_filter:
                continue
            if species_filter and chunk.species.lower() not in {"multi_species", species_filter}:
                continue
            bm25_score = self._bm25_score(query_tokens=query_tokens, terms=terms)
            keyword_score = self._keyword_score(query_tokens=query_tokens, chunk=chunk)
            embedding_score = (
                self._embedding_lite_score(query_tokens=query_tokens, terms=terms)
                if include_embedding and self._embedding_model
                else 0.0
            )
            score = bm25_score + keyword_score + embedding_score
            if score <= 0:
                continue
            hits.append(
                KnowledgeSearchHit(
                    chunk=chunk,
                    score=round(score, 4),
                    bm25_score=round(bm25_score, 4),
                    keyword_score=keyword_score,
                    embedding_score=round(embedding_score, 4),
                    hit_reasons=self._hit_reasons(
                        query_tokens=query_tokens,
                        chunk=chunk,
                        bm25_score=bm25_score,
                        keyword_score=keyword_score,
                        embedding_score=embedding_score,
                    ),
                    confidence=self._confidence(
                        bm25_score=bm25_score,
                        keyword_score=keyword_score,
                        embedding_score=embedding_score,
                    ),
                )
            )

        hits.sort(key=lambda hit: (-hit.score, hit.chunk.doc_id, hit.chunk.chunk_id))
        return hits[:limit]

    def _bm25_score(self, *, query_tokens: list[str], terms: Counter[str]) -> float:
        if not self._chunks or not self._avg_doc_length:
            return 0.0
        score = 0.0
        k1 = 1.5
        b = 0.75
        doc_length = sum(terms.values()) or 1
        document_count = len(self._chunks)
        for token in query_tokens:
            frequency = terms.get(token, 0)
            if frequency <= 0:
                continue
            doc_frequency = self._document_frequency.get(token, 0)
            inverse_document_frequency = math.log(
                1 + (document_count - doc_frequency + 0.5) / (doc_frequency + 0.5)
            )
            denominator = frequency + k1 * (1 - b + b * doc_length / self._avg_doc_length)
            score += inverse_document_frequency * frequency * (k1 + 1) / denominator
        return score

    @staticmethod
    def _keyword_score(*, query_tokens: list[str], chunk: KnowledgeChunk) -> int:
        keywords = {keyword.lower() for keyword in chunk.keywords}
        metadata_tokens = {
            chunk.doc_id.lower(),
            chunk.blueprint_scope.value,
            chunk.evidence_level.value,
            chunk.source.value,
            chunk.species.lower(),
            chunk.section.lower(),
        }
        score = 0
        for token in query_tokens:
            if token in keywords:
                score += 2
            elif any(token in value for value in metadata_tokens):
                score += 1
        return score

    @staticmethod
    def _embedding_lite_score(*, query_tokens: list[str], terms: Counter[str]) -> float:
        query_set = set(query_tokens)
        term_set = set(terms)
        if not query_set or not term_set:
            return 0.0
        overlap = len(query_set & term_set)
        union = len(query_set | term_set)
        return overlap / union if union else 0.0

    @staticmethod
    def _hit_reasons(
        *,
        query_tokens: list[str],
        chunk: KnowledgeChunk,
        bm25_score: float,
        keyword_score: int,
        embedding_score: float,
    ) -> list[str]:
        matched_keywords = sorted(set(query_tokens) & {item.lower() for item in chunk.keywords})
        reasons: list[str] = []
        if bm25_score > 0:
            reasons.append(f"bm25_match:{bm25_score:.3f}")
        if keyword_score > 0:
            reasons.append(f"keyword_match:{','.join(matched_keywords[:8]) or keyword_score}")
        if embedding_score > 0:
            reasons.append(f"embedding_overlap:{embedding_score:.3f}")
        reasons.append(f"evidence_level:{chunk.evidence_level.value}")
        reasons.append(f"blueprint_scope:{chunk.blueprint_scope.value}")
        return reasons

    @staticmethod
    def _confidence(*, bm25_score: float, keyword_score: int, embedding_score: float) -> float:
        confidence = min(1.0, (bm25_score / 12.0) + (keyword_score / 20.0) + embedding_score)
        return round(confidence, 3)


class ReferenceKnowledgeIndexer:
    """Build local knowledge chunks from versioned `references/*` markdown assets."""

    def __init__(
        self,
        references_root: Path | str | None = None,
        *,
        embedding_model: str | None = "keyword-overlap-v1",
    ) -> None:
        self.references_root = Path(references_root or Path(__file__).resolve().parents[2] / "references")
        self.project_root = self.references_root.parent
        self.embedding_model = embedding_model

    def build(self, paths: list[Path] | None = None) -> KnowledgeLoadResult:
        """Parse markdown knowledge cards and return chunks plus an index manifest."""

        items: list[KnowledgeItemV2] = []
        chunks: list[KnowledgeChunk] = []
        errors: list[str] = []
        source_paths = self._candidate_paths(paths)
        for path in source_paths:
            parsed_items, parsed_chunks, parsed_errors = self._parse_markdown_file(path)
            items.extend(parsed_items)
            chunks.extend(parsed_chunks)
            errors.extend(parsed_errors)

        unique_doc_ids = {item.doc_id for item in items}
        manifest = KnowledgeIndexManifest(
            index_id=f"references-{len(unique_doc_ids)}-docs-{len(chunks)}-chunks",
            created_at=datetime.now(timezone.utc),
            source_root=_safe_relative_path(self.references_root, self.project_root),
            doc_count=len(unique_doc_ids),
            chunk_count=len(chunks),
            bm25_index_path="memory://knowledge/bm25",
            embedding_index_path="memory://knowledge/embedding-lite" if self.embedding_model else None,
            embedding_model=self.embedding_model,
            sources=sorted({_safe_relative_path(path, self.project_root) for path in source_paths}),
        )
        return KnowledgeLoadResult(items=items, chunks=chunks, manifest=manifest, errors=errors)

    def build_index(self, paths: list[Path] | None = None) -> HybridKnowledgeIndex:
        """Build an in-memory hybrid index from local knowledge cards."""

        result = self.build(paths=paths)
        return HybridKnowledgeIndex(result.chunks, embedding_model=self.embedding_model)

    def _candidate_paths(self, paths: list[Path] | None) -> list[Path]:
        if paths is not None:
            return [Path(path) for path in paths if Path(path).is_file()]
        if not self.references_root.exists():
            return []
        return sorted(path for path in self.references_root.rglob("*.md") if path.is_file())

    def _parse_markdown_file(
        self,
        path: Path,
    ) -> tuple[list[KnowledgeItemV2], list[KnowledgeChunk], list[str]]:
        text = path.read_text(encoding="utf-8")
        sections = _split_level_two_sections(text)
        items: list[KnowledgeItemV2] = []
        chunks: list[KnowledgeChunk] = []
        errors: list[str] = []
        for section_title, section_body in sections:
            metadata = _extract_knowledge_metadata(section_body)
            if not metadata:
                continue
            try:
                item = KnowledgeItemV2(**metadata)
            except Exception as exc:  # pragma: no cover - message content depends on pydantic
                errors.append(f"{_safe_relative_path(path, self.project_root)}::{section_title}: {exc}")
                continue
            clean_text = _strip_metadata_fences(section_body).strip()
            if not clean_text:
                clean_text = section_title
            chunk = KnowledgeChunk(
                chunk_id=f"{item.doc_id}::{_slugify(section_title)}",
                doc_id=item.doc_id,
                source_path=_safe_relative_path(path, self.project_root),
                blueprint_scope=item.blueprint_scope,
                species=item.species,
                evidence_level=item.evidence_level,
                source=item.source,
                section=section_title,
                page_or_anchor=f"#{_slugify(section_title)}",
                text=f"{section_title}\n{clean_text}",
                updated_at=item.updated_at,
                owner=item.owner,
                keywords=_keywords_from_parts(
                    item.doc_id,
                    item.species,
                    item.blueprint_scope.value,
                    item.evidence_level.value,
                    item.source.value,
                    section_title,
                    clean_text,
                ),
                embedding_model=self.embedding_model,
            )
            items.append(item)
            chunks.append(chunk)
        return items, chunks, errors


def _split_level_two_sections(text: str) -> list[tuple[str, str]]:
    matches = list(_HEADING_PATTERN.finditer(text))
    sections: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections.append((match.group("title").strip(), text[start:end].strip()))
    return sections


def _extract_knowledge_metadata(text: str) -> dict[str, str]:
    for match in _YAML_BLOCK_PATTERN.finditer(text):
        body = match.group("body")
        if "knowledge_item.v2:" not in body:
            continue
        return _parse_simple_yaml_mapping(body)
    return {}


def _parse_simple_yaml_mapping(yaml_body: str) -> dict[str, str]:
    in_item = False
    data: dict[str, str] = {}
    for raw_line in yaml_body.splitlines():
        line = raw_line.rstrip()
        if not line.strip():
            continue
        if line.strip() == "knowledge_item.v2:":
            in_item = True
            continue
        if not in_item:
            continue
        if not raw_line.startswith("  ") or ":" not in line:
            break
        key, _, value = line.strip().partition(":")
        data[key.strip()] = _unquote(value.strip())
    return data


def _strip_metadata_fences(text: str) -> str:
    return _YAML_BLOCK_PATTERN.sub("", text).strip()


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def _keywords_from_parts(*parts: object) -> list[str]:
    tokens: list[str] = []
    for part in parts:
        tokens.extend(_tokenize(str(part)))
    return list(dict.fromkeys(tokens))


def _tokenize(text: str) -> list[str]:
    return [token.lower() for token in _TOKEN_PATTERN.findall(text.lower())]


def _normalize_scope(scope: BlueprintScope | str | None) -> BlueprintScope | None:
    if scope is None:
        return None
    if isinstance(scope, BlueprintScope):
        return scope
    return BlueprintScope(scope)


def _slugify(value: str) -> str:
    tokens = _tokenize(value)
    return "-".join(tokens) if tokens else "section"


def _safe_relative_path(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")
