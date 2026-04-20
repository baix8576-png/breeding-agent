# bio tool error patterns (diagnostics_v1)

## ENTRY: plink2.missing_bfile_triplet

- pattern_id: `plink2.missing_bfile_triplet`
- component: `tools.plink2`
- stage: `input_validation,execution`
- severity: `high`
- trigger_keywords:
  - `--bfile requires .bed + .bim + .fam`
  - `Failed to open`
  - `No such file or directory`
- trigger_regex:
  - `(?i)--bfile requires`
  - `(?i)failed to open .*\\.(bed|bim|fam)`
- likely_root_causes:
  1. Prefix path is wrong or files are not colocated.
  2. One of `.bed/.bim/.fam` is missing or unreadable.
  3. Data source is VCF but pipeline was configured as PLINK prefix.
- executable_fix_steps:
  1. Verify the trio exists and uses the same prefix.
  2. If input is VCF, convert to PLINK first.
  3. Re-run with corrected `--bfile` or `--vcf` path.
- command_examples:
```bash
ls -lh <prefix>.bed <prefix>.bim <prefix>.fam
plink2 --vcf input.vcf.gz --make-bed --out dataset_plink
plink2 --bfile dataset_plink --freq --out dataset_qc_check
```
- risk_notice:
  - Prefix collisions can silently read stale files from previous runs.
  - Conversion from VCF may change sample ordering if not validated.
- verification:
  1. `plink2 --bfile <prefix> --freq` completes without file-open errors.
  2. Output log confirms expected sample and variant counts.

## ENTRY: plink2.no_variants_after_filters

- pattern_id: `plink2.no_variants_after_filters`
- component: `tools.plink2`
- stage: `execution`
- severity: `medium`
- trigger_keywords:
  - `No variants remaining after main filters`
  - `0 variants remaining`
  - `Skipping --make-bed since no variants remain`
- trigger_regex:
  - `(?i)no variants remaining`
  - `(?i)0 variants remaining`
- likely_root_causes:
  1. Combined filters (`--geno/--maf/--hwe`) are too strict for cohort size.
  2. Input already heavily pre-filtered; additional filter stack removes all sites.
  3. Chromosome or sample subset selection is empty.
- executable_fix_steps:
  1. Run baseline stats without strict filters.
  2. Re-apply filters one-by-one to locate the destructive threshold.
  3. Tune thresholds by cohort size and objective.
- command_examples:
```bash
plink2 --bfile <prefix> --missing --freq --hardy --out qc_baseline
plink2 --bfile <prefix> --geno 0.1 --maf 0.005 --hwe 1e-6 midp --make-bed --out qc_relaxed
plink2 --bfile <prefix> --extract qc_relaxed.prune.in --make-bed --out qc_final
```
- risk_notice:
  - Over-relaxing thresholds increases false-positive and batch-effect risk.
  - Thresholds should align with project SOP, not only "make job pass".
- verification:
  1. Filtered dataset retains non-zero variants.
  2. QC summary metrics remain within project acceptance ranges.

## ENTRY: plink2.duplicate_variant_ids

- pattern_id: `plink2.duplicate_variant_ids`
- component: `tools.plink2`
- stage: `input_validation,execution`
- severity: `medium`
- trigger_keywords:
  - `Duplicate ID`
  - `duplicate variant ID`
  - `variants with duplicate IDs`
- trigger_regex:
  - `(?i)duplicate.*variant.*id`
  - `(?i)duplicate id`
- likely_root_causes:
  1. Multi-allelic records or merged cohorts produced repeated IDs.
  2. Missing IDs represented as `.` causing collisions after transformation.
  3. Liftover/merge operation retained non-unique rsID mappings.
- executable_fix_steps:
  1. Generate deterministic IDs from CHR:POS:REF:ALT.
  2. Rebuild binary files with normalized IDs.
  3. Keep an ID mapping table for downstream traceability.
- command_examples:
```bash
plink2 --bfile <prefix> --set-all-var-ids @:#:$r:$a --new-id-max-allele-len 80 missing --make-bed --out <prefix>.renamed
plink2 --bfile <prefix>.renamed --list-duplicate-vars ids-only suppress-first --out dup_check
```
- risk_notice:
  - Renaming IDs can break downstream annotation joins unless mapping is preserved.
  - Keep original variant IDs in audit artifacts when available.
