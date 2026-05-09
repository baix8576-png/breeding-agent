# QC Core Papers (V1 seed, 10 cards)

## QC-01 PLINK baseline toolchain
```yaml
knowledge_item.v2:
  doc_id: "paper_qc_plink_2007"
  version: "v2"
  species: "multi_species"
  blueprint_scope: "qc"
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-09T12:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Purcell S et al. *PLINK: A Tool Set for Whole-Genome Association and Population-Based Linkage Analyses* (2007), DOI `10.1086/519795`, PMID `17701901`.
- 方法: 提供大规模 SNP 数据管理、样本/位点过滤、IBD/IBS、关联分析与群体结构相关基础算子。
- 适用边界: 适合 SNP array 与标准 PLINK 二进制格式；超大 WGS 多等位位点场景建议切换 PLINK2 + BCFtools 联合流程。
- 参数建议: 先做 `--mind/--geno/--maf/--hwe` 级联过滤，再做关系与结构检查，最后进入下游分析。
- 风险: 阈值硬编码会导致跨物种偏差；应结合芯片密度、样本规模与群体历史动态调整。
- Source links: [PubMed](https://pubmed.ncbi.nlm.nih.gov/17701901/), [Google Scholar](https://scholar.google.com/scholar?q=PLINK+A+Tool+Set+for+Whole-Genome+Association+and+Population-Based+Linkage+Analyses)

## QC-02 GWAS case-control QC protocol
```yaml
knowledge_item.v2:
  doc_id: "paper_qc_anderson_2010"
  version: "v2"
  species: "multi_species"
  blueprint_scope: "qc"
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-09T12:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Anderson CA et al. *Data quality control in genetic case-control association studies* (2010), DOI `10.1038/nprot.2010.116`, PMID `21085122`.
- 方法: 给出样本缺失率、杂合度、亲缘关系、群体离群点与位点层面 QC 的标准流程。
- 适用边界: 适合病例-对照 SNP 研究范式；对低深度测序或高度结构化群体需补充专门策略。
- 参数建议: 缺失率与杂合度阈值以分布驱动，不建议仅依赖固定经验值。
- 风险: 过严阈值会损失有效样本，过松阈值会放大假阳性；建议保留阈值变更审计记录。
- Source links: [PubMed](https://pubmed.ncbi.nlm.nih.gov/21085122/), [Google Scholar](https://scholar.google.com/scholar?q=Data+quality+control+in+genetic+case-control+association+studies)

## QC-03 PLINK second-generation
```yaml
knowledge_item.v2:
  doc_id: "paper_qc_plink2_2015"
  version: "v2"
  species: "multi_species"
  blueprint_scope: "qc"
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-09T12:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Chang CC et al. *Second-generation PLINK: rising to the challenge of larger and richer datasets* (2015), DOI `10.1186/s13742-015-0047-8`, PMID `25722852`.
- 方法: 在 PLINK1 基础上大幅提升性能与格式兼容性，支持更大样本与更复杂变异表达。
- 适用边界: 适合高通量基因分型与大规模样本 QC；复杂变异注释仍需与其他工具协作。
- 参数建议: 将高频迭代步骤迁移到 PLINK1.9/2.0（例如大规模 HWE、LD、样本距离计算）。
- 风险: 版本行为差异可能导致结果不一致；需锁定版本并在审计中记录二进制与参数。
- Source links: [PubMed](https://pubmed.ncbi.nlm.nih.gov/25722852/), [Google Scholar](https://scholar.google.com/scholar?q=Second-generation+PLINK+rising+to+the+challenge+of+larger+and+richer+datasets)

## QC-04 KING robust kinship inference
```yaml
knowledge_item.v2:
  doc_id: "paper_qc_king_2010"
  version: "v2"
  species: "multi_species"
  blueprint_scope: "qc"
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-09T12:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Manichaikul A et al. *Robust relationship inference in genome-wide association studies* (2010), DOI `10.1093/bioinformatics/btq559`, PMID `20926424`.
- 方法: 在存在群体分层时稳定估计亲缘关系，提升样本关系识别鲁棒性。
- 适用边界: 适合大规模 SNP 数据中的近亲与隐性亲缘识别；极端缺失或低质数据需先清洗。
- 参数建议: 在 PCA/结构分析前完成 kinship 筛查并输出可追溯的剔除名单。
- 风险: 若未先做基础位点 QC，kinship 估计会受噪声放大，导致错误剔除。
- Source links: [PubMed](https://pubmed.ncbi.nlm.nih.gov/20926424/), [Google Scholar](https://scholar.google.com/scholar?q=Robust+relationship+inference+in+genome-wide+association+studies)

## QC-05 VCF standard and VCFtools
```yaml
knowledge_item.v2:
  doc_id: "paper_qc_vcftools_2011"
  version: "v2"
  species: "multi_species"
  blueprint_scope: "qc"
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-09T12:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Danecek P et al. *The variant call format and VCFtools* (2011), DOI `10.1093/bioinformatics/btr330`, PMID `21653522`.
- 方法: 建立 VCF 表达规范并提供基础过滤、比较、合并与统计工具集。
- 适用边界: 适合 SNP/小 indel 通用流程；复杂 SV 与高阶注释需结合专业工具。
- 参数建议: 强制压缩索引（bgzip/tabix）与 header 校验，避免下游随机失败。
- 风险: header 不一致、坐标/等位基因定义不统一会导致批次合并偏差。
- Source links: [PubMed](https://pubmed.ncbi.nlm.nih.gov/21653522/), [Google Scholar](https://scholar.google.com/scholar?q=The+variant+call+format+and+VCFtools)

## QC-06 GATK MapReduce framework
```yaml
knowledge_item.v2:
  doc_id: "paper_qc_gatk_2010"
  version: "v2"
  species: "multi_species"
  blueprint_scope: "qc"
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-09T12:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: McKenna A et al. *The Genome Analysis Toolkit* (2010), DOI `10.1101/gr.107524.110`, PMID `20644199`.
- 方法: 通过统一遍历框架组织 NGS 变异发现链路，提升可扩展性与并行能力。
- 适用边界: 适合标准短读长变异检测管线；新平台数据应先验证误差模型适配。
- 参数建议: 对齐后先做重复标记与局部重比对（按版本策略），再进入变异调用。
- 风险: 跳过关键预处理会显著增加假阳性与批次偏差。
- Source links: [PubMed](https://pubmed.ncbi.nlm.nih.gov/20644199/), [Google Scholar](https://scholar.google.com/scholar?q=The+Genome+Analysis+Toolkit+a+MapReduce+framework+for+analyzing+next-generation+DNA+sequencing+data)

## QC-07 Unified variation discovery framework
```yaml
knowledge_item.v2:
  doc_id: "paper_qc_depristo_2011"
  version: "v2"
  species: "multi_species"
  blueprint_scope: "qc"
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-09T12:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: DePristo MA et al. *A framework for variation discovery and genotyping using next-generation DNA sequencing data* (2011), DOI `10.1038/ng.806`, PMID `21478889`.
- 方法: 强调从原始 reads 到高质量变异的分层质量控制与机器误差剔除。
- 适用边界: 适合多样本联合调用策略；在极端低深度样本中需结合不确定性建模。
- 参数建议: 将质量重校准与变异过滤模型纳入标准主链，不作为可选步骤。
- 风险: 忽略平台偏差和批次效应会放大伪变异。
- Source links: [PubMed](https://pubmed.ncbi.nlm.nih.gov/21478889/), [Google Scholar](https://scholar.google.com/scholar?q=A+framework+for+variation+discovery+and+genotyping+using+next-generation+DNA+sequencing+data)

## QC-08 Sequencing-data uncertainty model
```yaml
knowledge_item.v2:
  doc_id: "paper_qc_li_2011"
  version: "v2"
  species: "multi_species"
  blueprint_scope: "qc"
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-09T12:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Li H. *A statistical framework for SNP calling, mutation discovery, association mapping and population genetical parameter estimation from sequencing data* (2011), DOI `10.1093/bioinformatics/btr509`.
- 方法: 在不确定读段背景下进行变异与群体参数推断，减少“硬调用”损失。
- 适用边界: 适合低中深度数据和概率型调用场景；需依赖高质量比对基础。
- 参数建议: 对 rare variant 任务保留似然信息，避免过早二值化。
- 风险: 比对错误与参考偏置会被统计模型放大，需配套 mapping 质量门禁。
- Source links: [Oxford Academic](https://academic.oup.com/bioinformatics/article/27/21/2987/217423), [Google Scholar](https://scholar.google.com/scholar?q=A+statistical+framework+for+SNP+calling+mutation+discovery+association+mapping+and+population+genetical+parameter+estimation+from+sequencing+data)

## QC-09 Read trimming best-practice
```yaml
knowledge_item.v2:
  doc_id: "paper_qc_trimmomatic_2014"
  version: "v2"
  species: "multi_species"
  blueprint_scope: "qc"
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-09T12:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Bolger AM et al. *Trimmomatic: a flexible trimmer for Illumina sequence data* (2014), DOI `10.1093/bioinformatics/btu170`.
- 方法: 面向 reads 的接头去除与质量剪切，降低下游比对与调用噪声。
- 适用边界: 适合短读长 Illumina 数据；长读长平台需专门预处理工具。
- 参数建议: 优先保留成对 reads 一致性，长度阈值与滑窗阈值按物种与文库质量调参。
- 风险: 过度剪切会引入覆盖偏差，影响等位基因频率估计。
- Source links: [Oxford Academic](https://academic.oup.com/bioinformatics/article/30/15/2114/2390096), [Google Scholar](https://scholar.google.com/scholar?q=Trimmomatic+a+flexible+trimmer+for+Illumina+sequence+data)

## QC-10 Multi-sample QC aggregation
```yaml
knowledge_item.v2:
  doc_id: "paper_qc_multiqc_2016"
  version: "v2"
  species: "multi_species"
  blueprint_scope: "qc"
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-09T12:00:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Ewels P et al. *MultiQC: summarize analysis results for multiple tools and samples in a single report* (2016), DOI `10.1093/bioinformatics/btw354`.
- 方法: 统一聚合多工具 QC 指标，快速发现批次效应和离群样本。
- 适用边界: 适合多样本批处理项目；需保证上游日志路径与命名规范一致。
- 参数建议: 在每次 pipeline 版本更新后强制产出 MultiQC 报告并纳入审计归档。
- 风险: 仅看全局均值会掩盖小群体异常；应同时检查分组维度。
- Source links: [Oxford Academic](https://academic.oup.com/bioinformatics/article/32/19/3047/2196507), [Google Scholar](https://scholar.google.com/scholar?q=MultiQC+summarize+analysis+results+for+multiple+tools+and+samples+in+a+single+report)
