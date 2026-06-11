# GeneAgent Knowledge Content Fill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fill the GeneAgent knowledge base to content-complete delivery quality across literature, SOPs, parameters, diagnostics, report templates, and executable script knowledge.

**Architecture:** Git-versioned, copyright-safe knowledge assets remain under `references/*`; local raw PDFs, extracted text, TEI, chunks, and indexes remain under `.geneagent/knowledge/*`. The content model is organized by animal genetics domain and execution workflow, with `knowledge_item.v2` metadata, `domain_scope` body text, retrieval regression tests, and script/template alignment gates proving each batch.

**Tech Stack:** Markdown knowledge cards, `knowledge_item.v2`, `ReferenceKnowledgeIndexer`, Python pytest, CrossRef/PubMed/Semantic Scholar metadata checks, local-only `.geneagent/knowledge/*` source cache, Bash workflow templates in `scripts/*`.

---

## Current Baseline

Current repository state after the 2026-06-06 cleanup:

- `references/*` has structure and first-pass M02-M15 coverage.
- `ReferenceKnowledgeIndexer` already validates metadata, chunk anchors, uniqueness, and retrieval queries.
- `tests/unit/knowledge/test_literature_knowledge_pack.py` distinguishes verified literature cards from internal candidate cards.
- `references/papers/animal_genomics_recent_high_impact_2022_2026.md` still has many cards marked `verify before citation export`; these are valid internal retrieval candidates but not final manuscript-grade citations.
- `scripts/*` has workflow-oriented folders, but the knowledge base still needs stronger bidirectional links between each script, SOP, parameter playbook, failure pattern, and report output.
- `AGENTS.md` requires no raw entity data, PDFs, TEI/XML, extracted full text, chunks, indexes, private IPs, credentials, or server paths in Git.

This plan does not redefine "complete" as structure-only. A batch is complete only when the knowledge content is specific enough to guide real animal genetics bioinformatics work, is traceable to a source or expert SOP boundary, and is covered by tests.

## 中文执行摘要

本计划把“知识库补充完整”拆成 9 个可验收批次，而不是一次性堆内容：

- B00 先补内容完整性测试，让当前缺口显性失败。
- B01-B02 补文献层：近期高水平文献做 DOI/PMID/出版社链接刷新，经典方法文献补齐方法族覆盖。
- B03-B05 补工作流层：五个脚本目录分别绑定 SOP、参数手册、失败诊断、输出契约和报告交接。
- B06-B07 补专业解释层：补物种覆盖、检索追溯、本地 source-fetch 边界和索引健康检查。
- B08 做最终验收：知识索引无错误、检索回归覆盖全域、脚本有资源限制、Git diff 无原始数据/凭据/PDF/TEI/索引。

完成标准不是“文件存在”，而是每个知识块能回答实际工作问题：输入怎么验、工具怎么跑、参数怎么选、结果怎么解释、失败怎么修、什么时候必须熔断、报告如何追溯。当前下一步从 B00 开始，先建立失败测试，再按批填内容。

## File Structure

- Create: `references/papers/literature_refresh_log_2026.md`
  Records DOI/PMID/publisher refresh batches, rejected duplicate candidates, and citation-export readiness.
- Modify: `references/papers/animal_genomics_recent_high_impact_2022_2026.md`
  Replaces candidate recent-literature cards with verified cards, official publisher/DOI/PubMed links, and GeneAgent-specific use/boundary notes.
- Modify: `references/papers/animal_genomics_classic_landmarks.md`
  Adds missing classic method cards and method-family crosswalks where the current evidence base is thin.
- Modify: `references/papers/species_literature_index.md`
  Adds species-specific evidence overlays and default cautions for cattle, pig, poultry, sheep/goat, and aquaculture.
- Create: `references/sop/genotype_processing_execution_sop.md`
- Create: `references/sop/population_genetics_execution_sop.md`
- Create: `references/sop/quantitative_genetics_execution_sop.md`
- Create: `references/sop/association_mapping_execution_sop.md`
- Create: `references/sop/reporting_audit_execution_sop.md`
  Domain-facing SOPs that supersede old blueprint-name SOPs while leaving old files as compatibility references.
