# Functional Genomics Annotation Domain

This file defines the interpretation domain used after GWAS, QTL, fine-mapping, selection scans, ROH islands, and other candidate-region discovery steps. It keeps functional evidence separate from statistical discovery and from causal validation.

## Domain scope and scientific intent

```yaml
knowledge_item.v2:
  doc_id: domain_functional_genomics_annotation_scope
  version: v2
  species: multi_species
  blueprint_scope: association_mapping
  evidence_level: sop
  source: sop
  updated_at: 2026-06-06T00:00:00+08:00
  owner: popgen_quantgen
```

Primary `domain_scope`: `functional_genomics_annotation`.

Functional genomics annotation explains what is known near or inside a candidate variant, marker, window, haplotype block, QTL interval, or selected region. It does not prove that a candidate gene or variant is causal. In animal genetics and breeding, annotation must account for uneven genome assemblies, breed-biased references, incomplete gene models, pangenome and structural variation, tissue specificity, developmental stage, and trait biology.

Inputs that can trigger this domain:
- GWAS lead markers and regional association intervals
- QTL or fine-mapping credible sets
- selection-signature candidate windows
- ROH islands or diversity outlier regions
- prediction-feature importance summaries when the model is explainable
- user-supplied candidate genes or regions

Evidence layers:

| Evidence layer | Typical sources | Use in report |
|---|---|---|
| gene model overlap | GFF/GTF, Ensembl/NCBI gene annotation, species genome annotation | identify nearby or overlapping genes |
| regulatory evidence | promoter/enhancer marks, chromatin accessibility, TF motifs, conservation | prioritize plausible regulatory mechanisms |
| pangenome/SV/CNV | pangenome graphs, assemblies, SV/CNV calls, breed-specific presence/absence | explain variants missed by SNP-only scans |
| eQTL/FarmGTEx | tissue eQTL, sQTL, TWAS-like summaries when available | connect loci to gene regulation |
| single-cell context | tissue/cell-type atlases and marker genes | locate candidate expression in relevant cell states |
| pathway/literature | GO/KEGG/Reactome, QTLdb, peer-reviewed studies | provide biological context, not proof |

Current execution bridge:
- no dedicated production execution blueprint yet
- report and retrieval layer can summarize evidence traces
- candidate interpretation from `association_mapping_gwas_qtl` and `selection_signatures` should route here

Risk boundary: annotation produces ranked hypotheses and evidence traces. It must not be phrased as causal validation, marker deployment readiness, or breeding decision approval.

## Gene model and coordinate annotation policy

```yaml
knowledge_item.v2:
  doc_id: domain_functional_genomics_annotation_gene_model_policy
  version: v2
  species: multi_species
  blueprint_scope: association_mapping
  evidence_level: sop
  source: sop
  updated_at: 2026-06-06T00:00:00+08:00
  owner: popgen_quantgen
```

Gene model annotation is the first explanatory layer for candidate regions, but nearest-gene logic is only a starting point.

Required region fields:
- chromosome, start, end, and reference assembly
- original marker ID or window ID
- source analysis domain and method
- trait, population contrast, or phenotype context
- coordinate system and liftover status when relevant

Minimum annotation outputs:
- overlapping genes and transcript IDs
- nearest upstream and downstream genes with distances
- coding consequence only when variant representation supports it
- UTR, intron, intergenic, splice, or promoter-proximal labels where annotation supports them
- source annotation version and species build
- unresolved or unannotated region counts

Do not overclaim:
- nearest gene equals causal gene
- a gene symbol match across species proves identical function
- a gene model version is interchangeable across assemblies
- an intergenic marker has no function without regulatory annotation

Manual-review conditions:
- candidate region spans many genes
- species annotation is sparse or assembly-specific
- region contains duplicated gene families, immune loci, olfactory receptors, or structural-variant-rich segments
- candidate gene is inferred from comparative genomics rather than the studied species

Risk boundary: gene overlap and distance are coordinates, not mechanisms. Gene model results should be reported as evidence candidates with traceable annotation source and assembly.

## Regulatory and pathway evidence policy

