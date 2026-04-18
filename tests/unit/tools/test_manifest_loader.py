from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.manifest_legacy import legacy_default_manifests
from tools.manifest_loader import ToolManifestLoadError, load_tool_manifests


def _manifest_payload(name: str) -> dict[str, object]:
    return {
        "schema_version": "1.0.0",
        "manifest_version": "1.0.0",
        "name": name,
        "description": f"{name} description",
        "category": "workflow",
        "inputs": ["request"],
        "outputs": ["result"],
        "preconditions": ["request available"],
        "resource_requirements": ["cpu:1"],
        "error_codes": ["GENERIC_FAILURE"],
        "supports_dry_run": True,
        "stage_scope": ["stage_01_intake"],
        "domain_scope": ["shared", "knowledge"],
    }


def _write_catalog(path: Path, manifests: list[dict[str, object]]) -> None:
    payload = {"schema_version": "1.0.0", "manifests": manifests}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_loader_loads_valid_manifests_from_directory(tmp_path: Path) -> None:
    manifests_dir = tmp_path / "manifests"
    manifests_dir.mkdir(parents=True, exist_ok=True)
    _write_catalog(
        manifests_dir / "catalog.v1.json",
        [_manifest_payload("unit_loader_a"), _manifest_payload("unit_loader_b")],
    )

    result = load_tool_manifests(
        manifests_dir=manifests_dir,
        builtin_manifests=legacy_default_manifests(),
    )

    assert result.source == "file"
    assert result.used_fallback is False
    assert sorted(item.name for item in result.manifests) == ["unit_loader_a", "unit_loader_b"]


def test_loader_rejects_duplicate_manifest_name_across_files(tmp_path: Path) -> None:
    manifests_dir = tmp_path / "manifests"
    manifests_dir.mkdir(parents=True, exist_ok=True)
    _write_catalog(manifests_dir / "a.json", [_manifest_payload("duplicated_tool")])
    _write_catalog(manifests_dir / "b.json", [_manifest_payload("duplicated_tool")])

    with pytest.raises(ToolManifestLoadError):
        load_tool_manifests(
            manifests_dir=manifests_dir,
            builtin_manifests=legacy_default_manifests(),
            strict=True,
        )


def test_loader_non_strict_fallbacks_to_builtin_when_file_invalid(tmp_path: Path) -> None:
    manifests_dir = tmp_path / "manifests"
    manifests_dir.mkdir(parents=True, exist_ok=True)
    (manifests_dir / "broken.json").write_text("{not valid json", encoding="utf-8")

    result = load_tool_manifests(
        manifests_dir=manifests_dir,
        builtin_manifests=legacy_default_manifests(),
        strict=False,
    )

    assert result.source == "builtin"
    assert result.used_fallback is True
    assert "input_contract_reader" in {item.name for item in result.manifests}
    assert any(issue.code == "PARSE_OR_VALIDATION_FAILED" for issue in result.issues)


def test_loader_strict_mode_raises_without_fallback(tmp_path: Path) -> None:
    manifests_dir = tmp_path / "manifests"
    manifests_dir.mkdir(parents=True, exist_ok=True)
    (manifests_dir / "broken.json").write_text("{not valid json", encoding="utf-8")

    with pytest.raises(ToolManifestLoadError):
        load_tool_manifests(
            manifests_dir=manifests_dir,
            builtin_manifests=legacy_default_manifests(),
            strict=True,
        )


def test_loader_is_atomic_on_error(tmp_path: Path) -> None:
    manifests_dir = tmp_path / "manifests"
    manifests_dir.mkdir(parents=True, exist_ok=True)
    _write_catalog(manifests_dir / "valid.json", [_manifest_payload("unit_loader_only_in_file")])
    (manifests_dir / "broken.json").write_text("{not valid json", encoding="utf-8")

    result = load_tool_manifests(
        manifests_dir=manifests_dir,
        builtin_manifests=legacy_default_manifests(),
        strict=False,
    )

    assert result.source == "builtin"
    assert result.used_fallback is True
    loaded_names = {item.name for item in result.manifests}
    assert "unit_loader_only_in_file" not in loaded_names
    assert "input_contract_reader" in loaded_names