- Modify: `references/parameter_playbooks/core_parameter_playbooks.md`
- Modify: `references/parameter_playbooks/qc_defaults.md`
- Modify: `references/parameter_playbooks/pca_component_policy.md`
- Modify: `references/parameter_playbooks/grm_resource_baseline.md`
- Modify: `references/parameter_playbooks/genomic_prediction_cv_policy.md`
- Modify: `references/parameter_playbooks/scheduler_resource_presets.md`
  Adds concrete command-level resource and parameter guidance for PLINK/PLINK2, bcftools, GCTA, GEMMA/EMMAX-compatible GWAS, Rscript helpers, and report scripts.
- Modify: `references/failure_cases/operational_failure_cases.md`
- Modify: `references/evaluation/diagnostics/bio_tool_error_patterns.md`
- Modify: `references/evaluation/diagnostics/scheduler_error_patterns.md`
  Adds tool-specific error signatures, safe automatic repairs, and breaker conditions.
- Modify: `references/report_templates/*.md`
  Ensures each report template has required sections, evidence-trace fields, and method caveat blocks.
- Modify: `scripts/*/operation_guide.md`
- Modify: `scripts/*/*.sh`
  Adds explicit knowledge links, thread/resource parameters, output contracts, and no-overwrite behavior.
- Create: `tests/unit/knowledge/test_content_completeness.py`
  Adds content-depth gates for literature, SOP, parameter, failure-case, and report-template readiness.
- Create: `tests/integration/test_script_knowledge_alignment.py`
  Adds script-to-knowledge and resource-bound checks across `scripts/*`.
- Modify: `tests/unit/knowledge/test_literature_knowledge_pack.py`
  Tightens verified-card requirements as batches are refreshed.
- Modify: `tests/unit/knowledge/test_references_coverage.py`
  Adds retrieval regressions for every content-complete module.
- Modify: `docs/HANDOFF.md`
  Records every completed batch with checklist blocks and verification evidence.

## Batch Map

| Batch | Owner role | Scope | Main proof |
|---|---|---|---|
| B00 | `test_eval` + `llm_orchestrator` | Baseline audit and content-completeness tests | failing tests identify missing content |
| B01 | `popgen_quantgen` | Recent-literature DOI/PMID refresh | zero unreviewed citation-export markers in accepted cards |
| B02 | `popgen_quantgen` | Classic method literature and method crosswalk | classic cards cover each major method family |
| B03 | `popgen_quantgen` | Domain SOPs for five workflow folders | every script family has an SOP with inputs, outputs, risks, and report use |
| B04 | `popgen_quantgen` + `hpc_scheduler` | Parameter/resource playbooks | every command template has explicit CPU/memory/thread/walltime guidance |
| B05 | `safety_fuse` | Failure cases and diagnostics | safe repair vs breaker rules exist for major tool/log patterns |
| B06 | `popgen_quantgen` | Species overlays | cattle, pig, poultry, sheep/goat, aquaculture defaults and caveats are filled |
| B07 | `llm_orchestrator` | Retrieval and local source ingestion | source-fetch and retrieval traceability tests cover the full content |
| B08 | `test_eval` + `orchestrator` | Final evidence gate and publication | full test gate, diff safety scan, HANDOFF, commit, push |

The batches can be developed in separate branches or worktrees. Merge order should be B00 first, B01-B06 in any reviewed order, B07 after at least two content batches, and B08 last.

### Task 1: B00 Baseline Content Audit Gates

**Files:**
- Create: `tests/unit/knowledge/test_content_completeness.py`
- Modify: `tests/unit/knowledge/test_references_coverage.py`

- [ ] **Step 1: Add failing tests for content completeness**

Add this test file:

