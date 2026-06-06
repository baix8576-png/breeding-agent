# Genotype Processing Domain

This file covers genotype processing after input readiness QC. It separates format normalization, allele alignment, liftover, phasing, and imputation from the narrower `data_preparation_qc` domain.

## Domain scope and processing boundary

```yaml
knowledge_item.v2:
  doc_id: domain_genotype_processing_scope
  version: v2
  species: multi_species
  blueprint_scope: genotype_processing
  evidence_level: sop
  source: sop
  updated_at: 2026-06-06T00:00:00+08:00
  owner: popgen_quantgen
```

Primary `domain_scope`: `genotype_processing`.

Genotype processing starts after GeneAgent has identified valid genotype-bearing inputs and sidecars. Its purpose is to make genotype data technically comparable across tools, reference builds, chips, sequence panels, and downstream scientific domains.

Core method families:

| Method family | Typical operations | Downstream domains |
|---|---|---|
| `format_normalization` | VCF normalization, PLINK conversion, variant ID repair, bgzip/index checks | all genotype-based domains |
| `allele_alignment` | REF/ALT and A1/A2 harmonization, strand ambiguity handling, reference allele checks | GWAS, GRM, prediction, imputation |
| `liftover` | coordinate translation across genome builds, contig-name mapping, post-liftover validation | meta-analysis, annotation, pangenome-aware reports |
| `phasing_imputation` | haplotype phasing, reference-panel imputation, dosage handling | selection scans, GWAS, prediction, fine mapping |

Current execution bridge:
- `qc_pipeline` for bounded format inventory and first-pass VCF/PLINK QC.
- `scripts/genotype_processing/run_genotype_qc.sh` for existing QC-oriented wrapper behavior.
- No dedicated automated phasing, imputation, or liftover blueprint is complete yet.

Not in scope:
- sample filtering decisions already covered by `data_preparation_qc`
- population structure interpretation
- association, selection, or prediction inference
- functional proof from candidate regions

Risk boundary: processing can make files tool-compatible, but it can also silently invert alleles, change coordinates, or alter marker sets. Any nontrivial transformation must be reversible or explicitly reported.

## Format normalization and conversion policy

```yaml
knowledge_item.v2:
  doc_id: domain_genotype_processing_format_normalization_policy
  version: v2
  species: multi_species
  blueprint_scope: genotype_processing
  evidence_level: sop
  source: sop
  updated_at: 2026-06-06T00:00:00+08:00
  owner: popgen_quantgen
```

Format normalization prepares VCF, BCF, PLINK binary, PLINK2 PGEN, and BAM-derived genotype calls for consistent downstream use. The main output should be a declared analysis-ready dataset plus a manifest that states exactly what changed.

Minimum checks before conversion:
- VCF header contains sample columns and genotype fields expected by the selected tool.
- Compressed VCF inputs are bgzip-compatible when random access is needed.
- Complete PLINK triplets have matching prefixes and sample counts.
- Variant IDs are stable or a deterministic ID template is declared.
- Contig names, genome build, and coordinate conventions are recorded when known.

Recommended normalization decisions:
- Split or retain multiallelic variants according to downstream method requirements.
- Left-align and normalize indels only with the declared reference FASTA.
- Preserve original variant ID, chromosome, position, REF, ALT, and any renamed ID in an audit table.
- Keep unfiltered and filtered dataset pointers separate.
- Record whether dosage fields, hard calls, or genotype probabilities are being used.

Do not do automatically:
- infer a genome build from chromosome names alone
- change marker IDs without an old-to-new mapping artifact
- merge datasets that use different builds or allele codings without alignment checks
- treat PLINK `A1/A2` as equivalent to VCF `REF/ALT`

Expected artifacts:
- `results/genotype_processing/format_manifest.json`
- `results/genotype_processing/variant_rename_map.tsv`
- `results/genotype_processing/normalization_summary.tsv`
- report section listing command, tool version, reference assets, and retained marker count

Risk boundary: conversion success is not biological validation. A PLINK file created from a VCF can still be unusable for GWAS or prediction if allele orientation, IDs, or build metadata are wrong.

## Allele alignment policy

```yaml
knowledge_item.v2:
  doc_id: domain_genotype_processing_allele_alignment_policy
  version: v2
  species: multi_species
  blueprint_scope: genotype_processing
  evidence_level: sop
  source: sop
  updated_at: 2026-06-06T00:00:00+08:00
  owner: popgen_quantgen
```

Allele alignment is required whenever genotype data are compared across reference panels, SNP arrays, sequencing batches, published summary statistics, or external annotation resources. It is a scientific safety gate, not a cosmetic cleanup.

Minimum allele checks:
- REF allele matches the declared reference FASTA when a reference is available.
- PLINK A1/A2 meanings are not confused with effect allele, minor allele, or VCF ALT.
- Strand-ambiguous A/T and C/G SNPs are flagged before merging panels.
- Duplicate variant IDs and duplicate chromosome-position pairs are reviewed separately.
- Allele-frequency shifts across batches or breeds are inspected before flipping alleles.

Blocking conditions:
- unknown reference build and no trusted mapping table for cross-dataset merge
- high fraction of REF mismatches after reference check
- strand-ambiguous SNPs with no frequency or panel evidence
- summary-statistic allele columns that cannot be mapped to genotype alleles

Manual-review conditions:
- multi-allelic sites collapsed into biallelic records
- indels represented differently across tools
- breed-specific or chip-specific allele-frequency differences that could mimic strand problems
- pangenome or structural-variant regions where a single linear reference is insufficient

