# Species Literature Index

This index routes GeneAgent knowledge retrieval by species while keeping detailed evidence in paper-card packs.

## Cattle literature index
```yaml
knowledge_item.v2:
  doc_id: "index_species_cattle_literature"
  version: "v2"
  species: "bos_taurus"
  blueprint_scope: "shared"
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
  blueprint_scope: "shared"
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
  blueprint_scope: "shared"
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
  blueprint_scope: "shared"
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
  blueprint_scope: "shared"
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