```python
from __future__ import annotations

import re
from pathlib import Path

from knowledge.indexing import ReferenceKnowledgeIndexer


REFERENCES = Path("references")
RECENT = REFERENCES / "papers" / "animal_genomics_recent_high_impact_2022_2026.md"
SCRIPT_GUIDES = sorted(Path("scripts").glob("*/operation_guide.md"))


def test_recent_literature_cards_have_refresh_state() -> None:
    text = RECENT.read_text(encoding="utf-8")
    sections = re.split(r"(?=^## RECENT-\d+ )", text, flags=re.MULTILINE)
    cards = [section for section in sections if section.startswith("## RECENT-")]
    assert len(cards) == 72
    for section in cards:
        heading = section.splitlines()[0]
        assert "- DOI/PMID:" in section, heading
        assert "- Source links:" in section, heading
        assert "- GeneAgent use:" in section, heading
        assert "- Boundary/risk:" in section, heading


def test_every_workflow_has_operation_guide_and_sop_bridge() -> None:
    expected = {
        "association_mapping",
        "genotype_processing",
        "population_genetics",
        "quantitative_genetics",
        "reporting_audit",
    }
    actual = {path.parent.name for path in SCRIPT_GUIDES}
    assert expected <= actual
    for path in SCRIPT_GUIDES:
        text = path.read_text(encoding="utf-8")
        assert "references/sop/" in text, path
        assert "references/parameter_playbooks/" in text, path
        assert "Output contract" in text or "output contract" in text, path


def test_reference_index_has_content_depth_floor() -> None:
    result = ReferenceKnowledgeIndexer(REFERENCES).build()
    assert result.errors == []
    assert result.manifest.doc_count >= 380
    assert result.manifest.chunk_count >= 380
```

- [ ] **Step 2: Verify the audit test fails for real gaps**

Run:

```powershell
$env:PYTHONUTF8='1'; $env:PYTHONIOENCODING='utf-8'; .\.venv\Scripts\python.exe -m pytest -q tests\unit\knowledge\test_content_completeness.py
```

Expected: FAIL on missing SOP bridges, missing output-contract wording, or current chunk-count floor. If it passes immediately, raise the floor to the current count plus the planned minimum batch size of 20 chunks.

- [ ] **Step 3: Add retrieval queries for content-complete domains**

Append query expectations to `tests/unit/knowledge/test_references_coverage.py`:

```python
CONTENT_COMPLETENESS_QUERIES = {
    "plink2 bcftools genotype processing operation guide SOP output contract": {
        "sop_genotype_processing_execution",
        "playbook_qc_defaults",
    },
    "population genetics PCA admixture ROH LD selection signature SOP": {
        "sop_population_genetics_execution",
        "domain_selection_signatures_fst_window_policy",
    },
    "GCTA GRM REML heritability genomic prediction resource threads memory": {
        "sop_quantitative_genetics_execution",
        "playbook_grm_resource_baseline",
    },
    "GWAS mixed model GEMMA association mapping QTL report caveat": {
        "sop_association_mapping_execution",
        "domain_association_mapping_trait_model_policy",
    },
    "report index audit bundle diagnostic traceability source path anchor": {
        "sop_reporting_audit_execution",
        "template_report_index_v2",
    },
}
```

- [ ] **Step 4: Commit the failing audit gate**

Commit only the new/modified test files:

```powershell
git add tests/unit/knowledge/test_content_completeness.py tests/unit/knowledge/test_references_coverage.py
git commit -m "test: add knowledge content completeness gates"
```

### Task 2: B01 Refresh Recent High-Impact Literature Cards

**Files:**
- Create: `references/papers/literature_refresh_log_2026.md`
- Modify: `references/papers/animal_genomics_recent_high_impact_2022_2026.md`
- Modify: `tests/unit/knowledge/test_literature_knowledge_pack.py`

- [ ] **Step 1: Add a stricter refresh-progress test**

Modify `tests/unit/knowledge/test_literature_knowledge_pack.py` with:

```python
def test_recent_pack_has_at_least_half_verified_cards_after_refresh_batch() -> None:
    text = RECENT_PACK.read_text(encoding="utf-8")
    sections = re.split(r"(?=^## RECENT-\d+ )", text, flags=re.MULTILINE)
    cards = [section for section in sections if section.startswith("## RECENT-")]
    verified = [
        section
        for section in cards
        if "verify before citation export" not in next(
            line for line in section.splitlines() if line.startswith("- DOI/PMID:")
        )
    ]
    assert len(verified) >= 36
```

