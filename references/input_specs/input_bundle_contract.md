# Input Bundle Contract

## Input request envelope

```yaml
knowledge_item.v2:
  doc_id: input_request_envelope
  version: v2
  species: multi_species
  blueprint_scope: genotype_processing
  evidence_level: sop
  source: sop
  updated_at: 2026-05-26T00:00:00Z
  owner: popgen_quantgen
```

Use this entry when converting user requests into a stable `InputBundle`. The request envelope must preserve the original request text, normalized working directory, species or breed statement when available, requested blueprint candidate, and every supplied file path before validation rewrites any path.

Required planning checks:
- Keep path separators normalized to `/` for scheduler-facing scripts.
- Record the user-provided file role instead of inferring role from suffix alone.
- Preserve unresolved or ambiguous inputs as validation warnings; do not silently drop them.
- Mark `cluster_execution_expected=false` until a bioinformatics blueprint and resource gate explicitly allow execution.

This is an SOP-level contract for traceability, not a scientific data-quality claim.

## Input file role matrix

```yaml
knowledge_item.v2:
  doc_id: input_file_role_matrix
  version: v2
  species: multi_species
  blueprint_scope: genotype_processing
  evidence_level: sop
  source: sop
  updated_at: 2026-05-26T00:00:00Z
  owner: popgen_quantgen
```

The file role matrix separates genotype, phenotype, covariate, pedigree, metadata, and reference resources before blueprint selection. A single file may support multiple roles only when the role mapping is explicit and the downstream parser can address the needed columns or sidecars.

Core roles:
- `genotype_vcf`: VCF or BCF plus required index when random access is needed.
- `genotype_plink`: complete `.bed/.bim/.fam` or `.pgen/.pvar/.psam` triplet.
- `phenotype_table`: trait records with sample ID and trait columns.
- `covariate_table`: fixed-effect covariates such as sex, batch, farm, age, or principal components.
- `pedigree_table`: animal ID, sire, dam, and optional family/group columns.
- `reference_panel`: imputation, lift-over, or annotation support; must not be mixed with cohort genotype input.

Risk boundary: do not allow an analysis to proceed because a path exists; it must have a declared role, expected format, and merge key.

## Sample ID policy

```yaml
knowledge_item.v2:
  doc_id: input_sample_id_policy
  version: v2
  species: multi_species
  blueprint_scope: genotype_processing
  evidence_level: sop
  source: sop
  updated_at: 2026-05-26T00:00:00Z
  owner: popgen_quantgen
```

Sample ID normalization is a first-class validation step. Genotype IDs, phenotype IDs, covariate IDs, and pedigree IDs must be compared before QC, PCA, GRM, or genomic prediction scripts are generated.

Minimum checks:
- Report exact counts for genotype-only, phenotype-only, covariate-only, and pedigree-only IDs.
- Do not auto-strip prefixes, suffixes, leading zeros, or breed codes without an explicit mapping table.
- Keep a reversible ID map if harmonization is approved.
- Treat duplicate sample IDs as blocking for model runs and manual-review for exploratory inventory reports.

For mixed-species or cross-breed datasets, sample ID policy must also record the grouping variable used for subgroup validation and stratification checks.

## Path and sidecar policy

```yaml
knowledge_item.v2:
  doc_id: input_path_sidecar_policy
  version: v2
  species: multi_species
  blueprint_scope: genotype_processing
  evidence_level: sop
  source: sop
  updated_at: 2026-05-26T00:00:00Z
  owner: popgen_quantgen
```

Path validation must detect both the primary file and required sidecars. VCF/BCF workflows may need `.tbi` or `.csi`; PLINK workflows need complete binary or pfile triplets; BAM-derived routes must declare that alignment processing is out of scope unless a supported wrapper exists.

Sidecar handling:
- Missing sidecars block submit paths but can still produce diagnostic guidance.
- Relative paths are resolved against `working_directory` and then represented with `/`.
- Scheduler scripts must not embed Windows `\` paths.
- Input files must remain inside the user-approved local or cluster workspace.

This policy protects reproducibility and avoids submitting jobs that fail immediately on missing index or companion files.

## Phenotype dictionary policy

```yaml
knowledge_item.v2:
  doc_id: input_phenotype_dictionary_policy
  version: v2
  species: multi_species
  blueprint_scope: genotype_processing
  evidence_level: sop
  source: sop
  updated_at: 2026-06-06T21:30:00+08:00
  owner: popgen_quantgen
```

Phenotype tables must be accompanied by a phenotype dictionary before they are used for GWAS, variance components, or genomic prediction. The dictionary can be a formal sidecar or a curated section in the run plan, but it must make trait meaning explicit.

Minimum dictionary fields:
- trait column name exactly as it appears in the file
- biological trait name and measurement unit
- trait direction where relevant, such as higher is better or lower is better
- missing-value codes, censoring rules, and impossible-value ranges
- phenotype type: continuous, binary, count, ordinal, repeated record, survival-like, EBV, deregressed proof, or adjusted phenotype
- measurement context such as age, sex, farm, batch, season, tissue, or test environment

Planning rules:
- Do not silently choose the first numeric column as the target trait.
- Do not transform traits without recording the transformation and whether original values remain available.
- Treat repeated records as a modeling-design issue, not a duplicate-row error, when an animal can legitimately have multiple measurements.
- Record whether the phenotype is raw, pre-adjusted, deregressed, or already model-derived.

Submit blockers:
- no trait column is identified
- duplicate trait names map to different columns
- binary traits are encoded ambiguously
- missing-value codes overlap valid biological values
- phenotype IDs cannot be linked to genotype IDs

Risk boundary: phenotype semantics define the analysis. A perfectly valid genotype workflow can produce misleading results if trait units, missingness, repeated records, or adjustment status are unknown.

## Covariate type policy

```yaml
knowledge_item.v2:
  doc_id: input_covariate_type_policy
  version: v2
  species: multi_species
  blueprint_scope: genotype_processing
  evidence_level: sop
  source: sop
  updated_at: 2026-06-06T21:30:00+08:00
  owner: popgen_quantgen
