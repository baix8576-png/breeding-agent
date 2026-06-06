# Animal Genomics Classic Landmark Papers

This pack complements the existing `qc/pca/grm/genomic_prediction` seed packs and the separated association-mapping domain. It stores durable landmark evidence for GeneAgent knowledge retrieval without duplicating every already-indexed core card.

## CLASSIC-01 Fisher 1918 infinitesimal model
```yaml
knowledge_item.v2:
  doc_id: "paper_classic_fisher_1918"
  version: "v2"
  species: "multi_species"
  blueprint_scope: knowledge_governance
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-26T20:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Fisher RA. *The correlation between relatives on the supposition of Mendelian inheritance* (1918).
- Year: 1918.
- DOI/PMID: DOI not available in seed card; classical source.
- Species/data: multi-species quantitative genetics theory.
- GeneAgent use: explain infinitesimal trait architecture behind BLUP/GBLUP assumptions.
- Boundary/risk: historical theory; pair with modern genomic prediction papers for operational settings.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=Fisher+1918+correlation+between+relatives+Mendelian+inheritance)

## CLASSIC-02 Wright 1931 population structure
```yaml
knowledge_item.v2:
  doc_id: "paper_classic_wright_1931"
  version: "v2"
  species: "multi_species"
  blueprint_scope: population_genetics
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-26T20:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Wright S. *Evolution in Mendelian populations* (1931).
- Year: 1931.
- DOI/PMID: DOI not available in seed card; classical source.
- Species/data: population genetics theory.
- GeneAgent use: supports interpretation of drift, inbreeding, and population differentiation in PCA/structure reports.
- Boundary/risk: not a modern workflow paper; do not use for software defaults.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=Wright+1931+Evolution+in+Mendelian+populations)

## CLASSIC-03 Lush animal breeding plans
```yaml
knowledge_item.v2:
  doc_id: "paper_classic_lush_1937"
  version: "v2"
  species: "multi_species"
  blueprint_scope: knowledge_governance
  evidence_level: "expert_opinion"
  source: "paper"
  updated_at: "2026-05-26T20:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Lush JL. *Animal Breeding Plans* (1937).
- Year: 1937.
- DOI/PMID: book; DOI not applicable.
- Species/data: livestock breeding theory.
- GeneAgent use: historical basis for selection index thinking and breeding objective framing.
- Boundary/risk: book-level evidence; not a parameter default source.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=Lush+Animal+Breeding+Plans+1937)

## CLASSIC-04 Henderson mixed model equations
```yaml
knowledge_item.v2:
  doc_id: "paper_classic_henderson_1975_mme"
  version: "v2"
  species: "multi_species"
  blueprint_scope: quantitative_genetics
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-26T20:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Henderson CR. *Best linear unbiased estimation and prediction under a selection model* (1975).
- Year: 1975.
- DOI/PMID: DOI `10.2307/2529430`.
- Species/data: mixed model theory.
- GeneAgent use: explains BLUP foundations behind animal model and GBLUP reporting.
- Boundary/risk: mathematical foundation; needs modern genomic relationship extensions for marker data.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=Henderson+1975+best+linear+unbiased+estimation+prediction+selection+model)

## CLASSIC-05 Henderson linear models book
```yaml
knowledge_item.v2:
  doc_id: "paper_classic_henderson_1984_linear_models"
  version: "v2"
  species: "multi_species"
  blueprint_scope: quantitative_genetics
  evidence_level: "expert_opinion"
  source: "paper"
  updated_at: "2026-05-26T20:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Henderson CR. *Applications of Linear Models in Animal Breeding* (1984).
- Year: 1984.
- DOI/PMID: book; DOI not applicable.
- Species/data: livestock mixed-model evaluation.
- GeneAgent use: background for animal model notation, fixed/random effects, and pedigree evaluation.
- Boundary/risk: book is not a modern software manual.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=Henderson+Applications+of+Linear+Models+in+Animal+Breeding+1984)

## CLASSIC-06 Falconer quantitative genetics
```yaml
knowledge_item.v2:
  doc_id: "paper_classic_falconer_mackay_1996"
  version: "v2"
  species: "multi_species"
  blueprint_scope: knowledge_governance
  evidence_level: "expert_opinion"
  source: "paper"
  updated_at: "2026-05-26T20:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Falconer DS and Mackay TFC. *Introduction to Quantitative Genetics* (4th edition, 1996).
