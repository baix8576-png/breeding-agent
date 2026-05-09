# Genomic Prediction Core Papers (V1 seed, 10 cards)

## GP-01 Origin paper of genomic selection
```yaml
knowledge_item.v2:
  doc_id: "paper_gp_meuwissen_2001"
  version: "v2"
  species: "multi_species"
  blueprint_scope: "genomic_prediction"
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-09T12:30:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Meuwissen TH et al. *Prediction of total genetic value using genome-wide dense marker maps* (2001), DOI `10.1093/genetics/157.4.1819`, PMID `11290733`.
- 方法: 奠定“全基因组标记联合建模预测育种值”的核心范式。
- 适用边界: 适合多基因控制性状；小样本高维场景需强正则化。
- 参数建议: 训练集规模、标记密度与有效群体大小联合设计。
- 风险: 训练-应用群体漂移会导致代际预测衰减。
- Source links: [PubMed](https://pubmed.ncbi.nlm.nih.gov/11290733/), [Google Scholar](https://scholar.google.com/scholar?q=Prediction+of+total+genetic+value+using+genome-wide+dense+marker+maps)

## GP-02 GBLUP computational equivalence
```yaml
knowledge_item.v2:
  doc_id: "paper_gp_vanraden_2008"
  version: "v2"
  species: "multi_species"
  blueprint_scope: "genomic_prediction"
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-09T12:30:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: VanRaden PM. *Efficient Methods to Compute Genomic Predictions* (2008), DOI `10.3168/jds.2007-0980`.
- 方法: 展示 marker-effects、GBLUP、混合模型求解路径的等价与工程化实现。
- 适用边界: 适合产业场景快速迭代预测；需与数据治理流程绑定。
- 参数建议: 标准化基因型矩阵并固定基准等位频率来源。
- 风险: 版本差异与缩放策略变化会造成历史预测不可比。
- Source links: [JDS archive](https://aipl.arsusda.gov/publish/jds/2008/abs91_4414.html), [Google Scholar](https://scholar.google.com/scholar?q=Efficient+Methods+to+Compute+Genomic+Predictions+VanRaden)

## GP-03 Relationship-driven accuracy decomposition
```yaml
knowledge_item.v2:
  doc_id: "paper_gp_habier_2007"
  version: "v2"
  species: "multi_species"
  blueprint_scope: "genomic_prediction"
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-09T12:30:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Habier D et al. *The Impact of Genetic Relationship Information on Genome-Assisted Breeding Values* (2007), DOI `10.1534/genetics.107.081190`, PMID `18073436`.
- 方法: 分解预测准确度中“关系信息”与“LD 信息”的贡献。
- 适用边界: 适合评估跨代迁移与跨群体泛化风险。
- 参数建议: 报告中单独给出跨代准确度衰减曲线。
- 风险: 若训练与验证样本关系泄露，会高估模型效果。
- Source links: [PubMed](https://pubmed.ncbi.nlm.nih.gov/18073436/), [Google Scholar](https://scholar.google.com/scholar?q=The+Impact+of+Genetic+Relationship+Information+on+Genome-Assisted+Breeding+Values)

## GP-04 Bayesian and shrinkage regression for dense markers
```yaml
knowledge_item.v2:
  doc_id: "paper_gp_deloscampos_2009"
  version: "v2"
  species: "multi_species"
  blueprint_scope: "genomic_prediction"
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-09T12:30:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: de los Campos G et al. *Predicting quantitative traits with regression models for dense molecular markers and pedigree* (2009), DOI `10.1534/genetics.109.101501`, PMID `19293140`.
- 方法: 系统比较高维回归与贝叶斯稀疏收缩在基因组预测中的表现。
- 适用边界: 适合中高维标记预测；计算成本较高时需模型裁剪。
- 参数建议: 使用交叉验证同时调优先验与收缩强度。
- 风险: 超参数固定不变会导致跨性状迁移失败。
- Source links: [PubMed](https://pubmed.ncbi.nlm.nih.gov/19293140/), [Google Scholar](https://scholar.google.com/scholar?q=Predicting+quantitative+traits+with+regression+models+for+dense+molecular+markers+and+pedigree)

## GP-05 Dairy genomic selection implementation review
```yaml
knowledge_item.v2:
  doc_id: "paper_gp_hayes_2009"
  version: "v2"
  species: "bos_taurus"
  blueprint_scope: "genomic_prediction"
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-09T12:30:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Hayes BJ et al. *Invited review: Genomic selection in dairy cattle: progress and challenges* (2009), DOI `10.3168/jds.2008-1646`, PMID `19164653`.
- 方法: 总结奶牛 GS 产业化落地中的参考群体、可靠度与更新机制。
- 适用边界: 以奶牛为主，但对其他家畜参考群体设计有普适启发。
- 参数建议: 建立滚动更新参考群体，控制代际漂移。
- 风险: 不更新参考群体将显著降低长期预测稳定性。
- Source links: [PubMed](https://pubmed.ncbi.nlm.nih.gov/19164653/), [Google Scholar](https://scholar.google.com/scholar?q=Genomic+selection+in+dairy+cattle+progress+and+challenges)

## GP-06 Across-population reliability
```yaml
knowledge_item.v2:
  doc_id: "paper_gp_deroos_2009"
  version: "v2"
  species: "multi_species"
  blueprint_scope: "genomic_prediction"
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-09T12:30:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: de Roos APW et al. *Reliability of Genomic Predictions Across Multiple Populations* (2009), DOI `10.1534/genetics.109.104935`, PMID `19822733`.
- 方法: 评估跨群体预测可靠度与 LD phase 持续性的关系。
- 适用边界: 适合跨品种/跨群体应用前的可行性评估。
- 参数建议: 上线前先做目标群体验证，不直接复用外部模型。
- 风险: 群体分化高时，训练群体外推准确率急剧下降。
- Source links: [PubMed](https://pubmed.ncbi.nlm.nih.gov/19822733/), [Google Scholar](https://scholar.google.com/scholar?q=Reliability+of+Genomic+Predictions+Across+Multiple+Populations)

## GP-07 rrBLUP and kernel framework
```yaml
knowledge_item.v2:
  doc_id: "paper_gp_endelman_2011"
  version: "v2"
  species: "multi_species"
  blueprint_scope: "genomic_prediction"
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-09T12:30:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Endelman JB. *Ridge Regression and Other Kernels for Genomic Selection with R Package rrBLUP* (2011), DOI `10.3835/plantgenome2011.08.0024`.
- 方法: 从 RR-BLUP 扩展到核方法，支持非线性关系建模。
- 适用边界: 适合中等规模模型实验与教学/原型验证。
- 参数建议: 默认先用加性模型作为基线，再评估核方法增益。
- 风险: 盲目使用复杂核会提高过拟合风险与解释难度。
- Source links: [ResearchGate metadata](https://www.researchgate.net/publication/265380226_Ridge_Regression_and_Other_Kernels_for_Genomic_Selection_with_R_Package_rrBLUP), [Google Scholar](https://scholar.google.com/scholar?q=Ridge+Regression+and+Other+Kernels+for+Genomic+Selection+with+R+Package+rrBLUP)

## GP-08 Bayesian Alphabet extension
```yaml
knowledge_item.v2:
  doc_id: "paper_gp_habier_2011_bayes"
  version: "v2"
  species: "bos_taurus"
  blueprint_scope: "genomic_prediction"
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-09T12:30:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Habier D et al. *Extension of the bayesian alphabet for genomic selection* (2011), DOI `10.1186/1471-2105-12-186`, PMID `21605355`.
- 方法: 引入 BayesCπ/BayesDπ 等策略，改进稀疏效应建模与先验敏感性。
- 适用边界: 适合潜在稀疏架构性状；算力较弱场景需控制迭代成本。
- 参数建议: 把 π 和先验超参数纳入系统调参，不用固定经验常量。
- 风险: MCMC 收敛与链混合不足会造成不稳定预测。
- Source links: [PubMed](https://pubmed.ncbi.nlm.nih.gov/21605355/), [Google Scholar](https://scholar.google.com/scholar?q=Extension+of+the+bayesian+alphabet+for+genomic+selection)

## GP-09 GRM-based prediction reliability theory
```yaml
knowledge_item.v2:
  doc_id: "paper_gp_goddard_2011"
  version: "v2"
  species: "multi_species"
  blueprint_scope: "genomic_prediction"
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-09T12:30:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Goddard ME et al. *Using the genomic relationship matrix to predict the accuracy of genomic selection* (2011), DOI `10.1111/j.1439-0388.2011.00964.x`.
- 方法: 用关系矩阵理论估计预测准确度，为实验设计与样本量规划提供依据。
- 适用边界: 适合上线前性能预估与方案比较。
- 参数建议: 将 Ne、训练集规模、标记密度联动纳入准确率预估。
- 风险: 仅用理论估计替代真实验证会导致上线性能偏差。
- Source links: [Journal metadata](https://www.ovid.com/journals/jabg/pdf/10.1111/j.1439-0388.2011.00964.x~using-the-genomic-relationship-matrix-to-predict-the), [Google Scholar](https://scholar.google.com/scholar?q=Using+the+genomic+relationship+matrix+to+predict+the+accuracy+of+genomic+selection)

## GP-10 Exact single-step when G is singular
```yaml
knowledge_item.v2:
  doc_id: "paper_gp_fernando_2016"
  version: "v2"
  species: "multi_species"
  blueprint_scope: "genomic_prediction"
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-09T12:30:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Fernando RL et al. *An efficient exact method to obtain GBLUP and single-step GBLUP when the genomic relationship matrix is singular* (2016), DOI `10.1186/s12711-016-0260-7`, PMID `27788669`.
- 方法: 处理 G 矩阵奇异问题，保证 GBLUP/ssGBLUP 在高维或重复基因型情形下可解。
- 适用边界: 适合大规模高共线标记数据的生产评估环境。
- 参数建议: 在模型装配阶段增加 G 奇异性检查和自动回退策略。
- 风险: 忽视矩阵条件数会导致求解异常或数值不稳定。
- Source links: [PubMed](https://pubmed.ncbi.nlm.nih.gov/27788669/), [Google Scholar](https://scholar.google.com/scholar?q=An+efficient+exact+method+to+obtain+GBLUP+and+single-step+GBLUP+when+the+genomic+relationship+matrix+is+singular)
