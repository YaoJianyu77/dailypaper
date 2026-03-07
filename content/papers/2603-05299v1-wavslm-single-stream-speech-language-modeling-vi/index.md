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
summary: 这篇论文想把文本里的单流自回归范式迁到语音建模上，避免复杂多流或强文本监督。
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
- WavLM蒸馏
- 自回归预训练
- 多模态
reading_priority: medium
---

# WavSLM: Single-Stream Speech Language Modeling via WavLM Distillation

## TL;DR
这篇论文想把文本里的单流自回归范式迁到语音建模上，避免复杂多流或强文本监督。

## 中文摘要
论文针对语音语言建模中语义与声学纠缠的问题，提出单流建模思路，并借助WavLM蒸馏来逼近文本LLM常见的自回归预训练范式。它的价值在于尝试减少对文本监督、层级token流或混合架构的依赖，让语音生成建模更接近统一范式。摘要给了方向，但没有在已提供内容中说明语音token化、生成目标和生成质量证据，摘要没有充分说明。

## Quick Facts
- Paper ID: `2603.05299v1`
- Authors: Luca Della Libera, Cem Subakan, Mirco Ravanelli
- Domain: Large Language Models
- Published: 2026-03-05T15:39:54Z
- arXiv: [abstract](https://arxiv.org/abs/2603.05299v1)
- PDF: [download](https://arxiv.org/pdf/2603.05299v1.pdf)
- Reading priority: medium
- Why this priority: 方向有潜力，也贴近多模态长期主线，但当前信息不足以判断其通用性和实证强度。

## Problem Framing
问题是把文本中的简单自回归训练范式迁移到语音上很难，因为语义与声学信息纠缠，现有方法常依赖文本监督、多层token流或复杂混合架构。

## Approach Snapshot
方法是提出WavSLM，通过WavLM蒸馏构建单流语音语言模型，以更接近文本LLM的生成式预训练方式；但摘要没有充分说明蒸馏目标、输入输出表示以及训练数据形态。

## Evidence Mentioned In Abstract
摘要给出的证据主要是对现有语音语言模型路线复杂度的概括，以及作者提出单流方案的动机；在已给内容中，没有看到对比方法、语音理解或生成任务结果，摘要没有充分说明。

## Reading Checklist
- 单流表示如何同时承载语义和声学信息，是否会牺牲其中一端？
- WavLM蒸馏具体蒸馏了什么信号，是表征、token还是生成目标？
- 方法在零样本生成、识别或理解任务上分别表现如何？

## Core Contributions
- 尝试把单流自回归建模引入语音语言模型。
- 把WavLM蒸馏作为连接现有语音表征与生成式建模的桥梁。
- 直接挑战语音建模必须依赖复杂多流架构的默认设定。

## Why Read It
- 如果你关心多模态中的语音支线，这篇讨论的是范式统一，而不是单一任务技巧。
- 它可能影响未来语音Agent或语音交互系统的预训练设计。
- 单流方案若成立，会让语音系统更容易复用文本LLM时代的工程经验。

## Risks Or Limits
- 语音的高带宽与细粒度变化可能让单流建模代价很高。
- 蒸馏方案可能把已有表征模型的偏差直接带入生成模型。

## Recommended For
- 关注语音语言模型、跨模态统一建模的研究者
- 在做语音交互或语音Agent预训练的工程师

## Keywords
- 语音语言模型
- 单流建模
- WavLM蒸馏
- 自回归预训练
- 多模态

## Abstract
Large language models show that simple autoregressive training can yield scalable and coherent generation, but extending this paradigm to speech remains challenging due to the entanglement of semantic and acoustic information. Most existing speech language models rely on text supervision, hierarchical token streams, or complex hybrid architectures, departing from the single-stream generative pretraining paradigm that has proven effective in text. In this work, we introduce WavSLM, a speech language model trained by quantizing and distilling self-supervised WavLM representations into a single codebook and optimizing an autoregressive next-chunk prediction objective. WavSLM jointly models semantic and acoustic information within a single token stream without text supervision or text pretraining. Despite its simplicity, it achieves competitive performance on consistency benchmarks and speech generation while using fewer parameters, less training data, and supporting streaming inference. Demo samples are available at https://lucadellalib.github.io/wavslm-web/.

## Recommendation Signals
- Recommendation score: 8.09
- Relevance score: 2.52
- Recency score: 3.0
- Popularity score: 1.6
- Quality score: 1.6
