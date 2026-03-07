---
paper_id: 2603.05218v1
title: 'KARL: Knowledge Agents via Reinforcement Learning'
authors:
- Jonathan D. Chang
- Andrew Drozdov
- Shubham Toshniwal
- Owen Oertell
- Alexander Trott
- Jacob Portes
- Abhay Gupta
- Pallavi Koppol
- Ashutosh Baheti
- Sean Kulinski
- Ivan Zhou
- Irene Dea
- Krista Opsahl-Ong
- Simon Favreau-Lessard
- Sean Owen
- Jose Javier Gonzalez Ortiz
- Arnav Singhvi
- Xabi Andrade
- Cindy Wang
- Kartik Sreenivasan
- Sam Havens
- Jialu Liu
- Peyton DeNiro
- Wen Sun
- Michael Bendersky
- Jonathan Frankle
domain: Large Language Models
slug: 2603-05218v1-karl-knowledge-agents-via-reinforcement-learning
published: '2026-03-05T14:30:25Z'
summary: 用评测集、合成数据和离策略强化学习一体化训练企业搜索Agent。
source_url: https://arxiv.org/abs/2603.05218v1
pdf_url: https://arxiv.org/pdf/2603.05218v1.pdf
scores:
  relevance: 2.0
  recency: 3.0
  popularity: 2.3
  quality: 2.3
  recommendation: 7.73
tags:
- paper-note
status: generated
updated: '2026-03-07'
keywords:
- Agent
- 企业搜索
- 强化学习
- 评测基准
- 合成数据
reading_priority: high
---

# KARL: Knowledge Agents via Reinforcement Learning

## TL;DR
用评测集、合成数据和离策略强化学习一体化训练企业搜索Agent。

## 中文摘要
KARL把企业搜索Agent训练拆成三个互相支撑的部分：KARLBench评测、多能力训练数据合成，以及迭代式大批量离策略RL后训练。评测覆盖六类搜索能力，作者还声称跨异构搜索行为联合训练比单一基准优化更能泛化。摘要同时强调其训练数据由长程推理和工具使用驱动生成，但关于最终系统在分布外设置下的细节被截断，摘要没有充分说明。

## Quick Facts
- Paper ID: `2603.05218v1`
- Authors: Jonathan D. Chang, Andrew Drozdov, Shubham Toshniwal, Owen Oertell, Alexander Trott, Jacob Portes, Abhay Gupta, Pallavi Koppol, Ashutosh Baheti, Sean Kulinski, Ivan Zhou, Irene Dea, Krista Opsahl-Ong, Simon Favreau-Lessard, Sean Owen, Jose Javier Gonzalez Ortiz, Arnav Singhvi, Xabi Andrade, Cindy Wang, Kartik Sreenivasan, Sam Havens, Jialu Liu, Peyton DeNiro, Wen Sun, Michael Bendersky, Jonathan Frankle
- Domain: Large Language Models
- Published: 2026-03-05T14:30:25Z
- arXiv: [abstract](https://arxiv.org/abs/2603.05218v1)
- PDF: [download](https://arxiv.org/pdf/2603.05218v1.pdf)
- Reading priority: high
- Why this priority: 虽然推荐分略低，但它同时覆盖Agent评测、数据构造和RL后训练，信息密度很高。

## Core Contributions
- 提出覆盖六类企业搜索能力的KARLBench，用于系统评估难验证的agentic search任务。
- 证明跨多种搜索行为联合训练优于只针对单一基准优化的策略。
- 提出结合长程推理、工具使用和迭代bootstrap的数据合成流程，以及大批量离策略RL后训练范式。

## Why Read It
- 如果你在做搜索Agent，这篇论文几乎覆盖了评测、数据和后训练三件最难的事。
- 它把Agent训练从“手工prompt加少量benchmark”推进到更系统的后训练框架。
- 对企业内部知识搜索这类难以直接验证的任务尤其有现实意义。

## Risks Or Limits
- 企业搜索场景高度依赖私有数据分布，外部复现与迁移难度可能很高。
- 摘要没有充分说明奖励设计、工具环境约束和线上成本。

## Recommended For
- 搜索Agent研究者
- RL后训练团队
- 企业AI工程师

## Keywords
- Agent
- 企业搜索
- 强化学习
- 评测基准
- 合成数据

## Abstract
We present a system for training enterprise search agents via reinforcement learning that achieves state-of-the-art performance across a diverse suite of hard-to-verify agentic search tasks. Our work makes four core contributions. First, we introduce KARLBench, a multi-capability evaluation suite spanning six distinct search regimes, including constraint-driven entity search, cross-document report synthesis, tabular numerical reasoning, exhaustive entity retrieval, procedural reasoning over technical documentation, and fact aggregation over internal enterprise notes. Second, we show that models trained across heterogeneous search behaviors generalize substantially better than those optimized for any single benchmark. Third, we develop an agentic synthesis pipeline that employs long-horizon reasoning and tool use to generate diverse, grounded, and high-quality training data, with iterative bootstrapping from increasingly capable models. Fourth, we propose a new post-training paradigm based on iterative large-batch off-policy RL that is sample efficient, robust to train-inference engine discrepancies, and naturally extends to multi-task training with out-of-distribution generalization. Compared to Claude 4.6 and GPT 5.2, KARL is Pareto-optimal on KARLBench across cost-quality and latency-quality trade-offs, including tasks that were out-of-distribution during training. With sufficient test-time compute, it surpasses the strongest closed models. These results show that tailored synthetic data in combination with multi-task reinforcement learning enables cost-efficient and high-performing knowledge agents for grounded reasoning.

## Recommendation Signals
- Recommendation score: 7.73
- Relevance score: 2.0
- Recency score: 3.0
- Popularity score: 2.3
- Quality score: 2.3
