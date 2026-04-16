"""Input validation helpers for genetics workflow execution."""

from __future__ import annotations

from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field

from contracts.validation import (
    ConsistencyCheck,
    ConsistencyStatus,
    NormalizedInputEntry,
    ValidationIssue,
    ValidationReport,
    ValidationSeverity,
)


class InputDataType(str, Enum):
    """Supported local input data types for the genetics MVP."""

    VCF = "vcf"
    PLINK_BED = "plink_bed"
    PLINK_BIM = "plink_bim"
    PLINK_FAM = "plink_fam"
    PHENOTYPE_TABLE = "phenotype_table"
    COVARIATE_TABLE = "covariate_table"
    PEDIGREE_TABLE = "pedigree_table"
    BAM = "bam"
    FASTA = "fasta"
    TEXT_TABLE = "text_table"


class InputBundleEntry(BaseModel):
    """Single dataset entry passed into the local validator."""

    role: str
    path: str
    data_type: InputDataType | None = None
    required: bool = True
    description: str | None = None
    original_path: str | None = None
    normalized_path: str | None = None


class InputBundle(BaseModel):
    """Grouped dataset description used during local validation."""

    task_id: str | None = None
    run_id: str | None = None
    species: str | None = None
    cohort_name: str | None = None
    entries: list[InputBundleEntry] = Field(default_factory=list)


class PipelineValidationIssue(BaseModel):
    """Detailed validation issue used only inside the pipeline layer."""

    code: str
    message: str
    path: str | None = None
    severity: ValidationSeverity = ValidationSeverity.ERROR
    blocking: bool = True
    hint: str | None = None


class PipelineFileCheck(BaseModel):
    """Per-file validation summary for a local genetics input."""

    role: str
    path: str
    exists: bool
    required: bool = True
    inferred_type: InputDataType | None = None
    suffix: str | None = None
    companion_paths: list[str] = Field(default_factory=list)
    issues: list[PipelineValidationIssue] = Field(default_factory=list)


class PipelineValidationSnapshot(BaseModel):
    """Detailed validation result retained inside the genetics pipeline layer."""

    task_id: str | None = None
    run_id: str | None = None
    bundle: InputBundle = Field(default_factory=InputBundle)
    files: list[PipelineFileCheck] = Field(default_factory=list)
    issues: list[PipelineValidationIssue] = Field(default_factory=list)
    genotype_inputs_present: bool = False
    detected_types: list[InputDataType] = Field(default_factory=list)
    consistency_checks: list[ConsistencyCheck] = Field(default_factory=list)
    ready_for_gate: str = "validation_pending"
    recommended_next_actions: list[str] = Field(default_factory=list)

    def to_contract_report(self) -> ValidationReport:
        """Collapse pipeline-local detail into the shared validation contract."""

        blocking_issue_count = sum(1 for issue in self.issues if issue.blocking)
        return ValidationReport(
            valid=blocking_issue_count == 0,
            issues=[
                ValidationIssue(
                    code=issue.code,
                    message=issue.message,
                    path=issue.path,
                    severity=issue.severity,
                    blocking=issue.blocking,
                    hint=issue.hint,
                )
                for issue in self.issues
            ],
            normalized_inputs=[
                NormalizedInputEntry(
                    role=file_result.role,
                    original_path=original_path,
                    normalized_path=file_result.path,
                    data_type=file_result.inferred_type.value if file_result.inferred_type is not None else None,
                    required=file_result.required,
                    exists=file_result.exists,
                )
                for file_result, original_path in self._zip_file_and_original_paths()
            ],
            detected_types=[detected.value for detected in self.detected_types],
            consistency_checks=self.consistency_checks,
            ready_for_gate=self.ready_for_gate,
            recommended_next_actions=self.recommended_next_actions,
        )

    def _zip_file_and_original_paths(self) -> list[tuple[PipelineFileCheck, str]]:
        original_by_normalized = {
            (entry.normalized_path or entry.path): (entry.original_path or entry.path)
            for entry in self.bundle.entries
        }
        return [
            (file_result, original_by_normalized.get(file_result.path, file_result.path))
            for file_result in self.files
        ]