- Year: 1996.
- DOI/PMID: book; DOI not applicable.
- Species/data: quantitative genetics concepts.
- GeneAgent use: definitions for heritability, genetic variance, selection response, and correlated traits.
- Boundary/risk: use as concept reference, not a pipeline-specific threshold source.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=Falconer+Mackay+Introduction+to+Quantitative+Genetics+1996)

## CLASSIC-07 Lander Botstein interval mapping
```yaml
knowledge_item.v2:
  doc_id: "paper_classic_lander_botstein_1989"
  version: "v2"
  species: "multi_species"
  blueprint_scope: knowledge_governance
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-26T20:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Lander ES and Botstein D. *Mapping Mendelian factors underlying quantitative traits using RFLP linkage maps* (1989).
- Year: 1989.
- DOI/PMID: DOI `10.1534/genetics.121.3.185`.
- Species/data: QTL mapping theory.
- GeneAgent use: supports explanations contrasting linkage QTL mapping with GWAS and genomic prediction.
- Boundary/risk: linkage-family design differs from population-scale GWAS.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=Lander+Botstein+1989+Mapping+Mendelian+factors+quantitative+traits)

## CLASSIC-08 Churchill Doerge permutation testing
```yaml
knowledge_item.v2:
  doc_id: "paper_classic_churchill_doerge_1994"
  version: "v2"
  species: "multi_species"
  blueprint_scope: knowledge_governance
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-26T20:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Churchill GA and Doerge RW. *Empirical threshold values for quantitative trait mapping* (1994).
- Year: 1994.
- DOI/PMID: DOI `10.1093/genetics/138.3.963`.
- Species/data: QTL significance control.
- GeneAgent use: explains empirical genome-wide thresholds and multiple-testing caution.
- Boundary/risk: not a direct SNP-chip QC threshold.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=Churchill+Doerge+1994+Empirical+threshold+values+quantitative+trait+mapping)

## CLASSIC-09 Pritchard STRUCTURE
```yaml
knowledge_item.v2:
  doc_id: "paper_classic_pritchard_structure_2000"
  version: "v2"
  species: "multi_species"
  blueprint_scope: population_genetics
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-26T20:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Pritchard JK et al. *Inference of population structure using multilocus genotype data* (2000).
- Year: 2000.
- DOI/PMID: DOI `10.1093/genetics/155.2.945`.
- Species/data: multilocus population structure.
- GeneAgent use: conceptual anchor for ancestry proportions and admixture caveats.
- Boundary/risk: STRUCTURE-style inference is not identical to PCA clustering.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=Pritchard+2000+Inference+of+population+structure+using+multilocus+genotype+data)

## CLASSIC-10 Patterson PCA ancestry
```yaml
knowledge_item.v2:
  doc_id: "paper_classic_patterson_2006_pca"
  version: "v2"
  species: "multi_species"
  blueprint_scope: population_genetics
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-26T20:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Patterson N et al. *Population structure and eigenanalysis* (2006).
- Year: 2006.
- DOI/PMID: DOI `10.1371/journal.pgen.0020190`.
- Species/data: genome-wide genotype PCA.
- GeneAgent use: supports PCA/eigenvector interpretation and stratification control.
- Boundary/risk: human-population examples need livestock-specific LD and sampling checks.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=Patterson+Price+Reich+2006+Population+structure+and+eigenanalysis)

## CLASSIC-11 Price EIGENSTRAT
```yaml
knowledge_item.v2:
  doc_id: "paper_classic_price_2006_eigenstrat"
  version: "v2"
  species: "multi_species"
  blueprint_scope: population_genetics
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-26T20:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Price AL et al. *Principal components analysis corrects for stratification in genome-wide association studies* (2006).
- Year: 2006.
- DOI/PMID: DOI `10.1038/ng1847`.
- Species/data: GWAS stratification correction.
- GeneAgent use: explains why PCA covariates are often added to association or prediction workflows.
- Boundary/risk: PCs should not be blindly included without trait and design review.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=Price+2006+Principal+components+analysis+corrects+for+stratification)

## CLASSIC-12 ADMIXTURE model
```yaml
knowledge_item.v2:
  doc_id: "paper_classic_alexander_admixture_2009"
  version: "v2"
  species: "multi_species"
  blueprint_scope: population_genetics
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-26T20:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Alexander DH et al. *Fast model-based estimation of ancestry in unrelated individuals* (2009).
- Year: 2009.
- DOI/PMID: DOI `10.1101/gr.094052.109`.
- Species/data: ancestry estimation.
- GeneAgent use: interpret structure-analysis alternatives when PCA is insufficient.
- Boundary/risk: K selection and relatedness filtering are frequent failure points.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=Alexander+Novembre+Lange+2009+ADMIXTURE)

