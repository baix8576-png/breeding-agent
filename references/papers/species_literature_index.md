# Species Literature Index

This index routes GeneAgent knowledge retrieval by species while keeping detailed evidence in paper-card packs.

## Cattle literature index
```yaml
knowledge_item.v2:
  doc_id: "index_species_cattle_literature"
  version: "v2"
  species: "bos_taurus"
  blueprint_scope: knowledge_governance
  evidence_level: "expert_opinion"
  source: "internal_note"
  updated_at: "2026-05-26T20:20:00+08:00"
  owner: "popgen_quantgen"
```
- Primary packs: `genomic_prediction_core_papers_v1.md`, `grm_core_papers_v1.md`, `animal_genomics_recent_high_impact_2022_2026.md`.
- Strong recent anchors: FarmGTEx cattle regulatory atlas, cattle single-cell atlas, bovine pangenome, indicine cattle diversity.
- Workflow fit: GRM, GBLUP, ssGBLUP, PCA, selection signatures, feed efficiency, fertility, methane/climate traits.
- Retrieval keywords: cattle, dairy, beef, Bos taurus, Bos indicus, FarmGTEx, CattleGTEx, pangenome, GBLUP.
- Curation warning: dairy, beef, taurine, indicine, yak, and crossbred evidence must not be merged without population-label review.

## Pig literature index
```yaml
knowledge_item.v2:
  doc_id: "index_species_pig_literature"
  version: "v2"
  species: "sus_scrofa"
  blueprint_scope: knowledge_governance
  evidence_level: "expert_opinion"
  source: "internal_note"
  updated_at: "2026-05-26T20:20:00+08:00"
  owner: "popgen_quantgen"
```
- Primary packs: `animal_genomics_recent_high_impact_2022_2026.md`, `genomic_prediction_core_papers_v1.md`, `qc_core_papers_v1.md`.
- Strong recent anchors: PigGTEx, pig pangenome, hybrid pig allele-specific regulation, pig genomic prediction review/benchmark.
- Workflow fit: line-specific QC, cross-line prediction, heterosis context, regulatory variant interpretation.
- Retrieval keywords: pig, Sus scrofa, PigGTEx, allele-specific, pangenome, cross-line prediction.
- Curation warning: commercial line structure and family relationships can inflate apparent model accuracy.

## Poultry literature index
```yaml
knowledge_item.v2:
  doc_id: "index_species_poultry_literature"
  version: "v2"
  species: "gallus_gallus"
  blueprint_scope: knowledge_governance
  evidence_level: "expert_opinion"
  source: "internal_note"
  updated_at: "2026-05-26T20:20:00+08:00"
  owner: "popgen_quantgen"
```
- Primary packs: `animal_genomics_recent_high_impact_2022_2026.md`, `pca_core_papers_v1.md`, `qc_core_papers_v1.md`.
- Strong recent anchors: ChickenGTEx, chicken pangenome/SV candidates, chicken single-cell atlas candidates.
- Workflow fit: PCA/structure, GWAS/QTL interpretation, genomic prediction in high-intensity commercial lines.
- Retrieval keywords: chicken, poultry, Gallus gallus, ChickenGTEx, egg traits, broiler, layer.
- Curation warning: proprietary line data and strong family structure require careful validation splits.

## Sheep goat literature index
```yaml
knowledge_item.v2:
  doc_id: "index_species_small_ruminant_literature"
  version: "v2"
  species: "small_ruminants"
  blueprint_scope: knowledge_governance
  evidence_level: "expert_opinion"
  source: "internal_note"
  updated_at: "2026-05-26T20:20:00+08:00"
  owner: "popgen_quantgen"
```
- Primary packs: `animal_genomics_recent_high_impact_2022_2026.md`, `pca_core_papers_v1.md`, `genomic_prediction_core_papers_v1.md`.
- Strong recent anchors: sheep pangenome, sheep regulatory atlas, goat pangenome, small-ruminant adaptation studies.
- Workflow fit: population structure, adaptation, cross-flock prediction, wool/meat/milk trait interpretation.
- Retrieval keywords: sheep, goat, Ovis aries, Capra hircus, small ruminant, adaptation, wool, flock.
- Curation warning: breed geography and management covariates can dominate population-genomic signals.

