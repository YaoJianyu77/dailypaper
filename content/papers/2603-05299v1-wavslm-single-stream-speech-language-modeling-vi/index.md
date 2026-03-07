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
summary: 这篇工作试图把文本 LLM 中“单流自回归预训练”的简洁范式搬到语音上，绕开文本监督和多流结构。
source_url: https://arxiv.org/abs/2603.05299v1
pdf_url: https://arxiv.org/pdf/2603.05299v1.pdf
scores:
  relevance: 2.52
  recency: 3.0
  popularity: 1.6
  quality: 1.6
  recommendation: 8.09
tags:
- paper-note
status: generated
updated: '2026-03-07'
keywords:
- 语音语言模型
- 单流建模
- WavLM 蒸馏
- 自回归 next-chunk
- 流式推理
reading_priority: medium
---

# WavSLM: Single-Stream Speech Language Modeling via WavLM Distillation

## TL;DR
这篇工作试图把文本 LLM 中“单流自回归预训练”的简洁范式搬到语音上，绕开文本监督和多流结构。

## 中文摘要
WavSLM 通过量化并蒸馏自监督 WavLM 表征，把语义与声学信息压进单一代码本，再做自回归 next-chunk 预测。它的主张是：不依赖文本监督、文本预训练或复杂多流架构，也能得到有竞争力的语音建模与生成效果，并支持流式推理。摘要给出了“更少参数、更少训练数据、竞争性表现”的方向性结论，但具体基准、指标和失效模式摘要没有充分说明。

## Quick Facts
- Paper ID: `2603.05299v1`
- Authors: Luca Della Libera, Cem Subakan, Mirco Ravanelli
- Domain: Large Language Models
- Published: 2026-03-05T15:39:54Z
- arXiv: [abstract](https://arxiv.org/abs/2603.05299v1)
- PDF: [download](https://arxiv.org/pdf/2603.05299v1.pdf)
- Reading priority: medium
- Why this priority: 方法问题有代表性，但离当前以 LLM、Agent、多模态系统为中心的主线稍远，而且摘要证据较概括。

## Research Background And Motivation
文本 LLM 证明了单流自回归预训练的可扩展性，但把这套范式迁移到语音并不直接，因为语义和声学信息高度纠缠。现有语音语言模型常依赖文本监督、层级 token 流或更复杂的混合架构。

## Problem Framing
问题是能否在不借助文本监督和复杂多流设计的情况下，用单一 token 流同时建模语音的语义与声学信息。这个问题重要，因为更简单的训练与推理范式更容易扩展和部署。

## Method Overview
作者先对自监督 WavLM 表征进行量化与蒸馏，得到单一代码本表示，再训练单流自回归模型做 next-chunk prediction。整个方案强调结构简单、无需文本预训练，并支持流式推理。

## Experimental Setup And Evidence
摘要声称该方法在一致性基准和语音生成上有竞争力，同时参数更少、训练数据更少，并支持 streaming inference。具体比较对象、生成质量评价方式和长时语音稳定性摘要没有充分说明。

## Research Or Engineering Value
如果结论成立，这项工作说明语音语言模型未必一定要走多流或文本依赖路线，单流范式也可能成为更简单的基础模型方案。对研究者来说，它提供了“语音版 LLM 预训练”是否能保持简洁性的一个重要样本。

## Reading Checklist
- 单一代码本如何同时保住语义与声学细节，是否会出现一端被压缩牺牲的问题？
- 所谓 competitive performance 具体落在哪些任务和指标上，和现有多流方法差距多大？
- 流式推理的延迟、稳定性和长时生成质量如何衡量？

## Core Contributions
- 提出基于 WavLM 蒸馏的单流语音语言模型，而不是依赖文本监督或层级 token 设计。
- 用单一代码本统一承载语义与声学信息，并采用自回归 next-chunk 目标训练。
- 在摘要中同时主张了竞争性性能、较少参数和较少训练数据，以及流式推理能力。

## Why Read It
- 如果你关心非文本模态能否复制 LLM 的简洁预训练范式，这篇论文很有代表性。
- 它的设计选择很克制，适合用来判断语音建模到底需不需要复杂结构。
- 即使你不做语音，这篇论文也能提供“单流表示是否足够”这一更普遍的问题样本。

## Risks Or Limits
- 单一代码本可能不足以同时覆盖高保真声学与高层语义。
- 方法可能高度依赖 WavLM 表征质量，创新边界需要仔细区分。

## Recommended For
- 做语音语言模型和语音生成的研究者
- 关注非文本模态是否能套用 LLM 训练范式的读者
- 研究流式生成系统的工程师

## Keywords
- 语音语言模型
- 单流建模
- WavLM 蒸馏
- 自回归 next-chunk
- 流式推理

## Abstract
Large language models show that simple autoregressive training can yield scalable and coherent generation, but extending this paradigm to speech remains challenging due to the entanglement of semantic and acoustic information. Most existing speech language models rely on text supervision, hierarchical token streams, or complex hybrid architectures, departing from the single-stream generative pretraining paradigm that has proven effective in text. In this work, we introduce WavSLM, a speech language model trained by quantizing and distilling self-supervised WavLM representations into a single codebook and optimizing an autoregressive next-chunk prediction objective. WavSLM jointly models semantic and acoustic information within a single token stream without text supervision or text pretraining. Despite its simplicity, it achieves competitive performance on consistency benchmarks and speech generation while using fewer parameters, less training data, and supporting streaming inference. Demo samples are available at https://lucadellalib.github.io/wavslm-web/.

## Recommendation Signals
- Recommendation score: 8.09
- Relevance score: 2.52
- Recency score: 3.0
- Popularity score: 1.6
- Quality score: 1.6
