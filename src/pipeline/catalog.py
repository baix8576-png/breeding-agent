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
    "association_mapping_gwas": [
        "cohort_alignment",
        "association_model",
        "gwas_scan",
        "gwas_report",
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
    "relationship_matrix": "grm_builder",
    "association_mapping": "association_mapping_gwas",
    "gwas": "association_mapping_gwas",
    "gwas_qtl": "association_mapping_gwas",
    "breeding_value_prediction": "genomic_prediction",
    "genomic_selection": "genomic_prediction",
}

PIPELINE_FOCUS = {
    "qc_pipeline": "Compatibility blueprint for genotype-processing QC and input sanity checks.",
    "pca_pipeline": "Compatibility blueprint for population-structure and diversity review.",
    "grm_builder": "Compatibility blueprint for relationship-matrix construction and packaging.",
    "association_mapping_gwas": "Association mapping workflow for PLINK2 GWAS scans and report packaging.",
    "genomic_prediction": "Quantitative genetics workflow for breeding-value prediction and validation.",
}
