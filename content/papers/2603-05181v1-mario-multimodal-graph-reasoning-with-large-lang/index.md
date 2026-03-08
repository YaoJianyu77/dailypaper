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
summary: 这篇工作试图让 LLM 在保留图拓扑的前提下处理文本、图像与关系共同构成的多模态图，并用图感知对齐与模态自适应路由提升推理质量。
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
institutions:
- New York University Shanghai
- New York University
- Tsinghua University
venue_or_journal: CVPR 2026
citation_summary: Citation count unavailable
keywords:
- 多模态图
- 大语言模型
- 视觉语言模型
- 跨模态对齐
- 图推理
- 指令微调
reading_priority: high
image_count: 10
analysis_depth: full
full_analysis_source: arxiv_source
---

# Mario: Multimodal Graph Reasoning with Large Language Models

## TL;DR
这篇工作试图让 LLM 在保留图拓扑的前提下处理文本、图像与关系共同构成的多模态图，并用图感知对齐与模态自适应路由提升推理质量。

## 中文摘要
论文关注多模态图推理：节点同时含文本和视觉属性，边提供关系线索，而现有方法多把图文对孤立编码。作者提出 Mario，两阶段处理这一问题：先用图拓扑引导的细粒度跨模态对比学习联合优化文本和视觉特征，再把对齐后的特征组织成图感知指令视图，并用可学习路由器为每个节点及邻域选择更有信息量的模态配置供 LLM 推理。若方法成立，它为 LLM 处理结构化多模态知识提供了一条更系统的路径；但摘要没有充分说明具体基准、指标和增益幅度，而且提供的摘要本身被截断。

