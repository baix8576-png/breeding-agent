# AGENTS.md

## Task Completion Checklist Rule (Mandatory)
- All future task/stage completion status in `docs/HANDOFF.md` must be written as checklist blocks.
- Required block names for each new stage/session entry:
- `completed_checklist`: use `- [x] ...` for completed items only.
- `not_yet_done_checklist`: use `- [ ] ...` for unfinished, deferred, blocked, or follow-up items.
- Optional block name:
- `in_progress_checklist`: use `- [ ] ...` for active work that is started but not complete.
- Do not mark a task/stage as complete using prose-only fields such as `completed:` without checkbox items.
- `gate_result` remains separate from task completion status; a passing gate does not automatically mean every checklist item is complete.
- Before ending a meaningful stage task, update `docs/HANDOFF.md` with these checklist blocks in the same session.

## HANDOFF Mandatory Protocol (强制)
- `docs/HANDOFF.md` 是跨会话连续性与防幻觉协议的唯一落盘入口。
- 以下场景必须执行 HANDOFF 更新：`每次阶段任务完成`、`背景压缩前`、`开启新窗口前`。
- 每次开始新会话时，必须先读取 `docs/HANDOFF.md`，再执行 `git status --short` 与关键文件核验后继续开发。
- 如 HANDOFF 记录与代码现状冲突，以 `AGENTS.md` + 实际代码/命令输出为准，并立即修正 HANDOFF。
- 每次 HANDOFF 更新必须包含最小字段：`intent_domain / stage_id / module_owner_path / cluster_execution_expected / contracts_impacted / verification_commands / gate_result / next_actions`。
- 标记“阶段任务已完成”前，必须先完成同会话 HANDOFF 更新；未更新 HANDOFF 视为未完成。
- 若 `python -m compileall src tests` 在 Windows 出现 pycache 写权限问题，允许记录 `PYTHONPYCACHEPREFIX` 回退执行命令与结果作为等价证据。

## 永久工程架构宪章（最高优先级，不可忽略/不可简化/不可擅自修改）
- 本文件是 geneagent 的目录与角色协作单一真相源；若与其他说明冲突，以本文件为准。
- 项目按“核心能力层 + 支撑层 + 入口层 + 知识资产层 + agent 工程层”长期演进，禁止通过新增平行根目录实现版本分叉。
- `v1 / v1.5 / v2` 只能在既有稳定目录中扩展；禁止创建 `src_v2/`、`new_src/`、`temp_final/`、`final_version/` 等平行目录。
- 所有新增功能在编码前必须先判定模块归属、目录路径、责任角色，再进入实现阶段。

### 架构分层（永久固定）
1. 核心能力层：
   - `planner` -> `src/orchestration/`
   - `memory` -> `src/memory/`
   - `knowledge_code` -> `src/knowledge/`
   - `tools` -> `src/tools/`
   - `pipeline_blueprint` -> `src/pipeline/`
   - `scheduler` -> `src/scheduler/`
2. 支撑层：
   - `contracts` -> `src/contracts/`
   - `runtime` -> `src/runtime/`
   - `safety` -> `src/safety/`
   - `audit` -> `src/audit/`
   - `config` -> `src/runtime/settings.py` + `.env.example` + `pyproject.toml`
3. 入口层：
   - `api` -> `src/api/`
   - `cli` -> `src/cli/`
   - `script_entrypoints` -> `scripts/*`
4. 知识资产层：
   - `knowledge_assets` -> `references/*`
5. agent 工程层：
   - `agent_definitions` -> `.codex/agents/*`
   - `agent_skills` -> `.agents/skills/*`