```yaml
knowledge_item.v2:
  doc_id: domain_functional_genomics_annotation_regulatory_evidence_policy
  version: v2
  species: multi_species
  blueprint_scope: association_mapping
  evidence_level: expert_opinion
  source: sop
  updated_at: 2026-06-06T00:00:00+08:00
  owner: popgen_quantgen
```

Regulatory annotation matters because many animal-genomics signals are noncoding. The interpretation should identify plausible regulatory context while preserving tissue, developmental, species, and assay limitations.

Evidence types:
- promoter or enhancer proximity
- ATAC-seq or DNase accessibility
- histone marks such as H3K27ac or H3K4me3
- conserved elements and constrained sequence
- transcription factor motif gain/loss when allele-specific sequence is available
- pathway, GO, KEGG, Reactome, or curated trait ontology terms

Required caveats:
- regulatory tracks are tissue and stage specific
- cross-species regulatory transfer is supporting evidence only
- pathway enrichment depends on background gene set and region-to-gene mapping
- motif predictions are weak without expression or chromatin support
- public annotations may not represent the studied breed, line, or environment

Report policy:
- keep evidence layer names visible
- cite the exact annotation resource and version
- separate direct overlap evidence from inferred gene-set enrichment
- mark evidence as `supporting`, `conflicting`, `missing`, or `not_applicable`
- avoid a single combined score unless its ingredients and weights are reviewed

Risk boundary: regulatory and pathway evidence can explain plausibility, but it cannot rescue a poorly controlled GWAS or selection scan.

## Pangenome, SV, and CNV interpretation policy

```yaml
knowledge_item.v2:
  doc_id: domain_functional_genomics_annotation_pangenome_sv_cnv_policy
  version: v2
  species: multi_species
  blueprint_scope: association_mapping
  evidence_level: sop
  source: sop
  updated_at: 2026-06-06T00:00:00+08:00
  owner: popgen_quantgen
```

Pangenome, structural-variant, and copy-number evidence can explain signals that SNP-only analyses miss. This is increasingly important in livestock and aquaculture species where breeds, lines, and wild relatives may carry sequence absent from a single reference.

Use pangenome/SV/CNV evidence when:
- lead markers sit near assembly gaps, segmental duplications, or breed-specific regions
- GWAS or selection peaks have weak SNP annotation but strong local SV evidence
- candidate genes are affected by presence/absence variation
- CNV burden or copy number differs by breed, line, phenotype, or population contrast
- pangenome papers or assemblies show alternative haplotypes in the region

Minimum fields:
- variant type: deletion, insertion, inversion, duplication, translocation, CNV, presence/absence
- coordinate representation and genome build
- detection method and confidence level
- whether genotypes are individual-level, population-level, or literature-derived
- relationship to candidate SNP/window interval
- reference or pangenome resource used

Do not overclaim:
- pangenome overlap is not proof of functional effect
- SV calls from one breed do not automatically transfer to another
- CNV region boundaries are often method-dependent
- graph coordinates and linear-reference coordinates need explicit mapping

Risk boundary: SV/CNV and pangenome evidence are powerful but representation-sensitive. GeneAgent should keep them as evidence layers unless the input dataset directly supports the variant class.

## eQTL, FarmGTEx, and single-cell evidence policy

```yaml
knowledge_item.v2:
  doc_id: domain_functional_genomics_annotation_eqtl_single_cell_policy
  version: v2
  species: multi_species
  blueprint_scope: association_mapping
  evidence_level: peer_reviewed
  source: sop
  updated_at: 2026-06-06T00:00:00+08:00
  owner: popgen_quantgen
```

Molecular QTL and cell atlas evidence help connect candidate regions to gene regulation, tissue relevance, and cell-type context. For animal breeding traits, this evidence is strongest when the tissue, developmental stage, sex, breed, and environmental context match the biological question.

Evidence sources:
- FarmGTEx, PigGTEx, ChickenGTEx, and cattle regulatory atlas style resources
- tissue eQTL, sQTL, caQTL, methylation QTL, or molecular association summaries
- single-cell or single-nucleus expression atlases
- cell-type marker genes and tissue specificity scores
- transcript isoform or allele-specific expression evidence

Planning checks:
- match species and genome build
- check whether the candidate variant or a linked marker exists in the molecular QTL resource
- record tissue and cell type relevance to the trait
- distinguish cis evidence from trans evidence
- state whether evidence comes from the same species, a related species, or a general model organism

