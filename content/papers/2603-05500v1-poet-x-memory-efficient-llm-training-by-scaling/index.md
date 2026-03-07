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
summary: 这篇论文关注的是把POET这类稳定训练思路做得更省显存、更可落地。
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
- 大语言模型训练
- 内存效率
- 正交变换
- 重参数化
- 训练稳定性
reading_priority: medium
image_count: 5
---

# POET-X: Memory-efficient LLM Training by Scaling Orthogonal Transformation

## TL;DR
这篇论文关注的是把POET这类稳定训练思路做得更省显存、更可落地。

## 中文摘要
论文围绕大模型训练中的稳定性与资源开销矛盾展开，目标是改进POET原始实现的高内存和高计算负担。按摘要可知，作者基于正交等价变换这一谱保持框架继续做扩展，标题表明重点在于通过缩放正交变换提升内存效率。这个方向对大模型训练工程有价值，但摘要没有充分说明具体复杂度改进、适用模型规模和稳定性收益是否保留。

## Quick Facts
- Paper ID: `2603.05500v1`
- Authors: Zeju Qiu, Lixin Liu, Adrian Weller, Han Shi, Weiyang Liu
- Domain: Large Language Models
- Published: 2026-03-05T18:59:23Z
- arXiv: [abstract](https://arxiv.org/abs/2603.05500v1)
- PDF: [download](https://arxiv.org/pdf/2603.05500v1.pdf)
- Reading priority: medium
- Why this priority: 工程价值明确，也契合大模型主线，但摘要对算法与实验展开不足，优先级略低于问题定义更新的两篇。

## Problem Framing
问题是原始POET虽然有训练稳定性优势，但矩阵操作带来的显存占用和计算开销较高，不利于大规模训练落地。

## Approach Snapshot
方法是在POET的正交等价重参数化框架上做内存效率优化，标题显示核心手段与正交变换的缩放有关；但摘要没有充分说明算法细节、额外参数开销和实现方式。

## Evidence Mentioned In Abstract
摘要提供的证据是POET已有稳定性优势，以及原始实现存在高内存和高计算成本这一明确瓶颈；但在已给内容中，没有看到任何训练规模、显存节省比例或收敛表现，摘要没有充分说明。

## Reading Checklist
- 所谓缩放正交变换具体改了哪些矩阵操作，复杂度从什么量级降到什么量级？
- 在降低内存占用后，原本POET的训练稳定性和谱保持性质是否仍然成立？
- 方法对不同架构和不同并行训练设置是否都适用？

## Core Contributions
- 把关注点放在POET落地的系统瓶颈，而不是只讨论理论稳定性。
- 尝试在保留正交等价训练思想的前提下降低内存与计算成本。
- 为大模型训练中的“稳定但太贵”这一常见矛盾提供了具体改进方向。

## Why Read It
- 如果你关心大模型训练系统，这类方法直接关系到可训练规模和成本。
- 它不是泛泛的优化器改动，而是针对一种已有稳定训练框架做工程化推进。
- 读这篇可以帮助判断正交约束类方法是否有真正的实用化路径。

## Risks Or Limits
- 摘要没有说明收益是否来自真实算法改进，还是仅来自特定实现技巧。
- 这类重参数化方法可能引入额外复杂性，部署和维护成本未说明。

## Recommended For
- 关注大模型训练稳定性、显存优化和系统效率的研究者
- 负责预训练或持续训练基础设施的工程师

## Keywords
- 大语言模型训练
- 内存效率
- 正交变换
- 重参数化
- 训练稳定性

## Figures
![cnp-crop_page1](images/cnp-crop_page1.png)

![linear_breakdown_page1](images/linear_breakdown_page1.png)

![matrix_coverage_new_page1](images/matrix_coverage_new_page1.png)

![memory_breakdown_page1](images/memory_breakdown_page1.png)

![throughput_scale_page1](images/throughput_scale_page1.png)

- Full asset manifest: [images/index.md](images/index.md)

## Abstract
Efficient and stable training of large language models (LLMs) remains a core challenge in modern machine learning systems. To address this challenge, Reparameterized Orthogonal Equivalence Training (POET), a spectrum-preserving framework that optimizes each weight matrix through orthogonal equivalence transformation, has been proposed. Although POET provides strong training stability, its original implementation incurs high memory consumption and computational overhead due to intensive matrix multiplications. To overcome these limitations, we introduce POET-X, a scalable and memory-efficient variant that performs orthogonal equivalence transformations with significantly reduced computational cost. POET-X maintains the generalization and stability benefits of POET while achieving substantial improvements in throughput and memory efficiency. In our experiments, POET-X enables the pretraining of billion-parameter LLMs on a single Nvidia H100 GPU, and in contrast, standard optimizers such as AdamW run out of memory under the same settings.

## Recommendation Signals
- Recommendation score: 8.2
- Relevance score: 3.0
- Recency score: 3.0
- Popularity score: 1.2
- Quality score: 1.2

## Assets
- Extracted assets are stored in the `images/` folder next to this page.
- Browse the image manifest here: [images/index.md](images/index.md)
