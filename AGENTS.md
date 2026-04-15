# AGENTS.md

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
- 根目录保留文件仅允许：`AGENTS.md`、`README.md`、`pyproject.toml`、`.env.example`、`.gitignore`（若后续加入）。
- 运行期/缓存生成物允许存在：`.venv/`、`.pytest_cache/`、`pytest-cache-files-*`、`__pycache__/`、`*.egg-info/`、`.tmp/`、`logs/`。
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
   - 首版主用 SLURM，长期保留 PBS 扩展位。
   - 禁止将调度逻辑散落到 `scripts/`、`runtime/`、`orchestration/`。
5. `src/knowledge/`：
   - 负责检索、索引、知识访问、知识解析、知识路由代码。
   - 不存放 SOP、规则表、模板正文等静态资料。
6. `references/`：
   - 负责领域文档、参考资料、静态知识、SOP、模板、输入规范、本地私有知识库资产。
   - 当前标准子目录包括：`input_specs/`、`qc_rules/`、`structure_analysis/`、`modeling_guides/`、`evaluation/`、`report_templates/`。
   - 禁止在 `references/` 中写入运行日志、中间产物、原始大数据文件。
7. `src/memory/`：
   - 负责短期记忆、工作记忆、长期记忆、对话上下文、历史记录、记忆读写与 handoff。
8. `src/contracts/`：
   - 负责公共数据结构、接口契约、领域枚举、稳定输入输出模型、公共异常边界。
   - 任何需要跨模块共享且要求稳定的结构优先放这里。
9. `src/runtime/`：
   - 负责应用装配、bootstrap、facade、运行期依赖拼装、配置加载入口。
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
    - 测试应尽量镜像 `src/` 的稳定边界；新增模块必须同步新增最小测试占位或回归测试。

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

## 项目目标占位区
- `业务目标（TODO）`：在此填写当前阶段的核心业务目标、成功标准与交付时间。
- `版本范围（TODO）`：在此填写 v1 / v1.5 / v2 的功能边界与非目标。
- `优先级（TODO）`：在此填写本迭代必须完成、可延期、明确不做的事项。
- `验收标准（TODO）`：在此填写功能验收、性能验收、安全验收与文档验收标准。

## 目录路由规则
- `AGENTS.md` 与 `.codex/config.toml`：由 `orchestrator` 统筹，`architect` 复核结构一致性。
- `pyproject.toml`、`.env.example`：由 `orchestrator` 统筹，`architect` 复核工程结构一致性。
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
- `tests/*`：优先路由到 `test_eval`。

## 构建/测试/评审约束
- 当前阶段允许实现入口、接口、占位服务、测试骨架与流程蓝图，但仍不实现业务算法与生产分析逻辑。
- 任何新增模块必须先有 skill 或 agent 职责归属，再进入实现阶段。
- 所有变更必须通过“角色内自检 + 跨角色最小复核”。
- `architect` 检查架构边界与接口一致性。
- `safety_fuse` 检查数据边界、熔断与高风险操作门禁。
- `test_eval` 检查可测性、回归点与验收标准是否可执行。
- 当前推荐命令：
- `Build: python -m compileall src tests`
- `Lint: TODO（后续接入 ruff）`
- `Test: pytest`

## 安全边界
- 原始实体数据（VCF/BAM/FASTQ/FASTA）禁止离开本地计算环境。
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
- 默认开发主机：Windows 10/11 + PowerShell。
- 代码编辑、Python、pytest、脚本预览与调度模拟默认都在 Windows PowerShell 中完成，不再依赖 WSL2。
- 本地开发目录默认使用 Windows 工作区，例如 `D:\geneagent`。
- 虚拟环境默认使用 Windows 目录结构：`.venv\Scripts\python.exe` 与 `.venv\Scripts\Activate.ps1`。
- 生产执行边界仍然是 Linux 集群登录节点与计算节点；Windows 仅作为本地开发与调试环境，不作为最终生产执行环境。
