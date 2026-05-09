# PCA Core Papers (V1 seed, 10 cards)

## PCA-01 PCA correction for stratification
```yaml
knowledge_item.v2:
  doc_id: "paper_pca_price_2006"
  version: "v2"
  species: "multi_species"
  blueprint_scope: "pca"
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-09T12:10:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Price AL et al. *Principal components analysis corrects for stratification in genome-wide association studies* (2006), DOI `10.1038/ng1847`, PMID `16862161`.
- 方法: 用主成分显式建模祖源差异，校正分层导致的虚假关联。
- 适用边界: 适合大多数 SNP 芯片 GWAS；极端近亲和强批次效应需先处理。
- 参数建议: 在 pruning 后提取 PC，再把前若干 PC 作为协变量进入关联模型。
- 风险: PC 数量选取不当会欠校正或过校正，损失检出效能。
- Source links: [Nature](https://www.nature.com/articles/ng1847), [Google Scholar](https://scholar.google.com/scholar?q=Principal+components+analysis+corrects+for+stratification+in+genome-wide+association+studies)

## PCA-02 Population structure and eigenanalysis
```yaml
knowledge_item.v2:
  doc_id: "paper_pca_patterson_2006"
  version: "v2"
  species: "multi_species"
  blueprint_scope: "pca"
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-09T12:10:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Patterson N et al. *Population Structure and Eigenanalysis* (2006), DOI `10.1371/journal.pgen.0020190`.
- 方法: 给出特征分解框架用于检测和量化群体结构，奠定 EIGENSTRAT 路线基础。
- 适用边界: 适合探索总体结构与离群个体；不能替代细粒度局部祖源推断。
- 参数建议: 先做 LD 剪枝再 PCA，减少高 LD 区域对特征向量的主导。
- 风险: 将 PCA 轴过度生物学解释会产生“地图幻觉”。
- Source links: [PLOS Genetics](https://journals.plos.org/plosgenetics/article?id=10.1371%2Fjournal.pgen.0020190), [Google Scholar](https://scholar.google.com/scholar?q=Population+Structure+and+Eigenanalysis)

## PCA-03 Spatial interpretation caution
```yaml
knowledge_item.v2:
  doc_id: "paper_pca_novembre_2008"
  version: "v2"
  species: "multi_species"
  blueprint_scope: "pca"
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-09T12:10:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Novembre J, Stephens M. *Interpreting principal component analyses of spatial population genetic variation* (2008), DOI `10.1038/ng.139`, PMID `18425127`.
- 方法: 解释 PCA 空间图形与地理结构关系，强调波纹/梯度图案可能由连续迁移产生。
- 适用边界: 适合区域尺度群体结构解释；对离散混合群体需结合 admixture 模型。
- 参数建议: 报告中同时给出 PC 解释率与地理/批次协变量相关性。
- 风险: 只凭 PCA 图形推断历史事件，易过度解读。
- Source links: [Nature Genetics](https://www.nature.com/articles/ng.139), [Google Scholar](https://scholar.google.com/scholar?q=Interpreting+principal+component+analyses+of+spatial+population+genetic+variation)

## PCA-04 STRUCTURE model baseline
```yaml
knowledge_item.v2:
  doc_id: "paper_pca_pritchard_2000"
  version: "v2"
  species: "multi_species"
  blueprint_scope: "pca"
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-09T12:10:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Pritchard JK et al. *Inference of population structure using multilocus genotype data* (2000), DOI `10.1093/genetics/155.2.945`, PMID `10835412`.
- 方法: 基于贝叶斯聚类推断群体成分和个体混合比例。
- 适用边界: 适合中等规模数据与深度结构探索；超大数据计算开销较高。
- 参数建议: 通过多 K 值重复运行并评估收敛稳定性，不依赖单次结果。
- 风险: K 选择主观性强，可能引入模型选择偏差。
- Source links: [PubMed](https://pubmed.ncbi.nlm.nih.gov/10835412/), [Google Scholar](https://scholar.google.com/scholar?q=Inference+of+population+structure+using+multilocus+genotype+data)

## PCA-05 ADMIXTURE fast model-based ancestry
```yaml
knowledge_item.v2:
  doc_id: "paper_pca_admixture_2009"
  version: "v2"
  species: "multi_species"
  blueprint_scope: "pca"
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-09T12:10:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Alexander DH et al. *Fast model-based estimation of ancestry in unrelated individuals* (2009), DOI `10.1101/gr.094052.109`, PMID `19648217`.
- 方法: 与 STRUCTURE 同类模型下的高效近似推断，显著提高速度。
- 适用边界: 适合大样本祖源比例估计；对强亲缘样本需谨慎。
- 参数建议: 使用交叉验证误差辅助选择 K，并与 PCA 结果交叉核验。
- 风险: 过度相信单模型分解结果，忽视模型假设偏离。
- Source links: [PubMed](https://pubmed.ncbi.nlm.nih.gov/19648217/), [Google Scholar](https://scholar.google.com/scholar?q=Fast+model-based+estimation+of+ancestry+in+unrelated+individuals)

## PCA-06 fastSTRUCTURE variational inference
```yaml
knowledge_item.v2:
  doc_id: "paper_pca_faststructure_2014"
  version: "v2"
  species: "multi_species"
  blueprint_scope: "pca"
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-09T12:10:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Raj A et al. *fastSTRUCTURE: Variational Inference of Population Structure in Large SNP Data Sets* (2014), DOI `10.1534/genetics.114.164350`.
- 方法: 用变分推断近似 STRUCTURE，提高大规模数据可用性。
- 适用边界: 适合大型 SNP 数据集结构分解；极弱结构可能受先验设置影响。
- 参数建议: 与 ADMIXTURE/PCA 形成三角验证，减少单算法偏差。
- 风险: 变分近似可能低估后验不确定性。
- Source links: [Genetics](https://academic.oup.com/genetics/article/197/2/573/6074271), [Google Scholar](https://scholar.google.com/scholar?q=fastSTRUCTURE+Variational+Inference+of+Population+Structure+in+Large+SNP+Data+Sets)

## PCA-07 PC-AiR for related samples
```yaml
knowledge_item.v2:
  doc_id: "paper_pca_pcair_2015"
  version: "v2"
  species: "multi_species"
  blueprint_scope: "pca"
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-09T12:10:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Conomos MP et al. *Robust inference of population structure for ancestry prediction and correction of stratification in the presence of relatedness* (2015), DOI `10.1002/gepi.21896`, PMID `25810074`.
- 方法: 在存在亲缘关系样本时稳健推断祖源结构，降低 relatedness 干扰。
- 适用边界: 适合家系/半家系数据；对缺失极高数据需先修复或筛除。
- 参数建议: 把 kinship 推断与 PC-AiR 联动，不要把相关个体直接混入标准 PCA。
- 风险: 如果 kinship 输入质量差，PC-AiR 仍可能残留结构偏差。
- Source links: [PubMed](https://pubmed.ncbi.nlm.nih.gov/25810074/), [Google Scholar](https://scholar.google.com/scholar?q=Robust+inference+of+population+structure+for+ancestry+prediction+and+correction+of+stratification+in+the+presence+of+relatedness)

## PCA-08 FastPCA linear-scaling approach
```yaml
knowledge_item.v2:
  doc_id: "paper_pca_fastpca_2016"
  version: "v2"
  species: "multi_species"
  blueprint_scope: "pca"
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-09T12:10:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Galinsky KJ et al. *Fast Principal-Component Analysis Reveals Convergent Evolution of ADH1B in Europe and East Asia* (2016), DOI `10.1016/j.ajhg.2015.12.022`, PMID `26924531`.
- 方法: 随机矩阵与近似分解实现近线性复杂度 PCA，支持超大样本。
- 适用边界: 适合 biobank 规模结构探索；近似算法参数需调优。
- 参数建议: 固定随机种子并记录近似误差设置，确保可复现。
- 风险: 近似阶数过低可能丢失弱结构信号。
- Source links: [PubMed](https://pubmed.ncbi.nlm.nih.gov/26924531/), [Google Scholar](https://scholar.google.com/scholar?q=Fast+Principal-Component+Analysis+Reveals+Convergent+Evolution+of+ADH1B+in+Europe+and+East+Asia)

## PCA-09 FlashPCA2 biobank-scale PCA
```yaml
knowledge_item.v2:
  doc_id: "paper_pca_flashpca2_2017"
  version: "v2"
  species: "multi_species"
  blueprint_scope: "pca"
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-09T12:10:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Abraham G et al. *FlashPCA2: principal component analysis of Biobank-scale genotype datasets* (2017), DOI `10.1093/bioinformatics/btx299`.
- 方法: 高效 partial PCA，降低内存占用并支持百万级样本。
- 适用边界: 适合资源受限环境的大样本 PCA；需要输入数据先做标准 QC。
- 参数建议: 仅提取下游需要的前若干主成分，避免无效全分解。
- 风险: 在批次效应强时，速度提升不能替代实验设计纠偏。
- Source links: [Oxford Academic](https://academic.oup.com/bioinformatics/article/33/17/2776/3798630), [Google Scholar](https://scholar.google.com/scholar?q=FlashPCA2+principal+component+analysis+of+Biobank-scale+genotype+datasets)

## PCA-10 PCA-based outlier scan
```yaml
knowledge_item.v2:
  doc_id: "paper_pca_pcadapt_2017"
  version: "v2"
  species: "multi_species"
  blueprint_scope: "pca"
  evidence_level: "peer_reviewed"
  source: "paper"
  updated_at: "2026-05-09T12:10:00+08:00"
  owner: "popgen_quantgen"
```
- Paper: Luu K et al. *pcadapt: an R package to perform genome scans for selection based on principal component analysis* (2017), DOI `10.1111/1755-0998.12592`, PMID `27601374`.
- 方法: 基于 PCA 识别与群体结构异常相关的候选位点。
- 适用边界: 适合群体结构-选择信号初筛；不能替代严谨因果验证。
- 参数建议: K 值与离群阈值需做敏感性分析，并报告 FDR 控制策略。
- 风险: 群体历史与批次偏差可造成伪选择信号。
- Source links: [PubMed](https://pubmed.ncbi.nlm.nih.gov/27601374/), [Google Scholar](https://scholar.google.com/scholar?q=pcadapt+an+R+package+to+perform+genome+scans+for+selection+based+on+principal+component+analysis)
