"""Tool registry entrypoint with file-based manifest loading."""

from __future__ import annotations

from pathlib import Path

from contracts.common import TaskDomain
from tools.manifest_legacy import legacy_default_manifests
from tools.manifest_loader import (
    ManifestLoadResult,
    default_manifests_dir,
    load_tool_manifests,
)
from tools.manifest_schema import ToolManifest


class ToolRegistry:
    """In-memory registry for tool manifests."""

    def __init__(
        self,
        *,
        manifests_dir: Path | None = None,
        strict_manifest_validation: bool = False,
    ) -> None:
        self._items: dict[str, ToolManifest] = {}
        self._manifests_dir = manifests_dir
        self._strict_manifest_validation = strict_manifest_validation
        self._last_load_result: ManifestLoadResult | None = None

    def register(self, manifest: ToolManifest) -> None:
        self._items[manifest.name] = manifest

    def register_many(self, manifests: list[ToolManifest]) -> None:
        for manifest in manifests:
            self.register(manifest)

    @property
    def last_load_result(self) -> ManifestLoadResult | None:
        return self._last_load_result

    def bootstrap_defaults(self) -> ManifestLoadResult:
        """Load default manifests from file source with legacy fallback."""

        if self._items:
            if self._last_load_result is not None:
                return self._last_load_result
            return ManifestLoadResult(
                manifests=[manifest.model_copy(deep=True) for manifest in self._items.values()],
                source="in_memory",
                used_fallback=False,
            )

        result = load_tool_manifests(
            manifests_dir=self._manifests_dir or default_manifests_dir(),
            builtin_manifests=legacy_default_manifests(),
            strict=self._strict_manifest_validation,
            allow_fallback=True,
        )
        self.register_many(result.manifests)
        self._last_load_result = result
        return result

    def get(self, name: str) -> ToolManifest | None:
        return self._items.get(name)

    def list_names(self) -> list[str]:
        return sorted(self._items)

    def list_for_stage(self, stage_id: str, domain: TaskDomain) -> list[ToolManifest]:
        """Return manifests applicable to the given stage and domain."""

        domain_key = domain.value
        manifests = [
            manifest
            for manifest in self._items.values()
            if (not manifest.stage_scope or stage_id in manifest.stage_scope)
            and (
                not manifest.domain_scope
                or "shared" in manifest.domain_scope
                or domain_key in manifest.domain_scope
            )
        ]
        manifests.sort(key=lambda item: item.name)
        return manifests