## Aquaculture literature index
```yaml
knowledge_item.v2:
  doc_id: "index_species_aquaculture_literature"
  version: "v2"
  species: "aquaculture_multi_species"
  blueprint_scope: knowledge_governance
  evidence_level: "expert_opinion"
  source: "internal_note"
  updated_at: "2026-05-26T20:20:00+08:00"
  owner: "popgen_quantgen"
```
- Primary packs: `animal_genomics_recent_high_impact_2022_2026.md`.
- Strong recent anchors: salmon, tilapia, shrimp genomic selection and aquaculture pangenome candidates.
- Workflow fit: future V2.x expansion; current core blueprints can inform QC/PCA/prediction but species defaults are not yet validated.
- Retrieval keywords: aquaculture, salmon, tilapia, shrimp, disease resistance, family structure.
- Curation warning: aquatic species have very different mating systems, family structures, and genome architectures.

## Cattle species overlay defaults

```yaml
knowledge_item.v2:
  doc_id: species_overlay_cattle_defaults
  version: v2
  species: bos_taurus
  blueprint_scope: knowledge_governance
  evidence_level: expert_opinion
  source: internal_note
  updated_at: 2026-06-06T21:30:00+08:00
  owner: popgen_quantgen
```

Cattle analyses should distinguish dairy, beef, taurine, indicine, crossbred, yak/related species, and management system context before interpreting structure, prediction, or candidate loci.

Default cautions:
- dairy and beef datasets can have different selection histories and phenotype recording systems
- taurine and indicine contrasts can dominate PCA, Fst, and prediction transferability
- dairy cow phenotypes often involve repeated records, parity, herd-year-season, and EBV/proof-derived targets
- feed efficiency, fertility, methane, heat tolerance, and disease resistance often need environment and management covariates
- pangenome, SV/CNV, FarmGTEx, and cattle regulatory atlas evidence should keep assembly and breed context visible

Workflow hints:
- use subgroup validation for breed, production type, and herd when available
- avoid global HWE or global missingness filters that remove indicine or crossbred subgroups without review
- treat cross-breed prediction as a transferability question, not a pooled accuracy claim

Operational overlay fields:
- common input types: SNP array PLINK files, imputed WGS VCF, pedigree, repeated phenotypes, herd-year-season/parity covariates, breed or production-type metadata
- typical marker densities: 50K dairy/beef arrays, medium/high-density arrays, imputed sequence panels, and emerging pangenome/SV resources
- reference genome caveats: assembly build and Bos taurus/Bos indicus/yak relatedness must be recorded for GWAS, liftover, and candidate genes
- common traits: milk, growth, carcass, fertility, health, feed efficiency, methane, heat tolerance, adaptation
- default QC cautions: stratify missingness and HWE review by breed/production group when mixed cohorts are present
- population-structure pitfalls: taurine-indicine, dairy-beef, herd, and family structure can dominate PCA and prediction validation
- literature anchors: FarmGTEx, cattle regulatory atlas, cattle single-cell atlas, bovine pangenome, indicine diversity, VanRaden/ssGBLUP literature
- report wording boundary: "Cattle defaults are subgroup-aware planning guidance; production type and breed transferability must be explicitly reported."

## Pig species overlay defaults

```yaml
knowledge_item.v2:
  doc_id: species_overlay_pig_defaults
  version: v2
  species: sus_scrofa
  blueprint_scope: knowledge_governance
  evidence_level: expert_opinion
  source: internal_note
  updated_at: 2026-06-06T21:30:00+08:00
  owner: popgen_quantgen
```

Pig analyses should preserve commercial line, crossbred, and family design context. Line structure and relatedness can strongly affect PCA, GWAS, and genomic prediction metrics.

