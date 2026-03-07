---
paper_id: 2603.05181v1
title: 'Mario: Multimodal Graph Reasoning with Large Language Models'
authors:
- Yuanfu Sun
- Kang Li
- Pengkang Guo
- Jiajin Liu
- Qiaoyu Tan
domain: Multimodal
slug: 2603-05181v1-mario-multimodal-graph-reasoning-with-large-lang
published: '2026-03-05T13:49:41Z'
summary: 这篇工作把多模态推理对象从孤立图文对换成带边结构的多模态图，并用可学习路由决定每个节点该看哪种模态组合。
source_url: https://arxiv.org/abs/2603.05181v1
pdf_url: https://arxiv.org/pdf/2603.05181v1.pdf
scores:
  relevance: 2.47
  recency: 3.0
  popularity: 2.3
  quality: 2.3
  recommendation: 8.81
tags:
- paper-note
status: generated
updated: '2026-03-07'
keywords:
- 多模态图推理
- 图条件 VLM
- 图指令微调
- 模态自适应路由
- LLM
reading_priority: high
image_count: 5
analysis_depth: full
full_analysis_source: arxiv_source
---

# Mario: Multimodal Graph Reasoning with Large Language Models

## TL;DR
这篇工作把多模态推理对象从孤立图文对换成带边结构的多模态图，并用可学习路由决定每个节点该看哪种模态组合。

## 中文摘要
论文针对多模态图推理，认为现有方法把图像文本对孤立编码，忽略了真实数据中的关系结构。Mario 分两步：先用图条件 VLM 在拓扑引导下做细粒度跨模态对齐，再把对齐后的特征组织成图感知指令视图，并通过可学习路由为每个节点和邻域选择最有信息量的模态配置交给 LLM。摘要称其在多个 MMG 基准上有效，但由于摘要截断，具体提升和适用边界摘要没有充分说明。

