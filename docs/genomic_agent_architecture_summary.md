# 基因组生信 Agent 平台架构总结（供工程同事搭建使用）

## 1. 文档目的

本文档用于指导工程同事基于既定方案搭建一个面向动植物基因组分析的多 Agent 平台。平台目标不是单纯做一个聊天机器人，而是构建一个可执行、可追溯、可扩展的 **Genomic AI Agent Platform**，覆盖以下三类核心能力：

1. **自然语言驱动自动生信分析**  
   用户通过自然语言描述任务、数据位置、表型信息和分析目标，系统自动规划并执行标准化生信流程。
2. **基因组知识问答与分析方案设计**  
   系统能够回答基因组学/生信方法问题，并结合用户数据场景输出分析方案。
3. **湿实验验证方案设计**  
   系统能够基于候选基因、候选位点、差异表达结果等，输出对应的验证实验路线。

---

## 2. 总体设计原则

### 2.1 核心原则

- **LLM 负责理解、规划、解释，不直接替代生信计算**
- **生信计算交给工作流引擎执行**，例如 Nextflow / Snakemake
- **所有分析能力通过能力注册中心统一管理**，而不是写死在 prompt 中
- **关键输出必须具备证据链与可追溯性**
- **高风险结论必须经过 Reviewer 或规则引擎审校**

### 2.2 不建议的做法

- 不建议把所有分析逻辑塞进一个大 prompt
- 不建议让模型自由拼装命令直接跑分析
- 不建议把“所有分析”一次性做满，应分阶段建设

---

## 3. 平台总体架构

平台推荐采用四层主架构：

1. **交互层**
2. **智能决策层（多 Agent 编排）**
3. **工作流执行层**
4. **数据与知识底座**

### 3.1 架构总览

```text
Client/UI/API
  ↓
Gateway/Auth/Audit
  ↓
Agent Orchestrator Layer
  ├── Router
  ├── Task Parser
  ├── Planner Agent
  ├── Analysis Execution Agent
  ├── QA Agent
  ├── Wet-lab Design Agent
  ├── Reviewer Agent
  └── Report Agent
  ↓
Capability Platform / Rule Engine / Knowledge Retrieval
  ↓
Workflow Engine (Nextflow / Snakemake)
  ↓
Data Platform (PostgreSQL + Object Storage + Vector DB + Graph DB optional)
```

### 3.2 推荐模块拆分

```text
genomic-agent-platform
├── gateway-service
├── auth-service
├── project-service
├── file-ingestion-service
├── metadata-service
├── task-service
├── agent-orchestrator-service
├── llm-service
├── knowledge-retrieval-service
├── capability-service
├── workflow-service
├── result-service
├── report-service
├── wetlab-design-service
├── audit-governance-service
├── notification-service
└── reference-asset-service
```

---

## 4. 多 Agent 设计

推荐采用 **总控 Agent + 专业 Agent 群** 的架构，而不是单 Agent。

### 4.1 Orchestrator Agent（总控编排 Agent）

职责：
- 接收用户请求
- 判断意图类型
- 调度其他 Agent
- 管理任务状态
- 管理上下文与结果回传

不负责：
- 不直接执行具体生信分析
- 不负责最终科学结论判定

### 4.2 Task Parser Agent（任务解析 Agent）

职责：
- 从自然语言中提取结构化任务信息
- 抽取实体：物种、数据类型、表型、参考基因组、目标任务、输出需求
- 输出统一 Task JSON

### 4.3 Feasibility Checker Agent（可行性判断 Agent）

职责：
- 检查数据是否足够支持当前分析
- 检查样本量、表型完整性、参考资源是否齐全
- 对自动执行给出可行/警告/不可行判断

### 4.4 Planner Agent（分析规划 Agent）

职责：
- 根据任务目标选择分析配方（Recipe）
- 生成执行 DAG
- 选择依赖能力单元
- 估算资源需求

### 4.5 Analysis Execution Agent（分析执行 Agent）

职责：
- 把执行计划翻译为具体 workflow 参数
- 调用 workflow-service 提交任务
- 跟踪状态、日志和产物

