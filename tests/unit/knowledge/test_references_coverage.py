from __future__ import annotations

from collections import Counter
from pathlib import Path

from knowledge.indexing import ReferenceKnowledgeIndexer


REFERENCES_ROOT = Path("references")
STANDARD_DIRECTORIES = {
    "analysis_domains",
    "input_specs",
    "qc_rules",
    "structure_analysis",
    "modeling_guides",
    "evaluation",
    "report_templates",
    "papers",
    "sop",
    "parameter_playbooks",
    "failure_cases",
    "ontology",
}
CORE_DIRECTORIES = {
    "qc_rules",
    "modeling_guides",
    "evaluation",
    "failure_cases",
    "parameter_playbooks",
}
MARKDOWN_ALLOWLIST = {
    "references/INDEX.md",
    "references/ontology/knowledge_item.v2.md",
}
FORBIDDEN_REFERENCE_SUFFIXES = {
    ".bam",
    ".bcf",
    ".cram",
    ".fasta",
    ".fastq",
    ".fq",
    ".pdf",
    ".tei",
    ".vcf",
    ".xml",
}
CURRENT_BLUEPRINT_SCOPES = {
    "knowledge_governance",
    "genotype_processing",
    "population_genetics",
    "quantitative_genetics",
    "association_mapping",
    "reporting_audit",
}
LEGACY_BLUEPRINT_SCOPES = {
    "qc",
    "pca",
    "grm",
    "genomic_prediction",
    "shared",
}
CONTENT_COMPLETENESS_QUERIES = {
    "plink2 bcftools genotype processing operation guide SOP output contract": {
        "sop_genotype_processing_execution",
        "playbook_qc_defaults",
    },
    "population genetics PCA admixture ROH LD selection signature SOP": {
        "sop_population_genetics_execution",
        "domain_selection_signatures_fst_window_policy",
    },
    "GCTA GRM REML heritability genomic prediction resource threads memory": {
        "sop_quantitative_genetics_execution",
        "playbook_grm_resource_baseline",
    },
    "GWAS mixed model GEMMA association mapping QTL report caveat": {
        "sop_association_mapping_execution",
        "domain_association_mapping_trait_model_policy",
    },
    "report index audit bundle diagnostic traceability source path anchor": {
        "sop_reporting_audit_execution",
        "template_report_index_v2",
    },
}


def _build_references():
    return ReferenceKnowledgeIndexer(REFERENCES_ROOT).build()


def test_references_build_without_metadata_errors_and_hit_chunk_floor() -> None:
    result = _build_references()

    assert result.errors == []
    assert result.manifest.metadata_schema == "knowledge_item.v2"
    assert result.manifest.chunk_count >= 240
    assert all(chunk.doc_id for chunk in result.chunks)
    assert all(chunk.source_path.startswith("references/") for chunk in result.chunks)
    assert all(chunk.page_or_anchor.startswith("#") for chunk in result.chunks)


def test_reference_doc_ids_are_globally_unique() -> None:
    result = _build_references()
    doc_ids = [item.doc_id for item in result.items]

    assert result.errors == []
    assert len(doc_ids) == len(set(doc_ids))


def test_reference_metadata_uses_current_blueprint_scopes_only() -> None:
    result = _build_references()
    scope_values = {item.blueprint_scope.value for item in result.items}

    assert result.errors == []
    assert scope_values <= CURRENT_BLUEPRINT_SCOPES
    assert not (scope_values & LEGACY_BLUEPRINT_SCOPES)


def test_standard_reference_directories_have_indexed_chunks() -> None:
    result = _build_references()
    counts: Counter[str] = Counter()
    for chunk in result.chunks:
        parts = Path(chunk.source_path).parts
        if len(parts) >= 2 and parts[0] == "references":
            counts[parts[1]] += 1

    for directory in STANDARD_DIRECTORIES:
        assert counts[directory] >= 3, (directory, counts[directory])

    for directory in CORE_DIRECTORIES:
        assert counts[directory] >= 5, (directory, counts[directory])