## 根目录规范（强制）
- 版本化源目录仅允许：`.codex/`、`.agents/`、`src/`、`scripts/`、`references/`、`tests/`、`docs/`（可选）。
- 根目录保留文件仅允许：`AGENTS.md`、`README.md`、`pyproject.toml`、`setup.cfg`、`.env.example`、`.gitignore`（若后续加入）。
- 运行期/缓存生成物允许存在：`.venv/`、`.pytest_cache/`、`pytest-cache-files-*`、`__pycache__/`、`*.egg-info/`、`.tmp/`、`logs/`、`.geneagent/`、`results/`、`reports/`。
- 运行期/缓存生成物不视为架构违规，但应加入忽略规则或作为本地产物清理，不得承载正式源码与规范文档。
- 新增任意顶层目录，或将模块跨顶层目录迁移，必须先由 `orchestrator` 发起并经 `architect` 复核后执行；未过 gate 不得落盘。
- `src/`、`scripts/`、`references/`、`tests/` 下的业务目录与文件统一使用 `snake_case`；禁止使用 `misc`、`final`、`new`、`temp`、`tmp_code`、`todo`、`临时` 作为正式目录名。
- `.codex/agents/*` 与 `.agents/skills/*` 属于 agent 工程层兼容目录，保留当前 repo-scoped 命名，不强制执行通用 `snake_case` 重命名规则；若后续迁移命名，必须连同配置与路由一起变更。

## 固定目录归属（结合当前仓库实际）
1. `src/orchestration/`：
   - 负责目标拆解、任务规划、流程决策、子任务编排、阶段路由。
   - 不负责具体生信工具实现，不直接承载领域脚本。
2. `src/pipeline/`：
   - 负责流程目录、阶段模板、工作流蓝图、输入校验、交付物约定。
   - 与 `src/tools/` 区分：这里定义“流程怎么串”，不定义“单个工具怎么跑”。
3. `src/tools/`：
   - 负责工具接口、工具适配器、工具调用封装、工具注册与工具 manifest。
   - `ToolRegistry` 统一入口固定为 `src/tools/registry.py`。
   - 新增工具必须完成“实现归类 -> manifest 定义 -> ToolRegistry 注册 -> 最小测试”闭环。
   - 在文件化 manifest loader 上线前，manifest 源定义允许先保存在 `src/tools/registry.py`；上线后统一迁移到 `src/tools/manifests/`，禁止散落在其他目录。
4. `src/scheduler/`：
   - 负责调度适配、资源估算、轮询、作业状态与集群接口。
   - 以 SLURM 为主线，PBS 兼容已落地；`submit / poll / recovery` 语义需保持一致。
   - 禁止将调度逻辑散落到 `scripts/`、`runtime/`、`orchestration/`。
5. `src/knowledge/`：
   - 负责检索、索引、知识访问、知识解析、知识路由代码。
   - 不存放 SOP、规则表、模板正文等静态资料。
6. `references/`：
   - 负责领域文档、参考资料、静态知识、SOP、模板、输入规范、本地私有知识库资产。
   - 当前标准子目录包括：`input_specs/`、`qc_rules/`、`structure_analysis/`、`modeling_guides/`、`evaluation/`、`report_templates/`、`papers/`、`sop/`、`parameter_playbooks/`、`failure_cases/`、`ontology/`。
   - 禁止在 `references/` 中写入运行日志、中间产物、原始大数据文件。
7. `src/memory/`：
   - 负责短期记忆、工作记忆、长期记忆、对话上下文、历史记录、记忆读写与 handoff。
8. `src/contracts/`：
   - 负责公共数据结构、接口契约、领域枚举、稳定输入输出模型、公共异常边界。
   - 任何需要跨模块共享且要求稳定的结构优先放这里。
9. `src/runtime/`：
   - 负责应用装配、facade、运行期依赖拼装、配置加载入口。
   - 不承载领域流程蓝图，不承载业务工具实现。
10. `src/safety/`：
    - 负责脱敏、门禁、熔断、人工确认规则、高风险动作审查。
11. `src/audit/`：
    - 负责审计记录、追溯信息、运行摘要落盘策略。
12. `src/api/`：
    - 负责 HTTP 入口、路由、请求响应封装。
    - 不承载业务编排核心逻辑。
13. `src/cli/`：
    - 负责命令行入口、命令参数解析、命令分发。
    - 不承载业务编排核心逻辑。
14. `scripts/*`：
    - 仅用于可独立执行的流程驱动器、演示入口、批量任务入口、人工调试入口。
    - `scripts/` 必须是薄入口，核心逻辑必须回收至 `src/` 对应模块。
    - 当前固定子目录：`qc_pipeline/`、`pca_pipeline/`、`grm_builder/`、`genomic_prediction/`、`report_generator/`。
