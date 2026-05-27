from __future__ import annotations

from collections import Counter
from pathlib import Path

from knowledge.indexing import ReferenceKnowledgeIndexer


REFERENCES_ROOT = Path("references")
STANDARD_DIRECTORIES = {
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


def test_reference_layer_retrieval_queries_cover_major_topics() -> None:
    index = ReferenceKnowledgeIndexer(REFERENCES_ROOT).build_index()
    query_expectations = {
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
            "structure_pca_interpretation_policy",
            "structure_admixture_caution_policy",
            "structure_cluster_labeling_caution",
        },
        "GRM GBLUP ssGBLUP fixed random effects": {
            "modeling_gblup_route_guide",
            "modeling_ssgblup_boundary_guide",
            "modeling_fixed_random_effect_checklist",
        },
        "cross validation bias calibration subgroup validation": {
            "evaluation_cross_validation_patterns",
            "evaluation_bias_calibration_notes",
            "evaluation_subgroup_validation_policy",
        },
        "report_index audit bundle diagnostic report": {
            "template_report_index_v2",
            "template_audit_bundle",
            "template_diagnostic_report",
        },
        "scheduler QOS PBS qsub plink2 bcftools gcta failure": {
            "diagnostic_scheduler_slurm_qos_or_resource_limit",
            "diagnostic_scheduler_pbs_unknown_queue",
            "diagnostic_bio_tool_plink2_missing_bfile_triplet",
            "diagnostic_bio_tool_bcftools_not_bgzip_or_missing_index",
            "diagnostic_bio_tool_gcta_id_mismatch_between_inputs",
        },
    }

    for query, expected_doc_ids in query_expectations.items():
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