### 4.6 QA Agent（知识问答/方案设计 Agent）

职责：
- 回答基因组学/生信方法问题
- 结合用户场景推荐分析策略
- 调用知识库和文献检索服务

### 4.7 Wet-lab Design Agent（湿实验设计 Agent）

职责：
- 基于候选基因/变异/通路/表达结果设计验证方案
- 给出 qPCR、KASP、Sanger、双荧光素酶、过表达/敲低等设计建议

### 4.8 Reviewer Agent（审校 Agent）

职责：
- 检查分析链路是否合规
- 检查结论是否与证据一致
- 检查湿实验方案是否与 dry-lab 结论一致
- 输出置信度与审校说明

### 4.9 Report Agent（报告 Agent）

职责：
- 生成摘要报告、技术报告、湿实验方案书
- 组织图表、表格、方法说明和风险提示

---

## 5. 三类任务的执行链路

## 5.1 自动生信分析

适用场景：
- WGS 重测序 + 表型做 GWAS
- RNA-seq 差异分析
- GWAS + RNA 联合候选基因挖掘

执行链路：

```text
用户输入
→ Orchestrator
→ Task Parser
→ Feasibility Checker
→ Planner Agent
→ Capability Registry + Rule Engine
→ Workflow Compiler
→ Analysis Execution Agent
→ Reviewer Agent
→ Wet-lab Design Agent（可选）
→ Report Agent
```

## 5.2 知识问答 / 方案设计

适用场景：
- 样本量是否适合做 GWAS
- 做 RNA-seq 还是做多组学
- 如何解释显著位点

执行链路：

```text
用户问题
→ Orchestrator
→ QA Agent
→ Knowledge Retrieval Service
→ Rule Engine
→ Reviewer Agent
→ Report/Answer
```

## 5.3 湿实验验证方案设计

适用场景：
- 已有候选基因和显著位点，设计验证方案
- 设计 qPCR/KASP/双荧光素酶/功能验证路线

执行链路：

```text
用户目标或分析结果
→ Orchestrator
→ Wet-lab Design Agent
→ Knowledge Retrieval Service
→ Reviewer Agent
→ Report Agent
```

---

## 6. 核心中台：Capability + Recipe + Rule

这是平台能否扩展的关键。

### 6.1 Capability Registry（能力注册中心）

能力单元示例：
- fastq_qc
- wgs_alignment
- variant_calling
- variant_filtering
- pca_analysis
- kinship_calc
- gwas_standard
- rnaseq_quant
- deg_analysis
- enrichment_analysis
- candidate_gene_rank
- wetlab_qpcr
- wetlab_kasp

每个能力单元需要管理：
- 输入 Schema
- 输出 Schema
- 依赖能力
- 工具链
- 适用物种范围
- 自动执行支持级别
- 审校策略

### 6.2 Recipe Library（分析配方库）

配方是多个能力的组合 DAG。建议 V1 先做：

- `WGS_GWAS_STANDARD_V1`
- `RNASEQ_DEG_STANDARD_V1`
- `GWAS_RNASEQ_INTEGRATION_V1`
- `WETLAB_VALIDATION_BASIC_V1`

### 6.3 Rule Engine（规则引擎）

推荐至少有以下硬规则：

- genome build 不明确时，不允许自动执行
- GWAS 必须执行 PCA 或 kinship 校正
- RNA-seq 无生物学重复时，不做标准 DE 推断，只能输出描述性结果或警告
- 候选基因排序时必须区分：
  - 距离证据
  - 功能证据
  - 表达证据
  - 文献证据
- lead SNP 不可直接表述为 causal SNP

---

## 7. 工作流执行层设计

### 7.1 推荐工作流引擎

优先推荐：
- **Nextflow**：适合容器化、云原生、HPC、模块化复用
- 备选：**Snakemake**：适合研究迭代快的团队

### 7.2 推荐运行环境

- 容器：Docker / Apptainer
- 调度：Kubernetes 或 Slurm
- 存储：MinIO / S3 / OSS