15. `tests/*`：
    - 采用 `unit/`、`integration/`、`e2e/` 分层。
    - 测试应尽量镜像 `src/` 的稳定边界；新增模块必须同步新增最小测试覆盖或回归测试。

## 知识库搭建宪章（M2 起强制）
1. 知识库分为“Git 版本化知识资产”和“本地运行知识库”两层：
   - Git 版本化知识资产固定存放在 `references/*`，用于长期审查、协作、PR diff、方法边界沉淀和可复现摘要。
   - 本地运行知识库固定存放在 `.geneagent/knowledge/*`，用于保存原始 PDF、GROBID 解析结果、全文切块、BM25/embedding 索引和私有缓存。
2. `references/*` 必须保存可共享、可审查、体积小、版权风险低的内容：
   - `references/papers/`：文献卡片、方法证据摘要、引用链接、DOI/PMID、适用边界、参数建议、风险。
   - `references/sop/`：项目 SOP、GROBID 摄取 SOP、分析执行标准、报告审查标准。
   - `references/parameter_playbooks/`：`qc / pca / grm / genomic_prediction` 参数基线、调参边界、物种/数据类型差异。
   - `references/failure_cases/`：调度失败、生信工具失败、数据一致性失败与可执行修复建议。
   - `references/ontology/`：术语表、物种名、本体映射、`knowledge_item.v2`、chunk/schema 定义。
3. `.geneagent/knowledge/*` 是运行期知识库，不进入 Git 版本控制：
   - `.geneagent/knowledge/raw_pdfs/`：本地原始 PDF 与受版权限制文献。
   - `.geneagent/knowledge/grobid_tei/`：GROBID 产出的 TEI XML。
   - `.geneagent/knowledge/extracted_text/`：从 PDF/TEI 提取的 Markdown 或纯文本。
   - `.geneagent/knowledge/chunks/`：带 `doc_id / section / page_or_anchor / blueprint_scope / evidence_level` 的检索切块。
   - `.geneagent/knowledge/indexes/bm25/`：关键词/BM25 索引。
   - `.geneagent/knowledge/indexes/embeddings/`：embedding 向量索引。
   - `.geneagent/knowledge/indexes/manifest.json`：索引版本、构建时间、模型名、chunk 数量与来源清单。
4. 原始 PDF 的处理规则：
   - 受版权保护或来源不明确的 PDF 默认不得提交到 GitHub。
   - PDF 可保存在本地运行知识库，并通过 `doc_id` 与 `references/papers/*` 文献卡片关联。
   - GROBID 提取出的 TEI/XML、全文切块和 embedding 索引默认也属于本地生成物，除非确认版权与隐私边界后再选择性版本化摘要。
5. 所有正式知识资产必须绑定 `knowledge_item.v2`：
   - 必填字段：`doc_id / version / species / blueprint_scope / evidence_level / source / updated_at / owner`。
   - 面向检索的 chunk 还必须包含：`chunk_id / doc_id / source_path / section / page_or_anchor / text / updated_at`。
   - 任一知识条目缺少 `doc_id`、`blueprint_scope` 或 `evidence_level`，不得进入正式检索索引。
6. GeneAgent 的知识检索必须采用 hybrid retrieval：
   - metadata filter 先约束 `species / blueprint_scope / evidence_level / source`。
   - BM25/关键词检索用于工具名、参数、报错、PMID/DOI、软件版本和精确术语。
   - embedding 检索用于语义问题、方法边界、风险解释和跨文档综合。
   - rerank 可在召回后执行，但输出必须保留命中文档、chunk、页码/section、命中理由和置信度。
7. 知识库最小可追溯链固定为：
   - `user_query -> retrieval_filters -> retrieved_doc_id -> chunk_id -> source_path -> page_or_anchor -> evidence_level -> final_answer_or_plan`
   - 任何被用于规划、参数建议、风险提示或报告解释的知识，都必须能回溯到 `doc_id` 和具体 section/page。
