"""Pipeline blueprints used to keep genetics workflow planning explicit."""

from __future__ import annotations

from pydantic import BaseModel, Field

from pipeline.catalog import PIPELINE_ALIASES, PIPELINE_CATALOG, PIPELINE_FOCUS
from pipeline.validators import InputDataType


class PipelineBlueprint(BaseModel):
    """Description of a genetics workflow without implementation details."""

    name: str
    summary: str
    focus: str
    input_requirements: list[dict[str, object]] = Field(default_factory=list)
    stages: list[dict[str, object]] = Field(default_factory=list)
    outputs: list[dict[str, object]] = Field(default_factory=list)
    assets: dict[str, list[str]] = Field(default_factory=dict)
    report_sections: list[str] = Field(default_factory=list)
    interpretation_notes: list[str] = Field(default_factory=list)
    ready_for_gate: str = "design_ready"


def build_blueprint(name: str) -> PipelineBlueprint:
    """Build a named blueprint from the pipeline catalog."""

    canonical_name = PIPELINE_ALIASES.get(name, name)
    builder = _BLUEPRINT_BUILDERS.get(canonical_name)
    if builder is None:
        available = ", ".join(sorted(_BLUEPRINT_BUILDERS))
        raise ValueError(f"Unknown pipeline blueprint '{name}'. Available blueprints: {available}.")
    return builder()


def build_output_template(name: str) -> list[dict[str, object]]:
    """Return the expected output checklist for a named blueprint."""

    return build_blueprint(name).outputs


def list_blueprints() -> list[str]:
    """List canonical blueprint names supported by the placeholder layer."""

    return sorted(_BLUEPRINT_BUILDERS.keys())


def _artifact(
    artifact_id: str,
    relative_path: str,
    format: str,
    description: str,
    required: bool = True,
) -> dict[str, object]:
    return {
        "artifact_id": artifact_id,
        "relative_path": relative_path,
        "format": format,
        "description": description,
        "required": required,
    }