## CLASSIC-13 Weir Cockerham F-statistics
```yaml
knowledge_item.v2:
  doc_id: "paper_classic_weir_cockerham_1984"
  version: "v2"
  species: "multi_species"
  blueprint_scope: population_genetics
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-26T20:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Weir BS and Cockerham CC. *Estimating F-statistics for the analysis of population structure* (1984).
- Year: 1984.
- DOI/PMID: DOI `10.1111/j.1558-5646.1984.tb05657.x`.
- Species/data: population differentiation statistics.
- GeneAgent use: supports FST interpretation in breed differentiation and selection-scan reports.
- Boundary/risk: requires sampling-bias and group-definition review.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=Weir+Cockerham+1984+Estimating+F-statistics)

## CLASSIC-14 Nei genetic distance
```yaml
knowledge_item.v2:
  doc_id: "paper_classic_nei_1972_distance"
  version: "v2"
  species: "multi_species"
  blueprint_scope: population_genetics
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-26T20:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Nei M. *Genetic distance between populations* (1972).
- Year: 1972.
- DOI/PMID: DOI not recorded in seed card.
- Species/data: allele-frequency divergence.
- GeneAgent use: background for breed-distance interpretation and dendrogram caution.
- Boundary/risk: not a substitute for PCA/admixture with genome-wide data.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=Nei+1972+Genetic+distance+between+populations)

## CLASSIC-15 Hill Weir LD variance
```yaml
knowledge_item.v2:
  doc_id: "paper_classic_hill_weir_1988_ld"
  version: "v2"
  species: "multi_species"
  blueprint_scope: genotype_processing
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-26T20:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Hill WG and Weir BS. *Variances and covariances of squared linkage disequilibria in finite populations* (1988).
- Year: 1988.
- DOI/PMID: DOI not recorded in seed card.
- Species/data: LD theory.
- GeneAgent use: supports LD pruning and marker-density interpretation.
- Boundary/risk: theoretical; empirical LD decay must be species/population specific.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=Hill+Weir+1988+squared+linkage+disequilibria)

## CLASSIC-16 Sabeti EHH
```yaml
knowledge_item.v2:
  doc_id: "paper_classic_sabeti_2002_ehh"
  version: "v2"
  species: "multi_species"
  blueprint_scope: population_genetics
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-26T20:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Sabeti PC et al. *Detecting recent positive selection in the human genome from haplotype structure* (2002).
- Year: 2002.
- DOI/PMID: DOI `10.1038/nature01140`.
- Species/data: haplotype selection signal.
- GeneAgent use: selection signature rationale for EHH-family analyses in animals.
- Boundary/risk: livestock demographic history and breed formation can create false positives.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=Sabeti+2002+Detecting+recent+positive+selection+haplotype+structure)

## CLASSIC-17 Voight iHS
```yaml
knowledge_item.v2:
  doc_id: "paper_classic_voight_2006_ihs"
  version: "v2"
  species: "multi_species"
  blueprint_scope: population_genetics
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-26T20:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Voight BF et al. *A map of recent positive selection in the human genome* (2006).
- Year: 2006.
- DOI/PMID: DOI `10.1371/journal.pbio.0040072`.
- Species/data: integrated haplotype score.
- GeneAgent use: supports iHS/XP-EHH terminology in selection-scan explanation.
- Boundary/risk: phase quality and allele-frequency bins need explicit QC.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=Voight+2006+map+recent+positive+selection+iHS)

## CLASSIC-18 Pickrell selection signals
```yaml
knowledge_item.v2:
  doc_id: "paper_classic_pickrell_2009_selection"
  version: "v2"
  species: "multi_species"
  blueprint_scope: population_genetics
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-26T20:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Pickrell JK et al. *Signals of recent positive selection in a worldwide sample of human populations* (2009).
- Year: 2009.
- DOI/PMID: DOI `10.1101/gr.087577.108`.
- Species/data: comparative selection scans.
- GeneAgent use: cautionary examples for combining multiple statistics in selection-signature reports.
- Boundary/risk: not livestock-specific; use with animal-specific validation papers.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=Pickrell+2009+Signals+of+recent+positive+selection)

