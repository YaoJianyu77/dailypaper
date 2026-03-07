---
paper_id: 2603.05500v1
title: 'POET-X: Memory-efficient LLM Training by Scaling Orthogonal Transformation'
authors:
- Zeju Qiu
- Lixin Liu
- Adrian Weller
- Han Shi
- Weiyang Liu
domain: Large Language Models
slug: 2603-05500v1-poet-x-memory-efficient-llm-training-by-scaling
published: '2026-03-05T18:59:23Z'
summary: Efficient and stable training of large language models (LLMs) remains a core
  challenge in modern machine learning systems.
source_url: https://arxiv.org/abs/2603.05500v1
pdf_url: https://arxiv.org/pdf/2603.05500v1.pdf
scores:
  relevance: 3.8
  recency: 3.0
  popularity: 1.2
  quality: 1.2
  recommendation: 8.67
tags:
- paper-note
status: generated
updated: '2026-03-07'
---

# POET-X: Memory-efficient LLM Training by Scaling Orthogonal Transformation

## Summary
Efficient and stable training of large language models (LLMs) remains a core challenge in modern machine learning systems.

## Quick Facts
- Paper ID: `2603.05500v1`
- Authors: Zeju Qiu, Lixin Liu, Adrian Weller, Han Shi, Weiyang Liu
- Domain: Large Language Models
- Published: 2026-03-05T18:59:23Z
- arXiv: [abstract](https://arxiv.org/abs/2603.05500v1)
- PDF: [download](https://arxiv.org/pdf/2603.05500v1.pdf)

## Abstract
Efficient and stable training of large language models (LLMs) remains a core challenge in modern machine learning systems. To address this challenge, Reparameterized Orthogonal Equivalence Training (POET), a spectrum-preserving framework that optimizes each weight matrix through orthogonal equivalence transformation, has been proposed. Although POET provides strong training stability, its original implementation incurs high memory consumption and computational overhead due to intensive matrix multiplications. To overcome these limitations, we introduce POET-X, a scalable and memory-efficient variant that performs orthogonal equivalence transformations with significantly reduced computational cost. POET-X maintains the generalization and stability benefits of POET while achieving substantial improvements in throughput and memory efficiency. In our experiments, POET-X enables the pretraining of billion-parameter LLMs on a single Nvidia H100 GPU, and in contrast, standard optimizers such as AdamW run out of memory under the same settings.

## Recommendation Signals
- Recommendation score: 8.67
- Relevance score: 3.8
- Recency score: 3.0
- Popularity score: 1.2
- Quality score: 1.2