def test_formal_markdown_files_expose_knowledge_item_metadata() -> None:
    missing_metadata: list[str] = []
    for path in REFERENCES_ROOT.rglob("*.md"):
        relative_path = path.as_posix()
        if path.name == "README.md" or relative_path in MARKDOWN_ALLOWLIST:
            continue
        if "knowledge_item.v2:" not in path.read_text(encoding="utf-8"):
            missing_metadata.append(relative_path)

    assert missing_metadata == []


def test_diagnostic_pattern_files_enter_reference_index() -> None:
    result = _build_references()
    doc_ids = {item.doc_id for item in result.items}

    assert "diagnostic_scheduler_slurm_qos_or_resource_limit" in doc_ids
    assert "diagnostic_scheduler_pbs_unknown_queue" in doc_ids
    assert "diagnostic_bio_tool_plink2_missing_bfile_triplet" in doc_ids
    assert "diagnostic_bio_tool_bcftools_not_bgzip_or_missing_index" in doc_ids
    assert "diagnostic_bio_tool_gcta_id_mismatch_between_inputs" in doc_ids


def test_analysis_domain_data_preparation_qc_enters_reference_index() -> None:
    result = _build_references()
    doc_ids = {item.doc_id for item in result.items}

    expected_doc_ids = {
        "domain_data_preparation_qc_scope",
        "domain_data_preparation_qc_input_roles",
        "domain_data_preparation_qc_sample_id_policy",
        "domain_data_preparation_qc_qc_boundary",
        "domain_data_preparation_qc_execution_bridge",
    }

    assert result.errors == []
    assert expected_doc_ids <= doc_ids


def test_analysis_domain_genotype_processing_enters_reference_index() -> None:
    result = _build_references()
    doc_ids = {item.doc_id for item in result.items}

    expected_doc_ids = {
        "domain_genotype_processing_scope",
        "domain_genotype_processing_format_normalization_policy",
        "domain_genotype_processing_allele_alignment_policy",
        "domain_genotype_processing_liftover_policy",
        "domain_genotype_processing_phasing_imputation_policy",
        "domain_genotype_processing_execution_bridge",
    }

    assert result.errors == []
    assert expected_doc_ids <= doc_ids


def test_analysis_domain_population_genetics_enters_reference_index() -> None:
    result = _build_references()
    doc_ids = {item.doc_id for item in result.items}

    expected_doc_ids = {
        "domain_population_structure_scope",
        "domain_population_structure_pca_pruning_policy",
        "domain_population_structure_stratification_boundary",
        "domain_population_structure_admixture_boundary",
        "domain_population_structure_execution_bridge",
        "domain_genetic_diversity_inbreeding_scope",
        "domain_genetic_diversity_inbreeding_ld_policy",
        "domain_genetic_diversity_inbreeding_roh_policy",
        "domain_genetic_diversity_inbreeding_pi_heterozygosity_policy",
        "domain_genetic_diversity_inbreeding_execution_bridge",
        "domain_selection_signatures_scope",
        "domain_selection_signatures_population_definition",
        "domain_selection_signatures_statistic_family_boundary",
        "domain_selection_signatures_candidate_region_policy",
        "domain_selection_signatures_execution_bridge",
    }

    assert result.errors == []
    assert expected_doc_ids <= doc_ids


def test_analysis_domain_association_mapping_enters_reference_index() -> None:
    result = _build_references()
    doc_ids = {item.doc_id for item in result.items}

    expected_doc_ids = {
        "domain_association_mapping_gwas_qtl_scope",
        "domain_association_mapping_gwas_input_model_policy",
        "domain_association_mapping_population_correction_policy",
        "domain_association_mapping_qtl_fine_mapping_boundary",
        "domain_association_mapping_candidate_interpretation_policy",
        "domain_association_mapping_execution_bridge",
    }

    assert result.errors == []
    assert expected_doc_ids <= doc_ids


