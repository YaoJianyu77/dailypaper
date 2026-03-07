---
paper_id: 2603.05210v1
title: Balancing Coverage and Draft Latency in Vocabulary Trimming for Faster Speculative
  Decoding
authors:
- Ofir Ben Shoham
domain: Large Language Models
slug: 2603-05210v1-balancing-coverage-and-draft-latency-in-vocabula
published: '2026-03-05T14:20:22Z'
summary: 从草稿模型词表下手优化推测解码，把覆盖率和延迟的矛盾显式化。
source_url: https://arxiv.org/abs/2603.05210v1
pdf_url: https://arxiv.org/pdf/2603.05210v1.pdf
scores:
  relevance: 3.3
  recency: 3.0
  popularity: 1.2
  quality: 1.2
  recommendation: 8.0
tags:
- paper-note
status: generated
updated: '2026-03-07'
keywords:
- 推测解码
- 词表裁剪
- 延迟优化
- 吞吐提升
- Pareto前沿
- 草稿模型
reading_priority: high
---

# Balancing Coverage and Draft Latency in Vocabulary Trimming for Faster Speculative Decoding

## TL;DR
从草稿模型词表下手优化推测解码，把覆盖率和延迟的矛盾显式化。

## 中文摘要
论文指出，推测解码里草稿模型往往才是主要延迟来源，而词表越大，语言模型头的顺序生成成本越高。作者将草稿词表选择表述为一个同时约束覆盖率与延迟的优化问题，用训练数据中的assistant回复估计覆盖率，并用架构感知FLOPs估计延迟，再以Tree-structured Parzen Estimator搜索Pareto前沿。摘要称，该方法可将草稿词表最多缩减97%，并在领域任务上带来最高16%的延迟下降和20%的吞吐提升。

## Quick Facts
- Paper ID: `2603.05210v1`
- Authors: Ofir Ben Shoham
- Domain: Large Language Models
- Published: 2026-03-05T14:20:22Z
- arXiv: [abstract](https://arxiv.org/abs/2603.05210v1)
- PDF: [download](https://arxiv.org/pdf/2603.05210v1.pdf)
- Reading priority: high
- Why this priority: 问题定义直接落在推理成本上，方法又足够工程化，适合优先吸收。

## Core Contributions
- 把草稿模型词表选择形式化为覆盖率与延迟的受约束优化问题。
- 结合覆盖统计与架构感知FLOPs，构造可操作的延迟代理目标。
- 用TPE搜索覆盖率-延迟Pareto前沿，直接服务推测解码加速。

## Why Read It
- 它不是又一个通用加速技巧，而是直击推测解码中常被忽略的词表成本。
- 方法可解释，容易与现有草稿模型或领域部署流程结合。
- 对服务特定领域流量的LLM推理系统尤其有现实意义。

## Risks Or Limits
- 收益依赖领域分布稳定性，词表裁剪后遇到分布漂移可能回退明显。
- 摘要没有充分说明裁剪词表对生成质量、罕见token和安全对齐的影响。","延迟模型基于FLOPs估计，真实系统中的内存与内核开销是否匹配，摘要没有充分说明。

## Recommended For
- LLM推理工程师
- 推测解码研究者
- 领域化模型部署团队

## Keywords
- 推测解码
- 词表裁剪
- 延迟优化
- 吞吐提升
- Pareto前沿
- 草稿模型

## Abstract
Speculative decoding accelerates inference for Large Language Models by using a lightweight draft model to propose candidate tokens that are verified in parallel by a larger target model. Prior work shows that the draft model often dominates speculative decoding latency, since it generates tokens sequentially and incurs high cost from its language modeling head as vocabulary size grows. This exposes a fundamental trade-off in draft model design: larger vocabularies improve token coverage and agreement with the target model, but incur higher draft latency, while smaller vocabularies reduce latency at the risk of missing tokens required for accurate draft generation. We address this trade-off through vocabulary trimming for draft models, motivated by the observation that domain-specific workloads use only a small fraction of the full vocabulary. We cast draft vocabulary selection as a constrained optimization problem that balances token coverage and draft latency. Coverage is computed over assistant responses in the training data, while latency is estimated using architecture-aware FLOPs that capture the cost of the language modeling head as a function of vocabulary size. We optimize a utility function with a Tree-structured Parzen Estimator to efficiently explore the coverage-latency Pareto frontier under a minimum coverage constraint. Experiments show improved speculative decoding throughput while reducing draft vocabularies by up to 97% with high coverage. On domain-specific tasks, we achieve up to 16% latency reduction and 20% throughput improvement, and up to 6.7% throughput gains on diverse out-of-distribution tasks.

## Recommendation Signals
- Recommendation score: 8.0
- Relevance score: 3.3
- Recency score: 3.0
- Popularity score: 1.2
- Quality score: 1.2
