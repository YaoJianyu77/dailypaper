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
summary: 这篇工作值得关注的点在于：它试图用接近文本自回归预训练的单流范式，直接做不依赖文本监督的语音语言建模。
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
venue_or_journal: arXiv preprint
citation_summary: Citation count unavailable
keywords:
- 语音语言模型
- 单流建模
- 自回归预训练
- WavLM
- 表征量化
- 知识蒸馏/表征蒸馏（摘要层面）
reading_priority: high
---

# WavSLM: Single-Stream Speech Language Modeling via WavLM Distillation

## TL;DR
这篇工作值得关注的点在于：它试图用接近文本自回归预训练的单流范式，直接做不依赖文本监督的语音语言建模。

## 中文摘要
论文针对语音生成里语义与声学信息纠缠、因此难以复用文本单流自回归范式的问题，提出了 WavSLM。其核心做法是先对自监督 WavLM 表征做量化与蒸馏，再在单一 token 流上进行自回归的 next-chunk 预测，从而同时建模语义与声学信息且不依赖文本监督或文本预训练。摘要声称该方法在一致性基准和语音生成上具有竞争力，同时参数更少、训练数据更少并支持流式推理，但摘要没有充分说明具体实验设置、对比对象和性能幅度。

## Quick Facts
- Paper ID: `2603.05299v1`
- Authors: Luca Della Libera, Cem Subakan, Mirco Ravanelli
- Institutions: Institution information not extracted
- Domain: Large Language Models
- Venue / Journal: arXiv preprint
- Citations: Citation count unavailable
- Published: 2026-03-05T15:39:54Z
- arXiv: [abstract](https://arxiv.org/abs/2603.05299v1)
- PDF: [download](https://arxiv.org/pdf/2603.05299v1.pdf)
- Reading priority: high
- Why this priority: 它虽然不是典型文本 LLM 论文，但问题设定与方法取向高度贴近当前基础模型主线：能否把简单、统一的自回归范式扩展到语音。对关注大模型、多模态和语音 Agent 的读者，这比常规任务型语音论文更值得优先核对；同时摘要中的关键收益都还缺少细节支撑，因此属于“值得尽快读正文验证”的高优先级。

## Research Background And Motivation
大语言模型证明了简单的自回归训练在文本上具备很强的可扩展性，但把同样范式迁移到语音并不直接，因为语音同时承载内容与声学细节。当前不少语音语言模型依赖文本监督、分层 token 或混合架构，因此一个真正语音原生、结构更简洁的单流方案具有现实吸引力。

## Problem Framing
论文要解决的问题是：能否在不借助文本监督或文本预训练的前提下，用单一自回归 token 流同时建模语音中的语义信息和声学信息。这个问题重要，因为如果成立，就可能把语音生成从复杂的多流/混合系统简化为更接近文本 LLM 的统一训练与推理范式。

## Method Overview
方法上，作者将自监督的 WavLM 表征进行量化并蒸馏到单一 codebook，再用自回归的 next-chunk prediction 目标训练语音语言模型。这样模型在单流离散 token 序列上联合建模语义与声学信息，同时保持无文本监督、无文本预训练，并强调支持流式推理。

## Experimental Setup And Evidence
摘要给出的证据主要是定性和方向性的：作者声称该方法在一致性 benchmark 和语音生成任务上达到有竞争力的表现，并且使用更少参数、更少训练数据，且支持流式推理。摘要没有充分说明所用基准、比较对象、评测维度、消融设计以及提升幅度，因此目前只能把这些结论视为待正文核实的主张。

## Research Or Engineering Value
如果这些主张成立，这项工作对研究和工程都很有价值：研究上，它为“语音是否也能像文本一样采用单流自回归预训练”提供了更直接的答案；工程上，它可能减少对文本转写、复杂分层 token 设计和重型混合架构的依赖，为实时语音生成、语音对话系统和语音原生 Agent 提供更简洁的基础模型路线。

## Reading Checklist
- 单一 codebook 是否真的足以同时保留高层语义与低层声学细节，还是在某些场景下会出现明显的信息折损？
- 摘要所说的“competitive”具体相对于哪些语音语言模型，对比是否控制了训练数据规模、参数量和是否使用文本监督？
- 流式推理是通过什么机制实现的，它对生成质量、延迟和长程一致性分别带来什么代价？

## Core Contributions
- 提出一个单流语音语言建模框架，尝试把文本 LLM 中有效的自回归预训练范式迁移到语音域。
- 通过量化并蒸馏 WavLM 自监督表征，把语音建模压缩到单一离散 token 流上，而不是依赖分层 token 或文本辅助。
- 在方法主张上同时强调三点：无需文本监督、模型更轻量、并可支持流式推理。

## Why Read It
- 这篇论文切中的不是常规语音生成小改动，而是语音基础模型是否能走向“单流、统一、自回归”这一更接近文本 LLM 的主线问题。
- 方法新意集中在表示设计与训练目标的组合：用 WavLM 蒸馏后的单一 codebook 作为语音 token 化接口，避免常见的复杂多流架构。
- 如果你关心多模态系统或语音 Agent，这项工作直接关系到未来是否能用更统一、更低系统复杂度的方式构建语音原生生成模型。

## Risks Or Limits
- 摘要没有充分说明实验细节，当前无法判断“更少参数、更少数据”与“性能竞争力”是否同时成立且公平。
- 单流建模可能在表达能力上受限，尤其是在高保真声学细节、韵律控制或复杂说话人变化上是否会吃亏，摘要没有说明。

## Recommended For
- 关注语音原生大模型和 speech LM 架构的人
- 研究多模态基础模型统一建模范式的研究者
- 构建实时语音交互系统或语音 Agent 的工程师

## Keywords
- 语音语言模型
- 单流建模
- 自回归预训练
- WavLM
- 表征量化
- 知识蒸馏/表征蒸馏（摘要层面）

## Abstract
Large language models show that simple autoregressive training can yield scalable and coherent generation, but extending this paradigm to speech remains challenging due to the entanglement of semantic and acoustic information. Most existing speech language models rely on text supervision, hierarchical token streams, or complex hybrid architectures, departing from the single-stream generative pretraining paradigm that has proven effective in text. In this work, we introduce WavSLM, a speech language model trained by quantizing and distilling self-supervised WavLM representations into a single codebook and optimizing an autoregressive next-chunk prediction objective. WavSLM jointly models semantic and acoustic information within a single token stream without text supervision or text pretraining. Despite its simplicity, it achieves competitive performance on consistency benchmarks and speech generation while using fewer parameters, less training data, and supporting streaming inference. Demo samples are available at https://lucadellalib.github.io/wavslm-web/.

## Recommendation Signals
- Recommendation score: 8.09
- Relevance score: 2.52
- Recency score: 3.0
- Popularity score: 1.6
- Quality score: 1.6
