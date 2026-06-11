from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from contracts.knowledge import KnowledgeItemV2
from knowledge.ingestion import KnowledgeIngestionBridge
from knowledge.runtime_store import KnowledgeRuntimeStore


def test_grobid_tei_ingestion_writes_local_runtime_chunks_and_rebuilds_index(tmp_path: Path) -> None:
    runtime_root = tmp_path / ".geneagent" / "knowledge"
    tei_path = runtime_root / "grobid_tei" / "demo.tei.xml"
    tei_path.parent.mkdir(parents=True)
    tei_path.write_text(_tei_fixture(), encoding="utf-8")
    store = KnowledgeRuntimeStore(runtime_root=runtime_root)
    store.build_from_references(
        Path("references"),
        paths=[Path("references/papers/grm_core_papers_v1.md")],
    )
    item = KnowledgeItemV2(
        doc_id="local_grobid_grm_demo",
        version="v2",
        species="cattle",
        blueprint_scope="quantitative_genetics",
        evidence_level="peer_reviewed",
        source="paper",
        updated_at=datetime(2026, 6, 11, tzinfo=timezone.utc),
        owner="geneagent",
    )

    result = KnowledgeIngestionBridge(store).ingest_grobid_tei(tei_path, item=item)

    assert result.status == "ingested"
    assert result.doc_id == "local_grobid_grm_demo"
    assert result.copyright_boundary == "local_runtime_only_no_git"
    assert result.chunks_written == 2
    assert (runtime_root / "chunks" / "local_ingestion.jsonl").is_file()
    manifest = store.load_manifest()
    assert manifest.doc_count == 11
    assert manifest.chunk_count == 12
    assert store.load_bm25_artifact().chunk_count == 12

    search = store.search(
        "allele frequency centered marker relationships",
        blueprint_scope="quantitative_genetics",
        limit=3,
        use_query_router=True,
    )
    assert search.hits
    assert search.hits[0].chunk.doc_id == "local_grobid_grm_demo"
    assert search.trace is not None
    assert search.trace.retrieved_chunks[0].source_path.endswith("demo.tei.xml")


def _tei_fixture() -> str:
    return """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader>
    <fileDesc>
      <titleStmt>
        <title>Runtime GRM Ingestion Demo</title>
      </titleStmt>
    </fileDesc>
    <profileDesc>
      <abstract>
        <p>Genomic relationship matrices support animal breeding decisions.</p>
      </abstract>
    </profileDesc>
  </teiHeader>
  <text>
    <body>
      <div>
        <head>Methods</head>
        <p>Allele frequency centered marker relationships are computed for genomic prediction.</p>
      </div>
    </body>
  </text>
</TEI>
"""
