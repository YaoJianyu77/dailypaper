---
paper_id: dblp:conf/mlsys/0015LCKCW24
title: 'Q-Hitter: A Better Token Oracle for Efficient LLM Inference via Sparse-Quantized
  KV Cache.'
authors:
- Zhenyu Zhang 0015
- Shiwei Liu 0003
- Runjin Chen
- Bhavya Kailkhura
- Beidi Chen
- Atlas Wang
domain: LLM Inference Systems
slug: dblp-conf-mlsys-0015lckcw24-q-hitter-a-better-token-oracle-for-efficient-llm
published: '2024'
summary: 这项工作把KV cache的稀疏保留与低比特量化联合建模，核心点是优先保留既关键又更适合量化的token，而不是只按注意力分数做选择。
source_url: https://proceedings.mlsys.org/paper_files/paper/2024/hash/bbb7506579431a85861a05fff048d3e1-Abstract-Conference.html
pdf_url: https://proceedings.mlsys.org/paper_files/paper/2024/hash/bbb7506579431a85861a05fff048d3e1-Paper-Conference.pdf
scores:
  relevance: 3.0
  recency: 0.0
  popularity: 2.0
  quality: 2.0
  recommendation: 7.97
tags:
- paper-note
status: generated
updated: '2026-03-08'
venue_or_journal: MLSys
citation_summary: Citation count unavailable
keywords:
- LLM推理
- KV cache
- 稀疏化
- 低比特量化
- Heavy Hitter
- 长上下文
reading_priority: high
analysis_priority_rank: 4
selected_for_full_analysis: false
---

# Q-Hitter: A Better Token Oracle for Efficient LLM Inference via Sparse-Quantized KV Cache.

## TL;DR
这项工作把KV cache的稀疏保留与低比特量化联合建模，核心点是优先保留既关键又更适合量化的token，而不是只按注意力分数做选择。

## 中文摘要
这篇论文关注长上下文LLM推理中的KV cache显存占用和带宽开销，核心观点是稀疏化与量化不能简单串接。作者指出，低比特量化会破坏基于累计注意力的Heavy Hitter选择，且被选中的关键token并不一定适合量化，因此提出同时考虑注意力重要性与“量化友好度”的Q-Hitter规则。对做LLM serving的人来说，这个思路的价值在于把token选择从单一重要性指标扩展为面向实际压缩路径的联合准则，但给定摘要没有充分说明具体吞吐、延迟、精度和硬件结果。

