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
summary: 如果摘要中的结论成立，这项工作把“稳定但昂贵”的正交等价训练推进到了更接近真实大模型预训练约束的实现形态。
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
venue_or_journal: Technical report
citation_summary: Citation count unavailable
keywords:
- 大语言模型训练
- 内存效率
- 正交等价变换
- 谱保持训练
- 训练稳定性
- 预训练优化
reading_priority: high
image_count: 8
---

# POET-X: Memory-efficient LLM Training by Scaling Orthogonal Transformation

## TL;DR
如果摘要中的结论成立，这项工作把“稳定但昂贵”的正交等价训练推进到了更接近真实大模型预训练约束的实现形态。

## 中文摘要
这篇工作针对 POET 在大模型训练中稳定但昂贵的问题，提出更可扩展、更省显存的变体 POET-X，继续通过正交等价变换处理权重矩阵，同时降低原方法带来的计算与内存负担。摘要声称它在保留 POET 泛化与稳定性收益的同时，显著提升吞吐和显存效率，并可在单张 Nvidia H100 上完成十亿参数级 LLM 预训练。值得读的点在于它试图把谱保持式训练方法从“理论上有吸引力”推进到“系统上可用”，但摘要没有充分说明具体机制细节、对比公平性和适用边界。

## Quick Facts
- Paper ID: `2603.05500v1`
- Authors: Zeju Qiu, Lixin Liu, Adrian Weller, Han Shi, Weiyang Liu
- Institutions: Institution information not extracted
- Domain: Large Language Models
- Venue / Journal: Technical report
- Citations: Citation count unavailable
- Published: 2026-03-05T18:59:23Z
- arXiv: [abstract](https://arxiv.org/abs/2603.05500v1)
- PDF: [download](https://arxiv.org/pdf/2603.05500v1.pdf)
- Reading priority: high
- Why this priority: 它与大模型训练这一核心方向高度对齐，摘要给出了“单张 H100 预训练十亿参数模型、AdamW 同设定下 OOM”的强工程信号，具备较高现实价值。虽然摘要没有充分说明细节与边界，但正因为方法新意和潜在影响都集中在训练系统层面，这篇论文值得优先核对。

## Research Background And Motivation
大模型预训练越来越受限于显存、吞吐和训练稳定性，很多看起来有理论吸引力的训练方法最终卡在系统成本上。POET 这类保持谱性质的训练框架提供了稳定性方向，但如果额外矩阵运算过重，就很难真正进入大规模 LLM 训练流程。

## Problem Framing
这篇论文要解决的问题是：能否在不丢掉 POET 所强调的稳定性与泛化收益的前提下，把它的高内存、高计算开销压缩到足以支持大规模 LLM 预训练的程度。这很关键，因为训练方法只有在系统开销可控时，才可能从“更稳的想法”变成“可部署的训练方案”。

## Method Overview
作者提出 POET-X，作为 POET 的可扩展、内存高效变体，仍以正交等价变换为核心来优化权重矩阵，但重点是以显著更低的计算成本完成这一步。按摘要表述，它的核心改动不是换一个训练目标，而是把原本由密集矩阵乘法带来的系统负担降下来，使该框架更适合大模型预训练。

### Method Figure
![cnp-crop_page1](images/cnp-crop_page1.png)


## Experimental Setup And Evidence
摘要给出的证据主要是实验性主张：POET-X 在保持 POET 泛化与稳定性收益的同时，提高了吞吐和显存效率，并能在单张 Nvidia H100 上预训练十亿参数级 LLM，而同样设置下 AdamW 会显存溢出。摘要没有充分说明具体实验配置、提升幅度、收敛质量、评测任务，以及这种优势在不同模型规模和硬件条件下是否稳定成立。

### Experiment Figure
![memory_breakdown_page1](images/memory_breakdown_page1.png)


## Research Or Engineering Value
如果这些结论成立，这项工作意味着某些原本因成本过高而难以落地的稳定训练思想，可能被带入真实的大模型预训练流程。对研究者，它提供了把正交/谱保持结构与大规模训练结合的实证路线；对工程侧，它指向在固定显存预算下训练更大模型或提升训练吞吐的可能性。

## Reading Checklist
- POET-X 具体通过什么机制降低正交等价变换的计算与显存开销，这种改动是否改变了原始 POET 的数学性质或优化行为？
- 摘要所说“保持泛化与稳定性收益”是通过哪些任务、曲线或对比得到的，是否覆盖不同模型规模与训练阶段？
- 与 AdamW 的对比是否控制了 batch size、序列长度、激活检查点等系统因素，单卡 H100 的结果能否迁移到多卡或不同硬件环境？

## Core Contributions
- 把原本高开销的 POET 框架推进为更可扩展、内存更高效的 POET-X，使其更接近可用于大模型预训练的实现。
- 直接针对 POET 的显存与吞吐瓶颈做系统级改造，核心目标是降低正交等价变换带来的密集矩阵乘法成本。
- 给出单张 Nvidia H100 上预训练十亿参数级 LLM 的可行性主张，并以 AdamW 在同设定下显存溢出作为强对照信号。

## Why Read It
- 现在值得读，因为大模型训练成本重新成为方法筛选门槛，任何能同时改善稳定性和显存效率的训练框架都具有现实价值。
- 这篇工作的重点不是泛泛提出新优化器，而是把“谱保持的稳定训练”推到可扩展实现，问题定义本身有方法论意义。
- 如果你关注单机或受限显存条件下的大模型预训练，它提供了一个可能比标准 AdamW 更有内存优势的方向。

## Risks Or Limits
- 摘要没有充分说明 POET-X 的具体实现机制，因此目前难判断收益主要来自数学改动、工程实现，还是特定硬件设置。
- 与 AdamW 的比较只给出“同设定下 OOM”这一强信号，但缺少更细的公平性信息，结论可能受 batch、长度和并行策略影响。

## Recommended For
- 研究 LLM 预训练优化器、参数化方法和训练稳定性的研究者
- 关注单机或受限显存条件下训练大模型的工程师
- 想评估正交/谱保持训练方法是否能实际落地的人

## Keywords
- 大语言模型训练
- 内存效率
- 正交等价变换
- 谱保持训练
- 训练稳定性
- 预训练优化

## Additional Figures

![linear_breakdown_page1](images/linear_breakdown_page1.png)


![matrix_coverage_new_page1](images/matrix_coverage_new_page1.png)


![throughput_scale_page1](images/throughput_scale_page1.png)


![throughput_scale_v3_page1](images/throughput_scale_v3_page1.png)


![val_ppl_1024_page1](images/val_ppl_1024_page1.png)


![val_ppl_256_page1](images/val_ppl_256_page1.png)

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