## CLASSIC-19 McQuillan ROH
```yaml
knowledge_item.v2:
  doc_id: "paper_classic_mcquillan_2008_roh"
  version: "v2"
  species: "multi_species"
  blueprint_scope: genotype_processing
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-26T20:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: McQuillan R et al. *Runs of homozygosity in European populations* (2008).
- Year: 2008.
- DOI/PMID: DOI `10.1016/j.ajhg.2007.11.004`.
- Species/data: ROH/inbreeding inference.
- GeneAgent use: supports ROH-based inbreeding interpretation for livestock QC reports.
- Boundary/risk: human ROH length distributions cannot be directly copied to livestock.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=McQuillan+2008+runs+of+homozygosity)

## CLASSIC-20 Purcell PLINK
```yaml
knowledge_item.v2:
  doc_id: "paper_classic_purcell_plink_2007"
  version: "v2"
  species: "multi_species"
  blueprint_scope: genotype_processing
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-26T20:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Purcell S et al. *PLINK: a tool set for whole-genome association and population-based linkage analyses* (2007).
- Year: 2007.
- DOI/PMID: DOI `10.1086/519795`.
- Species/data: genotype QC and association tooling.
- GeneAgent use: explains PLINK/PLINK2 role in QC, PCA preparation, and file-format conversion.
- Boundary/risk: modern pipelines should use version-pinned commands.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=Purcell+2007+PLINK+tool+set)

## CLASSIC-21 Chang PLINK 1.9
```yaml
knowledge_item.v2:
  doc_id: "paper_classic_chang_plink_2015"
  version: "v2"
  species: "multi_species"
  blueprint_scope: genotype_processing
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-26T20:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Chang CC et al. *Second-generation PLINK: rising to the challenge of larger and richer datasets* (2015).
- Year: 2015.
- DOI/PMID: DOI `10.1186/s13742-015-0047-8`.
- Species/data: large genotype dataset tooling.
- GeneAgent use: supports command-level explanation for high-throughput QC and PCA preprocessing.
- Boundary/risk: exact flags must follow local PLINK2 version.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=Chang+2015+Second-generation+PLINK)

## CLASSIC-22 Danecek VCFtools
```yaml
knowledge_item.v2:
  doc_id: "paper_classic_danecek_vcftools_2011"
  version: "v2"
  species: "multi_species"
  blueprint_scope: genotype_processing
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-26T20:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Danecek P et al. *The variant call format and VCFtools* (2011).
- Year: 2011.
- DOI/PMID: DOI `10.1093/bioinformatics/btr330`.
- Species/data: VCF processing.
- GeneAgent use: supports VCF input validation, site filtering, and reproducible variant summaries.
- Boundary/risk: VCFtools differs from bcftools/plink2 in edge-case handling.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=Danecek+2011+variant+call+format+VCFtools)

## CLASSIC-23 Li SAMtools
```yaml
knowledge_item.v2:
  doc_id: "paper_classic_li_samtools_2009"
  version: "v2"
  species: "multi_species"
  blueprint_scope: genotype_processing
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-26T20:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Li H et al. *The Sequence Alignment/Map format and SAMtools* (2009).
- Year: 2009.
- DOI/PMID: DOI `10.1093/bioinformatics/btp352`.
- Species/data: alignment and variant-processing infrastructure.
- GeneAgent use: supports BAM/CRAM provenance and index checks when sequencing-derived data are used.
- Boundary/risk: not a genotype QC threshold paper.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=Li+2009+SAMtools+Sequence+Alignment+Map+format)

## CLASSIC-24 Danecek BCFtools 2021
```yaml
knowledge_item.v2:
  doc_id: "paper_classic_danecek_bcftools_2021"
  version: "v2"
  species: "multi_species"
  blueprint_scope: genotype_processing
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-26T20:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Danecek P et al. *Twelve years of SAMtools and BCFtools* (2021).
- Year: 2021.
- DOI/PMID: DOI `10.1093/gigascience/giab008`.
- Species/data: VCF/BCF processing.
- GeneAgent use: supports modern bcftools index, view, query, and stats troubleshooting.
- Boundary/risk: command behavior must be version pinned in HPC wrappers.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=Twelve+years+of+SAMtools+and+BCFtools)