## Quick Facts
- Paper ID: `dblp:conf/mlsys/0015LCKCW24`
- Authors: Zhenyu Zhang 0015, Shiwei Liu 0003, Runjin Chen, Bhavya Kailkhura, Beidi Chen, Atlas Wang
- Institutions: Institution information not extracted
- Domain: LLM Inference Systems
- Venue / Journal: MLSys
- Citations: Citation count unavailable
- Published: 2024
- Source page: [open](https://proceedings.mlsys.org/paper_files/paper/2024/hash/bbb7506579431a85861a05fff048d3e1-Abstract-Conference.html)
- PDF: [download](https://proceedings.mlsys.org/paper_files/paper/2024/hash/bbb7506579431a85861a05fff048d3e1-Paper-Conference.pdf)
- Reading priority: high
- Why this priority: 主题与当前LLM inference systems主线高度一致，直接围绕KV cache的显存和带宽成本展开，并提出了稀疏化/量化耦合这一值得核实的系统问题。虽然给定摘要没有充分说明硬件设置和最终性能结果，但仍值得优先阅读全文确认其吞吐与精度证据。

## Research Background And Motivation
随着LLM上下文长度增长，KV cache逐渐成为推理阶段最直接的显存和带宽瓶颈，尤其影响长序列生成的可部署性。已有工作分别尝试做token级稀疏保留和低比特量化，但两者联用时的相互作用并不清楚，这正是该工作的动机。

## Problem Framing
论文要解决的问题是：在不明显破坏模型效果的前提下，如何同时利用KV cache稀疏化和低比特量化来降低LLM推理成本，并避免二者简单叠加后出现的选择失真。更具体地说，作者关心的是生成阶段该保留哪些token的KV，以及这些token是否真的适合被量化。

## Method Overview
作者从Heavy Hitter式token保留规则出发，先指出仅按累计注意力分数选token再做低比特量化会出问题，然后提出Q-Hitter作为新的经验性选择规则。其核心机制是把token的重要性与分层的“Quantization Friendliness”联合考虑，优先保留那些既对生成关键、又更适合低比特KV量化的token。

## Experimental Setup And Evidence
给定摘要提供的证据主要是问题诊断而不是完整结果：作者声称在<=4-bit场景下，后置量化会降低Heavy Hitter选择准确性，且深层更明显，同时被Heavy Hitter选中的token未必适合量化。关于Q-Hitter最终带来的吞吐、延迟、显存节省、精度保持，以及这些结论对应的模型规模和GPU设置，摘要没有充分说明。

## Research Or Engineering Value
如果这套联合选择规则成立，它的实际价值在于让KV cache压缩更接近可部署的系统优化，而不是单点压缩技巧：同样的显存预算下，可能获得更稳的精度-吞吐折中，并减少长上下文生成中的带宽压力。对研究上，它也提醒后续工作把“保留什么”和“如何量化”作为耦合设计，而不是各自独立优化。

## Reading Checklist
- “Quantization Friendliness”具体如何定义、是否需要在线估计、额外开销有多大？
- 相对Heavy Hitter和简单的稀疏+量化串接基线，Q-Hitter在吞吐、延迟、显存和任务精度上的收益分别是多少？
- 效果是否依赖特定模型、上下文长度、层深、bitwidth或GPU平台，尤其深层退化问题是否普遍存在？

## Core Contributions
- 指出KV cache稀疏化与低比特量化存在耦合效应，简单串接会在生成阶段产生次优结果。
- 分析了Heavy Hitter式token选择在<=4-bit量化下的两类缺陷：选择准确性下降，以及被选token未必量化友好。
- 提出Q-Hitter规则，把累计注意力与量化友好度联合用于token选择，目标是更稳地兼顾压缩与模型效果。

## Why Read It
- 它直接命中LLM inference系统里的KV cache显存和带宽瓶颈，题目与摘要都高度贴合serving效率主线。
- 论文关注的是“哪些token值得留给低比特KV cache”这一联合决策，而不是孤立地做稀疏或量化，问题设定本身有系统意义。
- 如果你在看长上下文推理或KV压缩方案，这篇可以用来检查现有heavy-hitter类方法在低bit场景下为什么会失效。

## Risks Or Limits
- 给定摘要没有提供具体实验数字，当前无法判断收益是否主要体现在吞吐、延迟、显存还是仅体现在存储占用。
- Q-Hitter可能需要额外的打分或统计逻辑；如果在线开销不低，系统净收益可能被抵消。 硬件前提、量化格式、实现细节和baseline公平性在摘要中都不清楚，复现与工程落地风险较高。

## Recommended For
- 做LLM serving、KV cache管理和长上下文推理优化的研究者
- 评估稀疏化与低比特量化联合设计的系统工程师
- 关注推理带宽瓶颈、token选择策略和缓存压缩机制的读者

## Keywords
- LLM推理
- KV cache
- 稀疏化
- 低比特量化
- Heavy Hitter
- 长上下文

## Abstract
This paper focuses on addressing the substantial memory footprints and bandwidth costs associated with the deployment of Large Language Models (LLMs). LLMs, characterized by their extensive context length (e.g., $\geq$4096), inherently demands vast memory resource and traffic to store and load the attention key and value embeddings within self-attention modules, referred to as the KV cache. In an effort to alleviate these resource-intensive aspects of LLM inference, techniques such as sparsification and quantization for KV cache reduction have been investigated as separate endeavors within the realm of LLMs. However, this paper illuminates the critical importance of considering the compound effects of these techniques when employed together, as a simplistic amalgamation of sparsification and quantization can yield sub-optimal performance.For instance, the "Heavy Hitter Oracle" has demonstrated that preserving just 20\% of the KV cache attributed to pivotal tokens, denoted as "Heavy Hitters", can yield substantial memory savings while upholding the model's original performance. Furthermore, the KV cache of these "Heavy Hitter" tokens, which are identified as those with the highest accumulated attention scores, can be further quantized with encouraging throughput saving.Nevertheless, our investigation uncovers two primary deficiencies in such unrefined post-sparsification quantization in low-bit scenarios: (1) the application of low-bit KV cache quantization, specifically $\leq$ 4-bit, significantly diminishes the accuracy of Heavy Hitter selection during the generation phase, particularly in deeper layers; (2) tokens selected by the "Heavy Hitter Oracle" are not necessarily well-suited for quantization, and their quantization can lead to sub-optimal performance. To surmount these challenges, we propose a novel rule-of-thumb for token selection during LLM generation, termed Q-Hitter. This approach combines both accumulated attention scores and "Quantization Friendliness" metrics for different layers, identifying tokens that are not only pivotal for preserving the generalization capabilities of LLMs but are also more amenable to KV cache quantization. Q-Hitter naturally offers a free lunch of KV cache quantization and can further escalate the affordability of state-of-the-art LLMs. Additionally, Q-Hitter empowers LLMs to effectively handle inputs of infinite sequence length. Extensive experiments conducted across various LLMs and tasks substantiate the superiority of the proposed Q-Hitter framework over the original H$_2$O framework. Remarkably, Q-Hitter achieves full model quality preservation while delivering up to a remarkable 20$\times$ reduction in memory usage and up to 33$\times$, 33$\times$, 4$\times$ and 1.3$\times$ throughput improvements compared with the Hugginface Accelerate, DeepSpeed, FlexGen and $\mathsf{H_2O}$, respectively. The code will be public upon acceptance.

## Recommendation Signals
- Recommendation score: 7.97
- Relevance score: 3.0
- Recency score: 0.0
- Popularity score: 2.0
- Quality score: 2.0
- Analysis candidate score: 7.75
- Analysis priority rank: 4
- Analysis signals: kv cache
