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
summary: 用合成数据、工具使用和离策略强化学习，系统化训练企业搜索型知识Agent。
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
- 知识Agent
- 企业搜索
- 强化学习
- 合成数据
- 工具使用
- 多任务泛化
reading_priority: high
---

# KARL: Knowledge Agents via Reinforcement Learning

## TL;DR
用合成数据、工具使用和离策略强化学习，系统化训练企业搜索型知识Agent。

## 中文摘要
论文先提出KARLBench，覆盖约束实体搜索、跨文档报告综合、表格数值推理、穷尽式实体检索、技术文档过程推理和企业笔记事实汇聚等六类任务。随后作者展示，多行为、多任务联合训练比只对单一基准优化更具泛化性，并给出一个利用长程推理与工具使用生成多样、可溯源训练数据的Agent合成管线。摘要称，基于迭代大批量离策略RL的后训练范式，使KARL在其基准上取得了具成本与延迟优势的表现，并在更高测试时计算下超过强闭源模型。

## Quick Facts
- Paper ID: `2603.05218v1`
- Authors: Jonathan D. Chang, Andrew Drozdov, Shubham Toshniwal, Owen Oertell, Alexander Trott, Jacob Portes, Abhay Gupta, Pallavi Koppol, Ashutosh Baheti, Sean Kulinski, Ivan Zhou, Irene Dea, Krista Opsahl-Ong, Simon Favreau-Lessard, Sean Owen, Jose Javier Gonzalez Ortiz, Arnav Singhvi, Xabi Andrade, Cindy Wang, Kartik Sreenivasan, Sam Havens, Jialu Liu, Peyton DeNiro, Wen Sun, Michael Bendersky, Jonathan Frankle
- Domain: Large Language Models
- Published: 2026-03-05T14:30:25Z
- arXiv: [abstract](https://arxiv.org/abs/2603.05218v1)
- PDF: [download](https://arxiv.org/pdf/2603.05218v1.pdf)
- Reading priority: high
- Why this priority: 它同时覆盖Agent评测、数据和RL训练范式，信息密度高且与当前Agent主线高度相关。

## Core Contributions
- 提出覆盖六类企业搜索行为的KARLBench评测集。
- 证明跨异构搜索行为的多任务训练优于单基准优化。
- 提出结合长程推理、工具使用和迭代自举的数据合成管线，以及大批量离策略RL后训练范式。

## Why Read It
- 它把Agent研究从prompt workflow推进到评测集、数据生成和后训练范式三件套。
- 企业搜索任务难验证，这篇正面处理了如何训练与如何评估的问题。
- 适合和RAG、工具调用以及RL后训练路线做方法论比较。

## Risks Or Limits
- 很多结论建立在作者自建基准上，外部可复现性与基准偏差需要警惕。
- 摘要没有充分说明训练成本、工具环境复杂度和真实企业数据权限约束。","对开放网页、长尾事实或强对抗查询的鲁棒性边界不清楚。

## Recommended For
- Agent研究者
- 企业搜索系统团队
- RL后训练研究者

## Keywords
- 知识Agent
- 企业搜索
- 强化学习
- 合成数据
- 工具使用
- 多任务泛化

## Abstract
We present a system for training enterprise search agents via reinforcement learning that achieves state-of-the-art performance across a diverse suite of hard-to-verify agentic search tasks. Our work makes four core contributions. First, we introduce KARLBench, a multi-capability evaluation suite spanning six distinct search regimes, including constraint-driven entity search, cross-document report synthesis, tabular numerical reasoning, exhaustive entity retrieval, procedural reasoning over technical documentation, and fact aggregation over internal enterprise notes. Second, we show that models trained across heterogeneous search behaviors generalize substantially better than those optimized for any single benchmark. Third, we develop an agentic synthesis pipeline that employs long-horizon reasoning and tool use to generate diverse, grounded, and high-quality training data, with iterative bootstrapping from increasingly capable models. Fourth, we propose a new post-training paradigm based on iterative large-batch off-policy RL that is sample efficient, robust to train-inference engine discrepancies, and naturally extends to multi-task training with out-of-distribution generalization. Compared to Claude 4.6 and GPT 5.2, KARL is Pareto-optimal on KARLBench across cost-quality and latency-quality trade-offs, including tasks that were out-of-distribution during training. With sufficient test-time compute, it surpasses the strongest closed models. These results show that tailored synthetic data in combination with multi-task reinforcement learning enables cost-efficient and high-performing knowledge agents for grounded reasoning.

## Recommendation Signals
- Recommendation score: 7.73
- Relevance score: 2.0
- Recency score: 3.0
- Popularity score: 2.3
- Quality score: 2.3
