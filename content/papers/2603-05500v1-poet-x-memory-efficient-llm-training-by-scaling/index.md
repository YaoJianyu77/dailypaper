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
summary: 这篇工作把 POET 的稳定训练路线从“理论上有吸引力”推进到“单卡也可能跑得动”的工程形态。
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
- 正交等价变换
- POET-X
- 训练稳定性
reading_priority: high
image_count: 5
---

# POET-X: Memory-efficient LLM Training by Scaling Orthogonal Transformation

## TL;DR
这篇工作把 POET 的稳定训练路线从“理论上有吸引力”推进到“单卡也可能跑得动”的工程形态。

## 中文摘要
POET-X 是对 POET 的系统级改造版，目标是在保留谱保持和训练稳定性优势的同时，大幅降低内存与计算开销。摘要称它能显著改善吞吐和显存效率，并支持在单张 H100 上预训练十亿参数 LLM，而同设定下 AdamW 会直接爆显存。真正值得核对的是它是否在不同规模和任务上都保住了训练质量，因为这些细节摘要没有充分说明。

## Quick Facts
- Paper ID: `2603.05500v1`
- Authors: Zeju Qiu, Lixin Liu, Adrian Weller, Han Shi, Weiyang Liu
- Domain: Large Language Models
- Published: 2026-03-05T18:59:23Z
- arXiv: [abstract](https://arxiv.org/abs/2603.05500v1)
- PDF: [download](https://arxiv.org/pdf/2603.05500v1.pdf)
- Reading priority: high
- Why this priority: 工程价值直接，且摘要给出明确硬件对比；但仍需核对它是否真正保住了训练质量和可迁移性。

## Research Background And Motivation
大模型训练的一个长期难点是同时兼顾稳定性、内存和吞吐。POET 这类保持谱性质的训练框架提供了稳定性思路，但原始实现的矩阵乘法开销太重。

## Problem Framing
问题是如何保留 POET 的稳定训练与泛化优势，同时把其高内存、高计算成本降到足以支撑更大规模 LLM 预训练。这个问题重要，因为很多“更稳的训练方法”最终都卡在系统成本上。

## Approach Snapshot
POET-X 将正交等价变换做成更可扩展、更省内存的版本，以更低成本完成原本昂贵的矩阵操作。核心卖点不是改变目标，而是把原方法从难以扩展的实现改造成可用于十亿参数级训练的系统化方案。

## Evidence Mentioned In Abstract
摘要声称 POET-X 在保持 POET 泛化和稳定性收益的同时，显著提升吞吐和显存效率，并能在单张 Nvidia H100 上预训练十亿参数 LLM；同设定下 AdamW 会因显存不足失败。具体训练预算、收敛速度、最终质量指标和不同模型规模下的趋势摘要没有充分说明。

## Research Or Engineering Value
如果成立，这项工作会降低大模型训练实验的硬件门槛，让单卡或小规模环境也能测试更大模型与更稳的优化路径。它也可能让“结构化重参数化训练”从理论兴趣点变成可实际采用的工程选项。

## Reading Checklist
- POET-X 具体如何降低正交等价变换的成本，复杂度相对原版降了多少？
- 在同等训练 token、步数和最终质量下，它与 AdamW 的真实成本收益比是多少？
- 所谓保留泛化和稳定性优势，是否覆盖不同模型规模、数据配方和下游任务？

## Core Contributions
- 提出 POET 的可扩展变体 POET-X，专门解决原方法的高显存和高计算瓶颈。
- 在不改变核心稳定训练动机的前提下，重新设计正交等价变换的执行方式。
- 给出单张 H100 预训练十亿参数 LLM 的可行性主张，并以 AdamW 显存不足作为对照。

## Why Read It
- 训练效率论文里少见同时抓稳定性和显存，切入点比常规优化器微调更有结构性。
- 单卡十亿参数的主张很硬，值得核对实现细节和真实边界。
- 如果你关心更稳的预训练，这篇论文提供了一个不同于 AdamW 路线的选择。

## Risks Or Limits
- 摘要没有给出最终模型质量与训练步数的完整对照，不能只看能不能跑。
- 收益可能依赖特定硬件和实现优化，换设备后未必成立。

## Recommended For
- 做大模型预训练系统与优化器研究的读者
- 资源受限但想跑更大模型的工程师
- 关注训练稳定性与参数化方法的研究者

## Keywords
- LLM 训练
- 内存效率
- 正交等价变换
- POET-X
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
