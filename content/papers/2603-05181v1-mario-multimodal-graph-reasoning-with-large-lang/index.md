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
summary: 它把多模态推理从孤立图文对推进到带边关系的图结构输入。
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
- 多模态
- 图推理
- 视觉-文本
- 跨模态
- LLM
reading_priority: high
---

# Mario: Multimodal Graph Reasoning with Large Language Models

## TL;DR
它把多模态推理从孤立图文对推进到带边关系的图结构输入。

## 中文摘要
论文把多模态推理问题从孤立的图文对扩展到多模态图，其中节点同时含文本和视觉属性，边提供结构线索。这个问题定义值得关注，因为真实系统里的多模态对象往往天然带关系，不适合继续按独立样本处理。摘要没有充分说明图如何被编码给 LLM、推理流程如何组织，以及相对现有 VLM 或图方法的增益来自哪里。

## Quick Facts
- Paper ID: `2603.05181v1`
- Authors: Yuanfu Sun, Kang Li, Pengkang Guo, Jiajin Liu, Qiaoyu Tan
- Domain: Multimodal
- Published: 2026-03-05T13:49:41Z
- arXiv: [abstract](https://arxiv.org/abs/2603.05181v1)
- PDF: [download](https://arxiv.org/pdf/2603.05181v1.pdf)
- Reading priority: high
- Why this priority: 推荐分在今日列表中最高，且多模态图这一问题定义与结构化多模态系统高度相关，值得优先看建模思路。

## Core Contributions
- 把多模态图推理明确为 LLM 需要处理的目标任务，输入不再是孤立图文对。
- 强调节点同时含文本与视觉属性、边提供结构线索的异构表示。
- 尝试让 LLM 面向带关系的多模态输入进行推理，而不是完全依赖预训练 VLM 的独立编码。

## Why Read It
- 多模态系统开始从单样本理解转向结构化输入，这篇工作切中了这个转折点。
- 如果你关心带关系的图文数据，这比普通图文对任务更接近真实场景。
- 它提供了一个值得跟踪的问题定义，而不只是再做一套图文编码器。

## Risks Or Limits
- 摘要没有充分说明具体图编码、提示设计或模型架构。
- 扩展到大图时的上下文长度与计算成本未说明。','与现有 VLM、图神经网络或检索式方法的比较设置未说明。

## Recommended For
- 多模态结构推理研究者
- 做图文联合表示的工程师
- 关注结构化多模态输入的 agent 团队

## Keywords
- 多模态
- 图推理
- 视觉-文本
- 跨模态
- LLM

## Abstract
Recent advances in large language models (LLMs) have opened new avenues for multimodal reasoning. Yet, most existing methods still rely on pretrained vision-language models (VLMs) to encode image-text pairs in isolation, ignoring the relational structure that real-world multimodal data naturally form. This motivates reasoning on multimodal graphs (MMGs), where each node has textual and visual attributes and edges provide structural cues. Enabling LLM-based reasoning on such heterogeneous multimodal signals while preserving graph topology introduces two key challenges: resolving weak cross-modal consistency and handling heterogeneous modality preference. To address this, we propose Mario, a unified framework that simultaneously resolves the two above challenges and enables effective LLM-based reasoning over MMGs. Mario consists of two innovative stages. Firstly, a graph-conditioned VLM design that jointly refines textual and visual features through fine-grained cross-modal contrastive learning guided by graph topology. Secondly, a modality-adaptive graph instruction tuning mechanism that organizes aligned multimodal features into graph-aware instruction views and employs a learnable router to surface, for each node and its neighborhood, the most informative modality configuration to the LLM. Extensive experiments across diverse MMG benchmarks demonstrate that Mario consistently outperforms state-of-the-art graph models in both supervised and zero-shot scenarios for node classification and link prediction. The code will be made available at https://github.com/sunyuanfu/Mario.

## Recommendation Signals
- Recommendation score: 8.81
- Relevance score: 2.47
- Recency score: 3.0
- Popularity score: 2.3
- Quality score: 2.3