- verification:
  1. Duplicate-ID report is empty or within expected threshold.
  2. Downstream tools consume normalized IDs without collision errors.

## ENTRY: bcftools.not_bgzip_or_missing_index

- pattern_id: `bcftools.not_bgzip_or_missing_index`
- component: `tools.bcftools`
- stage: `input_validation,execution`
- severity: `high`
- trigger_keywords:
  - `not compressed with bgzip`
  - `could not load index`
  - `failed to open index`
- trigger_regex:
  - `(?i)not compressed with bgzip`
  - `(?i)could not load index`
  - `(?i)failed to open.*\\.tbi|\\.csi`
- likely_root_causes:
  1. File compressed with `gzip` instead of `bgzip`.
  2. `.tbi/.csi` index missing or stale.
  3. VCF replaced but old index retained.
- executable_fix_steps:
  1. Recompress VCF with `bgzip`.
  2. Rebuild index with force overwrite.
  3. Retry command on refreshed pair.
- command_examples:
```bash
bgzip -c input.vcf > input.vcf.gz
bcftools index -f input.vcf.gz
bcftools view -h input.vcf.gz | head
```
- risk_notice:
  - Using wrong compression type can fail random-access operations deep in pipeline.
  - Regenerating index on wrong file version leads to silent mismatches.
- verification:
  1. `bcftools index -n input.vcf.gz` returns valid contig index summary.
  2. Downstream region queries (`-r chr:start-end`) run successfully.

## ENTRY: bcftools.malformed_header_or_fields

- pattern_id: `bcftools.malformed_header_or_fields`
- component: `tools.bcftools`
- stage: `input_validation`
- severity: `high`
- trigger_keywords:
  - `Could not parse the header`
  - `Wrong number of fields`
  - `Broken VCF record`
- trigger_regex:
  - `(?i)could not parse the header`
  - `(?i)wrong number of fields`
  - `(?i)broken vcf`
- likely_root_causes:
  1. Header metadata and body columns are inconsistent.
  2. File contains CRLF or non-tab delimiters after cross-platform edits.
  3. Upstream export produced invalid INFO/FORMAT declarations.
- executable_fix_steps:
  1. Inspect header and first broken lines.
  2. Normalize line endings and delimiters.
  3. Re-export or validate with upstream caller if structural defects persist.
- command_examples:
```bash
bcftools view -h input.vcf.gz | sed -n '1,80p'
zcat input.vcf.gz | sed -n '1,120p' | cat -vet
zcat input.vcf.gz | sed 's/\r$//' | bgzip -c > input.norm.vcf.gz
bcftools index -f input.norm.vcf.gz
```
- risk_notice:
  - Manual text edits on large VCFs can corrupt coordinates or genotypes.
  - Structural header fixes must stay consistent with body semantics.
- verification:
  1. `bcftools view input.norm.vcf.gz -Ou | head` runs without parse errors.
  2. Validation command no longer reports malformed records.

## ENTRY: bcftools.index_older_than_data

- pattern_id: `bcftools.index_older_than_data`
- component: `tools.bcftools`
- stage: `execution`
- severity: `medium`
- trigger_keywords:
  - `index file is older than the data file`
  - `stale index`
  - `index may be out of date`
- trigger_regex:
  - `(?i)index file is older than the data file`
  - `(?i)stale index`
- likely_root_causes:
  1. VCF replaced or edited after index generation.
  2. File copied without matching index timestamp/version.
  3. Incremental pipeline step mutated file in place.
- executable_fix_steps:
  1. Remove stale index artifacts.
  2. Rebuild index against the current data file.
  3. Enforce immutable output naming to avoid in-place mutation.
- command_examples:
```bash
rm -f input.vcf.gz.tbi input.vcf.gz.csi
bcftools index -f input.vcf.gz
bcftools view -r <chr>:<start>-<end> input.vcf.gz | head
```
- risk_notice:
  - In-place mutation breaks reproducibility and increases stale-index recurrence.
  - Region-based results may be incomplete if stale index is accidentally reused.
- verification:
  1. Fresh index timestamp is newer than data file timestamp.
  2. Region queries produce stable and complete records.

## ENTRY: vcftools.genotype_field_missing