- [ ] **Step 2: Verify the refresh-progress test fails before B01**

Run:

```powershell
$env:PYTHONUTF8='1'; $env:PYTHONIOENCODING='utf-8'; .\.venv\Scripts\python.exe -m pytest -q tests\unit\knowledge\test_literature_knowledge_pack.py::test_recent_pack_has_at_least_half_verified_cards_after_refresh_batch
```

Expected: FAIL until at least 36 recent cards have DOI/PMID and publisher links without refresh markers.

- [ ] **Step 3: Create the literature refresh log**

Create `references/papers/literature_refresh_log_2026.md` with `knowledge_item.v2` metadata and one `##` section per batch:

```markdown
## B01 Recent Literature Refresh Protocol

```yaml
knowledge_item.v2:
  doc_id: literature_refresh_protocol_2026
  version: v2
  species: multi_species
  blueprint_scope: knowledge_governance
  evidence_level: sop
  source: paper
  updated_at: 2026-06-11T00:00:00+08:00
  owner: popgen_quantgen
```

Each refreshed card must include a concrete title, year, journal or publisher, DOI or PMID, official source link, species/data scope, GeneAgent use, and boundary/risk. Google Scholar-only cards remain candidate cards and cannot be exported as manuscript citations.
```

- [ ] **Step 4: Refresh RECENT-09 to RECENT-36**

For each card:

1. Query CrossRef, PubMed, Semantic Scholar, and the publisher DOI page.
2. Replace generic `- Paper:` text with `Author/team. *Concrete title*.`.
3. Replace `DOI to verify before citation export` with `DOI `10.xxxx/...`` or `PMID `12345678``.
4. Replace Google Scholar-only links with DOI, PubMed, publisher, or journal links.
5. Record the decision in `references/papers/literature_refresh_log_2026.md`.

Do not add raw PDF files to Git.

- [ ] **Step 5: Run B01 tests and commit**

Run:

```powershell
$env:PYTHONUTF8='1'; $env:PYTHONIOENCODING='utf-8'; .\.venv\Scripts\python.exe -m pytest -q tests\unit\knowledge\test_literature_knowledge_pack.py tests\unit\knowledge\test_references_coverage.py
git diff --check -- references/papers tests/unit/knowledge
git add references/papers tests/unit/knowledge/test_literature_knowledge_pack.py tests/unit/knowledge/test_references_coverage.py
git commit -m "docs: refresh recent animal genomics literature cards"
```

### Task 3: B02 Complete Classic Literature and Method Crosswalks

**Files:**
- Modify: `references/papers/animal_genomics_classic_landmarks.md`
- Modify: `references/papers/qc_core_papers_v1.md`
- Modify: `references/papers/pca_core_papers_v1.md`
- Modify: `references/papers/grm_core_papers_v1.md`
- Modify: `references/papers/genomic_prediction_core_papers_v1.md`
- Modify: `tests/unit/knowledge/test_literature_knowledge_pack.py`

- [ ] **Step 1: Add method-family coverage assertions**

Add this test:

```python
def test_classic_literature_covers_required_method_families() -> None:
    text = CLASSIC_PACK.read_text(encoding="utf-8").lower()
    required_terms = [
        "animal model",
        "blup",
        "gblup",
        "single-step",
        "genomic selection",
        "mixed model",
        "gwas",
        "qtl",
        "linkage disequilibrium",
        "runs of homozygosity",
        "selection signature",
        "imputation",
    ]
    for term in required_terms:
        assert term in text, term
```

- [ ] **Step 2: Fill classic method gaps**

Update classic and core paper packs so each method family has:

- one landmark reference,
- one method-use note for GeneAgent,
- one not-applicable boundary,
- one report-explanation sentence,
- DOI/PMID or an official publisher/book/source link.

- [ ] **Step 3: Verify and commit**

Run:

```powershell
$env:PYTHONUTF8='1'; $env:PYTHONIOENCODING='utf-8'; .\.venv\Scripts\python.exe -m pytest -q tests\unit\knowledge\test_literature_knowledge_pack.py
git diff --check -- references/papers tests/unit/knowledge/test_literature_knowledge_pack.py
git add references/papers tests/unit/knowledge/test_literature_knowledge_pack.py
git commit -m "docs: complete classic method literature crosswalk"
```

