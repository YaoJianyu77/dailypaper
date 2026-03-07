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
summary: 这篇论文值得看的是它把多模态推理从孤立图文编码推进到带结构关系的多模态图场景。
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
- 大语言模型
- 视觉语言
- 结构化推理
reading_priority: high
image_count: 5
---

# Mario: Multimodal Graph Reasoning with Large Language Models

## TL;DR
这篇论文值得看的是它把多模态推理从孤立图文编码推进到带结构关系的多模态图场景。

## 中文摘要
论文关注带有图像、文本属性和边结构的多模态图推理，切入点比常见的图文对建模更接近真实世界数据组织方式。按摘要描述，作者试图让大语言模型在异构多模态图上进行推理，而不是只依赖预训练视觉语言模型分别编码图文对。这个问题设定本身有研究价值，但摘要被截断，具体框架、任务设置和效果证据都没有充分展开。

## Quick Facts
- Paper ID: `2603.05181v1`
- Authors: Yuanfu Sun, Kang Li, Pengkang Guo, Jiajin Liu, Qiaoyu Tan
- Domain: Multimodal
- Published: 2026-03-05T13:49:41Z
- arXiv: [abstract](https://arxiv.org/abs/2603.05181v1)
- PDF: [download](https://arxiv.org/pdf/2603.05181v1.pdf)
- Reading priority: high
- Why this priority: 问题设定新，且直接对接多模态与LLM主线；虽然摘要信息不完整，但值得优先核对其结构表示与实证是否站得住。

## Problem Framing
问题是现有多模态方法多把图像和文本成对独立编码，忽略了真实数据中的节点关系与图结构，因此难以处理多模态图上的结构化推理。

## Approach Snapshot
方法方向是让大语言模型面向多模态图进行推理，利用节点的文本与视觉属性以及边提供的结构线索；但摘要没有充分说明具体如何表示图、如何接入LLM、以及是否引入额外模块。

## Evidence Mentioned In Abstract
摘要只给出了问题动机和方法方向，即多模态图比孤立图文对更适合表达真实关系结构；但没有在已给内容中说明实验任务、对比基线、指标或定量结果，摘要没有充分说明。

## Reading Checklist
- 图结构、图像特征和文本特征最终是如何统一到LLM输入或中间表示中的？
- 实验是否覆盖真正需要关系推理的任务，而不只是图文匹配或分类任务的改写？
- 相比现有VLM或图模型，性能收益与计算开销分别是多少？

## Core Contributions
- 把研究对象从图文对扩展到带节点属性和边关系的多模态图。
- 尝试让LLM承担异构多模态图上的推理角色，而不是仅把LLM放在文本后处理位置。
- 明确指出现有多模态方法忽略关系结构这一建模缺口。

## Why Read It
- 如果你关心多模态Agent或复杂环境建模，这类结构化输入是更现实的方向。
- 它讨论的是问题定义层面的扩展，不只是给现有图文流水线再加一个模块。
- 对多模态推理是否需要显式结构表示，这篇会提供直接信号。

## Risks Or Limits
- 摘要截断严重，核心机制和实验证据都不完整。
- 多模态图任务容易因为数据构造方式而高估方法价值，需要核对任务难度。

## Recommended For
- 关注多模态推理、图结构建模与LLM结合的研究者
- 在做复杂环境感知、知识图谱结合多模态系统的工程师

## Keywords
- 多模态
- 图推理
- 大语言模型
- 视觉语言
- 结构化推理

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