## CLASSIC-25 Browning Beagle 5
```yaml
knowledge_item.v2:
  doc_id: "paper_classic_browning_beagle_2018"
  version: "v2"
  species: "multi_species"
  blueprint_scope: genotype_processing
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-26T20:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Browning BL et al. *A one-penny imputed genome from next-generation reference panels* (2018).
- Year: 2018.
- DOI/PMID: DOI `10.1016/j.ajhg.2018.07.015`.
- Species/data: phasing and imputation.
- GeneAgent use: supports imputation provenance and reference-panel caveats.
- Boundary/risk: livestock panel structure and breed diversity must be checked.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=Browning+2018+Beagle+5+one-penny+imputed+genome)

## CLASSIC-26 Howie IMPUTE
```yaml
knowledge_item.v2:
  doc_id: "paper_classic_howie_impute_2009"
  version: "v2"
  species: "multi_species"
  blueprint_scope: genotype_processing
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-26T20:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Howie BN et al. *A flexible and accurate genotype imputation method for the next generation of genome-wide association studies* (2009).
- Year: 2009.
- DOI/PMID: DOI `10.1371/journal.pgen.1000529`.
- Species/data: genotype imputation.
- GeneAgent use: explains imputation uncertainty and reference-panel matching.
- Boundary/risk: human reference examples require livestock validation.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=Howie+2009+flexible+accurate+genotype+imputation)

## CLASSIC-27 Yang GCTA variance explained
```yaml
knowledge_item.v2:
  doc_id: "paper_classic_yang_2010_common_snps"
  version: "v2"
  species: "multi_species"
  blueprint_scope: quantitative_genetics
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-26T20:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Yang J et al. *Common SNPs explain a large proportion of the heritability for human height* (2010).
- Year: 2010.
- DOI/PMID: DOI `10.1038/ng.608`.
- Species/data: GRM-based variance component estimation.
- GeneAgent use: supports marker-derived relationship matrix interpretation.
- Boundary/risk: human height example; livestock trait architecture differs.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=Yang+2010+Common+SNPs+explain+heritability+height)

## CLASSIC-28 Yang GCTA software
```yaml
knowledge_item.v2:
  doc_id: "paper_classic_yang_gcta_2011"
  version: "v2"
  species: "multi_species"
  blueprint_scope: quantitative_genetics
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-26T20:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Yang J et al. *GCTA: a tool for genome-wide complex trait analysis* (2011).
- Year: 2011.
- DOI/PMID: DOI `10.1016/j.ajhg.2010.11.011`.
- Species/data: GRM and variance component tooling.
- GeneAgent use: supports GCTA/GCTA64 command guidance and GRM diagnostics.
- Boundary/risk: tool flags and input formats must be version pinned.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=Yang+2011+GCTA+tool+genome-wide+complex+trait+analysis)

## CLASSIC-29 Daetwyler accuracy formula
```yaml
knowledge_item.v2:
  doc_id: "paper_classic_daetwyler_2008_accuracy"
  version: "v2"
  species: "multi_species"
  blueprint_scope: quantitative_genetics
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-26T20:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Daetwyler HD et al. *Accuracy of predicting the genetic risk of disease using a genome-wide approach* (2008).
- Year: 2008.
- DOI/PMID: DOI `10.1371/journal.pone.0003395`.
- Species/data: genomic prediction accuracy theory.
- GeneAgent use: supports sample size, effective population size, and heritability explanations.
- Boundary/risk: theoretical estimates do not replace validation.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=Daetwyler+2008+accuracy+genome-wide+prediction)

## CLASSIC-30 Goddard Hayes genomic selection review
```yaml
knowledge_item.v2:
  doc_id: "paper_classic_goddard_hayes_2007"
  version: "v2"
  species: "multi_species"
  blueprint_scope: quantitative_genetics
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-26T20:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Goddard ME and Hayes BJ. *Genomic selection* (2007).
- Year: 2007.
- DOI/PMID: DOI not recorded in seed card; verify before citation export.
- Species/data: livestock genomic selection review.
- GeneAgent use: high-level explanation of why dense markers changed breeding program design.
- Boundary/risk: pair with newer implementation reviews for current practice.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=Goddard+Hayes+2007+Genomic+selection)