### 7.3 工作流执行原则

- 所有分析必须容器化
- 所有分析必须记录软件版本和参数
- 所有关键文件必须记录 checksum
- 所有结果必须能追溯到输入和步骤

---

## 8. 数据与知识底座

### 8.1 数据层

建议采用以下组合：

- **PostgreSQL**：结构化元数据
- **Object Storage**：原始文件与结果文件
- **Vector DB**：文献/SOP/FAQ 检索
- **Graph DB（可选）**：基因—性状—通路—证据图谱

### 8.2 知识层

建议知识来源包括：

- 公共数据库：NCBI / Ensembl / UniProt / KEGG / GO / AnimalQTLdb / Gramene
- 文献：PubMed 摘要、全文知识片段
- 内部知识：SOP、方法文档、实验模板、项目复盘
- 用户项目私有知识：历史结果、过往分析记录

### 8.3 Reference Asset Manager（参考资源管理器）

必须单独做服务，负责：
- 参考基因组版本管理
- 注释文件管理
- 索引文件管理
- 染色体命名别名映射
- 项目与参考资源绑定

这是跨物种、多版本环境下避免结果错配的关键模块。

---

## 9. 数据模型与 ER 结构

### 9.1 核心实体关系

```text
User
├── Project
│   ├── Sample
│   │   ├── SampleFile
│   │   ├── PhenotypeRecord
│   │   └── Assay
│   ├── Task
│   │   ├── TaskInput
│   │   ├── TaskOutput
│   │   ├── PipelineRun
│   │   │   ├── PipelineStepRun
│   │   │   ├── RunLog
│   │   │   └── ResultArtifact
│   │   ├── QAConversation
│   │   ├── WetLabPlan
│   │   ├── CandidateGene
│   │   ├── CandidateVariant
│   │   ├── EvidenceRecord
│   │   └── Report
│   └── ReferenceAssetBinding
├── PromptTemplate
└── AuditLog
```

### 9.2 最重要的表

推荐优先落地这些表：

- `projects`
- `samples`
- `sample_files`
- `phenotype_records`
- `tasks`
- `task_inputs`
- `task_outputs`
- `pipeline_runs`
- `pipeline_step_runs`
- `result_artifacts`
- `candidate_genes`
- `candidate_variants`
- `evidence_records`
- `wetlab_plans`
- `wetlab_plan_items`
- `reports`
- `capabilities`
- `analysis_recipes`
- `rule_sets`
- `reference_assets`
- `audit_logs`

---

## 10. 统一任务对象（Task JSON）

所有 Agent 和服务间通信建议围绕统一 Task JSON。

示例：

```json
{
  "task_id": "task_001",
  "project_id": "proj_001",
  "intent": "analysis",
  "task_goal": "gwas_candidate_gene_prioritization",
  "species": {
    "scientific_name": "Ovis aries",
    "common_name": "sheep"
  },
  "reference": {
    "genome_build": "ARS-UI_Ramb_v2.0",
    "annotation_version": "ensembl_xx"
  },
  "inputs": [
    {
      "input_type": "fastq_dir",
      "uri": "s3://bucket/wgs_fastq/"
    },
    {
      "input_type": "phenotype_table",
      "uri": "s3://bucket/pheno.csv"
    }
  ],
  "phenotype": {
    "trait_name": "shear_force",
    "trait_type": "quantitative",
    "unit": "N"
  },
  "downstream_requirements": [
    "variant_annotation",
    "candidate_gene_ranking",
    "wetlab_validation_plan"
  ]
}
```

---

## 11. 各 Agent 的最小输入输出协议

建议所有 Agent 都遵循统一 envelope：

```json
{
  "trace_id": "trace_001",
  "task_id": "task_001",
  "project_id": "proj_001",
  "agent_name": "planner_agent",
  "agent_version": "v1",
  "input": {},
  "context": {},
  "constraints": {},
  "output_format": "json"
}
```

### 11.1 Orchestrator Agent 输出重点
- intent
- sub_intents
- routing_plan
- normalized_entry