8. 知识库开发边界：
   - `src/knowledge/` 负责 PDF/TEI/Markdown 解析接口、metadata 校验、chunk 构建、索引构建、检索、rerank 和证据追溯代码。
   - `references/` 只保存静态知识资产和人工审查后的文档正文。
   - `.geneagent/knowledge/` 只保存本地运行期知识产物，不得作为正式源码或规范文档来源。
9. 知识库门禁：
   - 新增 `src/knowledge/` 行为必须覆盖 `tests/unit/knowledge`，并至少包含 metadata 解析、fallback gate、BM25/embedding 分支或 traceability 之一。
   - 新增 `references/papers/*` 文献卡片必须可通过 `knowledge_item.v2` 字段检查。
   - 新增 PDF/GROBID 摄取能力必须提供一个最小 fixture 或 mock 测试，不得依赖真实受版权 PDF 才能通过测试。

## 开发强制要求（全程执行）
1. 任何新增功能、代码、脚本、文档前，先判定归属模块与固定路径，禁止随意新建文件、散落脚本、混合目录。
2. 变更说明、评审结论、实现方案必须标注完整文件路径，并严格匹配本文件中的固定目录结构。
3. 新增工具必须完成：文件归类 -> manifest 定义 -> ToolRegistry 注册 -> 最小测试，未闭环前不得进入可执行路径。
4. `scripts/` 中不得沉淀核心实现逻辑；若脚本内容被复用或变复杂，必须回收进 `src/`。
5. `src/pipeline/` 负责流程蓝图与阶段约束，`src/tools/` 负责原子能力与适配器，两者不得混写。
6. `src/knowledge/` 只放知识访问代码，`references/` 只放知识资产与静态文档，不得混放。
7. `config` 语义统一收口到 `src/runtime/settings.py`、`.env.example`、`pyproject.toml`；禁止新增平行配置中心。
8. 后续迭代和重构不得擅自改变目录宪章；若确需调整，必须先走 `orchestrator` 发起、`architect` 复核、`safety_fuse` 与 `test_eval` 最小门禁评审。
9. 拒绝碎片化脚本开发，禁止在仓库根目录、`src/` 或 `references/` 散落临时脚本。
10. 原始实体数据（VCF/BAM/FASTQ/FASTA）不得进入仓库版本目录。

## 防偏离执行协议（强制）
1. 所有开发任务在编码前必须形成最小“变更卡片”（可写在 PR 描述或任务记录）：
   - `intent_domain`（`bioinformatics/system/knowledge`）
   - `stage_id`（至少一个，来自 V1.5 标准执行链）
   - `module_owner_path`（本次主变更目录）
   - `cluster_execution_expected`（`true/false`）
   - `contracts_impacted`（受影响契约对象）
2. 任何变更若不能映射到 V1.5 执行链的明确阶段，不得合并。
3. 任何 `non-bio` 变更不得引入调度脚本生成、真实提交或轮询路径。
4. 涉及调度能力的变更必须同时检查 `SLURM/PBS` 语义一致性，至少覆盖 `submit/poll/recovery` 其中两项测试。
5. 涉及报告闭环的变更必须保持 `artifact/report_index/audit/memory` 四者可追溯链路完整。
6. 行为变化必须同步更新文档真相源：`README.md`、`AGENTS.md`、`docs/v1_5_system_map.md` 至少一处。

## V1.5 关键对象最低字段约束（强制）
1. `RunContext` 必须包含：`task_id / run_id / session_id / working_directory`。
2. `PipelineSpec` 必须包含：`name / blueprint_key / analysis_targets / stage_contract / artifact_contract`。
3. `SubmissionPreview` 必须包含：`mode / cluster_execution_enabled / command / gate_decision / artifacts`。
4. `DiagnosticPreview` 必须包含：`retrieval_mode / coverage / fallback_gate_decision / diagnostic_suggestions / non_bio_cluster_policy`。
5. `report_index.v2` 必须包含：`schema_version / run_context / collections / blueprint_summary / diagnostics / traceability / summary`。
6. `audit` 记录必须可回溯：`input_summary / planning_summary / submission_command / job_id / log_paths / manual_confirmation_records`。