Interpretation labels:
- `direct_support`: candidate variant or region is linked to candidate gene expression in a relevant tissue
- `context_support`: candidate gene is expressed in relevant tissue or cell type
- `indirect_support`: related pathway or homolog evidence only
- `missing_evidence`: no matching molecular data available
- `conflicting_evidence`: molecular evidence points to another gene or tissue

Risk boundary: eQTL and single-cell evidence are context dependent. They should prioritize candidate mechanisms, not declare causality by themselves.

## Candidate reporting and evidence ranking policy

```yaml
knowledge_item.v2:
  doc_id: domain_functional_genomics_annotation_candidate_reporting_policy
  version: v2
  species: multi_species
  blueprint_scope: association_mapping
  evidence_level: sop
  source: sop
  updated_at: 2026-06-06T00:00:00+08:00
  owner: popgen_quantgen
```

Functional annotation reports should make evidence traceable and uncertainty visible. A good report helps the user choose follow-up experiments or validation analyses; it does not collapse all evidence into a single unsupported biological story.

Minimum candidate table columns:

| Column | Meaning |
|---|---|
| `candidate_id` | stable region, marker, or gene identifier |
| `source_domain` | GWAS, QTL, selection scan, ROH, prediction feature, or user-supplied |
| `assembly` | genome build used for coordinates |
| `region` | chromosome/start/end or marker position |
| `gene_model_evidence` | overlap, nearest gene, transcript, or consequence |
| `regulatory_evidence` | chromatin, motif, enhancer/promoter, pathway context |
| `pangenome_sv_cnv_evidence` | structural or presence/absence support |
| `eqtl_single_cell_evidence` | molecular QTL or tissue/cell support |
| `literature_support` | linked paper card, DOI, PMID, or curated source |
| `evidence_label` | direct, context, indirect, missing, conflicting |
| `do_not_overclaim_note` | one-line boundary for interpretation |

Ranking policy:
- rank by evidence completeness and biological relevance, not by nearest-gene distance alone
- keep statistical evidence from the upstream domain visible
- show negative or missing evidence instead of omitting it
- separate candidate prioritization from validation recommendation
- keep all source links, annotation versions, and region definitions auditable

Risk boundary: a polished candidate table can look more certain than the evidence allows. The report must preserve why a candidate is plausible and why it is still unvalidated.

## Execution bridge and current automation boundary

```yaml
knowledge_item.v2:
  doc_id: domain_functional_genomics_annotation_execution_bridge
  version: v2
  species: multi_species
  blueprint_scope: association_mapping
  evidence_level: sop
  source: sop
  updated_at: 2026-06-06T00:00:00+08:00
  owner: popgen_quantgen
```

Functional genomics annotation is currently a knowledge and report-interpretation domain in GeneAgent. It has no dedicated production execution wrapper comparable to `run_gwas.sh` or `run_population_structure_diversity.sh`.

Current bridge:

| Upstream source | Functional annotation use | Current status |
|---|---|---|
| GWAS lead marker or region | candidate gene and regulatory interpretation | knowledge/reporting supported |
| QTL or fine-mapping interval | evidence-layer summary and caveats | knowledge/reporting supported |
| selection-signature window | candidate region explanation | knowledge/reporting supported |
| ROH island | gene and pathway context | knowledge/reporting supported |
| pangenome/SV/CNV resource | structural evidence summary | knowledge/reporting supported when source is curated |
| eQTL/FarmGTEx/single-cell resource | molecular and cell-context evidence | knowledge/reporting supported when source is curated |

Not yet automated:
- genome-wide gene overlap execution
- variant consequence annotation with a fixed toolchain
- pangenome graph query
- SV/CNV genotyping or annotation
- eQTL colocalization or TWAS
- pathway enrichment with reviewed background sets
- candidate-prioritization scoring engine

Submit boundary:
- GeneAgent may draft a plan or report section using curated knowledge cards.
- Real remote execution must remain blocked until the chosen annotation tool, reference files, resource paths, output schema, report template, and tests are present.
- Raw FASTA/GFF/GTF/VCF/BAM/reference panels must remain outside Git and inside approved local or remote work roots.