### 11.2 Task Parser Agent 输出重点
- normalized_task
- missing_fields
- ambiguities
- confidence_score

### 11.3 Feasibility Checker Agent 输出重点
- feasibility.status
- checks[]
- recommendations[]

### 11.4 Planner Agent 输出重点
- recipe_code
- execution_plan.steps[]
- qc_gates[]
- resource_estimate

### 11.5 Analysis Execution Agent 输出重点
- pipeline_run_id
- step bindings
- runtime log uri

### 11.6 QA Agent 输出重点
- short_answer
- detailed_answer
- recommendations[]
- evidence_requests[]

### 11.7 Wet-lab Design Agent 输出重点
- strategy_type
- experiments[]
- risks[]

### 11.8 Reviewer Agent 输出重点
- review_result.status
- overall_confidence
- findings[]
- required_notes_for_report[]

### 11.9 Report Agent 输出重点
- report_type
- title
- content_json

---

## 12. 第一版能力清单（MVP）

### 12.1 建议 V1 覆盖范围

优先覆盖四条高价值链路：

1. WGS/重测序标准分析
2. GWAS 与候选基因优先级
3. RNA-seq 差异分析与功能富集
4. 基础湿实验验证方案设计

### 12.2 能力清单

| 能力域 | 能力名称 | 编码 | 自动执行 | 优先级 |
|---|---|---|---|---|
| 数据预处理 | FASTQ 质控 | fastq_qc | 是 | P0 |
| 比对 | WGS 比对 | wgs_alignment | 是 | P0 |
| 变异检测 | SNP/Indel calling | variant_calling | 是 | P0 |
| 变异检测 | 变异过滤 | variant_filtering | 是 | P0 |
| 群体分析 | PCA | pca_analysis | 是 | P0 |
| 群体分析 | Kinship 计算 | kinship_calc | 是 | P0 |
| 关联分析 | GWAS | gwas_standard | 是 | P0 |
| 注释 | 变异注释 | variant_annotation | 是 | P0 |
| 基因挖掘 | 候选基因提取 | candidate_gene_extract | 是 | P0 |
| 基因挖掘 | 候选基因排序 | candidate_gene_rank | 是 | P0 |
| 转录组 | RNA-seq 质控 | rnaseq_qc | 是 | P0 |
| 转录组 | RNA-seq 定量 | rnaseq_quant | 是 | P0 |
| 转录组 | 差异表达分析 | deg_analysis | 是 | P0 |
| 功能分析 | GO/KEGG 富集 | enrichment_analysis | 是 | P0 |
| 综合分析 | GWAS + RNA 联合排序 | gwas_rnaseq_integration | 是 | P1 |
| 知识问答 | 方法学咨询 | methodology_qa | 是 | P0 |
| 知识问答 | 结果解读 | result_interpretation | 是 | P0 |
| 湿实验设计 | qPCR 方案设计 | wetlab_qpcr | 是 | P0 |
| 湿实验设计 | KASP 方案设计 | wetlab_kasp | 是 | P0 |
| 湿实验设计 | Sanger 验证方案 | wetlab_sanger | 是 | P1 |
| 湿实验设计 | 双荧光素酶方案 | wetlab_luciferase | 是 | P1 |
| 湿实验设计 | 基础功能验证建议 | wetlab_function_basic | 是 | P1 |

### 12.3 V1 不建议自动执行的能力

以下建议先做“方案咨询模式”，不要直接自动执行：

- 单细胞转录组
- 空间转录组
- 泛基因组
- 全基因组甲基化
- ChIP-seq / ATAC-seq 深度自动化
- CRISPR 精准设计自动执行
- SV 高复杂场景自动解释

---

## 13. 推荐技术选型

### 13.1 后端
- Python + FastAPI
- PostgreSQL
- Redis
- Celery / Arq / Kafka（按团队习惯）

### 13.2 Workflow
- Nextflow（推荐）
- Snakemake（备选）

### 13.3 存储
- MinIO / S3 / OSS

### 13.4 检索
- pgvector / Milvus / Weaviate
- Neo4j（可选）