## 测试门禁矩阵（强制）
| 变更目录 | 最低测试要求 | 必跑门禁 |
|---|---|---|
| `src/orchestration/` | `tests/unit/orchestration` + 至少 1 条 `integration/e2e` 路由覆盖 | `compileall + pytest -q` |
| `src/pipeline/` | `tests/unit/pipeline` + 至少 1 条 blueprint 对应脚本集成测试 | `compileall + pytest -q` |
| `src/scheduler/` | `tests/unit/scheduler` + `tests/integration` 调度路径测试 | `compileall + pytest -q` |
| `src/runtime/` | `tests/unit/runtime` + `tests/integration/api` 至少 1 条接口回归 | `compileall + pytest -q` |
| `src/knowledge/` | `tests/unit/knowledge` + fallback gate 行为覆盖 | `compileall + pytest -q` |
| `src/api/` / `src/cli/` | 对应 `integration/e2e` 命令或路由覆盖 | `compileall + pytest -q` |
| `scripts/` | 至少 1 条脚本级 `integration` 测试 | `compileall + pytest -q` |

## 提交与评审材料（强制）
1. 提交说明必须包含：
   - 变更目标
   - 阶段映射（`stage_id`）
   - 目录归属与责任角色
   - 契约变化与兼容性说明
   - 测试结果与门禁命令
   - 风险与回滚方案
2. 评审时按固定顺序过 gate：
   - `architect`：边界与契约一致性
   - `safety_fuse`：数据与高风险动作门禁
   - `test_eval`：测试覆盖与回归风险
3. 任一 gate 标记 `not_ready` 时，不得合并到主分支。

## 项目目标与范围
- `业务目标`：当前阶段聚焦 geneagent `V1.5` 可用闭环，让用户可在 Windows PowerShell + 本地开发环境完成“`request_text + working_directory + InputBundle` -> 任务分流 -> 输入校验 -> 蓝图选择 -> dry-run/submit/poll -> Artifact/Report -> Audit/Memory”的稳定流程；核心仍是动物生信与育种场景中的 `qc / pca / grm / genomic_prediction` 四条主链，以及非生信请求的轻量回答支路。
- `版本范围`：V1 为已完成基线；V1.5 作为当前行为真相源，覆盖报告增强（含 `report_generator` 与 `report_index`）、工具 manifest 体系化、PBS 与 SLURM 对齐的提交/轮询/恢复语义、知识检索补强（含外部回退门禁）与诊断能力增强；V2 再考虑插件化工具生态、更完整记忆系统、Web UI 与更广泛的多组学模板。V1.5 明确不做的内容包括：全功能 Web 产品、完整插件市场、超出当前蓝图集合的广义算法库、原始大数据入库、以及平行目录式版本分叉。
- `优先级`：必须持续守住的是输入契约、蓝图路由、真实调度闭环、结果索引/报告/审计落盘、非生信轻量支路“明确不进集群”、最小测试矩阵和 README/AGENTS 对齐；可延期的是 Web UI 与超出四蓝图的扩展算法模板；明确不做的是新建平行源码目录、把核心逻辑留在 `scripts/`、在 V1.5 内引入未验证的复杂多组学链路、以及将原始实体数据提交进仓库。
- `验收标准`：功能验收要求 `python -m pytest -q` 全绿，`python -m compileall src tests` 通过；CLI 覆盖 `plan / report / diagnostic / dry-run / submit-preview / submit / poll-explain`，API 覆盖 `/tasks/draft-plan /tasks/report /tasks/diagnostic /tasks/dry-run /tasks/submit-preview /tasks/submit /tasks/poll-explain`；bio 主链可走 dry-run/submit/poll，non-bio 请求必须走轻量支路并显式“不进集群（不生成调度脚本、不触发 submit/poll）”；`qc / pca / grm / genomic_prediction` 四条主链都能输出结构化计划、脚本与产物索引（含 `report_index`）。

