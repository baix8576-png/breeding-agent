from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from knowledge.source_fetcher import KnowledgeSourceFetcher


def _write_manifest(path: Path, sources: list[dict[str, str]]) -> None:
    path.write_text(json.dumps({"sources": sources}, indent=2), encoding="utf-8")


def test_fetch_manifest_downloads_only_open_sources_to_local_knowledge_root(tmp_path: Path) -> None:
    manifest_path = tmp_path / "sources.json"
    _write_manifest(
        manifest_path,
        [
            {
                "doc_id": "paper_open_pdf",
                "module_id": "L05",
                "title": "Open paper",
                "url": "https://example.test/open.pdf",
                "output_name": "open.pdf",
                "access": "open_access",
            },
            {
                "doc_id": "paper_restricted_pdf",
                "module_id": "L05",
                "title": "Restricted paper",
                "url": "https://example.test/restricted.pdf",
                "output_name": "restricted.pdf",
                "access": "restricted",
            },
        ],
    )
    requested_urls: list[str] = []

    def downloader(url: str) -> bytes:
        requested_urls.append(url)
        return b"open-pdf-bytes"

    fetcher = KnowledgeSourceFetcher(tmp_path / ".geneagent" / "knowledge", downloader=downloader)

    report = fetcher.fetch_manifest(manifest_path)

    assert requested_urls == ["https://example.test/open.pdf"]
    assert (tmp_path / ".geneagent" / "knowledge" / "raw_pdfs" / "open.pdf").read_bytes() == b"open-pdf-bytes"
    assert not (tmp_path / ".geneagent" / "knowledge" / "raw_pdfs" / "restricted.pdf").exists()
    assert [entry.status for entry in report.entries] == ["downloaded", "skipped"]
    assert report.entries[1].reason == "access_not_allowed:restricted"
    assert report.report_path is not None
    assert Path(report.report_path).is_file()


def test_fetch_manifest_rejects_unsafe_output_names_before_download(tmp_path: Path) -> None:
    manifest_path = tmp_path / "unsafe.json"
    _write_manifest(
        manifest_path,
        [
            {
                "doc_id": "paper_bad_path",
                "module_id": "L05",
                "title": "Unsafe path",
                "url": "https://example.test/open.pdf",
                "output_name": "../open.pdf",
                "access": "open_access",
            },
            {
                "doc_id": "paper_backslash_path",
                "module_id": "L05",
                "title": "Unsafe Windows path",
                "url": "https://example.test/open2.pdf",
                "output_name": "nested\\open2.pdf",
                "access": "open_access",
            },
        ],
    )

    def downloader(url: str) -> bytes:
        raise AssertionError(f"unsafe URL should not be downloaded: {url}")

    fetcher = KnowledgeSourceFetcher(tmp_path / ".geneagent" / "knowledge", downloader=downloader)

    report = fetcher.fetch_manifest(manifest_path)

    assert [entry.status for entry in report.entries] == ["failed", "failed"]
    assert [entry.reason for entry in report.entries] == [
        "unsafe_output_name",
        "unsafe_output_name",
    ]
    assert list((tmp_path / ".geneagent" / "knowledge").rglob("*.pdf")) == []


def test_fetch_manifest_checksum_mismatch_does_not_write_file(tmp_path: Path) -> None:
    manifest_path = tmp_path / "checksum.json"
    _write_manifest(
        manifest_path,
        [
            {
                "doc_id": "paper_bad_checksum",
                "module_id": "L05",
                "title": "Checksum mismatch",
                "url": "https://example.test/open.pdf",
                "output_name": "open.pdf",
                "access": "open_access",
                "expected_sha256": hashlib.sha256(b"expected").hexdigest(),
            }
        ],
    )
    fetcher = KnowledgeSourceFetcher(
        tmp_path / ".geneagent" / "knowledge",
        downloader=lambda _url: b"actual",
    )

    report = fetcher.fetch_manifest(manifest_path)

    assert report.entries[0].status == "failed"
    assert report.entries[0].reason == "checksum_mismatch"
    assert not (tmp_path / ".geneagent" / "knowledge" / "raw_pdfs" / "open.pdf").exists()


def test_fetcher_rejects_git_versioned_references_root(tmp_path: Path) -> None:
    references_root = tmp_path / "references"
    references_root.mkdir()

    with pytest.raises(ValueError, match="must not point inside references"):
        KnowledgeSourceFetcher(references_root)
