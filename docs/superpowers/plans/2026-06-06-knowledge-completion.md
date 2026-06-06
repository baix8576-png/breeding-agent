# GeneAgent Knowledge Completion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the GeneAgent knowledge base by small reviewable modules, with a safe local batch source-fetch tool for open/public documents.

**Architecture:** Static, copyright-safe knowledge assets live in `references/*` and are indexed by `ReferenceKnowledgeIndexer`; local raw sources live only in `.geneagent/knowledge/*`. Scientific organization is driven by `domain_scope` and `references/analysis_domains/*`, while `blueprint_scope` stores the current knowledge/execution module scope (`knowledge_governance`, `genotype_processing`, `population_genetics`, `quantitative_genetics`, `association_mapping`, or `reporting_audit`).

**Tech Stack:** Markdown `knowledge_item.v2` assets, Python standard-library JSON/urllib/hashlib, Pydantic contracts already present in `src/contracts/knowledge.py`, pytest unit tests.

---

## File Structure

- `references/ontology/knowledge_completion_modules.md`: canonical module map, literature batch plan, ingestion boundaries, and acceptance gates.
- `references/INDEX.md`: top-level pointer to the module map and source-fetch policy.
- `references/ontology/README.md`: ontology directory pointer to the module map.
- `src/knowledge/source_fetcher.py`: safe manifest-driven downloader for open/public source files into the ignored local runtime layer.
- `src/knowledge/__init__.py`: public export for fetcher classes.
- `tests/unit/knowledge/test_references_coverage.py`: regression checks that module-map chunks enter the reference index and retrieval.
- `tests/unit/knowledge/test_source_fetcher.py`: source-fetch safety and behavior tests.
- `docs/HANDOFF.md`: session completion record with checklist blocks and gate evidence.

### Task 1: Lock The Completion Module Map

**Files:**
- Create: `references/ontology/knowledge_completion_modules.md`
- Modify: `references/INDEX.md`
- Modify: `references/ontology/README.md`
- Test: `tests/unit/knowledge/test_references_coverage.py`

- [x] **Step 1: Write the failing index test**

```python
def test_knowledge_completion_module_map_enters_reference_index() -> None:
    result = ReferenceKnowledgeIndexer(Path("references")).build()
    doc_ids = {item.doc_id for item in result.items}
    assert {
        "ontology_knowledge_completion_scope_map",
        "ontology_knowledge_completion_module_order",
        "ontology_knowledge_completion_literature_batches",
        "ontology_knowledge_completion_ingestion_boundary",
        "ontology_knowledge_completion_acceptance_gates",
    } <= doc_ids
```

- [x] **Step 2: Verify the red test**

Run: `.\.venv\Scripts\python.exe -m pytest -q tests\unit\knowledge\test_references_coverage.py::test_knowledge_completion_module_map_enters_reference_index`

Expected before implementation: FAIL because the five `ontology_knowledge_completion_*` doc IDs are absent.

- [x] **Step 3: Add the formal ontology asset**

Create `references/ontology/knowledge_completion_modules.md` with five `##` sections, each containing `knowledge_item.v2` metadata and content for scope map, module order, literature batches, ingestion boundary, and acceptance gates.

- [x] **Step 4: Verify green**

Run: `.\.venv\Scripts\python.exe -m pytest -q tests\unit\knowledge\test_references_coverage.py::test_knowledge_completion_module_map_enters_reference_index tests\unit\knowledge\test_references_coverage.py::test_reference_layer_retrieval_queries_cover_major_topics`

Expected after implementation: PASS.

### Task 2: Add The Safe Batch Source Fetcher

**Files:**
- Create: `src/knowledge/source_fetcher.py`
- Modify: `src/knowledge/__init__.py`
- Test: `tests/unit/knowledge/test_source_fetcher.py`

- [x] **Step 1: Write failing behavior tests**

```python
def test_fetch_manifest_downloads_only_open_sources_to_local_knowledge_root(tmp_path: Path) -> None:
    fetcher = KnowledgeSourceFetcher(tmp_path / ".geneagent" / "knowledge", downloader=lambda _url: b"open")
    report = fetcher.fetch_manifest(tmp_path / "sources.json")
    assert [entry.status for entry in report.entries] == ["downloaded", "skipped"]
```

Add separate tests for unsafe output names, checksum mismatch, and `references` root rejection.

- [x] **Step 2: Verify red**

Run: `.\.venv\Scripts\python.exe -m pytest -q tests\unit\knowledge\test_source_fetcher.py`

Expected before implementation: ERROR with `ModuleNotFoundError: No module named 'knowledge.source_fetcher'`.

- [x] **Step 3: Implement minimal fetcher**

Implement `KnowledgeSourceFetcher.fetch_manifest()` using JSON manifests, an injectable downloader, SHA256 checks, and safe destination resolution under `.geneagent/knowledge/raw_pdfs`, `.geneagent/knowledge/source_docs`, and `.geneagent/knowledge/fetch_reports`.

- [x] **Step 4: Verify green**

Run: `.\.venv\Scripts\python.exe -m pytest -q tests\unit\knowledge\test_source_fetcher.py`

Expected after implementation: PASS.

### Task 3: Complete M02 Input Bundle Knowledge

**Files:**
- Modify: `references/input_specs/input_bundle_contract.md`
- Modify: `references/input_specs/dataset-bundle-template.md`
- Test: `tests/unit/knowledge/test_references_coverage.py`

- [ ] **Step 1: Add regression query**

Add a query expectation for `sample manifest phenotype covariate pedigree sex batch family id sidecar checksum`.

- [ ] **Step 2: Expand knowledge assets**