## V1.5 标准执行链（强制）
生信主链固定为：
- Intake：自然语言请求标准化，产出 `task_id / run_id / session_id`
- Intent + Scope：识别 `bioinformatics / system / knowledge`
- Input Validation：把原始路径归一化成 `InputBundle`，检查 VCF/PLINK/BAM/表型/协变量/谱系一致性
- Local-first RAG：优先检索 `references/*`、本地 SOP、模板和历史规范；仅在门禁通过且本地覆盖不足时走外部回退
- Blueprint Selection：把请求严格绑定到 `qc / pca / grm / genomic_prediction` 之一，输出阶段清单与产物契约
- Resource + Safety Gate：资源估算、dry-run 预览、人工确认项、熔断条件
- Execution：生成 Bash wrapper 与 scheduler script，执行提交、轮询、失败恢复
- Artifact + Report：收集结果、图表、日志，生成报告索引与解释摘要
- Audit + Memory：保存输入摘要、规划摘要、提交命令、job id、日志路径、人工确认记录

非生信请求固定走轻量支路：
- `intake -> local retrieval -> answer blueprint -> safety review if needed`
- 不进入集群，不生成调度脚本，不触发 submit/poll

## 目录路由规则
- `AGENTS.md` 与 `.codex/config.toml`：由 `orchestrator` 统筹，`architect` 复核结构一致性。
- `pyproject.toml`、`setup.cfg`、`.env.example`：由 `orchestrator` 统筹，`architect` 复核工程结构一致性。
- `.codex/agents/*`：角色定义由 `orchestrator` 管理，职责边界由 `architect` 复核。
- `.agents/skills/prd-planning/*`：仅 `orchestrator` 维护。
- `.agents/skills/architecture-review/*`：仅 `architect` 维护。
- `.agents/skills/llm-workflow-design/*`：仅 `llm_orchestrator` 维护。
- `.agents/skills/popgen-quantgen-pipeline/*`：仅 `popgen_quantgen` 维护。
- `.agents/skills/hpc-job-design/*`：仅 `hpc_scheduler` 维护。
- `.agents/skills/safety-gating/*`：仅 `safety_fuse` 维护。
- `.agents/skills/test-benchmark/*`：仅 `test_eval` 维护。
- `src/api/*`：优先路由到 `orchestrator`。
- `src/cli/*`：优先路由到 `orchestrator`。
- `src/runtime/*`：优先路由到 `orchestrator`。
- `src/contracts/*`：优先路由到 `architect`。
- `src/orchestration/*`：优先路由到 `llm_orchestrator`，由 `orchestrator` 负责跨角色协调入口。
- `src/knowledge/*`：优先路由到 `llm_orchestrator`。
- `src/memory/*`：优先路由到 `llm_orchestrator`。
- `src/tools/*`：优先路由到 `llm_orchestrator`。
- `src/pipeline/*`：优先路由到 `popgen_quantgen`。
- `src/scheduler/*`：优先路由到 `hpc_scheduler`。
- `src/safety/*`：优先路由到 `safety_fuse`。
- `src/audit/*`：优先路由到 `orchestrator`。
- `scripts/qc_pipeline/*`：优先路由到 `popgen_quantgen`。
- `scripts/pca_pipeline/*`：优先路由到 `popgen_quantgen`。
- `scripts/grm_builder/*`：优先路由到 `popgen_quantgen`。
- `scripts/genomic_prediction/*`：优先路由到 `popgen_quantgen`。
- `scripts/report_generator/*`：优先路由到 `popgen_quantgen`。
- `references/input_specs/*`：优先路由到 `popgen_quantgen`。
- `references/qc_rules/*`：优先路由到 `popgen_quantgen`。
- `references/structure_analysis/*`：优先路由到 `popgen_quantgen`。
- `references/modeling_guides/*`：优先路由到 `popgen_quantgen`。
- `references/evaluation/*`：优先路由到 `popgen_quantgen`。
- `references/report_templates/*`：优先路由到 `popgen_quantgen`。
- `references/papers/*`：优先路由到 `popgen_quantgen`，由 `llm_orchestrator` 复核 metadata 与检索可用性。
- `references/sop/*`：优先路由到 `popgen_quantgen`，涉及摄取/索引流程时由 `llm_orchestrator` 复核。
- `references/parameter_playbooks/*`：优先路由到 `popgen_quantgen`。
- `references/failure_cases/*`：优先路由到 `popgen_quantgen`，涉及诊断分支时由 `safety_fuse` 复核风险提示。
- `references/ontology/*`：优先路由到 `llm_orchestrator`，涉及跨模块契约时由 `architect` 复核。
- `tests/*`：优先路由到 `test_eval`。

