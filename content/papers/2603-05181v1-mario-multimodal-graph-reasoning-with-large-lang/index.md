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
近来，大语言模型推动了多模态推理的发展，但多数现有方法仍把图文对作为孤立样本交给预训练视觉语言模型编码，忽略了真实世界多模态数据天然具有的关系结构。为此，论文考虑多模态图（MMG）：每个节点同时带文本和视觉属性，边提供结构线索。在保留图拓扑的前提下，让 LLM 对这类异构多模态信号做推理面临两个关键挑战：跨模态一致性弱，以及不同节点存在异质的模态偏好。为解决这两个问题，作者提出统一框架 Mario。它包含两个阶段：第一阶段是图条件视觉语言模型，在图拓扑引导下通过细粒度跨模态对比学习联合优化文本与图像特征；第二阶段是模态自适应的图指令微调，将对齐后的多模态特征组织成图感知指令视图，并用可学习路由器为每个节点及其邻域选择最有信息量的模态配置交给 LLM。摘要称，在多个 MMG 基准上，Mario 在监督和零样本场景下的节点分类与链路预测任务中都持续优于现有最优图模型。

## Research Background And Motivation
多模态 LLM 的常见输入仍是单个图文对，但真实数据往往更像“带关系的多模态实体集合”，节点之间的边本身就是重要信号。现有“VLM 编码节点、GNN 做传播”的路线默认节点内文本和图像已充分对齐，这在噪声文本、弱配图、语义不完整的场景里并不成立。

## Problem Framing
论文要解决的是：在多模态图上，如何同时利用文本、图像和图结构，让 LLM 做节点分类与链路预测，而不是只在节点级做图文拼接。作者把问题拆成两个更具体的障碍：一是节点内图文常常语义不一致，需要借助邻居和拓扑来补全对齐；二是不同节点及其局部子图对文本、图像或二者组合的依赖不同，固定模板会浪费信息。

## Method Overview
Mario 是一个两阶段框架。第一阶段先训练图条件 VLM，用结构感知的跨模态对齐把节点文本和图像映射到更一致、同时保留拓扑信息的表示空间；第二阶段再把这些对齐后的表示转成多种图感知提示视图，并用模态自适应路由器为每个节点选择更合适的提示模板，让 LLM 在节点级和邻域级都能按需使用文本、图像或二者联合信息。

### Method Figure
![Mario_page1](images/Mario_page1.png)

*Figure cue:* Overview of the proposed Mario framework. Given a MMG, Stage 1 uses a graph-conditioned vision–language model to perform structure-aware image–text alignment: images and texts are initially encoded, symmetrically refined by a Transformer-embedded Mixer that injects graph structure into token embeddings, and then aligned via contrastive learning. Stage 2 builds on these aligned features with modality-adaptive graph instruction tuning, where a lightweight router, trained under LLM supervision (a),

## Method Details
- Stage 1 采用文本塔和图像塔的双塔编码结构，初始表示来自预训练视觉语言特征并加入位置编码；每层都以 [CLS] 作为节点级摘要，供后续图结构注入与跨模态对齐使用。
- 核心的 Topology-Aware Multimodal Mixer 会收集所有节点的 [CLS] 表示，对其做带图偏置的多头注意力；这个图偏置由按最短路距离分桶的、head-specific 可学习标量实现，使不同结构角色进入注意力计算。
- 混合器得到的结构感知节点表示会被重新注入到各模态序列前端，替换原 [CLS]，从而在后续 Transformer 层中持续把图上下文与 token/patch 级特征迭代融合。
- 跨模态对齐使用双向温度缩放 InfoNCE：同一节点的文本-图像对是唯一正样本，batch 内跨节点组合为负样本。由于输入表示已编码邻域信息，这一步学到的是“拓扑感知”的图文一致性，而不是纯节点内对齐。
- Stage 2 为每个节点构造三种提示视图（文本、图像、多模态），并加入基于 1/2-hop 邻居的图上下文 token；随后用 MAPR 路由器根据节点的 Stage 1 表示、1/2-hop 上下文均值和对数度数输出模板概率，训练时结合各模板对应的 LLM 损失后验与 KL 正则进行软路由，推理时切换为硬路由，只保留单一模板。

