# GeneAgent

## Windows PowerShell 快速开始
在 `D:\geneagent` 下打开 PowerShell 后，按下面顺序执行：

```powershell
cd D:\geneagent
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e ".[dev]"
python -m pytest -q
```

常用命令：

```powershell
python -m cli.app doctor
python -m cli.app plan "Run PCA on a sheep VCF dataset" --working-directory D:\geneagent
python -m cli.app dry-run --working-directory D:\geneagent --request-text "Prepare a dry-run for PCA on sheep VCF"
python -m api.app
```

说明：
- 仓库根目录的 `.venv\Scripts\python.exe` 是当前默认开发解释器。
- 这套流程面向 Windows PowerShell，不依赖 WSL2。
- 如果 PowerShell 提示脚本执行被禁止，先执行 `Set-ExecutionPolicy -Scope Process Bypass`，只对当前窗口生效。

## 项目定位
GeneAgent 是面向动植物遗传育种研究者的本地智能助手，支持用户通过自然语言完成群体遗传学与数量遗传学分析编排，并在本地 Linux 集群上自动生成 Bash 脚本、提交 SLURM 任务、轮询作业状态、整理结果与报错信息。

## 核心目标
- 用自然语言驱动群体遗传学与数量遗传学分析流程
- 在本地 Linux 集群执行真实计算任务
- 将 VCF/BAM/FASTQ/FASTA 等实体数据留在本地服务器
- 仅将 Prompt、脱敏报错日志、工具摘要、软件版本、参数结构发送给云端大模型
- 通过模块化架构支持后续新增工具、新增分析流程和新增调度器适配器

## 非目标
- 不替代研究者做最终科学结论判断
- 不自动上传任何原始组学数据或完整文件内容
- 不在未经确认的情况下执行破坏性命令
- 不自动开发全新算法
- 不在首版中支持未经验证的复杂多组学联合建模

## v1 支持范围
- 输入文件合规检查：VCF、BAM 及相关表型文件的格式与一致性检查
- 群体遗传学分析：群体结构、PCA、亲缘关系、LD、ROH、Fst、π、Tajima's D
- 数量遗传学分析：GWAS、遗传力估计、基因组选择、育种值预测
- 集群任务管理：资源估算、脚本生成、作业提交、作业轮询、结果汇总
- 报错诊断：日志提取、错误摘要、修复建议、熔断保护

## 交互方式
- 首版采用 `CLI first`
- 后续提供极简 Web UI
- UI/CLI 只负责交互，核心逻辑由 Orchestrator 与工具层完成

## 系统架构
- `UI / CLI`：接收自然语言需求，展示计划、确认项与结果
- `LLM Orchestrator`：进行意图识别、任务分类、流程编排与异常决策
- `Intent Router`：区分“需要生信分析”和“不需要生信分析”的问题
- `Validator`：在分析前检查输入文件、参数、路径、物种、样本与表型数据一致性
- `Knowledge & Memory`：负责本地知识检索、长期知识沉淀与会话上下文管理
- `Tool Registry`：统一注册分析工具，按 manifest 调用
- `Scheduler Adapter`：首版支持 SLURM，保留 PBS 适配层
- `Worker / Poller`：提交任务后进入休眠/轮询状态，通过 `squeue` 等命令监控作业
- `Circuit Breaker`：在高风险或高不确定场景下停止自动执行
- `Result Summarizer`：整理图表、结果摘要、产物索引与可追溯元数据

## 工作流程
1. 用户输入自然语言需求
2. Orchestrator 进行意图分析与任务分类
3. 若为生信分析任务，则先进行输入文件与参数合规检查
4. 优先检索本地知识库；若不足，再调用外部 MCP / 数据库检索
5. 结合知识检索结果生成任务计划与资源估算
6. 自动生成 Bash 脚本与调度脚本
7. 对高风险动作进行人工确认
8. 提交集群任务并记录作业 ID
9. Agent 进入休眠/轮询状态，等待作业完成
10. 作业完成后自动进行绘图、结果整理、报错诊断与简明解释输出
11. 若为非生信分析任务，则走知识检索与直接回答流程，不进入集群执行

## 记忆模块设计
- `短期会话记忆`：保存当前对话上下文与最近指令
- `运行记忆`：保存本次任务的输入文件、参数、资源请求、作业 ID、日志路径与中间状态
- `语义记忆`：保存群体遗传学、数量遗传学、育种场景中的概念、经验与常见规则
- `技能记忆`：保存分析工具用法、脚本模板、错误修复模式与最佳实践
- `长期知识库`：保存 SOP、软件文档、历史脚本模板、物种与育种场景知识、前沿文献索引与 FAQ

## 知识检索策略
- 默认优先使用本地知识库
- 本地知识库包括：SOP、软件文档、历史脚本模板、物种知识、育种场景知识、前沿文献索引、FAQ
- 本地知识不足时，再调用外部 MCP / 数据库检索
- 外部检索结果进入本次运行记忆，但不直接覆盖本地基准知识

