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
    assert search_payload["hits"][0]["chunk"]["doc_id"] == "paper_grm_vanraden_2008"
    assert search_payload["hits"][0]["chunk"]["source_path"] == "references/papers/grm_core_papers_v1.md"

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
