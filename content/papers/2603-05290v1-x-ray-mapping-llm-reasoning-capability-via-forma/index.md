---
paper_id: 2603.05290v1
title: 'X-RAY: Mapping LLM Reasoning Capability via Formalized and Calibrated Probes'
authors:
- Gao Tianxi
- Cai Yufan
- Yuan Yusi
- Dong Jin Song
domain: Large Language Models
slug: 2603-05290v1-x-ray-mapping-llm-reasoning-capability-via-forma
published: '2026-03-05T15:34:22Z'
summary: Large language models (LLMs) achieve promising performance, yet their ability
  to reason remains poorly understood.
source_url: https://arxiv.org/abs/2603.05290v1
pdf_url: https://arxiv.org/pdf/2603.05290v1.pdf
scores:
  relevance: 1.9
  recency: 3.0
  popularity: 2.0
  quality: 2.0
  recommendation: 7.8
tags:
- paper-note
status: generated
updated: '2026-03-07'
reading_priority: medium
---

# X-RAY: Mapping LLM Reasoning Capability via Formalized and Calibrated Probes

## TL;DR
Large language models (LLMs) achieve promising performance, yet their ability to reason remains poorly understood.

## 中文摘要
Large language models (LLMs) achieve promising performance, yet their ability to reason remains poorly understood.

## Quick Facts
- Paper ID: `2603.05290v1`
- Authors: Gao Tianxi, Cai Yufan, Yuan Yusi, Dong Jin Song
- Domain: Large Language Models
- Published: 2026-03-05T15:34:22Z
- arXiv: [abstract](https://arxiv.org/abs/2603.05290v1)
- PDF: [download](https://arxiv.org/pdf/2603.05290v1.pdf)
- Reading priority: medium

## Abstract
Large language models (LLMs) achieve promising performance, yet their ability to reason remains poorly understood. Existing evaluations largely emphasize task-level accuracy, often conflating pattern matching with reasoning capability. We present X-RAY, an explainable reasoning analysis system that maps the LLM reasoning capability using calibrated, formally verified probes. We model reasoning capability as a function of extractable \textit{structure}, operationalized through formal properties such as constraint interaction, reasoning depth, and solution-space geometry. X-Ray generates probes via formal tools with controlled structural variations, enabling precise isolation of incremental structural information through formal calibration and verification. We evaluate state-of-the-art LLMs on problems ranging from junior-level to advanced in mathematics, physics, and chemistry. Our analysis reveals a systematic asymmetry in LLM reasoning: models are relatively robust to constraint refinement, where additional conditions shrink an existing solution space, but degrade sharply under solution-space restructuring, where modifications alter the underlying structural form of the solution manifold. Moreover, calibrated formal probes differentiate models that appear indistinguishable on standard benchmarks and reveal failure modes that are structurally interpretable rather than opaque. Beyond evaluation, our framework is contamination-free and supports the training and testing of reasoning models.

## Recommendation Signals
- Recommendation score: 7.8
- Relevance score: 1.9
- Recency score: 3.0
- Popularity score: 2.0
- Quality score: 2.0