## CLASSIC-31 Aguilar single-step GBLUP
```yaml
knowledge_item.v2:
  doc_id: "paper_classic_aguilar_2010_ssgblup"
  version: "v2"
  species: "multi_species"
  blueprint_scope: quantitative_genetics
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-26T20:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Aguilar I et al. *Hot topic: A unified approach to utilize phenotypic, full pedigree, and genomic information for genetic evaluation of Holstein final score* (2010).
- Year: 2010.
- DOI/PMID: DOI `10.3168/jds.2009-2730`.
- Species/data: dairy cattle ssGBLUP.
- GeneAgent use: supports combining pedigree and genomic information in prediction planning.
- Boundary/risk: dairy-specific implementation; translate carefully to other species.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=Aguilar+2010+unified+approach+phenotypic+pedigree+genomic+information)

## CLASSIC-32 Legarra relationship matrix
```yaml
knowledge_item.v2:
  doc_id: "paper_classic_legarra_2009_relationship_matrix"
  version: "v2"
  species: "multi_species"
  blueprint_scope: quantitative_genetics
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-26T20:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Legarra A et al. *A relationship matrix including full pedigree and genomic information* (2009).
- Year: 2009.
- DOI/PMID: DOI `10.3168/jds.2009-2061`.
- Species/data: pedigree-genomic relationship matrix.
- GeneAgent use: supports H-matrix explanation and ssGBLUP context.
- Boundary/risk: requires pedigree consistency checks.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=Legarra+2009+relationship+matrix+full+pedigree+genomic+information)

## CLASSIC-33 Misztal single-step overview
```yaml
knowledge_item.v2:
  doc_id: "paper_classic_misztal_2013_ssgblup"
  version: "v2"
  species: "multi_species"
  blueprint_scope: quantitative_genetics
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-26T20:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Misztal I et al. *Single-step genomic evaluation in BLUPF90 software* and related ssGBLUP implementation literature.
- Year: 2013.
- DOI/PMID: DOI not recorded in seed card; verify before citation export.
- Species/data: livestock genomic evaluation.
- GeneAgent use: operational anchor for production genetic evaluation pipelines.
- Boundary/risk: software-specific behavior must be checked against local toolchain.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=Misztal+2013+single-step+genomic+evaluation+BLUPF90)

## CLASSIC-34 Gianola Bayesian quantitative genetics
```yaml
knowledge_item.v2:
  doc_id: "paper_classic_gianola_2006_bayes"
  version: "v2"
  species: "multi_species"
  blueprint_scope: quantitative_genetics
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-26T20:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Gianola D and Fernando RL. *Bayesian methods in animal breeding theory* lineage.
- Year: 2006.
- DOI/PMID: DOI not recorded in seed card; verify before citation export.
- Species/data: Bayesian animal breeding.
- GeneAgent use: background for BayesA/B/C and shrinkage-prior explanations.
- Boundary/risk: not a default algorithm choice by itself.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=Gianola+Fernando+Bayesian+methods+animal+breeding)

## CLASSIC-35 Tibshirani LASSO
```yaml
knowledge_item.v2:
  doc_id: "paper_classic_tibshirani_1996_lasso"
  version: "v2"
  species: "multi_species"
  blueprint_scope: quantitative_genetics
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-26T20:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Tibshirani R. *Regression shrinkage and selection via the lasso* (1996).
- Year: 1996.
- DOI/PMID: DOI `10.1111/j.2517-6161.1996.tb02080.x`.
- Species/data: regularized regression.
- GeneAgent use: supports sparse marker-effect model explanations.
- Boundary/risk: not livestock-specific; tune with cross-validation.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=Tibshirani+1996+Regression+shrinkage+selection+via+lasso)

## CLASSIC-36 Breiman random forest
```yaml
knowledge_item.v2:
  doc_id: "paper_classic_breiman_2001_random_forest"
  version: "v2"
  species: "multi_species"
  blueprint_scope: quantitative_genetics
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-26T20:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Breiman L. *Random forests* (2001).
- Year: 2001.
- DOI/PMID: DOI `10.1023/A:1010933404324`.
- Species/data: machine learning model family.
- GeneAgent use: explains tree-ensemble baseline options for genomic prediction benchmarking.
- Boundary/risk: marker dimensionality and leakage control are critical.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=Breiman+2001+Random+forests)

