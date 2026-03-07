---
paper_id: 2603.05210v1
title: Balancing Coverage and Draft Latency in Vocabulary Trimming for Faster Speculative
  Decoding
authors:
- Ofir Ben Shoham
domain: Large Language Models
slug: 2603-05210v1-balancing-coverage-and-draft-latency-in-vocabula
published: '2026-03-05T14:20:22Z'
summary: Speculative decoding accelerates inference for Large Language Models by using
  a lightweight draft model to propose candidate tokens that are verified in parallel
  by a larger target model.
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
reading_priority: medium
---

# Balancing Coverage and Draft Latency in Vocabulary Trimming for Faster Speculative Decoding

## TL;DR
Speculative decoding accelerates inference for Large Language Models by using a lightweight draft model to propose candidate tokens that are verified in parallel by a larger target model.

## 中文摘要
Speculative decoding accelerates inference for Large Language Models by using a lightweight draft model to propose candidate tokens that are verified in parallel by a larger target model.

## Quick Facts
- Paper ID: `2603.05210v1`
- Authors: Ofir Ben Shoham
- Domain: Large Language Models
- Published: 2026-03-05T14:20:22Z
- arXiv: [abstract](https://arxiv.org/abs/2603.05210v1)
- PDF: [download](https://arxiv.org/pdf/2603.05210v1.pdf)
- Reading priority: medium

## Abstract
Speculative decoding accelerates inference for Large Language Models by using a lightweight draft model to propose candidate tokens that are verified in parallel by a larger target model. Prior work shows that the draft model often dominates speculative decoding latency, since it generates tokens sequentially and incurs high cost from its language modeling head as vocabulary size grows. This exposes a fundamental trade-off in draft model design: larger vocabularies improve token coverage and agreement with the target model, but incur higher draft latency, while smaller vocabularies reduce latency at the risk of missing tokens required for accurate draft generation. We address this trade-off through vocabulary trimming for draft models, motivated by the observation that domain-specific workloads use only a small fraction of the full vocabulary. We cast draft vocabulary selection as a constrained optimization problem that balances token coverage and draft latency. Coverage is computed over assistant responses in the training data, while latency is estimated using architecture-aware FLOPs that capture the cost of the language modeling head as a function of vocabulary size. We optimize a utility function with a Tree-structured Parzen Estimator to efficiently explore the coverage-latency Pareto frontier under a minimum coverage constraint. Experiments show improved speculative decoding throughput while reducing draft vocabularies by up to 97% with high coverage. On domain-specific tasks, we achieve up to 16% latency reduction and 20% throughput improvement, and up to 6.7% throughput gains on diverse out-of-distribution tasks.

## Recommendation Signals
- Recommendation score: 8.0
- Relevance score: 3.3
- Recency score: 3.0
- Popularity score: 1.2
- Quality score: 1.2
