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
summary: 把WavLM表征蒸馏成单码本语音token流，重走文本LLM式自回归预训练。
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
keywords:
- 语音语言模型
- WavLM蒸馏
- 单码本
- 自回归生成
- 流式推理
reading_priority: high
---

# WavSLM: Single-Stream Speech Language Modeling via WavLM Distillation

## TL;DR
把WavLM表征蒸馏成单码本语音token流，重走文本LLM式自回归预训练。

## 中文摘要
论文试图把文本LLM中简单单流自回归训练范式迁移到语音生成，不依赖文本监督或分层token流。作者通过量化并蒸馏自监督WavLM表征到单一codebook，再用next-chunk prediction训练WavSLM，使语义和声学信息在同一token流里联合建模。摘要称其在一致性基准和语音生成上达到有竞争力的表现，同时参数更少、训练数据更少，并支持流式推理。

## Quick Facts
- Paper ID: `2603.05299v1`
- Authors: Luca Della Libera, Cem Subakan, Mirco Ravanelli
- Domain: Large Language Models
- Published: 2026-03-05T15:39:54Z
- arXiv: [abstract](https://arxiv.org/abs/2603.05299v1)
- PDF: [download](https://arxiv.org/pdf/2603.05299v1.pdf)
- Reading priority: high
- Why this priority: 同时贴合多模态与生成建模主线，而且方法上有明显的范式简化价值。

## Core Contributions
- 提出单流语音语言模型WavSLM，把语义和声学信息统一到一个token流。
- 通过量化和蒸馏WavLM表征构造单码本表示，避免依赖文本监督或文本预训练。
- 在方法设计上同时追求结构简化、数据效率和流式推理能力。

## Why Read It
- 如果你关注语音生成如何借鉴文本LLM范式，这篇工作切口很直接。
- 它用更简单的表示与训练目标挑战了语音模型必须多流或依赖文本监督的常见设定。

## Risks Or Limits
- 单码本表示是否会压缩掉细粒度声学信息，摘要未说明。
- 摘要没有充分说明分词/量化误差、跨语言泛化和失败样例。

## Recommended For
- 语音语言模型研究者
- 多模态生成研究者
- 流式音频系统工程师

## Keywords
- 语音语言模型
- WavLM蒸馏
- 单码本
- 自回归生成
- 流式推理

## Abstract
Large language models show that simple autoregressive training can yield scalable and coherent generation, but extending this paradigm to speech remains challenging due to the entanglement of semantic and acoustic information. Most existing speech language models rely on text supervision, hierarchical token streams, or complex hybrid architectures, departing from the single-stream generative pretraining paradigm that has proven effective in text. In this work, we introduce WavSLM, a speech language model trained by quantizing and distilling self-supervised WavLM representations into a single codebook and optimizing an autoregressive next-chunk prediction objective. WavSLM jointly models semantic and acoustic information within a single token stream without text supervision or text pretraining. Despite its simplicity, it achieves competitive performance on consistency benchmarks and speech generation while using fewer parameters, less training data, and supporting streaming inference. Demo samples are available at https://lucadellalib.github.io/wavslm-web/.

## Recommendation Signals
- Recommendation score: 8.53
- Relevance score: 3.3
- Recency score: 3.0
- Popularity score: 1.6
- Quality score: 1.6
