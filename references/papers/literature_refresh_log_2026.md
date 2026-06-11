# Literature Refresh Log 2026

## B01 Recent Literature Refresh Protocol

```yaml
knowledge_item.v2:
  doc_id: literature_refresh_protocol_2026
  version: v2
  species: multi_species
  blueprint_scope: knowledge_governance
  evidence_level: sop
  source: paper
  updated_at: 2026-06-11T00:00:00+08:00
  owner: popgen_quantgen
```

Refresh rule: accepted cards must have concrete title, year, journal, DOI or PMID, and at least one official DOI/publisher/PubMed/Semantic Scholar source link. Google Scholar-only cards remain candidates and are not citation-export ready. No PDFs, raw full text, TEI, chunks, or index files are added by this log.

## B01 recent-card refresh batch, 2026-06-11

Sources checked: CrossRef REST metadata, PubMed E-utilities summaries, DOI landing pages through `https://doi.org/...`, and light Semantic Scholar search where rate limits allowed. Semantic Scholar returned HTTP 429 for most broad searches, so final acceptance relied on CrossRef/PubMed exact DOI-title-year-journal agreement.

### Refreshed Cards

| Card | Decision | Verified metadata | Sources | Notes |
|---|---|---|---|---|
| RECENT-09 | refreshed | Talenti et al., 2022, Nature Communications, DOI `10.1038/s41467-022-28605-0`, PMID `35177600` | CrossRef, PubMed, DOI | Exact title/year/journal match. |
| RECENT-10 | refreshed | Li et al., 2023, Nature Communications, DOI `10.1038/s41467-023-42161-1`, PMID `37857610` | CrossRef, PubMed, DOI | Exact title/year/journal match. |
| RECENT-11 | refreshed | Mapel et al., 2024, Nature Communications, DOI `10.1038/s41467-024-44935-7`, PMID `38253538` | CrossRef, PubMed, DOI | Exact title/year/journal match. |
| RECENT-12 | refreshed | Olagunju et al., 2024, Nature Communications, DOI `10.1038/s41467-024-52384-5`, PMID `39333471` | CrossRef, PubMed, DOI | Exact title/year/journal match. |
| RECENT-13 | refreshed | Tang et al., 2024, Nature Communications, DOI `10.1038/s41467-024-46434-1`, PMID `38461177` | CrossRef, PubMed, DOI | Exact title/year/journal match. |
| RECENT-14 | refreshed | Quan et al., 2024, Nature Communications, DOI `10.1038/s41467-024-49923-5`, PMID `38961076` | CrossRef, PubMed, DOI | Exact title/year/journal match. |
| RECENT-15 | refreshed | Li et al., 2023, Genome Research, DOI `10.1101/gr.277638.122`, PMID `37914227` | CrossRef, PubMed, DOI | Replaced broad pig pangenome placeholder with verified paper. |
| RECENT-16 | refreshed | Liu et al., 2023, Nature Communications, DOI `10.1038/s41467-023-41220-x`, PMID `37726270` | CrossRef, PubMed, DOI | Exact DOI candidate verified. |
| RECENT-17 | refreshed | Li et al., 2023, Genome Research, DOI `10.1101/gr.277372.122`, PMID `37310928` | CrossRef, PubMed, DOI | Exact sheep pangenome/tail phenotype match. |
| RECENT-18 | refreshed | Zhang et al., 2024, iMeta, DOI `10.1002/imt2.254`, PMID `39742295` | PubMed, CrossRef, DOI | PubMed search identified the sheep epigenome atlas. |
| RECENT-19 | refreshed | Bian et al., 2024, Molecular Biology and Evolution, DOI `10.1093/molbev/msae251`, PMID `39665690` | CrossRef, PubMed, DOI | Updated year/doc_id from candidate 2023 to verified 2024. |
| RECENT-20 | refreshed | Rice et al., 2023, BMC Biology, DOI `10.1186/s12915-023-01758-0`, PMID `37993882` | CrossRef, PubMed, DOI | Exact chicken pangenome graph match. |
| RECENT-21 | refreshed | Yu et al., 2023, GigaScience, DOI `10.1093/gigascience/giad016`, PMID `36971291` | PubMed, CrossRef, DOI | Reframed from pangenome candidate to verified duck resequencing/artificial selection paper. |
| RECENT-22 | refreshed | Liu and Gao, 2025, Marine Biotechnology, DOI `10.1007/s10126-025-10535-9`, PMID `41251872` | CrossRef, PubMed, DOI | Updated to verified fish reference genome/pangenome review within 2022-2026 scope. |
| RECENT-23 | refreshed | Ajasa et al., 2024, Genetics Selection Evolution, DOI `10.1186/s12711-024-00907-5`, PMID `38750427` | CrossRef, PubMed, DOI | Replaced 2022 placeholder with verified Atlantic salmon multi-population genomic prediction paper. |
| RECENT-25 | refreshed | Luo et al., 2024, Aquaculture, DOI `10.1016/j.aquaculture.2023.740376`, PMID `38826717` | CrossRef, PubMed, DOI | Exact shrimp growth-trait genomic selection match. |
| RECENT-26 | refreshed | Guillenea et al., 2022, Journal of Dairy Science, DOI `10.3168/jds.2021-21173`, PMID `35033341` | CrossRef, PubMed, DOI | Reframed from generic review to verified dairy breed-origin prediction paper. |
| RECENT-27 | refreshed | Hay, CrossRef online year 2025, Translational Animal Science, DOI `10.1093/tas/txaf166`, PMID `41551236` | CrossRef, PubMed, DOI | PubMed lists 2026 pubdate; card keeps CrossRef online year and log records the discrepancy. |
| RECENT-28 | refreshed | Ye et al., 2022, Frontiers in Genetics, DOI `10.3389/fgene.2022.843300`, PMID `35754827` | CrossRef, PubMed, DOI | Tier-2 journal; retained because topic match is exact and peer-reviewed. |
| RECENT-29 | refreshed | Ye et al., 2023, Poultry Science, DOI `10.1016/j.psj.2023.102549`, PMID `36907129` | CrossRef, PubMed, DOI | Exact poultry genomic prediction match. |
| RECENT-30 | refreshed | Araujo et al., 2023, Journal of Animal Breeding and Genetics, DOI `10.1111/jbg.12748`, PMID `36408677` | CrossRef, PubMed, DOI | Updated year from candidate 2022 to verified 2023. |
| RECENT-31 | refreshed | Negro et al., 2024, animal, DOI `10.1016/j.animal.2024.101118`, PMID `38508133` | PubMed, CrossRef, DOI | Verified goat genomic breeding-value comparison. |
| RECENT-32 | refreshed | Alemu et al., 2025, Genetics Selection Evolution, DOI `10.1186/s12711-025-00966-2`, PMID `40217496` | CrossRef, PubMed, DOI | Reframed from vague WGS prediction to verified functional-variant dairy prediction paper. |
| RECENT-33 | refreshed | Wang et al., 2024, animal, DOI `10.1016/j.animal.2024.101258`, PMID `39126800` | CrossRef, PubMed, DOI | Verified pig low-coverage WGS imputation/prediction/GWAS paper. |
| RECENT-35 | refreshed | Luan et al., 2023, Journal of Animal Breeding and Genetics, DOI `10.1111/jbg.12772`, PMID `37014360` | CrossRef, PubMed, DOI | Verified pig multi-trait genomic prediction paper. |
| RECENT-41 | refreshed | Madilindi et al., 2022, Livestock Science, DOI `10.1016/j.livsci.2022.104871` | CrossRef, DOI | Added to satisfy the B01 half-pack verified threshold without forcing low-confidence RECENT-24/34/36 matches. |
| RECENT-42 | refreshed | Worku, 2024, Animal Biotechnology, DOI `10.1080/10495398.2024.2362677`, PMID `38860914` | CrossRef, PubMed, DOI | Verified climate-impact trait genetics paper for methane-emission breeding context. |
| RECENT-70 | refreshed | Leonard et al., 2023, Genome Biology, DOI `10.1186/s13059-023-02969-y`, PMID `37217946` | CrossRef, PubMed, DOI | Verified bovine super-pangenome graph-methods paper for pangenome expansion boundary. |