### 13.5 部署
- Kubernetes + 容器化
- 或 HPC + Slurm

---

## 14. 状态机设计

推荐统一任务状态：

```text
draft
→ parsed
→ ready_for_execution
→ running
→ reviewing
→ completed
```

异常流转：

```text
parsed → need_user_input
running → failed
reviewing → need_manual_review
failed → retrying → running
```

---

## 15. 错误协议建议

所有 Agent 建议统一返回：

```json
{
  "error": {
    "code": "MISSING_REQUIRED_FIELD",
    "message": "genome_build is required for this task",
    "recoverable": true,
    "suggested_action": "request genome build or infer from project settings"
  }
}
```

推荐错误码：
- `MISSING_REQUIRED_FIELD`
- `UNSUPPORTED_TASK_TYPE`
- `INSUFFICIENT_DATA`
- `REFERENCE_ASSET_NOT_FOUND`
- `WORKFLOW_SUBMISSION_FAILED`
- `RULE_VALIDATION_FAILED`
- `MANUAL_REVIEW_REQUIRED`

---

## 16. MVP 落地顺序建议

### Phase 1：先打通最强闭环
建议先做：

**WGS/重测序 + 表型 → GWAS → 候选基因 → 基础湿实验验证方案**

原因：
- 价值高
- 结构清晰
- 容易体现平台的差异化

### Phase 2：增加 RNA-seq 与联合分析
建议补：
- RNA-seq 差异分析
- GO/KEGG 富集
- GWAS + RNA 联合候选基因排序

### Phase 3：增加高级组学与复杂功能
如：
- 甲基化
- 单细胞
- 空间组学
- 泛基因组

---

## 17. 工程实现建议

### 17.1 先做“平台骨架”，不要先堆分析功能
先完成：
- 任务模型
- Agent 编排框架
- 能力注册中心
- Recipe 机制
- Rule Engine
- Workflow 接口
- 结果追溯

### 17.2 先做强 Schema，再做 prompt
核心对象必须先固定：
- Task JSON
- Capability JSON
- Execution Plan JSON
- WetLab Plan JSON
- Report JSON

### 17.3 先做“半自动”再做“全自动”
建议支持两种模式：
- **Copilot 模式**：只给分析方案和解释
- **Autopilot 模式**：自动跑标准流程

---

## 18. 工程同事的直接任务清单

建议按以下优先级分工：

### A. 平台/后端同学
- 建 `projects / tasks / pipeline_runs / result_artifacts` 等核心表
- 建 workflow-service
- 建 object storage 接入
- 建日志与审计机制

### B. Agent / LLM 同学
- 搭建 Orchestrator
- 搭建 Task Parser / Planner / QA / Wet-lab / Reviewer / Report Agent
- 固化统一 JSON 协议
- 建 tool-calling 框架

### C. 生信工程同学
- 抽象 V1 能力单元
- 建 WGS_GWAS_STANDARD_V1 配方
- 建 RNASEQ_DEG_STANDARD_V1 配方
- 输出标准输入/输出文件规范

### D. 知识工程同学
- 建 SOP 知识库
- 建文献检索索引
- 建公共数据库接入层
- 组织实验模板

---

## 19. 最终结论

本平台不应被实现为“单个聊天模型 + 若干脚本”，而应被实现为：

> **多 Agent 编排系统 + 能力注册中心 + 工作流执行引擎 + 知识/规则中台 + 结果审校与追溯层**

用一句话概括工程落地路线：

> **先固化任务模型和执行框架，再接入标准分析配方，最后扩展知识问答和湿实验设计能力。**

---

## 20. 推荐下一步输出文档

建议工程同事继续补 3 份文档：

1. `recipe_library_v1.md`  
   展开每个分析配方的 DAG、输入输出、工具链和 QC Gate

2. `rule_engine_v1.md`  
   固化自动执行规则、审校规则、风险提示规则

3. `agent_prompt_tool_spec_v1.md`  
   固化每个 Agent 的 prompt、工具权限、输入输出协议与失败回退策略

