from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from cli.app import app


runner = CliRunner()


def test_cli_knowledge_build_search_and_inspect_doc(tmp_path: Path) -> None:
    runtime_root = tmp_path / ".geneagent" / "knowledge"

    build_result = runner.invoke(
        app,
        [
            "knowledge",
            "build-index",
            "--runtime-root",
            str(runtime_root),
            "--references-root",
            "references",
            "--source-file",
            "references/papers/grm_core_papers_v1.md",
        ],
    )

    assert build_result.exit_code == 0, build_result.stdout
    build_payload = json.loads(build_result.stdout)
    assert build_payload["manifest"]["doc_count"] == 10
    assert build_payload["manifest"]["chunk_count"] == 10
    assert build_payload["manifest"]["bm25_index_path"].endswith("indexes/bm25/references_bm25.json")
    assert (runtime_root / "chunks" / "references.jsonl").is_file()
    assert (runtime_root / "indexes" / "manifest.json").is_file()
    assert (runtime_root / "indexes" / "bm25" / "references_bm25.json").is_file()

    search_result = runner.invoke(
        app,
        [
            "knowledge",
            "search",
            "VanRaden genomic relationship matrix GBLUP",
            "--runtime-root",
            str(runtime_root),
            "--blueprint-scope",
            "quantitative_genetics",
            "--limit",
            "3",
        ],
    )

    assert search_result.exit_code == 0, search_result.stdout
    search_payload = json.loads(search_result.stdout)
    assert search_payload["chunk_count"] == 10
    assert search_payload["plan"]["blueprint_scope"] == "quantitative_genetics"
    assert search_payload["rerank_applied"] is True
    assert search_payload["rerank_mode"] == "offline_deterministic"
    assert search_payload["trace"]["user_query"] == "VanRaden genomic relationship matrix GBLUP"
    assert search_payload["trace"]["retrieved_chunks"][0]["doc_id"] == "paper_grm_vanraden_2008"
    assert search_payload["hits"][0]["chunk"]["doc_id"] == "paper_grm_vanraden_2008"
    assert search_payload["hits"][0]["chunk"]["source_path"] == "references/papers/grm_core_papers_v1.md"

    plan_result = runner.invoke(
        app,
        [
            "knowledge",
            "plan-query",
            "猪 PigGTEx FarmGTEx eQTL regulatory variants literature DOI",
        ],
    )

    assert plan_result.exit_code == 0, plan_result.stdout
    plan_payload = json.loads(plan_result.stdout)
    assert plan_payload["species"] == "pig"
    assert plan_payload["blueprint_scope"] == "association_mapping"
    assert "paper" in plan_payload["sources"]

    inspect_result = runner.invoke(
        app,
        [
            "knowledge",
            "inspect-doc",
            "paper_grm_vanraden_2008",
            "--runtime-root",
            str(runtime_root),
        ],
    )

    assert inspect_result.exit_code == 0, inspect_result.stdout
    inspect_payload = json.loads(inspect_result.stdout)
    assert inspect_payload["doc_id"] == "paper_grm_vanraden_2008"
    assert inspect_payload["chunk_count"] == 1
    assert inspect_payload["sources"] == ["references/papers/grm_core_papers_v1.md"]


def test_cli_knowledge_ingest_tei_then_searches_local_runtime_chunks(tmp_path: Path) -> None:
    runtime_root = tmp_path / ".geneagent" / "knowledge"
    tei_path = runtime_root / "grobid_tei" / "demo.tei.xml"
    tei_path.parent.mkdir(parents=True)
    tei_path.write_text(_tei_fixture(), encoding="utf-8")

    build_result = runner.invoke(
        app,
        [
            "knowledge",
            "build-index",
            "--runtime-root",
            str(runtime_root),
            "--references-root",
            "references",
            "--source-file",
            "references/papers/grm_core_papers_v1.md",
        ],
    )
    assert build_result.exit_code == 0, build_result.stdout

    ingest_result = runner.invoke(
        app,
        [
            "knowledge",
            "ingest-tei",
            str(tei_path),
            "--runtime-root",
            str(runtime_root),
            "--doc-id",
            "local_cli_grobid_demo",
            "--species",
            "cattle",
            "--blueprint-scope",
            "quantitative_genetics",
            "--evidence-level",
            "peer_reviewed",
            "--source",
            "paper",
        ],
    )
    assert ingest_result.exit_code == 0, ingest_result.stdout
    ingest_payload = json.loads(ingest_result.stdout)
    assert ingest_payload["doc_id"] == "local_cli_grobid_demo"
    assert ingest_payload["chunks_written"] == 2
    assert ingest_payload["copyright_boundary"] == "local_runtime_only_no_git"

    search_result = runner.invoke(
        app,
        [
            "knowledge",
            "search",
            "allele frequency centered marker relationships",
            "--runtime-root",
            str(runtime_root),
            "--blueprint-scope",
            "quantitative_genetics",
            "--limit",
            "1",
        ],
    )
    assert search_result.exit_code == 0, search_result.stdout
    search_payload = json.loads(search_result.stdout)
    assert search_payload["hits"][0]["chunk"]["doc_id"] == "local_cli_grobid_demo"


def _tei_fixture() -> str:
    return """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader>
    <fileDesc>
      <titleStmt>
        <title>CLI Runtime GRM Ingestion Demo</title>
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
