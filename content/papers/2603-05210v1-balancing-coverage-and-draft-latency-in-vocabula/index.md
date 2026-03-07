---
paper_id: 2603.05210v1
title: Balancing Coverage and Draft Latency in Vocabulary Trimming for Faster Speculative
  Decoding
authors:
- Ofir Ben Shoham
domain: Large Language Models
slug: 2603-05210v1-balancing-coverage-and-draft-latency-in-vocabula
published: '2026-03-05T14:20:22Z'
summary: 这篇论文盯住了投机解码里常被忽视的瓶颈：草稿模型词表越大越慢，但词表太小又会拖累覆盖率。
source_url: https://arxiv.org/abs/2603.05210v1
pdf_url: https://arxiv.org/pdf/2603.05210v1.pdf
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
- 投机解码
- 词表裁剪
- 推理加速
- 草稿模型
- 延迟优化
reading_priority: high
---

# Balancing Coverage and Draft Latency in Vocabulary Trimming for Faster Speculative Decoding

## TL;DR
这篇论文盯住了投机解码里常被忽视的瓶颈：草稿模型词表越大越慢，但词表太小又会拖累覆盖率。

## 中文摘要
论文聚焦投机解码中的一个很具体但重要的系统权衡，即草稿模型词表裁剪如何在延迟和覆盖率之间取得平衡。摘要说明作者把瓶颈定位到草稿模型顺序生成和大词表语言模型头的成本，并试图通过词表裁剪改善整体速度。这个切口很实用，但给定摘要没有充分说明裁剪策略如何决定、对接受率的影响有多大，以及最终端到端收益是否稳定。

## Quick Facts
- Paper ID: `2603.05210v1`
- Authors: Ofir Ben Shoham
- Domain: Large Language Models
- Published: 2026-03-05T14:20:22Z
- arXiv: [abstract](https://arxiv.org/abs/2603.05210v1)
- PDF: [download](https://arxiv.org/pdf/2603.05210v1.pdf)
- Reading priority: high
- Why this priority: 这是很贴近生产系统的推理优化问题，抽象清晰且可落地；虽然摘要缺实验细节，但值得优先看其权衡分析是否扎实。

## Problem Framing
问题是投机解码虽能加速推理，但草稿模型往往成为瓶颈，而大词表一方面提高候选覆盖率，另一方面又增加草稿模型延迟。

## Approach Snapshot
方法是研究词表裁剪，在覆盖率与草稿延迟之间做平衡，从而加快投机解码；但摘要没有充分说明裁剪是静态的、动态的，还是上下文相关的。

## Evidence Mentioned In Abstract
摘要给出了清晰的问题分析：草稿模型生成是顺序的，且语言模型头成本会随词表增大；但在已提供信息中，没有看到接受率、吞吐、延迟或不同词表规模下的结果，摘要没有充分说明。

## Reading Checklist
- 词表裁剪规则是离线固定的，还是会随上下文动态变化？
- 裁剪后草稿模型提案质量下降多少，目标模型接受率是否明显受损？
- 端到端收益是在单步延迟、吞吐量还是总生成时长上最明显？

## Core Contributions
- 把投机解码瓶颈具体落到草稿模型词表规模这一可操作变量上。
- 明确提出覆盖率与延迟之间的基本权衡，而不是只追求更小草稿模型。
- 为推理优化提供了一个可能比改模型结构更轻量的系统手段。

## Why Read It
- 这类方法离真实部署很近，尤其适合服务端推理优化。
- 问题定义清楚，容易和现有投机解码实现结合评估。
- 如果结论稳健，可能为草稿模型设计提供新的默认策略。

## Risks Or Limits
- 摘要没有说明裁剪是否依赖特定语料、语言或模型家族。
- 如果接受率下降过多，局部加速可能换来端到端退化。

## Recommended For
- 关注推理加速、投机解码与大模型服务性能的工程师
- 研究解码算法与系统联合优化的研究者

## Keywords
- 投机解码
- 词表裁剪
- 推理加速
- 草稿模型
- 延迟优化

## Abstract
Speculative decoding accelerates inference for Large Language Models by using a lightweight draft model to propose candidate tokens that are verified in parallel by a larger target model. Prior work shows that the draft model often dominates speculative decoding latency, since it generates tokens sequentially and incurs high cost from its language modeling head as vocabulary size grows. This exposes a fundamental trade-off in draft model design: larger vocabularies improve token coverage and agreement with the target model, but incur higher draft latency, while smaller vocabularies reduce latency at the risk of missing tokens required for accurate draft generation. We address this trade-off through vocabulary trimming for draft models, motivated by the observation that domain-specific workloads use only a small fraction of the full vocabulary. We cast draft vocabulary selection as a constrained optimization problem that balances token coverage and draft latency. Coverage is computed over assistant responses in the training data, while latency is estimated using architecture-aware FLOPs that capture the cost of the language modeling head as a function of vocabulary size. We optimize a utility function with a Tree-structured Parzen Estimator to efficiently explore the coverage-latency Pareto frontier under a minimum coverage constraint. Experiments show improved speculative decoding throughput while reducing draft vocabularies by up to 97% with high coverage. On domain-specific tasks, we achieve up to 16% latency reduction and 20% throughput improvement, and up to 6.7% throughput gains on diverse out-of-distribution tasks.

## Recommendation Signals
- Recommendation score: 8.2
- Relevance score: 3.0
- Recency score: 3.0
- Popularity score: 1.2
- Quality score: 1.2