class InputValidator:
    """Conservative validator for local genetics datasets and sidecar files."""

    supported_suffixes = {
        ".vcf",
        ".vcf.gz",
        ".bam",
        ".bed",
        ".bim",
        ".fam",
        ".txt",
        ".csv",
        ".tsv",
        ".fa",
        ".fasta",
        ".fna",
    }
    genotype_types = {
        InputDataType.VCF,
        InputDataType.PLINK_BED,
        InputDataType.PLINK_BIM,
        InputDataType.PLINK_FAM,
        InputDataType.BAM,
    }

    def validate(
        self,
        inputs: InputBundle | dict[str, object] | list[str] | list[InputBundleEntry] | list[dict[str, object]],
    ) -> ValidationReport:
        """Validate local input paths and return the frozen shared contract."""

        return self.inspect(inputs).to_contract_report()

    def inspect(
        self,
        inputs: InputBundle | dict[str, object] | list[str] | list[InputBundleEntry] | list[dict[str, object]],
    ) -> PipelineValidationSnapshot:
        """Return a detailed pipeline-local validation snapshot."""

        bundle = self._normalize_inputs(inputs)
        file_results: list[PipelineFileCheck] = []
        issues: list[PipelineValidationIssue] = []
        seen_paths: set[str] = set()

        if not bundle.entries:
            issues.append(
                PipelineValidationIssue(
                    code="no_inputs_provided",
                    message="At least one local dataset path is required before a pipeline can be drafted.",
                    severity=ValidationSeverity.ERROR,
                    blocking=True,
                )
            )

        for entry in bundle.entries:
            path = Path(entry.path)
            inferred_type = entry.data_type or self._infer_type(path)
            companion_paths = self._companion_paths(path, inferred_type)
            file_issues: list[PipelineValidationIssue] = []

            if entry.path in seen_paths:
                file_issues.append(
                    PipelineValidationIssue(
                        code="duplicate_input",
                        message="The same normalized input path was supplied more than once.",
                        path=entry.path,
                        severity=ValidationSeverity.WARNING,
                        blocking=False,
                        hint="Deduplicate repeated dataset entries before generating shell wrappers.",
                    )
                )
            seen_paths.add(entry.path)

            if not path.exists():
                file_issues.append(
                    PipelineValidationIssue(
                        code="missing_path",
                        message="Input path does not exist in the current filesystem context.",
                        path=str(path),
                        severity=ValidationSeverity.ERROR,
                        blocking=entry.required,
                    )
                )
            elif not path.is_file():
                file_issues.append(
                    PipelineValidationIssue(
                        code="unsupported_path_kind",
                        message="Input path exists but is not a regular file.",
                        path=str(path),
                        severity=ValidationSeverity.ERROR,
                        blocking=entry.required,
                        hint="Provide a concrete file path instead of a directory placeholder.",
                    )
                )
            elif not self._is_supported_suffix(path):
                file_issues.append(
                    PipelineValidationIssue(
                        code="unsupported_suffix",
                        message="File suffix is not in the first-pass supported list.",
                        path=str(path),
                        severity=ValidationSeverity.ERROR,
                        blocking=entry.required,
                        hint="Supported MVP inputs include VCF, PLINK trio files, BAM, FASTA, and tabular metadata.",
                    )
                )
            elif inferred_type is None:
                file_issues.append(
                    PipelineValidationIssue(
                        code="unrecognized_input_type",
                        message="The validator could not infer a supported input data type.",
                        path=str(path),
                        severity=ValidationSeverity.ERROR,
                        blocking=entry.required,
                    )
                )

            if path.exists() and path.is_file() and inferred_type in {
                InputDataType.PLINK_BED,
                InputDataType.PLINK_BIM,
                InputDataType.PLINK_FAM,
            }:
                missing_companions = [companion_path for companion_path in companion_paths if not Path(companion_path).exists()]
                if missing_companions:
                    file_issues.append(
                        PipelineValidationIssue(
                            code="plink_trio_incomplete",
                            message="PLINK binary inputs require matching .bed/.bim/.fam companion files.",
                            path=str(path),
                            severity=ValidationSeverity.ERROR,
                            blocking=True,
                            hint=f"Missing companions: {', '.join(missing_companions)}",
                        )
                    )

            file_results.append(
                PipelineFileCheck(
                    role=entry.role,
                    path=entry.path,
                    exists=path.exists(),
                    required=entry.required,
                    inferred_type=inferred_type,
                    suffix=self._combined_suffix(path) or path.suffix or None,
                    companion_paths=companion_paths,
                    issues=file_issues,
                )
            )
            issues.extend(file_issues)

        detected_types = self._collect_detected_types(file_results)
        genotype_inputs_present = any(input_type in self.genotype_types for input_type in detected_types)
        if bundle.entries and not genotype_inputs_present:
            issues.append(
                PipelineValidationIssue(
                    code="missing_genotype_dataset",
                    message="No genotype-bearing dataset was detected among the supplied inputs.",
                    severity=ValidationSeverity.ERROR,
                    blocking=True,
                    hint="Provide at least one VCF, PLINK trio, or BAM file before drafting genetics workflows.",
                )
            )

        consistency_checks = self._consistency_checks(
            bundle=bundle,
            file_results=file_results,
            genotype_inputs_present=genotype_inputs_present,
        )
        for check in consistency_checks:
            if check.status == ConsistencyStatus.FAIL:
                issues.append(
                    PipelineValidationIssue(
                        code=f"consistency_{check.check_id}",
                        message=check.message,
                        severity=ValidationSeverity.ERROR,
                        blocking=True,
                    )
                )
            elif check.status == ConsistencyStatus.WARN:
                issues.append(
                    PipelineValidationIssue(
                        code=f"consistency_{check.check_id}",
                        message=check.message,
                        severity=ValidationSeverity.WARNING,
                        blocking=False,
                    )
                )

        blocking_issue_count = sum(1 for issue in issues if issue.blocking)
        return PipelineValidationSnapshot(
            task_id=bundle.task_id,
            run_id=bundle.run_id,
            bundle=bundle,
            files=file_results,
            issues=issues,
            genotype_inputs_present=genotype_inputs_present,
            detected_types=detected_types,
            consistency_checks=consistency_checks,
            ready_for_gate="ready_for_design" if blocking_issue_count == 0 else "blocked_by_validation",
            recommended_next_actions=self._recommended_next_actions(
                bundle=bundle,
                valid=blocking_issue_count == 0,
                issues=issues,
            ),
        )

    def _normalize_inputs(
        self,
        inputs: InputBundle | dict[str, object] | list[str] | list[InputBundleEntry] | list[dict[str, object]],
    ) -> InputBundle:
        if isinstance(inputs, InputBundle):
            raw_bundle = inputs
        elif isinstance(inputs, dict):
            raw_bundle = InputBundle.model_validate(inputs)
        else:
            entries: list[InputBundleEntry] = []
            for index, raw_entry in enumerate(inputs):
                if isinstance(raw_entry, InputBundleEntry):
                    entries.append(raw_entry)
                    continue
                if isinstance(raw_entry, dict):
                    entries.append(InputBundleEntry.model_validate(raw_entry))
                    continue
                entries.append(InputBundleEntry(role=f"input_{index + 1}", path=str(raw_entry)))
            raw_bundle = InputBundle(entries=entries)

        normalized_entries = [self._normalize_entry(index=index, entry=entry) for index, entry in enumerate(raw_bundle.entries)]
        return raw_bundle.model_copy(update={"entries": normalized_entries})

    def _normalize_entry(self, *, index: int, entry: InputBundleEntry) -> InputBundleEntry:
        original_path = entry.original_path or entry.path
        normalized_path = self._normalize_path(entry.path)
        inferred_type = entry.data_type or self._infer_type(Path(normalized_path))
        role = self._normalize_role(entry.role, inferred_type, index)
        return entry.model_copy(
            update={
                "role": role,
                "path": normalized_path,
                "data_type": inferred_type,
                "original_path": original_path,
                "normalized_path": normalized_path,
            }
        )

    def _normalize_path(self, raw_path: str) -> str:
        candidate = Path(raw_path).expanduser()
        try:
            return str(candidate.resolve(strict=False))
        except OSError:
            return str(candidate)

    def _normalize_role(self, role: str, inferred_type: InputDataType | None, index: int) -> str:
        normalized = role.strip().lower().replace(" ", "_").replace("-", "_")
        role_aliases = {
            "表型": "phenotype_table",
            "协变量": "covariate_table",
            "谱系": "pedigree_table",
            "pedigree": "pedigree_table",
            "phenotype": "phenotype_table",
            "covariate": "covariate_table",
        }
        normalized = role_aliases.get(normalized, normalized)
        if normalized and normalized != f"input_{index + 1}":
            return normalized
        if inferred_type is None:
            return f"input_{index + 1}"
        fallback_by_type = {
            InputDataType.VCF: "vcf",
            InputDataType.PLINK_BED: "plink_bed",
            InputDataType.PLINK_BIM: "plink_bim",
            InputDataType.PLINK_FAM: "plink_fam",
            InputDataType.BAM: "bam",
            InputDataType.PHENOTYPE_TABLE: "phenotype_table",
            InputDataType.COVARIATE_TABLE: "covariate_table",
            InputDataType.PEDIGREE_TABLE: "pedigree_table",
            InputDataType.FASTA: "fasta",
            InputDataType.TEXT_TABLE: f"table_{index + 1}",
        }
        return fallback_by_type.get(inferred_type, f"input_{index + 1}")

    def _consistency_checks(
        self,
        *,
        bundle: InputBundle,
        file_results: list[PipelineFileCheck],
        genotype_inputs_present: bool,
    ) -> list[ConsistencyCheck]:
        checks: list[ConsistencyCheck] = []
        existing = [result for result in file_results if result.exists]
        detected_types = {result.inferred_type for result in existing if result.inferred_type is not None}

        checks.append(
            ConsistencyCheck(
                check_id="genotype_presence",
                status=ConsistencyStatus.PASS if genotype_inputs_present else ConsistencyStatus.FAIL,
                message=(
                    "At least one genotype-bearing input is present."
                    if genotype_inputs_present
                    else "No genotype-bearing input detected (expected one of VCF/PLINK/BAM)."
                ),
                related_roles=[result.role for result in existing if result.inferred_type in self.genotype_types],
                related_paths=[result.path for result in existing if result.inferred_type in self.genotype_types],
            )
        )

        modalities = self._genotype_modalities(detected_types)
        if len(modalities) <= 1:
            modality_status = ConsistencyStatus.PASS
            modality_message = "Genotype modality is consistent within one primary source family."
        else:
            modality_status = ConsistencyStatus.WARN
            modality_message = (
                "Multiple genotype source families detected across VCF/PLINK/BAM; "
                "confirm which one is the canonical analysis backbone."
            )
        checks.append(
            ConsistencyCheck(
                check_id="genotype_modality",
                status=modality_status,
                message=modality_message,
                related_roles=[result.role for result in existing if result.inferred_type in self.genotype_types],
                related_paths=[result.path for result in existing if result.inferred_type in self.genotype_types],
            )
        )

        plink_missing = self._plink_missing_components(existing)
        checks.append(
            ConsistencyCheck(
                check_id="plink_trio_consistency",
                status=ConsistencyStatus.PASS if not plink_missing else ConsistencyStatus.FAIL,
                message=(
                    "PLINK trio prefixes are complete."
                    if not plink_missing
                    else f"Incomplete PLINK trio detected; missing companions for prefixes: {', '.join(plink_missing)}."
                ),
                related_roles=[result.role for result in existing if result.inferred_type in {InputDataType.PLINK_BED, InputDataType.PLINK_BIM, InputDataType.PLINK_FAM}],
                related_paths=[result.path for result in existing if result.inferred_type in {InputDataType.PLINK_BED, InputDataType.PLINK_BIM, InputDataType.PLINK_FAM}],
            )
        )

        has_phenotype = any(result.inferred_type == InputDataType.PHENOTYPE_TABLE for result in existing)
        has_covariate = any(result.inferred_type == InputDataType.COVARIATE_TABLE for result in existing)
        has_pedigree = any(result.inferred_type == InputDataType.PEDIGREE_TABLE for result in existing)
        metadata_present = has_phenotype or has_covariate or has_pedigree
        metadata_roles = [result.role for result in existing if result.inferred_type in {InputDataType.PHENOTYPE_TABLE, InputDataType.COVARIATE_TABLE, InputDataType.PEDIGREE_TABLE}]
        metadata_paths = [result.path for result in existing if result.inferred_type in {InputDataType.PHENOTYPE_TABLE, InputDataType.COVARIATE_TABLE, InputDataType.PEDIGREE_TABLE}]

        metadata_status = ConsistencyStatus.PASS
        metadata_message = "Metadata tables and genotype backbone are structurally compatible."
        if metadata_present and not genotype_inputs_present:
            metadata_status = ConsistencyStatus.FAIL
            metadata_message = "Phenotype/covariate/pedigree tables were provided without a genotype backbone."
        checks.append(
            ConsistencyCheck(
                check_id="metadata_requires_genotype",
                status=metadata_status,
                message=metadata_message,
                related_roles=metadata_roles,
                related_paths=metadata_paths,
            )
        )

        covariate_status = ConsistencyStatus.PASS
        covariate_message = "Covariate and pedigree sidecars are aligned with phenotype table prerequisites."
        if (has_covariate or has_pedigree) and not has_phenotype:
            covariate_status = ConsistencyStatus.WARN
            covariate_message = (
                "Covariate or pedigree table detected without phenotype table; "
                "genomic_prediction blueprint usually expects phenotype + genotype alignment."
            )
        checks.append(
            ConsistencyCheck(
                check_id="phenotype_alignment_prerequisite",
                status=covariate_status,
                message=covariate_message,
                related_roles=metadata_roles,
                related_paths=metadata_paths,
            )
        )

        if bundle.species is None:
            checks.append(
                ConsistencyCheck(
                    check_id="species_metadata",
                    status=ConsistencyStatus.WARN,
                    message="Species metadata is missing; provide species for downstream SOP and reporting context.",
                )
            )
        else:
            checks.append(
                ConsistencyCheck(
                    check_id="species_metadata",
                    status=ConsistencyStatus.PASS,
                    message="Species metadata is present in the InputBundle.",
                )
            )

        return checks

    def _genotype_modalities(self, detected_types: set[InputDataType]) -> list[str]:
        modalities: list[str] = []
        if InputDataType.VCF in detected_types:
            modalities.append("vcf")
        if any(t in detected_types for t in {InputDataType.PLINK_BED, InputDataType.PLINK_BIM, InputDataType.PLINK_FAM}):
            modalities.append("plink")
        if InputDataType.BAM in detected_types:
            modalities.append("bam")
        return modalities

    def _plink_missing_components(self, existing_results: list[PipelineFileCheck]) -> list[str]:
        prefix_map: dict[str, set[str]] = {}
        for result in existing_results:
            if result.inferred_type not in {InputDataType.PLINK_BED, InputDataType.PLINK_BIM, InputDataType.PLINK_FAM}:
                continue
            prefix = str(Path(result.path).with_suffix(""))
            ext = Path(result.path).suffix.lower()
            prefix_map.setdefault(prefix, set()).add(ext)

        missing: list[str] = []
        required = {".bed", ".bim", ".fam"}
        for prefix, observed in prefix_map.items():
            if observed != required:
                missing.append(prefix)
        return sorted(missing)

    def _is_supported_suffix(self, path: Path) -> bool:
        suffixes = {self._combined_suffix(path), path.suffix}
        return bool(self.supported_suffixes.intersection(suffixes))

    def _infer_type(self, path: Path) -> InputDataType | None:
        combined_suffix = self._combined_suffix(path)
        if combined_suffix == ".vcf.gz" or path.suffix == ".vcf":
            return InputDataType.VCF
        if path.suffix == ".bed":
            return InputDataType.PLINK_BED
        if path.suffix == ".bim":
            return InputDataType.PLINK_BIM
        if path.suffix == ".fam":
            return InputDataType.PLINK_FAM
        if path.suffix == ".bam":
            return InputDataType.BAM
        if path.suffix in {".fa", ".fasta", ".fna"}:
            return InputDataType.FASTA
        if path.suffix in {".csv", ".tsv", ".txt"}:
            lowered_name = path.name.lower()
            if "pheno" in lowered_name or "trait" in lowered_name:
                return InputDataType.PHENOTYPE_TABLE
            if "cov" in lowered_name or "pc" in lowered_name:
                return InputDataType.COVARIATE_TABLE
            if "ped" in lowered_name or "pedigree" in lowered_name:
                return InputDataType.PEDIGREE_TABLE
            return InputDataType.TEXT_TABLE
        return None

    def _companion_paths(self, path: Path, inferred_type: InputDataType | None) -> list[str]:
        if inferred_type not in {InputDataType.PLINK_BED, InputDataType.PLINK_BIM, InputDataType.PLINK_FAM}:
            return []

        prefix_path = path.with_suffix("")
        return [
            str(prefix_path.with_suffix(".bed")),
            str(prefix_path.with_suffix(".bim")),
            str(prefix_path.with_suffix(".fam")),
        ]

    def _combined_suffix(self, path: Path) -> str:
        return "".join(path.suffixes)

    def _collect_detected_types(self, file_results: list[PipelineFileCheck]) -> list[InputDataType]:
        ordered_types: list[InputDataType] = []
        for result in file_results:
            if result.inferred_type is None or result.inferred_type in ordered_types:
                continue
            ordered_types.append(result.inferred_type)
        return ordered_types

    def _recommended_next_actions(
        self,
        bundle: InputBundle,
        valid: bool,
        issues: list[PipelineValidationIssue],
    ) -> list[str]:
        if not bundle.entries:
            return [
                "Provide at least one genotype-bearing dataset path before selecting a pipeline blueprint.",
            ]
        if valid:
            return [
                "Proceed to blueprint selection with strict binding among qc/pca/grm/genomic_prediction.",
                "Keep phenotype/covariate/pedigree sidecars aligned with the same sample namespace before execution.",
            ]
        if any(issue.code in {"plink_trio_incomplete", "consistency_plink_trio_consistency"} for issue in issues):
            return [
                "Restore missing PLINK companion files so .bed/.bim/.fam remain in sync.",
                "Re-run local validation before generating shell wrappers.",
            ]
        return [
            "Fix blocking input issues before scheduler-facing script generation.",
            "Keep raw data in place and only repair metadata paths or sidecar files.",
        ]