### Task 4: B03 Add Domain Execution SOPs

**Files:**
- Create: `references/sop/genotype_processing_execution_sop.md`
- Create: `references/sop/population_genetics_execution_sop.md`
- Create: `references/sop/quantitative_genetics_execution_sop.md`
- Create: `references/sop/association_mapping_execution_sop.md`
- Create: `references/sop/reporting_audit_execution_sop.md`
- Modify: `references/sop/README.md`
- Modify: `tests/unit/knowledge/test_content_completeness.py`

- [ ] **Step 1: Add SOP doc ID assertions**

Add:

```python
def test_domain_execution_sops_are_indexed() -> None:
    result = ReferenceKnowledgeIndexer(Path("references")).build()
    doc_ids = {item.doc_id for item in result.items}
    assert {
        "sop_genotype_processing_execution",
        "sop_population_genetics_execution",
        "sop_quantitative_genetics_execution",
        "sop_association_mapping_execution",
        "sop_reporting_audit_execution",
    } <= doc_ids
```

- [ ] **Step 2: Create each SOP with identical section contract**

Each SOP must contain these `##` sections:

- `Scope and Inputs`
- `Preflight Checks`
- `Execution Steps`
- `Expected Outputs`
- `Failure and Breaker Rules`
- `Report and Audit Handoff`

Each SOP must include one `knowledge_item.v2` block with `blueprint_scope` matching the workflow family and `evidence_level: sop`.

- [ ] **Step 3: Verify and commit**

Run:

```powershell
$env:PYTHONUTF8='1'; $env:PYTHONIOENCODING='utf-8'; .\.venv\Scripts\python.exe -m pytest -q tests\unit\knowledge/test_content_completeness.py tests\unit\knowledge/test_references_coverage.py
git diff --check -- references/sop tests/unit/knowledge
git add references/sop tests/unit/knowledge
git commit -m "docs: add domain execution SOPs"
```

### Task 5: B04 Complete Parameter and Resource Playbooks

**Files:**
- Modify: `references/parameter_playbooks/core_parameter_playbooks.md`
- Modify: `references/parameter_playbooks/qc_defaults.md`
- Modify: `references/parameter_playbooks/pca_component_policy.md`
- Modify: `references/parameter_playbooks/grm_resource_baseline.md`
- Modify: `references/parameter_playbooks/genomic_prediction_cv_policy.md`
- Modify: `references/parameter_playbooks/scheduler_resource_presets.md`
- Modify: `tests/unit/knowledge/test_content_completeness.py`

- [ ] **Step 1: Add playbook completeness tests**

Add:

```python
def test_parameter_playbooks_name_tools_threads_and_breakers() -> None:
    playbooks = sorted(Path("references/parameter_playbooks").glob("*.md"))
    required_terms = ["threads", "memory", "walltime", "plink", "bcftools", "gcta", "breaker"]
    combined = "\n".join(path.read_text(encoding="utf-8").lower() for path in playbooks)
    for term in required_terms:
        assert term in combined, term
```

- [ ] **Step 2: Fill parameter matrices**

Add tables for:

- PLINK/PLINK2 genotype QC and format conversion,
- bcftools normalization/filtering,
- GCTA GRM/REML,
- GWAS mixed-model tools,
- genomic prediction CV and model comparison,
- report generation and audit export.

Each row must include input size trigger, default CPU, memory estimate, walltime, command flag, output file, and breaker condition.

- [ ] **Step 3: Verify and commit**

Run:

```powershell
$env:PYTHONUTF8='1'; $env:PYTHONIOENCODING='utf-8'; .\.venv\Scripts\python.exe -m pytest -q tests\unit\knowledge/test_content_completeness.py tests\unit\knowledge/test_references_coverage.py
git diff --check -- references/parameter_playbooks tests/unit/knowledge
git add references/parameter_playbooks tests/unit/knowledge
git commit -m "docs: complete parameter and resource playbooks"
```

### Task 6: B05 Align Scripts With Knowledge Assets

