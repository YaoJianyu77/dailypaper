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
summary: 用可扩展正交变换重参数化，把POET做成更省显存的LLM训练方案。
source_url: https://arxiv.org/abs/2603.05500v1
pdf_url: https://arxiv.org/pdf/2603.05500v1.pdf
scores:
  relevance: 3.8
  recency: 3.0
  popularity: 1.2
  quality: 1.2
  recommendation: 8.67
tags:
- paper-note
status: generated
updated: '2026-03-07'
keywords:
- LLM训练
- 正交变换
- 重参数化
- 显存效率
- 训练稳定性
reading_priority: high
---

# POET-X: Memory-efficient LLM Training by Scaling Orthogonal Transformation

## TL;DR
用可扩展正交变换重参数化，把POET做成更省显存的LLM训练方案。

## 中文摘要
该文围绕POET的正交等价变换训练框架，解决其原始实现矩阵乘法过重、显存与算力开销高的问题。作者提出POET-X，在保留谱不变、训练稳定和泛化收益的前提下降低变换成本。摘要称其可在单张Nvidia H100上完成十亿参数级LLM预训练，而同设置下AdamW会显存溢出。

## Quick Facts
- Paper ID: `2603.05500v1`
- Authors: Zeju Qiu, Lixin Liu, Adrian Weller, Han Shi, Weiyang Liu
- Domain: Large Language Models
- Published: 2026-03-05T18:59:23Z
- arXiv: [abstract](https://arxiv.org/abs/2603.05500v1)
- PDF: [download](https://arxiv.org/pdf/2603.05500v1.pdf)
- Reading priority: high
- Why this priority: 推荐分和相关性都高，且直接命中LLM训练效率与稳定性这条主线。

## Core Contributions
- 把POET从高成本的正交等价训练实现，改造为可扩展、显存更友好的POET-X。
- 在方法目标上同时保留谱保持、训练稳定性与泛化收益，而不是只做工程降本。
- 给出十亿参数级预训练可在单张H100上运行的可行性证据，并与AdamW的显存上限形成对照。

## Why Read It
- 如果你关注优化器与重参数化训练，这是少见直接把稳定性收益和系统成本一起讨论的工作。
- 对受限GPU预算下的大模型预训练很有参考价值。
- 它可能为替代AdamW的训练范式提供新切口。

## Risks Or Limits
- 摘要没有充分说明POET-X的具体变换形式、额外参数规模与实现复杂度。
- 单卡H100结果很吸引人，但跨模型规模、不同并行策略下是否同样成立，摘要未交代。

## Recommended For
- 优化器与训练算法研究者
- 大模型训练基础设施工程师
- 受限算力下做预训练的团队

## Keywords
- LLM训练
- 正交变换
- 重参数化
- 显存效率
- 训练稳定性

## Abstract
Efficient and stable training of large language models (LLMs) remains a core challenge in modern machine learning systems. To address this challenge, Reparameterized Orthogonal Equivalence Training (POET), a spectrum-preserving framework that optimizes each weight matrix through orthogonal equivalence transformation, has been proposed. Although POET provides strong training stability, its original implementation incurs high memory consumption and computational overhead due to intensive matrix multiplications. To overcome these limitations, we introduce POET-X, a scalable and memory-efficient variant that performs orthogonal equivalence transformations with significantly reduced computational cost. POET-X maintains the generalization and stability benefits of POET while achieving substantial improvements in throughput and memory efficiency. In our experiments, POET-X enables the pretraining of billion-parameter LLMs on a single Nvidia H100 GPU, and in contrast, standard optimizers such as AdamW run out of memory under the same settings.

## Recommendation Signals
- Recommendation score: 8.67
- Relevance score: 3.8
- Recency score: 3.0
- Popularity score: 1.2
- Quality score: 1.2