def _qc_blueprint() -> PipelineBlueprint:
    stages = [
        {
            "id": "dataset_inventory",
            "title": "Dataset Inventory",
            "kind": "input",
            "objective": "Record genotype, phenotype, covariate, and pedigree assets before analysis planning.",
            "required_inputs": ["genotype_dataset"],
            "optional_inputs": ["phenotype_table", "covariate_table", "pedigree_table"],
            "checks": [
                "Confirm genotype-bearing input is present.",
                "Check supported suffixes and PLINK trio completeness.",
                "Require task_id and run_id to be attached to downstream manifests.",
            ],
            "outputs": [
                _artifact(
                    "input_manifest",
                    "results/qc/input_manifest.json",
                    "json",
                    "Normalized placeholder manifest of detected local inputs and inferred types.",
                )
            ],
        },
        {
            "id": "sample_qc",
            "title": "Sample Quality Control",
            "kind": "qc",
            "objective": "Plan missingness, heterozygosity, and sample anomaly review without executing algorithms.",
            "required_inputs": ["genotype_dataset"],
            "optional_inputs": ["phenotype_table", "pedigree_table"],
            "checks": [
                "Reserve fields for missingness, heterozygosity, sex or pedigree consistency, and duplicate review.",
            ],
            "outputs": [
                _artifact(
                    "sample_qc_table",
                    "results/qc/sample_qc.tsv",
                    "tsv",
                    "Placeholder table for per-sample QC metrics and retain/drop recommendations.",
                )
            ],
        },
        {
            "id": "variant_qc",
            "title": "Variant Quality Control",
            "kind": "qc",
            "objective": "Plan missingness, MAF, and HWE review for downstream structure and prediction tasks.",
            "required_inputs": ["genotype_dataset"],
            "optional_inputs": [],
            "checks": [
                "Reserve fields for missing rate, MAF, HWE, and marker-level exclusion rationale.",
            ],
            "outputs": [
                _artifact(
                    "variant_qc_table",
                    "results/qc/variant_qc.tsv",
                    "tsv",
                    "Placeholder table for per-marker QC metrics and retain/drop recommendations.",
                )
            ],
        },
        {
            "id": "qc_report",
            "title": "QC Report Assembly",
            "kind": "report",
            "objective": "Assemble a reviewer-facing QC summary and retained dataset index.",
            "required_inputs": ["sample_qc_table", "variant_qc_table"],
            "optional_inputs": [],
            "checks": [
                "Record unresolved QC questions rather than inferring final biological conclusions.",
            ],
            "outputs": [
                _artifact(
                    "qc_summary_report",
                    "reports/qc_summary.md",
                    "markdown",
                    "Human-readable placeholder report for QC decisions, caveats, and retained dataset notes.",
                ),
                _artifact(
                    "retained_dataset_index",
                    "results/qc/retained_dataset/README.md",
                    "markdown",
                    "Index of future cleaned dataset outputs without generating real filtered files yet.",
                ),
            ],
        },
    ]
    outputs = [artifact for stage in stages for artifact in stage["outputs"]]
    return PipelineBlueprint(
        name="qc_pipeline",
        summary="Quality control planning workflow for genotype-centered analyses.",
        focus=PIPELINE_FOCUS["qc_pipeline"],
        input_requirements=[
            {
                "role": "genotype_dataset",
                "accepted_types": [InputDataType.VCF.value, InputDataType.PLINK_BED.value, InputDataType.BAM.value],
                "required": True,
                "description": "Primary genotype-bearing input used to plan downstream QC steps.",
            },
            {
                "role": "phenotype_table",
                "accepted_types": [InputDataType.PHENOTYPE_TABLE.value, InputDataType.TEXT_TABLE.value],
                "required": False,
                "description": "Optional trait table used for later cohort alignment checks.",
            },
            {
                "role": "pedigree_table",
                "accepted_types": [InputDataType.PEDIGREE_TABLE.value, InputDataType.TEXT_TABLE.value],
                "required": False,
                "description": "Optional pedigree sidecar used for sample identity review.",
            },
        ],
        stages=stages,
        outputs=outputs,
        assets={
            "scripts": ["scripts/qc_pipeline/", "scripts/report_generator/"],
            "references": [
                "references/input_specs/",
                "references/qc_rules/",
                "references/report_templates/qc-report-template.md",
            ],
        },
        report_sections=[
            "Input inventory",
            "Sample QC placeholder metrics",
            "Variant QC placeholder metrics",
            "Retained dataset note",
            "Known risks and unresolved checks",
        ],
        interpretation_notes=[
            "QC thresholds in this blueprint are placeholders and must be confirmed by project-specific SOPs.",
            "QC summaries do not imply biological interpretation or publication-ready sample exclusion criteria.",
        ],
        ready_for_gate="design_ready",
    )


