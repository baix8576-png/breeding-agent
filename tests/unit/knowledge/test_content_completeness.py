from __future__ import annotations

import re
from pathlib import Path

from knowledge.indexing import ReferenceKnowledgeIndexer


REFERENCES = Path("references")
RECENT = REFERENCES / "papers" / "animal_genomics_recent_high_impact_2022_2026.md"
SCRIPT_ROOT = Path("scripts")
DOI_OR_PMID_PATTERN = re.compile(r"\b(10\.\d{4,9}/\S+|PMID\s*:?\s*\d{6,})\b", re.IGNORECASE)
URL_PATTERN = re.compile(r"https?://")
WORKFLOW_NAMES = {
    "association_mapping",
    "genotype_processing",
    "population_genetics",
    "quantitative_genetics",
    "reporting_audit",
}
EXPECTED_CONTENT_SOURCES = {
    "references/papers/literature_refresh_log_2026.md",
    "references/sop/association_mapping_execution_sop.md",
    "references/sop/genotype_processing_execution_sop.md",
    "references/sop/population_genetics_execution_sop.md",
    "references/sop/quantitative_genetics_execution_sop.md",
    "references/sop/reporting_audit_execution_sop.md",
}


def _recent_cards() -> list[str]:
    text = RECENT.read_text(encoding="utf-8")
    sections = re.split(r"(?=^## RECENT-\d+ )", text, flags=re.MULTILINE)
    return [section for section in sections if section.startswith("## RECENT-")]


def test_recent_literature_cards_have_required_card_fields() -> None:
    cards = _recent_cards()
    headings = [card.splitlines()[0] for card in cards]

    assert len(cards) >= 72
    assert len(headings) == len(set(headings))
    for section in cards:
        heading = section.splitlines()[0]
        doi_line = next(
            (line for line in section.splitlines() if line.startswith("- DOI/PMID:")),
            "",
        )
        source_line = next(
            (line for line in section.splitlines() if line.startswith("- Source links:")),
            "",
        )
        doi_value = doi_line.removeprefix("- DOI/PMID:").strip()
        source_value = source_line.removeprefix("- Source links:").strip()
        assert DOI_OR_PMID_PATTERN.search(doi_value), (heading, doi_value)
        assert URL_PATTERN.search(source_value), (heading, source_value)
        assert "- GeneAgent use:" in section, heading
        assert "- Boundary/risk:" in section, heading


def test_every_workflow_has_operation_guide_and_knowledge_bridge() -> None:
    guides = [SCRIPT_ROOT / name / "operation_guide.md" for name in sorted(WORKFLOW_NAMES)]
    guide_names = {path.parent.name for path in guides if path.exists()}

    assert WORKFLOW_NAMES <= guide_names
    missing_bridge_terms: dict[str, list[str]] = {}
    for path in guides:
        text = path.read_text(encoding="utf-8")
        missing = []
        if "references/sop/" not in text:
            missing.append("references/sop/")
        if "references/parameter_playbooks/" not in text:
            missing.append("references/parameter_playbooks/")
        if "Output contract" not in text and "output contract" not in text:
            missing.append("Output contract")
        if missing:
            missing_bridge_terms[path.as_posix()] = missing

    assert missing_bridge_terms == {}


def test_reference_index_has_content_depth_floor() -> None:
    result = ReferenceKnowledgeIndexer(REFERENCES).build()
    indexed_sources = set(result.manifest.sources)
    missing_sources = sorted(EXPECTED_CONTENT_SOURCES - indexed_sources)

    assert result.errors == []
    assert missing_sources == []
    assert result.manifest.doc_count >= 380
    assert result.manifest.chunk_count >= 380


def test_domain_execution_sops_are_indexed() -> None:
    result = ReferenceKnowledgeIndexer(REFERENCES).build()
    doc_ids = {item.doc_id for item in result.items}

    assert result.errors == []
    assert {
        "sop_genotype_processing_execution",
        "sop_population_genetics_execution",
        "sop_quantitative_genetics_execution",
        "sop_association_mapping_execution",
        "sop_reporting_audit_execution",
    } <= doc_ids
