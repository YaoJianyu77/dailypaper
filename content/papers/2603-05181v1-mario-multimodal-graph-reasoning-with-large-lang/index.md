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
summary: 让LLM在带图结构的图文节点上做统一多模态推理。
source_url: https://arxiv.org/abs/2603.05181v1
pdf_url: https://arxiv.org/pdf/2603.05181v1.pdf
scores:
  relevance: 2.4
  recency: 3.0
  popularity: 2.3
  quality: 2.3
  recommendation: 8.27
tags:
- paper-note
status: generated
updated: '2026-03-07'
keywords:
- 多模态图
- 图推理
- LLM
- 视觉语言模型
- 指令微调
reading_priority: high
---

# Mario: Multimodal Graph Reasoning with Large Language Models

## TL;DR
让LLM在带图结构的图文节点上做统一多模态推理。

## 中文摘要
Mario把多模态推理对象从独立图文对扩展到多模态图，其中节点同时含文本和视觉属性、边提供结构线索。作者针对跨模态一致性弱和模态偏好异质两个难点，设计了两阶段框架：先用图条件VLM在拓扑指导下做细粒度跨模态对比学习，再做模态自适应的图指令微调。摘要显示其核心价值是把对齐后的多模态特征组织成图感知指令视图，但具体训练目标与评测任务被截断，摘要没有充分说明。

## Quick Facts
- Paper ID: `2603.05181v1`
- Authors: Yuanfu Sun, Kang Li, Pengkang Guo, Jiajin Liu, Qiaoyu Tan
- Domain: Multimodal
- Published: 2026-03-05T13:49:41Z
- arXiv: [abstract](https://arxiv.org/abs/2603.05181v1)
- PDF: [download](https://arxiv.org/pdf/2603.05181v1.pdf)
- Reading priority: high
- Why this priority: 直接落在多模态核心方向，而且问题设定和方法结构都具备新意。

## Core Contributions
- 把LLM推理对象提升为多模态图，而不是孤立的图文样本。
- 提出graph-conditioned VLM，用图拓扑引导文本与视觉特征对齐。
- 提出modality-adaptive graph instruction tuning，使不同模态偏好在图结构任务中可被动态利用。

## Why Read It
- 对多模态与图学习交叉方向而言，这篇论文的问题设定本身就很值得关注。
- 它不再默认视觉和文本贡献对称，而是把“模态偏好”作为一等公民来处理。
- 如果你在做图RAG、场景图推理或多模态Agent，方法结构有启发性。

## Risks Or Limits
- 摘要没有充分说明支持的任务类型、图规模上限和训练/推理成本。
- 两阶段方案可能引入较高训练复杂度，尤其在大图或高分辨率视觉输入下。

## Recommended For
- 多模态图研究者
- LLM推理团队
- 图结构VLM研究者

## Keywords
- 多模态图
- 图推理
- LLM
- 视觉语言模型
- 指令微调

## Abstract
Recent advances in large language models (LLMs) have opened new avenues for multimodal reasoning. Yet, most existing methods still rely on pretrained vision-language models (VLMs) to encode image-text pairs in isolation, ignoring the relational structure that real-world multimodal data naturally form. This motivates reasoning on multimodal graphs (MMGs), where each node has textual and visual attributes and edges provide structural cues. Enabling LLM-based reasoning on such heterogeneous multimodal signals while preserving graph topology introduces two key challenges: resolving weak cross-modal consistency and handling heterogeneous modality preference. To address this, we propose Mario, a unified framework that simultaneously resolves the two above challenges and enables effective LLM-based reasoning over MMGs. Mario consists of two innovative stages. Firstly, a graph-conditioned VLM design that jointly refines textual and visual features through fine-grained cross-modal contrastive learning guided by graph topology. Secondly, a modality-adaptive graph instruction tuning mechanism that organizes aligned multimodal features into graph-aware instruction views and employs a learnable router to surface, for each node and its neighborhood, the most informative modality configuration to the LLM. Extensive experiments across diverse MMG benchmarks demonstrate that Mario consistently outperforms state-of-the-art graph models in both supervised and zero-shot scenarios for node classification and link prediction. The code will be made available at https://github.com/sunyuanfu/Mario.

## Recommendation Signals
- Recommendation score: 8.27
- Relevance score: 2.4
- Recency score: 3.0
- Popularity score: 2.3
- Quality score: 2.3