def _pca_blueprint() -> PipelineBlueprint:
    stages = [
        {
            "id": "ld_pruning",
            "title": "Marker Pruning Plan",
            "kind": "qc",
            "objective": "Define placeholder LD-pruning steps before PCA and stratification review.",
            "required_inputs": ["genotype_dataset"],
            "optional_inputs": [],
            "checks": [
                "Record that LD pruning is required before PCA unless a method note says otherwise.",
            ],
            "outputs": [
                _artifact(
                    "pruning_manifest",
                    "results/structure/pruning_manifest.json",
                    "json",
                    "Planned LD-pruning configuration and prerequisite notes.",
                )
            ],
        },
        {
            "id": "pca_computation",
            "title": "PCA Blueprint",
            "kind": "structure",
            "objective": "Describe how principal components would be computed and exported.",
            "required_inputs": ["genotype_dataset"],
            "optional_inputs": ["covariate_table"],
            "checks": [
                "Reserve fields for sample IDs, component axes, and explained variance.",
            ],
            "outputs": [
                _artifact(
                    "eigenvec_placeholder",
                    "results/structure/pca/eigenvec.tsv",
                    "tsv",
                    "Placeholder principal component scores table.",
                ),
                _artifact(
                    "eigenval_placeholder",
                    "results/structure/pca/eigenval.tsv",
                    "tsv",
                    "Placeholder eigenvalue summary table.",
                ),
            ],
        },
        {
            "id": "structure_summary",
            "title": "Population Structure Summary",
            "kind": "structure",
            "objective": "Package structure plots, clustering notes, and cohort separation caveats.",
            "required_inputs": ["eigenvec_placeholder", "eigenval_placeholder"],
            "optional_inputs": [],
            "checks": [
                "Keep cluster descriptions descriptive rather than biological or breed-assignment claims.",
            ],
            "outputs": [
                _artifact(
                    "pca_plot_index",
                    "results/structure/figures/README.md",
                    "markdown",
                    "Placeholder index for PCA scatter plots and color-coding decisions.",
                ),
                _artifact(
                    "structure_summary_report",
                    "reports/structure_summary.md",
                    "markdown",
                    "Narrative summary of PCA interpretation and cohort structure warnings.",
                ),
            ],
        },
        {
            "id": "stratification_warning",
            "title": "Stratification Risk Note",
            "kind": "report",
            "objective": "Make downstream modelers aware of residual stratification risks.",
            "required_inputs": ["structure_summary_report"],
            "optional_inputs": [],
            "checks": [
                "Describe downstream adjustment needs without auto-selecting covariates.",
            ],
            "outputs": [
                _artifact(
                    "stratification_risk_note",
                    "reports/stratification_risk.md",
                    "markdown",
                    "Explicit caveat note for GWAS or genomic prediction stages.",
                )
            ],
        },
    ]
    outputs = [artifact for stage in stages for artifact in stage["outputs"]]
    return PipelineBlueprint(
        name="pca_pipeline",
        summary="Population structure and stratification-aware interpretation workflow.",
        focus=PIPELINE_FOCUS["pca_pipeline"],
        input_requirements=[
            {
                "role": "genotype_dataset",
                "accepted_types": [InputDataType.VCF.value, InputDataType.PLINK_BED.value],
                "required": True,
                "description": "Genotype matrix used for LD-pruned PCA planning.",
            },
            {
                "role": "covariate_table",
                "accepted_types": [InputDataType.COVARIATE_TABLE.value, InputDataType.TEXT_TABLE.value],
                "required": False,
                "description": "Optional sample covariates or previously generated PCs.",
            },
        ],
        stages=stages,
        outputs=outputs,
        assets={
            "scripts": ["scripts/pca_pipeline/", "scripts/report_generator/"],
            "references": [
                "references/input_specs/",
                "references/structure_analysis/",
                "references/report_templates/structure-summary-template.md",
            ],
        },
        report_sections=[
            "Dataset basis",
            "Pruning strategy note",
            "PCA artifact inventory",
            "Population structure summary",
            "Stratification caveats",
        ],
        interpretation_notes=[
            "The placeholder layer must not assign biological ancestry or breed labels automatically.",
            "PC inclusion in downstream models remains a design decision and is not fixed by this blueprint alone.",
        ],
        ready_for_gate="design_ready",
    )