## Experimental Setup And Evidence
提取文本显示，实验围绕四个问题展开：总体性能（RQ1）、零样本泛化与迁移（RQ2）、组件消融（RQ3）以及效率与可视化（RQ4）。任务明确包括节点分类和链路预测，场景覆盖监督与零样本设置；两阶段训练使用同一批数据，先预训练 GVLM，再固定其参数并用 LoRA 联合训练 LLM 与 MAPR。附录标题还表明作者做了 t-SNE 可视化、与 MMGCN/MGAT 的比较、额外 GNN 零样本结果，以及 Frozen vs LoRA-Tuned Mario 的比较，但提取文本没有充分说明具体数据集构成、基线名单、LLM 规模、超参数和评测协议细节。

### Experiment Figure
![Figure1_page1](images/Figure1_page1.png)

*Figure cue:* (a) Cosine similarity between text and image embeddings across three models on four datasets.
(b) Venn diagram over three prompt templates with different modality inputs: Text-Only, Image-Only, and Text+Image. Each colored circle corresponds to one template; numbers in each region give the proportion of nodes that can be correctly classified only by that template or by the union of the templates whose regions overlap (where overlapping regions blend the colors). Results are averaged over four da

## Main Results And Claims
提取文本支持的结论有四点：第一，论文声称 Mario 在多个多模态图基准上，对节点分类和链路预测都优于现有图模型，且覆盖监督与零样本场景；第二，作者在引言中给出一项对齐证据：把图拓扑纳入对齐后，跨模态一致性相对 frozen CLIP 平均提升 68%，相对逐节点微调再提升 6%；第三，图 1 相关文字说明接近 30% 的节点只能被三种模板中的某一种或某两种正确分类，这直接支持“固定单模板不足、需要自适应模态选择”的问题设定；第四，文中还声称零样本迁移可达到最高 1.6× 增益，且路由器让训练大约以单模板基线一半的 epoch 数收敛，推理阶段通过硬路由保持与单模板流程相当的计算开销。除这些结论外，提取文本没有充分说明更细的数值分布和统计稳定性。

## Research Or Engineering Value
如果这些结论成立，Mario 的价值不在于又一个更强的图模型，而在于给出了一条更系统的 MMG+LLM 方案：先用结构感知对齐修正节点内图文错位，再把节点级模态选择显式交给路由器。对需要同时看文本、图像和实体关系的系统，这种设计比“把所有输入直接拼进 prompt”更有可解释的工程分层，也更容易分析性能到底来自对齐还是来自提示策略。

## Relation To Prior Work
相对最常见的“先用 CLIP 类 VLM 独立编码每个节点，再把嵌入交给 GNN/GraphLLM”的路线，Mario 的核心差别是把图拓扑提前放进跨模态对齐阶段，而不是默认节点内图文已经同步。相对多数 GraphLLM 工作只处理文本图、并使用单一固定模板的做法，Mario 明确把文本、图像、多模态三种视图都保留下来，再让路由器按节点和局部子图做选择。文中还点名区分了两类接近路线：MLaGA 是先把图文融合成共享查询再对齐，隐含了模态效用相近的假设；Graph4MM 主要面向缺模态设置，而 Mario 更关注“模态齐全但一致性弱、偏好异质”的 fully observed MMG。

## Overall Assessment
这篇论文当前最值得信的部分，是问题定义和方法结构之间的对应关系比较严密：作者没有把 MMG 上的困难笼统归因于“多模态复杂”，而是拆成对齐问题和选择问题，并分别用图条件对齐和模板路由来处理；引言中的对齐提升、模板互补性和推理无额外算力也给了初步证据。最该怀疑的部分是实验充分性和外推边界：提取文本没有充分说明 benchmark、基线、公平比较、统计稳定性以及噪声图上的鲁棒性，而方法本身训练链路偏长、对图质量和邻域选择可能较敏感。因此，这篇论文很值得作为“MMG 上如何把表示学习与 LLM 推理解耦”的主线来读，但在接受其 SOTA 与泛化结论前，必须先补看完整实验和失败案例。