## Quick Facts
- Paper ID: `2603.05181v1`
- Authors: Yuanfu Sun, Kang Li, Pengkang Guo, Jiajin Liu, Qiaoyu Tan
- Institutions: New York University Shanghai, New York University, Tsinghua University
- Domain: Multimodal
- Venue / Journal: CVPR 2026
- Citations: Citation count unavailable
- Published: 2026-03-05T13:49:41Z
- arXiv: [abstract](https://arxiv.org/abs/2603.05181v1)
- PDF: [download](https://arxiv.org/pdf/2603.05181v1.pdf)
- Reading priority: high
- Why this priority: 这篇工作与当前高优先级方向“LLM + 多模态”高度贴合，而且把问题从孤立图文对推进到多模态图推理，方法上同时涉及图条件对齐与模态自适应路由，具备明显的新意和方法价值。虽然摘要证据不完整且被截断，但正因为问题定义和机制设计都值得核对，它仍应列为优先阅读对象。

## Abstract Translation
近年来，大语言模型（LLM）的进展为多模态推理打开了新路径。然而，现有大多数方法仍依赖预训练视觉语言模型（VLM）对孤立的图文对进行编码，忽略了真实世界多模态数据天然具有的关系结构。这促使我们研究多模态图（MMG）上的推理，其中每个节点同时具有文本和视觉属性，而边提供结构线索。在保留图拓扑的同时，让 LLM 对这类异构多模态信号进行推理，会带来两个关键挑战：解决较弱的跨模态一致性，以及处理异质的模态偏好。为此，我们提出 Mario，一个统一框架，同时应对上述两个挑战，并实现对 MMG 的有效 LLM 推理。Mario 包含两个创新阶段。第一，设计图条件视觉语言模型，在图拓扑引导下通过细粒度跨模态对比学习联合优化文本与视觉特征。第二，提出模态自适应图指令微调机制，将对齐后的多模态特征组织为图感知指令视图，并使用可学习路由器，为每个节点及其邻域选择对 LLM 最有信息量的模态配置。在多种 MMG 基准上的大量实验表明，Mario 在监督和零样本场景下的节点分类与链路预测任务中，都持续优于当前最先进的图模型。代码将公开。

## Research Background And Motivation
多模态推理正在从孤立图文样本走向带关系结构的真实数据，而传统“先用 VLM 编码节点，再交给 GNN/LLM 处理”的流程默认图像和文本天然对齐。论文认为，这个默认前提在多模态图里往往不成立，图结构不只是后续传播的辅助信息，也应进入跨模态对齐本身。

## Problem Framing
论文要解决的是：如何让 LLM 在保留图拓扑的前提下，对同时含文本、图像和边结构的多模态图进行推理。作者把问题拆成两个耦合难点：一是节点内部的图文语义可能并不一致，二是不同节点及其局部子图对文本、图像或两者组合的依赖并不相同；如果继续使用固定模板或先验对齐，噪声会被图传播和提示构造进一步放大。

## Method Overview
Mario 采用顺序式两阶段框架。第一阶段是 graph-conditioned VLM：在双塔编码器中加入拓扑感知的多模态 mixer，把图结构注入文本塔和图像塔的节点表征，并用双向 InfoNCE 进行结构感知的跨模态对齐。第二阶段是 modality-adaptive graph instruction tuning：将第一阶段得到的特征投影为图文本/图图像特殊 token，构造文本视图、图像视图和多模态视图三类图感知提示，再用轻量路由器 MAPR 为每个节点及其邻域选择最有信息量的提示配置，并与 LLM 联合训练；推理时使用硬路由，只保留一个模板。

### Method Figure
![Mario_page1](images/Mario_page1.png)

*Figure cue:* Overview of the proposed Mario framework. Given a MMG, Stage 1 uses a graph-conditioned vision–language model to perform structure-aware image–text alignment: images and texts are initially encoded, symmetrically refined by a Transformer-embedded Mixer that injects graph structure into token embeddings, and then aligned via contrastive learning. Stage 2 builds on these aligned features with modality-adaptive graph instruction tuning, where a lightweight router, trained under LLM supervision (a),

## Method Details
- 第一阶段使用双塔 Transformer 分别处理文本和图像，初始表示来自预训练视觉语言表征，并在后续层中持续维护每个节点的 [CLS] 汇总表示。
- Topology-Aware Multimodal Mixer 会收集所有节点的 [CLS] 表示做带图偏置的多头注意力；该偏置由按最短路径距离分桶的可学习相对位置标量构成，从而把结构角色直接注入跨节点注意力。
- Mixer 产出的结构感知节点表示会回填为下一层的 [CLS]，与原始 token/patch 序列一起继续编码，形成“结构聚合 -> 回注 token 流 -> 再编码”的逐层细化过程。
- 跨模态对齐采用对称、温度缩放的 InfoNCE：同一节点的文本/图像表征是唯一正样本，批内跨节点组合为负样本；由于表征已融入拓扑，优化目标不只是图文贴近，还要求其保留邻域依赖。
- 第二阶段先基于节点自身特征与 1/2-hop 邻域构造三种模板视图，再用 MAPR 根据节点多模态嵌入、1/2-hop 上下文均值和对数度数输出模板路由概率；训练时结合各模板的负因果语言建模损失形成性能后验，并用加权目标加 KL 正则逼近该后验，推理时切换为硬选择以避免额外计算。

## Experimental Setup And Evidence
实验围绕四个研究问题展开：RQ1 比较 Mario 与不同模态输入的主流基线在标准多模态图任务上的总体性能；RQ2 检查在未见过的 MMG 上的 zero-shot 泛化；RQ3 分析 graph-conditioned VLM 对表征学习和指令调优的贡献；RQ4 分析模态自适应提示相对单模板方法的收益与效率。提取文本明确覆盖监督和 zero-shot 两种设置，以及节点分类和链路预测两类任务；从图名/图注可见至少涉及 Arts、Reddit、CDs、Movies 四个数据集，并包含 t-SNE、训练损失曲线以及与 MMGCN、MGAT 的比较。LLM/VLM 主干、精确数据划分、超参数、Top-k 设定和正式评价指标名称，提取文本没有充分说明。

### Experiment Figure
![Figure1_page1](images/Figure1_page1.png)

*Figure cue:* (a) Cosine similarity between text and image embeddings across three models on four datasets.
(b) Venn diagram over three prompt templates with different modality inputs: Text-Only, Image-Only, and Text+Image. Each colored circle corresponds to one template; numbers in each region give the proportion of nodes that can be correctly classified only by that template or by the union of the templates whose regions overlap (where overlapping regions blend the colors). Results are averaged over four da

## Datasets And Benchmarks
- Arts
- Reddit
- CDs
- Movies

## Baselines
- Frozen CLIP
- 节点级微调的 CLIP / node-wise fine-tuning
- 单模板提示基线
- MMGCN
- MGAT
- 其他 GNN 基线（具体名称提取文本没有充分说明）

## Metrics
- 文本-图像嵌入余弦相似度（用于对齐分析）
- 节点分类指标（提取文本没有充分说明具体名称）
- 链路预测指标（提取文本没有充分说明具体名称）
- 训练损失/收敛曲线（用于效率分析）

## Ablations And Analysis
- RQ3：分析 GVLM 对表示学习与后续指令调优的贡献
- RQ4：分析 MAPR 相对单模板提示的性能与效率
- t-SNE 可视化 GVLM 对齐效果
- Frozen v.s. LoRA-Tuned Mario 分析（见附录标题）

## Evaluation Validity And Fairness
- 正面：实验声明同时覆盖监督与 zero-shot 场景，以及节点分类与链路预测两类任务。
- 正面：文中明确说明验证/测试节点不会作为 in-context exemplars 注入提示，降低了通过提示构造造成的信息泄漏风险。
- 正面：两阶段训练在相同数据集上顺序进行，便于把“表征对齐”和“LLM 适配”分开分析。
- 缺口：提取文本没有充分说明数据划分、随机种子、显著性检验、完整表格数值、计算预算和具体 backbone，因此“持续 SOTA”和“1.6× zero-shot 增益”的稳健性仍需通读实验节核对。

## Main Results And Claims
提取文本报告了三类结论。第一，在多种 MMG 基准上，Mario 在监督和 zero-shot 场景下的节点分类与链路预测任务中持续优于现有图模型，并声称 zero-shot 迁移最高可达到 1.6× 增益。第二，引言中的对齐分析称，引入图拓扑后，文本与图像嵌入的一致性相对 frozen CLIP 平均提升 68%，相对节点级微调再提升 6%。第三，图注和引言都支持“固定单模板不够”的判断：接近 30% 的节点只能被三种模态模板中的一种或两种正确分类，这为模态自适应路由提供了直接动机。

## Research Or Engineering Value
这篇工作现在值得读，主要因为它把当前很活跃但还缺少稳定范式的“LLM + 多模态 + 图结构”问题拆成了可操作的两段：结构感知对齐，以及面向 LLM 的模态路由。对做多节点上下文理解、知识增强推理、多模态检索代理或结构化内容分析的人，它提供了比“直接拼接图文特征进提示”更系统的接口方案；但是否值得工程化采纳，仍取决于完整实验是否证明其收益足以覆盖两阶段训练和模板路由的复杂度。

## Relation To Prior Work
相对常见的“预训练 VLM 编码每个节点，再交给 GNN 或 GraphLLM 处理”的路线，Mario 不接受“节点内部图文已经天然对齐”这个前提，而是把图拓扑直接引入跨模态对齐阶段。相对固定模板的 GraphLLM 做法，它认为 MMG 中不同节点对文本、图像和二者结合的依赖并不统一，因此引入了节点级模板路由，而不是共享一个提示形式。相对先把多模态早期融合后再做对齐/调优的路线，Mario 保留了文本视图、图像视图和多模态视图三条通道，再用监督驱动的路由去做选择，核心差异是避免把“模态效用相等”写死在模型里。文中还明确把自己与关注缺失模态场景的 Graph4MM 区分开：Mario 更聚焦于 fully observed MMG 中的弱一致性与偏好异质问题。

## Overall Assessment
从已给文本看，这篇论文最值得信的是问题定义和方法链路本身：弱跨模态一致性与节点级模态偏好这两个痛点在 MMG 场景里都很合理，而 Mario 的两阶段设计也确实逐一对应这两个问题。最该怀疑的是经验结论的强度，因为当前可见证据主要是少量 headline 结果、图示和研究问题说明，完整表格、指标和成本细节都缺失。如果正式实验部分确实支撑“跨数据集稳定收益 + zero-shot 明显增益”，它会是一篇把多模态图学习与 LLM 推理真正接上的方法论文；如果这些结果不够稳，那么它的主要价值可能更多停留在问题刻画和框架整合，而不是压倒性的实证优势。

## Technical Route Positioning
这篇论文属于“图学习 + 视觉语言表征 + LLM 指令调优”的多模态图推理路线，定位在整条链路里最容易失真的中间层：先把节点级图文表征在图结构约束下对齐，再把这些对齐后的多模态信号组织成适合 LLM 消化的图感知提示，并通过路由机制做节点级模态选择。它解决的不是纯图编码问题，也不是纯 LLM 推理问题，而是二者之间的接口设计与信息保真问题。

## Scorecard
- Overall: 6.4/10
- Innovation: 7/10
- Technical Quality: 7/10
- Experimental Rigor: 5/10
- Writing Clarity: 6/10
- Practical Value: 7/10

## Strengths
- 问题拆解比较到位：不是把“多模态图喂给 LLM”笼统处理，而是明确区分跨模态一致性和节点级模态偏好两个不同层面的失败来源。
- 方法链路完整：先做结构感知的跨模态对齐，再做面向 LLM 的模板构造与模态路由，逻辑上比直接把 VLM 特征拼接进提示更自洽。
- GVLM 没有把图结构只留给下游图模型，而是提前作用到对齐阶段，这一点相对常见的 VLM+GNN 管线更有针对性。
- MAPR 的训练目标不是硬编码规则，而是用各模板的实际 LLM 损失来反推路由后验，设计上贴近“让监督信号自己决定该信哪种模态”。

## Future Work
- 把方法扩展到缺失模态、动态图或边属性更复杂的多模态图，检验其是否仍然需要相同的对齐与路由机制。
- 减少第二阶段三模板训练的计算开销，例如更稀疏的路由训练或先验剪枝，以提升大规模部署可行性。
- 系统比较不同 VLM/LLM 主干、邻域检索策略和 hop 选择对结果的影响，确认收益是否来自 Mario 的核心机制而非特定 backbone 组合。
- 进一步分析路由决策的可解释性，检验它是否真正学到节点级模态偏好，而不是数据集偏置。

## Reading Checklist
- 先核对 GVLM 的拓扑偏置实现：最短路径分桶、注意力插入位置、层数为何 1-2 层就足够。
- 再看 Stage 2 的模板构造细节：1/2-hop 邻域如何筛选、Top-k 是多少、标签作为 exemplar 的拼接形式是什么。
- 重点检查 RQ3/RQ4 的消融表，确认收益到底主要来自图条件对齐、MAPR 路由，还是 LoRA 调优本身。
- 核对 zero-shot 协议和 1.6× 增益的具体定义，确认是否跨数据集、跨图域，还是仅在部分设置成立。

## Core Contributions
- 把多模态图而非孤立图文对明确设为 LLM 推理对象，问题定义更贴近结构化真实世界数据。
- 提出 graph-conditioned VLM，用图拓扑引导的细粒度跨模态对比学习联合优化文本与视觉特征。
- 提出模态自适应的图指令调优与可学习路由机制，为节点及邻域选择更合适的模态视图供 LLM 推理。

## Why Read It
- 它切中“LLM + 多模态 + 图结构”这个当前很活跃但仍缺少清晰范式的交叉问题。
- 方法把表征对齐、图结构利用和 LLM 接口设计拆成两阶段，便于判断真正有效的增益来源。
- 如果你关心 Agent 或复杂系统如何处理多节点、多模态上下文，这里的模态路由思路值得重点核对。

## Risks Or Limits
- 实验细节在提取文本里不完整，尤其是正式指标、完整基线列表、提升幅度分布和显著性，当前难以判断收益是否稳定。
- 训练复杂度偏高：第二阶段对每个样本需要跑三种模板的前反向，作者虽称收敛更快可部分抵消，但完整成本对比提取文本没有充分说明。
- 方法明显依赖图结构质量以及节点都有文本和图像的设定；对缺失模态、弱连接图或动态图的适用性，提取文本没有充分说明。
- 邻域 exemplar 选择、模板构造和路由输入都较多依赖设计选择，是否对不同图域都鲁棒，需要看更细的消融。

## Recommended For
- 关注大语言模型与多模态推理结合的研究者
- 研究图结构、关系推理或知识增强系统的读者
- 需要处理多节点、多模态上下文的 Agent/系统工程师

## Keywords
- 多模态图
- 大语言模型
- 视觉语言模型
- 跨模态对齐
- 图推理
- 指令微调

## Additional Figures

![movies_visual_page1](images/movies_visual_page1.png)

*Figure cue:* Movies

![arts_visual_page1](images/arts_visual_page1.png)

*Figure cue:* Movies

![moviesCLIP_tsne_page1](images/moviesCLIP_tsne_page1.png)

*Figure cue:* Movies – Frozen CLIP

![moviesclip_tuning_tsne_page1](images/moviesclip_tuning_tsne_page1.png)

*Figure cue:* Movies – Frozen CLIP

![moviesmario_tsne_page1](images/moviesmario_tsne_page1.png)

*Figure cue:* Movies – Frozen CLIP

![redditsclip_tsne_page1](images/redditsclip_tsne_page1.png)

*Figure cue:* Movies – Frozen CLIP

![redditsclip_tuning_tsne_page1](images/redditsclip_tuning_tsne_page1.png)


![redditsmario_tsne_page1](images/redditsmario_tsne_page1.png)

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
