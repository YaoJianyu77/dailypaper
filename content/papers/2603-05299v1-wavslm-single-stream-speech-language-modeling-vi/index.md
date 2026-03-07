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
summary: 用WavLM蒸馏出的单码本离散表示，尝试把语音生成做成真正的单流自回归建模。
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
- WavLM
- 单流建模
- 量化蒸馏
- 自回归生成
- 流式推理
reading_priority: high
---

# WavSLM: Single-Stream Speech Language Modeling via WavLM Distillation

## TL;DR
用WavLM蒸馏出的单码本离散表示，尝试把语音生成做成真正的单流自回归建模。

## 中文摘要
WavSLM将自监督WavLM表示量化并蒸馏到单一代码本中，再用自回归的next-chunk prediction训练语音语言模型。它试图同时在同一token流里建模语义和声学信息，并明确避免文本监督与文本预训练。摘要称，该方法在一致性基准和语音生成上具备竞争力，同时参数更少、训练数据更省，并支持流式推理。

## Quick Facts
- Paper ID: `2603.05299v1`
- Authors: Luca Della Libera, Cem Subakan, Mirco Ravanelli
- Domain: Large Language Models
- Published: 2026-03-05T15:39:54Z
- arXiv: [abstract](https://arxiv.org/abs/2603.05299v1)
- PDF: [download](https://arxiv.org/pdf/2603.05299v1.pdf)
- Reading priority: high
- Why this priority: 它正面挑战语音建模的表示范式，是多模态生成方向里少见的结构性尝试。

## Core Contributions
- 提出基于WavLM蒸馏和单码本量化的单流语音语言模型。
- 在同一token流中联合建模语义与声学信息，且不依赖文本监督。
- 兼顾生成能力与流式推理，强调简洁架构。

## Why Read It
- 它直接挑战语音建模为何不能沿用文本中的单流自回归范式。
- 如果你关注语音原生生成模型，这是一条明显更简化的路线。
- 参数和数据成本更低的表述，使其具备一定工程吸引力。

## Risks Or Limits
- 摘要没有充分说明量化码本大小、语义与声学权衡以及失真控制方式。
- 竞争力结论存在，但摘要没有充分说明所对比的基线和评测覆盖面。","不依赖文本是优点，也可能限制与文本任务对齐时的上限。

## Recommended For
- 语音生成研究者
- 多模态基础模型研究者
- 流式推理系统工程师

## Keywords
- 语音语言模型
- WavLM
- 单流建模
- 量化蒸馏
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