**Files:**
- Modify: `scripts/genotype_processing/run_genotype_qc.sh`
- Modify: `scripts/population_genetics/run_population_structure_diversity.sh`
- Modify: `scripts/quantitative_genetics/run_relationship_matrix.sh`
- Modify: `scripts/quantitative_genetics/run_breeding_value_prediction.sh`
- Modify: `scripts/association_mapping/run_gwas.sh`
- Modify: `scripts/reporting_audit/*.sh`
- Modify: `scripts/*/operation_guide.md`
- Create or modify: `tests/integration/test_script_knowledge_alignment.py`

- [ ] **Step 1: Add script alignment tests**

Add:

```python
from __future__ import annotations

from pathlib import Path


SCRIPT_ROOT = Path("scripts")


def test_bio_scripts_have_explicit_resource_controls() -> None:
    scripts = sorted(SCRIPT_ROOT.glob("*/*.sh"))
    assert scripts
    for script in scripts:
        text = script.read_text(encoding="utf-8")
        assert "#!/usr/bin/env bash" in text.splitlines()[0], script
        assert "set -euo pipefail" in text, script
        assert "THREAD" in text or "CPU" in text or "NTHREADS" in text, script
        assert "--threads" in text or "--thread" in text or "OMP_NUM_THREADS" in text or "OPENBLAS_NUM_THREADS" in text, script
        assert "RESULT" in text or "OUTPUT" in text or "OUT_DIR" in text, script


def test_operation_guides_link_to_knowledge_assets() -> None:
    guides = sorted(SCRIPT_ROOT.glob("*/operation_guide.md"))
    assert guides
    for guide in guides:
        text = guide.read_text(encoding="utf-8")
        assert "references/sop/" in text, guide
        assert "references/parameter_playbooks/" in text, guide
        assert "references/failure_cases/" in text or "references/evaluation/diagnostics/" in text, guide
```

- [ ] **Step 2: Update scripts with explicit controls**

For every `.sh` script:

- keep `#!/usr/bin/env bash` and LF line endings,
- add `set -euo pipefail`,
- require `THREADS` or workflow-specific CPU variable,
- export `OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS`, `MKL_NUM_THREADS`, and `NUMEXPR_NUM_THREADS` when numerical tools may run,
- define output directories under a user-provided working directory,
- refuse to overwrite existing non-empty result directories unless an explicit `ALLOW_OVERWRITE=1` style flag exists,
- write a small run manifest containing command, inputs, output directory, threads, and timestamp.

- [ ] **Step 3: Update operation guides**

Each `operation_guide.md` must include:

- input contract,
- output contract,
- resource controls,
- related SOP link,
- related parameter playbook link,
- related failure/diagnostic link,
- report handoff path.

- [ ] **Step 4: Verify and commit**

Run:

```powershell
$env:PYTHONUTF8='1'; $env:PYTHONIOENCODING='utf-8'; .\.venv\Scripts\python.exe -m pytest -q tests\integration/test_script_knowledge_alignment.py tests\integration/test_analysis_script_templates.py
git diff --check -- scripts tests/integration
git add scripts tests/integration/test_script_knowledge_alignment.py
git commit -m "chore: align scripts with knowledge SOPs"
```

### Task 7: B06 Complete Failure Cases and Diagnostic Knowledge

**Files:**
- Modify: `references/failure_cases/operational_failure_cases.md`
- Modify: `references/evaluation/diagnostics/bio_tool_error_patterns.md`
- Modify: `references/evaluation/diagnostics/scheduler_error_patterns.md`
- Modify: `tests/unit/knowledge/test_content_completeness.py`

- [ ] **Step 1: Add diagnostic coverage test**

Add:

```python
def test_diagnostics_cover_major_tools_and_breakers() -> None:
    paths = [
        Path("references/failure_cases/operational_failure_cases.md"),
        Path("references/evaluation/diagnostics/bio_tool_error_patterns.md"),
        Path("references/evaluation/diagnostics/scheduler_error_patterns.md"),
    ]
    text = "\n".join(path.read_text(encoding="utf-8").lower() for path in paths)
    for term in ["plink", "plink2", "bcftools", "gcta", "rscript", "ssh", "nohup", "permission denied"]:
        assert term in text, term
    for term in ["safe repair", "breaker", "do not retry", "operator review"]:
        assert term in text, term
```

