# Input Bundle Contract

## Input request envelope

```yaml
knowledge_item.v2:
  doc_id: input_request_envelope
  version: v2
  species: multi_species
  blueprint_scope: shared
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
  blueprint_scope: shared
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
  blueprint_scope: shared
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
  blueprint_scope: shared
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
