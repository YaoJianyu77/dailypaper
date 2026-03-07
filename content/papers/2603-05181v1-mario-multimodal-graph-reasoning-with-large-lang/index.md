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
summary: 让LLM在多模态图上推理，不再把图像和文本当作彼此孤立的节点属性。
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
- LLM推理
- 图条件VLM
- 指令微调
- 模态路由
- 链路预测
reading_priority: high
---

# Mario: Multimodal Graph Reasoning with Large Language Models

## TL;DR
让LLM在多模态图上推理，不再把图像和文本当作彼此孤立的节点属性。

## 中文摘要
Mario针对多模态图推理中的两个难点展开：跨模态一致性弱，以及不同节点或邻域对模态偏好不同。其第一阶段用图条件VLM在拓扑引导下做细粒度跨模态对比学习，第二阶段再通过带可学习路由的图指令微调，把更合适的模态配置交给LLM。摘要称，该方法在节点分类和链路预测上，无论监督还是零样本设定，都优于现有图模型。

## Quick Facts
- Paper ID: `2603.05181v1`
- Authors: Yuanfu Sun, Kang Li, Pengkang Guo, Jiajin Liu, Qiaoyu Tan
- Domain: Multimodal
- Published: 2026-03-05T13:49:41Z
- arXiv: [abstract](https://arxiv.org/abs/2603.05181v1)
- PDF: [download](https://arxiv.org/pdf/2603.05181v1.pdf)
- Reading priority: high
- Why this priority: 这是少数把多模态图结构问题明确升级为LLM推理问题的工作，方向契合度高。

## Core Contributions
- 提出图条件VLM，用图拓扑引导跨模态特征对齐。
- 提出带可学习路由的模态自适应图指令微调机制。
- 把LLM真正用于多模态图上的节点分类与链路预测推理。

## Why Read It
- 它把多模态、图结构和LLM三条线真正接到了一起。
- 方法设计具体，不是泛泛地把图特征塞进提示词。
- 如果你做图文知识图谱、社交图或商品图，这篇有较强迁移价值。

## Risks Or Limits
- 摘要没有充分说明图规模扩展性、训练成本和推理时延。
- 性能提升来自摘要总结，但不同模块各自贡献仍不清楚。","对视觉质量较差或文本噪声较大的节点是否稳健，摘要没有充分说明。

## Recommended For
- 多模态推理研究者
- 图学习研究者
- LLM应用团队

## Keywords
- 多模态图
- LLM推理
- 图条件VLM
- 指令微调
- 模态路由
- 链路预测

## Abstract
Recent advances in large language models (LLMs) have opened new avenues for multimodal reasoning. Yet, most existing methods still rely on pretrained vision-language models (VLMs) to encode image-text pairs in isolation, ignoring the relational structure that real-world multimodal data naturally form. This motivates reasoning on multimodal graphs (MMGs), where each node has textual and visual attributes and edges provide structural cues. Enabling LLM-based reasoning on such heterogeneous multimodal signals while preserving graph topology introduces two key challenges: resolving weak cross-modal consistency and handling heterogeneous modality preference. To address this, we propose Mario, a unified framework that simultaneously resolves the two above challenges and enables effective LLM-based reasoning over MMGs. Mario consists of two innovative stages. Firstly, a graph-conditioned VLM design that jointly refines textual and visual features through fine-grained cross-modal contrastive learning guided by graph topology. Secondly, a modality-adaptive graph instruction tuning mechanism that organizes aligned multimodal features into graph-aware instruction views and employs a learnable router to surface, for each node and its neighborhood, the most informative modality configuration to the LLM. Extensive experiments across diverse MMG benchmarks demonstrate that Mario consistently outperforms state-of-the-art graph models in both supervised and zero-shot scenarios for node classification and link prediction. The code will be made available at https://github.com/sunyuanfu/Mario.

## Recommendation Signals
- Recommendation score: 8.27
- Relevance score: 2.4
- Recency score: 3.0
- Popularity score: 2.3
- Quality score: 2.3
