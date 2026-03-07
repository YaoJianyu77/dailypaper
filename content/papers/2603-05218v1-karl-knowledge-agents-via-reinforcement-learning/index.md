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
summary: We present a system for training enterprise search agents via reinforcement
  learning that achieves state-of-the-art performance across a diverse suite of hard-to-verify
  agentic search tasks.
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
reading_priority: medium
---

# KARL: Knowledge Agents via Reinforcement Learning

## TL;DR
We present a system for training enterprise search agents via reinforcement learning that achieves state-of-the-art performance across a diverse suite of hard-to-verify agentic search tasks.

## 中文摘要
We present a system for training enterprise search agents via reinforcement learning that achieves state-of-the-art performance across a diverse suite of hard-to-verify agentic search tasks.

## Quick Facts
- Paper ID: `2603.05218v1`
- Authors: Jonathan D. Chang, Andrew Drozdov, Shubham Toshniwal, Owen Oertell, Alexander Trott, Jacob Portes, Abhay Gupta, Pallavi Koppol, Ashutosh Baheti, Sean Kulinski, Ivan Zhou, Irene Dea, Krista Opsahl-Ong, Simon Favreau-Lessard, Sean Owen, Jose Javier Gonzalez Ortiz, Arnav Singhvi, Xabi Andrade, Cindy Wang, Kartik Sreenivasan, Sam Havens, Jialu Liu, Peyton DeNiro, Wen Sun, Michael Bendersky, Jonathan Frankle
- Domain: Large Language Models
- Published: 2026-03-05T14:30:25Z
- arXiv: [abstract](https://arxiv.org/abs/2603.05218v1)
- PDF: [download](https://arxiv.org/pdf/2603.05218v1.pdf)
- Reading priority: medium

## Abstract
We present a system for training enterprise search agents via reinforcement learning that achieves state-of-the-art performance across a diverse suite of hard-to-verify agentic search tasks. Our work makes four core contributions. First, we introduce KARLBench, a multi-capability evaluation suite spanning six distinct search regimes, including constraint-driven entity search, cross-document report synthesis, tabular numerical reasoning, exhaustive entity retrieval, procedural reasoning over technical documentation, and fact aggregation over internal enterprise notes. Second, we show that models trained across heterogeneous search behaviors generalize substantially better than those optimized for any single benchmark. Third, we develop an agentic synthesis pipeline that employs long-horizon reasoning and tool use to generate diverse, grounded, and high-quality training data, with iterative bootstrapping from increasingly capable models. Fourth, we propose a new post-training paradigm based on iterative large-batch off-policy RL that is sample efficient, robust to train-inference engine discrepancies, and naturally extends to multi-task training with out-of-distribution generalization. Compared to Claude 4.6 and GPT 5.2, KARL is Pareto-optimal on KARLBench across cost-quality and latency-quality trade-offs, including tasks that were out-of-distribution during training. With sufficient test-time compute, it surpasses the strongest closed models. These results show that tailored synthetic data in combination with multi-task reinforcement learning enables cost-efficient and high-performing knowledge agents for grounded reasoning.

## Recommendation Signals
- Recommendation score: 7.73
- Relevance score: 2.0
- Recency score: 3.0
- Popularity score: 2.3
- Quality score: 2.3
