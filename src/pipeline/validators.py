"""Input validation helpers for genetics workflow placeholders."""

from __future__ import annotations

from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field

from contracts.validation import ValidationIssue, ValidationReport


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


class ValidationSeverity(str, Enum):
    """Severity levels for pipeline-local validation detail."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class InputBundleEntry(BaseModel):
    """Single dataset entry passed into the local validator."""

    role: str
    path: str
    data_type: InputDataType | None = None
    required: bool = True
    description: str | None = None


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
                    message=issue.message if issue.hint is None else f"{issue.message} Hint: {issue.hint}",
                    path=issue.path,
                )
                for issue in self.issues
            ],
        )


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
        inputs: InputBundle | list[str] | list[InputBundleEntry] | list[dict[str, object]],
    ) -> ValidationReport:
        """Validate local input paths and return the frozen shared contract."""

        return self.inspect(inputs).to_contract_report()

    def inspect(
        self,
        inputs: InputBundle | list[str] | list[InputBundleEntry] | list[dict[str, object]],
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
                        message="The same input path was supplied more than once.",
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
                missing_companions = [
                    companion_path
                    for companion_path in companion_paths
                    if not Path(companion_path).exists()
                ]
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

        blocking_issue_count = sum(1 for issue in issues if issue.blocking)
        return PipelineValidationSnapshot(
            task_id=bundle.task_id,
            run_id=bundle.run_id,
            bundle=bundle,
            files=file_results,
            issues=issues,
            genotype_inputs_present=genotype_inputs_present,
            detected_types=detected_types,
            ready_for_gate="ready_for_design" if blocking_issue_count == 0 else "blocked_by_validation",
            recommended_next_actions=self._recommended_next_actions(
                bundle=bundle,
                valid=blocking_issue_count == 0,
                issues=issues,
            ),
        )

    def _normalize_inputs(
        self,
        inputs: InputBundle | list[str] | list[InputBundleEntry] | list[dict[str, object]],
    ) -> InputBundle:
        if isinstance(inputs, InputBundle):
            return inputs

        entries: list[InputBundleEntry] = []
        for index, raw_entry in enumerate(inputs):
            if isinstance(raw_entry, InputBundleEntry):
                entries.append(raw_entry)
                continue
            if isinstance(raw_entry, dict):
                entries.append(InputBundleEntry.model_validate(raw_entry))
                continue
            entries.append(
                InputBundleEntry(
                    role=f"input_{index + 1}",
                    path=str(raw_entry),
                )
            )
        return InputBundle(entries=entries)

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
        if inferred_type not in {
            InputDataType.PLINK_BED,
            InputDataType.PLINK_BIM,
            InputDataType.PLINK_FAM,
        }:
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
                "Proceed to QC, PCA, GRM, or genomic prediction blueprint selection.",
                "Attach phenotype, covariate, and pedigree tables before drafting genomic prediction stages.",
            ]
        if any(issue.code == "plink_trio_incomplete" for issue in issues):
            return [
                "Restore missing PLINK companion files so .bed/.bim/.fam remain in sync.",
                "Re-run local validation before generating shell placeholders.",
            ]
        return [
            "Fix blocking input issues before scheduler-facing script generation.",
            "Keep raw data in place and only repair metadata paths or sidecar files.",
        ]