## 数据安全边界
允许发送到云端模型的信息：
- Prompt
- 脱敏后的报错日志
- 工具返回摘要
- 软件版本
- 参数结构

禁止发送到云端模型的信息：
- VCF / BAM / FASTQ / FASTA 原始数据
- 完整样本名
- 完整文件内容
- 敏感路径映射
- 可直接重建本地实验数据的信息

## 资源管理策略
- 提交前先查询集群可用资源和用户配额
- 根据分析类型估算 CPU、内存、运行时长与分区
- 若用户未指定资源，则采用保守默认值并在提交前展示
- 对异常高资源申请强制人工确认
- 所有工具 manifest 必须声明资源需求与是否支持 dry-run

## 熔断机制
触发条件包括但不限于：
- 连续脚本执行失败
- 调度器拒绝提交
- 资源申请异常
- 输入文件校验失败
- 检测到潜在危险命令
- 日志中出现高风险错误模式
- 连续多轮 LLM 规划结果互相冲突
- 疑似数据外泄请求

状态机定义：
- `Closed`：正常执行
- `Open`：停止自动提交，仅输出诊断建议
- `Half-Open`：人工确认后进行小范围重试
- `Half-Open` 成功后回到 `Closed`，失败则回到 `Open`

## 人工确认策略
以下场景必须人工确认：
- 覆盖已有结果
- 删除文件
- 重新提交失败任务
- 跨目录写入
- 异常高资源申请
- 任何潜在破坏性操作

## 工具扩展机制
系统采用 `tool registry + manifest` 机制。

每个工具必须声明：
- 输入
- 输出
- 前置条件
- 资源需求
- 错误码
- 是否支持 dry-run

该设计保证后续可以插拔式新增分析流程、适配新软件、扩展新物种场景。

## 输出产物
每次任务应至少输出以下内容：
- 生成的 Bash 脚本
- 调度脚本
- 作业 ID
- 日志路径
- 关键结果文件索引
- 图表
- 简明解释报告
- 可追溯元数据

## 审计与追溯
系统需完整记录：
- 输入摘要
- LLM 决策摘要
- 生成脚本
- 提交命令
- 作业 ID
- 错误日志
- 人工确认动作

该审计链用于复现实验流程、定位错误来源与支持责任追踪。

## 运行环境
- 开发主机：Windows 10/11 + PowerShell，默认不再依赖 WSL2
- 本地命令：优先在 Windows PowerShell 中完成 Python、pytest、调度脚本预览与 CLI/API 调试
- 虚拟环境：使用仓库根目录 `.venv\Scripts\Activate.ps1`
- 本地编辑：Windows 原生编辑器 / IDE
- 本地开发目录：推荐直接使用 `D:\geneagent`
- 部署位置：Linux 集群登录节点
- 调度器：首版支持 SLURM，后续扩展 PBS
- 分析软件：预建大型 Conda 环境，内含基础群体遗传学与数量遗传学软件
- 开发栈：Python + FastAPI / Typer + Pydantic + RQ / Celery / Async Worker + SQLite / PostgreSQL + 向量库

## 建议配置项
- `MODEL_PROVIDER`
- `MODEL_NAME`
- `API_KEY`
- `SCHEDULER_TYPE`
- `CONDA_ENV_NAME`
- `WORK_ROOT`
- `LOG_ROOT`
- `KNOWLEDGE_BASE_ROOT`
- `MAX_CPU`
- `MAX_MEM_GB`
- `DRY_RUN_DEFAULT`
- `ALLOW_CLOUD_FIELDS`

## 示例请求
- “请对这个羊群体的 VCF 做 PCA、群体结构分析和 LD 衰减分析，并给出推荐线程和内存。”
- “请检查这个 GWAS 输入文件是否合规，如果合规则生成 SLURM 脚本并提交任务。”
- “请根据当前日志判断 GEMMA 任务失败原因，并给出最可能的修复建议。”
- “请估计这个性状的遗传力，并说明所需表型和基因型输入格式。”
- “请基于现有基因型数据完成基因组选择流程，并输出育种值预测结果。”

## 安全原则
- 本地优先，数据不出域
- 最小权限执行
- 默认保守资源申请
- 默认保留审计记录
- 默认支持 dry-run
- 高风险动作必须人工确认
- 熔断优先级高于任务完成率

## Roadmap
- `v1`：CLI、SLURM、基础知识库、核心分析流程、熔断机制
- `v1.5`：极简 Web UI、PBS 适配、更多工具 manifest、增强报错诊断
- `v2`：更强的记忆系统、自动结果解释、更多育种场景模板、插件化工具生态

## 声明
GeneAgent 是研究辅助与流程编排系统，不替代研究者进行最终生物学解释、育种决策与科研结论确认。
