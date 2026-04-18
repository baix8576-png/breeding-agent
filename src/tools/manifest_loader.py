"""File-based tool manifest loader with schema validation and fallback control."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from tools.manifest_schema import ToolManifest, ToolManifestCatalog

MAX_MANIFEST_FILE_SIZE_BYTES = 256 * 1024


class ManifestLoadIssue(BaseModel):
    """Structured loader issue used for debugging and gate decisions."""

    model_config = ConfigDict(extra="forbid")

    level: str
    code: str
    message: str
    path: str | None = None
    tool_name: str | None = None


class ManifestLoadResult(BaseModel):
    """Result payload returned by the loader and registry bootstrap."""

    model_config = ConfigDict(extra="forbid")

    manifests: list[ToolManifest] = Field(default_factory=list)
    loaded_files: list[str] = Field(default_factory=list)
    issues: list[ManifestLoadIssue] = Field(default_factory=list)
    source: str = "builtin"
    used_fallback: bool = False


class ToolManifestLoadError(RuntimeError):
    """Raised when strict loading is enabled and the file source is invalid."""

    def __init__(self, message: str, *, issues: list[ManifestLoadIssue] | None = None) -> None:
        super().__init__(message)
        self.issues = issues or []


def default_manifests_dir() -> Path:
    """Return the default file-system source for tool manifests."""

    return Path(__file__).resolve().parent / "manifests"


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def discover_manifest_files(manifests_dir: Path) -> list[Path]:
    """Discover manifest JSON files under the manifest root."""

    if not manifests_dir.exists():
        return []
    root = manifests_dir.resolve()
    files: list[Path] = []
    for path in sorted(manifests_dir.rglob("*.json")):
        if not path.is_file():
            continue
        resolved = path.resolve()
        if not _is_relative_to(resolved, root):
            raise ValueError(f"manifest path escapes manifest root: {path}")
        size_bytes = resolved.stat().st_size
        if size_bytes > MAX_MANIFEST_FILE_SIZE_BYTES:
            raise ValueError(f"manifest file too large: {path}")
        files.append(resolved)
    return files


def parse_manifest_file(path: Path) -> list[ToolManifest]:
    """Parse one manifest file into validated manifest models."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and "manifests" in payload:
        catalog = ToolManifestCatalog.model_validate(payload)
        return list(catalog.manifests)
    if isinstance(payload, dict):
        return [ToolManifest.model_validate(payload)]
    if isinstance(payload, list):
        manifests = [ToolManifest.model_validate(item) for item in payload]
        if not manifests:
            raise ValueError("manifest list cannot be empty")
        return manifests
    raise ValueError("manifest file must contain an object, catalog, or list of manifests")


def _copy_manifests(manifests: Iterable[ToolManifest]) -> list[ToolManifest]:
    return [manifest.model_copy(deep=True) for manifest in manifests]


def load_tool_manifests(
    *,
    manifests_dir: Path,
    builtin_manifests: list[ToolManifest],
    strict: bool = False,
    allow_fallback: bool = True,
) -> ManifestLoadResult:
    """Load manifests from files, with optional strict failure or builtin fallback."""

    issues: list[ManifestLoadIssue] = []
    loaded_files: list[str] = []
    parsed_manifests: list[ToolManifest] = []
    has_errors = False
    try:
        manifest_files = discover_manifest_files(manifests_dir)
    except (OSError, ValueError) as exc:
        manifest_files = []
        has_errors = True
        issues.append(
            ManifestLoadIssue(
                level="error",
                code="DISCOVERY_FAILED",
                message=str(exc),
                path=str(manifests_dir),
            )
        )

    if not manifest_files:
        issues.append(
            ManifestLoadIssue(
                level="warning",
                code="NO_MANIFEST_FILES",
                message="No file-based manifests were found; fallback to legacy defaults.",
                path=str(manifests_dir),
            )
        )

    for manifest_file in manifest_files:
        loaded_files.append(str(manifest_file))
        try:
            parsed_manifests.extend(parse_manifest_file(manifest_file))
        except (OSError, json.JSONDecodeError, ValidationError, ValueError) as exc:
            has_errors = True
            issues.append(
                ManifestLoadIssue(
                    level="error",
                    code="PARSE_OR_VALIDATION_FAILED",
                    message=str(exc),
                    path=str(manifest_file),
                )
            )

    names_seen: dict[str, str] = {}
    for manifest in parsed_manifests:
        previous = names_seen.get(manifest.name)
        if previous is None:
            names_seen[manifest.name] = manifest.name
            continue
        has_errors = True
        issues.append(
            ManifestLoadIssue(
                level="error",
                code="DUPLICATED_MANIFEST_NAME",
                message=f"Manifest `{manifest.name}` is defined multiple times.",
                tool_name=manifest.name,
            )
        )

    if has_errors or not parsed_manifests:
        if strict:
            raise ToolManifestLoadError(
                "Strict tool manifest loading failed.",
                issues=issues,
            )
        if allow_fallback:
            return ManifestLoadResult(
                manifests=_copy_manifests(builtin_manifests),
                loaded_files=loaded_files,
                issues=issues,
                source="builtin",
                used_fallback=True,
            )
        return ManifestLoadResult(
            manifests=[],
            loaded_files=loaded_files,
            issues=issues,
            source="file",
            used_fallback=False,
        )

    return ManifestLoadResult(
        manifests=_copy_manifests(parsed_manifests),
        loaded_files=loaded_files,
        issues=issues,
        source="file",
        used_fallback=False,
    )
