---
paper_id: 2603.05210v1
title: Balancing Coverage and Draft Latency in Vocabulary Trimming for Faster Speculative
  Decoding
authors:
- Ofir Ben Shoham
domain: Large Language Models
slug: 2603-05210v1-balancing-coverage-and-draft-latency-in-vocabula
published: '2026-03-05T14:20:22Z'
summary: 论文抓住推测解码里草稿模型词表过大带来的延迟瓶颈，讨论如何在覆盖率和速度之间做可用折中。
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
- 推测解码
- 词表裁剪
- 推理加速
- 草稿模型
- 延迟优化
reading_priority: high
---

# Balancing Coverage and Draft Latency in Vocabulary Trimming for Faster Speculative Decoding

## TL;DR
论文抓住推测解码里草稿模型词表过大带来的延迟瓶颈，讨论如何在覆盖率和速度之间做可用折中。

## 中文摘要
论文抓住推测解码里的一个具体系统瓶颈：草稿模型词表越大，语言模型头越慢，但词表太小又会损失 token 覆盖率。它的价值在于把推理加速问题落到一个可操作的设计维度上，而不是只讨论草稿模型和目标模型的大小搭配。摘要没有充分说明裁剪策略如何确定、对接受率和最终吞吐的影响，以及不同 tokenizer 设置下是否稳健。

## Quick Facts
- Paper ID: `2603.05210v1`
- Authors: Ofir Ben Shoham
- Domain: Large Language Models
- Published: 2026-03-05T14:20:22Z
- arXiv: [abstract](https://arxiv.org/abs/2603.05210v1)
- PDF: [download](https://arxiv.org/pdf/2603.05210v1.pdf)
- Reading priority: high
- Why this priority: 推理加速价值直接、问题表述清楚，适合优先判断是否能转化为现有 serving 栈优化。

## Core Contributions
- 把草稿模型词表大小识别为推测解码中的关键延迟来源之一。
- 围绕词表裁剪明确提出覆盖率与草稿延迟之间的设计权衡。
- 把推测解码优化推进到输出头与词表层面的系统设计。

## Why Read It
- 这是直接面向线上推理吞吐和时延的可操作问题。
- 比单纯换更小的草稿模型更细粒度，可能更容易落地到现有 serving 栈。
- 对正在做 speculative decoding 的团队，这类瓶颈分析很实用。

## Risks Or Limits
- 摘要没有充分说明裁剪规则、动态或静态策略选择，以及是否需要重训练。
- 词表变小后对接受率、长尾 token 和多语言场景的影响未说明。','不同 tokenizer、不同草稿模型与目标模型组合上的泛化性未说明。

## Recommended For
- 做 LLM 推理栈优化的工程师
- speculative decoding 研究者
- 关注线上延迟与吞吐的团队

## Keywords
- 推测解码
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
