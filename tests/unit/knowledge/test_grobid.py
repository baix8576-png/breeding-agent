from __future__ import annotations

from knowledge.grobid import GrobidTeiParser


def test_grobid_tei_parser_extracts_title_abstract_and_sections() -> None:
    tei_xml = """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader>
    <fileDesc>
      <titleStmt>
        <title>Efficient Methods to Compute Genomic Predictions</title>
      </titleStmt>
    </fileDesc>
    <profileDesc>
      <abstract>
        <p>Genomic relationship matrices support prediction of breeding values.</p>
      </abstract>
    </profileDesc>
  </teiHeader>
  <text>
    <body>
      <div>
        <head>Methods</head>
        <p>Compute allele-frequency centered marker relationships.</p>
      </div>
      <div>
        <head>Boundary</head>
        <p>Use with careful sample and marker quality control.</p>
      </div>
    </body>
  </text>
</TEI>
"""

    parsed = GrobidTeiParser().parse_text(
        tei_xml,
        doc_id="paper_grm_vanraden_2008",
        source_path="references/papers/raw_pdfs/vanraden_2008.pdf",
    )

    assert parsed.doc_id == "paper_grm_vanraden_2008"
    assert parsed.title == "Efficient Methods to Compute Genomic Predictions"
    assert "Genomic relationship matrices" in parsed.abstract
    assert [section.title for section in parsed.sections] == ["Methods", "Boundary"]
    assert parsed.sections[0].page_or_anchor == "#methods"
