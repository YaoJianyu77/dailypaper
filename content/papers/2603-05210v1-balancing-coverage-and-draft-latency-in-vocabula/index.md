---
paper_id: 2603.05210v1
title: Balancing Coverage and Draft Latency in Vocabulary Trimming for Faster Speculative
  Decoding
authors:
- Ofir Ben Shoham
domain: Large Language Models
slug: 2603-05210v1-balancing-coverage-and-draft-latency-in-vocabula
published: '2026-03-05T14:20:22Z'
summary: 这篇工作把 speculative decoding 的草稿模型词表大小当成可优化对象，而不是默认沿用全词表。
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
- speculative decoding
- 词表裁剪
- 草稿模型
- Pareto 前沿
- TPE
reading_priority: medium
---

# Balancing Coverage and Draft Latency in Vocabulary Trimming for Faster Speculative Decoding

## TL;DR
这篇工作把 speculative decoding 的草稿模型词表大小当成可优化对象，而不是默认沿用全词表。

## 中文摘要
论文聚焦 speculative decoding 中经常被忽视的瓶颈：草稿模型的词表头会随着词表增大而拖慢整体延迟。作者把草稿词表选择写成覆盖率与延迟的约束优化问题，用训练数据中的 assistant 响应估计覆盖率，用架构感知 FLOPs 估计词表头开销，再用 TPE 搜索 Pareto 前沿。摘要称实验显示推测解码性能改进，但具体加速幅度、任务类型和对准确性的影响摘要没有充分说明。

## Quick Facts
- Paper ID: `2603.05210v1`
- Authors: Ofir Ben Shoham
- Domain: Large Language Models
- Published: 2026-03-05T14:20:22Z
- arXiv: [abstract](https://arxiv.org/abs/2603.05210v1)
- PDF: [download](https://arxiv.org/pdf/2603.05210v1.pdf)
- Reading priority: medium
- Why this priority: 工程问题切得准，但贡献相对集中在专域草稿模型设计，且实验细节摘要不完整。

## Research Background And Motivation
Speculative decoding 已成主流推理加速路线，但草稿模型串行生成和大词表输出头常常吞掉一部分收益。面向专域部署时，真实工作负载往往只会用到全词表中的小子集。

## Problem Framing
问题是如何在不显著损伤 token 覆盖和 target agreement 的前提下，缩小草稿模型词表以降低延迟。这个权衡直接决定 speculative decoding 在实际系统里能否净赚。

## Method Overview
作者把词表选择建模为带最低覆盖约束的优化问题，用训练数据中的 assistant 响应估计覆盖率，用架构感知 FLOPs 估计词表头延迟成本，再用 Tree-structured Parzen Estimator 搜索 coverage-latency Pareto 前沿。

## Experimental Setup And Evidence
摘要只说实验显示 speculative decoding 表现改进，说明该词表裁剪策略在覆盖与延迟之间找到了更好平衡。具体加速比、任务类型、草稿接受率变化和准确性损失摘要没有充分说明。

## Research Or Engineering Value
如果结论成立，这一方法能让专域或企业内部部署的 speculative decoding 更易落地，特别是在词表冗余明显的场景。它也给草稿模型设计提供了一个比“缩模型”更细粒度的优化旋钮。

## Reading Checklist
- 词表裁剪后的收益在跨域输入上是否快速退化，是否需要按场景重做选择？
- 词表缩小后对 target model 接受率和最终输出质量的影响有多大？
- 该方法是否依赖特定 tokenizer、模型结构或训练数据分布？

## Core Contributions
- 把 speculative decoding 中草稿模型的词表大小明确为一类可优化的系统瓶颈。
- 提出覆盖率与延迟联合建模的词表选择目标，而不是只按频率裁剪。
- 使用架构感知 FLOPs 和 TPE 搜索 Pareto 前沿，为草稿模型设计提供自动化流程。

## Why Read It
- 这是少见直接优化草稿模型输出头成本的推理系统论文，问题切得很实。
- 如果你在做专域推理服务，这种按工作负载裁剪词表的想法很可能比通用技巧更有效。
- 论文把速度收益写成显式权衡问题，方便判断何时值得用。

## Risks Or Limits
- 方法很可能依赖场景分布，跨域泛化未必稳定。
- 摘要没有说明准确性与接受率损失，不能只看延迟收益。

## Recommended For
- 做 LLM 推理系统与服务优化的工程师
- 关注 speculative decoding 细粒度瓶颈的研究者
- 需要专域部署高吞吐生成系统的团队

## Keywords
- speculative decoding
- 词表裁剪
- 草稿模型
- Pareto 前沿
- TPE

## Abstract
Speculative decoding accelerates inference for Large Language Models by using a lightweight draft model to propose candidate tokens that are verified in parallel by a larger target model. Prior work shows that the draft model often dominates speculative decoding latency, since it generates tokens sequentially and incurs high cost from its language modeling head as vocabulary size grows. This exposes a fundamental trade-off in draft model design: larger vocabularies improve token coverage and agreement with the target model, but incur higher draft latency, while smaller vocabularies reduce latency at the risk of missing tokens required for accurate draft generation. We address this trade-off through vocabulary trimming for draft models, motivated by the observation that domain-specific workloads use only a small fraction of the full vocabulary. We cast draft vocabulary selection as a constrained optimization problem that balances token coverage and draft latency. Coverage is computed over assistant responses in the training data, while latency is estimated using architecture-aware FLOPs that capture the cost of the language modeling head as a function of vocabulary size. We optimize a utility function with a Tree-structured Parzen Estimator to efficiently explore the coverage-latency Pareto frontier under a minimum coverage constraint. Experiments show improved speculative decoding throughput while reducing draft vocabularies by up to 97% with high coverage. On domain-specific tasks, we achieve up to 16% latency reduction and 20% throughput improvement, and up to 6.7% throughput gains on diverse out-of-distribution tasks.

## Recommendation Signals
- Recommendation score: 8.2
- Relevance score: 3.0
- Recency score: 3.0
- Popularity score: 1.2
- Quality score: 1.2
