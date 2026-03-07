---
paper_id: 2603.05299v1
title: 'WavSLM: Single-Stream Speech Language Modeling via WavLM Distillation'
authors:
- Luca Della Libera
- Cem Subakan
- Mirco Ravanelli
domain: Large Language Models
slug: 2603-05299v1-wavslm-single-stream-speech-language-modeling-vi
published: '2026-03-05T15:39:54Z'
summary: Large language models show that simple autoregressive training can yield
  scalable and coherent generation, but extending this paradigm to speech remains
  challenging due to the entanglement of semantic and acoustic information.
source_url: https://arxiv.org/abs/2603.05299v1
pdf_url: https://arxiv.org/pdf/2603.05299v1.pdf
scores:
  relevance: 3.3
  recency: 3.0
  popularity: 1.6
  quality: 1.6
  recommendation: 8.53
tags:
- paper-note
status: generated
updated: '2026-03-07'
reading_priority: medium
---

# WavSLM: Single-Stream Speech Language Modeling via WavLM Distillation

## TL;DR
Large language models show that simple autoregressive training can yield scalable and coherent generation, but extending this paradigm to speech remains challenging due to the entanglement of semantic and acoustic information.

## 中文摘要
Large language models show that simple autoregressive training can yield scalable and coherent generation, but extending this paradigm to speech remains challenging due to the entanglement of semantic and acoustic information.

## Quick Facts
- Paper ID: `2603.05299v1`
- Authors: Luca Della Libera, Cem Subakan, Mirco Ravanelli
- Domain: Large Language Models
- Published: 2026-03-05T15:39:54Z
- arXiv: [abstract](https://arxiv.org/abs/2603.05299v1)
- PDF: [download](https://arxiv.org/pdf/2603.05299v1.pdf)
- Reading priority: medium

## Abstract
Large language models show that simple autoregressive training can yield scalable and coherent generation, but extending this paradigm to speech remains challenging due to the entanglement of semantic and acoustic information. Most existing speech language models rely on text supervision, hierarchical token streams, or complex hybrid architectures, departing from the single-stream generative pretraining paradigm that has proven effective in text. In this work, we introduce WavSLM, a speech language model trained by quantizing and distilling self-supervised WavLM representations into a single codebook and optimizing an autoregressive next-chunk prediction objective. WavSLM jointly models semantic and acoustic information within a single token stream without text supervision or text pretraining. Despite its simplicity, it achieves competitive performance on consistency benchmarks and speech generation while using fewer parameters, less training data, and supporting streaming inference. Demo samples are available at https://lucadellalib.github.io/wavslm-web/.

## Recommendation Signals
- Recommendation score: 8.53
- Relevance score: 3.3
- Recency score: 3.0
- Popularity score: 1.6
- Quality score: 1.6
