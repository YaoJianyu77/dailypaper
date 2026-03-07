---
paper_id: 2603.05500v1
title: 'POET-X: Memory-efficient LLM Training by Scaling Orthogonal Transformation'
authors:
- Zeju Qiu
- Lixin Liu
- Adrian Weller
- Han Shi
- Weiyang Liu
domain: Large Language Models
slug: 2603-05500v1-poet-x-memory-efficient-llm-training-by-scaling
published: '2026-03-05T18:59:23Z'
summary: 核心目标是把正交等价训练的稳定性思路变得更省内存、更接近可扩展训练。
source_url: https://arxiv.org/abs/2603.05500v1
pdf_url: https://arxiv.org/pdf/2603.05500v1.pdf
scores:
  relevance: 3.0
  recency: 3.0
  popularity: 1.2
  quality: 1.2
  recommendation: 8.2
tags:
- paper-note
status: generated
updated: '2026-03-07'
keywords:
- LLM 训练
- 内存效率
- 正交变换
- 稳定训练
- 重参数化
reading_priority: medium
---

# POET-X: Memory-efficient LLM Training by Scaling Orthogonal Transformation

## TL;DR
核心目标是把正交等价训练的稳定性思路变得更省内存、更接近可扩展训练。

## 中文摘要
这篇工作面向 LLM 训练中的稳定性与资源开销矛盾，试图把 POET 的正交等价变换做得更省内存。如果它能在保留谱保持性质的同时降低矩阵运算负担，就有机会把原本成本较高的稳定训练思路推进到更实用的训练设置。摘要没有充分说明缩放正交变换的具体实现、额外算子成本，以及在大规模训练中的真实收益边界。

## Quick Facts
- Paper ID: `2603.05500v1`
- Authors: Zeju Qiu, Lixin Liu, Adrian Weller, Han Shi, Weiyang Liu
- Domain: Large Language Models
- Published: 2026-03-05T18:59:23Z
- arXiv: [abstract](https://arxiv.org/abs/2603.05500v1)
- PDF: [download](https://arxiv.org/pdf/2603.05500v1.pdf)
- Reading priority: medium
- Why this priority: 训练端价值明确，但方法更专用，且摘要没有充分说明实现与收益边界，适合第二梯队阅读。

## Core Contributions
- 面向 POET 的高内存和高计算开销提出更可扩展的训练变体。
- 延续正交等价变换与谱保持这一稳定性思路。
- 把训练稳定性方法推进到更关注系统资源成本的方向。

## Why Read It
- 训练稳定性与显存成本是大模型训练里的硬约束。
- 如果这类重参数化方法能降到可承受成本，可能影响训练 recipe 设计。
- 适合判断正交或谱约束类方法是否开始从理论兴趣走向工程可用。

## Risks Or Limits
- 摘要没有充分说明内存节省来自何处，是否引入新的算子或通信负担。
- 与标准优化器或现有稳定训练技巧的兼容性未说明。','实际适用模型规模、序列长度和分布式场景没有交代。

## Recommended For
- 做大模型预训练基础设施的工程师
- 关注稳定训练与参数化方法的研究者
- 需要控制显存成本的训练团队

## Keywords
- LLM 训练
- 内存效率
- 正交变换
- 稳定训练
- 重参数化

## Abstract
Efficient and stable training of large language models (LLMs) remains a core challenge in modern machine learning systems. To address this challenge, Reparameterized Orthogonal Equivalence Training (POET), a spectrum-preserving framework that optimizes each weight matrix through orthogonal equivalence transformation, has been proposed. Although POET provides strong training stability, its original implementation incurs high memory consumption and computational overhead due to intensive matrix multiplications. To overcome these limitations, we introduce POET-X, a scalable and memory-efficient variant that performs orthogonal equivalence transformations with significantly reduced computational cost. POET-X maintains the generalization and stability benefits of POET while achieving substantial improvements in throughput and memory efficiency. In our experiments, POET-X enables the pretraining of billion-parameter LLMs on a single Nvidia H100 GPU, and in contrast, standard optimizers such as AdamW run out of memory under the same settings.

## Recommendation Signals
- Recommendation score: 8.2
- Relevance score: 3.0
- Recency score: 3.0
- Popularity score: 1.2
- Quality score: 1.2