## Strengths
- 问题拆分清晰：把 MMG 上的难点明确为“弱跨模态一致性”和“异质模态偏好”，方法两阶段设计与这两个问题一一对应。
- 方法不是简单把图结构塞进 LLM，而是先做结构感知对齐，再做提示级模态选择，表示学习层和推理层的职责划分相对清楚。
- Topology-aware mixer 的实现比较具体，不是泛泛说“融合图信息”，而是通过最短路距离偏置和 [CLS] 重新注入实现结构条件化的图文对齐。
- MAPR 不是静态模板选择，而是用各模板的 LLM 损失后验反向监督路由器，训练目标与最终选择策略一致性较强。

## Future Work
- 检验对错误边、弱连接和噪声邻居的鲁棒性，确认 Stage 1 的结构条件对齐在坏图上是否会放大误差。
- 把 MAPR 的选择粒度从节点级扩展到更细的邻域或子任务级，研究不同 hop、不同节点类型下的路由校准问题。
- 降低 Stage 2 三模板联合训练的成本，例如蒸馏为更轻的选择器，或研究是否能在更少模板下保留大部分收益。
- 扩展到文本+图像之外的更异构输入，验证该框架是否真能泛化为更一般的多模态图推理接口。

## Reading Checklist
- 先看 Figure 1 和方法总览，确认作者提出的两个挑战是否真的由数据现象支撑，而不是事后命名。
- 细读 Stage 1：最短路距离偏置如何进入注意力、Mixer 放在每层的哪个位置、为何只替换 [CLS] 就足够传递结构信息。
- 核对 Stage 2 的模板构造：三种视图各包含哪些 token，邻居是如何按相似度筛选的，是否可能把标签泄露或引入过强的 ICL 先验。
- 重点看 RQ3/RQ4 消融：去掉 GVLM、去掉 MAPR、改成单模板后分别损失多少，才能判断两阶段是否都必要。

## Core Contributions
- 把多模态图推理中的两个核心障碍明确为跨模态一致性弱和模态偏好异质。
- 提出图条件 VLM，用拓扑引导的细粒度跨模态对比学习联合修正文图特征。
- 提出模态自适应图指令微调和可学习路由，让 LLM 按节点与邻域选择更合适的模态视图。

## Why Read It
- 它直接对应多模态 LLM 下一步常见痛点：输入不再是单轮图文，而是带关系结构的复杂对象。
- 方法里同时有表示学习和指令调优两层设计，值得看两者分工是否清晰。
- 如果你关心多模态 Agent 读图、读文档、看关系图，这篇论文的问题设置比普通 VLM 论文更接近真实系统。

## Risks Or Limits
- 最关键的问题是实验细节缺失：提取文本没有充分说明具体 benchmark、基线配置、显著性、不同任务上的绝对提升幅度和方差，因此“持续优于 SOTA”的可信度目前只能部分接受。
- 两阶段流程较长，Stage 2 训练时每个样本要跑三套模板，虽然推理不增算力，但训练成本和工程复杂度明显更高。
- 方法强依赖图结构质量。文本明确把邻居当作补全图文一致性的关键来源，但如果边本身有噪声，可能反而放大错误对齐；这部分提取文本没有充分说明。
- 模态路由依赖训练节点构造 1/2-hop 上下文与示例，泛化是否受图规模、节点度分布、邻域稀疏性影响，提取文本没有充分说明。

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

## Additional Figures

![movies_visual_page1](images/movies_visual_page1.png)

*Figure cue:* Movies

![arts_visual_page1](images/arts_visual_page1.png)

*Figure cue:* Movies

![moviesCLIP_tsne_page1](images/moviesCLIP_tsne_page1.png)

*Figure cue:* Movies – Frozen CLIP
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