## Quick Facts
- Paper ID: `2603.05181v1`
- Authors: Yuanfu Sun, Kang Li, Pengkang Guo, Jiajin Liu, Qiaoyu Tan
- Domain: Multimodal
- Published: 2026-03-05T13:49:41Z
- arXiv: [abstract](https://arxiv.org/abs/2603.05181v1)
- PDF: [download](https://arxiv.org/pdf/2603.05181v1.pdf)
- Reading priority: high
- Why this priority: 与多模态和 LLM 主线高度契合，问题设置比普通图文任务更接近真实系统；但实验摘要不完整，需要带着证据意识去读。

## Abstract Translation
近来的大语言模型进展为多模态推理带来了新机会，但现有多数方法仍依赖预训练视觉-语言模型把图文对孤立编码，忽略了真实世界多模态数据天然具有的关系结构。这促使作者考虑多模态图：每个节点同时具有文本和视觉属性，边提供结构线索。要在保留图拓扑的同时让 LLM 处理这类异构信号，会遇到两个关键挑战：跨模态一致性弱，以及不同节点对模态的偏好不同。为此，论文提出统一框架 Mario，同时解决这两个问题并支持在多模态图上进行 LLM 推理。Mario 包含两个阶段：第一阶段是图条件视觉-语言模型，在图拓扑引导下通过细粒度跨模态对比学习联合优化文本与视觉特征；第二阶段是模态自适应图指令微调，把对齐后的多模态特征组织成图感知指令视图，并用可学习路由器为每个节点及其邻域选择最有信息量的模态配置送入 LLM。摘要称，在多个多模态图基准上，Mario 在监督与零样本场景下的节点分类和链路预测都优于现有最强图模型；摘要还提到代码将公开。

## Research Background And Motivation
这篇工作处在两个趋势的交叉点上：一边是 LLM/指令调优正在从纯文本走向多模态推理，另一边是越来越多真实数据并不是孤立图文对，而是带关系边的多模态实体图。常见做法是先用 CLIP 一类 VLM 编码节点，再交给 GNN 或 GraphLLM，但这种流水线默认节点内图文已经对齐良好，也默认所有节点适合同一提示模板，这两点在真实多模态图里都很脆弱。

## Problem Framing
论文要解决的是：在多模态图中，如何既保留图结构和邻域依赖，又让 LLM 真正利用文本、图像和边关系进行节点分类与链路预测。作者把难点明确拆成两个瓶颈：第一，节点内图文往往噪声大、描述不完整或语义错位，直接融合后再做图传播可能放大错配；第二，不同节点及其局部子图对文本、图像、两者结合三种输入视图的依赖并不相同，固定模板会浪费可用监督。

## Method Overview
Mario 采用两阶段设计。第一阶段先训练一个图条件 VLM：在文本塔和图像塔内部引入拓扑感知的 multimodal mixer，使节点表示在图结构偏置下迭代吸收邻域信息，再用双向 InfoNCE 把两种模态在结构条件下对齐。第二阶段把这些对齐后的表示映射成可插入 LLM 的图文本和图图像 special tokens，围绕每个节点构造文本视图、图像视图和多模态视图三类图感知提示，并训练一个轻量路由器根据节点自身表示、1/2-hop 上下文和度信息，为每个样本选择最合适的提示视图；训练时做软路由联合学习，推理时做硬选择，只送一个模板进 LLM。

## Method Details
- GVLM 采用双塔编码器分别处理文本和图像，节点的 [CLS] 表示作为后续结构感知聚合的核心载体；初始表示来自预训练 VLM 特征并加入位置编码。
- Topology-Aware Multimodal Mixer 会收集图中节点的 [CLS] 表示，做带图结构位置偏置的多头注意力；该偏置由按最短路径距离分桶的可学习标量构成，用来编码节点间的结构角色关系。
- 每一层 mixer 得到的结构感知节点表示会回灌到对应模态序列中，替换下一层的 [CLS]，从而让 token/patch 级特征在多层过程中持续吸收图上下文，而不是只在输出端做一次图传播。
- 跨模态对齐使用对称、温度缩放的 InfoNCE：同一节点的文本-图像对为正样本，batch 内跨节点组合为负样本；因为表示已显式注入拓扑，所以这个对齐目标不只是节点内对齐，也隐含利用了邻域语义来缩小跨模态差距。
- 第二阶段先用共享投影器把 Stage 1 的文本/图像表示映射到 LLM token 空间，形成图文本和图图像 special tokens；再按 1/2-hop 邻居中与锚点拼接表示余弦相似度最高的节点构造三类模板，并用 MAPR 基于节点表示、邻域均值池化和对数度输入预测路由分布，通过“模板损失后验 + KL 正则”的方式学习选择最优模态视图。

## Experimental Setup And Evidence
实验围绕四个研究问题展开：1）在标准多模态图任务上与不同模态输入的强基线比较整体效果；2）在完全未见的多模态图上测试 zero-shot 泛化；3）分析图条件 VLM 对表示学习和后续指令调优的贡献；4）分析模态自适应图指令微调相对单模板方案的性能与效率。提取文本明确说明任务覆盖节点分类和链路预测，并且论文还包含 Dataset Details、Experiment Details、GVLM 对齐的 t-SNE 可视化、与 MMGCN/MGAT 的比较、额外 GNN zero-shot 结果以及 Frozen vs LoRA-Tuned Mario 的分析。具体 benchmark 名称、样本规模、所用 LLM/VLM 主干、超参数、重复次数和统计显著性，提取文本没有充分说明。

## Main Results And Claims
提取文本显示，作者报告 Mario 在多个多模态图基准上，对监督和 zero-shot 场景下的节点分类与链路预测都优于现有图模型；文中贡献总结还声称，在 zero-shot transfer 中最高可达到 1.6× 的收益。引言中的图表说明还给出一项对齐层面的证据：引入图拓扑后，跨模态一致性相对 frozen CLIP 平均提升 68%，相对逐节点微调再提升 6%。但各数据集上的绝对分数、方差、与不同基线的逐项差距，提取文本没有充分说明。

## Research Or Engineering Value
如果论文结论成立，这项工作最值得研究者和工程师关注的价值，不只是一个新的 MMG 模型，而是一条更系统的设计范式：先做结构感知的跨模态对齐，再做节点级模态路由。它适合那些节点天然带图文属性且实体之间有关系边的系统，如多模态知识图、文档图、内容网络、商品或媒体实体图。对多模态 Agent/复杂信息系统而言，它也给出一个重要提醒：不要假设节点内图文天然一致，也不要假设所有节点都该走同一种提示模板。

## Relation To Prior Work
相对常见的“用 VLM 编码单节点图文，再把嵌入交给 GNN/Graph 模型传播”的路线，Mario 的关键差异是把图结构直接放进跨模态对齐阶段，而不是默认 CLIP 式表征已经足够一致；它通过双塔编码内部的结构偏置和 per-modality 对齐，显式修正节点内图文错配。相对只处理文本图或依赖固定提示模板的 GraphLLM 路线，Mario 不再用一套模板覆盖所有节点，而是维护 text、image、multimodal 三类图感知模板并让路由器按节点选择。相对 MLaGA 这类先把图像和文本融合成共享查询再对齐的方案，Mario 更强调保留模态特有信息后再做节点级选择；相对主要处理缺失模态的 Graph4MM，它面向的是“模态齐全但对齐差、偏好异质”的 MMG 场景。

## Overall Assessment
这篇论文现在值得读，主要因为它抓住了一个比普通图文任务更贴近真实系统的问题：当输入是带关系结构的多模态实体图时，LLM 不能只依赖孤立图文编码，也不能默认所有节点都适合同一提示模板。全文最值得信的是问题拆解和机制设计的对应关系很清楚，Stage 1 与 Stage 2 各自解决的瓶颈明确，而且提取文本确实给出了一些支撑性证据，如跨模态一致性提升、监督与 zero-shot 上的整体优势、以及最高 1.6× 的 zero-shot 增益。最该保持怀疑的是实验普适性和真实成本：当前提取文本没有充分说明具体 benchmark、绝对提升、统计稳定性、对噪声边或缺失模态的鲁棒性，以及训练期三模板多次前反向的资源代价。因此，它更像一篇方向感很强、方法构型有说服力的系统论文；是否已经成为稳健、可复用的工程方案，还要依赖完整实验节和消融来验证。

## Strengths
- 问题定义抓得准：不是泛泛做“多模态图 + LLM”，而是把瓶颈具体落到跨模态错配和节点级模态偏好差异上。
- 方法分工清晰：Stage 1 先解决表示层的结构感知对齐，Stage 2 再解决提示层的自适应选择，逻辑闭环比较完整。
- 相对常见“先编码再图传播”的流程，Mario 把图结构前移到模态对齐阶段，这一点对 MMG 比普通图文任务更有针对性。
- 路由器设计有工程意识：训练期用多模板学习节点偏好，推理期硬选择单模板，文本中明确声称不会比单模板推理多算。

## Future Work
- 检验图条件对齐在错边、噪声边、异配图上的鲁棒性，明确结构信息何时帮助对齐、何时反而放大误差。
- 把 Mario 扩展到缺失模态、超过两种模态或更一般的异构图场景，验证 router 的稳定性与可迁移性。
- 拆分 zero-shot 收益来源，分别量化 GVLM、模板银行、MAPR 和训练节点 exemplars 的独立贡献。
- 探索更低成本的训练方案，例如减少三模板多次前反向开销，或把两阶段训练做得更统一。

## Reading Checklist
- 先看 Introduction 和 Figure 1，确认论文为何把问题拆成“跨模态一致性弱”和“模态偏好异质”两个层次。
- 细读 Graph-conditioned Vision-Language Model，重点核对 shortest-path bucket 图偏置、[CLS] 回灌机制，以及 InfoNCE 的正负样本定义。
- 细读 Modality-Adaptive Graph Instruction Tuning，确认三类模板分别包含哪些 special tokens、是否保留原始文本、邻居标签如何注入。
- 核对 zero-shot 设定到底是跨数据集、跨图还是跨类别，避免把更弱的泛化设定误读成更强的迁移结论。

## Core Contributions
- 把多模态图推理中的两个核心障碍明确为跨模态一致性弱和模态偏好异质。
- 提出图条件 VLM，用拓扑引导的细粒度跨模态对比学习联合修正文图特征。
- 提出模态自适应图指令微调和可学习路由，让 LLM 按节点与邻域选择更合适的模态视图。

## Why Read It
- 它直接对应多模态 LLM 下一步常见痛点：输入不再是单轮图文，而是带关系结构的复杂对象。
- 方法里同时有表示学习和指令调优两层设计，值得看两者分工是否清晰。
- 如果你关心多模态 Agent 读图、读文档、看关系图，这篇论文的问题设置比普通 VLM 论文更接近真实系统。

## Risks Or Limits
- 实验信息缺口较大：具体 benchmark、绝对指标、误差范围和显著性没有在提取文本中展开，当前只能相信方向性结论。
- 训练链路较长：需要先做 GVLM 预训练，再做 LLM + 路由器联合调优；而且 Stage 2 每个样本要跑三个模板，真实训练成本提取文本没有充分说明。
- 方法对图质量可能敏感，因为 Stage 1 明确把图拓扑注入跨模态对齐；如果边有噪声、图很稀疏或存在强异配，是否会放大错误信号，提取文本没有充分说明。
- 提示构造依赖从训练集节点中选择 1/2-hop 邻居并附带标签作为 in-context evidence，这种设计对可用训练图上下文有依赖，其收益中有多少来自路由本身、有多少来自 exemplar 构造，需要看完整消融。

## Recommended For
- 做多模态 LLM 与图推理的研究者
- 关注文档图、知识图或复杂实体关系理解的工程师
- 想研究输入路由与异构模态选择机制的读者

## Keywords
- 多模态图推理
- 图条件 VLM
- 图指令微调
- 模态自适应路由
- LLM

## Figures
![Figure1_page1](images/Figure1_page1.png)

![Mario_page1](images/Mario_page1.png)

![arts_visual_page1](images/arts_visual_page1.png)

![moviesCLIP_tsne_page1](images/moviesCLIP_tsne_page1.png)

![movies_visual_page1](images/movies_visual_page1.png)

- Full asset manifest: [images/index.md](images/index.md)

## Abstract
Recent advances in large language models (LLMs) have opened new avenues for multimodal reasoning. Yet, most existing methods still rely on pretrained vision-language models (VLMs) to encode image-text pairs in isolation, ignoring the relational structure that real-world multimodal data naturally form. This motivates reasoning on multimodal graphs (MMGs), where each node has textual and visual attributes and edges provide structural cues. Enabling LLM-based reasoning on such heterogeneous multimodal signals while preserving graph topology introduces two key challenges: resolving weak cross-modal consistency and handling heterogeneous modality preference. To address this, we propose Mario, a unified framework that simultaneously resolves the two above challenges and enables effective LLM-based reasoning over MMGs. Mario consists of two innovative stages. Firstly, a graph-conditioned VLM design that jointly refines textual and visual features through fine-grained cross-modal contrastive learning guided by graph topology. Secondly, a modality-adaptive graph instruction tuning mechanism that organizes aligned multimodal features into graph-aware instruction views and employs a learnable router to surface, for each node and its neighborhood, the most informative modality configuration to the LLM. Extensive experiments across diverse MMG benchmarks demonstrate that Mario consistently outperforms state-of-the-art graph models in both supervised and zero-shot scenarios for node classification and link prediction. The code will be made available at https://github.com/sunyuanfu/Mario.

## Recommendation Signals
- Recommendation score: 8.81
- Relevance score: 2.47
- Recency score: 3.0
- Popularity score: 2.3
- Quality score: 2.3

## Assets
- Extracted assets are stored in the `images/` folder next to this page.
- Browse the image manifest here: [images/index.md](images/index.md)