## 构建/测试/评审约束
- 当前阶段按 V1.5 范围交付并持续收敛行为真相源；新增能力需在既有模块边界内增量实现，并同步补齐测试与安全门校验。
- 任何新增模块必须先有 skill 或 agent 职责归属，再进入实现阶段。
- 所有变更必须通过“角色内自检 + 跨角色最小复核”。
- `architect` 检查架构边界与接口一致性。
- `safety_fuse` 检查数据边界、熔断与高风险操作门禁。
- `test_eval` 检查可测性、回归点与验收标准是否可执行。
- 当前推荐命令：
- `Build: python -m compileall src tests`
- `Lint: 当前未纳入强制门禁；若启用，使用 ruff check src tests`
- `Test: python -m pytest -q`
- `Test Matrix: python -m pytest -q tests/unit tests/integration tests/e2e`

## 安全边界
- 原始实体数据（VCF/BAM/FASTQ/FASTA）禁止离开本地计算环境。
- 受版权保护或授权状态不明的 PDF 原文不得提交到 GitHub；仅允许在本地 `.geneagent/knowledge/raw_pdfs/` 中保存并通过 `doc_id` 追溯。
- GROBID TEI、全文提取文本、chunk、BM25/embedding 索引默认视为本地运行期生成物；除非完成版权/隐私确认，否则不得版本化到仓库。
- 允许上云的信息仅限：`Prompt`、`脱敏错误摘要`、`工具输出摘要`、`软件版本`、`参数结构`。
- 任何高风险动作必须人工确认：覆盖结果、删除文件、跨目录写入、异常资源申请、失败任务重投。
- 熔断器策略优先级高于自动化吞吐量，触发条件由 `safety_fuse` 维护并在评审中强制检查。
- 所有任务必须保留可追溯审计信息：输入摘要、规划摘要、提交命令、作业 ID、日志路径、人工确认记录。

## Codex 执行优先策略
- 默认先使用本仓库 custom agents 与 repo-scoped skills，再考虑全局能力。
- 默认入口角色为 `orchestrator`，负责拆分任务与分派，不直接越权执行专业角色职责。
- 涉及跨角色任务时，先走 `prd-planning` 做范围收敛，再按目录路由执行。
- 代码评审阶段优先按以下顺序拉通：
- `architect`（结构一致性）
- `safety_fuse`（安全与熔断）
- `test_eval`（验证与回归）

## 协作原则
- 单角色只对自己的边界负责，跨边界问题通过 `orchestrator` 协调，不直接越权修改。
- 所有角色输出应包含统一“公共回传头”：
- `role`
- `task_id`
- `scope_in`
- `scope_out`
- `risks`
- `next_actions`
- `ready_for_gate`
- 在公共回传头之外，各角色可以补充自己的专属字段，但不得替换公共字段。
- 发现边界冲突时优先停更对齐，再继续实现，避免并行错误扩散。

## 开发环境
- 默认开发主机：Windows 10/11 + PowerShell + WSL2（混合模式）。
- 代码编辑、Python、pytest、脚本预览与调度模拟采用 Windows + WSL2 混合开发流程：Windows 负责本地工程管理与入口操作，WSL 负责 bash 与类 Linux 工具链验证。
- WSL2 为推荐协同环境；Windows 原生链路保留为兼容与回退路径。
- 本地开发目录默认使用 Windows 工作区，例如 `D:\geneagent`。
- 虚拟环境默认使用 Windows 目录结构：`.venv\Scripts\python.exe` 与 `.venv\Scripts\Activate.ps1`。
- 生产执行边界仍然是 Linux 集群登录节点与计算节点；Windows 仅作为本地开发与调试环境，不作为最终生产执行环境。