def _grm_blueprint() -> PipelineBlueprint:
    stages = [
        {
            "id": "marker_standardization",
            "title": "Marker Standardization Plan",
            "kind": "qc",
            "objective": "Declare preprocessing assumptions for relationship matrix construction.",
            "required_inputs": ["genotype_dataset"],
            "optional_inputs": [],
            "checks": [
                "Document allele coding, filtering assumptions, and scaling choices.",
            ],
            "outputs": [
                _artifact(
                    "marker_standardization_note",
                    "results/grm/marker_standardization.md",
                    "markdown",
                    "Placeholder note covering matrix-preparation assumptions.",
                )
            ],
        },
        {
            "id": "relationship_estimation",
            "title": "Relationship Matrix Blueprint",
            "kind": "relationship",
            "objective": "Define how a GRM or relatedness matrix would be built and stored.",
            "required_inputs": ["genotype_dataset"],
            "optional_inputs": ["pedigree_table"],
            "checks": [
                "Keep sample ordering explicit for downstream model reproducibility.",
                "Document whether pedigree is used only for cross-checking or later ssGBLUP integration.",
            ],
            "outputs": [
                _artifact(
                    "grm_matrix_placeholder",
                    "results/grm/grm_matrix.tsv",
                    "tsv",
                    "Placeholder matrix export or pointer to a future binary matrix artifact.",
                ),
                _artifact(
                    "grm_id_map",
                    "results/grm/grm_ids.tsv",
                    "tsv",
                    "Sample ordering file for matrix consumers.",
                ),
            ],
        },
        {
            "id": "matrix_qc",
            "title": "Matrix QC Summary",
            "kind": "relationship",
            "objective": "Reserve checks for symmetry, diagonals, scale, and sample coverage.",
            "required_inputs": ["grm_matrix_placeholder", "grm_id_map"],
            "optional_inputs": [],
            "checks": [
                "Record placeholder checks for symmetry, diagonals, scale, and missing samples.",
            ],
            "outputs": [
                _artifact(
                    "grm_qc_report",
                    "reports/grm_qc.md",
                    "markdown",
                    "Placeholder report for matrix completeness and sanity checks.",
                )
            ],
        },
        {
            "id": "grm_package",
            "title": "GRM Package Index",
            "kind": "report",
            "objective": "Index matrix artifacts for downstream prediction workflows.",
            "required_inputs": ["grm_qc_report"],
            "optional_inputs": [],
            "checks": [
                "Expose future deliverables without fabricating matrix values.",
            ],
            "outputs": [
                _artifact(
                    "grm_package_index",
                    "results/grm/README.md",
                    "markdown",
                    "Inventory of future GRM deliverables and consumer modules.",
                )
            ],
        },
    ]
    outputs = [artifact for stage in stages for artifact in stage["outputs"]]
    return PipelineBlueprint(
        name="grm_builder",
        summary="Relationship matrix planning workflow for relatedness and prediction stages.",
        focus=PIPELINE_FOCUS["grm_builder"],
        input_requirements=[
            {
                "role": "genotype_dataset",
                "accepted_types": [InputDataType.VCF.value, InputDataType.PLINK_BED.value],
                "required": True,
                "description": "Genotype matrix used to derive a GRM or relatedness representation.",
            },
            {
                "role": "pedigree_table",
                "accepted_types": [InputDataType.PEDIGREE_TABLE.value, InputDataType.TEXT_TABLE.value],
                "required": False,
                "description": "Optional pedigree used to compare genomic and recorded relationships.",
            },
        ],
        stages=stages,
        outputs=outputs,
        assets={
            "scripts": ["scripts/grm_builder/", "scripts/report_generator/"],
            "references": [
                "references/input_specs/",
                "references/structure_analysis/",
                "references/modeling_guides/",
            ],
        },
        report_sections=[
            "Marker standardization assumptions",
            "GRM matrix inventory",
            "Matrix QC summary",
            "Downstream consumer notes",
        ],
        interpretation_notes=[
            "Placeholder matrix outputs are not valid relatedness estimates until a concrete backend is implemented and validated.",
        ],
        ready_for_gate="design_ready",
    )


