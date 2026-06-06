# Data Preparation And QC Domain

This file defines the first detailed analysis-domain playbook after the scientific script-directory restructure. It covers the professional boundary behind `scripts/genotype_processing/` and the compatibility `qc_pipeline` execution bridge.

## Domain scope and scientific intent

```yaml
knowledge_item.v2:
  doc_id: domain_data_preparation_qc_scope
  version: v2
  species: multi_species
  blueprint_scope: genotype_processing
  evidence_level: sop
  source: sop
  updated_at: 2026-06-06T00:00:00+08:00
  owner: popgen_quantgen
```

Primary `domain_scope`: `data_preparation_qc`.

Data preparation and QC is the entry domain for animal genetics and breeding bioinformatics. Its job is to decide whether genotype-bearing inputs, sample metadata, phenotype records, covariates, and pedigree sidecars are ready for downstream population genetics, quantitative genetics, association mapping, and reporting workflows.

Scientific intent:
- Separate input readiness from biological inference.
- Produce reversible sample and variant diagnostics before filtering decisions.
- Preserve enough context for later PCA, GRM, GWAS, and genomic prediction reports to explain where each retained dataset came from.
- Identify submit blockers before a remote server or scheduler job is materialized.

Current execution bridge:
- `qc_pipeline` compatibility key.
- `scripts/genotype_processing/run_genotype_qc.sh` scientific-domain script path.
- `blueprint_scope=qc` for current `knowledge_item.v2` compatibility.

Not in scope:
- full phasing or imputation
- BAM alignment QC
- GWAS, QTL, fine mapping, or causal interpretation
- automatic biological sample removal without an explicit reviewed rule

Related assets:
- `references/input_specs/input_bundle_contract.md`
- `references/qc_rules/default_qc_threshold_profile.md`
- `references/parameter_playbooks/qc_defaults.md`
- `scripts/genotype_processing/operation_guide.md`

Risk boundary: passing QC readiness only means the dataset is suitable for the next planned stage under the declared assumptions. It does not certify that samples or variants are biologically correct.

## Input roles and sidecars

```yaml
knowledge_item.v2:
  doc_id: domain_data_preparation_qc_input_roles
  version: v2
  species: multi_species
  blueprint_scope: genotype_processing
  evidence_level: sop
  source: sop
  updated_at: 2026-06-06T00:00:00+08:00
  owner: popgen_quantgen
```

The first domain decision is not which tool to run, but which file role each path plays. The same suffix can be misleading: a table may be phenotype, covariate, batch metadata, pedigree support, or a sample inclusion list. GeneAgent should keep these roles explicit in the plan and report.

Core input roles:

| Role | Expected examples | Required before submit | Notes |
|---|---|---|---|
| `genotype_vcf` | `.vcf`, `.vcf.gz`, `.bcf` | VCF/BCF path plus index if random access is needed | Validate headers and genotype fields before conversion. |
| `genotype_plink` | `.bed/.bim/.fam`, `.pgen/.pvar/.psam` | complete triplet with matching prefix | Prefer complete PLINK inputs for fast QC and relatedness prep. |
| `phenotype_table` | TSV/CSV trait table | sample ID column plus trait columns when downstream modeling is requested | QC-only inventory may proceed without traits. |
| `covariate_table` | sex, batch, farm, chip, age, PC covariates | merge key and column definitions | Do not silently turn PCA results into covariates. |
| `pedigree_table` | animal, sire, dam, family/group columns | ID consistency when pedigree checks or ssGBLUP are requested | Unknown parents must have a declared missing-value convention. |
| `metadata_table` | breed, population, farm, sequencing lane, chip | optional for QC-only; required for subgroup-aware review | Provides context for stratified missingness and HWE interpretation. |

Submission blockers:
- missing genotype-bearing input
- incomplete PLINK triplet
- VCF/BCF sidecar required by the selected command but missing
- duplicate primary sample IDs in genotype or phenotype sidecars
- Windows `\` paths in scheduler-facing or remote script arguments
- input path outside the approved working root or remote allowlist

Report obligations:
- list every supplied path and assigned role
- record unresolved or ambiguous roles as warnings
- preserve exact pre-normalization user paths in audit summaries when safe
- never drop an unrecognized sidecar silently

Risk boundary: a path that exists is not automatically a valid biological input. It must have a role, a merge key when needed, and an explicit downstream purpose.

## Sample ID and merge policy

```yaml
knowledge_item.v2:
  doc_id: domain_data_preparation_qc_sample_id_policy
  version: v2
  species: multi_species
  blueprint_scope: genotype_processing
  evidence_level: sop
  source: sop
  updated_at: 2026-06-06T00:00:00+08:00
  owner: popgen_quantgen