Risk boundary: automatic allele flipping can create confident but wrong associations, GRM entries, or imputed dosages. GeneAgent should report ambiguous allele states and block high-risk merges instead of guessing.

## Liftover and genome build policy

```yaml
knowledge_item.v2:
  doc_id: domain_genotype_processing_liftover_policy
  version: v2
  species: multi_species
  blueprint_scope: genotype_processing
  evidence_level: expert_opinion
  source: sop
  updated_at: 2026-06-06T00:00:00+08:00
  owner: popgen_quantgen
```

Liftover translates coordinates between genome builds. In animal genomics this is often complicated by assembly updates, breed-biased reference genomes, missing contigs, alternative scaffolds, and marker names that outlive their original coordinates.

Required inputs:
- source genome build
- target genome build
- chain file or curated coordinate map
- reference FASTA for post-liftover allele checks when available
- rule for unresolved, duplicated, or multi-mapping variants

Post-liftover checks:
- count lifted, unresolved, duplicated, and multi-mapped variants
- sort and normalize output coordinates
- verify REF/ALT where a target reference is available
- keep source coordinate columns in a mapping artifact
- check whether downstream annotation resources use the target build

Do not claim:
- that liftover validates alleles by itself
- that a lifted marker is identical across assemblies in repetitive or structural-variant regions
- that failed markers can be dropped without reporting possible ascertainment bias

Expected report language:
- source and target build
- tool or mapping resource used
- unresolved marker count and proportion
- whether allele re-check was performed
- consequences for GWAS, selection scans, prediction, or annotation

Risk boundary: coordinate translation changes the reference frame for every downstream result. It must be traceable enough that a candidate region can be audited back to the original build.

## Phasing and imputation policy

```yaml
knowledge_item.v2:
  doc_id: domain_genotype_processing_phasing_imputation_policy
  version: v2
  species: multi_species
  blueprint_scope: genotype_processing
  evidence_level: sop
  source: sop
  updated_at: 2026-06-06T00:00:00+08:00
  owner: popgen_quantgen
```

Phasing and imputation are required for many haplotype-based selection scans and can improve marker density for association mapping or prediction. They are not generic QC steps and should not run without reference-panel, pedigree, population, and validation context.

Planning inputs:
- target genotype dataset and genome build
- reference panel species, breed composition, marker density, and build
- pedigree availability if family-aware phasing is intended
- target output type: phased haplotypes, hard calls, dosage, or genotype probabilities
- validation design for imputation accuracy when truth or high-density subsets exist

Safety checks:
- target and reference panel use compatible genome build and allele coding
- sample overlap between target and reference panel is intentional and documented
- low-frequency and rare variants are evaluated separately from common variants
- imputation INFO, R2, dosage certainty, or equivalent quality metric is retained
- downstream tools know whether input is hard call or dosage

Current GeneAgent status:
- planning and reporting knowledge are supported in this domain file
- literature cards and parameter playbooks may guide method selection
- no production-grade automated Beagle, Eagle, Minimac, or species-specific imputation wrapper is currently guaranteed by the script directory

Not-yet-automated boundary:
- selecting an optimal reference panel
- chromosome-by-chromosome scatter/gather imputation
- post-imputation dosage filtering
- trio or pedigree-aware phasing policy
- validation reports stratified by breed, chip, MAF bin, or chromosome

Risk boundary: imputation can add many plausible genotypes and still bias downstream inference if the reference panel is mismatched. GeneAgent must label imputed data and propagate imputation quality into reports.

## Execution bridge and artifacts

```yaml
knowledge_item.v2:
  doc_id: domain_genotype_processing_execution_bridge
  version: v2
  species: multi_species
  blueprint_scope: genotype_processing
  evidence_level: sop
  source: sop
  updated_at: 2026-06-06T00:00:00+08:00
  owner: popgen_quantgen
```

The current script directory is intentionally conservative. It can support genotype readiness, first-pass VCF/PLINK checks, and documented format inventory, but advanced processing remains a planning and review layer until dedicated wrappers and safety gates are added.

Current bridge:

| Domain concern | Current execution status | Expected trace |
|---|---|---|
| VCF/PLINK inventory | supported through `run_genotype_qc.sh` | QC manifest and report |
| PLINK/bcftools first-pass stats | supported when tools and inputs exist | sample, variant, and VCF stats |
| format normalization plan | planning/reporting supported | proposed command and required sidecars |
| allele alignment | planning/reporting supported | alignment checklist and blocker list |
| liftover | knowledge/planning only | source/target build plan |
| phasing/imputation | knowledge/planning only | reference-panel and validation plan |

Remote execution expectations:
- generated commands must use POSIX paths and explicit `--threads`, `--memory-mb`, and `--tmp-dir` parameters
- wrapper outputs must stay inside the approved run root
- reference FASTA, chain files, and reference panels must be read-only inputs
- raw VCF/BAM/FASTQ/FASTA or protected reference data must not be committed to Git

Failure routing:
- missing reference FASTA or chain file blocks liftover/normalization
- allele mismatch blocks cross-dataset merge
- reference-panel mismatch blocks imputation submit
- ambiguous strand SNPs require review before automatic alignment
- output overwrite requires higher-level approval

Risk boundary: GeneAgent may prepare and explain genotype-processing plans now, but it should not claim full imputation, phasing, liftover, or cross-build harmonization execution until those wrappers, tests, and reports exist.
