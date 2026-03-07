---
paper_id: 2603.05210v1
title: Balancing Coverage and Draft Latency in Vocabulary Trimming for Faster Speculative
  Decoding
authors:
- Ofir Ben Shoham
domain: Large Language Models
slug: 2603-05210v1-balancing-coverage-and-draft-latency-in-vocabula
published: '2026-03-05T14:20:22Z'
summary: 通过给draft模型裁剪词表，重新平衡投机解码的覆盖率和草稿延迟。
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
- 投机解码
- 词表裁剪
- 推理加速
- draft model
- 延迟优化
reading_priority: high
---

# Balancing Coverage and Draft Latency in Vocabulary Trimming for Faster Speculative Decoding

## TL;DR
通过给draft模型裁剪词表，重新平衡投机解码的覆盖率和草稿延迟。

## 中文摘要
这篇论文抓住了speculative decoding里常被忽略的瓶颈：draft model需要顺序生成，而大词表会让language modeling head成本偏高。作者把draft词表选择建模为同时权衡token覆盖率和生成延迟的约束优化问题，并用训练数据中的assistant响应估计覆盖率、用与架构相关的FLOPs估计延迟。核心思路是针对特定域只保留高价值词项，但摘要没有充分说明实际加速幅度、精度损失与适用工作负载。

## Quick Facts
- Paper ID: `2603.05210v1`
- Authors: Ofir Ben Shoham
- Domain: Large Language Models
- Published: 2026-03-05T14:20:22Z
- arXiv: [abstract](https://arxiv.org/abs/2603.05210v1)
- PDF: [download](https://arxiv.org/pdf/2603.05210v1.pdf)
- Reading priority: high
- Why this priority: 直接服务LLM推理加速，问题具体、工程价值高，且与当前部署实践高度相关。

## Core Contributions
- 把draft model词表大小显式视为speculative decoding的关键延迟来源。
- 提出覆盖率与延迟联合优化的词表裁剪formulation，而不是经验式删词。
- 给出结合训练语料分布与架构FLOPs的可计算选择准则。

## Why Read It
- 如果你在做LLM推理优化，这是一篇很务实的系统论文切口。
- 它把投机解码速度问题从模型结构转到了输出词表设计，角度新而直接。
- 对垂直域部署尤其有参考价值，因为域内词频分布通常更稳定。

## Risks Or Limits
- 词表裁剪高度依赖工作负载分布，域外迁移可能明显退化。
- 摘要没有充分说明对罕见但关键token的召回保护机制。

## Recommended For
- 推理工程师
- 投机解码研究者
- 垂直域LLM部署团队

## Keywords
- 投机解码
- 词表裁剪
- 推理加速
- draft model
- 延迟优化

## Abstract
Speculative decoding accelerates inference for Large Language Models by using a lightweight draft model to propose candidate tokens that are verified in parallel by a larger target model. Prior work shows that the draft model often dominates speculative decoding latency, since it generates tokens sequentially and incurs high cost from its language modeling head as vocabulary size grows. This exposes a fundamental trade-off in draft model design: larger vocabularies improve token coverage and agreement with the target model, but incur higher draft latency, while smaller vocabularies reduce latency at the risk of missing tokens required for accurate draft generation. We address this trade-off through vocabulary trimming for draft models, motivated by the observation that domain-specific workloads use only a small fraction of the full vocabulary. We cast draft vocabulary selection as a constrained optimization problem that balances token coverage and draft latency. Coverage is computed over assistant responses in the training data, while latency is estimated using architecture-aware FLOPs that capture the cost of the language modeling head as a function of vocabulary size. We optimize a utility function with a Tree-structured Parzen Estimator to efficiently explore the coverage-latency Pareto frontier under a minimum coverage constraint. Experiments show improved speculative decoding throughput while reducing draft vocabularies by up to 97% with high coverage. On domain-specific tasks, we achieve up to 16% latency reduction and 20% throughput improvement, and up to 6.7% throughput gains on diverse out-of-distribution tasks.

## Recommendation Signals
- Recommendation score: 8.0
- Relevance score: 3.3
- Recency score: 3.0
- Popularity score: 1.2
- Quality score: 1.2