- pattern_id: `vcftools.genotype_field_missing`
- component: `tools.vcftools`
- stage: `input_validation,execution`
- severity: `high`
- trigger_keywords:
  - `Require Genotypes in VCF file`
  - `No FORMAT field`
  - `No GT field`
- trigger_regex:
  - `(?i)require genotypes in vcf file`
  - `(?i)no .*gt`
- likely_root_causes:
  1. Input is site-only VCF with no per-sample genotype columns.
  2. FORMAT/GT tags removed during preprocessing.
  3. Wrong file type routed into genotype-dependent command path.
- executable_fix_steps:
  1. Confirm genotype columns and GT format tag.
  2. Route site-only VCF to site-stat tools instead of genotype-stat path.
  3. Re-export full genotype VCF if downstream step requires sample genotypes.
- command_examples:
```bash
bcftools view -h input.vcf.gz | grep -E '^##FORMAT=<ID=GT'
bcftools query -l input.vcf.gz | head
vcftools --gzvcf input.vcf.gz --freq --out vcftools_freq_check
```
- risk_notice:
  - Forcing genotype workflows on site-only files gives invalid biological conclusions.
  - Reconstructed genotype fields from incomplete data are not trustworthy.
- verification:
  1. GT tag exists in header and sample list is non-empty.
  2. Genotype-based vcftools command completes successfully.

## ENTRY: vcftools.input_open_failed

- pattern_id: `vcftools.input_open_failed`
- component: `tools.vcftools`
- stage: `input_validation,execution`
- severity: `medium`
- trigger_keywords:
  - `Could not open file`
  - `Error: cannot open VCF`
  - `Failed to open input`
- trigger_regex:
  - `(?i)could not open file`
  - `(?i)cannot open vcf`
- likely_root_causes:
  1. Relative path resolved from wrong working directory.
  2. Input file permissions or mount path inaccessible on compute node.
  3. Filename mismatch between wrapper output and scheduler script input.
- executable_fix_steps:
  1. Resolve absolute path before submit.
  2. Check read permission from the execution user.
  3. Re-run using canonicalized path in job script.
- command_examples:
```bash
readlink -f input.vcf.gz
ls -lh input.vcf.gz
test -r input.vcf.gz && echo "readable"
vcftools --gzvcf /abs/path/input.vcf.gz --freq --out freq_check
```
- risk_notice:
  - Path mismatch across login and compute nodes is common in mixed storage setups.
  - Hidden permission issues can appear only after scheduler dispatch.
- verification:
  1. Input path is absolute and readable from target runtime context.
  2. vcftools command runs and generates output files.

## ENTRY: vcftools.empty_output_after_filtering

- pattern_id: `vcftools.empty_output_after_filtering`
- component: `tools.vcftools`
- stage: `execution`
- severity: `medium`
- trigger_keywords:
  - `After filtering, kept 0 out of`
  - `No sites left`
  - `No individuals left`
- trigger_regex:
  - `(?i)kept 0 out of`
  - `(?i)no sites left`
  - `(?i)no individuals left`
- likely_root_causes:
  1. Combined site/sample filters are too strict.
  2. Region or sample include list does not overlap input data.
  3. Upstream prefilters already removed most records.
- executable_fix_steps:
  1. Profile baseline counts with no strict filters.
  2. Apply filters incrementally to isolate the destructive clause.
  3. Adjust thresholds or include list to preserve minimum analyzable set.
- command_examples:
```bash
vcftools --gzvcf input.vcf.gz --freq --out baseline_freq
vcftools --gzvcf input.vcf.gz --missing-indv --out baseline_indv
vcftools --gzvcf input.vcf.gz --maf 0.005 --max-missing 0.9 --recode --stdout | head
```
- risk_notice:
  - Relaxing filters too much can degrade downstream model quality.
  - Keep threshold changes auditable for reproducibility.
- verification:
  1. Filtered output keeps non-zero variants and samples.
  2. QC summaries remain consistent with project acceptance criteria.

## ENTRY: gcta.input_file_open_failed

- pattern_id: `gcta.input_file_open_failed`
- component: `tools.gcta64`
- stage: `input_validation,execution`
- severity: `high`
- trigger_keywords:
  - `Error: can't open the file`
  - `cannot open`
  - `No such file or directory`
