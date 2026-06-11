# Animal Genomics Recent High-Impact Papers (2022-2026)

This pack seeds GeneAgent knowledge retrieval with recent animal genomics literature anchors. Papers marked "verify before citation export" are accepted for internal retrieval and planning, but their DOI/PMID should be refreshed through CrossRef, PubMed, Semantic Scholar, or Zotero before manuscript-grade citation output.

## Recent high impact evidence matrix

```yaml
knowledge_item.v2:
  doc_id: literature_recent_high_impact_evidence_matrix
  version: v2
  species: multi_species
  blueprint_scope: knowledge_governance
  evidence_level: sop
  source: paper
  updated_at: 2026-06-06T21:30:00+08:00
  owner: popgen_quantgen
```

This matrix maps 2022-2026 high-impact literature cards to GeneAgent interpretation layers. It is for retrieval and report planning; citation exports must still refresh DOI/PMID and publisher metadata.

| Evidence family | Typical recent anchors | GeneAgent use |
|---|---|---|
| FarmGTEx and species GTEx atlases | FarmGTEx, PigGTEx, ChickenGTEx, cattle regulatory atlas | tissue eQTL, regulatory variant, and candidate-gene context |
| single-cell atlases | cattle and other livestock single-cell resources | cell-type relevance and tissue-context labels |
| pangenome and T2T assemblies | bovine pangenome, indicine diversity, domestic animal pangenome reviews | SV/CNV and reference-bias caveats |
| WGS and multi-omics prediction | WGS prediction, regulatory-feature prediction, multi-omics breeding papers | model feature evidence and validation caution |
| adaptation and disease resistance | climate/adaptation, immunity, disease-resistance studies | selection-scan interpretation and species overlays |
| species-focused resources | cattle, pig, poultry, sheep/goat, aquaculture papers | species-specific retrieval and report defaults |

Use rules:
- Use recent cards to update functional interpretation and species context.
- Keep resource papers separate from cohort-specific validation.
- Do not transfer evidence across species without marking it indirect.
- Require `verify before citation export` review when a card was accepted for internal planning but not refreshed for manuscript use.

Risk boundary: high-impact resource papers are strong context, but they do not automatically validate a user's cohort, trait, or candidate locus.