### Deferred Candidate Cards

| Card | Decision | Reason | Next check |
|---|---|---|---|
| RECENT-24 | deferred | CrossRef/PubMed searches returned older Nile tilapia genomic selection papers or adjacent salinity/GWAS results, but no confident 2023 growth/disease genomic selection benchmark matching the card. | Re-query with species-specific authors or Zotero; do not export citation until DOI/PMID is verified. |
| RECENT-34 | deferred | CrossRef returned WCGALP proceedings and older multi-breed prediction papers, not a peer-reviewed 2022-2026 livestock journal article matching the broad card. | Search targeted cattle/pig/sheep multi-breed studies or accept a proceedings card only if the evidence policy permits it. |
| RECENT-36 | deferred | Searches returned human/plant deep-learning genomics, preprints, MDPI/low-priority hits, or generic machine-learning papers without a strong livestock genomic-prediction benchmark match. | Re-screen with animal-breeding-specific terms and avoid low-quality or preprint-only substitutes. |

## B08 non-export candidate audit, 2026-06-11

```yaml
knowledge_item.v2:
  doc_id: literature_b08_non_export_candidate_audit
  version: v2
  species: multi_species
  blueprint_scope: knowledge_governance
  evidence_level: sop
  source: paper
  updated_at: 2026-06-11T00:00:00+08:00
  owner: popgen_quantgen
```