Risk boundary: current automation can explain and structure evidence, but it must not invent annotation results or pretend that external databases were queried when they were not.

## Coordinate liftover check

```yaml
knowledge_item.v2:
  doc_id: domain_functional_genomics_annotation_coordinate_liftover_check
  version: v2
  species: multi_species
  blueprint_scope: association_mapping
  evidence_level: sop
  source: sop
  updated_at: 2026-06-06T21:30:00+08:00
  owner: popgen_quantgen
```

Functional annotation starts with coordinates. Before a candidate region is compared with genes, QTL, eQTL, pangenome, SV, or single-cell resources, GeneAgent must confirm that the coordinate system is compatible.

Coordinate checklist:
- source analysis domain and candidate ID
- chromosome, start, end, and genome assembly
- whether coordinates are one-based or zero-based in the source artifact
- whether interval end is inclusive or half-open
- liftover source assembly and target assembly if translation occurred
- number of unresolved or multi-mapped candidates
- original coordinate retained in the report table

Blocking conditions:
- candidate region lacks assembly
- annotation resource uses a different assembly and no liftover policy is available
- chromosome naming cannot be mapped
- liftover creates multiple incompatible target intervals
- candidate interval crosses contig or assembly-gap ambiguity

Risk boundary: annotation on the wrong assembly can make the nearest gene, QTL overlap, and regulatory evidence entirely wrong.

## Tissue relevance matrix

```yaml
knowledge_item.v2:
  doc_id: domain_functional_genomics_annotation_tissue_relevance_matrix
  version: v2
  species: multi_species
  blueprint_scope: association_mapping
  evidence_level: expert_opinion
  source: sop
  updated_at: 2026-06-06T21:30:00+08:00
  owner: popgen_quantgen
```

Tissue and cell relevance should be recorded as a matrix rather than a single narrative sentence. This is especially important when using FarmGTEx, PigGTEx, ChickenGTEx, cattle regulatory atlases, single-cell atlases, or cross-species expression evidence.

Recommended matrix columns:
- candidate gene or region
- trait or biological process
- tissue or cell type
- evidence source and species
- genome build or annotation version
- evidence type: expression, eQTL, sQTL, chromatin, marker gene, literature
- relevance label: direct, context, indirect, missing, conflicting, or not applicable
- caveat about breed, age, sex, environment, or developmental stage

Interpretation rules:
- prioritize tissues directly related to the trait biology
- distinguish gene expression from variant-to-expression association
- keep single-cell cell-type evidence separate from bulk tissue evidence
- flag cross-species evidence as indirect unless species-specific data exist
- show missing evidence instead of implying absence of biology

Risk boundary: tissue relevance is context-specific. A gene expressed in many tissues is not automatically the causal gene for the studied trait.

## SV gene disruption policy

```yaml
knowledge_item.v2:
  doc_id: domain_functional_genomics_annotation_sv_gene_disruption_policy
  version: v2
  species: multi_species
  blueprint_scope: association_mapping
  evidence_level: expert_opinion
  source: sop
  updated_at: 2026-06-06T21:30:00+08:00
  owner: popgen_quantgen
```

Structural variants and copy-number variants can disrupt genes, regulatory elements, dosage, or haplotype context. Their interpretation must distinguish direct cohort evidence from literature or pangenome-derived context.

SV/CNV annotation fields:
- variant class: deletion, insertion, inversion, duplication, translocation, CNV, or presence/absence
- coordinate system and assembly
- detection source: user dataset, public pangenome, paper card, or curated database
- overlap with exon, intron, UTR, promoter, enhancer, or intergenic region
- affected transcript or gene model version
- dosage or presence/absence evidence when available
- relationship to GWAS/QTL/selection/ROH candidate interval

Do not overclaim:
- an SV overlap does not prove gene disruption without breakpoint and transcript context
- CNV dosage evidence from another breed may not apply to the current cohort
- pangenome presence/absence evidence is not equivalent to individual genotypes
- structural annotation should not be mixed with SNP-only evidence without stating representation differences

Risk boundary: SV/CNV evidence can be decisive when directly genotyped, but only contextual when inferred from literature or incompatible resources.
