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
summary: 它用 WavLM 蒸馏去支撑单流语音语言建模，目标是靠近文本 LLM 的简洁预训练范式。
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
- 自回归预训练
- 音频
reading_priority: medium
---

# WavSLM: Single-Stream Speech Language Modeling via WavLM Distillation

## TL;DR
它用 WavLM 蒸馏去支撑单流语音语言建模，目标是靠近文本 LLM 的简洁预训练范式。

## 中文摘要
这篇工作尝试把文本 LLM 中常见的单流自回归预训练范式迁移到语音建模，并用 WavLM 蒸馏处理语义与声学纠缠问题。它的价值在于尽量减少对文本监督、分层 token 流或复杂混合架构的依赖。摘要没有充分说明单流表示的构造方式、训练目标以及覆盖的是生成、理解还是两者兼顾。

## Quick Facts
- Paper ID: `2603.05299v1`
- Authors: Luca Della Libera, Cem Subakan, Mirco Ravanelli
- Domain: Large Language Models
- Published: 2026-03-05T15:39:54Z
- arXiv: [abstract](https://arxiv.org/abs/2603.05299v1)
- PDF: [download](https://arxiv.org/pdf/2603.05299v1.pdf)
- Reading priority: medium
- Why this priority: 方向有潜力，但更偏语音子领域，关键建模细节摘要没有充分说明，优先级低于主线 LLM 与 Agent 工作。

## Core Contributions
- 尝试用 WavLM 蒸馏构建单流语音语言模型。
- 把语音建模向文本 LLM 常见的单流自回归预训练范式靠拢。
- 减少对文本监督、分层 token 流或复杂混合架构的依赖。

## Why Read It
- 语音基础模型仍缺少像文本 LLM 那样统一而简洁的训练范式。
- 如果单流方案可行，系统复杂度和扩展路径都会更清晰。
- 对语音-语言统一建模和音频多模态都有参考价值。

## Risks Or Limits
- 摘要没有充分说明蒸馏目标、离散或连续表示形式以及训练数据假设。
- 仅凭摘要看不出它更偏生成、识别还是通用语音建模。','与现有语音语言模型的效率和质量差异没有展开。

## Recommended For
- 语音语言模型研究者
- 做音频多模态预训练的团队
- 关注统一生成范式的读者

## Keywords
- 语音语言模型
- 单流建模
- WavLM 蒸馏
- 自回归预训练
- 音频

## Abstract
Large language models show that simple autoregressive training can yield scalable and coherent generation, but extending this paradigm to speech remains challenging due to the entanglement of semantic and acoustic information. Most existing speech language models rely on text supervision, hierarchical token streams, or complex hybrid architectures, departing from the single-stream generative pretraining paradigm that has proven effective in text. In this work, we introduce WavSLM, a speech language model trained by quantizing and distilling self-supervised WavLM representations into a single codebook and optimizing an autoregressive next-chunk prediction objective. WavSLM jointly models semantic and acoustic information within a single token stream without text supervision or text pretraining. Despite its simplicity, it achieves competitive performance on consistency benchmarks and speech generation while using fewer parameters, less training data, and supporting streaming inference. Demo samples are available at https://lucadellalib.github.io/wavslm-web/.

## Recommendation Signals
- Recommendation score: 8.09
- Relevance score: 2.52
- Recency score: 3.0
- Popularity score: 1.6
- Quality score: 1.6
