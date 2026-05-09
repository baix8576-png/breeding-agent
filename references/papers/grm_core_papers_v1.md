# GRM Core Papers (V1 seed, 10 cards)

## GRM-01 Foundational genomic relationship construction
```yaml
knowledge_item.v2:
  doc_id: "paper_grm_vanraden_2008"
  version: "v2"
  species: "multi_species"
  blueprint_scope: "grm"
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-09T12:20:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: VanRaden PM. *Efficient Methods to Compute Genomic Predictions* (2008), DOI `10.3168/jds.2007-0980`.
- 方法: 给出从标记矩阵构建 G 矩阵并进入 GBLUP 的等价计算路径。
- 适用边界: 适合常见 SNP 芯片育种场景；对低频变异主导性状需额外校正。
- 参数建议: 基因型中心化与缩放方式要固定并审计，确保跨批次可比较。
- 风险: 参考等位基因频率设定不一致会导致 G 矩阵尺度漂移。
- Source links: [JDS archive](https://aipl.arsusda.gov/publish/jds/2008/abs91_4414.html), [Google Scholar](https://scholar.google.com/scholar?q=Efficient+Methods+to+Compute+Genomic+Predictions+VanRaden)

## GRM-02 Pedigree + genomic unified relationship matrix
```yaml
knowledge_item.v2:
  doc_id: "paper_grm_legarra_2009"
  version: "v2"
  species: "multi_species"
  blueprint_scope: "grm"
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-09T12:20:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Legarra A et al. *A relationship matrix including full pedigree and genomic information* (2009), DOI `10.3168/jds.2009-2061`.
- 方法: 提出将 A 与 G 融合到 H 矩阵的关键思路，支持单步评估框架。
- 适用边界: 适合仅部分样本有基因型的育种体系。
- 参数建议: 明确 A22 与 G 的对齐与缩放策略，保证矩阵兼容。
- 风险: 未调谐的 A/G 融合会产生系统偏差和不稳定 EBV。
- Source links: [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S0022030209707933), [Google Scholar](https://scholar.google.com/scholar?q=A+relationship+matrix+including+full+pedigree+and+genomic+information)

## GRM-03 Single-step computing procedures
```yaml
knowledge_item.v2:
  doc_id: "paper_grm_misztal_2009"
  version: "v2"
  species: "multi_species"
  blueprint_scope: "grm"
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-09T12:20:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Misztal I et al. *Computing procedures for genetic evaluation including phenotypic, full pedigree, and genomic information* (2009), DOI `10.3168/jds.2009-2064`, PMID `19700728`.
- 方法: 将表型、系谱与基因组信息在统一方程中联合求解。
- 适用边界: 适合产业级遗传评估主线；需较规范的谱系与表型系统。
- 参数建议: 统一定义基准群体与信息权重，再做大规模求解。
- 风险: 数据链路不一致时，单步模型可能掩盖上游数据缺陷。
- Source links: [PubMed](https://pubmed.ncbi.nlm.nih.gov/19700728/), [Google Scholar](https://scholar.google.com/scholar?q=Computing+procedures+for+genetic+evaluation+including+phenotypic+full+pedigree+and+genomic+information)

## GRM-04 Alternative G-matrix formulations
```yaml
knowledge_item.v2:
  doc_id: "paper_grm_forni_2011"
  version: "v2"
  species: "multi_species"
  blueprint_scope: "grm"
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-09T12:20:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Forni S et al. *Different genomic relationship matrices for single-step analysis using phenotypic, pedigree and genomic information* (2011), DOI `10.1186/1297-9686-43-1`.
- 方法: 比较不同 G 构造与调谐方式对单步评估结果的影响。
- 适用边界: 适合猪/牛等有产业化评估体系的群体。
- 参数建议: 在上线前做多种 G 定义的对照回归测试。
- 风险: 未做跨版本比较直接替换 G 定义，易引发历史结果不可比。
- Source links: [Genetics Selection Evolution](https://gsejournal.biomedcentral.com/articles/10.1186/1297-9686-43-1), [Google Scholar](https://scholar.google.com/scholar?q=Different+genomic+relationship+matrices+for+single-step+analysis+using+phenotypic+pedigree+and+genomic+information)

## GRM-05 Efficient inverse and matrix assembly
```yaml
knowledge_item.v2:
  doc_id: "paper_grm_aguilar_2011"
  version: "v2"
  species: "multi_species"
  blueprint_scope: "grm"
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-09T12:20:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Aguilar I et al. *Efficient computation of the genomic relationship matrix and other matrices used in single-step evaluation* (2011), DOI `10.1111/j.1439-0388.2010.00912.x`.
- 方法: 讨论单步评估中 G 与相关矩阵及其逆的高效计算策略。
- 适用边界: 适合中大规模群体单步评估实现优化。
- 参数建议: 把矩阵构建与逆运算拆分为可审计模块，便于性能与正确性回归。
- 风险: 数值稳定性处理不足会导致求解失败或隐性偏差。
- Source links: [ResearchGate metadata](https://www.researchgate.net/publication/51780070_Efficient_computation_of_the_genomic_relationship_matrix_and_other_matrices_used_in_single-step_evaluation), [Google Scholar](https://scholar.google.com/scholar?q=Efficient+computation+of+the+genomic+relationship+matrix+and+other+matrices+used+in+single-step+evaluation)

## GRM-06 Shrinkage realized relationship matrix
```yaml
knowledge_item.v2:
  doc_id: "paper_grm_endelman_2012"
  version: "v2"
  species: "multi_species"
  blueprint_scope: "grm"
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-09T12:20:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Endelman JB, Jannink JL. *Shrinkage Estimation of the Realized Relationship Matrix* (2012), DOI `10.1534/g3.112.004259`.
- 方法: 通过收缩估计提高关系矩阵稳定性，尤其在样本/标记比例不理想时。
- 适用边界: 适合植物与动物育种中样本有限、标记高维场景。
- 参数建议: 将 shrinkage 强度调参纳入交叉验证流程。
- 风险: 收缩过强会抹平真实群体差异，降低预测分辨率。
- Source links: [G3/Oxford](https://academic.oup.com/g3journal/article/2/11/1405/6026008), [Google Scholar](https://scholar.google.com/scholar?q=Shrinkage+Estimation+of+the+Realized+Relationship+Matrix)

## GRM-07 GREML heritability from genomic relationships
```yaml
knowledge_item.v2:
  doc_id: "paper_grm_yang_2010"
  version: "v2"
  species: "multi_species"
  blueprint_scope: "grm"
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-09T12:20:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Yang J et al. *Common SNPs explain a large proportion of heritability for human height* (2010), DOI `10.1038/ng.608`.
- 方法: 以个体间基因组相似度估计总体遗传方差贡献（GREML 核心思路）。
- 适用边界: 适合群体层面方差分解；不等价于单个位点因果解释。
- 参数建议: 严格执行 unrelated 样本筛选与分层协变量控制。
- 风险: 亲缘残留与批次效应会抬高方差解释比例。
- Source links: [Nature Genetics](https://www.nature.com/articles/ng.608), [Google Scholar](https://scholar.google.com/scholar?q=Common+SNPs+explain+a+large+proportion+of+heritability+for+human+height)

## GRM-08 GCTA software core
```yaml
knowledge_item.v2:
  doc_id: "paper_grm_gcta_2011"
  version: "v2"
  species: "multi_species"
  blueprint_scope: "grm"
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-09T12:20:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Yang J et al. *GCTA: A Tool for Genome-wide Complex Trait Analysis* (2011), DOI `10.1016/j.ajhg.2010.11.011`, PMID `21167468`.
- 方法: 提供 GRM 构建、方差分解与相关复杂性状分析的一体化工具。
- 适用边界: 适合复杂性状总体遗传结构分析；需要高质量输入与协变量建模。
- 参数建议: 固化 `--make-grm`、`--reml`、协变量输入模板与日志审计规范。
- 风险: 忽视样本结构与环境混杂会误导 h2 解释。
- Source links: [PubMed](https://pubmed.ncbi.nlm.nih.gov/21167468/), [Google Scholar](https://scholar.google.com/scholar?q=GCTA+A+Tool+for+Genome-wide+Complex+Trait+Analysis)

## GRM-09 Genome partitioning by common SNPs
```yaml
knowledge_item.v2:
  doc_id: "paper_grm_yang_2011_partition"
  version: "v2"
  species: "multi_species"
  blueprint_scope: "grm"
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-09T12:20:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Yang J et al. *Genome partitioning of genetic variation for complex traits using common SNPs* (2011), DOI `10.1038/ng.823`.
- 方法: 按染色体或注释分层分解遗传方差，连接 GRM 与生物学层次解释。
- 适用边界: 适合复杂性状结构化方差分析；不直接给出精细因果位点。
- 参数建议: 先统一 QC 与协变量策略，再进行分区方差比较。
- 风险: 分区策略过多会带来多重比较与解释膨胀。
- Source links: [Nature Genetics](https://www.nature.com/articles/ng.823), [Google Scholar](https://scholar.google.com/scholar?q=Genome+partitioning+of+genetic+variation+for+complex+traits+using+common+SNPs)

## GRM-10 Reliability approximation in ssGBLUP
```yaml
knowledge_item.v2:
  doc_id: "paper_grm_misztal_2013_reliability"
  version: "v2"
  species: "multi_species"
  blueprint_scope: "grm"
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-09T12:20:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Misztal I et al. *Methods to approximate reliabilities in single-step genomic evaluation* (2013), DOI `10.3168/jds.2012-5656`, PMID `23127903`.
- 方法: 在难以直接矩阵求逆时，给出 ssGBLUP 可靠度近似策略。
- 适用边界: 适合超大规模评估系统中的工程化上线。
- 参数建议: 近似可靠度必须与抽样精确解做周期性校准。
- 风险: 近似误差在数据分布变化后可能快速累积。
- Source links: [PubMed](https://pubmed.ncbi.nlm.nih.gov/23127903/), [Google Scholar](https://scholar.google.com/scholar?q=Methods+to+approximate+reliabilities+in+single-step+genomic+evaluation)