```

Sample ID handling is the highest-risk part of early analysis because silent mismatches propagate into PCA clusters, GRM rows, GWAS phenotype joins, and genomic prediction labels. GeneAgent should treat sample ID harmonization as a reviewed transformation, not a convenience cleanup.

Minimum checks:
- Count genotype-only, phenotype-only, covariate-only, pedigree-only, and shared IDs.
- Check duplicate IDs within every role before cross-role merging.
- Preserve family/sample two-column IDs from PLINK when present.
- Do not strip prefixes, breed codes, leading zeros, or suffixes without a user-supplied mapping table.
- If a mapping table is approved, keep both original and normalized IDs in a reversible artifact.
- For mixed-breed or multi-population work, keep the grouping variable visible for subgroup QC and later validation.

Blocking conditions:
- duplicate genotype sample IDs
- duplicate phenotype IDs for the same trait without an aggregation policy
- incompatible ID conventions where no mapping table is supplied
- pedigree animal IDs that cannot be reconciled with phenotype or genotype rows for requested relationship or prediction stages

Manual-review conditions:
- large phenotype-only or genotype-only sets
- ID differences explained by cohort subset design
- remapped IDs generated from user-provided key files
- breed-specific ID prefixes that may encode real population labels

Output requirements:
- `sample_id_reconciliation.tsv` or an equivalent report section for non-executed planning
- count table by role and overlap
- warnings that identify whether a mismatch blocks submit or only limits downstream interpretation

Risk boundary: automatic ID repair can create a scientifically wrong dataset even when all tools run successfully. GeneAgent should prefer a blocking diagnostic over a guessed merge.

## QC decision boundary

```yaml
knowledge_item.v2:
  doc_id: domain_data_preparation_qc_qc_boundary
  version: v2
  species: multi_species
  blueprint_scope: genotype_processing
  evidence_level: expert_opinion
  source: sop
  updated_at: 2026-06-06T00:00:00+08:00
  owner: popgen_quantgen
```

QC outputs are diagnostic evidence. They become filtering decisions only after the threshold, population context, and downstream purpose are explicit. This distinction matters in animal breeding because selected, structured, crossbred, or family-based populations often violate assumptions that are common in simple human-cohort QC examples.

Recommended first-pass diagnostics:
- sample missingness and variant missingness
- allele frequency and minor allele count summaries
- HWE review only when population assumptions are defensible
- heterozygosity or inbreeding outliers with breed/group context
- duplicate marker IDs and duplicated genomic positions
- chromosome, position, allele-coding, and non-autosomal marker summaries
- batch, farm, chip, sequencing lane, or family concentration of QC failures when metadata exists

Do not automate as irreversible decisions:
- removing all HWE outliers in structured or selected populations
- dropping rare variants before confirming the downstream method
- removing samples solely because they are heterozygosity outliers
- applying a single missingness threshold across species, genotyping platforms, or sequencing depths without rationale

Report language should separate:
- `diagnostic`: metric observed
- `candidate_filter`: rule proposed for review
- `applied_filter`: rule actually used by an execution wrapper
- `blocked`: failure that prevents safe submit

Risk boundary: QC thresholds are not universal defaults. They are project-specific parameters that must remain visible in `run_manifest.json`, reports, and audit bundles.

## Execution bridge and artifacts

```yaml
knowledge_item.v2:
  doc_id: domain_data_preparation_qc_execution_bridge
  version: v2
  species: multi_species
  blueprint_scope: genotype_processing
  evidence_level: sop
  source: sop
  updated_at: 2026-06-06T00:00:00+08:00
  owner: popgen_quantgen
```

The current automated bridge for this domain is the genotype QC wrapper under `scripts/genotype_processing/`. It should be treated as a thin execution entrypoint. Planning, resource gates, remote submission, polling, recovery, and report packaging remain in `src/pipeline/`, `src/scheduler/`, `src/runtime/`, and `src/audit/`.

Execution mapping:

| Domain concern | Current bridge | Expected artifact |
|---|---|---|
| input role inventory | `qc_pipeline` plan and QC wrapper manifest | `results/qc/input_manifest.json` |
| sample/variant QC metrics | `scripts/genotype_processing/run_genotype_qc.sh` | `results/qc/sample_qc.tsv`, `results/qc/variant_qc.tsv` |
| VCF-level stats | `bcftools stats` when VCF input is present | `results/qc/bcftools.stats.txt` |
| retained dataset index | wrapper output summary | `results/qc/retained_dataset/README.md` |
| report summary | reporting stage or wrapper summary | `reports/qc_summary.md` |
| traceability | script audit sidecar plus runtime audit | `results/qc/audit_sidecar.json`, report index, audit bundle |

Remote execution expectations:
- PC Agent -> trusted SSH shell or scheduler backend handles submission.
- The script receives bounded `--threads`, `--memory-mb`, `--tmp-dir`, and POSIX paths.
- Raw genotype, phenotype, covariate, and pedigree inputs are read-only.
- Existing outputs require `--force` or a higher-level reviewed overwrite decision.

Failure routing:
- missing tool path -> diagnostic and no blind retry
- missing sidecar -> input validation failure
- duplicate IDs -> blocking report
- non-POSIX paths -> pre-submit failure
- resource request above cap -> safety gate breaker before remote execution

Risk boundary: this bridge can produce first-pass QC artifacts, but it must not claim to have completed phasing, imputation, population structure, selection scans, association mapping, or genomic prediction.