- trigger_regex:
  - `(?i)gcta.*can't open the file`
  - `(?i)cannot open`
- likely_root_causes:
  1. GRM/PLINK prefix is wrong or incomplete.
  2. Required companion files are missing (`.grm.bin/.grm.N.bin/.grm.id`).
  3. Scheduler runtime path differs from local preview path.
- executable_fix_steps:
  1. Verify required files for selected GCTA mode.
  2. Convert or rebuild missing inputs.
  3. Use absolute prefixes in wrapper and scheduler script.
- command_examples:
```bash
ls -lh <grm_prefix>.grm.bin <grm_prefix>.grm.N.bin <grm_prefix>.grm.id
ls -lh <plink_prefix>.bed <plink_prefix>.bim <plink_prefix>.fam
gcta64 --grm <grm_prefix> --reml --pheno <pheno_file> --out reml_test
```
- risk_notice:
  - Prefix confusion is frequent when multiple cohorts share similar names.
  - Missing companion file can fail late in runtime and waste queue quota.
- verification:
  1. All required files exist with non-zero size.
  2. GCTA command starts and writes expected log header.

## ENTRY: gcta.no_valid_phenotype

- pattern_id: `gcta.no_valid_phenotype`
- component: `tools.gcta64`
- stage: `execution`
- severity: `high`
- trigger_keywords:
  - `no valid phenotype`
  - `Error: no phenotypes are available`
  - `all phenotype values are missing`
- trigger_regex:
  - `(?i)no valid phenotype`
  - `(?i)no phenotypes are available`
- likely_root_causes:
  1. Phenotype file format is invalid (missing FID/IID/trait columns).
  2. Missing values encoded unexpectedly and removed all records.
  3. IDs in phenotype file do not overlap GRM/sample IDs.
- executable_fix_steps:
  1. Validate phenotype file schema and delimiter consistency.
  2. Standardize missing value coding and trait column selection.
  3. Intersect phenotype IDs with analysis cohort IDs before run.
- command_examples:
```bash
head -n 5 pheno.txt
awk 'NF<3{print NR,$0}' pheno.txt | head
awk '{print $1,$2}' pheno.txt | sort -u > pheno.ids
awk '{print $1,$2}' <grm_prefix>.grm.id | sort -u > grm.ids
comm -12 pheno.ids grm.ids | wc -l
```
- risk_notice:
  - Silent delimiter problems (tab vs space) can invalidate all phenotypes.
  - Imputing phenotype blindly to bypass error is scientifically unsafe.
- verification:
  1. Trait column has valid non-missing values after filtering.
  2. Intersected IDs are non-zero and match expected cohort size.

## ENTRY: gcta.id_mismatch_between_inputs

- pattern_id: `gcta.id_mismatch_between_inputs`
- component: `tools.gcta64`
- stage: `execution`
- severity: `high`
- trigger_keywords:
  - `ID not found`
  - `sample size does not match`
  - `inconsistent IDs`
- trigger_regex:
  - `(?i)id not found`
  - `(?i)sample size.*does not match`
  - `(?i)inconsistent ids`
- likely_root_causes:
  1. GRM, phenotype, and covariate files use different sample subsets.
  2. ID formatting differs (trimmed strings, case, delimiter drift).
  3. Keep/remove filters applied inconsistently across preprocessing steps.
- executable_fix_steps:
  1. Compute exact ID intersection across all required inputs.
  2. Generate a unified keep list.
  3. Re-run GRM/model command with the keep list applied consistently.
- command_examples:
```bash
awk '{print $1,$2}' <grm_prefix>.grm.id | sort -u > grm.ids
awk '{print $1,$2}' pheno.txt | sort -u > pheno.ids
awk '{print $1,$2}' covar.txt | sort -u > covar.ids
comm -12 grm.ids pheno.ids | comm -12 - covar.ids > keep.ids
gcta64 --grm <grm_prefix> --keep keep.ids --pheno pheno.txt --qcovar covar.txt --reml --out reml_fixed
```
- risk_notice:
  - ID normalization can drop legitimate samples if formatting rules are wrong.
  - Always archive the generated keep list for audit traceability.
- verification:
  1. GCTA log no longer reports ID mismatch or size inconsistency.
  2. Effective sample size is recorded and consistent with keep list count.