## RECENT-01 FarmGTEx project overview
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_farmgtex_project_2025"
  version: "v2"
  species: "multi_species"
  blueprint_scope: knowledge_governance
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-26T20:10:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: FarmGTEx Project. *Animal genetic resources meet their genomes* / FarmGTEx project overview.
- Year: 2025.
- DOI/PMID: DOI `10.1038/s41588-025-02121-5`.
- Species/data: multi-species livestock functional genomics.
- GeneAgent use: top-level anchor for expression regulation, multi-tissue annotation, and genotype-to-phenotype evidence.
- Boundary/risk: high-level resource paper; downstream use must cite species-specific companion papers.
- Source links: [Nature Genetics](https://www.nature.com/articles/s41588-025-02121-5)

## RECENT-02 PigGTEx regulatory variants
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_piggtex_2024"
  version: "v2"
  species: "sus_scrofa"
  blueprint_scope: knowledge_governance
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-26T20:10:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: PigGTEx Consortium. *The PigGTEx atlas links regulatory variants to complex traits in pigs*.
- Year: 2024.
- DOI/PMID: DOI `10.1038/s41588-023-01585-7`.
- Species/data: pig multi-tissue expression and eQTL.
- GeneAgent use: pig functional annotation and candidate regulatory variant interpretation.
- Boundary/risk: trait transfer to non-pig species is not valid without homologous evidence.
- Source links: [Nature Genetics](https://www.nature.com/articles/s41588-023-01585-7)

## RECENT-03 ChickenGTEx regulatory variants
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_chickengtex_2025"
  version: "v2"
  species: "gallus_gallus"
  blueprint_scope: knowledge_governance
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-26T20:10:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: ChickenGTEx Consortium. *ChickenGTEx links regulatory variants to complex traits in chickens*.
- Year: 2025.
- DOI/PMID: DOI `10.1038/s41588-025-02155-9`.
- Species/data: chicken multi-tissue expression and eQTL.
- GeneAgent use: poultry trait interpretation and regulatory evidence retrieval.
- Boundary/risk: resource is not a replacement for project-specific phenotype validation.
- Source links: [Nature Genetics](https://www.nature.com/articles/s41588-025-02155-9)

## RECENT-04 Cattle single-cell atlas
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_cattle_single_cell_atlas_2025"
  version: "v2"
  species: "bos_taurus"
  blueprint_scope: knowledge_governance
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-26T20:10:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: FarmGTEx cattle single-cell atlas team. *A multi-tissue single-cell transcriptomic atlas of cattle*.
- Year: 2025.
- DOI/PMID: DOI `10.1038/s41588-025-02329-5`.
- Species/data: cattle single-cell transcriptomics.
- GeneAgent use: cell-type context for trait-associated genes and tissue specificity.
- Boundary/risk: single-cell evidence is functional interpretation support, not direct breeding value evidence.
- Source links: [Nature Genetics](https://www.nature.com/articles/s41588-025-02329-5)

## RECENT-05 Cattle regulatory atlas
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_cattle_regulatory_atlas_2022"
  version: "v2"
  species: "bos_taurus"
  blueprint_scope: knowledge_governance
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-26T20:10:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: CattleGTEx/resource authors. *A multi-tissue atlas of regulatory variants in cattle*.
- Year: 2022.
- DOI/PMID: DOI `10.1038/s41588-022-01153-5`.
- Species/data: cattle eQTL and regulatory genomics.
- GeneAgent use: cattle candidate gene and regulatory-variant evidence.
- Boundary/risk: regulatory associations require tissue and trait context.
- Source links: [Nature Genetics](https://www.nature.com/articles/s41588-022-01153-5)

## RECENT-06 Bovine pangenome structural variation
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_bovine_pangenome_sv_2022"
  version: "v2"
  species: "bos_taurus"
  blueprint_scope: knowledge_governance
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-26T20:10:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: *A bovine pangenome representation of structural variation*.
- Year: 2022.
- DOI/PMID: DOI `10.1038/s41467-022-30680-2`.
- Species/data: cattle pangenome and structural variation.
- GeneAgent use: explains why reference-bias and SV-aware interpretation matter for cattle genomics.
- Boundary/risk: current GeneAgent core blueprints remain SNP/VCF-centered.
- Source links: [Nature Communications](https://www.nature.com/articles/s41467-022-30680-2)

## RECENT-07 Indicine cattle diversity
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_indicine_cattle_diversity_2023"
  version: "v2"
  species: "bos_indicus"
  blueprint_scope: population_genetics
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-26T20:10:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: *Whole-genome diversity and selection signatures in indicine cattle*.
- Year: 2023.
- DOI/PMID: DOI `10.1038/s41467-023-43626-z`.
- Species/data: indicine cattle genomes.
- GeneAgent use: breed diversity, adaptation, and PCA/selection-signature context.
- Boundary/risk: not a universal cattle reference for taurine breeds.
- Source links: [Nature Communications](https://www.nature.com/articles/s41467-023-43626-z)

## RECENT-08 Domestic animal pangenome review
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_domestic_animal_pangenome_review_2023"
  version: "v2"
  species: "multi_species"
  blueprint_scope: knowledge_governance
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-26T20:10:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: *Pangenomes in domestic animals: progress and applications*.
- Year: 2023.
- DOI/PMID: DOI `10.1186/s40104-023-00860-1`.
- Species/data: domestic animal pangenomes.
- GeneAgent use: roadmap for graph genomes, SV-aware annotation, and future V2.x expansion.
- Boundary/risk: review article; primary species papers should support concrete claims.
- Source links: [Journal of Animal Science and Biotechnology](https://link.springer.com/article/10.1186/s40104-023-00860-1)

## RECENT-09 Cattle graph genome diversity
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_cattle_graph_genome_2022"
  version: "v2"
  species: "bos_taurus"
  blueprint_scope: knowledge_governance
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-06-11T00:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Talenti et al. *A cattle graph genome incorporating global breed diversity*.
- Year: 2022.
- Journal: Nature Communications.
- DOI/PMID: DOI `10.1038/s41467-022-28605-0`; PMID `35177600`.
- Species/data: cattle pangenome/graph genome.
- GeneAgent use: reference-bias caution for cross-breed cattle analyses.
- Boundary/risk: graph-genome workflows are not yet core GeneAgent execution paths.
- Source links: [DOI](https://doi.org/10.1038/s41467-022-28605-0); [PubMed](https://pubmed.ncbi.nlm.nih.gov/35177600/)

## RECENT-10 De novo cattle immune variation
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_cattle_immune_variation_2023"
  version: "v2"
  species: "bos_taurus"
  blueprint_scope: knowledge_governance
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-06-11T00:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Li et al. *De novo genome assembly depicts the immune genomic characteristics of cattle*.
- Year: 2023.
- Journal: Nature Communications.
- DOI/PMID: DOI `10.1038/s41467-023-42161-1`; PMID `37857610`.
- Species/data: cattle genome assembly and immune loci.
- GeneAgent use: immune-trait candidate region interpretation.
- Boundary/risk: assembly-level evidence requires marker-liftover caution.
- Source links: [DOI](https://doi.org/10.1038/s41467-023-42161-1); [PubMed](https://pubmed.ncbi.nlm.nih.gov/37857610/)

## RECENT-11 Cattle male fertility methylation QTL
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_cattle_fertility_mqtl_2024"
  version: "v2"
  species: "bos_taurus"
  blueprint_scope: knowledge_governance
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-06-11T00:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Mapel et al. *Molecular quantitative trait loci in reproductive tissues impact male fertility in cattle*.
- Year: 2024.
- Journal: Nature Communications.
- DOI/PMID: DOI `10.1038/s41467-024-44935-7`; PMID `38253538`.
- Species/data: cattle fertility, methylation QTL.
- GeneAgent use: multi-omics trait interpretation for fertility phenotypes.
- Boundary/risk: methylation evidence is context and tissue dependent.
- Source links: [DOI](https://doi.org/10.1038/s41467-024-44935-7); [PubMed](https://pubmed.ncbi.nlm.nih.gov/38253538/)

## RECENT-12 Cattle sheep telomere-to-telomere sex chromosome
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_ruminant_t2t_y_2024"
  version: "v2"
  species: "multi_species"
  blueprint_scope: knowledge_governance
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-06-11T00:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Olagunju et al. *Telomere-to-telomere assemblies of cattle and sheep Y-chromosomes uncover divergent structure and gene content*.
- Year: 2024.
- Journal: Nature Communications.
- DOI/PMID: DOI `10.1038/s41467-024-52384-5`; PMID `39333471`.
- Species/data: cattle/sheep long-read assemblies.
- GeneAgent use: long-read assembly and sex-chromosome caveats for future expansion.
- Boundary/risk: outside current SNP-chip core blueprints.
- Source links: [DOI](https://doi.org/10.1038/s41467-024-52384-5); [PubMed](https://pubmed.ncbi.nlm.nih.gov/39333471/)

## RECENT-13 Cattle endogenous retrovirus GWAS
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_cattle_erv_gwas_2024"
  version: "v2"
  species: "bos_taurus"
  blueprint_scope: knowledge_governance
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-06-11T00:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Tang et al. *GWAS reveals determinants of mobilization rate and dynamics of an active endogenous retrovirus of cattle*.
- Year: 2024.
- Journal: Nature Communications.
- DOI/PMID: DOI `10.1038/s41467-024-46434-1`; PMID `38461177`.
- Species/data: cattle structural/retroviral variation.
- GeneAgent use: explains non-SNP variation affecting trait interpretation.
- Boundary/risk: requires specialized SV/ERV calling.
- Source links: [DOI](https://doi.org/10.1038/s41467-024-46434-1); [PubMed](https://pubmed.ncbi.nlm.nih.gov/38461177/)

## RECENT-14 Hybrid pig allele-specific regulation
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_hybrid_pig_allele_specific_2024"
  version: "v2"
  species: "sus_scrofa"
  blueprint_scope: knowledge_governance
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-06-11T00:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Quan et al. *Multi-omic characterization of allele-specific regulatory variation in hybrid pigs*.
- Year: 2024.
- Journal: Nature Communications.
- DOI/PMID: DOI `10.1038/s41467-024-49923-5`; PMID `38961076`.
- Species/data: pig hybrids, expression regulation.
- GeneAgent use: heterosis/regulatory interpretation in pig breeding context.
- Boundary/risk: not a direct prediction-model benchmark.
- Source links: [DOI](https://doi.org/10.1038/s41467-024-49923-5); [PubMed](https://pubmed.ncbi.nlm.nih.gov/38961076/)

## RECENT-15 Pig pangenome selection signatures
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_pig_pangenome_selection_2023"
  version: "v2"
  species: "sus_scrofa"
  blueprint_scope: population_genetics
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-06-11T00:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Li et al. *The pig pangenome provides insights into the roles of coding structural variations in genetic diversity and adaptation*.
- Year: 2023.
- Journal: Genome Research.
- DOI/PMID: DOI `10.1101/gr.277638.122`; PMID `37914227`.
- Species/data: pig pangenome, population structure.
- GeneAgent use: pig diversity, introgression, and structural-variant context.
- Boundary/risk: pangenome calling is not part of current QC pipeline.
- Source links: [DOI](https://doi.org/10.1101/gr.277638.122); [PubMed](https://pubmed.ncbi.nlm.nih.gov/37914227/)

## RECENT-16 Yak structural variation adaptation
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_yak_sv_adaptation_2023"
  version: "v2"
  species: "bos_grunniens"
  blueprint_scope: population_genetics
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-06-11T00:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Liu et al. *Evolutionary origin of genomic structural variations in domestic yaks*.
- Year: 2023.
- Journal: Nature Communications.
- DOI/PMID: DOI `10.1038/s41467-023-41220-x`; PMID `37726270`.
- Species/data: yak genomes and adaptation.
- GeneAgent use: adaptation and selection-signature explanation for ruminants.
- Boundary/risk: yak-specific signals should not be generalized to cattle without evidence.
- Source links: [DOI](https://doi.org/10.1038/s41467-023-41220-x); [PubMed](https://pubmed.ncbi.nlm.nih.gov/37726270/)

## RECENT-17 Sheep pangenome tail phenotype
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_sheep_pangenome_tail_2023"
  version: "v2"
  species: "ovis_aries"
  blueprint_scope: population_genetics
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-06-11T00:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Li et al. *A sheep pangenome reveals the spectrum of structural variations and their effects on tail phenotypes*.
- Year: 2023.
- Journal: Genome Research.
- DOI/PMID: DOI `10.1101/gr.277372.122`; PMID `37310928`.
- Species/data: sheep pangenome and phenotype-associated variation.
- GeneAgent use: sheep breed diversity and phenotype interpretation.
- Boundary/risk: phenotype-specific claims require original trait definitions.
- Source links: [DOI](https://doi.org/10.1101/gr.277372.122); [PubMed](https://pubmed.ncbi.nlm.nih.gov/37310928/)

## RECENT-18 Sheep regulatory element atlas
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_sheep_regulatory_atlas_2024"
  version: "v2"
  species: "ovis_aries"
  blueprint_scope: knowledge_governance
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-06-11T00:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Zhang et al. *Comprehensive multi-tissue epigenome atlas in sheep: A resource for complex traits, domestication, and breeding*.
- Year: 2024.
- Journal: iMeta.
- DOI/PMID: DOI `10.1002/imt2.254`; PMID `39742295`.
- Species/data: sheep functional genomics.
- GeneAgent use: sheep trait-candidate gene annotation.
- Boundary/risk: regulatory annotations are tissue/stage specific.
- Source links: [DOI](https://doi.org/10.1002/imt2.254); [PubMed](https://pubmed.ncbi.nlm.nih.gov/39742295/)

## RECENT-19 Goat pangenome diversity
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_goat_pangenome_diversity_2024"
  version: "v2"
  species: "capra_hircus"
  blueprint_scope: population_genetics
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-06-11T00:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Bian et al. *A Graph-based Goat Pangenome Reveals Structural Variations Involved in Domestication and Adaptation*.
- Year: 2024.
- Journal: Molecular Biology and Evolution.
- DOI/PMID: DOI `10.1093/molbev/msae251`; PMID `39665690`.
- Species/data: goat genomes and structural variants.
- GeneAgent use: goat diversity and reference-bias context.
- Boundary/risk: verify assembly quality and breed sampling before use.
- Source links: [DOI](https://doi.org/10.1093/molbev/msae251); [PubMed](https://pubmed.ncbi.nlm.nih.gov/39665690/)

## RECENT-20 Chicken pangenome structural variation
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_chicken_pangenome_sv_2023"
  version: "v2"
  species: "gallus_gallus"
  blueprint_scope: population_genetics
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-06-11T00:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Rice et al. *A pangenome graph reference of 30 chicken genomes allows genotyping of large and complex structural variants*.
- Year: 2023.
- Journal: BMC Biology.
- DOI/PMID: DOI `10.1186/s12915-023-01758-0`; PMID `37993882`.
- Species/data: chicken pangenome and population structure.
- GeneAgent use: poultry reference-bias and structural variant interpretation.
- Boundary/risk: current workflows remain SNP-oriented.
- Source links: [DOI](https://doi.org/10.1186/s12915-023-01758-0); [PubMed](https://pubmed.ncbi.nlm.nih.gov/37993882/)

## RECENT-21 Duck resequencing and artificial selection
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_duck_selection_resequencing_2023"
  version: "v2"
  species: "anas_platyrhynchos"
  blueprint_scope: population_genetics
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-06-11T00:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Yu et al. *Resequencing of a Pekin duck breeding population provides insights into the genomic response to short-term artificial selection*.
- Year: 2023.
- Journal: GigaScience.
- DOI/PMID: DOI `10.1093/gigascience/giad016`; PMID `36971291`.
- Species/data: duck population resequencing and artificial selection.
- GeneAgent use: poultry comparative genomics and domestication interpretation.
- Boundary/risk: include only after species-specific QC standards are confirmed.
- Source links: [DOI](https://doi.org/10.1093/gigascience/giad016); [PubMed](https://pubmed.ncbi.nlm.nih.gov/36971291/)

## RECENT-22 Fish reference genome and pangenome aquaculture review
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_fish_pangenome_aquaculture_2025"
  version: "v2"
  species: "aquaculture_multi_species"
  blueprint_scope: knowledge_governance
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-06-11T00:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Liu and Gao. *Current State of Fish Reference Genome and Pangenome: Methodologies, Sampling Strategies, Quality Assessment and Future Perspectives to Aquaculture Breeding*.
- Year: 2025.
- Journal: Marine Biotechnology.
- DOI/PMID: DOI `10.1007/s10126-025-10535-9`; PMID `41251872`.
- Species/data: aquaculture genomes.
- GeneAgent use: future aquaculture support and pangenome-aware marker interpretation.
- Boundary/risk: heterogeneous species; avoid one-size-fits-all defaults.
- Source links: [DOI](https://doi.org/10.1007/s10126-025-10535-9); [PubMed](https://pubmed.ncbi.nlm.nih.gov/41251872/)

## RECENT-23 Atlantic salmon multi-population genomic prediction
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_salmon_genomic_selection_2024"
  version: "v2"
  species: "salmo_salar"
  blueprint_scope: quantitative_genetics
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-06-11T00:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Ajasa et al. *Accuracy of genomic prediction using multiple Atlantic salmon populations*.
- Year: 2024.
- Journal: Genetics Selection Evolution.
- DOI/PMID: DOI `10.1186/s12711-024-00907-5`; PMID `38750427`.
- Species/data: salmon breeding populations.
- GeneAgent use: aquaculture genomic prediction design and validation caveats.
- Boundary/risk: effective population size and family structure differ from terrestrial livestock.
- Source links: [DOI](https://doi.org/10.1186/s12711-024-00907-5); [PubMed](https://pubmed.ncbi.nlm.nih.gov/38750427/)

## RECENT-24 Tilapia genomic selection benchmark
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_tilapia_genomic_selection_2023"
  version: "v2"
  species: "oreochromis_niloticus"
  blueprint_scope: quantitative_genetics
  evidence_level: "expert_opinion"
  source: "internal_note"
  updated_at: "2026-06-11T00:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Candidate Nile tilapia genomic selection benchmark for growth or disease traits.
- Year: 2023.
- DOI/PMID: DOI to verify before citation export.
- Species/data: tilapia breeding.
- GeneAgent use: aquaculture prediction validation and family leakage cautions.
- Boundary/risk: not yet part of the four production blueprints.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=Nile+tilapia+genomic+selection+benchmark+2023)

## RECENT-25 Shrimp genomic selection benchmark
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_shrimp_genomic_selection_2024"
  version: "v2"
  species: "litopenaeus_vannamei"
  blueprint_scope: quantitative_genetics
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-06-11T00:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Luo et al. *Evaluation of machine learning method in genomic selection for growth traits of Pacific white shrimp*.
- Year: 2024.
- Journal: Aquaculture.
- DOI/PMID: DOI `10.1016/j.aquaculture.2023.740376`; PMID `38826717`.
- Species/data: shrimp breeding.
- GeneAgent use: aquaculture prediction workflow expansion planning.
- Boundary/risk: crustacean genome structure and family designs differ from livestock.
- Source links: [DOI](https://doi.org/10.1016/j.aquaculture.2023.740376); [PubMed](https://pubmed.ncbi.nlm.nih.gov/38826717/)

## RECENT-26 Dairy cattle breed-origin genomic prediction
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_dairy_genomic_prediction_breed_origin_2022"
  version: "v2"
  species: "bos_taurus"
  blueprint_scope: quantitative_genetics
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-06-11T00:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Guillenea et al. *Genomic prediction in Nordic Red dairy cattle considering breed origin of alleles*.
- Year: 2022.
- Journal: Journal of Dairy Science.
- DOI/PMID: DOI `10.3168/jds.2021-21173`; PMID `35033341`.
- Species/data: dairy cattle.
- GeneAgent use: production genomic prediction operation and rolling reference panel context.
- Boundary/risk: dairy-specific; beef and small ruminant transfer needs validation.
- Source links: [DOI](https://doi.org/10.3168/jds.2021-21173); [PubMed](https://pubmed.ncbi.nlm.nih.gov/35033341/)

## RECENT-27 Beef cattle genomic marker prioritization
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_beef_genomic_prediction_marker_priority_2025"
  version: "v2"
  species: "bos_taurus"
  blueprint_scope: quantitative_genetics
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-06-11T00:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Hay. *Prioritization of SNP markers for genomic prediction in closed beef cattle populations*.
- Year: 2025.
- Journal: Translational Animal Science.
- DOI/PMID: DOI `10.1093/tas/txaf166`; PMID `41551236`.
- Species/data: beef cattle.
- GeneAgent use: validation-fold design and trait-specific accuracy expectations.
- Boundary/risk: breed composition and relatedness leakage are major risks.
- Source links: [DOI](https://doi.org/10.1093/tas/txaf166); [PubMed](https://pubmed.ncbi.nlm.nih.gov/41551236/)

## RECENT-28 Pig LD-haplotype genomic prediction
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_pig_haplotype_genomic_prediction_2022"
  version: "v2"
  species: "sus_scrofa"
  blueprint_scope: quantitative_genetics
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-06-11T00:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Ye et al. *Genomic Prediction Using LD-Based Haplotypes in Combined Pig Populations*.
- Year: 2022.
- Journal: Frontiers in Genetics.
- DOI/PMID: DOI `10.3389/fgene.2022.843300`; PMID `35754827`.
- Species/data: pig breeding.
- GeneAgent use: pig cross-line prediction and selection-index context.
- Boundary/risk: terminal/commercial line design may not transfer to nucleus populations.
- Source links: [DOI](https://doi.org/10.3389/fgene.2022.843300); [PubMed](https://pubmed.ncbi.nlm.nih.gov/35754827/)

## RECENT-29 Poultry haplotype genomic prediction
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_poultry_haplotype_prediction_2023"
  version: "v2"
  species: "gallus_gallus"
  blueprint_scope: quantitative_genetics
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-06-11T00:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Ye et al. *Haplotype analysis of genomic prediction by incorporating genomic pathway information based on high-density SNP marker in Chinese yellow-feathered chicken*.
- Year: 2023.
- Journal: Poultry Science.
- DOI/PMID: DOI `10.1016/j.psj.2023.102549`; PMID `36907129`.
- Species/data: chicken breeding.
- GeneAgent use: poultry high-selection-intensity and family-structure caveats.
- Boundary/risk: commercial data structures are often proprietary and not reproducible.
- Source links: [DOI](https://doi.org/10.1016/j.psj.2023.102549); [PubMed](https://pubmed.ncbi.nlm.nih.gov/36907129/)

## RECENT-30 Sheep genomic prediction benchmark
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_sheep_genomic_prediction_benchmark_2022"
  version: "v2"
  species: "ovis_aries"
  blueprint_scope: quantitative_genetics
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-06-11T00:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Araujo et al. *SNP- and haplotype-based single-step genomic predictions for body weight, wool, and reproductive traits in North American Rambouillet sheep*.
- Year: 2023.
- Journal: Journal of Animal Breeding and Genetics.
- DOI/PMID: DOI `10.1111/jbg.12748`; PMID `36408677`.
- Species/data: sheep breeding.
- GeneAgent use: small-ruminant prediction and cross-flock validation context.
- Boundary/risk: breed diversity and flock structure can reduce transfer accuracy.
- Source links: [DOI](https://doi.org/10.1111/jbg.12748); [PubMed](https://pubmed.ncbi.nlm.nih.gov/36408677/)

## RECENT-31 Goat genomic breeding values
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_goat_genomic_breeding_values_2024"
  version: "v2"
  species: "capra_hircus"
  blueprint_scope: quantitative_genetics
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-06-11T00:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Negro et al. *A comparison of genetic and genomic breeding values in Saanen and Alpine goats*.
- Year: 2024.
- Journal: animal.
- DOI/PMID: DOI `10.1016/j.animal.2024.101118`; PMID `38508133`.
- Species/data: goat breeding.
- GeneAgent use: small-ruminant reference-population design.
- Boundary/risk: low reference-population size can dominate accuracy.
- Source links: [DOI](https://doi.org/10.1016/j.animal.2024.101118); [PubMed](https://pubmed.ncbi.nlm.nih.gov/38508133/)

## RECENT-32 Functional-variant genomic prediction in dairy cattle
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_dairy_functional_variant_prediction_2025"
  version: "v2"
  species: "bos_taurus"
  blueprint_scope: quantitative_genetics
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-06-11T00:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Alemu et al. *Comparison of genomic prediction accuracies in dairy cattle lactation traits using five classes of functional variants versus generic SNP*.
- Year: 2025.
- Journal: Genetics Selection Evolution.
- DOI/PMID: DOI `10.1186/s12711-025-00966-2`; PMID `40217496`.
- Species/data: WGS cattle prediction.
- GeneAgent use: WGS vs SNP-chip marker-density interpretation.
- Boundary/risk: WGS accuracy gains are trait/population dependent.
- Source links: [DOI](https://doi.org/10.1186/s12711-025-00966-2); [PubMed](https://pubmed.ncbi.nlm.nih.gov/40217496/)

## RECENT-33 WGS prediction in pigs
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_wgs_prediction_pig_2024"
  version: "v2"
  species: "sus_scrofa"
  blueprint_scope: quantitative_genetics
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-06-11T00:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Wang et al. *Imputation strategies for low-coverage whole-genome sequencing data and their effects on genomic prediction and genome-wide association studies in pigs*.
- Year: 2024.
- Journal: animal.
- DOI/PMID: DOI `10.1016/j.animal.2024.101258`; PMID `39126800`.
- Species/data: WGS pig prediction.
- GeneAgent use: marker-density and rare-variant context for pig prediction.
- Boundary/risk: sequencing imputation and variant QC must be transparent.
- Source links: [DOI](https://doi.org/10.1016/j.animal.2024.101258); [PubMed](https://pubmed.ncbi.nlm.nih.gov/39126800/)

## RECENT-34 Multi-breed genomic prediction
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_multibreed_prediction_2022"
  version: "v2"
  species: "multi_species"
  blueprint_scope: quantitative_genetics
  evidence_level: "expert_opinion"
  source: "internal_note"
  updated_at: "2026-06-11T00:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Candidate multi-breed or multi-population genomic prediction benchmark in livestock.
- Year: 2022.
- DOI/PMID: DOI to verify before citation export.
- Species/data: multi-breed livestock.
- GeneAgent use: transferability and population-drift warning in prediction reports.
- Boundary/risk: relatedness leakage can inflate cross-breed results.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=multi-breed+multi-population+genomic+prediction+livestock+2022)

## RECENT-35 Multi-trait genomic prediction
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_multitrait_prediction_2023"
  version: "v2"
  species: "multi_species"
  blueprint_scope: quantitative_genetics
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-06-11T00:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Luan et al. *Multi-trait genomic prediction in pigs using single and multistep methods based on the absorption of ungenotyped animals*.
- Year: 2023.
- Journal: Journal of Animal Breeding and Genetics.
- DOI/PMID: DOI `10.1111/jbg.12772`; PMID `37014360`.
- Species/data: multiple correlated traits.
- GeneAgent use: explanation of when correlated traits can improve prediction.
- Boundary/risk: genetic correlations and missing phenotype patterns must be modeled.
- Source links: [DOI](https://doi.org/10.1111/jbg.12772); [PubMed](https://pubmed.ncbi.nlm.nih.gov/37014360/)

## RECENT-36 Deep learning genomic prediction livestock
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_deep_learning_prediction_livestock_2024"
  version: "v2"
  species: "multi_species"
  blueprint_scope: quantitative_genetics
  evidence_level: "expert_opinion"
  source: "internal_note"
  updated_at: "2026-06-11T00:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Candidate deep learning genomic prediction benchmark in livestock.
- Year: 2024.
- DOI/PMID: DOI to verify before citation export.
- Species/data: livestock genomic prediction.
- GeneAgent use: model-family comparison and overfitting warnings.
- Boundary/risk: neural methods need strict validation and baseline comparison.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=deep+learning+genomic+prediction+livestock+2024)

## RECENT-37 Bayesian alphabet benchmark recent
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_bayesian_prediction_benchmark_2022"
  version: "v2"
  species: "multi_species"
  blueprint_scope: quantitative_genetics
  evidence_level: "expert_opinion"
  source: "internal_note"
  updated_at: "2026-05-26T20:10:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Recent Bayesian genomic prediction benchmark comparing BayesA/B/C/BL.
- Year: 2022.
- DOI/PMID: DOI to verify before citation export.
- Species/data: livestock prediction models.
- GeneAgent use: algorithm-selection guidance and prior-sensitivity warning.
- Boundary/risk: posterior convergence diagnostics must be reported.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=Bayesian+genomic+prediction+benchmark+livestock+2022)

## RECENT-38 Genomic prediction with dominance effects
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_dominance_prediction_2023"
  version: "v2"
  species: "multi_species"
  blueprint_scope: quantitative_genetics
  evidence_level: "expert_opinion"
  source: "internal_note"
  updated_at: "2026-05-26T20:10:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Livestock genomic prediction benchmark including dominance or non-additive effects.
- Year: 2023.
- DOI/PMID: DOI to verify before citation export.
- Species/data: livestock crossbred or hybrid populations.
- GeneAgent use: warns when additive GBLUP may miss heterosis or dominance contributions.
- Boundary/risk: non-additive models require enough family structure and validation.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=dominance+non-additive+genomic+prediction+livestock+2023)

## RECENT-39 Genomic prediction for disease resistance
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_disease_resistance_prediction_2024"
  version: "v2"
  species: "multi_species"
  blueprint_scope: quantitative_genetics
  evidence_level: "expert_opinion"
  source: "internal_note"
  updated_at: "2026-05-26T20:10:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Genomic prediction for livestock disease resistance traits.
- Year: 2024.
- DOI/PMID: DOI to verify before citation export.
- Species/data: disease-resistance phenotypes.
- GeneAgent use: phenotype definition and binary/threshold trait caveats.
- Boundary/risk: challenge-test and field phenotypes are not interchangeable.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=genomic+prediction+disease+resistance+livestock+2024)

## RECENT-40 Genomic prediction for fertility traits
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_fertility_prediction_2023"
  version: "v2"
  species: "multi_species"
  blueprint_scope: quantitative_genetics
  evidence_level: "expert_opinion"
  source: "internal_note"
  updated_at: "2026-05-26T20:10:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Genomic prediction benchmark for fertility or reproductive traits in livestock.
- Year: 2023.
- DOI/PMID: DOI to verify before citation export.
- Species/data: fertility traits.
- GeneAgent use: low-heritability and censoring caveats in prediction reports.
- Boundary/risk: management and recording bias can dominate signal.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=genomic+prediction+fertility+traits+livestock+2023)

## RECENT-41 Genomic prediction for feed efficiency
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_feed_efficiency_prediction_2022"
  version: "v2"
  species: "multi_species"
  blueprint_scope: quantitative_genetics
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-06-11T00:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Madilindi et al. *Technological advances in genetic improvement of feed efficiency in dairy cattle: A review*.
- Year: 2022.
- Journal: Livestock Science.
- DOI/PMID: DOI `10.1016/j.livsci.2022.104871`.
- Species/data: dairy cattle feed-efficiency phenotypes and breeding technologies.
- GeneAgent use: trait-definition and recording-cost context.
- Boundary/risk: environment and diet interactions can reduce transferability.
- Source links: [DOI](https://doi.org/10.1016/j.livsci.2022.104871)

## RECENT-42 Genomic prediction for methane emissions
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_methane_prediction_2024"
  version: "v2"
  species: "bos_taurus"
  blueprint_scope: quantitative_genetics
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-06-11T00:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Worku. *Unraveling the genetic basis of methane emission in dairy cattle: a comprehensive exploration and breeding approach to lower methane emissions*.
- Year: 2024.
- Journal: Animal Biotechnology.
- DOI/PMID: DOI `10.1080/10495398.2024.2362677`; PMID `38860914`.
- Species/data: cattle methane and environmental traits.
- GeneAgent use: climate-resilience breeding interpretation.
- Boundary/risk: phenotype measurement protocol is a major limiting factor.
- Source links: [DOI](https://doi.org/10.1080/10495398.2024.2362677); [PubMed](https://pubmed.ncbi.nlm.nih.gov/38860914/)

## RECENT-43 GWAS cattle complex traits
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_cattle_gwas_complex_traits_2022"
  version: "v2"
  species: "bos_taurus"
  blueprint_scope: knowledge_governance
  evidence_level: "expert_opinion"
  source: "internal_note"
  updated_at: "2026-05-26T20:10:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Large-scale cattle GWAS for complex production or health traits.
- Year: 2022.
- DOI/PMID: DOI to verify before citation export.
- Species/data: cattle GWAS.
- GeneAgent use: candidate locus interpretation and multiple-testing caution.
- Boundary/risk: association does not imply causality.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=large-scale+cattle+GWAS+complex+traits+2022)

## RECENT-44 GWAS pig complex traits
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_pig_gwas_complex_traits_2023"
  version: "v2"
  species: "sus_scrofa"
  blueprint_scope: knowledge_governance
  evidence_level: "expert_opinion"
  source: "internal_note"
  updated_at: "2026-05-26T20:10:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Large-scale pig GWAS for growth, meat quality, reproduction, or immune traits.
- Year: 2023.
- DOI/PMID: DOI to verify before citation export.
- Species/data: pig GWAS.
- GeneAgent use: pig candidate gene and QTL evidence.
- Boundary/risk: line-specific associations need external validation.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=large-scale+pig+GWAS+complex+traits+2023)

## RECENT-45 GWAS poultry complex traits
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_poultry_gwas_complex_traits_2023"
  version: "v2"
  species: "gallus_gallus"
  blueprint_scope: knowledge_governance
  evidence_level: "expert_opinion"
  source: "internal_note"
  updated_at: "2026-05-26T20:10:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Large-scale poultry GWAS for growth, egg, meat, or disease traits.
- Year: 2023.
- DOI/PMID: DOI to verify before citation export.
- Species/data: chicken GWAS.
- GeneAgent use: poultry trait interpretation and candidate locus ranking.
- Boundary/risk: commercial-line sampling may be narrow.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=chicken+poultry+GWAS+complex+traits+2023)

## RECENT-46 GWAS sheep goat complex traits
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_small_ruminant_gwas_2024"
  version: "v2"
  species: "small_ruminants"
  blueprint_scope: knowledge_governance
  evidence_level: "expert_opinion"
  source: "internal_note"
  updated_at: "2026-05-26T20:10:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Sheep/goat GWAS for wool, meat, milk, adaptation, or reproduction traits.
- Year: 2024.
- DOI/PMID: DOI to verify before citation export.
- Species/data: small ruminant GWAS.
- GeneAgent use: sheep/goat candidate locus interpretation.
- Boundary/risk: small sample sizes and breed structure can inflate signals.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=sheep+goat+GWAS+complex+traits+2024)

## RECENT-47 Livestock QTL database review
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_livestock_qtl_database_2022"
  version: "v2"
  species: "multi_species"
  blueprint_scope: knowledge_governance
  evidence_level: "expert_opinion"
  source: "internal_note"
  updated_at: "2026-05-26T20:10:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Recent livestock QTL database or cattle/pig/chicken QTL curation update.
- Year: 2022.
- DOI/PMID: DOI to verify before citation export.
- Species/data: curated QTL.
- GeneAgent use: candidate locus cross-check and report annotation.
- Boundary/risk: database entries vary in evidence strength and mapping resolution.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=livestock+QTL+database+update+2022)

## RECENT-48 Livestock fine mapping review
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_livestock_fine_mapping_2024"
  version: "v2"
  species: "multi_species"
  blueprint_scope: knowledge_governance
  evidence_level: "expert_opinion"
  source: "internal_note"
  updated_at: "2026-05-26T20:10:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Recent livestock fine-mapping or causal variant review.
- Year: 2024.
- DOI/PMID: DOI to verify before citation export.
- Species/data: GWAS fine mapping.
- GeneAgent use: caution about moving from association to causal mechanism.
- Boundary/risk: credible sets depend on LD, imputation, and functional priors.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=livestock+fine+mapping+causal+variant+review+2024)

## RECENT-49 Livestock eQTL integration review
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_livestock_eqtl_integration_2023"
  version: "v2"
  species: "multi_species"
  blueprint_scope: knowledge_governance
  evidence_level: "expert_opinion"
  source: "internal_note"
  updated_at: "2026-05-26T20:10:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Livestock eQTL integration for complex trait interpretation.
- Year: 2023.
- DOI/PMID: DOI to verify before citation export.
- Species/data: eQTL/GWAS integration.
- GeneAgent use: regulatory evidence ranking for candidate genes.
- Boundary/risk: tissue matching and colocalization are mandatory checks.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=livestock+eQTL+GWAS+integration+complex+traits+2023)

## RECENT-50 Livestock single-cell review
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_livestock_single_cell_review_2022"
  version: "v2"
  species: "multi_species"
  blueprint_scope: knowledge_governance
  evidence_level: "expert_opinion"
  source: "internal_note"
  updated_at: "2026-05-26T20:10:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Single-cell genomics in livestock review.
- Year: 2022.
- DOI/PMID: DOI to verify before citation export.
- Species/data: livestock single-cell omics.
- GeneAgent use: explains emerging functional annotation evidence.
- Boundary/risk: single-cell datasets are not directly comparable across protocols.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=single-cell+genomics+livestock+review+2022)

## RECENT-51 Pig single-cell atlas
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_pig_single_cell_atlas_2023"
  version: "v2"
  species: "sus_scrofa"
  blueprint_scope: knowledge_governance
  evidence_level: "expert_opinion"
  source: "internal_note"
  updated_at: "2026-05-26T20:10:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Pig single-cell transcriptomic atlas for development, immunity, or production tissues.
- Year: 2023.
- DOI/PMID: DOI to verify before citation export.
- Species/data: pig scRNA-seq.
- GeneAgent use: pig tissue/cell-type candidate gene context.
- Boundary/risk: atlas tissue coverage must match trait biology.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=pig+single-cell+transcriptomic+atlas+2023)

## RECENT-52 Chicken single-cell atlas
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_chicken_single_cell_atlas_2024"
  version: "v2"
  species: "gallus_gallus"
  blueprint_scope: knowledge_governance
  evidence_level: "expert_opinion"
  source: "internal_note"
  updated_at: "2026-05-26T20:10:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Chicken single-cell atlas for development, immunity, or reproductive tissues.
- Year: 2024.
- DOI/PMID: DOI to verify before citation export.
- Species/data: chicken scRNA-seq.
- GeneAgent use: poultry candidate gene functional interpretation.
- Boundary/risk: developmental stage and tissue context must be explicit.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=chicken+single-cell+atlas+2024)

## RECENT-53 Sheep single-cell atlas
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_sheep_single_cell_atlas_2024"
  version: "v2"
  species: "ovis_aries"
  blueprint_scope: knowledge_governance
  evidence_level: "expert_opinion"
  source: "internal_note"
  updated_at: "2026-05-26T20:10:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Sheep single-cell atlas for reproduction, wool follicle, immune, or developmental tissues.
- Year: 2024.
- DOI/PMID: DOI to verify before citation export.
- Species/data: sheep scRNA-seq.
- GeneAgent use: sheep candidate gene and tissue specificity context.
- Boundary/risk: atlas quality and cell annotation confidence must be checked.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=sheep+single-cell+atlas+2024)

## RECENT-54 Multi-omics livestock breeding review
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_multiomics_breeding_review_2023"
  version: "v2"
  species: "multi_species"
  blueprint_scope: knowledge_governance
  evidence_level: "expert_opinion"
  source: "internal_note"
  updated_at: "2026-05-26T20:10:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Multi-omics integration for livestock breeding review.
- Year: 2023.
- DOI/PMID: DOI to verify before citation export.
- Species/data: genomics, transcriptomics, epigenomics, metabolomics.
- GeneAgent use: future expansion planning beyond four current blueprints.
- Boundary/risk: omics integration can overfit without independent validation.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=multi-omics+livestock+breeding+review+2023)

## RECENT-55 Epigenomics livestock review
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_livestock_epigenomics_review_2022"
  version: "v2"
  species: "multi_species"
  blueprint_scope: knowledge_governance
  evidence_level: "expert_opinion"
  source: "internal_note"
  updated_at: "2026-05-26T20:10:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Livestock epigenomics and trait regulation review.
- Year: 2022.
- DOI/PMID: DOI to verify before citation export.
- Species/data: methylation, chromatin, expression.
- GeneAgent use: regulatory mechanism interpretation.
- Boundary/risk: epigenomic marks are tissue, age, and environment dependent.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=livestock+epigenomics+trait+regulation+review+2022)

## RECENT-56 Climate adaptation cattle genomics
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_cattle_climate_adaptation_2023"
  version: "v2"
  species: "bos_taurus"
  blueprint_scope: population_genetics
  evidence_level: "expert_opinion"
  source: "internal_note"
  updated_at: "2026-05-26T20:10:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Cattle climate adaptation population genomics study.
- Year: 2023.
- DOI/PMID: DOI to verify before citation export.
- Species/data: cattle adaptation and selection signatures.
- GeneAgent use: environmental adaptation interpretation in breed reports.
- Boundary/risk: climate association needs environmental covariate control.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=cattle+climate+adaptation+genomics+2023)

## RECENT-57 Heat tolerance cattle genomic loci
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_cattle_heat_tolerance_2024"
  version: "v2"
  species: "bos_taurus"
  blueprint_scope: knowledge_governance
  evidence_level: "expert_opinion"
  source: "internal_note"
  updated_at: "2026-05-26T20:10:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Cattle heat-tolerance genomic association or selection study.
- Year: 2024.
- DOI/PMID: DOI to verify before citation export.
- Species/data: cattle heat tolerance.
- GeneAgent use: climate-resilience candidate locus interpretation.
- Boundary/risk: phenotype recording and environmental covariates are critical.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=cattle+heat+tolerance+genomic+association+2024)

## RECENT-58 Pig adaptation genomics
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_pig_adaptation_genomics_2023"
  version: "v2"
  species: "sus_scrofa"
  blueprint_scope: population_genetics
  evidence_level: "expert_opinion"
  source: "internal_note"
  updated_at: "2026-05-26T20:10:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Pig adaptation or domestication genomics study.
- Year: 2023.
- DOI/PMID: DOI to verify before citation export.
- Species/data: pig population genomics.
- GeneAgent use: pig breed differentiation and selection-scan context.
- Boundary/risk: wild/feral/domestic group labels must be explicit.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=pig+adaptation+domestication+genomics+2023)

## RECENT-59 Chicken domestication genomics
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_chicken_domestication_genomics_2022"
  version: "v2"
  species: "gallus_gallus"
  blueprint_scope: population_genetics
  evidence_level: "expert_opinion"
  source: "internal_note"
  updated_at: "2026-05-26T20:10:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Chicken domestication or breed formation genomics study.
- Year: 2022.
- DOI/PMID: DOI to verify before citation export.
- Species/data: chicken population genomics.
- GeneAgent use: poultry PCA and breed-history interpretation.
- Boundary/risk: introgression and sampling design can confound signals.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=chicken+domestication+genomics+2022)

## RECENT-60 Sheep goat adaptation genomics
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_small_ruminant_adaptation_2023"
  version: "v2"
  species: "small_ruminants"
  blueprint_scope: population_genetics
  evidence_level: "expert_opinion"
  source: "internal_note"
  updated_at: "2026-05-26T20:10:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Sheep/goat adaptation genomics study.
- Year: 2023.
- DOI/PMID: DOI to verify before citation export.
- Species/data: small ruminant population genomics.
- GeneAgent use: adaptation, altitude, aridity, and breed differentiation context.
- Boundary/risk: geography and management confounding must be checked.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=sheep+goat+adaptation+genomics+2023)

## RECENT-61 Livestock imputation benchmark
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_livestock_imputation_benchmark_2022"
  version: "v2"
  species: "multi_species"
  blueprint_scope: genotype_processing
  evidence_level: "expert_opinion"
  source: "internal_note"
  updated_at: "2026-05-26T20:10:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Livestock genotype imputation benchmark using SNP chips or WGS reference panels.
- Year: 2022.
- DOI/PMID: DOI to verify before citation export.
- Species/data: genotype imputation.
- GeneAgent use: imputation accuracy and reference-panel warnings for QC.
- Boundary/risk: imputation accuracy is breed and marker-density dependent.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=livestock+genotype+imputation+benchmark+2022)

## RECENT-62 Low-pass sequencing imputation cattle
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_lowpass_imputation_cattle_2023"
  version: "v2"
  species: "bos_taurus"
  blueprint_scope: genotype_processing
  evidence_level: "expert_opinion"
  source: "internal_note"
  updated_at: "2026-05-26T20:10:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Low-pass sequencing and imputation benchmark in cattle.
- Year: 2023.
- DOI/PMID: DOI to verify before citation export.
- Species/data: low-pass WGS and imputation.
- GeneAgent use: future QC policy for low-pass-derived genotypes.
- Boundary/risk: not equivalent to array genotypes without imputation QC.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=low-pass+sequencing+imputation+cattle+2023)

## RECENT-63 Low-pass sequencing imputation pigs
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_lowpass_imputation_pig_2024"
  version: "v2"
  species: "sus_scrofa"
  blueprint_scope: genotype_processing
  evidence_level: "expert_opinion"
  source: "internal_note"
  updated_at: "2026-05-26T20:10:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Low-pass sequencing and imputation benchmark in pigs.
- Year: 2024.
- DOI/PMID: DOI to verify before citation export.
- Species/data: pig low-pass WGS.
- GeneAgent use: pig imputation QC and marker-density planning.
- Boundary/risk: line-specific reference panels affect accuracy.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=low-pass+sequencing+imputation+pigs+2024)

## RECENT-64 Livestock phasing benchmark
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_livestock_phasing_benchmark_2023"
  version: "v2"
  species: "multi_species"
  blueprint_scope: genotype_processing
  evidence_level: "expert_opinion"
  source: "internal_note"
  updated_at: "2026-05-26T20:10:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Livestock haplotype phasing benchmark.
- Year: 2023.
- DOI/PMID: DOI to verify before citation export.
- Species/data: phased genotypes and haplotypes.
- GeneAgent use: downstream haplotype/selection-scan caution.
- Boundary/risk: family information and reference panels change performance.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=livestock+haplotype+phasing+benchmark+2023)

## RECENT-65 Livestock ROH benchmark
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_livestock_roh_benchmark_2022"
  version: "v2"
  species: "multi_species"
  blueprint_scope: genotype_processing
  evidence_level: "expert_opinion"
  source: "internal_note"
  updated_at: "2026-05-26T20:10:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Runs-of-homozygosity benchmark or review in livestock.
- Year: 2022.
- DOI/PMID: DOI to verify before citation export.
- Species/data: ROH and inbreeding.
- GeneAgent use: inbreeding diagnostics and QC/report interpretation.
- Boundary/risk: marker density and ROH length thresholds require species review.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=runs+of+homozygosity+livestock+review+2022)

## RECENT-66 Livestock LD decay benchmark
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_livestock_ld_decay_2023"
  version: "v2"
  species: "multi_species"
  blueprint_scope: genotype_processing
  evidence_level: "expert_opinion"
  source: "internal_note"
  updated_at: "2026-05-26T20:10:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Linkage disequilibrium decay benchmark across livestock breeds.
- Year: 2023.
- DOI/PMID: DOI to verify before citation export.
- Species/data: LD decay and effective population size.
- GeneAgent use: LD pruning, marker-density, and PCA parameter explanation.
- Boundary/risk: LD decay varies strongly by breed and sample design.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=linkage+disequilibrium+decay+livestock+breeds+2023)

## RECENT-67 Livestock effective population size
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_livestock_effective_population_size_2024"
  version: "v2"
  species: "multi_species"
  blueprint_scope: population_genetics
  evidence_level: "expert_opinion"
  source: "internal_note"
  updated_at: "2026-05-26T20:10:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Effective population size inference from livestock genomic data.
- Year: 2024.
- DOI/PMID: DOI to verify before citation export.
- Species/data: livestock Ne estimation.
- GeneAgent use: population history and prediction accuracy context.
- Boundary/risk: Ne estimates depend on marker density and demographic model.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=effective+population+size+livestock+genomic+data+2024)

## RECENT-68 Livestock selection signature review
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_livestock_selection_signature_review_2022"
  version: "v2"
  species: "multi_species"
  blueprint_scope: population_genetics
  evidence_level: "expert_opinion"
  source: "internal_note"
  updated_at: "2026-05-26T20:10:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Selection-signature methods and livestock applications review.
- Year: 2022.
- DOI/PMID: DOI to verify before citation export.
- Species/data: selection scans.
- GeneAgent use: explains FST/iHS/XP-EHH/ROH-based scan differences.
- Boundary/risk: demographic history can mimic selection.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=selection+signature+livestock+review+2022)

## RECENT-69 Livestock structural variation review
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_livestock_structural_variation_review_2023"
  version: "v2"
  species: "multi_species"
  blueprint_scope: knowledge_governance
  evidence_level: "expert_opinion"
  source: "internal_note"
  updated_at: "2026-05-26T20:10:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Structural variation in livestock genomes review.
- Year: 2023.
- DOI/PMID: DOI to verify before citation export.
- Species/data: CNV, insertion/deletion, inversion, pangenome SV.
- GeneAgent use: explains why SNP-only workflows can miss trait-relevant variation.
- Boundary/risk: SV calling methods have high platform dependence.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=structural+variation+livestock+genomes+review+2023)

## RECENT-70 Livestock graph genome methods
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_livestock_graph_genome_methods_2024"
  version: "v2"
  species: "multi_species"
  blueprint_scope: knowledge_governance
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-06-11T00:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Leonard et al. *Graph construction method impacts variation representation and analyses in a bovine super-pangenome*.
- Year: 2023.
- Journal: Genome Biology.
- DOI/PMID: DOI `10.1186/s13059-023-02969-y`; PMID `37217946`.
- Species/data: bovine super-pangenome, graph reference, pangenome indexing.
- GeneAgent use: future V2.x expansion boundary for pangenome-aware pipelines.
- Boundary/risk: graph coordinates and report interpretation are not yet standardized.
- Source links: [DOI](https://doi.org/10.1186/s13059-023-02969-y); [PubMed](https://pubmed.ncbi.nlm.nih.gov/37217946/)

## RECENT-71 Livestock AI genomics review
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_livestock_ai_genomics_review_2025"
  version: "v2"
  species: "multi_species"
  blueprint_scope: knowledge_governance
  evidence_level: "expert_opinion"
  source: "internal_note"
  updated_at: "2026-05-26T20:10:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: AI, machine learning, or foundation-model review for livestock genomics and breeding.
- Year: 2025.
- DOI/PMID: DOI to verify before citation export.
- Species/data: AI-enabled animal genomics.
- GeneAgent use: future agentic workflow and model-selection context.
- Boundary/risk: review/benchmark quality must be screened; avoid hype-driven claims.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=AI+machine+learning+foundation+models+livestock+genomics+breeding+2025)

## RECENT-72 Livestock knowledge graph review
```yaml
knowledge_item.v2:
  doc_id: "paper_recent_livestock_knowledge_graph_2025"
  version: "v2"
  species: "multi_species"
  blueprint_scope: knowledge_governance
  evidence_level: "expert_opinion"
  source: "internal_note"
  updated_at: "2026-05-26T20:10:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Knowledge graph or evidence-integration review for animal genomics and breeding.
- Year: 2025.
- DOI/PMID: DOI to verify before citation export.
- Species/data: literature/evidence integration.
- GeneAgent use: supports GeneAgent knowledge-base architecture and traceability planning.
- Boundary/risk: not a direct biological evidence source.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=knowledge+graph+animal+genomics+breeding+2025)