def _genomic_prediction_blueprint() -> PipelineBlueprint:
    stages = [
        {
            "id": "cohort_alignment",
            "title": "Cohort Alignment Plan",
            "kind": "input",
            "objective": "Align genotype, phenotype, covariate, and pedigree roles before model design.",
            "required_inputs": ["genotype_dataset", "phenotype_table"],
            "optional_inputs": ["covariate_table", "pedigree_table"],
            "checks": [
                "Reserve explicit fields for sample ID matching and missing phenotype handling.",
                "Carry task_id and run_id into downstream manifests and report packaging.",
            ],
            "outputs": [
                _artifact(
                    "cohort_alignment_manifest",
                    "results/prediction/cohort_alignment.json",
                    "json",
                    "Placeholder manifest for train and validation cohorts, trait columns, and merge keys.",
                )
            ],
        },
        {
            "id": "relationship_selection",
            "title": "Relationship Backbone Selection",
            "kind": "relationship",
            "objective": "Select placeholder path among GBLUP, ssGBLUP, Bayes, or equivalent modeling backbones.",
            "required_inputs": ["genotype_dataset", "phenotype_table"],
            "optional_inputs": ["pedigree_table"],
            "checks": [
                "Document why GBLUP, ssGBLUP, Bayes, or equivalent was selected.",
            ],
            "outputs": [
                _artifact(
                    "model_family_note",
                    "results/prediction/model_family.md",
                    "markdown",
                    "Decision note for GBLUP, ssGBLUP, Bayes, or equivalent placeholder routes.",
                )
            ],
        },
        {
            "id": "model_blueprint",
            "title": "Model Blueprint",
            "kind": "model",
            "objective": "Describe training inputs, fixed effects, random effects, and expected prediction outputs.",
            "required_inputs": ["cohort_alignment_manifest", "model_family_note"],
            "optional_inputs": ["covariate_table"],
            "checks": [
                "Expose trait, effects, and backend assumptions as explicit fields.",
            ],
            "outputs": [
                _artifact(
                    "model_spec",
                    "results/prediction/model_spec.json",
                    "json",
                    "Structured placeholder spec for trait, effects, and model backend choices.",
                ),
                _artifact(
                    "prediction_table_placeholder",
                    "results/prediction/predictions.tsv",
                    "tsv",
                    "Placeholder EBV or GEBV prediction table schema.",
                ),
            ],
        },
        {
            "id": "cross_validation_design",
            "title": "Validation Design",
            "kind": "evaluation",
            "objective": "Specify cross-validation, stratified validation, and bias checks.",
            "required_inputs": ["model_spec"],
            "optional_inputs": [],
            "checks": [
                "Reserve fields for correlation, bias, fold structure, and subgroup validation.",
            ],
            "outputs": [
                _artifact(
                    "validation_plan",
                    "results/prediction/validation_plan.md",
                    "markdown",
                    "Placeholder design for correlation, bias, and fold structure metrics.",
                ),
                _artifact(
                    "metric_table_placeholder",
                    "results/prediction/metrics.tsv",
                    "tsv",
                    "Placeholder table schema for accuracy, bias, and subgroup metrics.",
                ),
            ],
        },
        {
            "id": "prediction_report",
            "title": "Prediction Report",
            "kind": "report",
            "objective": "Bundle model notes, evaluation placeholders, and interpretation caveats.",
            "required_inputs": ["prediction_table_placeholder", "metric_table_placeholder"],
            "optional_inputs": [],
            "checks": [
                "Do not convert placeholder metrics into scientific claims or breeding decisions.",
            ],
            "outputs": [
                _artifact(
                    "prediction_summary_report",
                    "reports/genomic_prediction_summary.md",
                    "markdown",
                    "Human-readable summary of modeling route, validation design, and caveats.",
                )
            ],
        },
    ]
    outputs = [artifact for stage in stages for artifact in stage["outputs"]]
    return PipelineBlueprint(
        name="genomic_prediction",
        summary="Quantitative genetics workflow planning for genomic prediction and breeding-value reporting.",
        focus=PIPELINE_FOCUS["genomic_prediction"],
        input_requirements=[
            {
                "role": "genotype_dataset",
                "accepted_types": [InputDataType.VCF.value, InputDataType.PLINK_BED.value],
                "required": True,
                "description": "Primary genotype dataset used to derive genomic relationships or marker effects.",
            },
            {
                "role": "phenotype_table",
                "accepted_types": [InputDataType.PHENOTYPE_TABLE.value, InputDataType.TEXT_TABLE.value],
                "required": True,
                "description": "Trait table defining response variables and observation units.",
            },
            {
                "role": "covariate_table",
                "accepted_types": [InputDataType.COVARIATE_TABLE.value, InputDataType.TEXT_TABLE.value],
                "required": False,
                "description": "Optional fixed-effect table such as batch, herd, or prior PCs.",
            },
            {
                "role": "pedigree_table",
                "accepted_types": [InputDataType.PEDIGREE_TABLE.value, InputDataType.TEXT_TABLE.value],
                "required": False,
                "description": "Optional pedigree used for ssGBLUP-style placeholder routes.",
            },
        ],
        stages=stages,
        outputs=outputs,
        assets={
            "scripts": [
                "scripts/grm_builder/",
                "scripts/genomic_prediction/",
                "scripts/report_generator/",
            ],
            "references": [
                "references/input_specs/",
                "references/modeling_guides/",
                "references/evaluation/",
                "references/report_templates/genomic-prediction-template.md",
            ],
        },
        report_sections=[
            "Trait and cohort scope",
            "Model family choice",
            "Training and validation design",
            "Prediction output inventory",
            "Interpretation caveats",
        ],
        interpretation_notes=[
            "Placeholder metric tables are schemas only and must not be reported as true predictive performance.",
            "The MVP layer must not recommend breeding decisions or culling actions from placeholder outputs.",
        ],
        ready_for_gate="design_ready",
    )


_BLUEPRINT_BUILDERS = {
    "qc_pipeline": _qc_blueprint,
    "pca_pipeline": _pca_blueprint,
    "grm_builder": _grm_blueprint,
    "genomic_prediction": _genomic_prediction_blueprint,
}


assert set(_BLUEPRINT_BUILDERS).issubset(set(PIPELINE_CATALOG))
