from __future__ import annotations

import re
from pathlib import Path

from knowledge.indexing import ReferenceKnowledgeIndexer


CLASSIC_PACK = Path("references/papers/animal_genomics_classic_landmarks.md")
RECENT_PACK = Path("references/papers/animal_genomics_recent_high_impact_2022_2026.md")
SPECIES_INDEX = Path("references/papers/species_literature_index.md")
CURATION_POLICY = Path("references/ontology/literature_curation_policy.md")


def _build(paths: list[Path]):
    return ReferenceKnowledgeIndexer(Path("references")).build(paths=paths)


def test_literature_packs_parse_without_metadata_errors() -> None:
    result = _build([CLASSIC_PACK, RECENT_PACK, SPECIES_INDEX, CURATION_POLICY])

    assert result.errors == []
    assert result.manifest.metadata_schema == "knowledge_item.v2"
    assert result.manifest.doc_count >= 124
    assert result.manifest.chunk_count >= 124
    assert all(chunk.doc_id for chunk in result.chunks)
    assert all(chunk.source_path.startswith("references/") for chunk in result.chunks)
    assert all(chunk.page_or_anchor.startswith("#") for chunk in result.chunks)
    assert all(chunk.evidence_level.value for chunk in result.chunks)
    assert all(chunk.blueprint_scope.value for chunk in result.chunks)


def test_classic_and_recent_pack_sizes_match_curation_targets() -> None:
    classic = _build([CLASSIC_PACK])
    recent = _build([RECENT_PACK])

    assert classic.errors == []
    assert recent.errors == []
    assert classic.manifest.doc_count == 42
    assert recent.manifest.doc_count == 72


def test_literature_doc_ids_are_unique_across_references() -> None:
    result = ReferenceKnowledgeIndexer(Path("references")).build()
    doc_ids = [item.doc_id for item in result.items]

    assert result.errors == []
    assert len(doc_ids) == len(set(doc_ids))


def test_recent_pack_is_inside_2022_2026_window() -> None:
    text = RECENT_PACK.read_text(encoding="utf-8")
    years = [int(item) for item in re.findall(r"^- Year: (\d{4})\.", text, flags=re.MULTILINE)]

    assert len(years) == 72
    assert min(years) >= 2022
    assert max(years) <= 2026
    assert sum(1 for year in years if 2022 <= year <= 2026) / len(years) == 1.0


def test_public_knowledge_base_name_is_not_stage_named() -> None:
    checked_files = [Path("references/INDEX.md"), Path("references/papers/README.md"), CURATION_POLICY]
    text = "\n".join(path.read_text(encoding="utf-8") for path in checked_files)

    assert "GeneAgent 知识库" in text
    assert "V2 阶段功能知识库" not in text


def test_literature_retrieval_queries_hit_expected_evidence() -> None:
    index = ReferenceKnowledgeIndexer(Path("references")).build_index(
        paths=[
            Path("references/papers/genomic_prediction_core_papers_v1.md"),
            Path("references/papers/grm_core_papers_v1.md"),
            CLASSIC_PACK,
            RECENT_PACK,
        ]
    )

    query_expectations = {
        "genomic selection Meuwissen VanRaden GBLUP": {"paper_gp_meuwissen_2001", "paper_gp_vanraden_2008"},
        "single step GBLUP pedigree genomic relationship matrix": {
            "paper_classic_legarra_2009_relationship_matrix",
            "paper_classic_aguilar_2010_ssgblup",
        },
        "FarmGTEx pig cattle chicken regulatory variants": {
            "paper_recent_farmgtex_project_2025",
            "paper_recent_piggtex_2024",
            "paper_recent_chickengtex_2025",
        },
        "livestock pangenome structural variation breeding": {
            "paper_recent_domestic_animal_pangenome_review_2023",
            "paper_recent_livestock_structural_variation_review_2023",
        },
        "single-cell atlas cattle economic traits": {
            "paper_recent_cattle_single_cell_atlas_2025",
            "paper_recent_livestock_single_cell_review_2022",
        },
        "GWAS QTL selection signature livestock": {
            "paper_recent_livestock_qtl_database_2022",
            "paper_recent_livestock_selection_signature_review_2022",
        },
    }

    for query, expected_doc_ids in query_expectations.items():
        hits = index.search(query, limit=12)
        hit_doc_ids = {hit.chunk.doc_id for hit in hits}

        assert hits, query
        assert hit_doc_ids & expected_doc_ids, f"{query}: {hit_doc_ids}"