- [ ] **Step 2: Fill diagnostic entries**

Add entries for:

- input path missing,
- sample ID mismatch,
- PLINK duplicate variant/sample errors,
- bcftools malformed VCF/contig errors,
- GCTA memory or non-positive definite GRM errors,
- GWAS covariate rank deficiency,
- Rscript package/version missing,
- SSH permission denied,
- lost PID without state sentinel,
- output directory exists,
- disk quota/full filesystem.

Each entry must state detection pattern, likely cause, safe repair, breaker rule, and report wording.

- [ ] **Step 3: Verify and commit**

Run:

```powershell
$env:PYTHONUTF8='1'; $env:PYTHONIOENCODING='utf-8'; .\.venv\Scripts\python.exe -m pytest -q tests\unit\knowledge/test_content_completeness.py tests\unit\knowledge/test_references_coverage.py
git diff --check -- references/failure_cases references/evaluation/diagnostics tests/unit/knowledge
git add references/failure_cases references/evaluation/diagnostics tests/unit/knowledge
git commit -m "docs: expand diagnostic failure knowledge"
```

### Task 8: B07 Complete Species Overlays

**Files:**
- Modify: `references/papers/species_literature_index.md`
- Modify: `references/analysis_domains/*.md`
- Modify: `tests/unit/knowledge/test_references_coverage.py`

- [ ] **Step 1: Add species retrieval expectations**

Add retrieval queries for:

```python
SPECIES_OVERLAY_QUERIES = {
    "cattle dairy beef taurine indicine genomic prediction selection pangenome": {"species_overlay_cattle_defaults"},
    "pig commercial line hybrid regulatory variant meat quality genomic prediction": {"species_overlay_pig_defaults"},
    "chicken poultry egg meat disease resistance population structure GWAS": {"species_overlay_poultry_defaults"},
    "sheep goat small ruminant wool milk adaptation ROH selection": {"species_overlay_sheep_goat_defaults"},
    "aquaculture fish shrimp salmon tilapia genomic selection disease resistance": {"species_overlay_aquaculture_defaults"},
}
```

- [ ] **Step 2: Fill species overlays**

Each species overlay must include:

- common input types,
- typical marker densities,
- reference genome caveats,
- common traits,
- default QC cautions,
- common population-structure pitfalls,
- literature anchors,
- report wording boundaries.

- [ ] **Step 3: Verify and commit**

Run:

```powershell
$env:PYTHONUTF8='1'; $env:PYTHONIOENCODING='utf-8'; .\.venv\Scripts\python.exe -m pytest -q tests\unit\knowledge/test_references_coverage.py
git diff --check -- references/papers references/analysis_domains tests/unit/knowledge
git add references/papers/species_literature_index.md references/analysis_domains tests/unit/knowledge/test_references_coverage.py
git commit -m "docs: complete species knowledge overlays"
```

### Task 9: B08 Final Knowledge Acceptance Gate

**Files:**
- Modify: `tests/unit/knowledge/test_content_completeness.py`
- Modify: `docs/HANDOFF.md`

- [ ] **Step 1: Tighten final completeness assertions**

At the end of execution, `tests/unit/knowledge/test_content_completeness.py` should enforce:

```python
def test_final_knowledge_content_completeness_floor() -> None:
    result = ReferenceKnowledgeIndexer(Path("references")).build()
    assert result.errors == []
    assert result.manifest.doc_count >= 430
    assert result.manifest.chunk_count >= 430


def test_no_recent_cards_remain_google_scholar_only_when_claiming_final() -> None:
    text = RECENT.read_text(encoding="utf-8")
    sections = re.split(r"(?=^## RECENT-\d+ )", text, flags=re.MULTILINE)
    cards = [section for section in sections if section.startswith("## RECENT-")]
    for section in cards:
        heading = section.splitlines()[0]
        source_line = next(line for line in section.splitlines() if line.startswith("- Source links:"))
        assert "[Google Scholar]" not in source_line or source_line.count("](") > 1, heading
```