def test_analysis_domain_functional_genomics_annotation_enters_reference_index() -> None:
    result = _build_references()
    doc_ids = {item.doc_id for item in result.items}

    expected_doc_ids = {
        "domain_functional_genomics_annotation_scope",
        "domain_functional_genomics_annotation_gene_model_policy",
        "domain_functional_genomics_annotation_regulatory_evidence_policy",
        "domain_functional_genomics_annotation_pangenome_sv_cnv_policy",
        "domain_functional_genomics_annotation_eqtl_single_cell_policy",
        "domain_functional_genomics_annotation_candidate_reporting_policy",
        "domain_functional_genomics_annotation_execution_bridge",
    }

    assert result.errors == []
    assert expected_doc_ids <= doc_ids


def test_analysis_domain_quantitative_genetics_enters_reference_index() -> None:
    result = _build_references()
    doc_ids = {item.doc_id for item in result.items}

    expected_doc_ids = {
        "domain_relationship_matrix_variance_components_scope",
        "domain_relationship_matrix_grm_construction_policy",
        "domain_relationship_matrix_variance_component_policy",
        "domain_relationship_matrix_sample_order_policy",
        "domain_relationship_matrix_execution_bridge",
        "domain_genomic_prediction_breeding_value_scope",
        "domain_genomic_prediction_model_family_policy",
        "domain_genomic_prediction_validation_policy",
        "domain_genomic_prediction_breeding_decision_boundary",
        "domain_genomic_prediction_execution_bridge",
    }

    assert result.errors == []
    assert expected_doc_ids <= doc_ids


def test_analysis_domain_reporting_audit_enters_reference_index() -> None:
    result = _build_references()
    doc_ids = {item.doc_id for item in result.items}

    expected_doc_ids = {
        "domain_hpc_execution_reporting_audit_scope",
        "domain_hpc_execution_reporting_remote_traceability_policy",
        "domain_hpc_execution_reporting_report_index_policy",
        "domain_hpc_execution_reporting_diagnostic_policy",
        "domain_hpc_execution_reporting_audit_bundle_policy",
        "domain_hpc_execution_reporting_execution_bridge",
    }

    assert result.errors == []
    assert expected_doc_ids <= doc_ids


def test_knowledge_completion_module_map_enters_reference_index() -> None:
    result = _build_references()
    doc_ids = {item.doc_id for item in result.items}

    expected_doc_ids = {
        "ontology_knowledge_completion_scope_map",
        "ontology_knowledge_completion_module_order",
        "ontology_knowledge_completion_literature_batches",
        "ontology_knowledge_completion_ingestion_boundary",
        "ontology_knowledge_completion_acceptance_gates",
    }

    assert result.errors == []
    assert expected_doc_ids <= doc_ids


