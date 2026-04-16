"""Named analysis families supported by the genetics v1 execution layer."""

PIPELINE_CATALOG = {
    "qc_pipeline": [
        "dataset_inventory",
        "sample_qc",
        "variant_qc",
        "qc_report",
    ],
    "pca_pipeline": [
        "ld_pruning",
        "pca_computation",
        "structure_summary",
        "stratification_warning",
    ],
    "population_structure": [
        "ld_pruning",
        "pca_computation",
        "structure_summary",
        "stratification_warning",
    ],
    "grm_builder": [
        "marker_standardization",
        "relationship_estimation",
        "matrix_qc",
        "grm_package",
    ],
    "genomic_prediction": [
        "cohort_alignment",
        "relationship_selection",
        "model_blueprint",
        "cross_validation_design",
        "prediction_report",
    ],
}

PIPELINE_ALIASES = {
    "population_structure": "pca_pipeline",
    "grm_construction": "grm_builder",
    "genomic_selection": "genomic_prediction",
}

PIPELINE_FOCUS = {
    "qc_pipeline": "Input sanity checks and quality-control execution for genotype-driven analysis.",
    "pca_pipeline": "Population structure exploration and stratification-aware review.",
    "grm_builder": "Relationship matrix construction and artifact packaging.",
    "genomic_prediction": "Quantitative genetics workflow for prediction and breeding-value reporting.",
}