## CLASSIC-37 Kuhn caret
```yaml
knowledge_item.v2:
  doc_id: "paper_classic_kuhn_caret_2008"
  version: "v2"
  species: "multi_species"
  blueprint_scope: quantitative_genetics
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-26T20:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Kuhn M. *Building predictive models in R using the caret package* (2008).
- Year: 2008.
- DOI/PMID: DOI `10.18637/jss.v028.i05`.
- Species/data: model training workflow.
- GeneAgent use: supports cross-validation and tuning vocabulary.
- Boundary/risk: caret itself is not the target production engine.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=Kuhn+2008+caret+package+predictive+models)

## CLASSIC-38 Benjamini Hochberg FDR
```yaml
knowledge_item.v2:
  doc_id: "paper_classic_benjamini_hochberg_1995"
  version: "v2"
  species: "multi_species"
  blueprint_scope: knowledge_governance
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-26T20:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Benjamini Y and Hochberg Y. *Controlling the false discovery rate* (1995).
- Year: 1995.
- DOI/PMID: DOI `10.1111/j.2517-6161.1995.tb02031.x`.
- Species/data: multiple testing control.
- GeneAgent use: supports GWAS/QTL/eQTL report interpretation.
- Boundary/risk: FDR thresholds must be selected per analysis design.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=Benjamini+Hochberg+1995+controlling+false+discovery+rate)

## CLASSIC-39 Storey q-value
```yaml
knowledge_item.v2:
  doc_id: "paper_classic_storey_2003_qvalue"
  version: "v2"
  species: "multi_species"
  blueprint_scope: knowledge_governance
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-26T20:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Storey JD and Tibshirani R. *Statistical significance for genomewide studies* (2003).
- Year: 2003.
- DOI/PMID: DOI `10.1073/pnas.1530509100`.
- Species/data: genome-wide multiple testing.
- GeneAgent use: explains q-value and genome-scale testing language.
- Boundary/risk: p-value dependence structures require caution.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=Storey+Tibshirani+2003+Statistical+significance+genomewide+studies)

## CLASSIC-40 Li Durbin BWA
```yaml
knowledge_item.v2:
  doc_id: "paper_classic_li_durbin_bwa_2009"
  version: "v2"
  species: "multi_species"
  blueprint_scope: genotype_processing
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-26T20:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Li H and Durbin R. *Fast and accurate short read alignment with Burrows-Wheeler transform* (2009).
- Year: 2009.
- DOI/PMID: DOI `10.1093/bioinformatics/btp324`.
- Species/data: sequencing alignment.
- GeneAgent use: supports WGS-derived VCF provenance explanation.
- Boundary/risk: alignment parameters are upstream of GeneAgent's current four blueprints.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=Li+Durbin+2009+BWA+Burrows-Wheeler+transform)

## CLASSIC-41 McKenna GATK
```yaml
knowledge_item.v2:
  doc_id: "paper_classic_mckenna_gatk_2010"
  version: "v2"
  species: "multi_species"
  blueprint_scope: genotype_processing
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-26T20:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: McKenna A et al. *The Genome Analysis Toolkit: a MapReduce framework for analyzing next-generation DNA sequencing data* (2010).
- Year: 2010.
- DOI/PMID: DOI `10.1101/gr.107524.110`.
- Species/data: sequencing variant discovery.
- GeneAgent use: explains upstream variant-calling provenance and quality annotations.
- Boundary/risk: current GeneAgent does not run GATK as a core tool.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=McKenna+2010+Genome+Analysis+Toolkit)

## CLASSIC-42 Browning haplotype phase
```yaml
knowledge_item.v2:
  doc_id: "paper_classic_browning_2007_phase"
  version: "v2"
  species: "multi_species"
  blueprint_scope: genotype_processing
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-26T20:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Browning SR and Browning BL. *Rapid and accurate haplotype phasing and missing-data inference for whole-genome association studies* (2007).
- Year: 2007.
- DOI/PMID: DOI `10.1086/521987`.
- Species/data: phasing and missing genotype inference.
- GeneAgent use: supports imputation/phasing provenance checks before downstream PCA or prediction.
- Boundary/risk: reference population design is species and breed dependent.
- Source links: [Google Scholar](https://scholar.google.com/scholar?q=Browning+Browning+2007+Rapid+accurate+haplotype+phasing)