def test_m02_to_m15_completion_detail_doc_ids_exist() -> None:
    result = _build_references()
    doc_ids = {item.doc_id for item in result.items}

    expected_doc_ids = {
        "input_phenotype_dictionary_policy",
        "input_covariate_type_policy",
        "input_pedigree_consistency_policy",
        "input_sidecar_checksum_policy",
        "input_missing_file_diagnostic_policy",
        "qc_rule_sex_duplicate_relatedness_checks",
        "qc_rule_batch_platform_missingness_review",
        "qc_rule_filter_order_and_count_audit",
        "domain_genotype_processing_variant_normalization_execution_checklist",
        "domain_genotype_processing_plink_bfile_pfile_bridge",
        "domain_genotype_processing_imputation_quality_boundary",
        "domain_genotype_processing_reference_assembly_record",
        "domain_population_structure_pruning_relatedness_detail",
        "domain_population_structure_pca_component_retention_policy",
        "domain_population_structure_admixture_k_selection_policy",
        "domain_population_structure_cluster_name_review_policy",
        "domain_genetic_diversity_roh_threshold_detail",
        "domain_genetic_diversity_ld_decay_window_policy",
        "domain_genetic_diversity_ne_inbreeding_caveat_policy",
        "domain_genetic_diversity_group_summary_policy",
        "domain_selection_signatures_fst_window_policy",
        "domain_selection_signatures_haplotype_scan_prerequisites",
        "domain_selection_signatures_composite_consensus_policy",
        "domain_selection_signatures_candidate_region_merge_policy",
        "domain_association_mapping_trait_model_policy",
        "domain_association_mapping_covariate_pc_policy",
        "domain_association_mapping_multiple_testing_policy",
        "domain_association_mapping_qtl_overlap_evidence_policy",
        "domain_functional_genomics_annotation_coordinate_liftover_check",
        "domain_functional_genomics_annotation_tissue_relevance_matrix",
        "domain_functional_genomics_annotation_sv_gene_disruption_policy",
        "domain_relationship_matrix_grm_qc_prerequisites",
        "domain_relationship_matrix_a_matrix_h_matrix_boundary",
        "domain_relationship_matrix_reml_convergence_policy",
        "domain_relationship_matrix_sparse_relatedness_policy",
        "domain_genomic_prediction_training_validation_split_policy",
        "domain_genomic_prediction_multi_breed_validation_policy",
        "domain_genomic_prediction_model_comparison_policy",
        "domain_genomic_prediction_deployment_decision_gate",
        "species_overlay_cattle_defaults",
        "species_overlay_pig_defaults",
        "species_overlay_poultry_defaults",
        "species_overlay_sheep_goat_defaults",
        "species_overlay_aquaculture_defaults",
        "literature_landmark_method_evidence_matrix",
        "literature_recent_high_impact_evidence_matrix",
        "literature_card_update_and_dedup_policy",
        "sop_remote_shell_execution_review_gate",
        "evaluation_operational_acceptance_gate",
        "failure_recovery_decision_matrix",
        "template_report_review_completion_gate",
        "ontology_retrieval_regression_query_catalog",
        "ontology_index_health_check_policy",
        "ontology_chunk_traceability_review_gate",
    }

    assert result.errors == []
    assert expected_doc_ids <= doc_ids


