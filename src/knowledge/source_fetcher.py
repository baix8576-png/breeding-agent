"""Safe local source fetcher for GeneAgent knowledge ingestion."""

from __future__ import annotations

import hashlib
import json
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Any

_ALLOWED_ACCESS = {"open_access", "public_document"}


@dataclass(frozen=True)
class SourceFetchEntry:
    """One source-fetch status row written to the local fetch report."""

    doc_id: str
    module_id: str
    title: str
    url: str
    output_name: str
    status: str
    reason: str
    destination: str | None = None
    sha256: str | None = None


@dataclass(frozen=True)
class SourceFetchReport:
    """Fetch report for a manifest run."""

    entries: list[SourceFetchEntry]
    report_path: str | None


class KnowledgeSourceFetcher:
    """Fetch open/public knowledge source files into the ignored local runtime layer."""

    def __init__(
        self,
        local_knowledge_root: Path | str = Path(".geneagent") / "knowledge",
        *,
        downloader: Callable[[str], bytes] | None = None,
    ) -> None:
        self.local_knowledge_root = Path(local_knowledge_root)
        if _points_inside_references(self.local_knowledge_root):
            raise ValueError("local_knowledge_root must not point inside references")
        self._downloader = downloader or _default_downloader

    def fetch_manifest(self, manifest_path: Path | str) -> SourceFetchReport:
        """Download allowed manifest entries and write a JSONL status report."""

        manifest = _load_manifest(Path(manifest_path))
        entries: list[SourceFetchEntry] = []
        for raw_item in manifest:
            item = _normalize_manifest_item(raw_item)
            entries.append(self._fetch_item(item))

        report_path = self._write_report(Path(manifest_path), entries)
        return SourceFetchReport(entries=entries, report_path=str(report_path))

    def _fetch_item(self, item: dict[str, str]) -> SourceFetchEntry:
        base = {
            "doc_id": item["doc_id"],
            "module_id": item["module_id"],
            "title": item["title"],
            "url": item["url"],
            "output_name": item["output_name"],
        }
        access = item["access"]
        if access not in _ALLOWED_ACCESS:
            return SourceFetchEntry(
                **base,
                status="skipped",
                reason=f"access_not_allowed:{access}",
            )

        if not _safe_output_name(item["output_name"]):
            return SourceFetchEntry(**base, status="failed", reason="unsafe_output_name")

        destination = self._destination_for(item["output_name"])
        if destination is None:
            return SourceFetchEntry(**base, status="failed", reason="destination_outside_knowledge_root")
        if destination.exists():
            return SourceFetchEntry(
                **base,
                status="skipped",
                reason="destination_exists",
                destination=str(destination),
            )

        try:
            payload = self._downloader(item["url"])
        except Exception as exc:  # pragma: no cover - exact network error type is environment-dependent
            return SourceFetchEntry(
                **base,
                status="failed",
                reason=f"download_error:{exc.__class__.__name__}",
                destination=str(destination),
            )

        sha256 = hashlib.sha256(payload).hexdigest()
        expected_sha256 = item.get("expected_sha256", "")
        if expected_sha256 and sha256.lower() != expected_sha256.lower():
            return SourceFetchEntry(
                **base,
                status="failed",
                reason="checksum_mismatch",
                destination=str(destination),
                sha256=sha256,
            )

        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(payload)
        return SourceFetchEntry(
            **base,
            status="downloaded",
            reason="ok",
            destination=str(destination),
            sha256=sha256,
        )

    def _destination_for(self, output_name: str) -> Path | None:
        subdir = "raw_pdfs" if output_name.lower().endswith(".pdf") else "source_docs"
        root = self.local_knowledge_root.resolve()
        destination = (root / subdir / output_name).resolve()
        if not _is_relative_to(destination, root):
            return None
        return destination

    def _write_report(self, manifest_path: Path, entries: list[SourceFetchEntry]) -> Path:
        report_dir = self.local_knowledge_root / "fetch_reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        report_path = report_dir / f"{manifest_path.stem}.jsonl"
        lines = [json.dumps(asdict(entry), sort_keys=True) for entry in entries]
        report_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
        return report_path


def _load_manifest(manifest_path: Path) -> list[dict[str, Any]]:
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and isinstance(data.get("sources"), list):
        return data["sources"]
    raise ValueError("source fetch manifest must be a list or an object with a sources list")


def _normalize_manifest_item(raw_item: dict[str, Any]) -> dict[str, str]:
    required_fields = ("doc_id", "module_id", "title", "url", "output_name", "access")
    normalized: dict[str, str] = {}
    for field in required_fields:
        value = str(raw_item.get(field, "")).strip()
        if not value:
            raise ValueError(f"source fetch manifest item missing {field}")
        normalized[field] = value
    expected_sha256 = str(raw_item.get("expected_sha256", "")).strip()
    if expected_sha256:
        normalized["expected_sha256"] = expected_sha256
    return normalized


def _safe_output_name(output_name: str) -> bool:
    if output_name in {"", ".", ".."}:
        return False
    if any(separator in output_name for separator in ("/", "\\")):
        return False
    if ":" in output_name:
        return False
    return output_name == Path(output_name).name


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _points_inside_references(path: Path) -> bool:
    return "references" in {part.lower() for part in path.parts}


def _default_downloader(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=30) as response:
        return response.read()
