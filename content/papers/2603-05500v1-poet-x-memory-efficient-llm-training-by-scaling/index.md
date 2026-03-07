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
summary: 通过缩放正交变换重写POET，把LLM训练的显存和计算开销压到更可部署的水平。
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
- 内存效率
- 正交变换
- POET
- 训练稳定性
- 单卡预训练
reading_priority: high
---

# POET-X: Memory-efficient LLM Training by Scaling Orthogonal Transformation

## TL;DR
通过缩放正交变换重写POET，把LLM训练的显存和计算开销压到更可部署的水平。

## 中文摘要
论文从POET的正交等价变换出发，提出更可扩展、显存更友好的POET-X，以降低原方法大量矩阵乘法带来的负担。摘要称，该方法在保持POET泛化性与训练稳定性的同时，显著提升吞吐并改善内存效率。作者进一步给出一个强工程信号：十亿参数级LLM可在单张Nvidia H100上完成预训练，而同设定下AdamW会因显存不足失败。

## Quick Facts
- Paper ID: `2603.05500v1`
- Authors: Zeju Qiu, Lixin Liu, Adrian Weller, Han Shi, Weiyang Liu
- Domain: Large Language Models
- Published: 2026-03-05T18:59:23Z
- arXiv: [abstract](https://arxiv.org/abs/2603.05500v1)
- PDF: [download](https://arxiv.org/pdf/2603.05500v1.pdf)
- Reading priority: high
- Why this priority: 同时命中LLM训练稳定性和显存效率两个核心问题，且摘要给出了单卡H100预训练这一强部署信号。

## Core Contributions
- 提出POET-X，在POET框架内以更低成本执行正交等价变换。
- 把训练稳定性与泛化收益保留下来，同时改善吞吐与显存占用。
- 将方法落到十亿参数级LLM预训练场景，强调单卡可训练性。

## Why Read It
- 如果你在意大模型训练的显存墙，这是少见直接对优化器或重参数化方案动刀的工作。
- 它不是单纯追求更快，而是把稳定训练和硬件可达性放在一起考虑。
- 适合与AdamW、低内存优化器和其他训练稳定化路线做横向比较。

## Risks Or Limits
- 摘要没有充分说明缩放正交变换的具体实现细节和额外工程复杂度。
- 单卡H100结论很强，但摘要没有充分说明任务规模、序列长度和批大小等前提。","泛化收益主要来自摘要表述，跨模型族或下游任务的边界仍不清楚。

## Recommended For
- LLM训练系统研究者
- 优化器与重参数化方向研究者
- 资源受限的预训练工程团队

## Keywords
- LLM训练
- 内存效率
- 正交变换
- POET
- 训练稳定性
- 单卡预训练

## Abstract
Efficient and stable training of large language models (LLMs) remains a core challenge in modern machine learning systems. To address this challenge, Reparameterized Orthogonal Equivalence Training (POET), a spectrum-preserving framework that optimizes each weight matrix through orthogonal equivalence transformation, has been proposed. Although POET provides strong training stability, its original implementation incurs high memory consumption and computational overhead due to intensive matrix multiplications. To overcome these limitations, we introduce POET-X, a scalable and memory-efficient variant that performs orthogonal equivalence transformations with significantly reduced computational cost. POET-X maintains the generalization and stability benefits of POET while achieving substantial improvements in throughput and memory efficiency. In our experiments, POET-X enables the pretraining of billion-parameter LLMs on a single Nvidia H100 GPU, and in contrast, standard optimizers such as AdamW run out of memory under the same settings.

## Recommendation Signals
- Recommendation score: 8.67
- Relevance score: 3.8
- Recency score: 3.0
- Popularity score: 1.2
- Quality score: 1.2