def test_reference_layer_retrieval_queries_cover_major_topics() -> None:
    index = ReferenceKnowledgeIndexer(REFERENCES_ROOT).build_index()
    query_expectations = {
        "data preparation genotype QC sample ID VCF PLINK phenotype covariate sidecar": {
            "domain_data_preparation_qc_scope",
            "domain_data_preparation_qc_input_roles",
            "domain_data_preparation_qc_sample_id_policy",
        },
        "VCF normalization PLINK conversion allele alignment liftover phasing imputation reference panel": {
            "domain_genotype_processing_format_normalization_policy",
            "domain_genotype_processing_allele_alignment_policy",
            "domain_genotype_processing_liftover_policy",
            "domain_genotype_processing_phasing_imputation_policy",
        },
        "input bundle sample id phenotype covariate pedigree": {
            "input_request_envelope",
            "input_sample_id_policy",
        },
        "QC missingness MAF HWE heterozygosity": {
            "qc_rule_missingness_thresholds",
            "qc_rule_maf_hwe_policy",
            "qc_rule_heterozygosity_inbreeding",
        },
        "PCA stratification admixture cluster labeling": {
            "domain_population_structure_scope",
            "domain_population_structure_stratification_boundary",
            "structure_pca_interpretation_policy",
            "structure_admixture_caution_policy",
            "structure_cluster_labeling_caution",
        },
        "LD decay ROH inbreeding nucleotide diversity heterozygosity livestock": {
            "domain_genetic_diversity_inbreeding_ld_policy",
            "domain_genetic_diversity_inbreeding_roh_policy",
            "domain_genetic_diversity_inbreeding_pi_heterozygosity_policy",
        },
        "Fst pi Tajima iHS XP-EHH selection signatures candidate regions": {
            "domain_selection_signatures_scope",
            "domain_selection_signatures_statistic_family_boundary",
            "domain_selection_signatures_candidate_region_policy",
        },
        "GWAS QTL fine mapping PLINK2 glm covariates candidate gene interpretation": {
            "domain_association_mapping_gwas_qtl_scope",
            "domain_association_mapping_gwas_input_model_policy",
            "domain_association_mapping_qtl_fine_mapping_boundary",
            "domain_association_mapping_candidate_interpretation_policy",
        },
        "candidate gene functional annotation GWAS selection QTL eQTL FarmGTEx single-cell pangenome SV CNV": {
            "domain_functional_genomics_annotation_gene_model_policy",
            "domain_functional_genomics_annotation_regulatory_evidence_policy",
            "domain_functional_genomics_annotation_pangenome_sv_cnv_policy",
            "domain_functional_genomics_annotation_eqtl_single_cell_policy",
            "domain_functional_genomics_annotation_candidate_reporting_policy",
        },
        "GRM GBLUP ssGBLUP fixed random effects": {
            "domain_relationship_matrix_variance_components_scope",
            "domain_genomic_prediction_model_family_policy",
            "modeling_gblup_route_guide",
            "modeling_ssgblup_boundary_guide",
            "modeling_fixed_random_effect_checklist",
        },
        "GRM kinship REML heritability variance components sample order GCTA": {
            "domain_relationship_matrix_grm_construction_policy",
            "domain_relationship_matrix_variance_component_policy",
            "domain_relationship_matrix_sample_order_policy",
        },
        "GEBV genomic prediction breeding value cross validation bias calibration": {
            "domain_genomic_prediction_breeding_value_scope",
            "domain_genomic_prediction_validation_policy",
            "domain_genomic_prediction_breeding_decision_boundary",
        },
        "cross validation bias calibration subgroup validation": {
            "evaluation_cross_validation_patterns",
            "evaluation_bias_calibration_notes",
            "evaluation_subgroup_validation_policy",
        },
        "report_index audit bundle diagnostic report": {
            "domain_hpc_execution_reporting_report_index_policy",
            "domain_hpc_execution_reporting_audit_bundle_policy",
            "template_report_index_v2",
            "template_audit_bundle",
            "template_diagnostic_report",
        },
        "remote execution traceability logs job id stdout stderr report generator audit bundle": {
            "domain_hpc_execution_reporting_remote_traceability_policy",
            "domain_hpc_execution_reporting_execution_bridge",
            "domain_hpc_execution_reporting_diagnostic_policy",
        },
        "scheduler QOS PBS qsub plink2 bcftools gcta failure": {
            "diagnostic_scheduler_slurm_qos_or_resource_limit",
            "diagnostic_scheduler_pbs_unknown_queue",
            "diagnostic_bio_tool_plink2_missing_bfile_triplet",
            "diagnostic_bio_tool_bcftools_not_bgzip_or_missing_index",
            "diagnostic_bio_tool_gcta_id_mismatch_between_inputs",
        },
        "knowledge completion modules classic papers recent high impact literature raw PDF batch fetch domain scope": {
            "ontology_knowledge_completion_scope_map",
            "ontology_knowledge_completion_literature_batches",
            "ontology_knowledge_completion_ingestion_boundary",
        },
        "phenotype dictionary trait units covariate type pedigree consistency sidecar checksum missing file diagnostic": {
            "input_phenotype_dictionary_policy",
            "input_covariate_type_policy",
            "input_pedigree_consistency_policy",
            "input_sidecar_checksum_policy",
            "input_missing_file_diagnostic_policy",
        },
        "sex check duplicate samples cryptic relatedness batch platform missingness filter order audit": {
            "qc_rule_sex_duplicate_relatedness_checks",
            "qc_rule_batch_platform_missingness_review",
            "qc_rule_filter_order_and_count_audit",
        },
        "variant normalization left align split multiallelic PLINK bfile pfile imputation quality reference assembly": {
            "domain_genotype_processing_variant_normalization_execution_checklist",
            "domain_genotype_processing_plink_bfile_pfile_bridge",
            "domain_genotype_processing_imputation_quality_boundary",
            "domain_genotype_processing_reference_assembly_record",
        },
        "PCA pruning relatedness component retention admixture K cluster name review": {
            "domain_population_structure_pruning_relatedness_detail",
            "domain_population_structure_pca_component_retention_policy",
            "domain_population_structure_admixture_k_selection_policy",
            "domain_population_structure_cluster_name_review_policy",
        },
        "ROH threshold LD decay effective population size group diversity summary": {
            "domain_genetic_diversity_roh_threshold_detail",
            "domain_genetic_diversity_ld_decay_window_policy",
            "domain_genetic_diversity_ne_inbreeding_caveat_policy",
            "domain_genetic_diversity_group_summary_policy",
        },
        "selection signature Fst window haplotype prerequisite XP-EHH iHS XP-CLR consensus candidate merge": {
            "domain_selection_signatures_fst_window_policy",
            "domain_selection_signatures_haplotype_scan_prerequisites",
            "domain_selection_signatures_composite_consensus_policy",
            "domain_selection_signatures_candidate_region_merge_policy",
        },
        "GWAS trait model binary quantitative covariate PC multiple testing QTL overlap evidence": {
            "domain_association_mapping_trait_model_policy",
            "domain_association_mapping_covariate_pc_policy",
            "domain_association_mapping_multiple_testing_policy",
            "domain_association_mapping_qtl_overlap_evidence_policy",
        },
        "functional annotation coordinate liftover tissue relevance FarmGTEx single cell SV gene disruption": {
            "domain_functional_genomics_annotation_coordinate_liftover_check",
            "domain_functional_genomics_annotation_tissue_relevance_matrix",
            "domain_functional_genomics_annotation_sv_gene_disruption_policy",
        },
        "relationship matrix GRM QC A matrix H matrix REML convergence sparse relatedness": {
            "domain_relationship_matrix_grm_qc_prerequisites",
            "domain_relationship_matrix_a_matrix_h_matrix_boundary",
            "domain_relationship_matrix_reml_convergence_policy",
            "domain_relationship_matrix_sparse_relatedness_policy",
        },
        "genomic prediction training validation split multi breed model comparison deployment decision gate": {
            "domain_genomic_prediction_training_validation_split_policy",
            "domain_genomic_prediction_multi_breed_validation_policy",
            "domain_genomic_prediction_model_comparison_policy",
            "domain_genomic_prediction_deployment_decision_gate",
        },
        "species overlay cattle pig poultry sheep goat aquaculture defaults cautions": {
            "species_overlay_cattle_defaults",
            "species_overlay_pig_defaults",
            "species_overlay_poultry_defaults",
            "species_overlay_sheep_goat_defaults",
            "species_overlay_aquaculture_defaults",
        },
        "literature landmark method evidence matrix recent high impact dedup card update": {
            "literature_landmark_method_evidence_matrix",
            "literature_recent_high_impact_evidence_matrix",
            "literature_card_update_and_dedup_policy",
        },
        "remote shell execution review gate operational acceptance failure recovery report review traceability": {
            "sop_remote_shell_execution_review_gate",
            "evaluation_operational_acceptance_gate",
            "failure_recovery_decision_matrix",
            "template_report_review_completion_gate",
        },
        "retrieval regression query catalog index health chunk traceability evidence anchor source path": {
            "ontology_retrieval_regression_query_catalog",
            "ontology_index_health_check_policy",
            "ontology_chunk_traceability_review_gate",
        },
    }

    for query, expected_doc_ids in query_expectations.items():
        hits = index.search(query, limit=20)
        hit_doc_ids = {hit.chunk.doc_id for hit in hits}

        assert hits, query
        assert hit_doc_ids & expected_doc_ids, f"{query}: {hit_doc_ids}"


def test_content_completeness_retrieval_queries_cover_workflow_assets() -> None:
    index = ReferenceKnowledgeIndexer(REFERENCES_ROOT).build_index()

    for query, expected_doc_ids in CONTENT_COMPLETENESS_QUERIES.items():
        hits = index.search(query, limit=20)
        hit_doc_ids = {hit.chunk.doc_id for hit in hits}

        assert hits, query
        assert hit_doc_ids & expected_doc_ids, f"{query}: {hit_doc_ids}"


def test_references_do_not_contain_runtime_or_raw_data_artifacts() -> None:
    forbidden = [
        path.as_posix()
        for path in REFERENCES_ROOT.rglob("*")
        if path.is_file() and path.suffix.lower() in FORBIDDEN_REFERENCE_SUFFIXES
    ]

    assert forbidden == []