Default cautions:
- nucleus, multiplier, and commercial crossbred animals may represent different target populations
- litter, family, farm, and batch effects can be confounded with traits
- genotype imputation and prediction transfer should be evaluated across lines
- PigGTEx and regulatory resources are useful evidence layers but may not match every commercial line or tissue context
- heterosis or crossbred performance traits require careful phenotype definition and validation split design

Workflow hints:
- keep line and family metadata visible in QC, PCA, GWAS, and prediction reports
- use family- or line-blocked validation when deployment is cross-line
- do not interpret line-separated PCA clusters as biological ancestry without metadata review

Operational overlay fields:
- common input types: SNP array PLINK files, imputed sequence VCF, line/crossbred labels, litter/family metadata, farm/batch covariates, carcass/meat/reproduction phenotypes
- typical marker densities: commercial SNP arrays, imputed high-density panels, WGS subsets, pangenome/SV resources for research contexts
- reference genome caveats: Sus scrofa assembly version and line-specific reference bias must be visible for candidate-region interpretation
- common traits: growth, feed efficiency, meat quality, litter size, fertility, disease resistance, immune traits, crossbred performance
- default QC cautions: review missingness and allele frequency by line, farm, batch, and family before pooled filtering
- population-structure pitfalls: nucleus versus commercial crossbred design can inflate random-CV accuracy and GWAS signals
- literature anchors: PigGTEx, pig pangenome, hybrid pig allele-specific regulation, pig genomic prediction and imputation studies
- report wording boundary: "Pig results must state whether inference targets a line, a crossbred population, or transfer between them."

## Poultry species overlay defaults

```yaml
knowledge_item.v2:
  doc_id: species_overlay_poultry_defaults
  version: v2
  species: gallus_gallus
  blueprint_scope: knowledge_governance
  evidence_level: expert_opinion
  source: internal_note
  updated_at: 2026-06-06T21:30:00+08:00
  owner: popgen_quantgen
```

Poultry analyses should account for commercial line structure, high selection intensity, family design, sex-specific traits, and production-type differences between layer and broiler systems.

Default cautions:
- line and family structure can inflate apparent prediction accuracy
- hatch, generation, cage/pen, farm, and batch variables may be important covariates
- egg, growth, carcass, immune, and behavior traits often require different phenotype dictionaries
- ChickenGTEx and regulatory evidence should be tied to tissue, developmental stage, and line context
- proprietary line labels may be masked; validation groups still need a stable anonymous grouping variable

Workflow hints:
- prefer line- or generation-aware validation for deployment claims
- report sex and production type where relevant
- treat unknown line labels as a limitation, not as an excuse to ignore structure

Operational overlay fields:
- common input types: SNP array genotypes, line/generation metadata, sex, hatch/batch/farm covariates, egg/growth/carcass/immune phenotypes
- typical marker densities: commercial poultry arrays, high-density research panels, imputed WGS, ChickenGTEx/regulatory resources for interpretation
- reference genome caveats: Gallus gallus assembly and line-specific annotation gaps must be recorded for candidate genes and regulatory interpretation
- common traits: egg production, growth, feed efficiency, carcass, immune response, disease resistance, behavior, reproduction
- default QC cautions: line, hatch, sex, and generation effects can create subgroup-specific missingness or allele-frequency shifts
- population-structure pitfalls: proprietary or masked line labels still need anonymous grouping for validation and PCA interpretation
- literature anchors: ChickenGTEx, poultry genomic prediction benchmarks, chicken pangenome/SV studies, GWAS/QTL literature
- report wording boundary: "Poultry reports must not convert commercial-line clusters into biological labels unless validated metadata supports the label."

## Sheep and goat species overlay defaults

```yaml
knowledge_item.v2:
  doc_id: species_overlay_sheep_goat_defaults
  version: v2
  species: small_ruminants
  blueprint_scope: knowledge_governance
  evidence_level: expert_opinion
  source: internal_note
  updated_at: 2026-06-06T21:30:00+08:00
  owner: popgen_quantgen
```