```

Covariates must be typed before a model is planned. Animal breeding datasets often contain sex, farm, batch, line, hatch, parity, age, environmental group, sequencing lane, chip version, and principal components in the same table; they cannot be treated as interchangeable numeric columns.

Covariate typing checklist:
- `categorical_fixed_effect`: sex, farm, line, hatch, batch, chip, lane, management group
- `continuous_fixed_effect`: age, weight, parity number, inbreeding coefficient, dosage summary
- `derived_structure_covariate`: PC scores or ancestry proportions after review
- `blocking_or_split_variable`: family, farm, generation, year, line, or validation group
- `do_not_model_without_review`: variables downstream of the trait, leakage-prone summaries, or post-outcome measurements

Operational rules:
- Keep sample ID, trait, and covariate columns distinct.
- Record the intended model role of every covariate.
- Treat covariates with many missing values as review items before imputation or row removal.
- Do not add PCs, breed labels, or batch variables automatically; propose them with evidence from structure/QC reports.
- Preserve categorical level counts and rare-level warnings.

Risk boundary: covariates can remove confounding or introduce leakage. GeneAgent should expose covariate intent and require review when a variable could encode the outcome or validation split.

## Pedigree consistency policy

```yaml
knowledge_item.v2:
  doc_id: input_pedigree_consistency_policy
  version: v2
  species: multi_species
  blueprint_scope: genotype_processing
  evidence_level: sop
  source: sop
  updated_at: 2026-06-06T21:30:00+08:00
  owner: popgen_quantgen
```

Pedigree inputs are optional for many first-pass workflows, but once supplied they become part of the identity and model contract. Pedigree consistency checks should run before GRM comparison, ssGBLUP planning, family-blocked validation, or relatedness interpretation.

Minimum pedigree columns:
- animal ID
- sire ID
- dam ID
- optional sex, birth year, breed, flock/herd, family, generation, or line

Consistency checks:
- animal IDs must not be duplicated
- sire and dam IDs should not equal the animal ID
- parent IDs should either appear as animals or be marked as founders/missing
- sex-coded parent roles should be plausible when sex metadata exists
- cycles in parentage should block pedigree-based modeling
- genotype IDs should map to pedigree IDs with an explicit genotyped-animal subset

Use in downstream planning:
- compare pedigree relationship and genomic relationship only after ID mapping is verified
- use family or generation labels for validation splits when leakage risk matters
- treat missing parents as ordinary pedigree information, not as file corruption
- keep pedigree-derived exclusions separate from genotype QC exclusions

Risk boundary: pedigree errors can silently distort ssGBLUP, family validation, relatedness interpretation, and inbreeding summaries.

## Sidecar checksum policy

```yaml
knowledge_item.v2:
  doc_id: input_sidecar_checksum_policy
  version: v2
  species: multi_species
  blueprint_scope: genotype_processing
  evidence_level: sop
  source: sop
  updated_at: 2026-06-06T21:30:00+08:00
  owner: popgen_quantgen
```

Input sidecars and checksums protect reproducibility. GeneAgent should identify required companion files and record stable fingerprints for inputs that will be used in remote execution or repeated analysis.

Sidecar examples:
- VCF/BCF: `.tbi` or `.csi` index when random access is required
- PLINK1: `.bed`, `.bim`, `.fam`
- PLINK2: `.pgen`, `.pvar`, `.psam`
- phenotype/covariate/pedigree: dictionary, schema, or column-role sidecar
- annotation and reference resources: version manifest, genome build statement, and optional checksum file

Checksum rules:
- compute or accept SHA256 checksums for small metadata files when practical
- record file size and modification time when hashing large genotype files is deferred
- never modify a source file while calculating sidecars
- store checksum reports in run artifacts, not by overwriting user inputs
- flag checksum drift between dry-run and submit

Submit blockers:
- missing required sidecar for a declared input format
- PLINK triplet prefix mismatch
- VCF index older than the VCF when random access is required
- checksum mismatch for a file with an expected checksum

Risk boundary: sidecar drift is a reproducibility failure. A job that reads a changed VCF, phenotype table, or annotation file is a different analysis.

## Missing file diagnostic policy

```yaml
knowledge_item.v2:
  doc_id: input_missing_file_diagnostic_policy
  version: v2
  species: multi_species
  blueprint_scope: genotype_processing
  evidence_level: sop
  source: sop
  updated_at: 2026-06-06T21:30:00+08:00
  owner: popgen_quantgen
```

Missing-file diagnostics should be helpful without guessing. The validator must explain which role is missing, which downstream stage is blocked, and which file or sidecar would unblock it.

Diagnostic output should include:
- requested role and original user-supplied path
- normalized path with `/` separators
- whether the primary file is missing or a sidecar is missing
- expected suffixes or companion files
- affected modules such as QC, PCA, GRM, GWAS, prediction, or report generation
- whether a diagnostic-only plan can still be produced

Recommended response:
- use `blocked_for_submit` when the missing file prevents execution
- use `warning_for_report` when the file is optional but limits interpretation
- show exact examples of valid alternatives, such as `.bed/.bim/.fam` triplet or bgzip-indexed VCF
- keep missing-file errors out of remote scripts; block before scheduler materialization

Risk boundary: a missing file should never become a remote job failure when it could have been detected locally.