Audit decision: remaining broad recent-literature candidates are kept in the GeneAgent knowledge base only as non-export retrieval leads. They may support gap detection and future curation planning, but they must not be exported as formal citations, used as peer-reviewed evidence, or presented in reports as verified papers until a curator records a DOI, PMID, publisher page, or equivalent authoritative metadata source.

### B08 Candidate Status Table

| Cards | Status | Reason | Required promotion evidence |
|---|---|---|---|
| RECENT-24 | non-export candidate | Nile tilapia genomic selection lead remains broad and may map to multiple growth, disease, salinity, or farm-benchmark papers. | Exact title, year, journal, DOI or PMID, and a publisher/PubMed/CrossRef source. |
| RECENT-34, RECENT-36, RECENT-37, RECENT-38, RECENT-39, RECENT-40 | non-export candidate | Genomic-prediction leads are method-family placeholders; several adjacent papers exist, but the exact livestock benchmark is not pinned to citation-grade metadata. | Verified peer-reviewed article, species, trait, validation design, DOI/PMID, and source links. |
| RECENT-43, RECENT-44, RECENT-45, RECENT-46 | non-export candidate | GWAS species leads are intentionally broad and would be misleading if treated as one paper. | One selected high-quality study per species with trait, sample size, model, DOI/PMID, and publisher/PubMed source. |
| RECENT-47, RECENT-48, RECENT-49 | non-export candidate | QTL, fine-mapping, and eQTL integration leads need more precise database/review selection before citation export. | Authoritative database update or review with DOI/PMID and clear scope. |
| RECENT-50, RECENT-51, RECENT-52, RECENT-53 | non-export candidate | Single-cell leads remain useful for retrieval planning, but exact livestock atlas papers must be selected by species and tissue context. | Verified atlas paper or review with species, tissue, year, DOI/PMID, and source links. |
| RECENT-54, RECENT-55 | non-export candidate | Multi-omics and epigenomics leads need stricter screening to avoid review-quality drift. | High-quality review or representative study with DOI/PMID and explicit animal-breeding relevance. |
| RECENT-56, RECENT-57, RECENT-58, RECENT-59, RECENT-60 | non-export candidate | Adaptation and domestication leads are population- and trait-specific; broad candidate wording is not citation-grade. | Species-specific paper with validated population sampling, method, DOI/PMID, and source links. |
| RECENT-61, RECENT-62, RECENT-63, RECENT-64 | non-export candidate | Imputation/phasing benchmark leads need one exact livestock benchmark per technology and species. | Verified benchmark with input density, reference-panel design, DOI/PMID, and source links. |
| RECENT-65, RECENT-66, RECENT-67, RECENT-68, RECENT-69 | non-export candidate | ROH, LD decay, effective-population-size, selection-signature, and structural-variation review leads remain method coverage placeholders. | Curated landmark/recent review or benchmark with DOI/PMID and explicit method boundary. |
| RECENT-71, RECENT-72 | non-export candidate | AI-genomics and knowledge-graph leads are emerging-topic placeholders and require extra screening for source quality. | High-quality peer-reviewed article or review with DOI/PMID, source links, and clear animal-genomics scope. |

### B08 Use Boundary

- GeneAgent may retrieve these candidate cards to explain that a topic needs curation before citation export.
- GeneAgent must prefer verified cards with `evidence_level: peer_reviewed` and `source: paper` for report claims, manuscript citation lists, and parameter recommendations.
- A future refresh may promote a candidate only by updating the card metadata, replacing the non-export DOI/PMID line with verified identifiers, and adding the accepted source to this log.
