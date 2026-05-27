# GROBID PDF Ingestion SOP

## GROBID PDF ingestion SOP metadata

```yaml
knowledge_item.v2:
  doc_id: sop_grobid_pdf_ingestion
  version: v2
  species: multi_species
  blueprint_scope: shared
  evidence_level: sop
  source: sop
  updated_at: 2026-05-26T00:00:00Z
  owner: llm_orchestrator
```

This SOP governs local PDF ingestion for literature card enrichment. Raw PDFs are not committed to Git. They may be stored under `.geneagent/knowledge/raw_pdfs/` and linked to Git-versioned summary cards through `doc_id`.

## Input and output boundary

Inputs:
- local PDF paths under approved local or cluster storage
- optional DOI, PMID, CorpusID, or manual citation metadata
- target `doc_id` for the corresponding literature card

Outputs:
- GROBID TEI XML under `.geneagent/knowledge/grobid_tei/`
- extracted text under `.geneagent/knowledge/extracted_text/`
- candidate chunks under `.geneagent/knowledge/chunks/`
- reviewed summary card updates under `references/papers/`

Do not put raw PDF, TEI, extracted full text, or embedding index files into Git unless a separate copyright and privacy review explicitly permits a small derived summary.

## Processing workflow

1. Confirm the PDF source and local storage boundary.
2. Run GROBID `processFulltextDocument` or an equivalent local parser.
3. Extract title, abstract, body section headings, references, DOI, and PMID when available.
4. Draft a card summary with method use, scope, parameter relevance, and risk boundary.
5. Validate `knowledge_item.v2` metadata before adding the reviewed summary to `references/papers/`.

## Quality gate

Minimum acceptance:
- citation metadata is sufficient to identify the work
- source link, DOI, PMID, or publisher page is recorded when available
- summary avoids long copyrighted excerpts
- risk boundary and GeneAgent use are explicit
- metadata validates through the reference indexer

If parsing fails, record the failure class in `references/failure_cases/` or diagnostics rather than silently producing a low-quality card.