Add `##` sections for phenotype dictionaries, covariate typing, pedigree consistency, sidecar checksums, and missing-file diagnostics.

- [ ] **Step 3: Verify**

Run: `.\.venv\Scripts\python.exe -m pytest -q tests\unit\knowledge\test_references_coverage.py`.

Expected: PASS with no metadata errors.

### Task 4: Complete M03-M04 Genotype QC And Processing

**Files:**
- Modify: `references/qc_rules/default_qc_threshold_profile.md`
- Modify: `references/analysis_domains/genotype_processing.md`
- Modify: `references/parameter_playbooks/qc_defaults.md`
- Test: `tests/unit/knowledge/test_references_coverage.py`

- [ ] **Step 1: Add regression queries**

Add queries for `variant missingness sample missingness MAF HWE heterozygosity sex check duplicate samples` and `bcftools norm plink make-bed allele flip liftover imputation reference panel`.

- [ ] **Step 2: Expand knowledge assets**

Add focused sections for each QC decision point and state operator-review thresholds for high missingness, relatedness surprises, and allele-strand ambiguity.

- [ ] **Step 3: Verify**

Run: `.\.venv\Scripts\python.exe -m pytest -q tests\unit\knowledge\test_references_coverage.py`.

Expected: PASS with query hits from QC and genotype-processing assets.

### Task 5: Complete M05-M08 Population Genetics And Association Mapping

**Files:**
- Modify: `references/analysis_domains/population_structure.md`
- Modify: `references/analysis_domains/genetic_diversity_inbreeding.md`
- Modify: `references/analysis_domains/selection_signatures.md`
- Modify: `references/analysis_domains/association_mapping_gwas_qtl.md`
- Test: `tests/unit/knowledge/test_references_coverage.py`

- [ ] **Step 1: Add regression queries**

Add queries for PCA/admixture, ROH/LD/diversity, Fst/iHS/XP-EHH/XP-CLR, and GWAS/QTL mixed-model correction.

- [ ] **Step 2: Expand knowledge assets**

Add sections for method family selection, population definition, candidate interval reporting, covariate correction, and false-positive risk.

- [ ] **Step 3: Verify**

Run: `.\.venv\Scripts\python.exe -m pytest -q tests\unit\knowledge\test_references_coverage.py`.

Expected: PASS and at least one hit per population/association module query.

### Task 6: Complete M09-M13 Functional, Quantitative, Species, And Literature Layers

**Files:**
- Modify: `references/analysis_domains/functional_genomics_annotation.md`
- Modify: `references/analysis_domains/relationship_matrix_variance_components.md`
- Modify: `references/analysis_domains/genomic_prediction_breeding_value.md`
- Modify: `references/papers/species_literature_index.md`
- Modify: `references/papers/animal_genomics_classic_landmarks.md`
- Modify: `references/papers/animal_genomics_recent_high_impact_2022_2026.md`
- Test: `tests/unit/knowledge/test_literature_knowledge_pack.py`
- Test: `tests/unit/knowledge/test_references_coverage.py`

- [ ] **Step 1: Add regression queries**

Add queries for `FarmGTEx eQTL single-cell regulatory atlas pangenome SV CNV candidate gene`, `GRM REML heritability variance components`, and `GEBV genomic prediction bias calibration validation`.

- [ ] **Step 2: Expand knowledge assets**

Add cards and domain sections only after DOI/PMID/publisher metadata is checked; store raw PDFs only in `.geneagent/knowledge/raw_pdfs` when license permits.

- [ ] **Step 3: Verify**

Run: `.\.venv\Scripts\python.exe -m pytest -q tests\unit\knowledge\test_literature_knowledge_pack.py tests\unit\knowledge\test_references_coverage.py`.

Expected: PASS with unique doc IDs and recent-literature coverage retained.

### Task 7: Complete M14-M15 Operational And Retrieval QA

**Files:**
- Modify: `references/sop/*`
- Modify: `references/evaluation/*`
- Modify: `references/failure_cases/*`
- Modify: `references/report_templates/*`
- Modify: `tests/unit/knowledge/test_references_coverage.py`

- [ ] **Step 1: Add operational regression queries**

Add queries for `remote execution logs stdout stderr report index audit bundle`, `plink2 bcftools gcta failure recovery`, and `knowledge retrieval trace source path anchor evidence level`.

- [ ] **Step 2: Expand knowledge assets**

Add sections for safe retry, no-overwrite rules, report review, diagnostic escalation, and audit bundle traceability.

- [ ] **Step 3: Verify**

Run: `.\.venv\Scripts\python.exe -m pytest -q tests\unit\knowledge`.

Expected: PASS for all knowledge tests.

### Task 8: Final Gates For Each Batch

**Files:**
- Modify: `docs/HANDOFF.md`

- [ ] **Step 1: Run targeted knowledge gate**

Run: `.\.venv\Scripts\python.exe -m pytest -q tests\unit\knowledge`.

Expected: PASS.

- [ ] **Step 2: Run compile gate**

Run: `$env:PYTHONPYCACHEPREFIX='D:\geneagent\pycache_temp'; .\.venv\Scripts\python.exe -m compileall src tests`.

Expected: PASS.

- [ ] **Step 3: Run full test gate**

Run: `.\.venv\Scripts\python.exe -m pytest -q`.

Expected: PASS before claiming a batch complete.

- [ ] **Step 4: Run diff check**

Run: `git diff --check -- references src tests docs\HANDOFF.md`.

Expected: PASS, with only line-ending warnings allowed.

- [ ] **Step 5: Update HANDOFF**

Append a new session entry to `docs/HANDOFF.md` with `completed_checklist`, `not_yet_done_checklist`, commands, gate result, risks, and next actions.
