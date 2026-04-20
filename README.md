# GeneAgent

GeneAgent 是面向动物遗传育种与群体基因组分析场景的 Agent 工程项目。当前文档以 **V1.5 行为真相源** 为准。

## Windows PowerShell 标准启动命令
在 `D:\geneagent` 打开 PowerShell 后，按顺序执行：

```powershell
cd D:\geneagent
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e ".[dev]"
python -m compileall src tests
python -m pytest -q
```

常用开发命令：

```powershell
python -m cli.app doctor
python -m cli.app plan "Run PCA on a sheep VCF dataset" --working-directory D:\geneagent
python -m cli.app dry-run --working-directory D:\geneagent --request-text "Prepare a dry-run for PCA on sheep VCF"
python -m cli.app submit-preview --working-directory D:\geneagent --dry-run-completed
python -m cli.app submit --working-directory D:\geneagent --dry-run-completed
python -m cli.app poll-explain SLURM-12345
python -m cli.app report --working-directory D:\geneagent --request-text "Generate report index for latest run"
python -m cli.app diagnostic --working-directory D:\geneagent --request-text "Diagnose scheduler/tool failures"
python -m api.app
```

## V1.5 当前定位
- 顶层分流：`bioinformatics / system / knowledge`
- 生信主链蓝图：`qc / pca / grm / genomic_prediction`
- 主链能力：`plan -> dry-run -> submit -> poll -> artifact/report -> audit/memory`
- 非生信支路：`intake -> local retrieval -> answer blueprint`（不进集群）

## V1.5 标准执行链（生信主链）
1. `Intake`：自然语言请求标准化，产出 `task_id / run_id / session_id`
2. `Intent + Scope`：识别 `bioinformatics / system / knowledge`
3. `Input Validation`：原始路径归一化为 `InputBundle`，校验 VCF/PLINK/BAM/表型/协变量/谱系一致性
4. `Local-first RAG`：优先检索 `references/*`、本地 SOP、模板和历史规范
5. `Blueprint Selection`：严格绑定 `qc / pca / grm / genomic_prediction`，输出阶段清单与产物契约
6. `Resource + Safety Gate`：资源估算、dry-run 预览、人工确认项、熔断条件
7. `Execution`：生成 Bash wrapper + scheduler script，执行提交、轮询与失败恢复
8. `Artifact + Report`：收集结果/图表/日志，生成报告索引与解释摘要
9. `Audit + Memory`：落盘输入摘要、规划摘要、提交命令、job id、日志路径、人工确认记录

## 非生信轻量支路（硬约束）
流程：
`intake -> local retrieval -> answer blueprint -> safety review if needed`

约束：
- 不进入集群执行
- 不生成调度脚本
- 不触发 `submit/poll`
- 不分配集群 job id

## 调度与执行语义
- `SLURM` 为主线，`PBS` 为兼容适配
- 语义对齐：`submit / poll / recovery`
- 命令族示例：
  - SLURM：`sbatch / squeue / sacct`
  - PBS：`qsub / qstat`

## Local-first Knowledge 策略
- 本地优先检索，仅在本地命中覆盖不足且通过安全门禁时才允许外部回退
- 外部回退为显式分支，不覆盖本地基准知识，只作为补充证据
- 错误诊断优先使用 `references/*` 与本地知识条目，输出可执行修复建议

## CLI / API 覆盖面（V1.5）
CLI 重点命令：
- `plan`
- `dry-run`
- `submit-preview`
- `submit`
- `poll-explain`
- `report`
- `diagnostic`

API 重点路由：
- `POST /tasks/draft-plan`
- `POST /tasks/dry-run`
- `POST /tasks/submit-preview`
- `POST /tasks/submit`
- `POST /tasks/poll-explain`
- `POST /tasks/report`
- `POST /tasks/diagnostic`

## V1.5 验收标准
- `python -m pytest -q` 全绿
- `python -m compileall src tests` 通过
- 生信请求可走 `dry-run/submit/poll` 闭环
- `qc / pca / grm / genomic_prediction` 均产出结构化计划、脚本与产物索引（含 `report_index`）
- non-bio 请求明确“不进集群”

## 目录与架构
目录宪章、模块边界、角色路由以 `AGENTS.md` 为单一真相源。  
禁止通过平行源码目录进行版本分叉（如 `src_v2/`、`new_src/` 等）。

## 运行环境边界
- 默认开发环境：Windows 10/11 + PowerShell
- 生产执行边界：Linux/HPC 调度节点
- macOS/WSL2：兼容开发路径，不作为默认真相源

## 安全边界
- 原始实体数据（VCF/BAM/FASTQ/FASTA）不得离开本地计算环境
- 允许上云信息仅限：Prompt、脱敏错误摘要、工具输出摘要、软件版本、参数结构
- 高风险动作必须人工确认：覆盖结果、删除文件、跨目录写入、异常资源申请、失败任务重投

## 路线图
- `V1`：已完成基线闭环（分流、四蓝图、主链调度、审计与记忆回写）
- `V1.5`：当前行为真相源（PBS 兼容、report/diagnostic、manifest 体系化、知识检索补强）
- `V2`：后续扩展（插件化工具生态、增强记忆系统、更广泛多组学模板）

## 声明
GeneAgent 是流程编排与研究辅助系统，不替代研究者做最终生物学解释与育种决策。