- [ ] **Step 2: Run full knowledge gate**

Run:

```powershell
$env:PYTHONUTF8='1'; $env:PYTHONIOENCODING='utf-8'; .\.venv\Scripts\python.exe -m pytest -q tests\unit\knowledge tests\integration/test_script_knowledge_alignment.py tests\integration/test_analysis_script_templates.py
```

Expected: PASS.

- [ ] **Step 3: Run full project gate**

Run:

```powershell
$env:PYTHONUTF8='1'; $env:PYTHONIOENCODING='utf-8'; $env:PYTHONPYCACHEPREFIX='D:\geneagent\pycache_temp'; .\.venv\Scripts\python.exe -m compileall src tests
$env:PYTHONUTF8='1'; $env:PYTHONIOENCODING='utf-8'; .\.venv\Scripts\python.exe -m pytest -q
git diff --check -- references scripts tests docs/HANDOFF.md
```

Expected: PASS. Git may warn about LF-to-CRLF on Windows; no whitespace errors may appear.

- [ ] **Step 4: Run safety scans**

Run:

```powershell
git diff | rg -n "BEGIN OPENSSH|PRIVATE KEY|password=|GENEAGENT_HPC_SSH_PASSWORD|10\.11\.|\.vcf|\.bam|\.cram|\.fastq|\.fq|\.fasta|\.pdf|\.tei|embedding|bm25"
rg --files references | rg "\.(bam|bcf|cram|fasta|fastq|fq|pdf|tei|vcf|xml)$"
```

Expected: no committed credentials, server-private details, raw entity data, raw PDFs, TEI/XML, extracted full text, or indexes.

- [ ] **Step 5: Update HANDOFF and commit final batch**

Append a `docs/HANDOFF.md` entry with:

- `completed_checklist` for every B00-B08 batch completed,
- `not_yet_done_checklist` containing only optional expansion beyond the delivery knowledge base,
- exact verification commands and results,
- `gate_result: pass`.

Commit:

```powershell
git add references scripts tests docs/HANDOFF.md docs/superpowers/plans/2026-06-11-knowledge-content-fill-plan.md
git commit -m "docs: complete GeneAgent knowledge content"
git push
```

## Definition of Content Complete

The knowledge base is content complete only when all of these are true:

- Every planned formal knowledge layer has enough content for an operator to run and interpret animal genetics workflows without inventing missing method rules.
- Every recent literature card is either verified for citation export or explicitly marked as a non-export candidate with a refresh record.
- Every script folder has an operation guide, a domain SOP, parameter playbook links, failure-case links, and output/report handoff instructions.
- Every major tool family has resource controls, failure diagnostics, and breaker rules.
- Every species overlay includes both useful defaults and warnings against invalid cross-species transfer.
- `ReferenceKnowledgeIndexer(Path("references")).build()` has no errors and all `doc_id` values are globally unique.
- Retrieval regression tests cover literature, input contracts, genotype processing, population genetics, association mapping, quantitative genetics, functional annotation, reporting/audit, failure diagnostics, and local source-ingestion policy.
- The Git diff contains no raw data, no raw PDFs, no private server details, and no credentials.

## Self-Review

Spec coverage:

- Literature content is covered by B01 and B02.
- SOP content is covered by B03.
- Parameter and resource content is covered by B04.
- Code/script knowledge alignment is covered by B05.
- Failure diagnostics are covered by B06.
- Species content is covered by B07.
- Retrieval, tests, gates, HANDOFF, and publication are covered by B08.

Placeholder scan:

- This plan intentionally uses no unresolved placeholder markers.
- Every task names concrete files and commands.
- Code-changing tasks include explicit test snippets or shell commands.

Risk review:

- Full DOI/PMID verification requires online metadata sources and may hit rate limits; each batch must keep a refresh log and may be split into smaller commits.
- Some candidate papers may be rejected when metadata cannot be verified or quality is weak; rejected candidates should be recorded in the refresh log rather than silently retained.
- Windows line-ending warnings are acceptable only when `git diff --check` reports no whitespace errors.
