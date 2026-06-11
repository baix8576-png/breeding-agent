from __future__ import annotations

from pathlib import Path

from knowledge.runtime_store import KnowledgeRuntimeStore


def test_runtime_search_applies_offline_rerank_by_default(tmp_path: Path) -> None:
    store = KnowledgeRuntimeStore(runtime_root=tmp_path / ".geneagent" / "knowledge")
    store.build_from_references(
        Path("references"),
        paths=[Path("references/papers/grm_core_papers_v1.md")],
    )

    result = store.search(
        "VanRaden genomic relationship matrix GBLUP",
        blueprint_scope="quantitative_genetics",
        limit=3,
        use_query_router=True,
    )

    assert result.rerank_applied is True
    assert result.rerank_mode == "offline_deterministic"
    assert result.hits
    assert any(reason == "rerank:offline_deterministic" for reason in result.hits[0].hit_reasons)
    assert any(reason.startswith("rerank_bonus:") for reason in result.hits[0].hit_reasons)
    assert result.trace is not None
    assert any(reason == "rerank:offline_deterministic" for reason in result.trace.retrieved_chunks[0].hit_reasons)


def test_runtime_search_can_disable_rerank(tmp_path: Path) -> None:
    store = KnowledgeRuntimeStore(runtime_root=tmp_path / ".geneagent" / "knowledge")
    store.build_from_references(
        Path("references"),
        paths=[Path("references/papers/grm_core_papers_v1.md")],
    )

    result = store.search(
        "VanRaden genomic relationship matrix GBLUP",
        blueprint_scope="quantitative_genetics",
        limit=3,
        use_query_router=True,
        rerank=False,
    )

    assert result.rerank_applied is False
    assert result.rerank_mode is None
    assert result.hits
    assert not any(reason.startswith("rerank:") for reason in result.hits[0].hit_reasons)