Small-ruminant analyses should keep breed geography, flock structure, adaptation context, and trait system visible. Sheep and goats are often studied for adaptation, wool/fiber, meat, milk, fertility, disease resistance, and local breed conservation.

Default cautions:
- breed geography and management can dominate population-genomic signals
- flock and family structure can affect GWAS, ROH, and prediction validation
- adaptation scans require explicit population definitions and environmental context
- pangenome or regulatory evidence may be less complete than cattle or pig resources
- sheep and goat evidence should not be merged without species and assembly review

Workflow hints:
- use population labels from metadata, not automatic PCA naming
- preserve environmental or geographic variables for adaptation interpretation
- report conservation or management recommendations only after expert review

Operational overlay fields:
- common input types: SNP array or WGS genotypes, flock/breed/geography metadata, pedigree when available, wool/meat/milk/fertility/disease phenotypes, environmental covariates
- typical marker densities: medium-density sheep/goat arrays, imputed panels, WGS subsets, pangenome/regulatory resources for selected research tasks
- reference genome caveats: sheep and goat assemblies are not interchangeable; coordinate and annotation transfer must be reported
- common traits: wool/fiber, meat, milk, fertility, disease resistance, adaptation, conservation, tail/fat deposition phenotypes
- default QC cautions: small breed sample sizes and local management can make global filters destructive
- population-structure pitfalls: geography, flock, breed history, and recent relatedness can confound ROH, Fst, PCA, and GWAS
- literature anchors: sheep pangenome, sheep epigenome atlas, goat pangenome, small-ruminant adaptation studies, Rambouillet/goat prediction papers
- report wording boundary: "Small-ruminant results should be framed around species, breed, flock, and environment, not generic livestock defaults."

## Aquaculture species overlay defaults

```yaml
knowledge_item.v2:
  doc_id: species_overlay_aquaculture_defaults
  version: v2
  species: aquaculture_multi_species
  blueprint_scope: knowledge_governance
  evidence_level: expert_opinion
  source: internal_note
  updated_at: 2026-06-06T21:30:00+08:00
  owner: popgen_quantgen
```

Aquaculture species are not one workflow class. Salmonids, tilapia, shrimp, carp, oysters, and other farmed aquatic species differ in ploidy, family structure, reproduction, genome architecture, disease traits, and recording systems.

Default cautions:
- family-based breeding designs can make random validation overly optimistic
- polyploidy, duplicated genomes, or unusual recombination patterns may require species-specific methods
- disease challenge traits need challenge design and tank/batch covariates
- sex determination and environmental sex effects can vary by species
- current GeneAgent defaults are advisory until species-specific wrappers and benchmarks are validated

Workflow hints:
- use family, tank, hatchery, and generation metadata when available
- treat aquaculture genomic prediction as a target-population validation problem
- route uncertain species-specific settings to expert review before remote execution

Operational overlay fields:
- common input types: SNP array or sequencing genotypes, family/tank/hatchery metadata, challenge-test records, growth and disease phenotypes, sex/ploidy metadata where relevant
- typical marker densities: species-specific SNP panels, low-pass or WGS-derived markers, imputed panels, and emerging pangenome resources
- reference genome caveats: genome duplication, ploidy, contig quality, and species-specific recombination can invalidate terrestrial livestock defaults
- common traits: growth, fillet or body composition, disease resistance, salinity/temperature tolerance, survival, maturation, reproduction
- default QC cautions: family-based sampling and tank/batch effects must be visible before filtering, PCA, or validation
- population-structure pitfalls: hatchery/family structure can dominate random validation and mimic population differentiation
- literature anchors: Atlantic salmon genomic prediction, Nile tilapia and shrimp genomic selection, aquaculture pangenome/reference-genome reviews
- report wording boundary: "Aquaculture settings require species-specific validation; GeneAgent defaults are advisory until a species wrapper and benchmark exist."
