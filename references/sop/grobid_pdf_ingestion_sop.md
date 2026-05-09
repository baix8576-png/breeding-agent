# PDF 文献摄取 SOP（GROBID）

适用范围:
- `references/papers/*` 的核心论文卡片补全（方法细节、参数段落、风险段落）。
- 输入为本地 PDF（不提交到 git），输出为可检索文本与结构化卡片草案。

## 1. 输入与输出约定
- 输入:
  - 本地 PDF 路径（例如 `D:\data\papers\*.pdf` 或 WSL 对应挂载路径）。
- 输出:
  - `references/papers/_extracted/<doc_id>.tei.xml`
  - `references/papers/_extracted/<doc_id>.sections.md`
  - `references/papers/<scope>_core_papers_v1.md` 中对应卡片补全

注意:
- 原始 PDF 不进仓库版本目录。
- 仅落盘提取文本摘要与结构化元数据。

## 2. GROBID 处理流程
1. 启动 GROBID 服务（本地或容器）。
2. 调用 `processFulltextDocument` 获取 TEI XML。
3. 解析 TEI 的 `title/abstract/body/ref-list`。
4. 抽取与卡片相关段落:
   - 方法描述
   - 适用条件或限制
   - 参数/阈值建议
   - 错误来源/偏差风险

## 3. knowledge_item.v2 对齐
每条论文卡片必须保留字段:
- `doc_id`
- `version`
- `species`
- `blueprint_scope`
- `evidence_level`
- `source`
- `updated_at`
- `owner`

建议附加字段:
- `doi`
- `pmid`
- `pdf_extract_tool: grobid`
- `extract_status: parsed|partial|failed`

## 4. 质量门禁
- 最低通过标准:
  - 标题与 DOI 可解析
  - 方法段至少 1 条
  - 风险段至少 1 条
- 失败处理:
  - 解析失败或乱码 -> 记录到 `references/failure_cases/`
  - 仅元数据成功 -> 标记 `extract_status: partial`

## 5. 审计与可追溯
- 每次批量摄取记录:
  - 输入 PDF 数量
  - 成功/失败数量
  - 失败原因分类（OCR 失败、编码异常、版面破碎等）
  - 卡片更新列表（`doc_id`）

## 6. 与当前项目阶段的关系
- 本 SOP 服务于 M2-03 的“知识摄取上线”。
- 先完成首批高引用核心文献卡片，再做 TEI 级自动化补全。
