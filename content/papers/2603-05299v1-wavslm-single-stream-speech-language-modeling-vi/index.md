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
summary: 这篇工作把自监督语音表征压成单一离散码流并做自回归下一块预测，试图用更接近文本 LM 的简单范式同时统一语义与声学建模。
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
- WavLM
- 表征蒸馏
- 离散量化
- 自回归 next-chunk prediction
reading_priority: medium
---

# WavSLM: Single-Stream Speech Language Modeling via WavLM Distillation

## TL;DR
这篇工作把自监督语音表征压成单一离散码流并做自回归下一块预测，试图用更接近文本 LM 的简单范式同时统一语义与声学建模。

## 中文摘要
这篇工作试图解决语音中语义与声学纠缠，导致文本 LLM 式单流自回归预训练难以直接迁移的问题。作者将自监督 WavLM 表征量化并蒸馏到单一码本，再以 next-chunk 目标训练单流语音语言模型，在无文本监督和无文本预训练下联合建模两类信息。摘要声称该方法在一致性基准和语音生成上具有竞争力，同时参数更少、训练数据更少，并支持流式推理。但比较对象、评测设置和优势来源没有展开，摘要没有充分说明。

## Quick Facts
- Paper ID: `2603.05299v1`
- Authors: Luca Della Libera, Cem Subakan, Mirco Ravanelli
- Domain: Large Language Models
- Published: 2026-03-05T15:39:54Z
- arXiv: [abstract](https://arxiv.org/abs/2603.05299v1)
- PDF: [download](https://arxiv.org/pdf/2603.05299v1.pdf)
- Reading priority: medium
- Why this priority: 它的价值在于把文本 LM 的单流自回归范式直接迁到语音建模，并且摘要强调效率与流式推理，这对方法论很值得跟进；但论文更偏语音方向，且关键实验细节与比较对象在摘要中没有展开，所以优先级适合列为中等偏上而非当天最先读。

## Research Background And Motivation
文本大模型已经证明单流自回归预训练在规模化和生成一致性上的价值，但语音同时包含语义、说话人、韵律和细粒度声学因素，导致直接照搬文本范式并不容易。现有语音语言模型常借助文本监督、多层 token 或混合架构，因此一个真正语音原生、结构更简单的单流方案具有方法论价值。

## Problem Framing
问题是：能否在不依赖文本监督、文本预训练或复杂多流结构的前提下，用单一 token 流同时表示并生成语音中的语义与声学信息。这个问题重要，是因为它决定语音生成模型能否像文本 LLM 一样走向更统一、更可扩展、也更适合流式部署的预训练范式。

## Method Overview
方法是先用自监督 WavLM 提取语音表征，再把这些表征量化并蒸馏到单一码本中，最后用自回归的 next-chunk prediction 目标训练语音语言模型。核心思路不是分层拆开语义和声学，而是把二者压到同一离散序列里联合预测，从而维持单流生成结构。

## Experimental Setup And Evidence
摘要给出的证据主要是结果声明：模型在一致性基准和语音生成上达到“有竞争力”的表现，同时使用更少参数、更少训练数据，并支持流式推理。摘要没有给出具体基线、指标、任务设置、消融或数值，因此这些优势目前只能视为待正文核实的主张，摘要没有充分说明。

## Research Or Engineering Value
如果这条路线成立，它意味着语音原生生成模型可以用更接近文本 LM 的统一训练范式完成表示学习与生成，而不必依赖文本桥接或复杂多流工程。对研究上，它能帮助判断单流自回归在语音域的适用边界；对工程上，它可能带来更小模型、更低数据成本和更自然的流式推理路径。

## Reading Checklist
- 单一码本是否足以同时保留语义内容、说话人特征、韵律和细粒度声学细节，量化误差会如何影响生成质量？
- 所谓“competitive”具体是相对哪些文本监督、多流 token 或混合架构基线成立，比较任务、指标和代价分别是什么？
- 流式推理是如何实现的，它是否会牺牲长程一致性、延迟表现或语音自然度？

## Core Contributions
- 提出一个不依赖文本监督或文本预训练的单流语音语言建模框架。
- 用 WavLM 表征的量化与蒸馏，把原本可能需要分层处理的语义与声学信息压入单一码本并做统一自回归预测。
- 摘要声称该框架在保持结构简洁的同时兼顾竞争性生成表现、较低参数与数据成本，以及流式推理能力。

## Why Read It
- 它直接检验文本 LLM 中“简单单流自回归”这条主线能否迁移到语音原生生成，是方法论上值得关注的问题。
- 相比常见的文本辅助或多流设计，这个方案的建模假设更强，若成立会显著简化语音 foundation model 的结构选择。
- 摘要同时把性能、效率和流式部署放在同一方案里，这对研究和工程都比单纯追求更大模型更有现实价值。

## Risks Or Limits
- 单一码本可能形成信息瓶颈，难以同时承载高层语义和细粒度声学，导致生成质量或可控性受限。
- 摘要未说明“竞争力”来自哪些基线、哪些评测和哪些指标，核心结论目前证据不足。

## Recommended For
- 关注语音原生生成模型和 speech foundation model 的研究者
- 研究离散语音 token、表征蒸馏与自回归生成的读者
- 关心低复杂度、低数据成本和流式语音部署路径的工程师

## Keywords
- 语音语言模型
- 单流建模
- WavLM
- 表征蒸馏
- 离散量化
- 自回归 next-chunk prediction

## Abstract
Large language models show that simple autoregressive training can yield scalable and coherent generation, but extending this paradigm to speech remains challenging due to the entanglement of semantic and acoustic information. Most existing speech language models rely on text supervision, hierarchical token streams, or complex hybrid architectures, departing from the single-stream generative pretraining paradigm that has proven effective in text. In this work, we introduce WavSLM, a speech language model trained by quantizing and distilling self-supervised WavLM representations into a single codebook and optimizing an autoregressive next-chunk prediction objective. WavSLM jointly models semantic and acoustic information within a single token stream without text supervision or text pretraining. Despite its simplicity, it achieves competitive performance on consistency benchmarks and speech generation while using fewer parameters, less training data, and supporting streaming inference. Demo samples are available at https://lucadellalib.github.io/wavslm-web/.

## Recommendation Signals
- Recommendation score: 8.09
- Relevance score: 2.52
- Recency score: 3.0
- Popularity score: 1.6
- Quality score: 1.6
