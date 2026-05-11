"""Payload policies for cloud-safe text exchange."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence

from pydantic import BaseModel, Field


class CloudPayloadReview(BaseModel):
    sanitized_payload: dict[str, object] = Field(default_factory=dict)
    dropped_fields: list[str] = Field(default_factory=list)
    redacted_fields: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    allowed: bool = True
    violation_reasons: list[str] = Field(default_factory=list)
    allowed_fields: list[str] = Field(default_factory=list)


class CloudPayloadPolicy:
    """Strict allow-list and redaction rules for cloud-bound text payloads."""

    def __init__(
        self,
        *,
        allowed_fields: set[str] | list[str] | tuple[str, ...] | None = None,
        blocked_field_fragments: set[str] | list[str] | tuple[str, ...] | None = None,
    ) -> None:
        default_allowed = {
            "prompt",
            "sanitized_error_log",
            "tool_summary",
            "software_version",
            "parameter_schema",
        }
        default_blocked_fragments = {
            "vcf",
            "bam",
            "fastq",
            "fasta",
            "sample_name",
            "sample_names",
            "file_content",
            "raw_content",
            "raw_path",
            "path_mapping",
            "token",
            "secret",
            "password",
            "api_key",
        }
        self.allowed_fields = {
            str(item).strip().lower()
            for item in (allowed_fields or default_allowed)
            if str(item).strip()
        }
        self.blocked_field_fragments = {
            str(item).strip().lower()
            for item in (blocked_field_fragments or default_blocked_fragments)
            if str(item).strip()
        }

    _windows_path = re.compile(r"(?<!\w)(?:[A-Za-z]:\\|\\\\)[^\s\"'<>]+")
    _posix_path = re.compile(r"(?<![:\w])(?:/[^/\s\"'<>]+)+")
    _home_path = re.compile(r"(?<!\w)~(?:/[^/\s\"'<>]+)+")

    def can_send_field(self, field_name: str) -> bool:
        """Return whether a field is inside the explicit cloud allow-list."""

        return field_name.strip().lower() in self.allowed_fields

    def redact_paths(self, text: str) -> str:
        """Mask Windows, POSIX, and home-relative paths before cloud exchange."""

        sanitized = self._windows_path.sub("[REDACTED_PATH]", text)
        sanitized = self._posix_path.sub("[REDACTED_PATH]", sanitized)
        sanitized = self._home_path.sub("[REDACTED_PATH]", sanitized)
        return sanitized

    def sanitize_text(self, text: str) -> str:
        """Apply text-only sanitization rules for cloud-bound content."""

        return self.redact_paths(text)

    def review_payload(self, payload: Mapping[str, object]) -> CloudPayloadReview:
        """Drop non-allow-listed fields and redact path-like content from the rest."""

        sanitized_payload: dict[str, object] = {}
        dropped_fields: list[str] = []
        redacted_fields: list[str] = []
        warnings: list[str] = []
        violation_reasons: list[str] = []

        for original_name, value in payload.items():
            field_name = str(original_name).strip().lower()
            if any(fragment in field_name for fragment in self.blocked_field_fragments):
                dropped_fields.append(str(original_name))
                reason = f"Field '{original_name}' was dropped because it matches a protected-content pattern."
                warnings.append(reason)
                violation_reasons.append(reason)
                continue
            if not self.can_send_field(field_name):
                dropped_fields.append(str(original_name))
                reason = f"Field '{original_name}' is outside the approved cloud payload boundary."
                warnings.append(reason)
                violation_reasons.append(reason)
                continue

            sanitized_value, changed = self._sanitize_value(value)
            sanitized_payload[field_name] = sanitized_value
            if changed:
                redacted_fields.append(str(original_name))

        allowed = not violation_reasons
        return CloudPayloadReview(
            sanitized_payload=sanitized_payload,
            dropped_fields=dropped_fields,
            redacted_fields=redacted_fields,
            warnings=warnings,
            allowed=allowed,
            violation_reasons=violation_reasons,
            allowed_fields=sorted(self.allowed_fields),
        )

    def _sanitize_value(self, value: object) -> tuple[object, bool]:
        if isinstance(value, str):
            sanitized = self.sanitize_text(value)
            return sanitized, sanitized != value
        if isinstance(value, Mapping):
            changed = False
            sanitized_mapping: dict[str, object] = {}
            for key, nested_value in value.items():
                sanitized_value, nested_changed = self._sanitize_value(nested_value)
                sanitized_mapping[str(key)] = sanitized_value
                changed = changed or nested_changed
            return sanitized_mapping, changed
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            changed = False
            sanitized_items: list[object] = []
            for item in value:
                sanitized_item, nested_changed = self._sanitize_value(item)
                sanitized_items.append(sanitized_item)
                changed = changed or nested_changed
            return sanitized_items, changed
        return value, False
